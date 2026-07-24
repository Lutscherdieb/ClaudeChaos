# General — mod design & balance notes

Mod-specific design/balance rationale that isn't general enough for the shared skills and isn't
private session state. Committed so it travels with the mod. Update it whenever a General design/balance
decision is made (governance requirement — see root `CLAUDE.md`). This is a **basic seed**; expand it
as decisions are revisited.

## Core concept

A **Class** mod themed around a military/army general. Signature material is the **ammo-cube tier
chain** `Shot → Shell → Bomb → Rocket`: each is both an independently obtainable self-flying missile
when hand-placed (mana 5 / 8 / 12 / 25) *and* a token spawned by various cubes (`Bunker`, `Artillery`,
`Rocket_Silo`, `Bombardement`, `Bomber`, etc.), with the `Arms_Race` upgrade chain substituting one tier
for the next. Files: `General_Cubes`, `General_Perks`, `General_UpgradePerks` (dedicated sprite-less
upgrade file), `General_Synergies` (`CLASSSPECIES`).

## Palette / sprites

- **`(107, 142, 35)`** — General class color (olive drab). Used for the `General` class perk's own
  inner border + star icon fill, and reused as the inner border on `Arms_Race`/`Arms_Race_Mk2`/
  `Arms_Race_Mk3` (all `BelongsTo: General`), per the same convention as DJ's class-purple border
  extension (see `GameData/DJ/DESIGN.md`).
- **`(255, 210, 0)`** gold — reused from DJ's own Note/Echo gold (see `GameData/DJ/DESIGN.md`) as a
  cross-mod-consistent "gold accent" value. Used as a 1px outline around the `General` perk's star icon
  (added on top of the olive fill, at the user's request for a sharper/more distinct star) — a deliberate
  deviation from the base "icon fill == border color" convention (`cube-chaos-sprite-art`'s "Base
  class/species icon style" section), not a base-game rule.
- **Bullet/projectile bicolor look** (the 3 mini-bullets on the `Arms_Race` icon): dark cap/outline
  `(60, 62, 66)`, brass/gold casing `(185, 145, 45)`, dark red tapering tip `(150, 60, 40)` — sampled
  directly from the real `Shell` token cube's own icon in `General_Cubes.c.png` (nose-east: cap, then
  casing, then a triangular tip taper). Reusing the exact `Shell` cube colors ties the `Arms_Race` perk
  icon to the mechanic (it turns Bullets into Shells).
- Background is the standard game-wide `(0, 148, 255)`, guide ring is the universal `(255, 0, 220)`
  (see the `cube-chaos-sprite-art` skill).
- **A non-`CLASS` `BelongsTo: General` reward perk icon doesn't need to be fully olive** — only the
  border ring needs the class color; the interior can use a different (but existing, cataloged) palette
  like the bullet bicolor above, per explicit user guidance ("doesn't need to be fully of that color and
  can even not contain the color except for the border").
- **`Faction_Colours`** tint (a mod-defined `COMPOUND: ABILITY`) recolors placed cubes to the owner's
  faction — the underlying sprites are repainted flat grayscale so the tint reads clean (plain
  luminosity, no contrast boost — see `cube-chaos-scripting`'s `CubeColourShift` notes).
- Arcing-eligible ammo cubes need a nose-diagonal `_Arc` sprite variant + `SetSpriteToCube` at the
  grant site (see `cube-chaos-sprite-art`'s directional-cube section).

## Deliberate design decisions

- **Splash-damage projectiles: tune the combined direct-hit + splash total, not each in isolation** —
  the primary target eats both. See the projectile-balance memory.
- **The ammo cubes are created in many places** — before baking any new `Ability:` into `Shot`/`Shell`/
  `Bomb`/`Rocket`, grep every `CreateCubeOnPosition CubeConstant <that cube>` site; each either needs
  the now-redundant dynamic grant removed or the new baked ability stripped at that spawn site (e.g.
  `Bomber`'s dropped `Bomb` strips `Flying`/`ChargeEveryX` so it falls straight down). Full rationale in
  `cube-chaos-scripting`.
- **`General_Inherited_Strength`** (an `Inheritable` `StrengthX 1` compound) is granted by the
  `General-Remnant` synergy so a placed ally and its whole creation tree deal +1.
- Several perks (`Thirst_for_Blood`, `Experienced_Fighter`, `Wartime_Logistics`, `Believer` + upgrades)
  are reworked shapes absorbed from the removed Cubehammer40k mod.

## Dragon evolution line — `War_Dragon`

Mimics the base-game per-class Dragon line (reference: Cryomancer's `Icy_Dragon_Egg` in
`GameData/Characters/Classes/Cryomancer.c.txt`, cubes in `Characters/2TokenCubes.c.txt`). Shared
egg→baby→adult shape (see DJ's `DESIGN.md` for the full breakdown; same across all three mods):

- **Egg** `War_Dragon_Egg` (TOKEN 10/7/7) → **Baby** `Baby_War_Dragon` (TOKEN 5/15/15,
  `GrowingUp 40`) → **Adult** `War_Dragon` (TOKEN 200/**25**/25 — lowest-hp of the three dragons,
  a deliberate glass-cannon since its bombardment is the strongest).
- **Grant**: `PERK: War_Dragon_Egg BelongsTo: General` (`General_Perks`); upgrade
  `PERK: Baby_War_Dragon IsUpgradeFrom: War_Dragon_Egg 60` (`General_UpgradePerks`, sprite-less).

**General signature — supercharged Bomber.** Built on this mod's own `Bomber` "fly into enemy
territory → drop payload" loop, but: **100% drop (no chance roll)**, the payload is a self-flying
`Rocket` (baby drops `Shell`) instead of a falling Bomb (so it's NOT stripped of `Flying`/`ChargeEveryX`
— it flies on into the enemy line), and it repositions with `TeleportToPosition` to the top of a random
enemy column every 12s. Drop fires per column-advance while over an enemy (`AfterThisMoves` + enemy-
territory + `TheFirstCubeInDirectionFromPositionWhich South … IsEnemyToCaster` — the base Bomber's exact
condition, at 100%). **`RandomMovementX 120`** (baby 150) is layered on so it drifts organically instead
of flying a dead-straight mechanical line — a deliberate flavor choice the user asked for. Balanced by a
**deliberately weak melee** (`EveryXMeleeY 300 2` = 2 dmg/5s, weakest of the three dragons). Charge speed
`ChargeEveryX 45` (baby 60), slightly faster than a stock Bomber (60). Splash/combined-total balance
still applies to the dropped Rockets — see the projectile-balance note above.

> Open playtest items: the drop cadence (100% × per-move over enemies + fast charge) is intentionally
> strong per the user; watch for Rocket-flooding in practice and add a `Cooldown` gate if it's too much.

## Docs

Has a `README.md` + `Preview/` cards — keep them in sync on every content/sprite change
(`render_preview_cards.py`).
