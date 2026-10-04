from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel, Field


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
    return ChatResponse(
        request_id=str(uuid4()),
        status="accepted",
        message=request.message,
        note=(
            "Day 1 gateway is running. "
            "LLM orchestration will be connected in later phases."
        ),
    )