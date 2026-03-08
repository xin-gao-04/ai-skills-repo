# Debugging Wizard For Claude

Use this adapter when the user needs root-cause analysis, stack-trace investigation, log correlation, or a systematic debugging workflow.

## Shared Assets

Primary guidance lives in `../shared/source-claude-skill.md`.

Load references from `../shared/references/` as needed:

- `debugging-tools.md`
- `common-patterns.md`
- `strategies.md`
- `quick-fixes.md`
- `systematic-debugging.md`

## Response Contract

- reproduce first when possible
- state evidence before proposing a fix
- isolate one hypothesis at a time
- add prevention guidance such as tests or safeguards
