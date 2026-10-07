from typing import List

from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter()


class ModelInfo(BaseModel):
    id: str
    tier: str
    provider: str
    available: bool


MODELS: List[ModelInfo] = [
    ModelInfo(
        id="local",
        tier="local",
        provider="ollama",
        available=False,
    ),
    ModelInfo(
        id="cheap",
        tier="cheap",
        provider="cloud",
        available=False,
    ),
    ModelInfo(
        id="strong",
        tier="strong",
        provider="cloud",
        available=False,
    ),
]


@router.get("", response_model=List[ModelInfo])
def list_models():
    return MODELS