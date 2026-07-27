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

## The endgame / New-Game+ loop

`Third_Map`'s exit reads `Winning_Map_Portal` → `End_Of_Everything`, a `CHOICE:` scenario (see `references/challenge-and-branching-choices.md`) offering: accept victory and end the run, or **`ReadAScenario Loop_Map`** (a `NODEMAP:` shaped exactly like `Third_Map` but escalated, `EXTRA_DIFFICULTY: 3` on its `Boss_Battle`) to continue with a fresh map and grant the player the `Void` perk (which is what actually unlocks the Nightmare-selection pool — see `cube-chaos-scripting`'s perk-economy Blight/Boon/Nightmare section), or challenge `The_Challenges` (a separate small `NODEMAP:` of bespoke gauntlet battles — see `references/challenge-and-branching-choices.md`). **A new endgame branch follows this same shape**: a `CHOICE:` scenario with one option `ReadAScenario`-ing a new `NODEMAP:`-based map, rather than inventing a new mechanism.
