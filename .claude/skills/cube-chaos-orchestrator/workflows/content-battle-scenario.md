# Workflow: a new battle-type scenario (new `SCENARIO:` with a `MAP:` body)

Covers authoring a genuinely new *kind* of battle screen — a new `SCENARIO: Name` with its own `MAP:`/`STARTINGMANA:`/`WORLDABILITY:`/`APPLYTERRAINPERKS`/`CUBE_SELECTION` body, distinct from a Terrain perk (which reuses the existing `Battle`/`Cursed_Battle`/`Boss_Battle` wrapper and only changes the map layout underneath it — see `content-terrain.md`) or a bespoke fixed-hand challenge (see `content-challenge-scenario.md`). Use this workflow when the ask is "a new kind of normal-ish battle node" — e.g. a battle with a unique win/loss twist that should be pickable as an ordinary map node, not a one-off superboss gauntlet.

## Gather before writing anything

- What makes this battle different from a normal `Battle`/`Cursed_Battle`/`Boss_Battle` — a different reward payout, a different win/loss condition, different starting mana, etc. Get this in plain language first.
- Whether it should still respect an equipped Terrain perk (almost certainly yes — every real battle-type scenario does) or deliberately ignore terrain (no real precedent for this; flag it to the user as a departure if requested).
- Which existing `.c.txt` file in the active mod this belongs in, or whether it needs a new one.

## Preview-and-approve gate (before the Sequence below)

Print the new scenario's theme/twist, its `WORLDABILITY:` win/loss chain (the real DSL, not a paraphrase), and its reward payout, then get the user's explicit OK before writing the file — same discipline as the orchestrator's Step C gate for cube/perk content, adapted since a battle scenario has no sprite of its own (it's referenced by an existing `CubeImage:`, not a new icon).

## Sequence

1. **`cube-chaos-scenario-scripting`**'s `references/battle-and-terrain-maps.md` — copy the base `Battle` wrapper's shape (`MAP: 52 28`, `STARTINGMANA:`, `RANDOMFITTINGSETUP:`, `AI:`, `SECONDARYREVEALEDHAND:`, the `WORLDABILITY: NormalWinLoss` + `AfterYouLose`/`BeforeYouWin`/`AfterYouWin` set, `APPLYTERRAINPERKS`, `EndMapData`, the terrain-dispatch `START_ACTION:`, `CUBE_SELECTION`), then change only the specific `WORLDABILITY:` line(s) that implement the new twist.
2. Keep the terrain-dispatch `START_ACTION:` block identical to a real battle scenario's (the `IfElse PerkExists ... Terrain` check + the 4 `TriggerWorldSomething`/fallback `ReadAPartialScenario` calls) unless the user explicitly wants this battle type to ignore equipped Terrain perks.
3. If this battle needs a fixed/scripted hand instead of `RANDOMFITTINGSETUP:`, that's actually the Challenge shape — see `content-challenge-scenario.md` instead.
4. **`cube-chaos-rule-text`** — the scenario's `Info:` line is short flavor/rules text, same tone as real scenario `Info:` lines (e.g. `Cursed_Battle`'s "Cursed Battle, but gain 5 more gold and a consumable").
5. Wire the new scenario into a map node: either a new `MAP_NODE: <Name> <weight> [body] End` in an existing `NODEMAP:` (see `content-nodemap.md` if editing one), or a `ReadAScenario`/`TriggerCampaignSomething` hook from an existing perk/scenario, depending on how the user wants it reached.
6. **Test-launch** — `cube-chaos-mod-setup`'s loop, then actually play into this battle type at least once to confirm the win/loss twist behaves as intended (a battle-scenario bug is exactly the kind of silent/no-parse-error issue the launch gate exists for).

## If this is an edit, not a fresh scenario

Read `workflows/editing-checklist.md` first.
