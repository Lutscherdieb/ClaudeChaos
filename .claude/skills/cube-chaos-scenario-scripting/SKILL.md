---
name: cube-chaos-scenario-scripting
description: Use whenever authoring the SCENARIO:/MAP:/NODEMAP:/CHOICE: file-level DSL for a Cube Chaos mod - a genuinely different sublanguage from CUBE:/PERK: Ability chains (covered by cube-chaos-scripting), used for battle-map layouts (Terrain perks), campaign node-maps, reward/economy screens (shops, chests, the Forge), and bespoke branching/challenge scenarios. Trigger on "SCENARIO:", "battlefield", "battle map", "terrain perk", "node map", "campaign map", "NODEMAP:", "CHOICE:", "shop scenario", "challenge scenario", "DATARECT", "PLACERECT", or when a GameData/<Mod>/*.c.txt file needs a SCENARIO: block instead of a CUBE:/PERK: block.
---

# Cube Chaos scenario/map scripting DSL

`cube-chaos-scripting` covers `CUBE:`/`PERK:` blocks and the `Ability:`/`WorldAbility:` trigger-chain DSL that runs *inside* them. This skill covers a structurally different, file-level DSL: `SCENARIO:` blocks, which define whole screens/flows — a battle's map layout, the campaign's branching node-map, a shop/chest/forge economy screen, a bespoke challenge battle, or a branching `CHOICE:` menu. A `SCENARIO:` isn't something a `CUBE:`/`PERK:` grants directly; it's read into by name via `ReadAScenario`/`ReadAPartialScenario`/`TriggerWorldSomething` calls from inside an `Ability:`/`WorldAbility:`/`CampaignAbility:` chain — see "Bridging from Ability chains" below.

## Ground truth: the entire scenario/map layer lives only in `Extra_Mechanics`

Unlike the `CUBE:`/`PERK:` layer — where `Base_Core`/`Characters`/`Main` hold the bulk of canonical examples and `Extra_Mechanics`/`Modding_Example` are comparatively peripheral — for this DSL, **`GameData/Extra_Mechanics/` is the sole and complete implementation of every `SCENARIO:` in the entire base game.** Confirmed by directory listing: `Base_Core/` and `Main/` contain zero `.c.txt` files with any `SCENARIO:` block at all (checked exhaustively — `Base_Core` has `1Compounds.c.txt`/`2AiCompounds.c.txt`/`3TokenCubes.c.txt`/`GameRulePerks.c.txt`/`ToolTipText.c.txt`, `Main` has `Perks.c.txt`/`Curses.c.txt`/`Consumables.c.txt`/etc. — none define a `SCENARIO:`). Every battle screen, the entire campaign node-map, every shop/chest/forge, and all branching endgame `CHOICE:` menus in the actual shipped game are defined in `Extra_Mechanics/Battle_Scenarios.c.txt`, `NodeMap_Scenarios.c.txt`, `Reward_Scenarios.c.txt`, `Challenge_Scenarios.c.txt`, `Battle_Maps.c.txt`, and `TerrainPerks.c.txt`. Treat these six files as the definitive reference, not merely convenient examples — same read-only rule applies (`CLAUDE.md`): read freely, never edit.

Neither `ModdingInfo.txt` (grammar production lists) nor `ModdingExplanation.txt` (CUBE header prose) documents this file-level DSL at all — they only cover the `Ability:`-chain layer and its `Trigger`/`Action`/`BOOLEAN`/etc. production lists. The one exception: the three bridge functions below (`ReadAScenario`/`ReadAPartialScenario`/`TriggerWorldSomething`) *are* in `ModdingInfo.txt`'s production lists, since they're called from inside an ordinary `Ability:` chain.

## Universal `SCENARIO:` block shape

```
SCENARIO: Name
Info: <flavor text, ends with the literal word End> End
CubeImage: SomeExistingCubeName        (optional — icon shown for this scenario's map node/choice; references an existing CUBE:, not a new sprite)
PerkImage: SomeExistingPerkName        (optional alternative to CubeImage:, same idea)
End
<exactly one body-type block>
SEnd
```

The header (`SCENARIO: Name` through the first `End`) is always the same shape. The body is exactly one of: `MAP:`/`ADDITIONALMAP:` (a battle or partial battle-map — see `references/battle-and-terrain-maps.md`), `NODEMAP:` (a campaign map — see `references/nodemap-generation.md`), `PERK_REWARD:`/`CUBE_REWARD:`/`SHOP:`/`CURSED_TRADE:`/`PERK_SELECTION:`/`CLASS_SELECTION`/`DOUBLE_SIDED_PERK_SELECTION:` (an economy/reward screen — see `references/reward-and-economy-scenarios.md`), `CHOICE:` (a branching menu — see `references/challenge-and-branching-choices.md`), or a bare `START_ACTION:` with no other body (a scenario that's just a one-shot effect plus a redirect to another scenario, e.g. `Heal`, `Map_Forge`). `SEnd` always closes the whole block, distinct from a `CUBE:`/`PERK:` block's plain `End`.

**A scenario name is referenced as a bare, unquoted identifier everywhere** — `ReadAScenario Shop`, `ReadAPartialScenario Earth_Terrain`, `TriggerWorldSomething Battle_Terrain_Generation` — never wrapped in `StringConstant`, even though `ModdingInfo.txt` types these functions' argument as `String`. Match this exactly; it's the scenario-DSL's own convention distinct from ordinary `STRING`-typed DSL arguments elsewhere.

## Bridging from `Ability:`/`WorldAbility:`/`CampaignAbility:` chains

Three functions cross from the ordinary cube/perk ability layer into this scenario layer (confirmed in `ModdingInfo.txt`'s production list, `ReadAScenario` line 346, `ReadAPartialScenario` line 380, `TriggerWorldSomething` line 381):

- **`ReadAScenario <Name>`** — jump to a whole new scenario (a map node's `START_ACTION:`, an endgame `Choice:`, a perk that opens a shop/chest on the spot).
- **`ReadAPartialScenario <Name>`** — merge in *part* of a scenario's map data (used exclusively for battle-map composition — layering a terrain's ground layout, then a leader-placement layout, then a boss layout onto the same battle; see `references/battle-and-terrain-maps.md`).
- **`TriggerWorldSomething <Name>`** — fire a named signal that any `WorldAbility: AfterWorldSomething ...` chain listening for that exact name can react to (this is how `Battle_Terrain_Generation`/`Battle_Player_Generation`/`Battle_Enemy_Generation`/`Battle_Boss_Generation` actually reach a Terrain perk's `MapGenerationTPEB`-based `WorldAbility:` — see `references/battle-and-terrain-maps.md`).

## Research protocol — this skill first, base game second, write back always

1. **Check this skill and its `references/` files first.** Most block-shape and field questions for a given scenario type are already settled below.
2. **If not covered, go to the six `Extra_Mechanics` files named above** — they are this DSL's complete ground truth, not a sample of it (see above). Grep for a real working example of the exact block type before writing one from scratch; this DSL has the same near-zero error recovery as the `Ability:`-chain layer.
3. **Write the finding back into this skill (core file or the relevant `references/` file), in the same edit** — with the evidence (`file:line`, occurrence counts, or the exact real block copied from).

## Reference index — load only what the current task needs

| File | Load when you're... |
|---|---|
| `references/battle-and-terrain-maps.md` | Authoring a Terrain perk (battlefield layout), a new kind of battle scenario, or anything using `ADDITIONALMAP:`/`DATA:`/`DATARECT:`/`PLACERECT:`/`CAMPAIGNSETUP:` |
| `references/nodemap-generation.md` | Designing a new campaign/world map screen (`NODEMAP:`, `MAP_NODE:`, `LAYER:`, `CONNECTION:`, branching path generation) — **or rewriting an existing map's nodes from a `PERK:`** (`AfterAMapIsGenerated`, `EveryMapNodeWhich`, `MapNodeIsType`, `SetMapNodeScenario`), which is what "change what nodes the map has" almost always means |
| `references/reward-and-economy-scenarios.md` | Building a new non-combat map-node screen: a chest/shop/forge/curse-trade, or any `PERK_REWARD:`/`CUBE_REWARD:`/`SHOP:`/`PERK_SELECTION:` block |
| `references/challenge-and-branching-choices.md` | Building a bespoke fixed-hand challenge battle, or any `CHOICE:`/`Choice:`/`Condition:` branching menu |

## Debugging checklist

1. Read the exact error line the same way as the `Ability:`-chain layer — an unlabeled error is often a scoping/registration issue, not local syntax.
2. Grep the six `Extra_Mechanics` scenario files for real usage of the exact block/field you're using, and compare token-for-token.
3. Relaunch and recheck `Log.txt` after every fix — see `cube-chaos-mod-setup` for the test loop.
