import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from math import inf, nan
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.database import Base
from app.api.metrics import router as metrics_router
from app.schemas.metrics import RequestMetrics
from app.services import metrics_service
from app.services.cost_service import MODEL_PRICING, calculate_cost

metrics_app = FastAPI()
metrics_app.include_router(metrics_router, prefix="/metrics")


@pytest.fixture
def isolated_database(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    monkeypatch.setattr(metrics_service, "SessionLocal", factory)
    monkeypatch.setattr(metrics_service, "initialize_database", lambda: Base.metadata.create_all(engine))
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_metrics_validation_and_optional_fields():
    early = RequestMetrics(query=" Explain Docker ", complexity="medium", selected_model="cheap")
    assert early.query == "Explain Docker"
    assert early.input_tokens is None
    with pytest.raises(ValidationError):
        RequestMetrics(query="  ")
    with pytest.raises(ValidationError):
        RequestMetrics(query="valid", input_tokens=-1)
    with pytest.raises(ValidationError):
        RequestMetrics(query="valid", quality_score=6)
    with pytest.raises(ValidationError):
        RequestMetrics(query="valid", estimated_cost=inf)
    with pytest.raises(ValidationError):
        RequestMetrics(query="valid", context_reduction_percent=nan)


def test_derived_metrics_and_supplied_values_are_preserved():
    derived = metrics_service.derive_metrics(RequestMetrics(
        query="usage", input_tokens=100, output_tokens=50,
        context_before_tokens=1000, context_after_tokens=400,
    ))
    assert derived.total_tokens == 150
    assert derived.context_reduction_percent == 60
    explicit = metrics_service.derive_metrics(RequestMetrics(
        query="explicit", input_tokens=100, output_tokens=50, total_tokens=123,
        context_before_tokens=1000, context_after_tokens=400,
        context_reduction_percent=42,
    ))
    assert explicit.total_tokens == 123
    assert explicit.context_reduction_percent == 42


def test_context_reduction_zero_before_is_safe():
    result = metrics_service.derive_metrics(RequestMetrics(
        query="zero", context_before_tokens=0, context_after_tokens=0,
    ))
    assert result.context_reduction_percent == 0


def test_cost_utility_and_explicit_estimate():
    MODEL_PRICING["test-model"] = {"input": 1.0, "output": 2.0}
    try:
        assert calculate_cost("test-model", 1_000_000, 500_000) == 2.0
        assert calculate_cost("unconfigured", 1, 1) is None
    finally:
        MODEL_PRICING.pop("test-model")
    derived = metrics_service.derive_metrics(RequestMetrics(
        query="explicit cost", selected_model="cheap", input_tokens=100,
        output_tokens=50, estimated_cost=0.123,
    ))
    assert derived.estimated_cost == 0.123
    assert metrics_service.derive_metrics(RequestMetrics(
        query="unknown", selected_model="unconfigured", input_tokens=1, output_tokens=1,
    )).estimated_cost is None


def test_database_logging_retrieval_and_aggregation(isolated_database):
    with metrics_service.SessionLocal() as session:
        first = metrics_service.log_request({
            "query": "one", "selected_model": "cheap", "input_tokens": 100,
            "output_tokens": 50, "latency_ms": 100, "estimated_cost": 0.01,
            "cache_hit": True, "quality_score": 4, "escalated": False, "fallback_used": False,
        }, session=session)
        first_id = first.id
        metrics_service.log_request({
            "query": "two", "final_model": "strong", "total_tokens": 300,
            "latency_ms": 300, "estimated_cost": 0.03, "cache_hit": False,
            "quality_score": 2, "escalated": True, "fallback_used": True,
        }, session=session)
        metrics_service.log_request({"query": "three", "cache_hit": None}, session=session)

    retrieved = metrics_service.get_request(first_id)
    assert retrieved is not None
    assert retrieved.total_tokens == 150
    assert [row.query for row in metrics_service.get_recent_requests()] == ["three", "two", "one"]
    summary = metrics_service.get_summary_metrics()
    assert summary == {
        "total_requests": 3,
        "total_tokens": 450,
        "average_latency_ms": 200,
        "average_cost": 0.02,
        "cache_hits": 1,
        "cache_hit_rate": 1 / 3,
        "average_quality_score": 3,
        "escalation_count": 1,
        "fallback_count": 1,
        "model_usage_count": {"cheap": 1, "strong": 1},
    }


def test_empty_summary(isolated_database):
    assert metrics_service.get_summary_metrics() == {
        "total_requests": 0, "total_tokens": 0, "average_latency_ms": 0,
        "average_cost": 0, "cache_hits": 0, "cache_hit_rate": 0,
        "average_quality_score": None, "escalation_count": 0,
        "fallback_count": 0, "model_usage_count": {},
    }


def test_metrics_api_log_recent_lookup_and_validation(isolated_database, monkeypatch):
    client = TestClient(metrics_app)
    body = {
        "query": "Explain Docker", "complexity": "simple", "selected_model": "cheap",
        "input_tokens": 100, "output_tokens": 150, "latency_ms": 500, "cache_hit": False,
    }
    response = client.post("/metrics/log", json=body)
    assert response.status_code == 201
    logged = response.json()
    assert logged["success"] is True
    request_id = logged["request_id"]
    assert client.get("/metrics/recent").json()[0]["id"] == request_id
    assert client.get(f"/metrics/{request_id}").json()["total_tokens"] == 250
    assert client.get("/metrics").json()["total_requests"] == 1
    assert client.get("/metrics/99999").status_code == 404
    assert client.post("/metrics/log", json={"query": "bad", "input_tokens": -2}).status_code == 422
