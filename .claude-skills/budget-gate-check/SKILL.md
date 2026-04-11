---
name: budget-gate-check
description: Use when adding a new LLM call anywhere in either agent, changing a model assignment, modifying max_tokens_per_call, changing scan frequency or market count limits, or investigating why a daily budget was exceeded unexpectedly.
---

# Budget Gate Check

## Overview

Both agents enforce a daily LLM budget hard stop. Exceeding it causes **silent fallback** — the agent keeps running but stops learning or updating regimes. This is easy to miss and dangerous.

**Budget limits:**
- Prediction agent: `$2.00/day`
- Trading agent: `$0.05/day`

**Budget gate location:** `_over_daily_budget()` is called before every LLM invocation. Any new LLM call must be wrapped by this gate.

**Cost reference (verify against current Anthropic pricing):**
- Haiku: ~$0.0002 per typical call (300 in + 200 out tokens)
- Trading agent typical daily spend: ~$0.004/day (1 Opus regime + possible intraday Haiku)
- Trading agent headroom: ~$0.046/day — very tight
- Prediction agent typical daily spend: ~$0.25/day (15 markets × Opus + Haiku screening)
- Prediction agent headroom: ~$1.75/day — relatively spacious

## Core Process

**Step 1 — Map all existing LLM calls for the agent.**

For the prediction agent: Haiku screener, Sonnet/Opus per-market estimation, ensemble personas (Opus × 5 for high-stakes markets only), weekly Haiku heuristic generation.

For the trading agent: optional Haiku pre-analysis (if `two_stage_regime: true`), Opus daily regime call, conditional Haiku intraday check.

**Step 2 — Compute cost of the new call.**

```
cost_per_call = (tokens_in * rate_in + tokens_out * rate_out) / 1_000_000
daily_add = cost_per_call * calls_per_day
```

Use `_compute_cost()` in `regime_selector.py` as the reference implementation. Use expected output tokens, not `max_tokens`.

**Step 3 — Check headroom.**

If the new call consumes > 20% of available daily headroom, require ROI justification using the `roi-before-change` skill before proceeding.

**Step 4 — Wrap the new call in a budget gate.**

Pattern from `regime_selector.py`:
```python
if self._over_daily_budget():
    logger.warning("LLM daily budget exceeded — [describe fallback behavior]")
    return [safe_fallback]
# only then:
response = client.messages.create(...)
```

The gate must fire **before** `messages.create()`, not after.

**Step 5 — Record actual usage after the call.**

```python
cost_engine.record_llm_call(
    model=model,
    input_tokens=response.usage.input_tokens,
    output_tokens=response.usage.output_tokens
)
```

Use actual counts from `response.usage` — never estimated values.

**Step 6 — For the trading agent: verify intraday budget reservation.**

`check_intraday_regime()` reserves 30% of daily budget (`intraday_budget_pct=0.30`). Any new call added to the main intraday loop must not exhaust this reservation. If `spent >= budget - intraday_budget`, the intraday check silently skips — new calls added before it can trigger this condition.

## Common Mistakes

- **Adding a call without a budget gate** — agent runs correctly until budget is hit, then silently falls back with no indication the new call is responsible.
- **Using `max_tokens` as a cost proxy** — max_tokens is the ceiling, not typical output. Use actual `output_tokens` from the response.
- **Enabling Silicon Crowd ensemble for all markets** — this calls Opus 5× per market (~$0.075/market). It must remain gated to high-stakes markets only.
- **Reducing `scan_interval_minutes` without accounting for cost doubling** — halving the interval doubles LLM cost for the same market count.
- **Treating Perplexity/news API calls as free** — they are capped at 2/day in config and have their own API cost. They are not tracked by `cost_engine` but count against operational budget.
