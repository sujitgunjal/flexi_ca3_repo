from app.orchestration.state import RequestState


class RouterAgent:

    def run(self, state: RequestState) -> RequestState:
        print("[RouterAgent] Selecting model...")

        complexity = state.get("complexity", "medium")

        # Placeholder routing logic
        if complexity == "high":
            model = "strong"
        elif complexity == "medium":
            model = "cheap"
        else:
            model = "local"

        state["selected_model"] = model

        print(
            f"[RouterAgent] Selected model: {model}"
        )

        return state