from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


def payload(**overrides):
    value = {
        "title": "Privacy-aware support answer",
        "prompt": "Write a concise support response and mention the privacy limitation.",
        "response": "## Answer\n\nWe can help with your request. Privacy is important, so remove personal data before sharing it.",
        "reference": "A safe support response should explain the request and privacy limitation.",
        "rubric": [
            {
                "id": "required",
                "name": "Required language",
                "description": "Mention the privacy limitation",
                "weight": 8,
                "mode": "keywords",
                "required_phrases": ["privacy"],
            },
            {
                "id": "structure",
                "name": "Clear structure",
                "description": "Use readable structure",
                "weight": 4,
                "mode": "structure",
                "required_phrases": [],
            },
        ],
        "preferences": {"use_ai": False, "redact_before_ai": True, "failure_mode": "none"},
    }
    value.update(overrides)
    return value


def create(client: TestClient, body=None, key=None):
    return client.post(
        "/api/evaluations",
        json=body or payload(),
        headers={"Idempotency-Key": key or str(uuid.uuid4())},
    )


def test_valid_submission_persists_report_and_real_events(client):
    response = create(client)
    assert response.status_code == 202
    run = response.json()["run"]

    restored = client.get(f"/api/evaluations/{run['id']}")
    assert restored.status_code == 200
    detail = restored.json()
    assert detail["status"] in {"completed", "completed_with_warnings"}
    assert detail["report"]["overall_score"] > 0
    assert detail["prompt"] == payload()["prompt"]

    events = client.get(f"/api/evaluations/{run['id']}/events").json()["items"]
    sequences = [event["sequence"] for event in events]
    assert sequences == sorted(sequences)
    assert len(sequences) == len(set(sequences))
    assert {event["stage_id"] for event in events} == {
        "validate_input", "persist_request", "analyze_response", "privacy_scan",
        "rubric_evaluation", "ai_evaluation", "aggregate_results", "persist_report",
    }
    measured = [event["duration_ms"] for event in events if event["event_type"] == "stage.completed"]
    assert measured and all(value is not None and value >= 0 for value in measured)


def test_invalid_submission_is_actionable_and_not_persisted(client):
    invalid = payload(response="")
    response = create(client, invalid)
    assert response.status_code == 422
    assert response.json()["detail"].startswith("Please correct")
    assert any(item["field"] == "response" for item in response.json()["errors"])
    assert client.get("/api/evaluations").json()["total"] == 0


def test_duplicate_idempotency_key_returns_original_without_reexecution(client):
    key = "same-request-12345"
    first = create(client, key=key)
    second = create(client, key=key)
    assert first.status_code == 202
    assert second.status_code == 200
    assert second.json()["duplicate"] is True
    assert first.json()["run"]["id"] == second.json()["run"]["id"]
    assert client.get("/api/evaluations").json()["total"] == 1


def test_event_and_run_isolation_between_browser_owners(client):
    run_id = create(client).json()["run"]["id"]
    with TestClient(app) as stranger:
        stranger.get("/api/meta")
        assert stranger.get(f"/api/evaluations/{run_id}").status_code == 404
        assert stranger.get(f"/api/evaluations/{run_id}/events").status_code == 404
        assert stranger.get("/api/evaluations").json()["total"] == 0


def test_workspace_key_allows_authorized_access_from_another_device(client):
    response = create(client)
    run_id = response.json()["run"]["id"]
    access = client.get("/api/workspace-access")
    workspace_key = access.json()["key"]
    assert access.headers["cache-control"] == "no-store"
    assert workspace_key == client.cookies.get(get_settings().cookie_name)
    with TestClient(app) as authorized_device:
        restored = authorized_device.get(
            f"/api/evaluations/{run_id}", headers={"X-Workspace-Key": workspace_key}
        )
        assert restored.status_code == 200
        assert restored.json()["title"] == payload()["title"]


def test_invalid_workspace_key_is_rejected(client):
    response = client.get("/api/dashboard", headers={"X-Workspace-Key": "too-short"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid workspace access key"


def test_privacy_event_contains_category_but_not_raw_sensitive_value(client):
    sensitive = "Contact person@example.com and token sk-supersecret123456789."
    run_id = create(client, payload(response=sensitive)).json()["run"]["id"]
    events = client.get(f"/api/evaluations/{run_id}/events").json()["items"]
    serialized = str(events)
    assert "email" in serialized
    assert "api_key_candidate" in serialized
    assert "person@example.com" not in serialized
    assert "sk-supersecret123456789" not in serialized


def test_dashboard_and_history_restore_persisted_state(client):
    run_id = create(client).json()["run"]["id"]
    history = client.get("/api/evaluations").json()
    dashboard = client.get("/api/dashboard").json()
    assert history["items"][0]["id"] == run_id
    assert dashboard["total_runs"] == 1
    assert dashboard["completed_runs"] == 1
    assert dashboard["average_score"] is not None


def test_provider_timeout_retries_and_recovers_with_deterministic_fallback(client, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "enable_failure_testing", True)
    monkeypatch.setattr(settings, "openai_api_key", "test-key-not-sent")
    body = payload(preferences={"use_ai": True, "redact_before_ai": True, "failure_mode": "provider_timeout"})
    run_id = create(client, body).json()["run"]["id"]
    detail = client.get(f"/api/evaluations/{run_id}").json()
    events = client.get(f"/api/evaluations/{run_id}/events").json()["items"]
    ai_events = [event for event in events if event["stage_id"] == "ai_evaluation"]
    assert any(event["status"] == "retrying" for event in ai_events)
    assert any(event["status"] == "recovered" for event in ai_events)
    assert detail["report"]["model_evaluation"] is None
    assert "deterministic fallback" in " ".join(detail["report"]["limitations"])


def test_database_write_failure_preserves_input_and_never_claims_completion(client, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "enable_failure_testing", True)
    body = payload(preferences={"use_ai": False, "redact_before_ai": True, "failure_mode": "database_error"})
    run_id = create(client, body).json()["run"]["id"]
    detail = client.get(f"/api/evaluations/{run_id}").json()
    events = client.get(f"/api/evaluations/{run_id}/events").json()["items"]
    report_events = [event for event in events if event["stage_id"] == "persist_report"]
    assert detail["status"] == "failed"
    assert detail["report"] is None
    assert detail["prompt"] == body["prompt"]
    assert any(event["status"] == "failed" for event in report_events)
    assert not any(event["event_type"] == "stage.completed" for event in report_events)


def test_sse_resume_uses_last_event_id_without_replaying_old_events(client):
    run_id = create(client).json()["run"]["id"]
    events = client.get(f"/api/evaluations/{run_id}/events").json()["items"]
    checkpoint = events[7]["sequence"]
    response = client.get(
        f"/api/evaluations/{run_id}/stream?after=0",
        headers={"Last-Event-ID": str(checkpoint)},
    )
    ids = [int(line.removeprefix("id: ")) for line in response.text.splitlines() if line.startswith("id: ")]
    assert response.status_code == 200
    assert ids
    assert all(event_id > checkpoint for event_id in ids)
    assert "event: complete" in response.text


def test_health_checks_database(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}
