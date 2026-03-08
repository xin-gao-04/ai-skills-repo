# Aluminum Investment Agent For Claude

Use this instruction file for aluminum-sector investment analysis.

## When To Use

- aluminum industry weekly reports
- price, inventory, and cost-driven cycle analysis
- company ranking across major A-share aluminum names
- event-driven reassessment after inventory, policy, or macro shocks

## Shared Assets

All shared assets live in `../shared/`.

If local command execution is available:

```bash
pip install -r ../shared/requirements.txt
python ../shared/trigger.py --run-now --skill-dir ..
```

## Response Contract

Your answer should be delivered as a complete Markdown report.

Your answer should include:

- key market variables
- industry profit and elasticity view
- cycle position
- stock ranking and valuation framing
- action suggestion with time horizon
- risk list and next observation points

When comparing companies, always include a Markdown comparison table and a ranked conclusion from best to worst current value-for-money.
