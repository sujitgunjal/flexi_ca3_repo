from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import RequestLog
from app.schemas.metrics import MetricsSummary, RequestLogResponse, RequestMetrics, TraceEventResponse
from app.services.metrics_service import (
    get_recent_requests,
    get_request,
    get_summary_metrics,
    log_request,
)
from app.services.trace_service import get_trace

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

class MetricsLogResponse(BaseModel):
    success: bool
    request_id: int


@router.post("/log", response_model=MetricsLogResponse, status_code=201)
def create_metrics_log(metrics: RequestMetrics):
    record = log_request(metrics)
    return MetricsLogResponse(success=True, request_id=record.id)


@router.get("/recent", response_model=list[RequestLogResponse])
def recent_metrics():
    return get_recent_requests()


@router.get("/summary", response_model=MetricsSummary)
def summary_metrics(baseline_tokens: int | None = Query(default=None, ge=0),
                    baseline_cost: float | None = Query(default=None, ge=0)):
    return get_summary_metrics(
        baseline_tokens=baseline_tokens, baseline_cost=baseline_cost
    )


@router.get("/{request_id}/trace", response_model=list[TraceEventResponse])
def request_trace(request_id: int):
    if get_request(request_id) is None:
        raise HTTPException(status_code=404, detail="Request metrics not found")
    return get_trace(request_id)


@router.get("/{request_id}", response_model=RequestLogResponse)
def metrics_by_id(request_id: int):
    record = get_request(request_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Request metrics not found")
    return record
