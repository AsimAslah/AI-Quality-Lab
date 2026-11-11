from __future__ import annotations

import re


PATTERNS: dict[str, re.Pattern[str]] = {
    "email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    "phone": re.compile(r"(?<!\w)(?:\+?\d{1,3}[ .-]?)?(?:\(?\d{2,4}\)?[ .-]?)?\d{3}[ .-]?\d{4}(?!\w)"),
    "payment_card_candidate": re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
    "api_key_candidate": re.compile(r"\b(?:sk|rk|pk)[-_][A-Za-z0-9_-]{12,}\b|\bAIza[0-9A-Za-z_-]{20,}\b"),
    "ip_address": re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"),
}


def scan_pii(text: str) -> dict:
    findings: list[dict] = []
    for category, pattern in PATTERNS.items():
        matches = list(pattern.finditer(text))
        if matches:
            findings.append(
                {
                    "category": category,
                    "count": len(matches),
                    "severity": "high" if category in {"payment_card_candidate", "api_key_candidate"} else "medium",
                    "positions": [{"start": match.start(), "end": match.end()} for match in matches[:10]],
                    "note": "Pattern match only; review context before treating as sensitive data.",
                }
            )
    return {
        "finding_count": sum(item["count"] for item in findings),
        "categories": [item["category"] for item in findings],
        "findings": findings,
    }


def redact_pii(text: str) -> str:
    redacted = text
    for category, pattern in PATTERNS.items():
        redacted = pattern.sub(f"[{category.upper()} REDACTED]", redacted)
    return redacted
