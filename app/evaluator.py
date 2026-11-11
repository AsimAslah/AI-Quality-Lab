from __future__ import annotations

import math
import re
from collections import Counter


WORD_RE = re.compile(r"[A-Za-z0-9']+")
STOP_WORDS = {
    "the", "and", "that", "with", "this", "from", "your", "have", "will", "for", "are", "was", "were",
    "into", "about", "should", "would", "could", "must", "then", "than", "when", "what", "how", "why",
}


def tokens(text: str) -> list[str]:
    return [word.lower() for word in WORD_RE.findall(text)]


def analyze_text(text: str) -> dict:
    words = tokens(text)
    paragraphs = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]
    headings = len(re.findall(r"(?m)^#{1,6}\s+|^[A-Z][^\n]{2,60}:$", text))
    bullets = len(re.findall(r"(?m)^\s*(?:[-*+] |\d+[.)] )", text))
    return {
        "character_count": len(text),
        "word_count": len(words),
        "sentence_count": len(sentences),
        "paragraph_count": len(paragraphs),
        "heading_count": headings,
        "bullet_count": bullets,
        "average_sentence_words": round(len(words) / max(1, len(sentences)), 1),
    }


def _overlap_score(source: str, target: str) -> tuple[float, list[str]]:
    source_terms = {t for t in tokens(source) if len(t) > 3 and t not in STOP_WORDS}
    target_terms = {t for t in tokens(target) if len(t) > 3 and t not in STOP_WORDS}
    if not source_terms:
        return 50.0, []
    overlap = sorted(source_terms & target_terms)
    return min(100.0, 100 * len(overlap) / len(source_terms)), overlap[:8]


def evaluate_criterion(criterion: dict, prompt: str, response: str, reference: str | None, analysis: dict) -> dict:
    mode = criterion["mode"]
    required = criterion.get("required_phrases", [])
    lower_response = response.lower()
    evidence: list[str] = []
    limitations: list[str] = []
    label = "deterministic"

    if mode == "keywords":
        found = [phrase for phrase in required if phrase.lower() in lower_response]
        score = 100.0 if not required else 100 * len(found) / len(required)
        evidence.append(f"Found {len(found)} of {len(required)} required phrases")
        if found:
            evidence.append("Matched: " + ", ".join(found[:5]))
    elif mode == "structure":
        components = [analysis["paragraph_count"] > 1, analysis["bullet_count"] > 0, analysis["heading_count"] > 0]
        score = 40 + 20 * sum(components)
        evidence.append(
            f"{analysis['paragraph_count']} paragraphs, {analysis['bullet_count']} list items, {analysis['heading_count']} headings"
        )
        limitations.append("Structure is measured mechanically; suitability depends on the task.")
    elif mode == "length":
        count = analysis["word_count"]
        if count < 20:
            score = max(10.0, count * 3.5)
        elif count <= 800:
            score = 100.0
        else:
            score = max(50.0, 100 - math.log10(count / 800) * 45)
        evidence.append(f"Response contains {count} words")
        limitations.append("Length alone does not establish completeness or concision.")
    elif mode == "reference":
        label = "heuristic"
        if reference:
            score, overlap = _overlap_score(reference, response)
            evidence.append(f"Reference-term coverage: {score:.0f}%")
            if overlap:
                evidence.append("Shared terms: " + ", ".join(overlap))
            limitations.append("Lexical overlap is not proof of factual accuracy or semantic equivalence.")
        else:
            score = 50.0
            evidence.append("No reference was supplied; neutral score applied")
            limitations.append("Reference-based assessment was unavailable.")
    else:
        label = "heuristic"
        score, overlap = _overlap_score(prompt + " " + criterion["description"], response)
        score = min(100.0, 35 + score * 0.75)
        evidence.append(f"Instruction-cue coverage: {score:.0f}%")
        if overlap:
            evidence.append("Observed cues: " + ", ".join(overlap))
        limitations.append("Keyword coverage cannot prove that instructions were followed correctly.")

    if required and mode != "keywords":
        missing = [phrase for phrase in required if phrase.lower() not in lower_response]
        phrase_score = 100 * (len(required) - len(missing)) / len(required)
        score = score * 0.7 + phrase_score * 0.3
        evidence.append(f"Required phrase check: {len(required) - len(missing)}/{len(required)}")

    return {
        "criterion_id": criterion["id"],
        "name": criterion["name"],
        "weight": criterion["weight"],
        "score": round(max(0.0, min(100.0, score)), 1),
        "method": label,
        "evidence": evidence,
        "limitations": limitations,
    }


def score_rubric(rubric: list[dict], prompt: str, response: str, reference: str | None, analysis: dict) -> list[dict]:
    return [evaluate_criterion(item, prompt, response, reference, analysis) for item in rubric]


def aggregate_results(results: list[dict]) -> float:
    total_weight = sum(float(result["weight"]) for result in results)
    if not total_weight:
        return 0.0
    return round(sum(float(result["score"]) * float(result["weight"]) for result in results) / total_weight, 1)


def response_keywords(text: str, limit: int = 8) -> list[str]:
    counts = Counter(t for t in tokens(text) if len(t) > 3 and t not in STOP_WORDS)
    return [term for term, _ in counts.most_common(limit)]
