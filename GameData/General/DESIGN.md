# General — mod design & balance notes

Mod-specific design/balance rationale that isn't general enough for the shared skills and isn't
private session state. Committed so it travels with the mod. Update it whenever a General design/balance
decision is made (governance requirement — see root `CLAUDE.md`). This is a **basic seed**; expand it
as decisions are revisited.

## Core concept

A **Class** mod themed around a military/army general. Signature material is the **ammo-cube tier
chain** `Shot → Shell → Bomb → Rocket`: each is both an independently obtainable self-flying missile
when hand-placed (mana 5 / 8 / 12 / 17) *and* a token spawned by various cubes (`Bunker`, `Artillery`,
`Rocket_Silo`, `Bombardier`, `Bomber`, etc.), with the `Arms_Race` upgrade chain substituting one tier
for the next. Files: `General_Cubes`, `General_Perks`, `General_UpgradePerks` (dedicated sprite-less
upgrade file), `General_Synergies` (`CLASSSPECIES`).

## Palette / sprites

- Olive class color; gold star-outline accent; Shell-style bicolor bullets.
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

## Docs

Has a `README.md` + `Preview/` cards — keep them in sync on every content/sprite change
(`render_preview_cards.py`).
