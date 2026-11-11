from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    __table_args__ = (
        UniqueConstraint("owner_hash", "idempotency_key", name="uq_owner_idempotency"),
        Index("ix_runs_owner_created", "owner_hash", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued", index=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    rubric: Mapped[list] = mapped_column(JSON, nullable=False)
    preferences: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    report: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    warning_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_stage: Mapped[str | None] = mapped_column(String(48), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    events: Mapped[list["ExecutionEvent"]] = relationship(
        back_populates="run", cascade="all, delete-orphan", order_by="ExecutionEvent.sequence"
    )


class ExecutionEvent(Base):
    __tablename__ = "execution_events"
    __table_args__ = (
        UniqueConstraint("run_id", "sequence", name="uq_event_run_sequence"),
        Index("ix_events_run_time", "run_id", "occurred_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    stage_id: Mapped[str] = mapped_column(String(48), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    message: Mapped[str] = mapped_column(String(300), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(300), nullable=True)

    run: Mapped[EvaluationRun] = relationship(back_populates="events")
