---
name: calibration-review
description: Use when reviewing prediction agent performance, analyzing Brier scores or win rates, evaluating learned heuristics, deciding whether to adjust Kelly fraction or confidence thresholds, or preparing for a weekly meta-analysis run.
---

# Calibration Review

## Overview

The prediction agent's calibration state lives in three places:
1. **Vault snapshot** — `~/obsidian-vault/agents/prediction-agent/calibration/YYYY-MM.md`
2. **Vault heuristics** — `~/obsidian-vault/agents/prediction-agent/heuristics/learned.md`
3. **Database** — `prediction_agent/data/predictions.db` (source of truth)

When vault and database disagree, trust the database. The vault is written by `obsidian_sync.py` on a schedule and may lag.

**Key metric thresholds:**

| Metric | Healthy | Warning | Action Required |
|---|---|---|---|
| Brier score | < 0.20 | 0.20–0.25 | > 0.25 |
| Win rate (rolling 20) | > 55% | 50–55% | < 50% |
| Kelly fraction (dynamic) | 0.07–0.12 | 0.05–0.07 | < 0.05 or > 0.15 |
| Bets placed / day | 1–5 | 6–10 | > 10 |
| Avg edge at fill | > 0.08 | 0.06–0.08 | < 0.06 |

Kelly fraction is set dynamically — the config `kelly_fraction` is the **base**, not the active value. Do not adjust config to compensate for a high Brier score; the dynamic function already handles this.

## Core Process

**Step 1 — Read the vault snapshot.**

Open `calibration/YYYY-MM.md`. Note Brier score, win rate with n (sample size matters — <10 resolved bets means no conclusions), Kelly fraction (the dynamic output), and bankroll trajectory.

**Step 2 — Check domain breakdown.**

If the calibration note lacks a domain breakdown, query the database:
```sql
SELECT domain, COUNT(*) as n, AVG(llm_prob - resolved_yes) as avg_bias,
       AVG((llm_prob - resolved_yes)*(llm_prob - resolved_yes)) as brier
FROM markets_analyzed m JOIN resolutions r ON m.ticker = r.ticker
GROUP BY domain HAVING n >= 5
ORDER BY ABS(avg_bias) DESC;
```
Domains with `|avg_bias| > 0.05` are candidates for new heuristics.

**Step 3 — Review active heuristics.**

Open `heuristics/learned.md`. For each heuristic:
- `confidence` >= 0.70? Below this, treat as provisional.
- `evidence_count` >= 8? Below 8 resolved markets is insufficient.
- Has domain Brier improved since the heuristic was added? If not, the heuristic may be stale.

**Step 4 — Check ensemble persona weights.**

Top-3 personas are selected by domain accuracy from: `base_rate`, `news`, `skeptic`, `consensus`, `tail_risk`. If calibration is degrading in a specific domain, persona weights for that domain may be stale.

**Step 5 — Recommend action by tier.**

```
Brier > 0.25 for 2+ weeks:
  → Tighten min_edge and min_confidence in config (bet less)
  → Do NOT add more Opus calls — this is a selectivity problem

Domain bias > 0.08:
  → Run HeuristicGenerator.run_meta_analysis() manually
  → Review generated heuristics before they enter the DB

Win rate < 50% for rolling 20:
  → Check whether circuit breaker L1 has activated (Kelly halved)
  → If not, consider raising min_edge by 0.02

Kelly fraction < 0.05:
  → Brier score is > 0.25; agent is correctly being conservative
  → Do not override — fix the underlying calibration
```

**Step 6 — Append findings to the calibration note.**

Include the domain breakdown table even if unchanged.

## Common Mistakes

- **Treating the vault snapshot as source of truth** — the DB may have resolved bets that haven't synced yet.
- **Adjusting Kelly fraction in config when Brier is high** — the dynamic Kelly already handles this. Manually lowering the base makes the agent overly conservative when calibration recovers.
- **Generating heuristics from < 8 resolved bets** — the HeuristicGenerator has a bias threshold but not a minimum n. Enforce n >= 8 manually.
- **Treating a Brier improvement in week 1 as signal** — wait for n >= 30 before drawing trend conclusions.
- **Ignoring the market-mid blending** — the final probability blends LLM output with market mid. A large apparent LLM edge may be smaller post-blend. Think in terms of blended probability.
