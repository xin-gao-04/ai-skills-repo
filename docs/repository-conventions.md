# Repository Conventions

## Goals

- Keep shared logic independent from any one agent vendor
- Keep adapter files thin and readable
- Avoid duplicating analysis logic across platforms

## Adapter Rule

Each platform adapter should contain instructions only. Business logic, sample output, and dependencies belong in `shared/`.

## Path Rule

Adapter files should refer to `../shared/` relative paths when describing commands.

## Versioning

When shared logic changes, update both adapters if the usage contract changes.

