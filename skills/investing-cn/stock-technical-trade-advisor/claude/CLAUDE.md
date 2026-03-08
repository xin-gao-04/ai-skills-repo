# Stock Technical Trade Advisor For Claude

Use this instruction file as the Claude-side adapter for the shared stock analysis skill.

## Purpose

Analyze one stock or ETF with structured technical reasoning, scenario planning, and position-aware trade guidance.

Shared implementation files are located in `../shared/`.

## When To Use

Use this skill when the user asks for:

- technical analysis of one stock or ETF
- buy, sell, add, reduce, or watch conditions
- price levels, stop-loss ideas, or scenario-based planning
- guidance that depends on holdings, cost basis, risk style, or holding horizon

## Required Interaction

If the user only gives a symbol, ask up to three questions before running analysis:

1. Are you currently holding it, watching it, or preparing to buy?
2. If holding, what are your cost basis and share count?
3. Is your style short-term, swing, or longer-position trading?

If the user explicitly says "analyze directly" or refuses follow-up questions, assume:

- status: watch
- risk style: balanced
- horizon: swing

## Shared Commands

If your Claude environment can run local commands, use:

```bash
pip install -r ../shared/requirements.txt
python ../shared/analyze_stock.py --symbol 600584 --market cn
```

Position-aware example:

```bash
python ../shared/analyze_stock.py --symbol 600584 --market cn --position-status holding --cost-price 45.8 --shares 2000 --risk-style balanced --horizon swing --no-interactive
```

For an A-share complete-mode package with local indicators and sentiment side data:

```bash
python ../shared/fetch_stock_data.py --code 601600 --days 250
```

If command execution is unavailable, still follow the same reasoning framework and clearly label the answer as a prompt-only assessment.

## Response Contract

Your answer must be delivered as a complete Markdown report.

Your answer must include:

- overall structure judgment
- month/week/day timeframe view and whether they resonate
- bullish evidence
- bearish evidence
- key price levels
- position-aware action plan
- suggested position size and risk-reward framing
- three scenarios:
  - strong repair
  - neutral range
  - continued weakening

Use the same sectioned Markdown structure defined by the Codex adapter so outputs stay consistent across platforms.

## Reasoning Standard

Do not simply list indicators. First classify the structure, then weigh bullish and bearish evidence, then explain conflicts, then map the result to the user's position and risk style.

## Shared References

- `../shared/analyze_stock.py`
- `../shared/fetch_stock_data.py`
- `../shared/example_output.md`
- `../shared/requirements.txt`
- `../shared/references/indicators.md`
- `../shared/references/risk-management.md`
- `../shared/references/sentiment.md`
