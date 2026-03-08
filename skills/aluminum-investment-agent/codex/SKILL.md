---
name: aluminum-investment-agent
description: Aluminum-sector investment analysis advisor for A-shares. Covers aluminum prices, inventories, costs, profit elasticity, stock comparison, and action-oriented reporting.
---

# Aluminum Investment Agent For Codex

Use this skill when the user wants:

- aluminum-sector weekly or event-driven analysis
- comparison of China Hongqiao-style A-share aluminum names such as 601600, 000807, 000933, and 002532
- profit elasticity and cycle-position judgment
- commodity-to-equity transmission analysis

## Adapter Scope

Shared materials live in `../shared/`.

## Workflow

1. Collect aluminum, alumina, inventory, power-cost, and macro data.
2. Estimate industry profit and company elasticity.
3. Judge cycle position and whether price leads or fundamentals lead.
4. Compare listed names by cost, elasticity, valuation, and risk.
5. Output a structured action report with conditions and risks.

## Shared References

- `../shared/trigger.py`
- `../shared/references/data-sources.md`
- `../shared/references/profit-model.md`
- `../shared/references/scoring-model.md`

