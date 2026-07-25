# DJ — mod design & balance notes

Mod-specific design/balance rationale that isn't general enough for the shared skills and isn't
private session state. Committed so it travels with the mod. Update it whenever a DJ design/balance
decision is made (governance requirement — see root `CLAUDE.md`). This is a **basic seed**; expand it
as decisions are revisited.

## Core concept

A **Class** mod themed around a DJ / music. Signature material is the **`Note`** — a `TOKEN`
homing-projectile cube (see `DJ_Cubes.c.txt` for its current stats/abilities) generated and consumed
by DJ cubes/perks — plus **`Echo`**-style ability duplication and fusion/combination perks. Files:
`DJ_Cubes`, `DJ_Perks`, `DJ_UpgradePerks` (dedicated sprite-less upgrade file), `DJ_Synergies`
(`CLASSSPECIES`), `DJ_Consumables`, `DJ_Curses`.

> **Numbers in this file are illustrative, not authoritative — the `.c.txt` is.** Mana costs, hp,
> timers, and other stat/parameter numbers are deliberately not restated here; a rebalance edits the
> `.c.txt` and has no reason to touch this doc, so a copied-in number silently goes stale (real incident:
> General's ammo-cube mana list drifted out of sync twice — see that mod's `DESIGN.md` history). Read
> the *shape* of a design here; read the *current numbers* from the `.c.txt`.

## Palette / sprites

- Class purple `RGB(170,0,255)`; `Note`/`Echo` gold accent; magenta `(255,0,220)` guide border.
- **All DJ perk icons extend the class-purple border** (a deliberate family-styling choice, not a
  base-game requirement — see the DJ-icon-border feedback memory).
- Fusion abilities (`Forced_Fusion`, `Symphony`) reuse the "two things merge into one" icon idiom.

## Deliberate design decisions

- **`Note` is a homing projectile, not a zero-ability `NORANDOM` donor tag** (that was an
  earlier design, since replaced — see `DJ_Cubes.c.txt` for current stats). It carries no `NORANDOM` tag, so it's a
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

- **Egg** `Bass_Dragon_Egg`: base compound `Dragon_Egg CubeConstant <baby>` — hatches after a fixed
  time on the field (the shared base-game `Dragon_Egg` compound's own built-in constant, ~4 min across
  all three mods' dragon lines) and drops the baby into hand.
- **Baby** `Baby_Bass_Dragon`: `GrowingUp <threshold> CubeConstant <adult>` plus growth/regen — grows
  into the adult once its maxhp climbs past the threshold, deliberately timed as a late-game payoff,
  matching the base game's own dragon lines. Current threshold/growth/regen numbers: `DJ_Cubes.c.txt`.
- **Adult** `Bass_Dragon` — see `DJ_Cubes.c.txt` for current stats/abilities.
- **Grant**: `PERK: Bass_Dragon_Egg BelongsTo: DJ` (reward perk, `DJ_Perks`) adds the egg at battle
  start; `PERK: Baby_Bass_Dragon IsUpgradeFrom: Bass_Dragon_Egg` (`DJ_UpgradePerks`, sprite-less)
  starts you with the baby — see that file for the current forge cost.

**DJ signature — Note artillery.** The baby periodically spawns a Note to its north; the adult spawns a
Note on each of the 4 touching positions on a faster cadence (`North`/`South`/`Forwards`/`Backwards` —
sideways two are faction-relative so an AI-owned dragon still fires the right way) **and** periodically
teleports to the top of a random enemy's column (`SetStorage ARandomEnemy` →
`TeleportToPosition TopPositionAboveCube Storage`; teleport is NOT default on base dragons, built
explicitly). Current cadence numbers: `DJ_Cubes.c.txt`. Because `Note` is a homing projectile (see
above), each spawned Note flies off to strike enemies — the adult is a multi-way music battery.

**Sprite (2026-07-25, revised after the Baby/Adult originally shipped as a palette-swap of the same
generic silhouette used by `War_Dragon`/`Hell_Dragon` — see `cube-chaos-sprite-art`'s dragon-line
corollary):** `Bass_Dragon` reads as a subwoofer/amp/e-guitar beast, not a generic winged lizard —
concentric-ring speaker-cone face, boxy amp-cabinet torso, a guitar-neck tail with fret ticks and a
headstock tip, and small sound-wave arcs floating off both sides of the head. Both the baby and adult
also carry a small ripple mark directly above the head, deliberately placed there because that's where
each one's own `Ability:` actually spawns its Note (baby: north; adult: also north, though it spawns on
all 4 sides — the icon only marks the one direction to keep it readable, not all 4). Adult fills the
tile near edge-to-edge; baby is deliberately smaller/rounder with no sound-wave arcs or guitar neck yet.

## Docs

Has a `README.md` + `Preview/` cards — keep them in sync on every content/sprite change
(`render_preview_cards.py`).
