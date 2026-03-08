---
name: macro-sector-rotation-agent
description: A-share macro regime and sector rotation advisor. Produces sector ranking, style rotation judgment, and structured allocation guidance using the shared reference framework.
---

# Macro Sector Rotation Agent For Codex

Use this skill when the user wants:

- A-share sector rotation analysis
- weekly or monthly allocation views
- style switching judgment across value, growth, and defense
- macro or policy-driven sector recommendations

## Adapter Scope

Shared materials live in `../shared/`.

## Workflow

1. Build a macro snapshot: PMI, social financing, CPI/PPI, rates, DXY, policy headlines.
2. Judge macro regime and liquidity state.
3. Score sector signals across momentum, valuation, fundamentals, and catalysts.
4. Rank sectors and output overweights, neutral allocations, and avoids.
5. Explicitly resolve signal conflicts.

## Shared References

- `../shared/trigger.py`
- `../shared/references/data-sources.md`
- `../shared/references/regime-sector-playbook.md`
- `../shared/references/rotation-signal-model.md`
- `../shared/references/sector-scoring-model.md`
- `../shared/references/quality-checklist.md`

