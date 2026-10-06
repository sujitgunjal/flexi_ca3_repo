"""Validation and response schemas for request metrics."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RequestMetrics(BaseModel):
    """Measurements available at any stage of a gateway request."""

    model_config = ConfigDict(
        extra="forbid", str_strip_whitespace=True, allow_inf_nan=False
    )

    query: str = Field(min_length=1)
    complexity: str | None = Field(default=None, max_length=32)
    selected_model: str | None = Field(default=None, max_length=128)
    final_model: str | None = Field(default=None, max_length=128)
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
    latency_ms: float | None = Field(default=None, ge=0)
    estimated_cost: float | None = Field(default=None, ge=0)
    cache_hit: bool | None = None
    context_before_tokens: int | None = Field(default=None, ge=0)
    context_after_tokens: int | None = Field(default=None, ge=0)
    context_reduction_percent: float | None = None
    quality_score: float | None = Field(default=None, ge=1, le=5)
    quality_status: str | None = Field(default=None, max_length=32)
    escalated: bool | None = None
    fallback_used: bool | None = None

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        if not value:
            raise ValueError("query must not be blank")
        return value


class RequestLogResponse(RequestMetrics):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class MetricsSummary(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    total_requests: int
    total_tokens: int
    average_latency_ms: float
    average_cost: float
    cache_hits: int
    cache_hit_rate: float
    average_quality_score: float | None
    escalation_count: int
    fallback_count: int
    model_usage_count: dict[str, int]
