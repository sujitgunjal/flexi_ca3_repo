from app.orchestration.graph import llm_graph


initial_state = {
    "query": "Explain artificial intelligence",
    "conversation_history": [],
    "cache_hit": False,
    "cost": 0.0,
    "latency": 0.0
}


result = llm_graph.invoke(initial_state)


print("\n========== FINAL STATE ==========")

for key, value in result.items():
    print(f"{key}: {value}")