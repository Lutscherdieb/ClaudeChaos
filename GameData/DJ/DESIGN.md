# DJ — mod design & balance notes

Mod-specific design/balance rationale that isn't general enough for the shared skills and isn't
private session state. Committed so it travels with the mod. Update it whenever a DJ design/balance
decision is made (governance requirement — see root `CLAUDE.md`). This is a **basic seed**; expand it
as decisions are revisited.

## Core concept

A **Class** mod themed around a DJ / music. Signature material is the **`Note`** — a `0 1 1` `TOKEN`
homing-projectile cube (`Flying`/`HomingX 120`/`ProjectileX 2`/`DieAfterX 7200`) generated and consumed
by DJ cubes/perks — plus **`Echo`**-style ability duplication and fusion/combination perks. Files:
`DJ_Cubes`, `DJ_Perks`, `DJ_UpgradePerks` (dedicated sprite-less upgrade file), `DJ_Synergies`
(`CLASSSPECIES`), `DJ_Consumables`, `DJ_Curses`.

## Palette / sprites

- Class purple `RGB(170,0,255)`; `Note`/`Echo` gold accent; magenta `(255,0,220)` guide border.
- **All DJ perk icons extend the class-purple border** (a deliberate family-styling choice, not a
  base-game requirement — see the DJ-icon-border feedback memory).
- Fusion abilities (`Forced_Fusion`, `Symphony`) reuse the "two things merge into one" icon idiom.

## Deliberate design decisions

- **`Note` is a `0 1 1` homing projectile, not a zero-ability `NORANDOM` donor tag** (that was an
  earlier design, since replaced — see `DJ_Cubes.c.txt`). It carries no `NORANDOM` tag, so it's a
  normal (if usually unwanted) ability-donor candidate at any random-ability-scan site; nothing in this
  mod currently relies on it being excluded. The `Bass_Dragon` line below leans on its current homing
  behavior: spawned Notes fly off and home enemies.
- **`Echo` was renamed from `Encore`** — it counts its own copies via its literal name
  (`AmountOfPerksInInventoryWhich IsSameString NameOfPerk Test StringConstant Echo`), so the literal
  name must stay in sync or the self-count silently reads 0.
- `Record`/`Microphone` do a plain multi-ability `GainAllAbilitiesOfCube` grant — this is the leading
  suspect in a reported freeze when combined with the base-game `Reciprocity` perk (unguarded
  ability-grant recursion). See the freeze-investigation memory; use `Silent` for any new
  ability-grant-reacting perk.

## Dragon evolution line — `Bass_Dragon`

Mimics the base-game per-class Dragon line (reference: Cryomancer's `Icy_Dragon_Egg` in
`GameData/Characters/Classes/Cryomancer.c.txt`, cubes in `Characters/2TokenCubes.c.txt`). The 3-stage
shape is shared by all three mods in this repo (General's `War_Dragon`, Unholy's `Hell_Dragon`):

- **Egg** `Bass_Dragon_Egg` (TOKEN 10/7/7, `ArmorX 1`): base compound `Dragon_Egg CubeConstant <baby>`
  — after 4 min on the field it dies and drops the baby into hand.
- **Baby** `Baby_Bass_Dragon` (TOKEN 5/15/15): `GrowingUp 40 CubeConstant <adult>` + `GrowthX 5` +
  `RegenerationX 2` + `WorthXMore 25`. Grows maxhp past 40 (~5 min) then becomes the adult
  (egg 4 min + baby ~5 min ≈ full dragon by ~9 min — deliberately a late-game payoff, matching base).
- **Adult** `Bass_Dragon` (TOKEN 200/30/30) + `Flying`/`GrowthX 2`/`EveryXMeleeY 120 4`.
- **Grant**: `PERK: Bass_Dragon_Egg BelongsTo: DJ` (reward perk, `DJ_Perks`) adds the egg at battle
  start; `PERK: Baby_Bass_Dragon IsUpgradeFrom: Bass_Dragon_Egg 60` (`DJ_UpgradePerks`, sprite-less)
  starts you with the baby, forge cost 60.

**DJ signature — Note artillery.** Baby spawns 1 Note/10s (North). Adult spawns a Note on each of the
4 touching positions every 6s (`North`/`South`/`Forwards`/`Backwards` — sideways two are faction-
relative so an AI-owned dragon still fires the right way) **and** teleports to the top of a random
enemy's column every 15s (`SetStorage ARandomEnemy` → `TeleportToPosition TopPositionAboveCube Storage`;
teleport is NOT default on base dragons, built explicitly). Because `Note` is a homing projectile
(see above), each spawned Note flies off to strike enemies — the adult is a 4-way music battery.

## Docs

Has a `README.md` + `Preview/` cards — keep them in sync on every content/sprite change
(`render_preview_cards.py`).
