from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import RequestLog

router = APIRouter()


class RequestRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    query: str
    complexity: str | None = None
    selected_model: str | None = None
    final_model: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    latency_ms: float | None = None
    estimated_cost: float | None = None
    cache_hit: bool | None = None
    escalated: bool | None = None


@router.get("", response_model=list[RequestRecordResponse])
def get_requests(
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_db),
):
    return session.scalars(
        select(RequestLog)
        .order_by(RequestLog.timestamp.desc(), RequestLog.id.desc())
        .limit(limit)
    ).all()
