from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.schemas.metrics import MetricsSummary, RequestLogResponse, RequestMetrics
from app.services.metrics_service import (
    get_recent_requests,
    get_request,
    get_summary_metrics,
    log_request,
)

router = APIRouter()


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


@router.get("", response_model=MetricsSummary)
@router.get("/summary", response_model=MetricsSummary)
def summary_metrics():
    return get_summary_metrics()


@router.get("/{request_id}", response_model=RequestLogResponse)
def metrics_by_id(request_id: int):
    record = get_request(request_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Request metrics not found")
    return record
