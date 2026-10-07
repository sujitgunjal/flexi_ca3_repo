from time import perf_counter
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError

from app.database.database import SessionLocal
from app.database.models import RequestLog
from app.orchestration.graph import llm_graph
from app.providers.registry import get_tier


router = APIRouter()


class ChatMessage(BaseModel):
    role: str = Field(
        ...,
        description="Message role: user, assistant, or system",
    )
    content: str


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        description="Current user message",
    )
    conversation_id: Optional[str] = None
    history: List[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    request_id: str
    status: str
    message: str
    note: str
    decision: dict | None = None


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest):
    request_id = str(uuid4())
    started_at = perf_counter()

    # Convert API request into LangGraph state
    initial_state = {
        "query": request.message,
        "conversation_history": [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in request.history
        ],
        "cache_hit": False,
        "cost": 0.0,
        "latency": 0.0,
    }

    try:
        # Generate calls the routed model inside the graph.
        result = llm_graph.invoke(initial_state)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"LLM provider error: {str(exc)}",
        )

    selected_model = result.get("selected_model", "cheap")
    response_text = result.get("response") or ""

    if not response_text:
        raise HTTPException(
            status_code=502,
            detail="LLM provider returned an empty response",
        )

    try:
        with SessionLocal() as session:
            session.add(
                RequestLog(
                    query=request.message,
                    complexity=result.get("complexity"),
                    selected_model=selected_model,
                    final_model=result.get("final_model", selected_model),
                    latency_ms=(perf_counter() - started_at) * 1000,
                    cache_hit=bool(result.get("cache_hit", False)),
                    escalated=bool(result.get("escalation", False)),
                    fallback_used=bool(result.get("fallback_used", False)),
                )
            )
            session.commit()
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail="The response was generated, but the request could not be recorded.",
        ) from exc

    decision = result.get("decision") or {}
    complexity = decision.get("complexity", {})
    try:
        answer_model = get_tier(selected_model).model
    except ValueError:
        answer_model = selected_model

    return ChatResponse(
        request_id=request_id,
        status="success",
        message=response_text,
        decision=decision or None,
        note=(
            f"Decision engine: {decision.get('provider', 'n/a')} "
            f"({decision.get('decision_model', 'n/a')}). "
            f"Answer model: {selected_model} ({answer_model}). "
            f"Complexity: {result.get('complexity')} "
            f"(raw confidence {complexity.get('raw_confidence')}, "
            f"calibrated confidence {complexity.get('calibrated_confidence')}). "
            f"Uncertain: {result.get('uncertain')}. "
            f"Reason: {result.get('routing_reason')}."
        ),
    )