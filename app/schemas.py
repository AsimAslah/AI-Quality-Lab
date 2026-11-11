from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.config import get_settings


settings = get_settings()


class RubricCriterion(BaseModel):
    id: str = Field(min_length=1, max_length=48, pattern=r"^[a-zA-Z0-9_-]+$")
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=3, max_length=500)
    weight: float = Field(ge=1, le=10)
    mode: Literal["keywords", "structure", "length", "reference", "instruction"] = "instruction"
    required_phrases: list[str] = Field(default_factory=list, max_length=12)

    @field_validator("required_phrases")
    @classmethod
    def validate_phrases(cls, values: list[str]) -> list[str]:
        cleaned = []
        for value in values:
            value = value.strip()
            if not value or len(value) > 80:
                raise ValueError("Each required phrase must contain 1–80 characters")
            cleaned.append(value)
        return cleaned


class EvaluationPreferences(BaseModel):
    use_ai: bool = False
    redact_before_ai: bool = True
    failure_mode: Literal["none", "provider_timeout", "database_error"] = "none"


class EvaluationCreate(BaseModel):
    title: str = Field(default="Untitled evaluation", min_length=2, max_length=160)
    prompt: str = Field(min_length=3, max_length=settings.max_prompt_chars)
    response: str = Field(min_length=3, max_length=settings.max_response_chars)
    reference: str | None = Field(default=None, max_length=settings.max_reference_chars)
    rubric: list[RubricCriterion] = Field(min_length=1, max_length=12)
    preferences: EvaluationPreferences = Field(default_factory=EvaluationPreferences)

    @field_validator("title", "prompt", "response")
    @classmethod
    def strip_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Must not be blank")
        return value

    @model_validator(mode="after")
    def unique_criteria(self) -> "EvaluationCreate":
        ids = [criterion.id for criterion in self.rubric]
        if len(ids) != len(set(ids)):
            raise ValueError("Rubric criterion IDs must be unique")
        return self


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    sequence: int
    stage_id: str
    event_type: str
    status: str
    occurred_at: datetime
    duration_ms: float | None
    message: str
    metadata: dict
    error_code: str | None
    error_message: str | None


class RunSummary(BaseModel):
    id: str
    title: str
    status: str
    overall_score: float | None
    warning_count: int
    current_stage: str | None
    created_at: datetime
    completed_at: datetime | None


class RunDetail(RunSummary):
    prompt: str
    response: str
    reference: str | None
    rubric: list[dict]
    preferences: dict
    report: dict | None
    error_code: str | None


class DashboardOut(BaseModel):
    total_runs: int
    completed_runs: int
    average_score: float | None
    privacy_warnings: int
    recent: list[RunSummary]
