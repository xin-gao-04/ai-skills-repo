# Code Documenter For Claude

Use this adapter when the user wants code documentation, API docs, coverage-oriented documentation work, or developer-facing guides produced from an existing codebase.

## Shared Assets

Primary guidance lives in `../shared/source-claude-skill.md`.

Load references from `../shared/references/` as needed:

- `documentation-systems.md`
- `coverage-reports.md`
- `interactive-api-docs.md`
- `python-docstrings.md`
- `typescript-jsdoc.md`

## Response Contract

- document real behavior from the codebase rather than inferred behavior
- prefer concise, navigable documentation structures
- include examples where they reduce ambiguity
- call out any gaps between code and docs
