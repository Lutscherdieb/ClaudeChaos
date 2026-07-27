# Workflow: a new reward/economy map-node (chest, shop, forge, trade)

Covers a new non-combat map-node screen — a themed perk/cube chest, a shop variant, a forge variant, a curse-trade variant, or a simple flavor-effect node (heal-with-a-catch, a coin bonus). Most of these are small deltas on an existing real reward scenario, not new mechanisms — see `cube-chaos-scenario-scripting`'s `references/reward-and-economy-scenarios.md` for the confirmed field tables before assuming a new field is needed.

## Gather before writing anything

- What the node actually grants/costs, in plain language, and which existing block type it maps to: `PERK_REWARD:` (perk chest/trade), `CUBE_REWARD:` (cube chest), `SHOP:`, `CURSED_TRADE:`, or `PERK_SELECTION:` (Forge-style upgrade, or a `TYPE: 2` trash/destroy screen) — or, if it's just a one-shot effect plus a redirect, the simpler flavor-text-+-`START_ACTION:` shape (see the reference file's first section).
- Any twist on the base version (a cost, a restriction, a bonus) — this is usually the whole ask, e.g. `Painfull_Perk_Chest` = `Basic_Perk_Reward` + "lose 1 life first."

## Preview-and-approve gate (before the Sequence below)

Print the node's effect (the real `START_ACTION:`/block fields, not a paraphrase), which real scenario it's modeled on, and its `Info:`/`CubeImage:`, then get the user's explicit OK before writing the file.

## Sequence

1. **`cube-chaos-scenario-scripting`**'s `references/reward-and-economy-scenarios.md` — pick the closest real scenario and copy its block structure, applying only the requested twist (an extra `START_ACTION:` effect before/after a `ReadAScenario` into an unchanged base reward block is the standard pattern for "existing reward, plus a catch").
2. If the node needs a genuinely new pool restriction (a new `BELONGSTO:`/`PERKREQ:` filter), confirm the exact `BelongsTo:`/predicate string against real perk data rather than guessing.
3. Wire the node into a map: a new `MAP_NODE:` entry in an existing `NODEMAP:` (see `content-nodemap.md`), or a direct `ReadAScenario` from an existing perk/scenario.
4. **`cube-chaos-rule-text`** — the `Info:` line should state the effect and any catch plainly (real examples: "Perk Chest, but if you have more than 1 life lose 1").
5. **Test-launch** — `cube-chaos-mod-setup`'s loop, then actually open/use the new node once to confirm the reward/cost applies as intended.

## If this is an edit, not a fresh scenario

Read `workflows/editing-checklist.md` first.
