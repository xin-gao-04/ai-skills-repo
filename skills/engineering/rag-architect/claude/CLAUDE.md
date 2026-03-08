# RAG Architect For Claude

Use this adapter when the user is designing or improving a retrieval-augmented generation system, including chunking, indexing, retrieval quality, and evaluation.

## Shared Assets

Primary guidance lives in `../shared/source-claude-skill.md`.

Load references from `../shared/references/` as needed:

- `chunking-strategies.md`
- `embedding-models.md`
- `retrieval-optimization.md`
- `vector-databases.md`
- `rag-evaluation.md`

## Response Contract

- make the retrieval pipeline explicit end to end
- separate recall, precision, latency, and cost tradeoffs
- include evaluation criteria rather than only architecture sketches
- identify the highest-risk failure modes and mitigations
