# Macro Sector Rotation Agent For Claude

Use this instruction file for A-share macro and sector rotation analysis.

## When To Use

- sector allocation and style rotation
- weekly or monthly macro reports
- policy-driven industry positioning
- market regime transitions and conflict resolution

## Shared Assets

All shared assets live in `../shared/`.

If local command execution is available:

```bash
pip install -r ../shared/requirements.txt
python ../shared/trigger.py --run-now --skill-dir ..
```

## Response Contract

Your answer should include:

- macro regime
- liquidity state
- sector ranking with scores
- top drivers and invalidation risks
- overweight, neutral, and underweight lists
- explicit conflict adjudication when signals disagree

