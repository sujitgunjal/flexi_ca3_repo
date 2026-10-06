from app.decision.base import DecisionProviderError
from app.decision.service import DecisionService
from app.orchestration.state import RequestState


class ComplexityAgent:

    def __init__(self, service: DecisionService | None = None):
        self.service = service or DecisionService()

    def run(self, state: RequestState) -> RequestState:
        print("[ComplexityAgent] Requesting a structured decision...")
        query = state.get("query", "")

        try:
            decision = self.service.decide(query)
        except DecisionProviderError as exc:
            raise RuntimeError(str(exc)) from exc

        payload = decision.model_dump()
        state["complexity"] = decision.complexity.label
        state["reasoning"] = decision.reasoning.label
        state["context_requirement"] = decision.context.label
        state["selected_model"] = decision.selected_model
        state["routing_reason"] = decision.routing_reason
        state["uncertain"] = decision.uncertain
        state["decision"] = payload

        print(
            "[ComplexityAgent] "
            f"complexity={decision.complexity.label} "
            f"reasoning={decision.reasoning.label} "
            f"context={decision.context.label}"
        )
        return state
