# Railway Agent API Proxy with Local Fallback

**Extracted:** 2026-04-09
**Context:** Bloomberg terminal connecting to Railway-hosted prediction agent

## Problem
Local dashboard needs data from an agent running on Railway (remote SQLite, no direct file access). The agent's SQLite DB is inaccessible from the local bloomberg_terminal backend.

## Solution
1. Add `prediction_agent_api_url: str = ""` to settings/config
2. The agent must expose a FastAPI server (started as a daemon thread in `main.py`)
3. Implement a `_prediction_get(path)` helper in the bloomberg_terminal backend that GETs the Railway URL via httpx
4. Each endpoint checks the URL first; falls back to local SQLite if unset or unreachable
5. Set `PREDICTION_AGENT_API_URL` env var to Railway public domain to enable live mode

## Example

```python
# bloomberg_terminal/backend/app/routers/agent.py

def _prediction_get(path: str) -> Any:
    """GET from Railway-hosted prediction agent API. Returns parsed JSON or None."""
    base = settings.prediction_agent_api_url.rstrip("/")
    try:
        resp = httpx.get(f"{base}{path}", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("prediction API proxy error (%s): %s", path, exc)
        return None

@router.get("/prediction/bets")
def get_prediction_bets(limit: int = 50):
    if settings.prediction_agent_api_url:
        data = _prediction_get(f"/bets?limit={limit}")
        return data if data is not None else {"available": False, "error": "prediction API unavailable"}
    # ... local SQLite fallback
    db_path = settings.prediction_agent_db
    ...
```

## Required Setup

- `httpx` must be in bloomberg_terminal requirements (already at v0.27.2)
- Agent must have a FastAPI server started in a daemon thread at startup
- Railway service must have "Public Networking" enabled to get a public domain
- Set env var: `PREDICTION_AGENT_API_URL=https://<service>.up.railway.app`

## Reuse Pattern

For each new ClawTrader agent added to Railway:
1. Add a `<agent>_api_url: str = ""` field to `config.py`
2. Add a `_<agent>_get(path)` proxy helper
3. Wire frontend api.ts methods → bloomberg_terminal router → proxy helper
4. Add panel to the relevant dashboard component

## When to Use
Any time a new ClawTrader agent is deployed to Railway and needs to be surfaced in the bloomberg_terminal dashboard. Also applies when migrating existing local agents to Railway.
