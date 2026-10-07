from app.orchestration.state import RequestState


class ComplexityAgent:

    def run(self, state: RequestState) -> RequestState:
        print("[ComplexityAgent] Analyzing request complexity...")

        # Placeholder logic
        state["complexity"] = "medium"  # This could be determined based on the request content, length, etc.   

        print(
            f"[ComplexityAgent] Complexity: "
            f"{state['complexity']}"
        )

        return state