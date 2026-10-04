from app.orchestration.state import RequestState


class CacheAgent:

    def run(self, state: RequestState) -> RequestState:
        print("[CacheAgent] Checking cache...")

        # Day 1/2 placeholder
        state["cache_hit"] = False

        print("[CacheAgent] Cache MISS")

        return state