from app.evaluator import aggregate_results, analyze_text, score_rubric
from app.pii import redact_pii, scan_pii
from app.security import redact_error


def test_weighted_scoring_uses_configured_weights():
    assert aggregate_results([
        {"score": 100, "weight": 9}, {"score": 0, "weight": 1}
    ]) == 90.0


def test_reference_check_is_labeled_heuristic():
    rubric = [{"id": "ref", "name": "Reference", "description": "Compare", "weight": 5, "mode": "reference", "required_phrases": []}]
    response = "The capital of France is Paris."
    results = score_rubric(rubric, "What is the capital?", response, "Paris is the capital of France.", analyze_text(response))
    assert results[0]["method"] == "heuristic"
    assert any("not proof" in note for note in results[0]["limitations"])


def test_sensitive_data_is_detected_and_redacted():
    text = "Email me at user@example.com with sk-abcdefghijklmnop"
    scan = scan_pii(text)
    assert scan["finding_count"] == 2
    redacted = redact_pii(text)
    assert "user@example.com" not in redacted
    assert "sk-abcdefghijklmnop" not in redacted


def test_error_redaction_hides_secrets_and_database_urls():
    safe = redact_error("api_key=secret-value postgresql://user:password@host/db")
    assert "secret-value" not in safe
    assert "password@host" not in safe
