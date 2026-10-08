from types import SimpleNamespace
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import chat as chat_api


def create_test_client(monkeypatch):
    captured_states = []

    class TestCache:
        def set(self, *_args, **_kwargs):
            return None

    monkeypatch.setattr(chat_api, "cache", TestCache())
    monkeypatch.setattr(chat_api, "log_request", lambda _metrics: SimpleNamespace(id=1))

    def invoke(state):
        captured_states.append(state)
        return {
            "selected_model": "cheap",
            "response": "Test response",
            "decision": {
                "provider": "test-provider",
                "decision_model": "test-decision-model",
                "complexity": {
                    "raw_confidence": 0.9,
                    "calibrated_confidence": 0.85,
                },
            },
            "complexity": "low",
            "uncertain": False,
            "routing_reason": "test routing decision",
        }

    monkeypatch.setattr(chat_api.llm_graph, "invoke", invoke)
    monkeypatch.setattr(
        chat_api,
        "get_tier",
        lambda _: SimpleNamespace(model="test-answer-model"),
    )

    app = FastAPI()
    app.include_router(chat_api.router, prefix="/chat")
    return TestClient(app), captured_states


def test_chat_generates_conversation_id_when_not_supplied(monkeypatch):
    client, captured_states = create_test_client(monkeypatch)

    response = client.post("/chat", json={"message": "What is Docker?"})

    assert response.status_code == 200
    body = response.json()
    UUID(body["conversation_id"])
    UUID(body["request_id"])
    assert body["status"] == "success"
    assert body["message"] == "Test response"
    assert body["decision"]["provider"] == "test-provider"
    assert body["note"]
    assert captured_states[0]["conversation_history"] == []


def test_chat_preserves_supplied_conversation_id(monkeypatch):
    client, _ = create_test_client(monkeypatch)

    response = client.post(
        "/chat",
        json={
            "conversation_id": "123",
            "message": "Explain the previous architecture",
        },
    )

    assert response.status_code == 200
    assert response.json()["conversation_id"] == "123"


def test_chat_passes_history_with_supplied_conversation_id(monkeypatch):
    client, captured_states = create_test_client(monkeypatch)
    history = [
        {"role": "user", "content": "What is an LLM gateway?"},
        {"role": "assistant", "content": "An LLM gateway is..."},
    ]

    response = client.post(
        "/chat",
        json={
            "conversation_id": "123",
            "message": "Explain the previous architecture",
            "history": history,
        },
    )

    assert response.status_code == 200
    assert response.json()["conversation_id"] == "123"
    assert captured_states[0]["conversation_history"] == history
