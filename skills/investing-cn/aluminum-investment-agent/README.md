# aluminum-investment-agent

Aluminum-sector investment analysis skill for A-shares, migrated from the Claude project package into the shared repository layout.

## Structure

- `shared/trigger.py`: scheduled Claude-oriented trigger script
- `shared/references/`: data source, profit model, and scoring references
- `codex/SKILL.md`: Codex adapter
- `claude/CLAUDE.md`: Claude adapter

## Notes

- This skill focuses on the aluminum chain and representative listed companies.
- The trigger script remains useful for periodic report generation where Anthropic API access is available.

