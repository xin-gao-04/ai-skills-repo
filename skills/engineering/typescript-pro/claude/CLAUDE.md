# TypeScript Pro For Claude

Use this adapter when the user needs advanced TypeScript design, stricter type safety, custom utility types, type guards, or tsconfig guidance.

## Shared Assets

Primary guidance lives in `../shared/source-claude-skill.md`.

Load references from `../shared/references/` as needed:

- `advanced-types.md`
- `type-guards.md`
- `utility-types.md`
- `configuration.md`
- `patterns.md`

## Response Contract

- prefer type-first API design
- explain tradeoffs in strictness and ergonomics
- run `tsc --noEmit` or equivalent validation when possible
- keep public APIs explicit and maintainable
