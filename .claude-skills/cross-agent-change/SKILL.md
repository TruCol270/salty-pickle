---
name: cross-agent-change
description: Use when modifying cross_agent_bridge.py, changing database schema in either agent, changing what the prediction agent writes to predictions.db, changing how the trading agent reads prediction signals, or adding a new cross-agent data flow.
---

# Cross-Agent Change

## Overview

The bridge (`shared/cross_agent_bridge.py`) is **read-only by design** — it opens each agent's SQLite DB with `PRAGMA journal_mode=WAL` and reads without writing. This isolation boundary is intentional. Neither agent writes through the bridge; each writes only to its own DB via its own logging module.

**Data that crosses the bridge:**

| Direction | Data | Method |
|---|---|---|
| Prediction → Trading | High-confidence market estimates | `get_recent_prediction_signals()` |
| Prediction → Trading | Calibration stats | `get_prediction_calibration()` |
| Trading → Prediction | Regime label + weights | `get_current_equity_regime()` |
| Trading → Prediction | P&L performance | `get_equity_performance()` |

**Database paths:**
- Prediction: `prediction_agent/data/predictions.db`
- Trading: `trading_agent/data/experiment.db`

## Core Process

**Step 1 — Identify the direction the change affects.**

Prediction → trading, trading → prediction, or trading → options? Each direction has separate read methods. Schema changes to `predictions.db` affect `get_recent_prediction_signals()` and `get_prediction_calibration()`.

**Step 2 — Verify column names against the live schema.**

```bash
sqlite3 prediction_agent/data/predictions.db ".schema markets_analyzed"
sqlite3 prediction_agent/data/predictions.db ".schema resolutions"
sqlite3 trading_agent/data/experiment.db ".schema regime_log"
sqlite3 trading_agent/data/experiment.db ".schema fills"
```

The bridge SQL is inline strings. Broken queries fail silently (caught exceptions return `[]`). Always run the schema check after any schema change.

**Step 3 — Verify the bridge stays read-only.**

Every `CrossAgentBridge` method must:
- Open with `sqlite3.connect(path, timeout=5)`
- Read and return
- Close in a `finally` block
- Never call `conn.execute()` with INSERT/UPDATE/DELETE
- Never call `conn.commit()`

If new functionality requires writing cross-agent state, it belongs in `tournament.py` (the designated shared state store), not the bridge.

**Step 4 — Verify failure modes return safe defaults.**

Every bridge method must catch `FileNotFoundError` (DB doesn't exist) and return `[]` or `{}`. Never propagate a connection failure to the caller.

**Step 5 — Check `_infer_domain()` covers new ticker formats.**

`get_recent_prediction_signals()` uses `_infer_domain()` to filter by domain. Current prefixes:
- Economics: `FED`, `GDP`, `CPI`, `ECON`, `RATE`, `JOBS`
- Politics: `PRES`, `ELECT`, `GOV`, `SENATE`, `HOUSE`
- Crypto: `BTC`, `ETH`, `CRYPTO`
- Markets: `AAPL`, `TSLA`, `SPY`, `STOCK`, `EARN`

Unmapped tickers fall to `"general"` which is not filterable. If new Kalshi market categories are being scanned, add their prefixes.

**Step 6 — Verify `obsidian_sync.py` compatibility.**

Both agents have `agent_logging/obsidian_sync.py` that reads from the same DBs. If you change a schema, verify the sync module's queries still work. Broken sync queries fail silently — calibration and regime logs stop updating without any error.

## Common Mistakes

- **Adding a write to the bridge** — the bridge is read-only by design. Writes go through the agent's own logging module.
- **Using the bridge for real-time signals** — the bridge reads DB rows written at the end of each agent cycle. It cannot provide sub-cycle latency.
- **Changing a column name without updating all bridge SQL** — SQL strings are not validated at import time. Broken queries return `[]` silently.
- **Assuming `get_recent_prediction_signals()` returns today's signals** — it returns the most recent rows ordered by `ts DESC`. If the prediction agent hasn't run today, results are from prior days. Always check the `ts` field.
- **Switching from WAL mode** — both agents write to their DBs while running. WAL allows concurrent reads. Default journal mode would cause `SQLITE_BUSY` errors.
