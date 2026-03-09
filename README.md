# AI Skills Repo

This repository stores self-built and curated skills in a platform-neutral layout, with thin adapters for each agent platform.

## Layout

- `skills/<skill-name>/shared/`: shared logic, scripts, examples, dependencies
- `skills/<skill-name>/codex/`: Codex adapter files
- `skills/<skill-name>/claude/`: Claude adapter files
- `docs/`: repository-level notes and conventions

## Current Skills

### `investing-cn`

- `stock-technical-trade-advisor`
- `macro-sector-rotation-agent`
- `aluminum-investment-agent`
- `a-share-shortline-state-machine`

### `engineering`

- `cpp-pro`
- `typescript-pro`
- `api-designer`
- `code-documenter`
- `debugging-wizard`
- `cli-developer`
- `devops-engineer`
- `rag-architect`
- `qt5-widgets-desktop-engineering`

## Add A New Skill

1. Create `skills/<category>/<skill-name>/shared/`
2. Put core scripts and assets in `shared/`
3. Add a Codex adapter in `codex/`
4. Add a Claude adapter in `claude/`
5. Document install and usage differences in the skill README

## Cross-Device Use

Codex:

1. Copy or install the skill folder to `~/.codex/skills/<skill-name>`
2. Install dependencies from `shared/requirements.txt`
3. Restart Codex so it reloads available skills

Repository-managed publish scripts:

- Windows: `pwsh -File .\scripts\publish-to-codex.ps1 -SkillName <skill-name>`
- macOS: `./scripts/publish-to-codex.sh --skill <skill-name>`
- Details: `docs/publishing.md`

Claude:

1. Open the skill's `claude/CLAUDE.md`
2. Use it as the project instruction or agent prompt layer
3. Keep the `shared/` files beside it so script paths stay valid
