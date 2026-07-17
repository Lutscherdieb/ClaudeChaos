# Workflow: a perk-family `PERK:` (new or edited)

Covers reward perks, Curses, Blights, Boons, Nightmares, Terrain perks, Consumables, Golden perks, Neutral perks, and CubeUpgrade perks — they're all a `PERK:` block with a trigger chain and a `Description:`, differing mainly in `BelongsTo:`/category and border color. Don't split this into a separate workflow per category; the deltas are small and tabulated below.

## Gather before writing anything

- Which exact category (this determines `BelongsTo:`, trigger keyword, border color, AND whether `Value:` is even legal — see the table below). If the user hasn't said and it's not obvious from context, ask.
- What the effect actually does, in plain language, before touching the DSL.
- **`Value:` is category-gated, not a universal optional field — get this wrong in either direction and it's a real bug, not a style nit.** A plain reward perk (`BelongsTo: <ClassName>/<SpeciesName>`, or the `DJ` family itself) must have **no** `Value:` line at all (167:0 audit against every base-game class/species reward perk — see `cube-chaos-scripting`'s Perk economy section for why: `Value` isn't a power rating, it's a price tag for a different economy those perks don't participate in, and adding one makes the perk incorrectly sellable in shops). Every *other* category in the table below (Curse, Blight, Boon, Terrain, Consumable, Golden, Neutral, CubeUpgrade) is expected to carry one — pick from that category's real clustering (`cube-chaos-scripting` has the round-multiples-of-50 pattern for curses and the general pricing-ladder note for upgrades) rather than an arbitrary number, and rather than skipping it.

## Category deltas

| Category | `BelongsTo:` | Trigger keyword | Allegiance checks | Border style + color (`cube-chaos-sprite-art`) |
|---|---|---|---|---|
| Reward perk | `<ClassName>`/`<SpeciesName>`/none | `Ability:` | `IsAllyToCaster`/`IsEnemyToCaster` | None by default (optionally the class's own Style 1 color, as a deliberate family-branding choice — see "Optionally extending the class-color border") |
| Curse | *(none at all)* | `WorldAbility:` | `IsAlly`/`IsEnemy`, and bare `IsPlaced` (no CUBE arg) | Style 2, red `(255,0,0)` |
| Blight | `Blight` | `WorldAbility:` (check real examples) | `IsAlly`/`IsEnemy` | Style 3, red `(255,0,0)` |
| Boon | `Boon` | `Ability:`/`WorldAbility:` (check real examples) | Usually `IsAllyToCaster` | Style 3, lime-green `(182,255,0)` |
| Nightmare | `Nightmare` (verify against `Extra_Mechanics/Nightmares.c.txt`) | check real examples | check real examples | Style 3, red `(255,0,0)` |
| Terrain perk | `TerrainPerk` | check real examples | check real examples | Style 2, brown `(105,48,0)` |
| Consumable | none (lives in `Main/Consumables.c.txt`) | check real examples | check real examples | Style 2, orange `(255,106,0)` (real file has a tiny 8px cosmetic flourish, safe to skip) |
| Golden perk | none (lives in `Main/GoldenPerks.c.txt`) | check real examples | check real examples | Style 2, yellow `(255,255,0)` |
| Neutral perk | `Neutral` | `Ability:`/`WorldAbility:` | check real examples | Style 2, gray `(128,128,128)` |
| CubeUpgrade | none (lives in `Main/CubeUpgrades.c.txt`, uses `SpecialAction:` not `Ability:`) | `SpecialAction:` | check real examples | No confirmed pattern — don't force one, see `cube-chaos-sprite-art` |

"Check real examples" means exactly that — grep the matching base-game `.c.txt` for 2-3 real instances before writing the trigger/allegiance logic from scratch, per `cube-chaos-scripting`'s core discipline (this DSL has near-zero error recovery, so matching a proven pattern beats deriving from the grammar list alone).

**Consumables cannot be restricted to one class.** `BelongsTo:` is a strictly single-valued field — it's either a category (`Consumable`, `Blight`, ...) or a class/species name (`DJ`, `Priest`, `Fungus`, ...), never both, and there's no second `BelongsTo:` line, no `Consumable/ClassName` slash syntax, no `RequiresClass:`-style field, and no in-`ClickAction:`/`Ability:` predicate anywhere in the engine that checks the caster's class (confirmed by grepping every `BelongsTo:` line across the whole `GameData` tree and the full DSL function reference — zero hits). If a user asks for a class-specific consumable, this is a real engine limitation, not something to work around silently — surface it and offer the actual choice: a normal cross-class `BelongsTo: Consumable` (shop/chest economy, `Value:` price tag, orange border), or a `BelongsTo: <ClassName>` reward perk that mimics consumable feel via `ClickAction:` + `LoseThisPerk` (truly class-gated since it lives in that class's own reward pool, but can't carry a `Value:` per the reward-perk pricing rule above, and won't render with the Consumable orange border).

**`ClickAction:` is the trigger keyword for Consumables** (confirmed via `Main/Consumables.c.txt`), typically wrapped as `ClickAction: If BattleOngoing Both LoseThisPerk <effect>` (or `If Not BattleOngoing` for consumables that only work outside battle) — `LoseThisPerk` consumes the item on use. To target "your hand" vs "the enemy's hand" inside a consumable's effect, `EveryCubeInHandOfFactionWhich DoubleConstant 1 True <action>` is your own hand and `DoubleConstant 2` is the enemy's (confirmed via `Bottled_Architect` and `Signal_Jammer`).

**A fresh `IsUpgradeFrom:` upgrade perk goes in its own `<ModPrefix>_UpgradePerks.c.txt`, never appended into the same file as the perk it upgrades.** This matches the base game's own convention (upgrades always live in a separate, sprite-less file — see `cube-chaos-sprite-art`'s upgrade-perk section) and avoids ever having to reason about blank sprite-sheet slots for the regular perks file at all. If the perk being upgraded still lives in the mixed-file style from before this convention was adopted, that's a sign to split it out now rather than adding one more upgrade to the pile.

## Preview-and-approve gate (before the Sequence below)

Before writing any file, run the orchestrator's **Step C preview-and-approve gate**: print the theoretical spec (category + `Value:`/`BalanceCap:` + the real trigger chain + the `Description:` *derived from that chain*, sprite/border as concept only) and get the user's explicit OK. Iterate on the printed table — not on files — until they approve. Sprites and the Sequence below happen only after that OK.

## Sequence

1. **`cube-chaos-scripting`** — the `PERK:` block, trigger chain, and its paired `Description:`. If this is an `IsUpgradeFrom:` upgrade, write it directly into `<ModPrefix>_UpgradePerks.c.txt`, not the regular perks file.
2. **`cube-chaos-rule-text`** — review the `Description:` wording against the chain, including the "only add the stacking-clarification sentence when the re-trigger mechanism is genuinely non-obvious" rule (not for every stacking perk by default).
3. **`cube-chaos-sprite-art`** — skip entirely for an `IsUpgradeFrom:` upgrade (it has no sprite of its own and its file has no matching sheet at all). For a fresh non-upgrade perk: pick the border style + color from the table above (or the confirmed-precedent table in that skill directly, which is authoritative if this file and it ever disagree), generate it from scratch via the border-pattern-library recipes, then draw the interior art. Figure out the correct grid slot and whether the sheet needs resizing.
4. **Test-launch** — `cube-chaos-mod-setup`'s loop.

## If this is an edit, not a fresh perk

Read `workflows/editing-checklist.md` first.
