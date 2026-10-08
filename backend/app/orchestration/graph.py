from langgraph.graph import END, START, StateGraph

from app.agents.cache_agent import CacheAgent
from app.agents.context_agent import ContextAgent
from app.agents.decision_agent import ComplexityAgent
from app.agents.generate_agent import GenerateAgent
from app.agents.quality_agent import QualityAgent
from app.agents.router_agent import RouterAgent
from app.orchestration.state import RequestState


cache_agent = CacheAgent()
complexity_agent = ComplexityAgent()
context_agent = ContextAgent()
router_agent = RouterAgent()
generate_agent = GenerateAgent()
quality_agent = QualityAgent()


def build_graph():

    graph = StateGraph(RequestState)

    # Add nodes
    graph.add_node("cache", cache_agent.run)
    graph.add_node("complexity", complexity_agent.run)
    graph.add_node("context", context_agent.run)
    graph.add_node("router", router_agent.run)
    graph.add_node("generate", generate_agent.run)
    graph.add_node("quality", quality_agent.run)

    # Connect nodes
    graph.add_edge(START, "cache")
    graph.add_conditional_edges(
        "cache", lambda state: END if state.get("cached_response") else "complexity",
        {"complexity": "complexity", END: END},
    )
    graph.add_edge("complexity", "context")
    graph.add_edge("context", "router")
    graph.add_edge("router", "generate")
    graph.add_edge("generate", "quality")
    graph.add_edge("quality", END)

    return graph.compile()


llm_graph = build_graph()
