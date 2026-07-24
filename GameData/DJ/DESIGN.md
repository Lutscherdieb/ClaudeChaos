# DJ — mod design & balance notes

Mod-specific design/balance rationale that isn't general enough for the shared skills and isn't
private session state. Committed so it travels with the mod. Update it whenever a DJ design/balance
decision is made (governance requirement — see root `CLAUDE.md`). This is a **basic seed**; expand it
as decisions are revisited.

## Core concept

A **Class** mod themed around a DJ / music. Signature material is the **`Note`** — a `0 0 0` `TOKEN`
cube generated and consumed by DJ cubes/perks — plus **`Echo`**-style ability duplication and
fusion/combination perks. Files: `DJ_Cubes`, `DJ_Perks`, `DJ_UpgradePerks` (dedicated sprite-less
upgrade file), `DJ_Synergies` (`CLASSSPECIES`), `DJ_Consumables`, `DJ_Curses`.

## Palette / sprites

- Class purple `RGB(170,0,255)`; `Note`/`Echo` gold accent; magenta `(255,0,220)` guide border.
- **All DJ perk icons extend the class-purple border** (a deliberate family-styling choice, not a
  base-game requirement — see the DJ-icon-border feedback memory).
- Fusion abilities (`Forced_Fusion`, `Symphony`) reuse the "two things merge into one" icon idiom.

## Deliberate design decisions

- **`Note` is `0 0 0` with a `NORANDOM` keyword tag** — this makes it a *passing-but-unpickable*
  ability donor at several ability-scan sites, so those guards name-exclude it. See the
  `GainRandomAbilityOfCube` zero-ability crash-guard notes in `cube-chaos-scripting`.
- **`Echo` was renamed from `Encore`** — it counts its own copies via its literal name
  (`AmountOfPerksInInventoryWhich IsSameString NameOfPerk Test StringConstant Echo`), so the literal
  name must stay in sync or the self-count silently reads 0.
- `Record`/`Microphone` do a plain multi-ability `GainAllAbilitiesOfCube` grant — this is the leading
  suspect in a reported freeze when combined with the base-game `Reciprocity` perk (unguarded
  ability-grant recursion). See the freeze-investigation memory; use `Silent` for any new
  ability-grant-reacting perk.

## Docs

Has a `README.md` + `Preview/` cards — keep them in sync on every content/sprite change
(`render_preview_cards.py`).
