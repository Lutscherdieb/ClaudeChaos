# Workflow: a themed Dragon evolution line (per class/species)

A **Dragon evolution line** is a reusable compound content pattern that mimics the base game's own
per-class/species dragons: a 3-stage **Egg → Baby → Adult** creature whose adult's signature abilities
key off that class/species's core mechanic. Every base class and species ships one (Cryomancer's Icy,
Warrior's Anger, Engineer's Iron, Wizard's Magic, Priest's Holy, Dwarf's Stone, Undead's Undead, …).
This repo's own mods each got one built this way (see "This repo's implementations" below).

**This is a great thing to suggest** when a user asks "what should I add to my class/species?" — it's a
high-impact, well-understood, self-contained late-game payoff that reuses proven base-game machinery, and
it instantly makes a mod class feel parity-complete with the base roster.

It's assembled from the normal content types, so it still routes through the usual skills
(`cube-chaos-scripting` → `cube-chaos-rule-text` → `cube-chaos-sprite-art`, and `cube-chaos-balancing`
only lightly since the stats anchor to the base dragons). This file is the *recipe* that ties them into
one coherent unit and records the base-game facts so the next session doesn't re-derive them.

## The mechanic (base-game facts, verified)

Two stock `COMPOUND: ABILITY`s in `GameData/Characters/1Compounds.c.txt` drive the whole evolution.
**Both are non-`LOCAL`** (the file's first `LOCAL` is at line 86, well after them) and `Characters`
loads before any mod package in `Loading_Order.txt`, so **a mod cube can reference them freely**:

- **`Dragon_Egg CUBE`** (`1Compounds.c.txt:1-5`, `ModdingInfo.txt:112`): body
  `EveryXMinutes DoubleConstant 4 Both AddCubeToHandOfThis GenericCube Die` — "After 4 minutes kill this
  and add CODE 1 to your hand." The egg sits on the board for 4 min, then dies and drops the baby into hand.
- **`GrowingUp CONSTANT CUBE`** (`1Compounds.c.txt:7-11`, `ModdingInfo.txt:159`): body
  `EveryTick If IsLarger MaxHpOfCube Caster GenericConstant Both Exile CreateCubeOnPosition GenericCube
  PositionOfThis` — "When this has more than CODE 1 max hp, replace this with CODE 2." So the baby, once
  its **maxhp** climbs past the threshold, transforms into the adult in place. Pair it with `GrowthX`
  (raises maxhp over time) so it actually reaches the threshold.

## Anatomy — 3 cubes + 2 perks per line

Templates below use `<Theme>` (e.g. `Icy`, `Bass`, `War`, `Hell`) and `<Owner>` (the class/species
perk name, e.g. `Cryomancer`, `DJ`, `General`, `Unholy`). Base reference: Cryomancer's whole line
(`Characters/Classes/Cryomancer.c.txt:64-71`, `Characters/2TokenCubes.c.txt:667-694`,
`Characters/Classes/ZUpgradeClassPerks.c.txt:588-594`).

**1. Egg cube** — goes in `<ModPrefix>_Cubes.c.txt`:
```
CUBE: <Theme>_Dragon_Egg 10 7 7
TOKEN
Ability: Dragon_Egg CubeConstant Baby_<Theme>_Dragon
Ability: ArmorX 1
AiPlacementRule: And AiStacking AiBackline
End
```

**2. Baby cube** — same file:
```
CUBE: Baby_<Theme>_Dragon 5 15 15
TOKEN
Ability: GrowingUp 40 CubeConstant <Theme>_Dragon
Ability: <a weaker/single-target version of the adult's signature>   (Text: ... End)
Ability: GrowthX 5
Ability: RegenerationX 2
Ability: WorthXMore 25
AiPlacementRule: And AiStacking AiBackline
End
```

**3. Adult cube** — same file:
```
CUBE: <Theme>_Dragon 200 30 30
TOKEN
Ability: <2-3 signature abilities keyed off the class's core mechanic>   (each with Text: ... End)
Ability: Flying
Ability: GrowthX 2
Ability: EveryXMeleeY 120 4
AiPlacementRule: And AiStacking AiBackline
End
```

**4. Egg reward-perk** — goes in `<ModPrefix>_Perks.c.txt` (or the species file). Starts the player with
the egg. `BelongsTo:` the class/species so it enters that reward pool:
```
PERK: <Theme>_Dragon_Egg
BelongsTo: <Owner>
Ability: AtTheStartOfTheBattle Both AddCubeToHandOfThis FreeCopy CubeConstant <Theme>_Dragon_Egg RemoveThisAbility
Description: Start with a free <Theme>_Dragon_Egg in your hand End
ReferenceCube: <Theme>_Dragon_Egg
ReferenceCube: Baby_<Theme>_Dragon
ReferenceCube: <Theme>_Dragon
End
```

**5. Baby upgrade-perk** — goes in `<ModPrefix>_UpgradePerks.c.txt` (the dedicated **sprite-less** upgrade
file — create it if the mod lacks one). Lets the player pay 60 at the forge to start with the *baby*
instead, skipping the 4-min egg wait:
```
PERK: Baby_<Theme>_Dragon
Ability: AtTheStartOfTheBattle Both AddCubeToHandOfThis CopyOfCube CubeConstant Baby_<Theme>_Dragon RemoveThisAbility
Description: Start with a free Baby_<Theme>_Dragon in your hand End
IsUpgradeFrom: <Theme>_Dragon_Egg 60
ReferenceCube: Baby_<Theme>_Dragon
ReferenceCube: <Theme>_Dragon
End
```

Notes on these blocks (all base-verified):
- **`ReferenceCube: <Name>`** is a real `PERK:` field — lists related cubes in the perk's tooltip so
  the player can preview the whole evolution chain from the egg perk.
- Egg perk uses **`FreeCopy`**, baby upgrade uses **`CopyOfCube`** — mirror the base game exactly.
- The `AtTheStartOfTheBattle Both AddCubeToHandOfThis <copy> RemoveThisAbility` shape is the general
  "start each battle with a free X in hand" idiom (see `cube-chaos-scripting`).
- Put `Description:` immediately **after** the `Ability:` (single-ability perk rule, `cube-chaos-scripting`).

## The design principle: the adult keys off the class's core mechanic

This is what makes each dragon *this* class's dragon rather than a reskin. Base examples: the **Iron**
Dragon (Engineer) spawns Iron cubes + buffs all allies' hp; the **Icy** Dragon (Cryomancer) mass-freezes
and kills over-frozen enemies; the **Anger** Dragon (Warrior) buffs every ally's melee; the **Magic**
Dragon (Wizard) amps ally damage + spawns Shock_Waves. So pick the adult's 2-3 signatures from the mod's
signature material/keyword. Give the **baby a weaker/single-target version** of the same idea (escalation).

Useful primitives this pattern tends to reach for (all in `cube-chaos-scripting`): `RandomMovementX`
(organic wander), `Burning` (0-arg fire keyword), and the `SetStorage ARandomEnemy` →
`TeleportToPosition TopPositionAboveCube Storage` "teleport/spawn at the top of a random enemy's column"
idiom (teleport is **not** default on base dragons — build it explicitly if wanted).

## Sequence

1. **Preview-and-approve gate first** (orchestrator Step C) — present all 5 blocks per line as a spec
   table (real DSL + derived rule text + stats), get the theme names via `AskUserQuestion`, and confirm
   the adult signature. A batch of three lines is normal — present together, accept per-line feedback.
2. **`cube-chaos-scripting`** writes the 5 blocks; **`cube-chaos-rule-text`** derives each `Text:`/
   `Description:` (base keywords like `Burning`/`Flying`/`GrowthX` referenced colour-only, no `\A`).
3. **`cube-chaos-sprite-art`**: **~4 sprites per line** — egg/baby/adult **17×17 cube tiles** (no border,
   multi-color: body + dark outline + highlight + gold-eye accent) + the egg-perk **27×27** icon (Style-1
   class-color border). The **baby upgrade perk needs no sprite** (reuses the egg-perk icon). New cubes
   usually fit existing blank sheet slots; a perk sheet may need a grid resize (e.g. 1×1 → 2×2).
4. **`cube-chaos-mod-setup`** launch + `Log.txt` check: `without real Image`/`empty Image` warnings
   before sprites are drawn are expected; `CLASS/SPECIES + X HAS N REWARD PERKS` count advisories are
   harmless.
5. Record the line in the mod's `DESIGN.md`; regen README preview cards + `<img>` lists if the mod has a
   README.

## Stat / pacing anchors

- Egg `10/7/7` + `ArmorX 1`; Baby `5/15/15`; Adult `200/<25-30>/<...>` — the base 200-mana adult range.
- Pacing: egg 4 min (fixed by `Dragon_Egg`) + baby maxhp climb (`GrowthX 5`, threshold `GrowingUp 40`
  ≈ 5 min) ≈ **~9 min to full dragon** — a deliberate late-game payoff. Base babies vary wildly (Icy's
  25 maxhp already exceeds its threshold so it matures *instantly*; Anger's `GrowthX 2` to threshold 50
  takes ~20 min). Tune via the baby's starting maxhp / `GrowthX` / `GrowingUp` threshold.
- Adult power is balanced by role: a strong-bombardment adult should get **weak melee**
  (`EveryXMeleeY 300 2`) and/or lower hp (glass cannon), matching how base dragons trade off.

## This repo's implementations (copy from these)

Built 2026-07 for all three custom entities — **parse-clean, sprites in-game, full-maturation playtest
left to the user** (the ~9-min chain can't be watched in a boot check; the DSL mirrors proven base code):

- **DJ → `Bass_Dragon`** (`GameData/DJ/`): Note-artillery. Adult spawns a Note on each of the 4 touching
  positions /6s (`Forwards`/`Backwards` for the sideways two) + teleports to a random enemy column /15s.
  Leans on DJ's `Note` being a homing projectile. See `DJ/DESIGN.md`.
- **General → `War_Dragon`** (`GameData/General/`): supercharged Bomber — 100% `Rocket` drop per
  column-advance over an enemy, `RandomMovementX` drift, teleport /12s, deliberately weak melee, lowest
  hp. See `General/DESIGN.md`.
- **Unholy → `Hell_Dragon`** (`GameData/Unholy/`): Hellfire Breath — grants the `Burning` keyword to all
  enemies /5s (baby: a random enemy /8s). Added `Unholy_UpgradePerks.c.txt` (mod had no upgrade file).
  See `Unholy/DESIGN.md`.
