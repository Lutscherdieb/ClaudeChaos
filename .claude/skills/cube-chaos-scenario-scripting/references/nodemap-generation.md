# Campaign node-map generation (`NODEMAP:`)

Load this when designing a new campaign/world map screen — the branching node graph the player walks through between battles (Battle/Heal/Shop/Perk_Chest/Boss_Battle/etc. nodes). All real examples are from `Extra_Mechanics/NodeMap_Scenarios.c.txt` — the sole source in the base game (see the parent skill's Ground truth section). Only 5 real `NODEMAP:` blocks exist (`First_Map`, `Second_Map`, `Third_Map`, `Loop_Map`, `The_Challenges`), so treat "copy the closest real map and adjust the node list" as the practical method, not "derive new layer/connection numbers from the grammar" — several of this DSL's numeric fields have no documentation anywhere and their exact generation algorithm isn't determinable from the text files alone (flagged explicitly below wherever that applies, same honesty standard as `cube-chaos-scripting`'s perk-economy shop-filter note).

## The entry point: `SCENARIO: Campaign`

A `NODEMAP:`-based map is reached from a `SCENARIO: Campaign` — the scenario equivalent of the game's own "start" button:

```
SCENARIO: Campaign
Info: A series of maps with escalating difficulty and rewards, equivalent to the start button in the main menu End
STARTINGPOINT
MaxScore: 1
End

CAMPAIGN:

STARTING_LIVES: 3

PERK: Reroll_Cost_Increase
PERK: Terrain_Depth_Generation
PERK: Debt_Effects
PERK: Gravity
PERK: Pandoras_Box
PERK: Spell_Ghosts
PERK: Overflow_Deal

End

PERK_SELECTION: 
TYPE: 1 
End

START_ACTION: Both ReadAScenario First_Map ReadAScenario Class_Species_Selection

SEnd
```

`STARTINGPOINT` (bare keyword in the header) marks this as a selectable game-mode entry, `MaxScore:` is a run-completion score cap. The `CAMPAIGN:` body's `PERK:` list grants a fixed set of `BelongsTo: NULL` system-rule perks at run start (see `cube-chaos-scripting`'s perk-economy `BelongsTo: NULL` note) — these are what actually implement rules like "terrain depth increases over time" or "debt exists," not the `NODEMAP:` itself. **A new game mode is a new `SCENARIO: Campaign`-shaped scenario**; a new map *within* the existing campaign is just a new `NODEMAP:`-bodied scenario referenced from somewhere (typically `End_Map_Portal`'s or another map's own dispatch logic) — the far more common ask, and what the rest of this file covers.

## `NODEMAP:` block shape

```
SCENARIO: First_Map
Info: The first map with battles End
CubeImage: The_Vortex
End
NODEMAP:

RESET_NODE_MAP

BACKGROUND_COLOUR: 0 100 0

DEAD_END_SCENARIO: Nowhere_To_Go

RANDOMIZED_PATH_SYSTEM:

 MAP_NODE: NULL 45 End
 MAP_NODE: Battle 45 End
 MAP_NODE: Heal 45 End
 MAP_NODE: Perk_Chest 45 End
 MAP_NODE: Boss_Battle 60
  SECRETMODIFIER: Boss_Scaling
  EXTRA_DIFFICULTY: 1
 End
 MAP_NODE: Cursed_Battle 45
  EXTRA_MODIFIER
  EXTRA_DIFFICULTY: 1
 End
 MAP_NODE: Random_Event 45 End
 MAP_NODE: Cursed_Trade 45 End
 MAP_NODE: Shop 45 End
 MAP_NODE: End_Map_Portal 45 End
 MAP_NODE: Map_Forge 45 End

 LAYER: 1 1 0
 LAYER: 1 1 1
 LAYER: 3 1 3
 LAYER: 5 1 1
 LAYER: 5 1 1
 LAYER: 5 1 1
 LAYER: 3 1 3
 LAYER: 1 1 4
 LAYER: 2 1 8
 LAYER: 1 1 9

 REPLACEINLAYER: 3 3 2 1 6
 REPLACEINLAYER: 5 5 1 1 6
 REPLACEINLAYER: 5 5 1 1 7
 REPLACEINLAYER: 2 6 4 1 5
 REPLACEFIRSTINLAYER: 8 8 1 8 10

 CLOSESTPATHS

 CONNECTION: 3 4
 CONNECTION: 3 4
 CONNECTION: 3 4
 CONNECTION: 3 4
 CONNECTION: 3 4
 CONNECTION: 3 4
 CONNECTION: 3 4
 CONNECTION: 3 4

End

STARTING_NODE: 0

End

SEnd
```

### Confirmed, stable-meaning fields

- **`RESET_NODE_MAP`** — bare keyword, clears any previous map state. Appears once, always first inside `NODEMAP:`.
- **`RESET_GLOBAL_MODIFIERS`** + **`ADD_CURRENT_TO_GLOBAL_MODIFIERS`** — appear as a pair, before `RESET_NODE_MAP`, in every map *after* the first (`Second_Map`/`Third_Map`/`Loop_Map`, never `First_Map`). Reads as "snapshot this run's accumulated modifiers into the persistent global pool before starting a fresh map" — include this pair on any new map meant to follow an earlier one in sequence, omit it only for a genuine first/entry map.
- **`BACKGROUND_COLOUR: r g b`** — the node-map screen's background tint. Every real map uses a different color (green `0 100 0`, teal `0 100 100`, olive `100 100 0`, pinkish `110 100 100` for the challenge gauntlet) — pick a new, unused triple for a new map so it reads as visually distinct.
- **`DEAD_END_SCENARIO: Name`** — the scenario read if the player reaches a node with no outgoing connections. Every real map uses `Nowhere_To_Go` (a `CHOICE:` scenario offering "take 5 curses to reach a new map" — see `references/challenge-and-branching-choices.md`); reuse it rather than inventing a new dead-end unless the new map has a genuinely different dead-end story beat.
- **`RANDOMIZED_PATH_SYSTEM:`** wraps the actual node-graph generation body (everything below down to its matching `End`).
- **`MAP_NODE: ScenarioName weight [body] End`** — declares one node type usable in this map. `weight` is a relative pick-frequency (real values cluster at `45`; `60` for `Boss_Battle`, meaning boss nodes are picked somewhat *more* often when eligible, not less). Node bodies are optional:
  - **`SECRETMODIFIER: Name`** — attaches a named modifier to this node type (`Boss_Battle`'s `Boss_Scaling`, unconfirmed further than "some kind of scaling tag read by the boss-battle logic").
  - **`EXTRA_DIFFICULTY: N`** — adds `N` difficulty specifically when this node type is hit (used on `Boss_Battle` and `Cursed_Battle`).
  - **`EXTRA_MODIFIER`** — bare flag, seen only on `Cursed_Battle`; exact effect unconfirmed.
  - **The order `MAP_NODE:` blocks are declared in this list is significant** — later `LAYER:`/`REPLACEINLAYER:` fields reference node types by their declaration position (see below), not by name.
- **`STARTING_NODE: 0`** — the graph index the player starts on (every real map uses `0`).
- **`CLOSESTPATHS`** — bare keyword, appears once, always immediately before the `CONNECTION:` lines; reads as "connect nodes by nearest-neighbor" but the precise pathing algorithm isn't determinable from the text alone.

### Fields to copy wholesale rather than hand-derive

**`LAYER:`, `REPLACEINLAYER:`, `REPLACEFIRSTINLAYER:`, and `CONNECTION:` have no documentation anywhere** (`ModdingInfo.txt`/`ModdingExplanation.txt` are both silent on the whole `NODEMAP:` DSL) and their exact numeric semantics aren't confidently reverse-engineerable from just 5 real examples — e.g. `LAYER: 1 1 0`'s three numbers plausibly read as (node-count-in-this-layer, some per-node connectivity parameter, a `MAP_NODE:`-list index used as that layer's default fill), but this isn't independently confirmed, and getting a layer/connection number subtly wrong risks a technically-loading but broken/unplayable map graph with no parse error to catch it (unlike the `Ability:`-chain DSL, there's no `Log.txt` signal for "this map's connectivity is wrong"). **The practical, lower-risk method: pick the real map whose node-type list is closest to what the new map needs, copy its entire `LAYER:`/`REPLACEINLAYER:`/`REPLACEFIRSTINLAYER:`/`CONNECTION:` block structure unchanged, and only edit the `MAP_NODE:` declarations themselves** (which node types exist, their weights, their `SECRETMODIFIER:`/`EXTRA_DIFFICULTY:` bodies) — every real map's layer/connection shape is near-identical anyway (10 layers, a `REPLACEFIRSTINLAYER:` near the end pulling in the map-portal exit node, 8 `CONNECTION:` lines), so this covers the realistic "add a new map to the campaign" case without needing the exact algorithm. If a genuinely novel graph shape is needed (not just a reskin of an existing map's node list), say so explicitly to the user rather than presenting a hand-derived layer/connection block as confirmed-correct.

## Rewriting an already-generated map from a `PERK:` (the common case — no new `NODEMAP:` needed)

**Before writing a new `NODEMAP:` because a request says "change what nodes the map has," check whether it's actually asking to *rewrite* nodes on the existing map — that's a `PERK:` with a `CampaignAbility:`, not a new map.** Every real "the map is different now" effect in the base game works this way; not one of them defines its own `NODEMAP:`.

The four productions involved (all in `ModdingInfo.txt`'s ordinary `Action`/`BOOLEAN`/`DOUBLE` lists, usable from any normal ability chain):

| Production | Signature | Meaning |
|---|---|---|
| `EveryMapNodeWhich` | `BOOLEAN Action` | Loop over every node on the current map; candidate binds to `Test` |
| `MapNodeIsType` | `DOUBLE String` | Does this node carry that type tag? |
| `SetMapNodeScenario` | `DOUBLE String` | Replace which `SCENARIO:` the node runs |
| `SetMapNodeExtraModifier` | `DOUBLE PERK` | Attach a modifier perk to the node (`Boss_Scaling`, etc.) |

Copyable reference implementation — `Main/NeutralPerks.c.txt:359`, `PERK: Boss_Rush`:

```
CampaignAbility: AfterAMapIsGenerated EveryMapNodeWhich MapNodeIsType Test Battle
 Both SetMapNodeScenario Test Boss_Battle
  SetMapNodeExtraModifier Test PerkConstant Boss_Scaling
```

### `MapNodeIsType` is a **tag** test, not scenario-name equality — filter accordingly

A `Boss_Battle` node answers `True` to **both** `Battle` and `Boss`; a `Cursed_Battle` node answers `True` to both `Battle` and `Cursed_Battle`. So `MapNodeIsType Test Battle` alone matches plain, cursed **and** boss battles.

- **To hit only plain battles, write the exclusion explicitly**: `And MapNodeIsType Test Battle Not MapNodeIsType Test Boss` — this is `Main/Curses.c.txt:790-792`'s own real filter.
- **To test "the node I'm standing on is a boss battle", nest both tags**: `If MapNodeIsType CurrentMapNode Boss If MapNodeIsType CurrentMapNode Battle` (`Main/UpgradeConsumables.c.txt:222`, `Repeating_Bottled_Universe`) — or just the `Boss` tag alone, which is what `Extra_Mechanics/Blights.c.txt:116` does.
- Real guards used alongside: `IsLarger Test DoubleConstant 0` (skip node 0, the one already occupied) and `ExcludeLastXNodes DoubleConstant N` (leave the map exit alone).

**Verify by naming the exclusion out loud before you write the filter**: state which of plain / cursed / boss the effect should hit, then check the `BOOLEAN` has one clause per exclusion. A bare `MapNodeIsType Test Battle` that was *meant* to be "normal battles only" produces no error — it just also eats the cursed and boss nodes.

### The first map is generated BEFORE class/species selection — a `BelongsTo: CLASS`/`SPECIES` perk must also fire its chain from an `ObtainAction:`

`SCENARIO: Campaign`'s entry point is `START_ACTION: Both ReadAScenario First_Map ReadAScenario Class_Species_Selection` (`Extra_Mechanics/NodeMap_Scenarios.c.txt:25`) — the map is read **first**, so `AfterAMapIsGenerated` has already fired and finished by the time the player picks a class and its perk is granted. A class perk whose whole identity is map-node rewriting therefore **silently does nothing on map 1** and only starts working on map 2. No error, no warning; it just looks like the class is broken for its first ten minutes.

**Rule: put the chain in a `COMPOUND: ACTION` and reference that compound from BOTH `CampaignAbility: AfterAMapIsGenerated` and `ObtainAction:`. Never write the chain out twice.**

```
COMPOUND: ACTION
CrusaderBossConversion
EveryMapNodeWhich And MapNodeIsType Test Battle Not MapNodeIsType Test Boss
 If X%Chance DoubleConstant 50
  Both SetMapNodeScenario Test Boss_Battle
   SetMapNodeExtraModifier Test PerkConstant Boss_Scaling
End

PERK: Crusader
CampaignAbility: AfterAMapIsGenerated CrusaderBossConversion   <- maps 2..N
ObtainAction:                         CrusaderBossConversion   <- map 1, at class selection
```

A `COMPOUND: ACTION` takes no parameters and needs no `Text:` (it isn't an `ABILITY`); `Characters/Classes/Programmer.c.txt`'s `GetLeastFragment` is the base game's own precedent for one called from several sites. Put it at the top of the perks file — `COMPOUND:` blocks don't consume sprite slots (slot index counts only `^CUBE:`/`^PERK:` lines), same as `General_Perks.c.txt`'s `BloodthirstX`.

**Verification: `grep -c 'EveryMapNodeWhich' <file>` must be exactly 1.** More than one means the chain got written out per-site again.

**This rule first shipped as "repeat that exact chain verbatim as an `ObtainAction:`", verified by a grep that both sites exist — and the session that wrote it violated it within the hour** (2026-08-02, `Crusader`). A follow-up "make it 50% instead of always" edit changed the `CampaignAbility:` copy and silently left the `ObtainAction:` copy unconditional, so every run's *first* map stayed 100% boss battles; the user caught it in play after four runs. The old grep-count check passed the entire time, because both sites still *existed* — it only ever verified presence, never agreement. **A verification step that cannot detect drift is not a verification step, and any rule of the form "keep these two copies in sync" will eventually be edited on one side only.** Hence the compound: there is now exactly one copy and nothing to keep in sync. (This does *not* apply to a mid-run pickup like `Boss_Rush`, which is only ever offered when a later map still exists — hence its `Requirement: MapLeft` and its lack of an `ObtainAction:`. Copying `Boss_Rush` verbatim onto a class perk is exactly how this bug gets introduced, since the omission looks deliberate in the source you copied from.) Found 2026-08-02 while building the `Crusader` class, whose base perk is precisely this effect. For the wider `ObtainAction:`/`CampaignAbility:`/`WorldAbility:` trigger-choice question this sits inside, see `cube-chaos-scripting/references/perk-economy.md` (which points back here for this specific trap).

### What reusing `SCENARIO: Boss_Battle` actually costs

Before writing a custom boss-node scenario "so it has a reward," check the base one — it already has a better one than a normal battle (`Extra_Mechanics/Battle_Scenarios.c.txt:83`):

| | `Battle` | `Boss_Battle` |
|---|---|---|
| Gold on win | 15 | **30** |
| Cube reward | `Basic_Cube_Reward` | **`Rare_Cube_Reward`** (skipped on the final map) |
| XP | `DifficultyXP` | **4×** `DifficultyXP` |
| Difficulty added | +1 | **+2** (plus `EXTRA_DIFFICULTY: 1` on the node and `Boss_Scaling`) |
| On loss | lose a life, move on | lose a life **and `ReadAScenario Boss_Repeat`** — refight the same boss |

So a mod only needs its own boss scenario if it wants to *change* one of those — most often to slow the difficulty ramp or drop the forced refight, both of which compound badly once *every* node is a boss.

## The endgame / New-Game+ loop

`Third_Map`'s exit reads `Winning_Map_Portal` → `End_Of_Everything`, a `CHOICE:` scenario (see `references/challenge-and-branching-choices.md`) offering: accept victory and end the run, or **`ReadAScenario Loop_Map`** (a `NODEMAP:` shaped exactly like `Third_Map` but escalated, `EXTRA_DIFFICULTY: 3` on its `Boss_Battle`) to continue with a fresh map and grant the player the `Void` perk (which is what actually unlocks the Nightmare-selection pool — see `cube-chaos-scripting`'s perk-economy Blight/Boon/Nightmare section), or challenge `The_Challenges` (a separate small `NODEMAP:` of bespoke gauntlet battles — see `references/challenge-and-branching-choices.md`). **A new endgame branch follows this same shape**: a `CHOICE:` scenario with one option `ReadAScenario`-ing a new `NODEMAP:`-based map, rather than inventing a new mechanism.
