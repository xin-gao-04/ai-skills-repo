# AI Skills Repo

This repository stores self-built skills in a platform-neutral layout, with thin adapters for each agent platform.

## Layout

- `skills/<skill-name>/shared/`: shared logic, scripts, examples, dependencies
- `skills/<skill-name>/codex/`: Codex adapter files
- `skills/<skill-name>/claude/`: Claude adapter files
- `docs/`: repository-level notes and conventions

## Current Skills

- `stock-technical-trade-advisor`
- `macro-sector-rotation-agent`
- `aluminum-investment-agent`

## Add A New Skill

1. Create `skills/<skill-name>/shared/`
2. Put core scripts and assets in `shared/`
3. Add a Codex adapter in `codex/`
4. Add a Claude adapter in `claude/`
5. Document install and usage differences in the skill README

## Cross-Device Use

Codex:

1. Copy or install the skill folder to `~/.codex/skills/<skill-name>`
2. Install dependencies from `shared/requirements.txt`
3. Restart Codex so it reloads available skills

Claude:

1. Open the skill's `claude/CLAUDE.md`
2. Use it as the project instruction or agent prompt layer
3. Keep the `shared/` files beside it so script paths stay valid
