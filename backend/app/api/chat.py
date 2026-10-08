from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.orchestration.graph import llm_graph
from app.providers.registry import get_tier
from app.cache.redis_cache import RedisError, cache, generate_cache_key
from app.services.metrics_service import log_request


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
    conversation_id: str
    status: str
    message: str
    note: str
    decision: dict | None = None


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest):
    request_id = str(uuid4())
    conversation_id = request.conversation_id or str(uuid4())
    metric_record = log_request({"query": request.message})

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
        "metrics_request_id": metric_record.id,
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

    cache_key = result.get("cache_key") or generate_cache_key(request.message)
    if not result.get("cache_hit") and not result.get("cache_unavailable"):
        try:
            cache.set(cache_key, {
                "response": response_text,
                "selected_model": result.get("selected_model", "cheap"),
                "decision": result.get("decision"),
                "complexity": result.get("complexity"),
                "uncertain": result.get("uncertain"),
                "routing_reason": result.get("routing_reason"),
            })
        except RedisError:
            # Cache write failure does not turn a successful model response into an error.
            import logging
            logging.getLogger(__name__).exception("Redis cache write failed; response returned uncached")
            from app.services.metrics_service import record_cache_event
            record_cache_event(metric_record.id, False, cache_key,
                               fallback_used=True)

    decision = result.get("decision") or {}
    complexity = decision.get("complexity", {})
    try:
        answer_model = get_tier(selected_model).model
    except ValueError:
        answer_model = selected_model

    return ChatResponse(
        request_id=request_id,
        conversation_id=conversation_id,
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
