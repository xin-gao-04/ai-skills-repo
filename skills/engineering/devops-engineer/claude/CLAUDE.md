# DevOps Engineer For Claude

Use this adapter when the user needs CI/CD design, deployment automation, containerization, infrastructure-as-code, Kubernetes operations, or incident response guidance.

## Shared Assets

Primary guidance lives in `../shared/source-claude-skill.md`.

Load references from `../shared/references/` as needed:

- `deployment-strategies.md`
- `docker-patterns.md`
- `github-actions.md`
- `kubernetes.md`
- `terraform-iac.md`
- `incident-response.md`

## Response Contract

- optimize for repeatable, observable delivery
- call out rollout and rollback strategy explicitly
- include security and secrets handling in the plan
- validate the deployment path with concrete commands where possible
