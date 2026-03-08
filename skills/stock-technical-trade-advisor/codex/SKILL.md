---
name: stock-technical-trade-advisor
description: Technical analysis and trade-action advisor for a single stock or ETF. Uses shared/analyze_stock.py and returns structured trading guidance with position-aware scenarios.
---

# Stock Technical Trade Advisor For Codex

Use this skill when the user wants technical analysis or trade-action guidance for a single stock or ETF.

## Adapter Scope

This file is the Codex-specific adapter. Shared logic lives in `../shared/`.

## Before Running

If the user only provides a symbol or says "analyze this stock", ask the minimum required context first:

- Are they `holding`, `watching`, or `preparing to buy`?
- If holding: what is the cost basis and share count?
- Are they trading `short-term`, `swing`, or `position`?

If the user says not to ask follow-up questions, use defaults:

- `position-status`: `watch`
- `risk-style`: `balanced`
- `horizon`: `swing`

## Shared Commands

Run from this skill directory or adapt the path explicitly:

```bash
pip install -r ../shared/requirements.txt
python ../shared/analyze_stock.py --symbol 600584 --market cn
```

For richer A-share review data before a Claude-side or manual deep dive:

```bash
python ../shared/fetch_stock_data.py --code 601600 --days 250
```

## Position-Aware Run

```bash
python ../shared/analyze_stock.py --symbol 600584 --market cn --position-status holding --cost-price 45.8 --shares 2000 --risk-style balanced --horizon swing --no-interactive
```

## Output Requirements

Your response must distinguish:

- generic technical conclusion
- position-aware conclusion
- condition-triggered action plan

Reasoning must explicitly cover:

1. current structure across month, week, and day: strong trend, weak repair, range, or medium-term weakening
2. bullish evidence versus bearish evidence
3. signal conflict and why key levels matter
4. portfolio action after applying cost basis, size, and risk style
5. three scenarios: strong repair, neutral range, continued weakening
6. when available, how sentiment clues such as northbound flow, margin data, or dragon-tiger records change confidence

## Reference Files

- `../shared/analyze_stock.py`
- `../shared/fetch_stock_data.py`
- `../shared/example_output.md`
- `../shared/requirements.txt`
- `../shared/references/indicators.md`
- `../shared/references/risk-management.md`
- `../shared/references/sentiment.md`
