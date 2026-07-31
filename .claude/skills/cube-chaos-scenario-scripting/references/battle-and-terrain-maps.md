# Battle scenarios, Terrain perks, and the map-layout DSL

Load this when authoring a Terrain perk (`BelongsTo: Terrain`), a new kind of battle scenario (a new `MAP:`-bodied `SCENARIO:`), or anything using `ADDITIONALMAP:`/`DATA:`/`DATARECT:`/`PLACERECT:`/`CAMPAIGNSETUP:`. This is the mechanism behind "how do I make a Terrain perk create its own battlefield."

All real examples below are from `Extra_Mechanics/Battle_Scenarios.c.txt`, `Extra_Mechanics/Battle_Maps.c.txt`, `Extra_Mechanics/TerrainPerks.c.txt`, and `Extra_Mechanics/1Compounds.c.txt` — the sole source for this whole mechanic (see the parent skill's Ground truth section).

## The base battle wrapper (`SCENARIO: Battle`/`Cursed_Battle`/`Boss_Battle`)

```
SCENARIO: Battle
Info: Normal Battle End
CubeImage: Fighting_Symbol
End
MAP: 52 28

STARTINGMANA: 2 50

RANDOMFITTINGSETUP: 2

AI: 2 True
SECONDARYREVEALEDHAND: 2

WORLDABILITY: NormalWinLoss
WORLDABILITY: AfterYouLose Both LoseALife If IsSmaller RemainingLives DoubleConstant 1 EndCampaign
WORLDABILITY: BeforeYouWin 1Shot GrantXP DifficultyXP
WORLDABILITY: AfterYouWin Both Both
ChangeCurrency DoubleConstant 15 
ReadAScenario Basic_Cube_Reward
ChangeDifficulty DoubleConstant 1 

APPLYTERRAINPERKS

EndMapData

START_ACTION: IfElse PerkExists ARandomPerkInInventoryWhich PerkIsType Test Terrain Both Both
  TriggerWorldSomething Battle_Terrain_Generation
  TriggerWorldSomething Battle_Enemy_Generation
  TriggerWorldSomething Battle_Player_Generation
 Both Both 
 ReadAPartialScenario Earth_Terrain
 ReadAPartialScenario Battle_Normal_Enemy
 ReadAPartialScenario Battle_Normal_Player

CUBE_SELECTION

SEnd
```

Field meanings, confirmed by comparing `Battle`/`Cursed_Battle`/`Boss_Battle`/`The_Rich`/`The_Dream`/`The_Eternal`/`The_Replacement` (7 real battle-type scenarios):

- **`MAP: width height`** — the battlefield's tile dimensions. Every real battle scenario in the base game uses `52 28`; there's no confirmed example of any other size, so treat `52 28` as the standard rather than an arbitrary sample.
- **`STARTINGMANA: faction amount`** — starting mana pool for that faction (faction `2` = the enemy in every real example; the player's own starting mana comes from class/species perks, not this field).
- **`RANDOMFITTINGSETUP: faction`** — randomizes that faction's starting hand/setup (used for the AI faction in every real example).
- **`AI: faction True`** — marks a faction as AI-controlled.
- **`SECONDARYREVEALEDHAND: faction`** — reveals that faction's hand to the player (the enemy's hand is visible in normal battles).
- **`WORLDABILITY:`** (repeatable) — same underlying DSL as a `CUBE:`/`PERK:`'s `WorldAbility:`, but using a distinct set of *battle-outcome*-scoped triggers not used anywhere in the cube/perk layer: `NormalWinLoss` (a built-in bare keyword handling the standard win condition), `AfterYouLose`, `BeforeYouWin`, `AfterYouWin`. These fire once for the whole battle, not per-cube.
- **`APPLYTERRAINPERKS`** — a bare marker keyword, always placed right after the last `WORLDABILITY:` line and before `EndMapData`. Its exact mechanism isn't independently confirmed (undocumented in `ModdingInfo.txt`/`ModdingExplanation.txt`), but every real battle-type scenario has it exactly once in this position — include it in any new battle scenario rather than omitting it.
- **`EndMapData`** — closes the map-data body (parallel to `ADDITIONALMAP:`'s own `EndMapData` below).
- **`START_ACTION:`** — runs once when the scenario loads. For every real battle scenario, this is the terrain-dispatch `IfElse` described next.
- **`CUBE_SELECTION`** — a bare marker keyword appearing once, immediately before `SEnd`, in every real battle-type scenario. Exact semantics unconfirmed; include it in the same position for a new battle scenario rather than omitting it.
- **`HAND: faction slot amount CubeName`** — NOT present in the standard `Battle`/`Cursed_Battle`/`Boss_Battle`, but used by the bespoke Challenge scenarios to hardcode a fixed starting hand instead of a random one — see `references/challenge-and-branching-choices.md`.

`Cursed_Battle` and `Boss_Battle` are the same shape with different `WORLDABILITY: AfterYouWin`/`AfterYouLose` payouts (more gold/XP, a consumable reward, a `ReadAScenario Boss_Repeat` retry-on-loss branch) — copy whichever of the three is the closest real analog for a new battle-type scenario rather than building the wrapper from scratch.

## The terrain-generation dispatch — how a Terrain perk actually builds its own battlefield

This is the mechanism the `START_ACTION:` above triggers, and what makes a Terrain perk special versus an ordinary perk:

1. **Every battle-type scenario's `START_ACTION:` checks `PerkExists ARandomPerkInInventoryWhich PerkIsType Test Terrain` first.**
   - If the player has a Terrain perk: fire, in order, `TriggerWorldSomething Battle_Terrain_Generation`, then `Battle_Enemy_Generation` (or **`Battle_Boss_Generation`** specifically for `Boss_Battle`/`*_Boss_Terrain`-flavored scenarios), then `Battle_Player_Generation`.
   - Else: fall back to the hardcoded default — `ReadAPartialScenario Earth_Terrain` + `Battle_Normal_Enemy` (or `Earth_Boss_Terrain`) + `Battle_Normal_Player`.
2. **The four `TriggerWorldSomething` signal names are caught by `MapGenerationTPEB`** — a stock `COMPOUND: ABILITY`, defined once in `Extra_Mechanics/1Compounds.c.txt` and **not `LOCAL`-scoped**, so any mod package can reference it directly (`Extra_Mechanics` loads right after `Base_Core`, before `Characters`/`Main`/every mod package — see `GameData/Loading_Order.txt`):
   ```
   COMPOUND: ABILITY
   MapGenerationTPEB
   AfterWorldSomething Both Both Both
    If IsType Battle_Terrain_Generation GenericAction
    If IsType Battle_Player_Generation 
     If Not CubeExists ARandomCubeWhich And IsAlly Test IsALeader Test 
      GenericAction
    If IsType Battle_Enemy_Generation 
     If Not CubeExists ARandomCubeWhich And IsEnemy Test IsALeader Test
      GenericAction
    If IsType Battle_Boss_Generation 
     If Not CubeExists ARandomCubeWhich And IsEnemy Test IsALeader Test
      GenericAction
   NORANDOM
   End
   ```
   `GenericAction` is the `CODE`-style placeholder (see `cube-chaos-scripting`'s parameterized-compound section) that each Terrain perk's own `WorldAbility: MapGenerationTPEB <4 ReadAPartialScenario calls>` fills in with its own 4 partial-scenario reads, matched positionally to which signal fired. **The `If Not CubeExists ... IsALeader` guards on the Player/Enemy/Boss branches are what make this safe to coexist with the scenario's own fallback logic** — a Terrain perk's leader-placement partial only actually runs if no leader has already been placed by something else, so nothing double-places a leader.
3. **A Terrain `PERK:` itself is a thin wrapper naming its own 4 partial scenarios, in this fixed order** (ground / player / enemy / boss-ground):
   ```
   PERK: Mountains
   BelongsTo: Terrain
   WorldAbility: MapGenerationTPEB
    ReadAPartialScenario Mountain_Terrain
    ReadAPartialScenario Battle_High_Player
    ReadAPartialScenario Battle_High_Enemy
    ReadAPartialScenario Mountain_Boss_Terrain
   Description: High mountains connected via rope bridges End
   ReferenceCube: Limestone
   ReferenceCube: Rope_Bridge
   ReferenceCube: Mana_Crystal
   End
   ```
   No `Value:`/`BalanceCap:` — confirmed 0/15 real Terrain perks carry either (see `cube-chaos-scripting`'s perk-economy reference for the general category-gating rule). `ReferenceCube:` (an ordinary, already-documented repeatable `PERK:` field — `cube-chaos-scripting`'s `references/authoring-and-inheritance.md`) lists the terrain's constituent decorative cubes so the tooltip previews them; every real Terrain perk uses 2-3.

## The partial-scenario map-layout DSL (`ADDITIONALMAP:`)

```
SCENARIO: Earth_Terrain
Info: Normal terrain made of earth End
End

ADDITIONALMAP: // 52 28 //
CUBE: 1 Earth
CUBE: 2 Rock

DATARECT: 2 0  0 27  52 1

DATARECT: 1 0  5 26  42 1
DATARECT: 2 0  47 26  5 1
DATARECT: 2 0  0 26  5 1

PLACERECT: 0 0 26 28 1
PLACERECT: 26 0 26 28 2

EndMapData
SEnd
```

- **`ADDITIONALMAP: // w h //`** opens a partial map fragment. The `// w h //` is a human-readable comment only (not parsed) — every real file's comment matches its parent battle's own `MAP: w h` (`52 28`), so keep it in sync for readability even though the engine doesn't check it.
- **`CUBE: localIndex Name`** — declares a **local numeric alias** for a real cube name, scoped to this one `ADDITIONALMAP:` block only. Every following `DATA:`/`DATARECT:` line in the same block references cubes by this local index, never by name — **re-declare the mapping fresh in every scenario that needs it**; there's no cross-scenario sharing of the index table, and indices are reused with different meanings across different scenarios (e.g. index `1` is `Earth` in one scenario and `Limestone` in another).
- **`DATA: localIndex x y faction`** — places one cube of that local index at tile `(x, y)`. `faction` follows the standard 2-faction convention (`cube-chaos-scripting`): `0` = neutral/unowned terrain decoration, `1` = player, `2` = enemy.
- **`DATARECT: localIndex faction x y width height`** — fills a `width × height` rectangle (top-left at `x, y`) with that cube — how large terrain features (a rock floor, an ocean) get authored without one `DATA:` line per tile. Note the argument order differs from `DATA:` (faction comes right after the index, before the position).
- **`PLACERECT: x y width height faction`** — marks a rectangular zone as belonging to a faction for cube-placement purposes during the battle. Every terrain scenario ends with 2 (player half + enemy half) or 3 `PLACERECT:` lines — a third one at faction `3` marks a thin neutral middle strip for terrains with a raised second lane (`Mountains`, `Hovering_Vault`, `Loop_Monument` all do this; most terrains just split the map into two halves).
- **`CAMPAIGNSETUP: faction x`** — appears only inside the shared `Battle_<Height>_Player`/`Battle_<Height>_Enemy` partial scenarios (never the terrain-ground ones), pins the starting column `x` where that faction's leader gets placed for that height tier.
- **`EndMapData`/`SEnd`** close the block, same as the base battle wrapper.

## The 4-partial-scenario convention, and shared height tiers

Every real Terrain perk supplies exactly 4 `ReadAPartialScenario` calls, always in the order **ground layout → player leader placement → enemy leader placement → boss ground layout**. Only the ground-layout pair (`<Name>_Terrain`/`<Name>_Boss_Terrain`) is unique per terrain — **the player/enemy leader-placement scenarios are shared across every terrain at the same height tier**, not authored per-terrain. Confirmed across all 11 real terrains:

| Height tier | Shared `Player`/`Enemy` scenarios | Terrains using this tier |
|---|---|---|
| Normal | `Battle_Normal_Player`/`Battle_Normal_Enemy` | `Base_Terrain`, `Warehouse`, `Glacier`, `Basalt_Monoliths`, `Trash_Furnace`, `Jello_Plate` |
| High | `Battle_High_Player`/`Battle_High_Enemy` | `Mountains`, `Termite_Chasm`, `Bronze_Forest`, `Titanic_Battle` |
| Middle | `Battle_Middle_Player`/`Battle_Middle_Enemy` | `Ocean`, `Spiky_Cave`, `Salt_Bridges` |
| Low | `Battle_Low_Player`/`Battle_Low_Enemy` | `Acid_Dome` (the only low-tier terrain) |

**When adding a new Terrain perk, reuse an existing height tier's `Battle_*_Player`/`Battle_*_Enemy` pair rather than authoring a new one**, unless the new terrain's leader-start row genuinely doesn't fit any existing tier — this matches the real base game's own economy (11 terrains sharing just 4 tiers) and halves the amount of new map DSL a new terrain actually needs (only the 2 ground-layout scenarios are ever genuinely new).

**The Normal tier's floor sits at a fixed row: y=22 is the floor's top surface, y=0-21 is open air.** Confirmed by `Earth_Terrain`'s own `DATARECT:` rows (its Earth/Rock fill only ever touches y=22 through y=27 — 6 rows — never anything above y=22) and cross-checked against `Battle_Normal_Player`'s leader placement (`DATA: 1 0 21 2` — the leader stands at y=21, i.e. directly on top of the y=22 floor). **A "flat barren" terrain is NOT a full 52×28 solid fill** — that would leave no open airspace for units to be placed/move in at all, which no real terrain does. Fill only the tier's own floor band (y=22-27 for Normal) and leave y=0-21 empty, the same as every real terrain. The other 3 tiers shift this row to match their own leader y (High: leader at y=12, Middle: y=17, Low: y=25 — read the matching `Battle_<Tier>_Player`'s `DATA:` line for the exact row rather than assuming a fixed offset).

**Boss leader placement lives inside the terrain's own `<Name>_Boss_Terrain` partial, not in a separate `Battle_<Tier>_Boss` call — confirmed via `Boss_Battle`'s own `START_ACTION:` (`Extra_Mechanics/Battle_Scenarios.c.txt:110-118`).** Its Terrain-exists branch fires `Battle_Terrain_Generation`/`Battle_Boss_Generation`/`Battle_Player_Generation` (no separate boss-leader signal), and its own non-Terrain fallback list is `Earth_Terrain` + `Battle_Normal_Player` + `Earth_Boss_Terrain` — never `Battle_Normal_Boss`. Every real `<Name>_Boss_Terrain` file independently places its own `Boss` cube (e.g. `Earth_Boss_Terrain`: `DATA: 6 51 21 2`; `Basalt_Monoliths_Boss_Terrain`: `DATA: 4 51 21 2`; `Mountain_Boss_Terrain`: `DATA: 6 51 12 2`, matching that tier's own leader row), typically on a small `Stable_Plates` footing pad, no `Boss_Shield` — `Battle_Normal_Boss`/`Battle_High_Boss`/`Battle_Middle_Boss`/`Battle_Low_Boss` (which DO grant `Boss_Shield`) appear to be dead/unused by the terrain-generation path specifically; don't call them from a new Terrain perk's own boss partial, just place `Boss` directly the way every real terrain does.

**A handful of map-DSL cube names used in real boss-terrain decoration have no corresponding `CUBE:` text definition anywhere in `GameData`** — same category as `Boss`/`Leader`/`Difficulty_Leader`/`Empty` (engine-hardcoded, usable only as a map-placement name, not moddable/inspectable as DSL). Confirmed absent from every `.c.txt` in the repo (checked per-subfolder, not a single whole-tree grep — see the grep-silent-failure note in `cube-chaos-mod-setup`): `Spiker_Wall`, `Spikes`, `Solar_Panel` (all used only inside `Extra_Mechanics/Battle_Maps.c.txt`'s own boss-terrain decoration clusters). Don't go looking for their `CUBE:` block if you want to reuse or reference one — it doesn't exist; just use the name directly in a `DATA:`/`DATARECT:` line the same way the base game does.

**Gravity is real: an unsupported cube (nothing solid directly South of it) falls, one tile at a time, until it hits something solid** — confirmed via `Skewer_Trap`'s (`Main/3GeneralCubes.c.txt:5852`, a real obtainable `TYPE Wall` cube, not an `Extra_Mechanics` TOKEN) own trigger, `AfterACubeMoves ... If IsSameCube Caster CubeInDirectionFromCube South Victim`, which fires specifically when a falling cube comes to rest in the tile directly above it. **To build a pit/fall-trap in a terrain's floor, leave the tiles directly above the trap empty instead of filling them with the floor cube** — e.g. a trap meant to sit "2 tiles below the floor surface" needs the floor's normal top 2 rows left unfilled at that one column, with the trap cube occupying the row below that gap; a unit that steps onto that column has nothing to stand on and falls straight into it. **Also watch for a trap-style cube's own `AfterThisIsCreated`-time area effect hitting terrain fill, not just player units** — `Skewer_Trap` kills up to 2 *neutral* cubes directly below itself on creation; placing multiple neutral copies of it stacked in the same column (or one directly above plain neutral floor filler) causes it to silently gut its own neighbors/the floor beneath it at terrain-generation time. Space multiple instances of a self-triggering neutral decoration at least 3 tiles apart in the same column, or make sure what's below it isn't neutral, to avoid this.

## Practical sequence for a new Terrain perk

1. Design the ground layout as a grid of `DATARECT:`/`DATA:` fills — sketch it as a simple ASCII/ratio plan first (which cube fills which region) before writing tile coordinates, since getting the numbers right by eye against 11 real examples is the realistic workflow (there's no visual map editor exposed to modding).
2. Pick (or confirm) a height tier and reuse its existing `Battle_*_Player`/`Battle_*_Enemy` — don't write new ones unless genuinely necessary.
3. Write the `<Name>_Terrain` and `<Name>_Boss_Terrain` partial `SCENARIO:` blocks (boss version = ground layout + a `Boss`-faction-2 `DATA:`/`DATARECT:` placement, following a real boss-terrain example's shape).
4. Write the `PERK: <Name> / BelongsTo: Terrain / WorldAbility: MapGenerationTPEB <4 reads> / Description: / ReferenceCube:` block.
5. Sprite: Style 2 clean-3-ring border, brown `(105,48,0)` ring 1 — see `cube-chaos-sprite-art`.
6. Any new `TOKEN` cubes the terrain needs (decorative ground pieces) go through the normal `CUBE:` workflow — most terrain cubes are simple (`Burrowed` + `AiPlacementRule: And AiStacking AiDefense` + a `Crumble` death animation is the overwhelmingly common shape for a static ground tile — see `Extra_Mechanics/TokenCubes.c.txt`).
7. Test-launch and check `Log.txt` — a map-DSL mistake (bad tile coordinates, wrong local index) is exactly the kind of silent/off-by-one error the launch gate exists to catch; a botched `DATARECT:` won't always error, it can just render terrain in the wrong place.
