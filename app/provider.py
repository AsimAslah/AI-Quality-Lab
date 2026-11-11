from __future__ import annotations

import json
from dataclasses import dataclass

import httpx

from app.config import Settings


class ProviderError(RuntimeError):
    pass


@dataclass
class ProviderResult:
    criteria: list[dict]
    summary: str
    usage: dict
    model: str


class OpenAICompatibleProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def evaluate(self, prompt: str, response: str, reference: str | None, rubric: list[dict]) -> ProviderResult:
        if not self.settings.openai_api_key:
            raise ProviderError("AI provider is not configured")
        system = (
            "You are an evaluation assistant. Return JSON only with keys criteria and summary. "
            "criteria must contain criterion_id, score (0-100), and short evidence. "
            "Do not claim certainty or factual verification unless the supplied reference directly supports it."
        )
        user = json.dumps({"prompt": prompt, "response": response, "reference": reference, "rubric": rubric})
        try:
            with httpx.Client(timeout=self.settings.provider_timeout_seconds) as client:
                http_response = client.post(
                    f"{self.settings.openai_base_url.rstrip('/')}/chat/completions",
                    headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
                    json={
                        "model": self.settings.openai_model,
                        "temperature": 0,
                        "response_format": {"type": "json_object"},
                        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                    },
                )
                http_response.raise_for_status()
            payload = http_response.json()
            content = payload["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            if not isinstance(parsed.get("criteria"), list) or not isinstance(parsed.get("summary"), str):
                raise ProviderError("Provider returned an invalid evaluation schema")
            return ProviderResult(
                criteria=parsed["criteria"],
                summary=parsed["summary"][:1000],
                usage=payload.get("usage", {}),
                model=payload.get("model", self.settings.openai_model),
            )
        except (httpx.HTTPError, KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
            raise ProviderError(str(exc)) from exc
