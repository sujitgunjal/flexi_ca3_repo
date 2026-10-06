from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.decision.base import DecisionProviderError
from app.decision.schemas.decision import DecisionResponse
from app.decision.service import DecisionService


router = APIRouter()


class DecisionRequest(BaseModel):
    query: str = Field(..., min_length=1)
    request_id: str | None = None


@router.post("", response_model=DecisionResponse)
def create_decision(request: DecisionRequest):
    try:
        return DecisionService().decide(
            request.query,
            request_id=request.request_id,
        )
    except DecisionProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
