---
name: a-share-shortline-state-machine
description: A-share shortline state-machine, setup, and risk-gate advisor for Chinese equities. Use when the user wants short-term market phase judgment, dragon-head or setup recognition, repair/main-up/expansion/crowding/fade analysis, hot-money or leaderboard interpretation, case mapping to historical A-share examples, and explicit invalidation or kill-switch rules for fast-moving speculative trades.
---

# A Share Shortline State Machine For Codex

Use this skill for shortline A-share analysis where timing, state recognition, and risk interception matter more than medium-term valuation.

## Core Workflow

1. Verify current market facts with public sources before making any state judgment.
2. Classify the market into one state first, then identify the target setup.
3. Apply kill switches after the setup check, not before.
4. Map the current target to the closest historical case and explain both similarity and difference.
5. End with action bias, invalidation conditions, and uncertainty points.

## State Machine

The state sequence is defined in `shared/references/rules/state_machine.yaml`.

- `S0`: cooldown or ice-point observation
- `S1`: repair
- `S2`: main uptrend
- `S3`: expansion
- `S4`: climax or crowding
- `S5`: fade confirmed
- `S6`: second-wave or second return

Always judge the state from market-wide evidence first:

- high-level names and whether they are补跌 or repaired
- limit-up and limit-down structure
- board break rate
- whether the leading theme still has sector-wide confirmation

Do not classify from a single stock in isolation.

## Setup Recognition

Use `shared/references/rules/setup_rules.yaml`.

Priority setups:

- `A`: main-line dragon-head confirmation relay
- `B`: core follower under the overall dragon-head
- `C`: trend-capacity rolling structure
- `D`: first repair batch after a fade
- `E`: high-recognition second-wave return

If the state and setup do not match, return `no setup` rather than forcing a bullish conclusion.

## Kill Switches

Use `shared/references/rules/kill_switches.yaml`.

Treat these as hard risk controls:

- serious abnormal volatility or risk notices
- retail-cluster takeover
- high-level synchronized fade
- suspected program-trading abnormality
- theme detached from company facts
- crowding
- exchange monitoring

If `K3` is triggered, prioritize a fade-confirmed interpretation and cap the action bias to avoid or observe.

## Evidence Standard

Separate all claims into:

- known facts
- reasonable inference
- unknown information

Never upgrade a thesis only because a famous seat or well-known trader appeared on the leaderboard. Seat labels are low-weight priors.

## Output Contract

Return the result as a Markdown report in this order:

1. market state recognition
2. setup recognition
3. positive evidence
4. negative evidence
5. case mapping
6. score and explanation
7. conclusion
8. invalidation conditions
9. uncertainty points

The report must include:

- current state and confidence
- why the target fits or does not fit a setup
- which kill switches fired
- closest historical case
- explicit action bias such as observe, trial, avoid, or only for leaders
- invalidation and uncertainty

## Required References

Read these as needed:

- `shared/references/rules/state_machine.yaml`
- `shared/references/rules/setup_rules.yaml`
- `shared/references/rules/kill_switches.yaml`
- `shared/references/cases/case_library.yaml`
- `shared/references/scoring/scoring_weights.yaml`
- `shared/references/templates/analysis_template.md`
- `shared/references/schemas/input.schema.json`
- `shared/references/schemas/output.schema.json`
- `shared/references/source-system-prompt.md`

## Practical Rules

- Browse for up-to-date market facts, announcements,监管,龙虎榜, and board statistics whenever the answer depends on the current trading cycle.
- If the user gives only a stock or theme, infer the minimum viable context from current market state and then state what remains unknown.
- In crowded or fading states, favor risk framing over entry-point storytelling.
- If data is incomplete, still output the best feasible judgment and explain exactly which missing data could change the call.

