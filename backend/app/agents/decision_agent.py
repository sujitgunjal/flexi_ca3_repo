from app.orchestration.state import RequestState


class ComplexityAgent:

    def run(self, state: RequestState) -> RequestState:
        print("[ComplexityAgent] Analyzing request complexity...")

        # Placeholder logic
        state["complexity"] = "medium"

        print(
            f"[ComplexityAgent] Complexity: "
            f"{state['complexity']}"
        )

        return state