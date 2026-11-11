from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.evaluator import aggregate_results, analyze_text, response_keywords, score_rubric
from app.models import EvaluationRun, ExecutionEvent
from app.pii import redact_pii, scan_pii
from app.provider import OpenAICompatibleProvider, ProviderError
from app.security import redact_error


settings = get_settings()

STAGES = [
    ("validate_input", "Receive & validate input"),
    ("persist_request", "Save evaluation request"),
    ("analyze_response", "Analyze submitted response"),
    ("privacy_scan", "Check potential PII exposure"),
    ("rubric_evaluation", "Evaluate rubric criteria"),
    ("ai_evaluation", "Optional AI-assisted evaluation"),
    ("aggregate_results", "Aggregate evaluation results"),
    ("persist_report", "Store final report"),
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _duration_ms(start_ns: int) -> float:
    return round((time.perf_counter_ns() - start_ns) / 1_000_000, 3)


class EventRecorder:
    def __init__(self, run_id: str):
        self.run_id = run_id

    def emit(
        self,
        stage_id: str,
        event_type: str,
        status: str,
        message: str,
        *,
        duration_ms: float | None = None,
        metadata: dict[str, Any] | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> ExecutionEvent:
        for attempt in range(3):
            db = SessionLocal()
            try:
                current = db.scalar(
                    select(func.max(ExecutionEvent.sequence)).where(ExecutionEvent.run_id == self.run_id)
                ) or 0
                event = ExecutionEvent(
                    run_id=self.run_id,
                    sequence=current + 1,
                    stage_id=stage_id,
                    event_type=event_type,
                    status=status,
                    occurred_at=_now(),
                    duration_ms=duration_ms,
                    message=message[:300],
                    metadata_json=metadata or {},
                    error_code=error_code,
                    error_message=redact_error(error_message) if error_message else None,
                )
                db.add(event)
                db.commit()
                db.refresh(event)
                return event
            except OperationalError:
                db.rollback()
                if attempt == 2:
                    raise
                time.sleep(0.05 * (2**attempt))
            finally:
                db.close()
        raise RuntimeError("Unable to persist event")


def seed_pending_events(run_id: str) -> None:
    recorder = EventRecorder(run_id)
    for stage_id, label in STAGES:
        recorder.emit(stage_id, "stage.pending", "pending", f"{label} is waiting to run")


def _set_run(run_id: str, **values: Any) -> None:
    db = SessionLocal()
    try:
        run = db.get(EvaluationRun, run_id)
        if not run:
            return
        for key, value in values.items():
            setattr(run, key, value)
        run.updated_at = _now()
        db.commit()
    finally:
        db.close()


def _load_run(db: Session, run_id: str) -> EvaluationRun:
    run = db.get(EvaluationRun, run_id)
    if not run:
        raise RuntimeError("Evaluation run no longer exists")
    return run


def process_evaluation(run_id: str, recovered_after_restart: bool = False) -> None:
    recorder = EventRecorder(run_id)
    _set_run(run_id, status="running", error_code=None)
    if recovered_after_restart:
        recorder.emit(
            "validate_input", "pipeline.recovered", "recovered", "Resumed persisted run after server restart"
        )

    analysis: dict = {}
    privacy: dict = {}
    rubric_results: list[dict] = []
    provider_result: dict | None = None
    limitations: list[str] = []

    try:
        # 1. Validate the already-accepted, persisted payload again at the worker boundary.
        stage = "validate_input"
        _set_run(run_id, current_stage=stage)
        start = time.perf_counter_ns()
        recorder.emit(stage, "stage.started", "running", "Validating persisted submission and rubric")
        with SessionLocal() as db:
            run = _load_run(db, run_id)
            if not run.prompt.strip() or not run.response.strip() or not run.rubric:
                raise ValueError("Persisted submission is incomplete")
            input_meta = {
                "prompt_chars": len(run.prompt), "response_chars": len(run.response), "criteria": len(run.rubric)
            }
        recorder.emit(
            stage, "stage.completed", "completed", f"Validated {input_meta['criteria']} rubric criteria",
            duration_ms=_duration_ms(start), metadata=input_meta,
        )

        # 2. Verify durable persistence.
        stage = "persist_request"
        _set_run(run_id, current_stage=stage)
        start = time.perf_counter_ns()
        recorder.emit(stage, "stage.started", "running", "Verifying the saved evaluation request")
        with SessionLocal() as db:
            run = _load_run(db, run_id)
            saved_at = run.created_at.isoformat()
        recorder.emit(
            stage, "stage.completed", "completed", "Evaluation request is stored durably",
            duration_ms=_duration_ms(start), metadata={"saved_at": saved_at},
        )

        # 3. Analyze response.
        stage = "analyze_response"
        _set_run(run_id, current_stage=stage)
        start = time.perf_counter_ns()
        recorder.emit(stage, "stage.started", "running", "Measuring response structure and content signals")
        with SessionLocal() as db:
            run = _load_run(db, run_id)
            analysis = analyze_text(run.response)
            keywords = response_keywords(run.response)
        recorder.emit(
            stage, "stage.completed", "completed",
            f"Analyzed {analysis['word_count']} words across {analysis['paragraph_count']} paragraphs",
            duration_ms=_duration_ms(start), metadata={**analysis, "top_terms": keywords},
        )

        # 4. Privacy scan.
        stage = "privacy_scan"
        _set_run(run_id, current_stage=stage)
        start = time.perf_counter_ns()
        recorder.emit(stage, "stage.started", "running", "Scanning for potential sensitive-data patterns")
        with SessionLocal() as db:
            run = _load_run(db, run_id)
            privacy = scan_pii("\n".join(filter(None, [run.prompt, run.response, run.reference or ""])))
        count = privacy["finding_count"]
        recorder.emit(
            stage, "stage.completed", "completed", f"Detected {count} potential PII pattern{'s' if count != 1 else ''}",
            duration_ms=_duration_ms(start),
            metadata={"finding_count": count, "categories": privacy["categories"]},
        )

        # 5. Deterministic and heuristic rubric evaluation.
        stage = "rubric_evaluation"
        _set_run(run_id, current_stage=stage)
        start = time.perf_counter_ns()
        recorder.emit(stage, "stage.started", "running", "Applying deterministic and labeled heuristic checks")
        with SessionLocal() as db:
            run = _load_run(db, run_id)
            rubric_results = score_rubric(run.rubric, run.prompt, run.response, run.reference, analysis)
        methods = sorted({result["method"] for result in rubric_results})
        recorder.emit(
            stage, "stage.completed", "completed", f"Evaluated {len(rubric_results)} rubric criteria",
            duration_ms=_duration_ms(start), metadata={"criteria": len(rubric_results), "methods": methods},
        )

        # 6. Optional provider evaluation, with actual retries and fallback.
        stage = "ai_evaluation"
        _set_run(run_id, current_stage=stage)
        with SessionLocal() as db:
            run = _load_run(db, run_id)
            preferences = dict(run.preferences)
            use_ai = bool(preferences.get("use_ai"))
        if not use_ai:
            recorder.emit(stage, "stage.skipped", "skipped", "AI-assisted evaluation was not requested", metadata={"reason": "disabled_by_user"})
            limitations.append("AI-assisted evaluation was not requested; results use deterministic and heuristic checks.")
        elif privacy["finding_count"] and not settings.allow_external_ai_with_pii:
            recorder.emit(
                stage, "stage.skipped", "skipped", "External AI was blocked because potential PII was detected",
                metadata={"reason": "privacy_gate", "finding_count": privacy["finding_count"]},
            )
            limitations.append("Model-assisted checks were skipped by the privacy gate.")
        elif not settings.openai_api_key:
            recorder.emit(
                stage, "stage.skipped", "skipped", "AI provider is not configured; deterministic results remain available",
                metadata={"reason": "provider_unavailable"},
            )
            limitations.append("No AI provider is configured; subjective checks remain heuristic.")
        else:
            start = time.perf_counter_ns()
            recorder.emit(stage, "stage.started", "running", "Calling the configured model provider with a strict timeout")
            last_error: Exception | None = None
            for attempt in range(1, settings.provider_max_attempts + 1):
                try:
                    if settings.enable_failure_testing and settings.app_env == "development" and preferences.get("failure_mode") == "provider_timeout":
                        raise ProviderError("Controlled provider timeout")
                    with SessionLocal() as db:
                        run = _load_run(db, run_id)
                        prompt = redact_pii(run.prompt) if preferences.get("redact_before_ai", True) else run.prompt
                        response = redact_pii(run.response) if preferences.get("redact_before_ai", True) else run.response
                        reference = redact_pii(run.reference) if run.reference and preferences.get("redact_before_ai", True) else run.reference
                        provider = OpenAICompatibleProvider(settings)
                        outcome = provider.evaluate(prompt, response, reference, run.rubric)
                    provider_result = {
                        "criteria": outcome.criteria, "summary": outcome.summary,
                        "model": outcome.model, "usage": outcome.usage,
                    }
                    recorder.emit(
                        stage, "stage.completed", "completed", "Model-assisted evaluation completed",
                        duration_ms=_duration_ms(start), metadata={"model": outcome.model, "usage": outcome.usage, "attempt": attempt},
                    )
                    break
                except ProviderError as exc:
                    last_error = exc
                    if attempt < settings.provider_max_attempts:
                        backoff = 0.15 * (2 ** (attempt - 1))
                        recorder.emit(
                            stage, "provider.retrying", "retrying", f"Provider attempt {attempt} failed; retrying",
                            metadata={"attempt": attempt, "backoff_ms": round(backoff * 1000)},
                            error_code="provider_error", error_message=str(exc),
                        )
                        time.sleep(backoff)
            if provider_result is None:
                recorder.emit(
                    stage, "stage.recovered", "recovered", "Provider unavailable; continued with deterministic fallback",
                    duration_ms=_duration_ms(start), metadata={"attempts": settings.provider_max_attempts, "fallback": "deterministic"},
                    error_code="provider_exhausted", error_message=str(last_error),
                )
                limitations.append("The model provider failed; the report recovered with the deterministic fallback and labeled heuristic checks.")

        # 7. Aggregate.
        stage = "aggregate_results"
        _set_run(run_id, current_stage=stage)
        start = time.perf_counter_ns()
        recorder.emit(stage, "stage.started", "running", "Combining weighted criterion scores and report caveats")
        overall = aggregate_results(rubric_results)
        warnings = privacy["finding_count"] + len(limitations)
        report = {
            "overall_score": overall,
            "capability": "model_assisted" if provider_result else "deterministic_and_heuristic",
            "rubric_results": rubric_results,
            "analysis": analysis,
            "privacy": privacy,
            "model_evaluation": provider_result,
            "limitations": limitations + [
                "This report does not prove factual accuracy or guarantee that the response is hallucination-free."
            ],
            "generated_at": _now().isoformat(),
        }
        recorder.emit(
            stage, "stage.completed", "completed", f"Calculated a weighted score of {overall:.1f}/100",
            duration_ms=_duration_ms(start), metadata={"overall_score": overall, "warning_count": warnings},
        )

        # 8. Persist final report.
        stage = "persist_report"
        _set_run(run_id, current_stage=stage)
        start = time.perf_counter_ns()
        recorder.emit(stage, "stage.started", "running", "Saving the final report and terminal run state")
        final_status = "completed_with_warnings" if warnings else "completed"
        if settings.enable_failure_testing and settings.app_env == "development" and preferences.get("failure_mode") == "database_error":
            raise OperationalError("controlled database failure", {}, Exception("controlled"))
        _set_run(
            run_id, report=report, overall_score=overall, warning_count=warnings,
            status=final_status, current_stage=stage, completed_at=_now(),
        )
        recorder.emit(
            stage, "stage.completed", "completed", "Saved the evaluation report",
            duration_ms=_duration_ms(start), metadata={"status": final_status, "report_version": 1},
        )
    except Exception as exc:
        safe = redact_error(exc)
        try:
            recorder.emit(
                locals().get("stage", "validate_input"), "stage.failed", "failed", "Evaluation could not complete",
                error_code=exc.__class__.__name__.lower(), error_message=safe,
            )
            _set_run(run_id, status="failed", error_code=exc.__class__.__name__.lower(), completed_at=_now())
        except Exception:
            # When persistence itself is unavailable, never fabricate a successful state.
            pass
