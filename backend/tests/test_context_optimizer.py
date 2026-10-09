from app.agents.context_agent import ContextAgent
from app.context.embeddings import HashEmbedder
from app.context.selector import select_relevant_messages


HISTORY = [
    {"role": "user", "content": "How do I bake sourdough bread at home?"},
    {"role": "assistant", "content": "Use a starter, stretch the dough, and bake it in a Dutch oven."},
    {"role": "user", "content": "Redis stores cache entries as keys with a TTL."},
    {"role": "assistant", "content": "A Redis TTL expires the cached response automatically."},
]


def test_selector_keeps_messages_related_to_the_query():
    embedder = HashEmbedder()
    query = "How does Redis expire a cache key?"
    embeddings = embedder.embed([query] + [item["content"] for item in HISTORY])

    selected = select_relevant_messages(query, HISTORY, embeddings, token_limit=80, message_cap=2)

    assert selected
    assert all("sourdough" not in item["content"].lower() for item in selected)
    assert any("redis" in item["content"].lower() for item in selected)
    positions = [
        next(index for index, message in enumerate(HISTORY) if message["content"] == item["content"])
        for item in selected
    ]
    assert positions == sorted(positions)


def test_low_context_requirement_keeps_fewer_tokens_than_high():
    agent = ContextAgent(embedder=HashEmbedder())
    query = "How does Redis expire a cache key?"

    low = agent.run({
        "query": query,
        "conversation_history": HISTORY,
        "context_requirement": "low",
    })
    high = agent.run({
        "query": query,
        "conversation_history": HISTORY * 6,
        "context_requirement": "high",
    })

    assert low["messages_selected"] <= 2
    assert low["optimized_token_count"] <= low["original_token_count"]
    assert low["context_reduction_percent"] > 0
    assert high["messages_selected"] >= low["messages_selected"]
    assert "user: " + query in low["optimized_context"]


def test_empty_history_keeps_the_query_only():
    result = ContextAgent(embedder=HashEmbedder()).run({
        "query": "What is DNS?",
        "conversation_history": [],
        "context_requirement": "medium",
    })

    assert result["optimized_context"] == "What is DNS?"
    assert result["optimized_history"] == []
    assert result["messages_selected"] == 0
    assert result["context_reduction_percent"] == 0
