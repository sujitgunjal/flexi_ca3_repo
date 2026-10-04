from datetime import datetime, timezone

from fastapi import APIRouter


router = APIRouter()


@router.get("")
def health_check():
    return {
        "status": "healthy",
        "service": "llm-gateway",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }