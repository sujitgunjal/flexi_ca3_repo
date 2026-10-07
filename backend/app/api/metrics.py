from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import RequestLog

router = APIRouter()


@router.get("")
def get_metrics(session: Session = Depends(get_db)):
    metrics = session.execute(
        select(
            func.count(RequestLog.id),
            func.coalesce(
                func.sum(case((RequestLog.cache_hit.is_(True), 1), else_=0)), 0
            ),
            func.coalesce(
                func.sum(case((RequestLog.cache_hit.is_(False), 1), else_=0)), 0
            ),
            func.coalesce(func.sum(RequestLog.input_tokens), 0),
            func.coalesce(func.sum(RequestLog.output_tokens), 0),
            func.coalesce(func.sum(RequestLog.estimated_cost), 0.0),
            func.avg(RequestLog.latency_ms),
            func.avg(RequestLog.context_reduction_percent),
            func.coalesce(
                func.sum(case((RequestLog.escalated.is_(True), 1), else_=0)), 0
            ),
            func.coalesce(
                func.sum(case((RequestLog.fallback_used.is_(True), 1), else_=0)), 0
            ),
        )
    ).one()

    return {
        "total_requests": metrics[0],
        "cache_hits": metrics[1],
        "cache_misses": metrics[2],
        "llm_calls": metrics[2],
        "tokens_input": metrics[3],
        "tokens_output": metrics[4],
        "estimated_cost": float(metrics[5]),
        "average_latency_ms": float(metrics[6] or 0.0),
        "context_reduction_percent": float(metrics[7] or 0.0),
        "escalations": metrics[8],
        "fallbacks": metrics[9],
    }