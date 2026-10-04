from fastapi import APIRouter


router = APIRouter()


@router.get("")
def get_metrics():
    return {
        "total_requests": 0,
        "cache_hits": 0,
        "cache_misses": 0,
        "llm_calls": 0,
        "tokens_input": 0,
        "tokens_output": 0,
        "estimated_cost": 0.0,
        "average_latency_ms": 0.0,
        "context_reduction_percent": 0.0,
        "escalations": 0,
        "fallbacks": 0,
    }