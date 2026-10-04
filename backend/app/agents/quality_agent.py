from app.orchestration.state import RequestState


class QualityAgent:

    def run(self, state: RequestState) -> RequestState:
        print("[QualityAgent] Evaluating response quality...")

        # Placeholder quality score
        state["quality_score"] = 0.90
        state["escalation"] = False

        print(
            f"[QualityAgent] Quality score: "
            f"{state['quality_score']}"
        )

        return state