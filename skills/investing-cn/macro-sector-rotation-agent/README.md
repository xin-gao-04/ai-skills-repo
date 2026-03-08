# macro-sector-rotation-agent

Macro and sector rotation analysis skill for A-shares, migrated from the Claude project package into the shared repository layout.

## Structure

- `shared/trigger.py`: scheduled Claude-oriented trigger script
- `shared/references/`: macro, rotation, scoring, and quality references
- `codex/SKILL.md`: Codex adapter
- `claude/CLAUDE.md`: Claude adapter

## Notes

- This skill is currently prompt-and-trigger driven rather than a standalone local factor engine.
- The shared trigger remains useful for scheduled report generation where Anthropic API access is available.

