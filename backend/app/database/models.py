"""ORM models for persisted gateway evaluation data."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class RequestLog(Base):
    """One gateway request and its optional evaluation measurements."""

    __tablename__ = "request_logs"
    __table_args__ = (Index("ix_request_logs_timestamp", "timestamp"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    complexity: Mapped[str | None] = mapped_column(String(32), nullable=True)
    selected_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    final_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    cache_hit: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    context_before_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    context_after_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    context_reduction_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    escalated: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    fallback_used: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
