---
name: agent-change-safety
description: Use when modifying any code in prediction_agent/, trading_agent/, or shared/, before refactoring or editing execution engines, risk engines, LLM routing modules, or config files. Use when a change is described as "simplify," "clean up," "consolidate," "remove dead code," or "flatten."
---

# Agent Change Safety

## Overview

Both agents contain interlocking safety systems that are easy to accidentally remove during cleanup. Three systems must survive every change:

1. **Circuit breakers** — L1/L2/L3 drawdown gates (`_check_circuit_breaker()`, `_check_drawdown_halt()`, `_halted` flag)
2. **Adaptive thresholds** — dynamic min_edge/min_confidence/Kelly based on rolling win rate and Brier score (`_update_adaptive_thresholds()`, `_get_dynamic_kelly_fraction()`)
3. **Smart model routing** — Haiku pre-screens, Sonnet/Opus executes (`_call_haiku_pre_analysis()`, `check_intraday_regime()`)

**Order type rule (non-negotiable):** Every order path must produce `order_type="limit"` with an explicit `limit_price`. Never a variable resolved from config at runtime — grep must always be able to verify the literal string.

## When to Use

Before touching any file in:
- `prediction_agent/execution/`
- `prediction_agent/llm/`
- `trading_agent/execution/`
- `trading_agent/llm/`
- Either `config/config.yaml`
- `shared/cross_agent_bridge.py`

## Core Process

**Step 1 — Identify safety systems in the target file.**

Grep for these patterns before changing anything:
- `_cb_enabled`, `_halted`, `_cb_level`, `circuit_breaker` → circuit breaker logic
- `_adaptive_enabled`, `_min_edge`, `_min_confidence`, `_get_dynamic_kelly` → adaptive thresholds
- `haiku`, `model_fast`, `two_stage`, `_call_haiku` → model routing
- `order_type="limit"`, `limit_price` → order type enforcement

**Step 2 — Document what each safety system does before changing anything.**

Write it out explicitly. Do not rely on memory.

**Step 3 — Apply the change.**

**Step 4 — Verify all invariants still hold.**

| Invariant | Where to verify |
|---|---|
| `_halted` flag gates all order submission | `ExecutionRiskEngine.submit_signal()` |
| CB L1 halves position sizing (does not halt) | `_get_effective_max_position_pct()` |
| CB L2 pauses for 24h | `_check_circuit_breaker()` |
| CB L3 pauses indefinitely | same |
| Adaptive thresholds update at most every 5 min | `_adaptive_ttl = 300.0` |
| Kelly fraction is dynamic (Brier-gated) | `_get_dynamic_kelly_fraction()` |
| Haiku pre-analysis failure is non-fatal | returns `{}` on failure, not an exception |
| All orders use `order_type="limit"` | both execution modules |
| Budget gate checked before every LLM call | `_over_daily_budget()` in both agents |

**Step 5 — If a safety system was removed or its behavior changed, undo the change.**

There is no acceptable version of "I simplified the circuit breaker." If behavior is preserved, the implementation is fine. If behavior changed, the change is rejected.

## Common Mistakes

- **Merging `_should_bet()` into a single if-chain** — buries the CB check ordering. CB must remain the first gate.
- **Moving adaptive threshold logic into config** — config values are static; the adaptive system reads rolling win rate at runtime. Not equivalent.
- **Removing the `_halted` flag** — replacing it with a raise or return-early pattern breaks EOD flatten, which calls `submit_signal()` internally.
- **Changing `model_fast` to the same model as `model`** — eliminates the routing cost advantage without any warning.
- **Setting `order_type` to a variable** — must be the literal string `"limit"` at the call site.
