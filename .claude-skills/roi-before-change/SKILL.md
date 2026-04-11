---
name: roi-before-change
description: Use before proposing or implementing any change to either agent — new feature, data source, prompt modification, model upgrade, new LLM call, or changed scan frequency. Use when the request is "add X," "improve Y," or "what if we tried Z."
---

# ROI Before Change

## Overview

Both agents have hard daily LLM budgets. Every change is a resource allocation decision. The agent system costs ~$267/month to run; every change must generate more return than it costs.

**Priority order (do not reorder):**
1. Token cost reduction
2. Bet selectivity (fewer, higher-confidence trades)
3. Raw accuracy (third — costs more tokens to improve marginally)

Raw accuracy is last because improving it typically requires more Opus calls, which erodes the budget advantage faster than the accuracy gain recovers it.

**Budget reference:**
- Prediction agent: `$2.00/day` — Haiku ~$0.0002/call, Sonnet ~$0.003/call, Opus ~$0.015/call
- Trading agent: `$0.05/day` — one extra Opus call exhausts ~8% of daily budget

## Core Process

**Step 1 — Classify the change.**

```
Token cost reduction:
  Shorter prompts, fewer markets scanned, caching, Haiku substitution
  → Measurable immediately from cost_engine logs

Bet selectivity:
  Higher confidence threshold, tighter edge, domain filtering
  → Measurable from bets_placed count and win_rate in calibration logs

Raw accuracy:
  Better prompts, more context, stronger models, more personas
  → Measurable only from Brier score over 20+ resolved markets (slow loop)
```

**Step 2 — Estimate the cost of the change.**

For any new LLM call:
```
cost = (input_tokens * rate_in + output_tokens * rate_out) / 1_000_000
daily_add = cost * calls_per_day
```

Use `_compute_cost()` in `regime_selector.py` as the reference implementation. Verify rates against current Anthropic pricing before committing.

**Step 3 — Estimate the benefit with a named metric.**

- Token savings: `cost_engine.get_today_llm_spend()` before and after
- Selectivity gain: `bets_placed` count in calibration log, `win_rate`
- Accuracy gain: Brier score in `calibration/YYYY-MM.md` after 20+ resolved bets

Be honest: accuracy feedback loops are weeks long. State this explicitly. Do not claim accuracy improvements are measurable short-term.

**Step 4 — Apply the decision rule.**

```
Cost reduction                          → implement (unless removes a safety feature)
Selectivity gain + cost <10% of budget → implement
Accuracy gain + new Opus call          → pause, quantify token cost first
Accuracy gain + existing Haiku call    → acceptable, implement
Cost >20% of daily budget for agent    → reject or find cheaper path
```

**Step 5 — State the measurement plan before writing code.**

Name the exact field and file where improvement will be visible. If you cannot name it, you cannot verify the change worked.

## Common Mistakes

- **Proposing accuracy improvements without budgeting the token cost** — "better reasoning" with Opus has a concrete dollar cost.
- **Treating selectivity and accuracy as equivalent** — they are not. Fewer, better bets is strictly higher priority.
- **Adding a new data source without checking scan token impact** — each additional market context adds ~200-400 tokens. At 15 markets/scan, this compounds.
- **Upgrading Haiku to Sonnet "to improve quality"** — Sonnet costs ~15x more per call. This wipes the routing cost advantage immediately.
- **Skipping the measurement plan** — if you cannot name what metric changes, you cannot verify the change worked.
