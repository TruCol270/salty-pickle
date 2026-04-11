# ClawTrader Agent Launch Pattern

**Extracted:** 2026-04-08
**Context:** Launching prediction_agent or trading_agent as Python modules from the project root

## Problem

Running `python3 -m prediction_agent.main` fails with:
```
FileNotFoundError: Config file not found: /path/to/ClawTrader/config/config.yaml
```

The default `--config` argparse argument resolves relative to CWD, not the module location. The actual config lives at `prediction_agent/config/config.yaml`, not `config/config.yaml`.

Also: macOS system Python is `python3`, not `python`.

## Solution

Always launch with explicit PYTHONPATH and config path:

```bash
# Prediction agent
PYTHONPATH=/Users/colmantruett/Projects/ClawTrader python3 -m prediction_agent.main \
  --config prediction_agent/config/config.yaml

# Smoke test
PYTHONPATH=/Users/colmantruett/Projects/ClawTrader python3 -m prediction_agent.main \
  --smoke-test --config prediction_agent/config/config.yaml

# Trading agent
PYTHONPATH=/Users/colmantruett/Projects/ClawTrader python3 -m trading_agent.main \
  --config trading_agent/config/config.yaml
```

## When to Use

Any time a ClawTrader agent is launched from the terminal — startup, smoke test, debugging. If you see `FileNotFoundError: Config file not found`, check whether `--config` is pointing to the right path.
