---
name: regime-trade-analysis
description: Use when reviewing trading agent performance, analyzing a regime decision, debugging a missed or unexpected trade, reviewing the Streamlit dashboard, comparing regime log to P&L, or verifying whether the intraday Haiku check fired correctly.
---

# Regime Trade Analysis

## Overview

The trading agent operates at two timescales:

1. **Daily (post-close, ~16:30 ET):** `LLMRegimeSelector.run()` sets `RegimeParams` — strategy weights, `max_position_pct`, param adjustments. Cost: ~$0.004–$0.015.
2. **Intraday (on 2-sigma vol deviation):** `check_intraday_regime()` calls Haiku only when `vol_ratio > 2.0 or < 0.5` AND budget allows. Requires `confidence >= 0.70` to accept the change. Cost: ~$0.0003.

**Hard limits that no regime can override:**

| Limit | Value |
|---|---|
| Max position per symbol | 30% of equity |
| Max daily turnover | 2x equity |
| Max intraday drawdown | 5% |
| Min trade size | $5.00 |

The LLM-set `max_position_pct` from regime is a soft ceiling within the hard limit. Both constraints apply.

## Core Process

**Step 1 — Orient to the regime for the day.**

Read `~/obsidian-vault/agents/trading-agent/regime-log/YYYY-MM.md`. For the day:
- Regime label, strategy weights, `enable_news_filter`, `max_position_pct`
- Any intraday change? Look for `[Intraday adjustment]` prefix in reasoning.

**Step 2 — Check the trade log.**

Read `~/obsidian-vault/agents/trading-agent/performance/YYYY-MM-DD-trades.md`:
- Is `limit_price` present on every trade? (Missing = something bypassed `execution_engine.py`)
- Does `regime` field on each trade match the day's regime?
- Are shares consistent with VIX gating? VIX > 25 → max_value halved; VIX > 35 → quartered.

**Step 3 — If a trade was missing, trace the rejection gates in order.**

```
1. _halted == True?
   → Intraday drawdown exceeded 5%; no trades until next open_day()

2. signal.is_actionable() == False?
   → FLAT signal; no action needed

3. check_risk_limits() rejected?
   → daily_turnover_usd >= equity * 2.0  (turnover cap)
   → max_pos_value < $5.00               (trade too small)
   → existing position >= regime_max     (already at limit)

4. _size_order() returned qty == 0?
   → max_value too small after VIX gating

5. Paper fill rejection?
   → 15% random rejection rate in paper mode; not a strategy issue
```

Work through gates in order. Stop at the first gate that explains the miss.

**Step 4 — Verify intraday regime check behavior.**

The check fires only when `vol_ratio > 2.0 OR vol_ratio < 0.5`. If vol_ratio was 1.8, no intraday check should have fired. Budget guard: the check reserves 30% of daily budget (`intraday_budget_pct=0.30`); if `spent >= budget - intraday_budget`, the check is silently skipped.

**Step 5 — Cross-reference prediction bridge signals.**

Check `shared/cross_agent_bridge.py` `get_recent_prediction_signals()` — were high-confidence prediction signals available that day? If signals were present but unused, verify the bridge was called in the main loop.

**Step 6 — Append findings to regime log.**

Include: regime label, what fired or didn't, and the action taken.

## Common Mistakes

- **Blaming regime for a halt-caused miss** — `_halted` is set post-fill by `_check_drawdown_halt()`. Subsequent signals are silent no-ops. Always check `_halted` first.
- **Expecting intraday changes in the regime_log table** — intraday changes mutate in-memory `RegimeParams` and use `[Intraday adjustment]` prefix, not a new DB row.
- **Confusing config `max_position_pct` with regime `max_position_pct`** — config sets the default; the daily LLM call sets the active value. They can differ.
- **Attributing low fill rate to filtering when paper rejection is the cause** — paper simulation rejects 15% of limit orders randomly. A day with 3 signals and 1 fill may reflect paper mechanics.
- **Forgetting VIX gating when sizing looks wrong** — `_vix_level` defaults to 0.0 if VIX data was unavailable at `open_day()`. Verify VIX was loaded.
