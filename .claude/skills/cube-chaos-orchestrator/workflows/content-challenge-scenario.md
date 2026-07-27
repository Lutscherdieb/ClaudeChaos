# Workflow: a bespoke challenge battle (fixed-hand gauntlet)

Covers a one-off "superboss"/gauntlet battle with a scripted enemy hand and a single thematic rule-twist — the real-game shape is `The_Rich`/`The_Dream`/`The_Eternal`/`The_Replacement`, reached from the endgame's "Challenge the universe" choice. Also covers building a new `CHOICE:` branching menu generally, since challenges are entered/exited through one.

## Gather before writing anything

- The challenge's one specific twist, in plain language, and the exact `WORLDABILITY:` chain that implements it (this is the whole point of a challenge — get this right before anything else).
- The fixed enemy hand: which cubes, in which of the 6 hand slots.
- Where the challenge is reached from — an existing `CHOICE:` menu (add a new option) or a new one.

## Preview-and-approve gate (before the Sequence below)

Print the challenge's twist as the real `WORLDABILITY:` DSL chain (not a paraphrase), the fixed `HAND:` list, and the `CHOICE:` entry that reaches it (label text + condition, if any), then get the user's explicit OK before writing any file.

## Sequence

1. **`cube-chaos-scenario-scripting`**'s `references/challenge-and-branching-choices.md` — copy the closest real challenge's full structure (the `Battle`-wrapper shape from `references/battle-and-terrain-maps.md`, with `HAND:` replacing `RANDOMFITTINGSETUP:`, and both `AfterYouWin`/`AfterYouLose` redirecting to `End_Of_Everything_NO_CHALLENGE` or an equivalent no-loop-back ending), then swap in the new twist's `WORLDABILITY:` line and the new `HAND:` list.
2. Add or edit the `CHOICE:` scenario that reaches this challenge — a new `Choice:` entry with its label, the `ReadAScenario <NewChallenge>` action, and a `Condition:` if it should only appear in some state.
3. **`cube-chaos-rule-text`** — the scenario's `Info:` line should describe the twist plainly (real examples: "The Eternal: Every 10 seconds every enemy leader's hp is set to 1000") since this is the *only* place the player learns the rule before entering.
4. **Test-launch** — `cube-chaos-mod-setup`'s loop, then actually play the challenge at least once to confirm the twist behaves as intended and the win/loss redirects land correctly.

## If this is an edit, not a fresh challenge

Read `workflows/editing-checklist.md` first.
