from app.orchestration.state import RequestState
from app.providers import generate_response


class GenerateAgent:

    def run(self, state: RequestState) -> RequestState:
        model = state.get("selected_model", "cheap")
        prompt = state.get("query", "")
        if "optimized_history" in state:
            history = state.get("optimized_history") or []
        else:
            history = state.get("conversation_history") or []

        print(f"[GenerateAgent] Generating response with model: {model}")

        state["response"] = generate_response(
            model=model,
            prompt=prompt,
            history=history,
        )

        print(f"[GenerateAgent] Response created for model: {model}")

        return state
