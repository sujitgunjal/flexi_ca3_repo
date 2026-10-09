# Evaluation metrics

## Comparison setup

**Baseline:** Every request → Strong Model → Response.

**Proposed Gateway:** Request → Cache → Complexity → Context Optimization → Model Selection → LLM → Quality Check → Escalation/Fallback → Response.

**Research question:**

> Can a multi-agent resource optimization layer reduce LLM inference cost and context consumption while maintaining comparable response quality and acceptable latency?

Run the same dataset against both paths, record per-request observations, and compare totals and distributions. Keep model/provider, dataset version, and run conditions with the eventual results so comparisons are interpretable. Do not treat this Day 1 template as measured results.

## Metrics

| Metric | What to record and calculate | Why it matters |
|---|---|---|
| Cost | Estimated cost per request and total cost for baseline and gateway. `cost_reduction = ((baseline_cost - gateway_cost) / baseline_cost) * 100` | Measures the main resource-saving goal. Handle a zero baseline cost before calculating a percentage. |
| Tokens | Input, output, and total tokens; context tokens before and after optimization. `context_tokens_saved = before - after`; `context_reduction_percent = ((before - after) / before) * 100` | Shows inference consumption and whether context optimization reduces prompt size. Reduction is undefined when original tokens are missing or zero. Token reduction is not itself a measure of answer quality; assess quality separately. |

| Latency | Average latency, P95 latency, and latency per model | Captures user-perceived delay and reveals whether optimization adds overhead or improves response time. |
| Routing | Percentage of requests sent to local, cheap, and strong models | Shows how the gateway distributes work and whether it avoids unnecessary strong-model use. |
| Cache | Cache hits, misses, hit rate, and API calls avoided. `cache_hit_rate = cache_hits / total_requests` | Measures requests served without inference. Future calculations must avoid division by zero. |
| Quality | Rate each response 1–5: 1 incorrect/unusable, 2 mostly incorrect, 3 partially correct, 4 good, 5 excellent. Track average score, quality pass rate, and escalation rate. | Checks that savings do not come at the cost of useful answers and indicates when escalation is needed. Define the pass threshold before a run. |
| Reliability | Fallback count, fallback rate, and successful fallback rate | Indicates how often provider failure recovery is needed and whether it restores a usable response. |

The results template records `context_before_tokens`, `context_after_tokens`, `context_tokens_saved`, and `context_reduction_percent`. Only measured values should be entered.

For rates, state the denominator used and omit or explicitly define rates when the denominator is zero. Record baseline and gateway measurements from the same query where possible.
