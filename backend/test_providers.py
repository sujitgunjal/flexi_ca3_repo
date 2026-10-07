import sys

from app.providers import generate_response
from app.providers.health import check_all_providers

sys.stdout.reconfigure(errors="replace")


results = check_all_providers()

print("========== PROVIDER HEALTH ==========")
for item in results:
    print(
        f"{item.tier}: {item.status} | {item.provider} | {item.model} | "
        f"{item.latency_ms} ms | {item.detail}"
    )

probe_tier = sys.argv[1] if len(sys.argv) > 1 else None

if probe_tier:
    print(f"\n========== PROBE {probe_tier} ==========")
    reply = generate_response(
        model=probe_tier,
        prompt="Reply with the single word OK.",
        timeout=45,
    )
    print(reply)

if any(not item.available for item in results):
    raise SystemExit(1)

print("\n========== ALL TIERS HEALTHY ==========")
