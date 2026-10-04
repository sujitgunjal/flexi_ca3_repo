from app.orchestration.state import RequestState


class ContextAgent:

    def run(self, state: RequestState) -> RequestState:
        print("[ContextAgent] Optimizing context...")

        query = state.get("query", "")

        # Placeholder context optimization
        state["optimized_context"] = query

        print("[ContextAgent] Context optimization complete")

        return state