# Repository Conventions

## Goals

- Keep shared logic independent from any one agent vendor
- Keep adapter files thin and readable
- Avoid duplicating analysis logic across platforms

## Adapter Rule

Each platform adapter should contain instructions only. Business logic, sample output, and dependencies belong in `shared/`.

## Path Rule

- Claude adapters should refer to `../shared/` relative paths when describing commands.
- Codex adapters should refer to the published runtime layout, where `shared/` contents are copied into the skill root. Use paths such as `references/...`, `trigger.py`, or `analyze_stock.py`.

## Category Rule

- Skills may be grouped under category folders such as `skills/investing-cn/<skill-name>` or `skills/engineering/<skill-name>`.
- A valid skill directory is any directory under `skills/` that contains both `shared/` and `codex/`.

## Versioning

When shared logic changes, update both adapters if the usage contract changes.
