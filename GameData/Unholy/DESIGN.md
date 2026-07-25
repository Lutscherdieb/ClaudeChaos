# Unholy — mod design & balance notes

Mod-specific design/balance rationale that isn't general enough for the shared skills and isn't
private session state. Kept in the repo so it travels with the mod. Update this whenever an Unholy
design or balance decision is made (this is a governance requirement — see root `CLAUDE.md`).

> **Numbers in this file are illustrative, not authoritative — the `.c.txt` is.** Mana costs, hp,
> timers, and other stat/parameter numbers are deliberately not restated here where a pointer will do; a
> rebalance edits the `.c.txt` and has no reason to touch this doc, so a copied-in number silently goes
> stale (real incident: General's ammo-cube mana list drifted twice — see that mod's `DESIGN.md`). Read
> the *shape* of a design here; read the *current numbers* from the `.c.txt`.

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
by any class. Balance is anchored to real base-game analogs, not invented from scratch. **Exact current
mana/hp for every cube lives in `Unholy_Cubes.c.txt`** — deliberately not restated below, see the note
at the top of this file:

| Cube | 0HP? | Balance anchor / notes |
|---|---|---|
| `Ritual` | yes | Species starter; teleports + explodes, spawns Imps |
| `Cultist` | no | Species starter; cheap charging attacker + sacrifice |
| `Hellhound` | no | Fast rusher — priced off the `Small_Warrior_Slime` charge speed with a fast bite |
| `Plague_Imp` | no | The `Imp` token's kit made obtainable + green; poisons touching non-Imps on death (priced as Imp-body value + death poison) |
| `Martyr` | no | A holy-recolored `Cultist` (same stats) minus the sacrifice; on death buffs touching allies' hp |
| `Brimstone` | **yes** | 0HP one-shot; on death spawns a neutral `Molten_Brimstone` (burns itself + all touching, plus Acidic) at the column top (enemy column for Unholy) |
| `Plague_Ritual` | **yes** | 0HP legendary; on death creates an allied `Plague_Imp` on each empty touching position, each buffed +Strength per cube that was touching this at death |
| `Blood_Totem` | no | Stationary sacrificial engine piece — see its own section below |

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
  (`Plague_Imp` = Imp-body value + death poison — see `Unholy_Cubes.c.txt` for the resulting final
  cost). This is a design anchor the user set, not a base-game measured figure. (`Damned_Soul` no
  longer prices off this — see the `Phylactery` section below, it's a pure `SoulMemory` token now,
  not obtainable.)

### Starting cubes — deliberately 8, above the base-game 2 convention

The `Unholy` species perk grants **all 8 obtainable cubes** as starters (`Ritual`, `Cultist`, `Hellhound`,
`Plague_Imp`, `Martyr`, `Brimstone`, `Plague_Ritual`, `Blood_Totem`), via one
`ObtainAction: AddCubeToInventory` line each. This is a deliberate departure from the base-game convention of exactly 2 starters per
class/species — chosen so the full demon kit is guaranteed in hand (the new cubes were effectively
unfindable as rare drops in the global pool) and so the species reads as a complete themed toolbox.
There is no hard engine limit on starter count (`ObtainAction:` is repeatable); this just sits above
the base power/variety baseline. Revisit and trim to a curated few if it plays too strong. The six
new starters (all but `Ritual`/`Cultist`) also carry `TYPE Starter` (inventory-sorting only), matching
`Ritual`/`Cultist`.

### `Blood_Totem` implementation notes

A stationary "feed it allies, it pays back scaling hp regen" engine piece — not a 0HP cube, not a
combat body. Exact numbers live in `Unholy_Cubes.c.txt`; the design shape:

- **Kill-on-contact uses `BeforeThisCollides`, matching the base game's own `Void` cube exactly**
  (`Base_Core/3TokenCubes.c.txt`: `BeforeThisCollides TargetCube Victim Die`, "Before a cube collides
  with this kill it") — this repo's established real precedent for "a stationary cube instantly kills
  whatever walks into it," just narrowed to `IsAllyToCaster Victim` since this totem is meant to be a
  deliberate sacrifice tool for its own side, not a hazard to enemies.
- **Explicit `Not IsALeader Victim` guard, added during design review, not requested by the user.**
  A literal "kill any ally that touches this" would let a misplaced Leader finish the battle instantly
  (losing your leader = instant loss). The base game's own `DeadlyX` keyword independently excludes
  leaders from its own "kill" effect ("Kill the next STACKING 1 **non leader** cubes this damages",
  `ModdingInfo.txt:101`), which is the precedent this guard follows.
- **Kill counter uses `EnergyX`, not an opaque internal `EveryXTimes` counter — user's own suggested
  fix.** An earlier draft used `EveryXTimes 10` (fires every 10th matching trigger) to gate the Growth
  grant; the user pointed out this hides the count from the player, and proposed reusing the base
  game's own `EnergyX` `STACKING` ability as a *visible* counter instead (its own tooltip is just
  `Energy: N`, ModdingInfo.txt:117 — no side effects of its own, i.e. exactly a generic display
  counter). Implementation: `GainAbilityStacking EnergyX 0 1` on every kill, then
  `If Not IsSmaller GetStackingOfAbilityOnCube EnergyX Caster 10` triggers
  `ChangeAbilityStacking EnergyX -10` (reset) + `GainAbilityStacking GrowthX 0 1` (the payoff). Player
  can now watch the totem's Energy stack climb toward the next Growth tick on its own tooltip.
- **"Enemy territory" (the periodic damage tick) implemented as position-based, not
  faction-of-cube-based** — `EveryCubeWhich Not IsEqual PlacabilityOfPosition PositionOfCube Test FactionOfCube Caster TakeXDamage 1`,
  reusing the same `PlacabilityOfPosition` check this mod's own
  `Ritual` teleport already established for "the enemy's side of the board" (see the 0HP mechanic
  section above). This means a friendly cube that ends up pushed onto the enemy's side would also take
  the tick — a deliberate reading of "territory" as literal board geography, not "all enemy cubes",
  flagged to and accepted by the user at design time.
- **Self-damage is a genuine soft-kill clock, not just flavor.** At 5 max hp and 1 self-damage per 20s
  tick, the totem dies on its own in ~100 seconds unless the Growth payoff (healing over time) offsets
  it — i.e. the totem only sustains itself if the player actually feeds it ally kills. This mirrors the
  mod's existing self-damage subtheme (`Molten_Brimstone`'s self+touching tick, the Imp/`Acidic`
  friendly-fire choice) rather than being a new pattern.

## `Phylactery` — soul-echo perk

A droppable `BelongsTo: Unholy` reward perk (`Unholy_Species.c.txt`), not a species-wide passive.
Whenever an allied cube other than `Damned_Soul` itself dies, 10% chance to add a `Damned_Soul` to
hand — a 0hp/5-mana `TOKEN` whose only baked ability is `Flying`. On creation it's also granted
`SoulMemory`, a small helper compound (`AfterThisDies IfElse X%Chance 30 (...) (...)`) — when the
`Damned_Soul` later dies, 30% chance to create an allied `Plague_Imp`, otherwise an allied `Imp`.

- **Abandoned design 1: originally meant to recreate the *exact* ally that died** (via `GenericCube`,
  baking `Victim`'s type into the helper compound at grant time). **Runtime-confirmed broken** —
  `GenericCube` is not usable in a mod-authored `COMPOUND: ABILITY` at all, even just defining one
  throws `ERROR: character: (_) cannot be represented numericly...` at boot, independent of whether
  it's ever granted. See `cube-chaos-scripting/references/authoring-and-inheritance.md`'s `GenericCube`
  section for the full isolation-tested writeup — despite being a real listed production and despite
  the base game's own `Dragon_Egg`/`GrowingUp` using it, it's evidently hardcoded-engine-only, not a
  general modding mechanism. The Imp/Plague_Imp weighted-roll design (above) is the fallback the user
  chose over a curated per-cube-name branch, once the literal ask turned out to be unbuildable.
- **Abandoned design 2: the helper compound was first named `Soul_Memory`.** Also threw the identical
  `character: (_) cannot be represented numericly` error — turned out to be unrelated to `GenericCube`,
  isolated (via a `Foo_Bar`-named control) to **any underscore in a mod-authored `COMPOUND: ABILITY`'s
  own declared name**, not just this one. Renamed to the underscore-free `SoulMemory` and confirmed
  clean. See the same skill section for the full writeup — likely a long-standing latent issue in every
  other underscored compound name in this codebase too (`Dragon_Egg`, `Take_Off`), just never isolated
  since it doesn't break the ability's actual function.
- **Deliberately excludes `Damned_Soul` itself from re-triggering Phylactery** (`If Not CubeHasName
  Victim Damned_Soul`), so a dying `Damned_Soul` can't roll its own 10% chance to spawn a fresh
  `Damned_Soul`. Not a supercritical-cascade risk either way (each hop is one independent 10% roll, not
  a spawn-then-everyone-rolls shape like the old `Cultist` ripple bug — see `cube-chaos-scripting/
  references/death-fusion-reactive.md`), just avoids an odd "soul of a soul" chain. User-confirmed
  choice, made before the `GenericCube` failure was discovered but still applicable to the current
  design (a dying `Damned_Soul` would otherwise still roll its own 10% chance for a fresh one).
- **`Damned_Soul` still gets caught by the species' own 0hp rescue** (top of this file) since it's
  created at 0hp for an Unholy player — it teleports to the enemy backline, gains 1 hp, and
  `ExplodesX 0` (floor(5/10) = 0, negligible) before going on to do its actual job as a flying decoy
  that spawns an Imp/Plague_Imp once something kills it. Intentional/thematic, not a bug.
- `Damned_Soul` was previously an obtainable/starter attacker (`38 4 4`, melee, `AfterThisDies` created
  a fixed `Imp`) — fully repurposed into a `Phylactery`-only summon token; no longer in `PERK: Unholy`'s
  `ObtainAction:` starter list or the roster table above. The Imp/Plague_Imp echo on its own death
  loosely rhymes with that original behavior.
- **Upgrade: `Lichdom`** (`Unholy_UpgradePerks.c.txt`, `IsUpgradeFrom: Phylactery 80`) — drops the
  `IsAllyToCaster Victim` check entirely (triggers on *any* cube dying, not just allies) and doubles the
  chance to 20%. Priced at the "major scope/power jump" tier (`80`, not the standard `60`) specifically
  because of the scope drop, not just the doubled percentage — deaths happen on both sides of the board,
  so this is a bigger jump than "2x" sounds like. User-confirmed.

## Dragon evolution line — `Hell_Dragon`

Mimics the base-game per-class/species Dragon line (reference: Cryomancer's `Icy_Dragon_Egg` in
`GameData/Characters/Classes/Cryomancer.c.txt`, cubes in `Characters/2TokenCubes.c.txt`; base species
attach theirs the same way, e.g. `Chaos_Dragon_Egg BelongsTo: Chaos`). Shared egg→baby→adult shape
(see DJ's `DESIGN.md` for the full breakdown; same across all three mods):

- **Egg** `Hell_Dragon_Egg` → **Baby** `Baby_Hell_Dragon` (`GrowingUp`) → **Adult** `Hell_Dragon` — see
  `Unholy_Cubes.c.txt` for current stats/abilities.
- **Grant**: `PERK: Hell_Dragon_Egg BelongsTo: Unholy` (appended to `Unholy_Species.c.txt`);
  upgrade `PERK: Baby_Hell_Dragon IsUpgradeFrom: Hell_Dragon_Egg` in the **new**
  `Unholy_UpgradePerks.c.txt` (this mod had no upgrade-perks file before — added for this line; see
  that file for the current forge cost).

**Unholy signature — Hellfire Breath.** Applies the base-game `Burning` **keyword** (0-arg; "after 5s
deal 1 dmg to every touching cube and this", `ModdingInfo.txt:89`, an immutable base-game constant safe
to cite directly) to enemies — chosen over direct damage because it's literally "burning" and spreads
between adjacent burning enemies, fitting the chaotic-demon theme (cf. the Imp/`Acidic` "hits allies
too" choice above). Adult lights **all** enemies on a periodic tick
(`EveryCubeWhich IsEnemyToCaster Test GainAbility Burning`); baby lights a **single random** enemy on a
slower cadence (baby→adult escalation, mirroring the other two lines; current cadence numbers:
`Unholy_Cubes.c.txt`). Rule text references `Burning` colour-only (`\C255 106 0`) per the base-keyword
convention, no `\A`. Note: because `Burning` is a binary keyword (no stack level), re-application
frequency only controls how fast newly-created enemies get ignited — the burn rate itself is fixed by
the keyword (quoted above).

**Sprite (2026-07-25, revised after the Baby/Adult originally shipped as a palette-swap of the same
generic silhouette used by `Bass_Dragon`/`War_Dragon` — see `cube-chaos-sprite-art`'s dragon-line
corollary):** `Hell_Dragon` reads as a red lizard fire-dragon with a demonic touch — curved horns, bat
wings, a flame-tipped tail — deliberately in the Pokémon Charmeleon→Charizard body-plan family per the
user's own reference. Adult fills the tile near edge-to-edge; baby is smaller with horn nubs and a tiny
flame wisp instead of full horns/wings/tail. Wingspan and leg thickness went through one round of
"bigger wings, thicker legs" that the user then asked to revert — the shipped version keeps the original
(smaller-winged, thinner-legged) proportions; don't re-apply the bigger-wing/thicker-leg pass without
asking again first.

## Sprite notes

- **Species identity color: `RGB(150, 20, 20)`** (blood red) — the `Unholy` base-perk icon fill AND
  its species border. Chosen via `AskUserQuestion` before use (species/class colors are always
  confirmed with the user, never picked unprompted).
- `Plague_Imp` = green recolor of the `Imp` silhouette. `Martyr` = holy (white/gold) recolor of the
  `Cultist` silhouette. `Molten_Brimstone` = molten/glowing hazard token.
- `Blood_Totem` = an original silhouette, not a recolor — a stepped stone/idol totem shape (narrow
  spiked finial, glowing recessed "face" socket at the neck, wide stepped base flush to the tile's
  bottom row), deliberately distinct from the attacker cubes' sword/warrior silhouettes since it's a
  stationary non-combatant. Uses the demon family palette below (body/outline/highlight) plus the void
  and accent colors for the recessed face and its two glowing eyes.
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
- **`Phylactery` perk icon** (`Unholy_Species.c.png`, PERK slot 2 — row1/col0 of the 2×2 sheet, no
  resize needed): a lich's soul-jar — stone-gray urn (`(95,88,82)` base, `(20,18,16)` outline,
  `(150,140,128)` highlight) with a ghostly green soul-flame escaping its neck (`(110,235,140)` base,
  `(35,120,70)` shadow, `(225,255,230)` core). Deliberately breaks from the demon-red family palette
  above (thematically a lich/undead item, not a demon) while keeping the shared blood-red `(150,20,20)`
  perk border — see next bullet. `Lichdom` (its upgrade) needs no icon of its own, reuses this one
  automatically per `IsUpgradeFrom:` convention.
- **Ordinary Unholy reward perks (`Hell_Dragon_Egg`, `Phylactery`) extend the class/species border style
  to non-`BelongsTo:SPECIES` perks** — plain 2-ring border (magenta guide, gap, then a `(150,20,20)`
  ring at offset 2), same construction as `cube-chaos-sprite-art`'s "Optionally extending the class-color
  border" note, confirmed by re-measuring `Hell_Dragon_Egg`'s existing tile pixel-for-pixel before
  drawing `Phylactery`'s to match. This is a deliberate whole-mod style choice (ties every Unholy perk
  icon visually to the species), not an engine requirement — apply it to any future Unholy reward perk
  icon for consistency.

## Docs

Has a `README.md` + `Preview/` cards (added 2026-07-25) — keep them in sync on every content/sprite
change (`render_preview_cards.py`, run from the parent repo's root; it renders DJ, General, and Unholy
by default). The preview script resolves this perk file under its `_Species.c.txt` basename instead of
the usual `_Perks.c.txt` — see the script's `perks_source_basename()` if a species mod's perks ever stop
showing up in its own preview cards.
