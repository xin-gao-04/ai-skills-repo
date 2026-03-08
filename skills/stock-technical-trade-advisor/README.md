# stock-technical-trade-advisor

Single-stock or ETF technical analysis skill with shared execution logic and separate Codex and Claude adapters.

## Structure

- `shared/analyze_stock.py`: core analysis script
- `shared/fetch_stock_data.py`: enriched A-share data collector
- `shared/requirements.txt`: Python dependencies
- `shared/example_output.md`: sample output
- `shared/references/`: indicator, sentiment, and risk-management references
- `codex/SKILL.md`: Codex adapter
- `claude/CLAUDE.md`: Claude adapter

## Shared Command

```bash
python shared/analyze_stock.py --symbol 600584 --market cn
```

## Complementary Full-Data Command

```bash
python shared/fetch_stock_data.py --code 601600 --days 250
```

## Notes

- Keep `shared/` intact when moving the skill to another device.
- The merged version keeps the stronger parts of both implementations:
  - the existing daily-structure scoring engine
  - the Claude project's multi-timeframe, sentiment, and risk-management references
- The Claude adapter is intentionally prompt-oriented so it can be reused in Claude project instructions even if the exact packaging surface differs by client.
