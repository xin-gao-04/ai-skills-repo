# Shared Core

This directory holds the platform-neutral implementation for `stock-technical-trade-advisor`.

## Files

- `analyze_stock.py`: analysis engine
- `fetch_stock_data.py`: A-share full-data collector for Claude-style complete mode
- `requirements.txt`: dependencies
- `example_output.md`: sample output
- `references/`: indicator, risk-management, and sentiment notes merged from the Claude project version
- `quickstart.md`: prompt and workflow examples

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
python analyze_stock.py --symbol 600584 --market cn
python analyze_stock.py --symbol AAPL --market us --bench-symbol SPY
```

## Full-Data A-Share Mode

```bash
python fetch_stock_data.py --code 601600 --days 250
```

This produces a structured JSON package for higher-precision Claude-side review and preserves sentiment side data such as northbound flow, margin balance, and dragon-tiger list records when available.
