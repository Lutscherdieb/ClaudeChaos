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

**This section describes the concept only — read `Unholy_Species.c.txt` for the actual trigger/guard
logic, don't treat this prose as a mirror of it.** The exact mechanism has already changed shape twice in
one day as bugs got caught; restating the DSL here would just be one more copy to keep in sync.

The `Unholy` species intercepts any allied cube created with 0 hp on the player's own side (which would
normally die instantly) and additionally creates a true, unmodified copy of it on a random empty position
on the enemy's side. The original cube is untouched and still dies normally wherever it was placed (see
"dual-use" below) — the species reaction is a bonus on top of that, not a replacement for it. So a 0HP
cube gives an Unholy player **both** effects: the normal local one-shot, **plus** a second copy that,
being genuinely 0 hp itself, resolves the exact same one-shot again — deep in enemy territory this time.

**History, in brief:** originally this teleported the *same* cube instance to the enemy's side instead of
copying it, so delivery and the local effect were mutually exclusive — changed to the copy-based version
by user request, a deliberate power increase. Two follow-up corrections, both user-caught in play: an
early copy-based draft gave the copy a small survival buff (so it wasn't a genuinely *true* copy anymore),
and also granted it a bonus explosion on top of its own death effect — both were removed, since a true
copy was the actual goal and the copy's own effect was judged strong enough without an added bonus.
Whatever currently stops the copy's own creation from recursively spawning a further copy of itself lives
entirely in the `.c.txt` — don't assume any specific mechanism without checking there first.

**`Hellstorm` is excluded from this reaction** since it now carries its own dedicated self-teleport (see
its own section below) — without the exclusion it would double-deliver itself. **`Ritual`/`Plague_Ritual`
remain on the shared mechanic** — neither has `Hellstorm`'s "must always land in enemy territory or the
cube is pointless" property, so for them the extra local trigger reads as a harmless-to-good bonus rather
than a double-proc risk.

**Known unresolved gap, flagged not fixed:** several base-game 0hp cubes (e.g. `Mindcontrol`, `Shovel`,
`Cauterize`) target "the cube below them" as their whole effect, and a copy delivered onto an empty
random enemy tile has no guarantee anything is there to hit — such a copy can whiff entirely. There's no
general fix possible (the DSL can't rewrite another cube's own targeting from outside it, and these are
base-game files this repo never edits anyway); the user explicitly chose to accept this rather than
special-case a hand-picked list of known offenders (2026-07-25).

### 0HP cubes are dual-use (usable by ANY class)

A 0HP cube is a legitimate **obtainable one-shot** for any class, not an Unholy-only card — the base
game already ships these (`Freezing_Pain`, fires on creation then dies). Model:

- **Non-Unholy player:** the 0HP cube is created, its effect fires, and it dies immediately — a
  one-time consumable, exactly like a Cryomancer starter cube (freeze 3 enemies, then die).
- **Unholy player:** the cube does the exact same thing (fires locally, dies) — **plus** the species
  delivers a true copy that resolves the same way again, in enemy territory.

**Effect timing is the design lever.** An on-creation effect fires at the placement spot for everyone,
and now fires *again* for the delivered copy (a fresh creation event) wherever it lands. A death-timed
effect fires at placement for everyone (including now the Unholy player's own original), and
*additionally* fires again wherever the delivered copy dies — deep in enemy lines, effectively
instantly. So **death-timed payloads still specifically reward the Unholy synergy** with a bonus repeat
in enemy territory, on top of (not instead of) the local trigger everyone gets. `Brimstone` was originally
built on the old exclusive-delivery version of this; see its own redesign section below.

> Open verify item: that a death-timed effect reliably fires on the instant creation-death of a 0HP cube
> for a **non-Unholy** player. High confidence (the whole 0HP mechanic depends on 0HP cubes dying and
> firing death hooks), but it's the one load-bearing assumption — confirm in a playtest.

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
| `Brimstone` | no (2026-07-25, was yes) | Flying self-igniter — periodically re-applies base `Burning` to itself, so it ticks self+touching damage every 5s until it dies, then still drops a neutral `Molten_Brimstone` at its column top. See "Brimstone redesign" below. |
| `Hellstorm` | **yes** | New 2026-07-25; 0HP — on creation, self-teleports to a random enemy-side position (own dedicated ability, excluded from the species' shared 0HP mechanic — see below); on death, drops a neutral `Molten_Brimstone` at the column top, then two more a few seconds apart (3 waves total). Effectively "what `Brimstone` used to do", now split into its own cube. See its own section below. |
| `Plague_Ritual` | **yes** | 0HP legendary; on death creates an allied `Plague_Imp` on each empty touching position, each buffed +Strength per cube that was touching this at death |
| `Blood_Totem` | no | Stationary sacrificial engine piece — see its own section below |

### `Brimstone` redesign — no longer 0HP (2026-07-25)

`Brimstone` was originally a 0HP one-shot bomb (see roster table history); the user split that role
off into the new `Hellstorm` (below) and repurposed `Brimstone` itself into a standing flying
self-igniter: it re-applies the base `Burning` keyword to itself every 5 seconds via `EveryXSeconds`,
and since `Burning` is itself "after 5s, deal 1 dmg to self+touching, then lose the ability"
(an immutable base-game constant), the reapplication cadence turns it into a steady self+touching
damage tick — hitting allies too, matching the mod's existing Imp/`Acidic` friendly-fire theme. It
still drops a neutral `Molten_Brimstone` on death, unchanged from before.

**Deliberate consequence, confirmed with the user at design time: `Brimstone` no longer benefits from
the species' 0HP-rescue mechanic** (top of this file) since it's no longer created at 0 hp. It's now a
plain stationary self-igniter wherever it's placed, not a teleport-delivered payload — `Hellstorm` is
the cube that now carries that delivery mechanic forward.

**Follow-up tuning pass, 2026-07-25 (same day):** hp raised, the self-`Burning` reapplication slowed
down, and `ChargeEveryX` added so it's no longer purely stationary — user request, no rationale beyond
feel; see `Unholy_Cubes.c.txt` for the current numbers. The charge rate was picked to match this file's
`Imp`/`Plague_Imp` anchor (its other real anchors in this mod are `Hellhound` faster and
`Cultist`/`Martyr` slower) — adjust if it plays differently than intended once `Flying`+`Charging`
together are seen in motion.

### `Hellstorm` implementation notes

Do-what-old-`Brimstone`-did-but-bigger: 0HP, and on death drops 3 waves of neutral `Molten_Brimstone` at
the column top (wave spacing tuned to 8s, 2026-07-25, was 5s — user request; see `Unholy_Cubes.c.txt`
for the current value).

**Redesign, 2026-07-25 (same day as the species mechanic rewrite above): reverted to a self-contained
teleport instead of relying on the species.** Once the species mechanic changed from "teleport the
original" to "spawn a surviving copy, leave the original in place," `Hellstorm` specifically didn't want
the new behavior — its whole point is that it's *irrelevant where it's placed* since it's always meant
to land on the enemy side, unlike `Ritual`/`Plague_Ritual` where a local bonus trigger is fine. So it
now carries its own on-creation ability reproducing the *old* teleport package directly (survive, relocate
to a random empty enemy-side position, gain a mana-scaled explosion-on-death) — see `Unholy_Cubes.c.txt`
for the actual chain — and the species explicitly excludes `Hellstorm` by name from its own reaction to
avoid double-delivering it. Consequence:
`FreePlacement` is no longer needed (removed) since placement genuinely doesn't matter anymore, and mana
cost dropped 100→50 to match (it's no longer also picking up the species' separate bonus-copy value that
other 0hp cubes get) — `IDENT` scaled down alongside it, see `Unholy_Cubes.c.txt` for current numbers.

- **Implemented as nested one-shot delayed grants, not a counter/stacking ability.** The user's original
  idea was an `Inheritable`-tagged ability that the first spawned `Molten_Brimstone` would pass to the
  next. Checked and ruled out: `Inheritable` in this engine only cascades an ability *through a damage
  hit* (victim inherits from attacker), it has no "the next thing I create inherits this" meaning, so it
  can't drive a creation-chain. The actual mechanism used instead: each spawned `Molten_Brimstone` is
  handed a one-shot `GainAbilityText EveryXSeconds 5 (Both RemoveThisAbility <spawn the next one>)` —
  the same idiom as the base game's own `HarrowingPast` compound ("after 20 seconds, remove this ability,
  then do X"). This needed no new `COMPOUND: ABILITY` and no counter variable at all, since the wave
  count (3) is small and fixed — just 2 levels of nesting.
- **Known caveat, accepted as-is:** the chain only continues if each spawned `Molten_Brimstone` survives
  the 5 seconds before its turn to pass the torch. `Molten_Brimstone` has 25 hp and only takes 1
  self-damage/sec (25s to self-kill), so this is comfortable margin against its own self-damage tick, but
  it can still be cut short by enemy fire — a dead `Molten_Brimstone` silently drops the remaining waves.
  Not treated as a bug, same tier as this mod's other "verify in playtest" items.
- Added as a starter (`ObtainAction:` in `Unholy_Species.c.txt`) alongside the other 8, per this repo's
  "test new obtainable cubes as starters during dev" convention — trim later if 9 starters plays too
  strong, matching the existing note below about the roster already being above the base-game norm.
- Icon: a bigger/more intense variant of `Brimstone`'s own meteor icon — same demon-family molten
  palette (rock body `(150,30,30)`, outline `(25,10,10)`, highlight `(197,72,62)`, gold molten core
  `(255,205,70)`, orange flame accent `(255,110,0)`), with 3 small flame tufts above the body instead of
  `Brimstone`'s 2, echoing the 3-wave ability. Drawn directly into the sheet's next free slot (already
  sized `4×4` for `Unholy_Cubes.c.png` — 15 real cubes now fit the existing grid, no resize needed).

### `Plague_Ritual` implementation notes

- **Spawns in `AfterThisDies`.** Historical note: this was originally chosen because the species used to grant every 0HP cube `ExplodesX` (`BeforeThisDies`) and Plague_Ritual's imps spawn on its own *touching* tiles — exactly where that blast would land, so `AfterThisDies` (a strictly later death phase) let the explosion clear the tiles first without also killing the freshly-spawned imps. **The species no longer grants `ExplodesX` to anything (dropped 2026-07-25), so this specific ordering concern no longer applies** — kept as `AfterThisDies` anyway since there's no reason to move it, just noting the original motivating scenario is gone. Four explicit N/S/E/W creates, each guarded by `And PositionExists IsPositionEmpty` (no single "each empty touching position" iterator exists).
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

The `Unholy` species perk grants **all 9 obtainable cubes** as starters (`Ritual`, `Cultist`, `Hellhound`,
`Plague_Imp`, `Martyr`, `Brimstone`, `Hellstorm`, `Plague_Ritual`, `Blood_Totem`), via one
`ObtainAction: AddCubeToInventory` line each. This is a deliberate departure from the base-game convention of exactly 2 starters per
class/species — chosen so the full demon kit is guaranteed in hand (the new cubes were effectively
unfindable as rare drops in the global pool) and so the species reads as a complete themed toolbox.
There is no hard engine limit on starter count (`ObtainAction:` is repeatable); this just sits above
the base power/variety baseline. Revisit and trim to a curated few if it plays too strong. The seven
new starters (all but `Ritual`/`Cultist`) also carry `TYPE Starter` (inventory-sorting only), matching
`Ritual`/`Cultist`.

### `Blood_Totem` implementation notes

A stationary "feed it allies, it pays back direct hp" engine piece — not a 0HP cube, not a
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
- **Kill payoff simplified from a visible `EnergyX`/`GrowthX` stacking counter to a direct,
  ungated `HealXDamage 1` per kill — user request, 2026-07-25.** The original draft counted kills via
  a visible `EnergyX` stacking ability and paid out `GrowthX` (permanent max-hp growth) every 10th
  kill; the user asked to drop the counting entirely and have each kill just heal the totem 1 hp on
  the spot, no cap. Net effect: the totem no longer grows permanently stronger over a game, it just
  sustains its own hp off ally sacrifices, as often as it gets fed.
- **The 1-minute rate limit lives on the periodic damage tick, not the kill-on-contact heal —
  user correction, 2026-07-25.** An earlier draft put a `Cooldown 3600` on the `BeforeThisCollides`
  kill+heal instead; the user clarified the cooldown belongs on the *other* ability (the one that
  already had a periodic 20s cadence), so `EveryXSeconds DoubleConstant 20` became
  `EveryXSeconds DoubleConstant 60` (that ability's own `DOUBLE` argument is literally seconds, not
  ticks — unlike `Cooldown`) and the kill-on-contact heal is ungated again.
- **"Enemy territory" (the periodic damage tick) implemented as position-based, not
  faction-of-cube-based** — `EveryCubeWhich Not IsEqual PlacabilityOfPosition PositionOfCube Test FactionOfCube Caster TakeXDamage 1`,
  reusing the same `PlacabilityOfPosition` check this mod's own
  `Ritual` teleport already established for "the enemy's side of the board" (see the 0HP mechanic
  section above). This means a friendly cube that ends up pushed onto the enemy's side would also take
  the tick — a deliberate reading of "territory" as literal board geography, not "all enemy cubes",
  flagged to and accepted by the user at design time.
- **Self-damage is a genuine soft-kill clock, not just flavor.** At 5 max hp and 1 self-damage per
  minute tick, the totem dies on its own in ~5 minutes unless it's fed ally kills (each kill heals 1
  hp, uncapped) — i.e. the totem only sustains itself if the player actually feeds it. This mirrors
  the mod's existing self-damage subtheme (`Molten_Brimstone`'s self+touching tick, the Imp/`Acidic`
  friendly-fire choice) rather than being a new pattern.
- **Mana cost halved 60 → 30 — user request, 2026-07-25**, alongside the above simplification
  (no rationale given beyond the ask; the totem's kit is strictly weaker without the Growth payoff, so
  the cheaper cost tracks that).

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
- **`Damned_Soul` still gets caught by the species' own 0hp mechanic** (top of this file) since it's
  created at 0hp on the player's own side when placed from hand — a true copy of it is delivered to a
  random enemy-side position, which (also being 0hp) immediately resolves its own `SoulMemory` there,
  turning into an Imp/Plague_Imp deep in enemy territory. The original, placed copy does the exact same
  thing locally. Intentional/thematic, not a bug.
- `Damned_Soul` was previously an obtainable/starter attacker (`38 4 4`, melee, `AfterThisDies` created
  a fixed `Imp`) — fully repurposed into a `Phylactery`-only summon token; no longer in `PERK: Unholy`'s
  `ObtainAction:` starter list or the roster table above. The Imp/Plague_Imp echo on its own death
  loosely rhymes with that original behavior.
- **Upgrade: `Lichdom`** (`Unholy_UpgradePerks.c.txt`, `IsUpgradeFrom: Phylactery 80`) — drops the
  `IsAllyToCaster Victim` check entirely (triggers on *any* cube dying, not just allies) and doubles the
  chance to 20%. Priced at the "major scope/power jump" tier (`80`, not the standard `60`) specifically
  because of the scope drop, not just the doubled percentage — deaths happen on both sides of the board,
  so this is a bigger jump than "2x" sounds like. User-confirmed.

## Class+Species synergies — `Unholy_Synergies.c.txt`

11 `PERK: <Class>-Unholy BelongsTo: CLASSSPECIES` perks, one per base-game class (Warrior,
Chronomancer, Cryomancer, Engineer, Priest, Programmer, Pyromaniac, Roboticist, Rogue, Wizard,
No_Class). **Scope deliberately excludes this repo's own `DJ`/`General` classes** — user chose the
11-base-class scope explicitly over 13 (the 2026-07-25 launch log confirms the engine notices and
warns `Missing: DJ-Unholy`/`Missing: General-Unholy`, which is expected and not a bug to fix). See
`Unholy_Synergies.c.txt` for the current `Ability:`/`Description:` of each — not restated here.

- **Warrior** grants the leader all of `Catapult`'s abilities at battle start (`GainAllAbilitiesOfCube`).
- **Chronomancer** reacts to a `Time_Warp` being created (same `CubeHasName Victim Time_Warp` idiom the
  base game's own `Chronomancer-Plant`/`-Elemental`/`-Devourer`/`-No_Species` already use) and
  accelerates a random non-leader ally.
- **Cryomancer/Priest/Rogue/No_Class** all key off the species' own signature moment — `AfterACubeIsCreated
  If IsAllyToCaster Victim If IsSmaller HpOfCube Victim DoubleConstant 1`, the exact same condition the
  `Unholy` species perk itself reacts to. **Open verify item, flagged before implementation and accepted
  by the user:** since the species' own reaction bumps that same cube's hp 0→1 in the same event
  dispatch, there's a theoretical listener-ordering race — if the species' listener runs before a
  synergy's, the synergy's hp-check could read hp=1 and silently never fire. Nothing in
  `ModdingInfo.txt`/`ModdingExplanation.txt` documents cross-PERK listener order for the same trigger
  (only same-cube death*-phase* order is documented — see `cube-chaos-scripting`'s death-sequencing
  notes). Shipped as-is (matching this mod's existing precedent of shipping the teleport itself as
  "uncharted DSL, verify in playtest" rather than blocking on an unconfirmed risk) — **user explicitly
  deferred verification to real playtest** rather than a design change. If a playtest ever shows one of
  these four NOT firing when a 0-hp ally is created, the fix is to move it off this shared trigger
  entirely (e.g. a marker ability granted by the species' own chain, reacted to via a differently-timed
  hook) rather than tweaking the condition, since any condition reading a field the species' own
  reaction also mutates has the identical hazard.
- **Cryomancer** additionally reuses the base game's own `Icy_Dragon` stacking-`FrozenX`-past-manacost
  kill pattern (`2TokenCubes.c.txt:685`) rather than inventing a new freeze-kill mechanic.
- **Engineer/Pyromaniac** both react to an allied `ExplodesX`-carrying cube dying (Engineer: anywhere;
  Pyromaniac: specifically in enemy territory, igniting touching enemies) — kept deliberately distinct
  from each other so they don't read as reskins.
- **Programmer** reacts to a non-leader enemy dying with a 10% chance to add a free copy to hand.
  **Bug fix, 2026-07-25: the original grant (`AddCubeToHandOfThis FreeCopy Victim`) was missing
  `SetFaction FactionOfThis`, so the copy silently kept the dead enemy's own faction instead of joining
  the player** — caught by the user in play ("basically useless"). Confirmed against real base-game
  precedent for this exact "copy a dying cube to hand" shape (`ZUpgradeClassPerks.c.txt`'s
  `Universal_Frozen_Statues`, `PerkFragments.c.txt`'s `Effect:_Add_Free_Copy`): both always pair
  `FreeCopy`/`CopyWithAction` with an explicit `SetFaction FactionOfThis` for exactly this reason — a
  bare `FreeCopy` never reassigns faction on its own. **General takeaway for any future "copy a cube
  (especially an enemy's) into your own hand/board" effect** — `SetFaction FactionOfThis` is not optional
  window-dressing, it's required for the copy to actually be usable by the player.
- **Roboticist** reacts to a `RobotPartX` ally dying in enemy territory by copying a random 0-hp hand
  cube onto its death position — reuses the exact hand-search-then-`CopyWithAction`-onto-board shape
  already runtime-confirmed on this mod's own `Cultist` (see the death-sequencing skill reference for
  the original derivation). **Deliberately does NOT consume the hand cube** (matches the `Cultist`
  precedent's own behavior of copying, not removing) — flag to the user if a consuming version was
  actually wanted instead.
- **Rogue** reacts to a non-`Incursion` 0-hp ally being created by placing an `Incursion` on
  `ARandomRightPosition`. That selector has no empty-tile guard, matching the base game's own
  established precedent for `ARandomLeftPosition`/`ARandomRightPosition` (`cube-chaos-rule-text`'s fixed
  term note: every real usage across the whole game is bare/unfiltered) — an occasional silent no-op on
  a crowded right side is expected, not a bug.
- **Wizard** reacts to a `Concentrate` being created (mirrors the base game's own `Concentrate`-reactive
  synergies) by adding a free `Imp` to hand.
- **No_Class** grants the rescued 0-hp cube `ExtraLife` — pairs well with the species' own
  teleport-then-explode: the cube detonates, then reforms at full hp wherever it died (i.e. in enemy
  territory).

### Sprite: shared demonic-horns identifier, but 11 genuinely distinct demon variants

All 11 tiles share small curved horns (the common visual identifier tying the whole batch together —
the same idea as DJ's synergy set sharing a headphones motif across its species tiles, done in reverse
here since Unholy is the fixed *species* side of the pair). **Beyond the horns, each tile is a
genuinely different demon variant per class** — different body/head silhouette (armored pauldrons +
helmet + sword for Warrior, a pointed hood + robe for Priest/Rogue, a boxy glitchy body for Programmer,
flame-shoulder plumes for Pyromaniac, ice-shard shoulders for Cryomancer, a bell-robe + floating orb for
Wizard, a mechanical gauntlet for Engineer, a chest gear for Roboticist, a chest hourglass for
Chronomancer, the plain undecorated baseline for No_Class) rather than one shared bust with a small
floating symbol beside it — **the first draft did exactly that (one identical silhouette + a
same-sized colored icon next to it) and the user rejected it on sight as "too sameish."** Per-class
theme colors are pulled from each class's own real sampled base-perk-tile color where one made sense
(`(255,0,0)`-family for Warrior, `(0,254,33)` for Priest's cross, `(197,204,112)` for Chronomancer's
hourglass matching `Time_Warp`'s own tint, `(186,226,255)` for Cryomancer matching `FrozenX`'s own
color, `(255,106,0)`-family for Pyromaniac matching `Burning`), not invented. This "ask for a shared
identifier before drawing a synergy batch, then build genuinely distinct silhouettes around it" step is
now a standing part of `cube-chaos-orchestrator`'s `content-class-species.md` workflow, not just a
one-off here.

Two build mistakes worth remembering if this sheet is ever redrawn or extended: (1) a shared element
(the demon bust) very nearly fills the 15×15 safe interior when centered, so it and any per-class
addition must be composed together and off-center from the start, not centered-then-squeezed — a first
pass centered the bust and a floating prop overflowed past column 20 into the frame's own border band;
(2) **small/thin decorative shapes (a sword blade, an ice-spike tip, a gear's spokes) must be painted
*after* the auto-outline pass, never unioned into it** — the auto-outliner recolors any pixel touching
background to flat outline color, and a small isolated shape is *all* boundary pixels, so a first pass
that ran the outliner over these shapes together with the main body silhouette swallowed every one of
them into a flat near-black blob with no visible theme color at all (confirmed by re-rendering at 8×
zoom — exactly the pitfall `cube-chaos-sprite-art`'s "practical build technique" note already documents
for the `Hell_Dragon`/`Bass_Dragon` wing/sound-wave case, hit again here despite that precedent).

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
