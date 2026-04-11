---
name: paper-fill-bet-id-mismatch
description: "Paper execution layers must reuse bet.id for fills, not generate a new UUID — avoids FK constraint failures on fills table"
user-invocable: false
origin: auto-extracted
---

# Paper Fill bet_id Must Match Original Bet ID

**Extracted:** 2026-04-01
**Context:** Any paper trading execution layer backed by a bets/fills relational schema

## Problem

A `fills` table with a FK constraint `bet_id REFERENCES bets(bet_id)` will raise
`FOREIGN KEY constraint failed` when a paper fill generates a fresh UUID for `bet_id`
instead of reusing the original `bet.id` that was already persisted to `bets`.

The bug is easy to miss because paper fills look correct in application logs — the fill
object is valid — but the DB write silently fails (or raises, depending on error handling).

## Root Cause

```python
# WRONG — generates a new UUID; bets table has bet.id, not this
fill = BetFill(
    bet_id=str(uuid.uuid4()),  # ← FK fails: this ID not in bets table
    ...
)

# CORRECT — thread the original bet ID through
fill = BetFill(
    bet_id=bet.id,  # ← matches the row already inserted into bets
    ...
)
```

## Solution

In `_paper_fill(self, bet: Bet, ...) -> BetFill`, always use `bet.id`:

```python
def _paper_fill(self, bet: Bet, market_id: str) -> BetFill:
    fill = BetFill(
        bet_id=bet.id,   # thread through original ID, not uuid.uuid4()
        ...
    )
```

The correct ID chain in BetEngine:
```python
self._bet_logger.record_bet(bet)        # inserts bet.id into bets table
fill = self._place_polymarket_bet(bet)  # must use same bet.id in fill
self._bet_logger.record_fill(fill)      # FK: fills.bet_id → bets.bet_id
```

## When to Use

- Any time you implement a paper/simulation execution path alongside a real one
- Both paths must return a `BetFill` (or equivalent) with the same ID that was written to the parent table
- The FK chain is: `record_bet(bet.id)` → `place_order(bet)` → `BetFill(bet_id=bet.id)` → `record_fill(fill)`
