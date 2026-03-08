# API Designer For Claude

Use this adapter when the user wants REST or GraphQL API design, OpenAPI authoring, versioning strategy, pagination patterns, or error model design.

## Shared Assets

Primary guidance lives in `../shared/source-claude-skill.md`.

Load references from `../shared/references/` as needed:

- `rest-patterns.md`
- `versioning.md`
- `pagination.md`
- `error-handling.md`
- `openapi.md`

## Response Contract

- start from resource modeling before endpoint details
- deliver a consistent request and response contract
- include versioning, auth, and error semantics
- produce OpenAPI-ready output when the task calls for a spec
