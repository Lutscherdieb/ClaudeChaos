# Unholy — mod design & balance notes

Mod-specific design/balance rationale that isn't general enough for the shared skills and isn't
private session state. Kept in the repo so it travels with the mod. Update this whenever an Unholy
design or balance decision is made (this is a governance requirement — see root `CLAUDE.md`).

## Core concept: the 0HP mechanic

The `Unholy` species (`Unholy_Species.c.txt`) intercepts any **allied cube created with 0 hp** —
which would normally die instantly — and instead rescues it into a **teleporting bomb**: +1 hp, an
instant `TeleportToPosition` to a random empty tile on the enemy's half, and
`ExplodesX floor(manacost / 10)` on death. So for an Unholy player a 0HP cube is delivered straight
into the enemy backline and explodes there, with blast damage scaling off its mana cost. **The
explosion hits all touching cubes, allies included — self-damage is a deliberate subtheme.** (Changed
from the original `ChargeEveryX` charge-forward delivery — teleport lands the payload behind enemy
lines instead of walking it there. The teleport uses `ARandomPositionWhich And IsPositionEmpty Test
Not IsEqual PlacabilityOfPosition Test FactionOfCube Victim` = a random empty position the enemy owns;
it's uncharted DSL, verify in playtest.)

### 0HP cubes are dual-use (usable by ANY class)

A 0HP cube is a legitimate **obtainable one-shot** for any class, not an Unholy-only card — the base
game already ships these (`Freezing_Pain`, `15 0 0`, `IDENT 2`, fires on creation then dies). Model:

- **Non-Unholy player:** the 0HP cube is created, its effect fires, and it dies immediately — a
  one-time consumable, exactly like a Cryomancer starter cube (freeze 3 enemies, then die).
- **Unholy player:** the species rescues it, so it *also* teleports to the enemy backline and explodes.

**Effect timing is the design lever.** An `AfterThisIsCreated` effect fires at the placement spot for
everyone. An `AfterThisDies` effect fires at placement for a non-Unholy player (instant death), but
for an **Unholy** player it fires wherever the cube dies — deep in enemy lines after teleporting there. So
**death-timed payloads are the ones that reward the Unholy synergy** by delivering into enemy
territory. `Brimstone` is built on exactly this.

> Open verify item: that `AfterThisDies`/`BeforeThisDies` reliably fire on the instant creation-death
> of a 0HP cube for a **non-Unholy** player. High confidence (the whole 0HP mechanic + `ExplodesX`
> depend on 0HP cubes dying and firing death hooks; `Ritual` already uses `AfterThisDies`), but it's
> the one load-bearing assumption — confirm in a playtest.

## Deliberate design choices

- **Imps damage their own allies.** The base `Imp` (and the new `Plague_Imp`) use `Acidic`, which hits
  "all touching cubes with different names" — i.e. it damages adjacent *allies* of a different name,
  not just enemies. This is intentional, not a bug: demons are chaotic and don't discriminate. New
  Unholy cubes may lean into this (e.g. `Plague_Imp` poisons **all** adjacent non-`Plague_Imp` cubes on
  death via `If Not HasNameOfCube Target Caster`, allies included).

## Cube roster & balance anchors

The signature 0HP cubes (`Ritual`, `Brimstone`) live alongside regular demon-themed bodies obtainable
by any class. Balance is anchored to real base-game analogs, not invented from scratch:

| Cube | Mana / HP | 0HP? | Balance anchor / notes |
|---|---|---|---|
| `Ritual` | 30 / 0 | yes | Species starter; teleports + explodes (boom 3), spawns Imps |
| `Cultist` | 5 / 3 | no | Species starter; cheap charging attacker + sacrifice |
| `Hellhound` | 20 / 3 | no | Fast rusher — `Small_Warrior_Slime` charge speed (30) with a 2/s bite |
| `Plague_Imp` | 32 / 4 | no | The `Imp` token's kit made obtainable + green; poisons touching non-Imps on death (Imp-body ≈25 + death poison) |
| `Damned_Soul` | 38 / 4 | no | `Medium_Warrior_Slime` body; Temporary (1 min) + Inspatial, leaves an allied Imp on death (≈25 Imp + ~13 own body) |
| `Martyr` | 5 / 3 | no | A holy-recolored `Cultist` (same stats) minus the sacrifice; on death buffs touching allies +1 hp |
| `Brimstone` | 40 / 0 | **yes** | 0HP one-shot; on death spawns a neutral `Molten_Brimstone` (25 hp, burns 1/sec to itself + all touching, plus Acidic 1/sec) at the column top (enemy column for Unholy) |
| `Plague_Ritual` | 90 / 0 | **yes** | 0HP legendary; on death creates an allied `Plague_Imp` on each empty touching position, each buffed +1 Strength per cube that was touching this at death |

### `Plague_Ritual` implementation notes

- **Spawns in `AfterThisDies`, on purpose.** The species grants every 0HP cube `ExplodesX` (`BeforeThisDies`), and Plague_Ritual's imps spawn on its *touching* tiles — exactly where that blast lands. Putting the imp-spawn in `AfterThisDies` (a strictly later death phase) means the explosion fires while the imps don't exist yet, so it hits the surrounding enemies/allies (self-damage theme intact) and the imps appear afterward, unharmed. This is the fix for "the explosion killed the imps." Four explicit N/S/E/W creates, each guarded by `And PositionExists IsPositionEmpty` (no single "each empty touching position" iterator exists).
- **No variable needed.** Each imp's Strength = `AmountOfCubesWhich And (IsPositionTouchingPosition PositionOfCube Test PositionOfCube Caster) (Not CubeHasName Test Plague_Imp)`, counted inline at each creation. Excluding `Plague_Imp` keeps the count stable as imps are created (they don't inflate it), so no `SetVariable` snapshot is needed, and it works with a dead `Caster` because it's position-based (`PositionOfCube Caster` persists after death). Applied via `GainAbilityStacking StrengthX 0 <count>` (computed → can't be inline `GainAbility`).
- **Consequences of the ordering (both intended):** the blast *clears* touching tiles first, so a strong blast → more empty spots → often more imps; and Strength counts post-blast survivors (touching non-imp cubes still standing), so a big blast that kills the neighbors yields more imps but each with less Strength.
- **Playtest checks:** (1) the teleport (species section) is uncharted DSL — verify it lands the cube on the enemy half and doesn't misbehave when no empty enemy tile exists; (2) whether `IsPositionTouchingPosition` counts only the 4 orthogonal neighbors (assumed, matching the game's "touching" convention).

- 0HP one-shots price like `Freezing_Pain` (deliberately cheap — for a non-Unholy player you pay for a
  single effect that then dies).
- Regular charging attackers price off the `Warrior_Slime` ladder: `Small 5/1/1` charge30,
  `Medium 13/4/4` charge60 melee2, `Large 25/5/5` charge90 melee5.
- **The `Imp` token is treated as ≈25 mana of value** when pricing anything that spawns or embodies it
  (`Plague_Imp` = Imp-body + death poison → 32; `Damned_Soul` = 25 Imp + its own body → 38). This is a
  design anchor the user set, not a base-game measured figure.

### Starting cubes — deliberately 8, above the base-game 2 convention

The `Unholy` species perk grants **all 8 cubes** as starters (`Ritual`, `Cultist`, `Hellhound`,
`Plague_Imp`, `Damned_Soul`, `Martyr`, `Brimstone`, `Plague_Ritual`), via one
`ObtainAction: AddCubeToInventory` line each. This is a deliberate departure from the base-game convention of exactly 2 starters per
class/species — chosen so the full demon kit is guaranteed in hand (the new cubes were effectively
unfindable as rare drops in the global pool) and so the species reads as a complete themed toolbox.
There is no hard engine limit on starter count (`ObtainAction:` is repeatable); this just sits above
the base power/variety baseline. Revisit and trim to a curated few if it plays too strong. The six
new starters (all but `Ritual`/`Cultist`) also carry `TYPE Starter` (inventory-sorting only), matching
`Ritual`/`Cultist`.

## Dragon evolution line — `Hell_Dragon`

Mimics the base-game per-class/species Dragon line (reference: Cryomancer's `Icy_Dragon_Egg` in
`GameData/Characters/Classes/Cryomancer.c.txt`, cubes in `Characters/2TokenCubes.c.txt`; base species
attach theirs the same way, e.g. `Chaos_Dragon_Egg BelongsTo: Chaos`). Shared egg→baby→adult shape
(see DJ's `DESIGN.md` for the full breakdown; same across all three mods):

- **Egg** `Hell_Dragon_Egg` (TOKEN 10/7/7) → **Baby** `Baby_Hell_Dragon` (TOKEN 5/15/15,
  `GrowingUp 40`) → **Adult** `Hell_Dragon` (TOKEN 200/30/30) + `Flying`/`GrowthX 2`/`EveryXMeleeY 120 4`.
- **Grant**: `PERK: Hell_Dragon_Egg BelongsTo: Unholy` (appended to `Unholy_Species.c.txt`);
  upgrade `PERK: Baby_Hell_Dragon IsUpgradeFrom: Hell_Dragon_Egg 60` in the **new**
  `Unholy_UpgradePerks.c.txt` (this mod had no upgrade-perks file before — added for this line).

**Unholy signature — Hellfire Breath.** Applies the base-game `Burning` **keyword** (0-arg; "after 5s
deal 1 dmg to every touching cube and this", `ModdingInfo.txt:89`) to enemies — chosen over direct
damage because it's literally "burning" and spreads between adjacent burning enemies, fitting the
chaotic-demon theme (cf. the Imp/`Acidic` "hits allies too" choice above). Adult lights **all** enemies
every 5s (`EveryCubeWhich IsEnemyToCaster Test GainAbility Burning`); baby lights a **single random**
enemy every 8s (baby→adult escalation, mirroring the other two lines). Rule text references `Burning`
colour-only (`\C255 106 0`) per the base-keyword convention, no `\A`. Note: because `Burning` is a
binary keyword (no stack level), re-application frequency only controls how fast newly-created enemies
get ignited — the 1 dmg/5s burn rate itself is fixed by the keyword.

## Sprite notes

- **Species identity color: `RGB(150, 20, 20)`** (blood red) — the `Unholy` base-perk icon fill AND
  its species border. Chosen via `AskUserQuestion` before use (species/class colors are always
  confirmed with the user, never picked unprompted).
- `Plague_Imp` = green recolor of the `Imp` silhouette. `Martyr` = holy (white/gold) recolor of the
  `Cultist` silhouette. `Molten_Brimstone` = molten/glowing hazard token.
- Multi-color shading (base + outline + highlight + accent), never flat single-color icons — cube icons
  are NOT flat red despite the species color, per explicit user requirement.
- **Demon family palette** (sampled from the existing `Imp`/`Cultist`/`Ritual` tiles, reuse for new
  red demons): body `(150,30,30)`, outline `(25–30,10–12,10–12)`, highlight `(197,72,62)`, shadowed
  recess (hood void) `(18,9,9)`, glowing-eyes accent `(255,205,70)`, on BG `(0,148,255)`.
- **`Ritual`'s pentagram** uses 2 layered line widths only: black outline `RGB(15,10,10)` (wider) + red
  `RGB(185,40,40)` (narrower), clean geometry (R=0.44, star=0.90R). A 3rd bright-core layer was tried
  and rejected by the user — it crowded the star at 17px and read worse than the clean 2-tone. Keep it
  black-outline + red only.
- `Unholy_Species.c.png`'s perk icon (demon head) is still flat single-red — offered to recolor it too
  but the user scoped the recolor to the cubes; revisit if asked.
- **Recolor maps used** (`scratchpad/build_sheet.py` regenerates the whole 3×3 sheet from the old
  tiles + these maps):
  - `Plague_Imp` (green): `(25,10,10)→(8,22,8)`, `(150,30,30)→(70,140,45)`,
    `(197,72,62)→(130,195,90)`, `(255,205,70)→(215,240,120)`.
  - `Martyr` (holy): `(150,30,30)→(228,228,238)`, `(30,12,12)→(120,95,40)`, `(18,9,9)→(90,70,30)`,
    `(197,72,62)→(255,255,255)`, gold `(255,205,70)` kept.
  - `Molten_Brimstone`: dark rock `(40,20,15)` + rock body `(100,50,35)` + orange glow `(255,110,0)`
    + gold core `(255,205,70)`.

## Docs

Has a `README.md` + `Preview/` cards (added 2026-07-25) — keep them in sync on every content/sprite
change (`render_preview_cards.py`, run from the parent repo's root; it renders DJ, General, and Unholy
by default). The preview script resolves this perk file under its `_Species.c.txt` basename instead of
the usual `_Perks.c.txt` — see the script's `perks_source_basename()` if a species mod's perks ever stop
showing up in its own preview cards.
