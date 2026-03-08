# CLI Developer For Claude

Use this adapter when the user wants to build or refine command-line tools, command UX, argument parsing, shell ergonomics, or multi-language CLI architecture.

## Shared Assets

Primary guidance lives in `../shared/source-claude-skill.md`.

Load references from `../shared/references/` as needed:

- `design-patterns.md`
- `ux-patterns.md`
- `python-cli.md`
- `node-cli.md`
- `go-cli.md`

## Response Contract

- make command behavior predictable and script-friendly
- design clear help text, flags, and exit codes
- preserve backwards compatibility when changing existing commands
- include runnable examples for the main workflows
