# Kalshi Live Mode Switch (Atomic Two-Field Pattern)

**Extracted:** 2026-04-08
**Context:** Switching the prediction agent from Kalshi demo → live trading

## Problem

Setting only `account.mode: live` in config.yaml is not sufficient. The agent's `is_live()` check requires BOTH fields:

```python
def is_live(config: dict) -> bool:
    mode = config.get("account", {}).get("mode", "demo")
    demo = config.get("broker", {}).get("kalshi", {}).get("demo", True)
    return mode == "live" and not demo
```

Missing either field silently routes to the wrong endpoint (demo API or live API depending on which field was changed).

## Solution

Always flip both fields atomically in `prediction_agent/config/config.yaml`:

```yaml
account:
  mode: live          # was: demo

broker:
  kalshi:
    demo: false       # was: true
```

To revert to demo:
```yaml
account:
  mode: demo

broker:
  kalshi:
    demo: true
```

## Verification

After the switch, run the smoke test to confirm the correct endpoint is reached:
```bash
PYTHONPATH=/Users/colmantruett/Projects/ClawTrader python3 -m prediction_agent.main \
  --smoke-test --config prediction_agent/config/config.yaml
# Expected: OK: Kalshi client initialized
```

Check which URL is being used:
- Demo: `https://demo-api.kalshi.co/trade-api/v2`
- Live: `https://api.elections.kalshi.com/trade-api/v2`

## When to Use

Any time the Kalshi trading mode is changed. The two-field atomic requirement is tested in `tests/test_mode_switch.py::test_kalshi_mode_atomic`.
