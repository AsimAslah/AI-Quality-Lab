from __future__ import annotations

import json
import threading
import time
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query, Request, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import database_is_ready, get_db
from app.models import EvaluationRun, ExecutionEvent
from app.pipeline import STAGES, process_evaluation, seed_pending_events
from app.schemas import DashboardOut, EvaluationCreate
from app.security import rate_limiter, require_owner


router = APIRouter(prefix="/api")
settings = get_settings()


def event_dict(event: ExecutionEvent) -> dict:
    return {
        "id": event.id, "run_id": event.run_id, "sequence": event.sequence, "stage_id": event.stage_id,
        "event_type": event.event_type, "status": event.status, "occurred_at": event.occurred_at.isoformat(),
        "duration_ms": event.duration_ms, "message": event.message, "metadata": event.metadata_json,
        "error_code": event.error_code, "error_message": event.error_message,
    }


def run_summary(run: EvaluationRun) -> dict:
    return {
        "id": run.id, "title": run.title, "status": run.status, "overall_score": run.overall_score,
        "warning_count": run.warning_count, "current_stage": run.current_stage,
        "created_at": run.created_at.isoformat(), "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }


def run_detail(run: EvaluationRun) -> dict:
    return {
        **run_summary(run), "prompt": run.prompt, "response": run.response, "reference": run.reference,
        "rubric": run.rubric, "preferences": run.preferences, "report": run.report, "error_code": run.error_code,
    }


def owned_run(db: Session, owner_hash: str, run_id: str) -> EvaluationRun:
    run = db.scalar(
        select(EvaluationRun).where(EvaluationRun.id == run_id, EvaluationRun.owner_hash == owner_hash)
    )
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return run


@router.get("/health")
def health(response: Response) -> dict:
    ready = database_is_ready()
    if not ready:
        response.status_code = 503
    return {"status": "ok" if ready else "degraded", "database": "connected" if ready else "unavailable"}


@router.get("/meta")
def meta() -> dict:
    return {
        "stages": [{"id": stage_id, "name": name} for stage_id, name in STAGES],
        "limits": {
            "prompt_chars": settings.max_prompt_chars, "response_chars": settings.max_response_chars,
            "reference_chars": settings.max_reference_chars, "rubric_criteria": 12,
        },
        "capabilities": {
            "external_ai_configured": bool(settings.openai_api_key),
            "failure_testing": settings.enable_failure_testing and settings.app_env == "development",
        },
    }


@router.post("/evaluations")
def create_evaluation(
    payload: EvaluationCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    response: Response,
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=8, max_length=64),
    db: Session = Depends(get_db),
) -> dict:
    owner = require_owner(request)
    rate_limiter.check(f"submit:{owner}", settings.rate_limit_submissions_per_minute)
    existing = db.scalar(
        select(EvaluationRun).where(
            EvaluationRun.owner_hash == owner, EvaluationRun.idempotency_key == idempotency_key
        )
    )
    if existing:
        response.status_code = status.HTTP_200_OK
        return {"run": run_detail(existing), "duplicate": True}

    if payload.preferences.failure_mode != "none" and not (
        settings.app_env == "development" and settings.enable_failure_testing
    ):
        raise HTTPException(status_code=400, detail="Failure testing is unavailable in this environment")

    run = EvaluationRun(
        owner_hash=owner, idempotency_key=idempotency_key, title=payload.title,
        prompt=payload.prompt, response=payload.response, reference=payload.reference,
        rubric=[item.model_dump() for item in payload.rubric], preferences=payload.preferences.model_dump(),
    )
    db.add(run)
    try:
        db.commit()
        db.refresh(run)
    except IntegrityError:
        db.rollback()
        existing = db.scalar(
            select(EvaluationRun).where(
                EvaluationRun.owner_hash == owner, EvaluationRun.idempotency_key == idempotency_key
            )
        )
        if existing:
            response.status_code = status.HTTP_200_OK
            return {"run": run_detail(existing), "duplicate": True}
        raise HTTPException(status_code=409, detail="Could not create evaluation")

    seed_pending_events(run.id)
    background_tasks.add_task(process_evaluation, run.id)
    response.status_code = status.HTTP_202_ACCEPTED
    return {"run": run_detail(run), "duplicate": False}


@router.get("/evaluations")
def list_evaluations(
    request: Request,
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> dict:
    owner = require_owner(request)
    runs = db.scalars(
        select(EvaluationRun).where(EvaluationRun.owner_hash == owner)
        .order_by(desc(EvaluationRun.created_at)).limit(limit).offset(offset)
    ).all()
    total = db.scalar(select(func.count()).select_from(EvaluationRun).where(EvaluationRun.owner_hash == owner)) or 0
    return {"items": [run_summary(run) for run in runs], "total": total}


@router.get("/evaluations/{run_id}")
def get_evaluation(run_id: str, request: Request, db: Session = Depends(get_db)) -> dict:
    run = owned_run(db, require_owner(request), run_id)
    return run_detail(run)


@router.get("/evaluations/{run_id}/events")
def get_events(run_id: str, request: Request, db: Session = Depends(get_db)) -> dict:
    owned_run(db, require_owner(request), run_id)
    events = db.scalars(
        select(ExecutionEvent).where(ExecutionEvent.run_id == run_id).order_by(ExecutionEvent.sequence)
    ).all()
    return {"items": [event_dict(event) for event in events]}


@router.get("/evaluations/{run_id}/stream")
def stream_events(
    run_id: str, request: Request, after: int = Query(default=0, ge=0), db: Session = Depends(get_db)
) -> StreamingResponse:
    owner = require_owner(request)
    owned_run(db, owner, run_id)

    def generate():
        sequence = after
        idle_ticks = 0
        while True:
            with next(get_db()) as stream_db:
                still_owned = stream_db.scalar(
                    select(EvaluationRun).where(EvaluationRun.id == run_id, EvaluationRun.owner_hash == owner)
                )
                if not still_owned:
                    yield "event: error\ndata: {\"detail\":\"Evaluation unavailable\"}\n\n"
                    return
                events = stream_db.scalars(
                    select(ExecutionEvent).where(
                        ExecutionEvent.run_id == run_id, ExecutionEvent.sequence > sequence
                    ).order_by(ExecutionEvent.sequence)
                ).all()
                for event in events:
                    sequence = event.sequence
                    yield f"id: {event.sequence}\nevent: execution\ndata: {json.dumps(event_dict(event))}\n\n"
                terminal = still_owned.status in {"completed", "completed_with_warnings", "failed"}
            if terminal and not events:
                yield f"event: complete\ndata: {json.dumps({'run_id': run_id, 'status': still_owned.status})}\n\n"
                return
            idle_ticks += 1
            if idle_ticks % 15 == 0:
                yield f": heartbeat {datetime.utcnow().isoformat()}\n\n"
            time.sleep(0.2)

    return StreamingResponse(
        generate(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )


@router.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)) -> dict:
    owner = require_owner(request)
    base = EvaluationRun.owner_hash == owner
    total = db.scalar(select(func.count()).select_from(EvaluationRun).where(base)) or 0
    completed = db.scalar(
        select(func.count()).select_from(EvaluationRun).where(
            base, EvaluationRun.status.in_(["completed", "completed_with_warnings"])
        )
    ) or 0
    average = db.scalar(select(func.avg(EvaluationRun.overall_score)).where(base))
    warnings = db.scalar(select(func.sum(EvaluationRun.warning_count)).where(base)) or 0
    recent = db.scalars(
        select(EvaluationRun).where(base).order_by(desc(EvaluationRun.created_at)).limit(5)
    ).all()
    return {
        "total_runs": total, "completed_runs": completed,
        "average_score": round(float(average), 1) if average is not None else None,
        "privacy_warnings": int(warnings), "recent": [run_summary(run) for run in recent],
    }
