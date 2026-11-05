---
name: "hk-cost-estimate"
description: "Prepare an order-of-cost estimate for a Hong Kong building from CFA and current HK$/m2 rates, with contingencies, escalation, fees, budget check and S-curve cash flow."
---

# HK order-of-cost estimate

Use when the user asks what a Hong Kong scheme will cost, whether it fits a budget, or for a feasibility cost plan or cash flow.

## Before starting
1. Read `/mnt/project-files/architect-kb/cost/cost-rules.md`.
2. Note the rate source and quarter in `cost/hk_cost_rates.json` (Arcadis Q2 2026). If a newer quarter is out, say the rates may be stale.

## Gather inputs
- CFA by use (or the `floors[]` of an existing B(P)R project: use `from_floors`). Warn that GFA understates CFA.
- Quality level per use, abnormal items (piling on reclamation, demolition, slope works, basements beyond 3 levels) as lump sums.
- Tender date (escalation), contract period (cash flow), client budget.

## Run
`python3 /mnt/project-files/architect-kb/tools/cost_estimate.py <file>.json -o <report>.md`, save under `/mnt/project-files/projects/<project-name>/`.

## Report back
- Lead with the construction cost and range, the total excl. land, and the budget result.
- List what is excluded (land, finance, legal, loose furniture) and every unmapped floor.
- State: order-of-cost estimate for a QS to develop; rates transcribed from Arcadis Q2 2026, to be re-checked.
