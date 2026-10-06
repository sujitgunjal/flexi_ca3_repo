"""Provider-independent persistence and aggregation for request metrics."""

from collections.abc import Mapping
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.database.database import SessionLocal, initialize_database
from app.database.models import RequestLog
from app.schemas.metrics import RequestMetrics
from app.services.cost_service import calculate_cost


def derive_metrics(metrics: RequestMetrics) -> RequestMetrics:
    """Fill derived values only when the caller did not supply them."""
    values = metrics.model_dump()
    if values["total_tokens"] is None and values["input_tokens"] is not None and values["output_tokens"] is not None:
        values["total_tokens"] = values["input_tokens"] + values["output_tokens"]
    before = values["context_before_tokens"]
    after = values["context_after_tokens"]
    if values["context_reduction_percent"] is None and before is not None and after is not None:
        values["context_reduction_percent"] = 0.0 if before == 0 else ((before - after) / before) * 100
    if values["estimated_cost"] is None:
        values["estimated_cost"] = calculate_cost(
            values["final_model"] or values["selected_model"],
            values["input_tokens"],
            values["output_tokens"],
        )
    return RequestMetrics.model_validate(values)


def _validated_metrics(metrics: RequestMetrics | Mapping[str, Any]) -> RequestMetrics:
    return metrics if isinstance(metrics, RequestMetrics) else RequestMetrics.model_validate(metrics)


def log_request(
    metrics: RequestMetrics | Mapping[str, Any], *, session: Session | None = None
) -> RequestLog:
    """Validate, derive and persist one request; owns its session by default."""
    record_data = derive_metrics(_validated_metrics(metrics)).model_dump()
    initialize_database()
    owns_session = session is None
    db = session or SessionLocal()
    try:
        record = RequestLog(**record_data)
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    except Exception:
        db.rollback()
        raise
    finally:
        if owns_session:
            db.close()


def get_recent_requests(limit: int = 100) -> list[RequestLog]:
    initialize_database()
    with SessionLocal() as db:
        return list(db.scalars(select(RequestLog).order_by(RequestLog.timestamp.desc(), RequestLog.id.desc()).limit(limit)))


def get_request(request_id: int) -> RequestLog | None:
    initialize_database()
    with SessionLocal() as db:
        return db.get(RequestLog, request_id)


def get_summary_metrics() -> dict[str, Any]:
    """Aggregate stored rows in SQL without loading request records in bulk."""
    initialize_database()
    with SessionLocal() as db:
        row = db.execute(
            select(
                func.count(RequestLog.id),
                func.coalesce(func.sum(RequestLog.total_tokens), 0),
                func.avg(RequestLog.latency_ms),
                func.avg(RequestLog.estimated_cost),
                func.coalesce(func.sum(case((RequestLog.cache_hit.is_(True), 1), else_=0)), 0),
                func.avg(RequestLog.quality_score),
                func.coalesce(func.sum(case((RequestLog.escalated.is_(True), 1), else_=0)), 0),
                func.coalesce(func.sum(case((RequestLog.fallback_used.is_(True), 1), else_=0)), 0),
            )
        ).one()
        usage_rows = db.execute(
            select(func.coalesce(RequestLog.final_model, RequestLog.selected_model), func.count(RequestLog.id))
            .where(func.coalesce(RequestLog.final_model, RequestLog.selected_model).is_not(None))
            .group_by(func.coalesce(RequestLog.final_model, RequestLog.selected_model))
        ).all()
    return {
        "total_requests": row[0],
        "total_tokens": row[1],
        "average_latency_ms": float(row[2] or 0),
        "average_cost": float(row[3] or 0),
        "cache_hits": row[4],
        "cache_hit_rate": (row[4] / row[0]) if row[0] else 0,
        "average_quality_score": float(row[5]) if row[5] is not None else None,
        "escalation_count": row[6],
        "fallback_count": row[7],
        "model_usage_count": {model: count for model, count in usage_rows},
    }
