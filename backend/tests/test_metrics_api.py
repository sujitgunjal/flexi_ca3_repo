from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.api.metrics import get_metrics
from app.api.requests import get_requests
from app.database.database import Base, _create_engine, initialize_database
from app.database.models import RequestLog


def test_metrics_and_requests_return_persisted_records():
    test_engine = _create_engine("sqlite:///:memory:")
    try:
        initialize_database(test_engine)
        with Session(test_engine) as session:
            session.add_all(
                [
                    RequestLog(
                        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
                        query="First request",
                        complexity="medium",
                        selected_model="cheap",
                        input_tokens=12,
                        output_tokens=8,
                        estimated_cost=0.03,
                        latency_ms=120.0,
                        cache_hit=False,
                        context_reduction_percent=10.0,
                    ),
                    RequestLog(
                        timestamp=datetime(2026, 1, 2, tzinfo=timezone.utc),
                        query="Cached request",
                        cache_hit=True,
                        latency_ms=40.0,
                        escalated=True,
                    ),
                ]
            )
            session.commit()

            metrics = get_metrics(session)
            requests = get_requests(limit=100, session=session)

        assert metrics == {
            "total_requests": 2,
            "cache_hits": 1,
            "cache_misses": 1,
            "llm_calls": 1,
            "tokens_input": 12,
            "tokens_output": 8,
            "estimated_cost": 0.03,
            "average_latency_ms": 80.0,
            "context_reduction_percent": 10.0,
            "escalations": 1,
            "fallbacks": 0,
        }
        assert [request.query for request in requests] == [
            "Cached request",
            "First request",
        ]
        assert requests[0].cache_hit is True
    finally:
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()
