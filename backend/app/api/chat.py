from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.orchestration.graph import llm_graph


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


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest):
    request_id = str(uuid4())

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

    return ChatResponse(
        request_id=request_id,
        status="success",
        message=response_text,
        note=(
            f"LangGraph selected model: {selected_model}. "
            f"Complexity: {result.get('complexity')}. "
            f"Cache hit: {result.get('cache_hit')}."
        ),
    )