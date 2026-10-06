from app.orchestration.state import RequestState


class RouterAgent:

    def run(self, state: RequestState) -> RequestState:
        print("[RouterAgent] Applying the routing decision...")

        selected_model = state.get("selected_model")
        routing_reason = state.get("routing_reason")

        if selected_model and routing_reason:
            print(f"[RouterAgent] Selected model: {selected_model}")
            print(f"[RouterAgent] Reason: {routing_reason}")
            return state

        complexity = state.get("complexity", "medium")
        if complexity in {"complex", "high"}:
            selected_model = "strong"
        elif complexity == "simple":
            selected_model = "local"
        else:
            selected_model = "cheap"

        state["selected_model"] = selected_model
        state["routing_reason"] = (
            "Decision layer did not supply a route, "
            f"so complexity '{complexity}' mapped to '{selected_model}'"
        )
        print(f"[RouterAgent] Selected model: {selected_model}")
        return state
