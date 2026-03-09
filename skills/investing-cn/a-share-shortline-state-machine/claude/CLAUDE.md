# A Share Shortline State Machine For Claude

Use this adapter for fast-cycle A-share analysis centered on state recognition, setup matching, and risk interception.

## When To Use

- shortline market state judgment
- dragon-head, repair, expansion, crowding, or fade analysis
- leaderboard interpretation with explicit skepticism toward seat mythology
- case mapping against prior A-share shortline examples
- kill-switch style risk control for speculative names or themes

## Workflow

1. Confirm public facts first.
2. Classify the market state.
3. Match the target to a setup only if the state supports it.
4. Apply kill switches.
5. Map to historical cases and explain key differences.
6. End with action bias, invalidation, and uncertainty.

## Required References

- `../shared/references/rules/state_machine.yaml`
- `../shared/references/rules/setup_rules.yaml`
- `../shared/references/rules/kill_switches.yaml`
- `../shared/references/cases/case_library.yaml`
- `../shared/references/scoring/scoring_weights.yaml`
- `../shared/references/templates/analysis_template.md`
- `../shared/references/source-system-prompt.md`

## Output Contract

Output a Markdown report with:

1. market state recognition
2. setup recognition
3. positive evidence
4. negative evidence
5. case mapping
6. score and explanation
7. conclusion
8. invalidation conditions
9. uncertainty points

Always separate facts, inference, and unknowns. Do not treat famous seats as high-confidence confirmation.

