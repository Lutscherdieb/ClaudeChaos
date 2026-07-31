# Targeting, movement, and board geometry

Load this when writing anything about board positions, directions, territory, movement/patrol
behavior, gravity, or counting/searching cubes by position.

## Absolute board coordinates ARE real and heavily used — `MaxWorldX`/`MaxWorldY`/`PositionFromXAndY`/`XOfPosition`/`YOfPosition`

Don't conclude these are unused/theoretical from a single scoped grep coming up empty — **this repo's grep tool has a confirmed bug where a search scoped to the whole `GameData` directory can silently return zero results** (see `cube-chaos-mod-setup`'s debugging-checklist note; the install path containing a space, `Cube Chaos`, is the suspected cause) even when real usages exist. Re-run scoped to individual subfolders (`GameData/Main`, `GameData/Base_Core`, etc.) before concluding a function is unprecedented — this exact mistake was made and corrected while researching this section: an initial per-subfolder-but-still-empty-looking pass wrongly concluded these were "zero real-game precedent," when in fact `MaxWorldX`/`MaxWorldY`/`PositionFromXAndY` are used 40+ times across `Base_Core`, `Main`, `Characters`, and `Extra_Mechanics`.

`MaxWorldX`/`MaxWorldY` (bare 0-arg `DOUBLE`s, `ModdingInfo.txt:637-640`) return the current battle's board dimensions; `PositionFromXAndY DOUBLE DOUBLE` (`ModdingInfo.txt:712`) builds an absolute `POSITION` from raw coordinates; `XOfPosition`/`YOfPosition POSITION` read them back. A confirmed real idiom for **the board's center column**, from the base game's own `Map_Compression` neutral perk (`Main/NeutralPerks.c.txt:396-424`, "removes every 4th column/row starting from the center"): `Division (Addition DoubleConstant 1 MaxWorldX) DoubleConstant 2` for the horizontal center rounded *up*, or drop the `+1` (`Division MaxWorldX DoubleConstant 2`) for rounded *down* — both real, just pick per whichever tie-break direction the effect wants (confirmed via the Voidling mod's own battle-center cube replacement, which rounds X up and Y down on explicit user instruction, both variants parsing and behaving as expected). Wrap in `RoundedDown` for a position ultimately fed to `CubeOfPosition`/`CreateCubeOnPosition` (grid coordinates should be whole numbers) — real precedent both with (`NeutralPerks.c.txt:310`, `RoundedDown Division MaxWorldX DoubleConstant 2`) and without (`NeutralPerks.c.txt:400`, stored as a comparison-only variable) the wrap, depending on whether the value is used as a real position or just compared against.

## Replacing whatever cube currently occupies a position, guaranteeing the replacement happens even if the tile was empty

The base game's own "replace a cube with something else" idiom (`Characters/Species/Shadow.c.txt`'s `Shadow_Hive` perk: `TargetCube ARandomCubeWhich CubeHasName Test Solid_Shadow Both Exile CreateCubeOnPosition CubeConstant Solid_Shadow_Hive PositionOfCube Target`) assumes a matching cube already exists — the `TargetCube`/`ARandomCubeWhich` search only finds something to exile if one's already there. For "replace whatever is at position P, or just place fresh there if it's empty" (rather than skipping the whole effect when P happens to be unoccupied), snapshot the position first and make the exile conditional while the creation stays unconditional:
```
If CubeExists CubeOfPosition <P>
 TargetCube CubeOfPosition <P>
  Exile
CreateCubeOnPosition <CUBE> <P>
```
Real usage, the Voidling mod's `VoidCenterFormation` (`GameData/Voidling/Voidling_Species.c.txt`) — the battle-start replacement must always produce a `True_Void` at the board's exact center regardless of whether a cube happened to be standing there, so the `Exile` is gated behind an `If CubeExists` guard while `CreateCubeOnPosition` sits outside it, referencing the position via snapshotted `SetVariable`d coordinates rather than `PositionOfCube Target` (which would be unavailable when the `If` branch never ran). This differs from `Shadow_Hive`'s shape specifically because that perk is fine skipping its whole effect when no matching cube exists — a "there must always be a result" effect needs the position computed independently of whether the exile fired.

## `AfterACubeCollides` binding roles (undocumented in ModdingInfo.txt/ModdingExplanation.txt)

For the `AfterACubeCollides` trigger (fires when a cube's movement collides it into another cube): `Culprit` = the cube that performed/caused the move, `Victim` = the cube that actually got moved (equal to `Culprit` for a plain self-move, different when one cube pushes another), and `Storage` = auto-bound by the trigger itself to the cube that was collided *into* — readable immediately with no `SetStorage` call needed. Confirmed by the base game's own `Mycelium_Tunneling`/`Advanced_Mycelium_Tunneling` species perks, which read `CubeHasName Storage Mycelium` straight out of the trigger with no prior assignment. `Storage` here follows the same "immune to `Test`/`Target` rebinding" rule as any other `Storage` use (see `cube-chaos-scripting/SKILL.md`'s "Implicit target resolution" section), so it stays valid across nested `TargetCube` calls in the same ability body.

## Why a self-referential `AfterThis*`/`BeforeThis*` trigger's "other cube" is always `Victim`/`Culprit`, never `Target` — the full mechanism, traced end-to-end from bytecode

**Real bug, the General mod's `Medic` (2026-07-31, two wrong fixes before landing on the real one — both wrong attempts and the full trace are kept here since the reasoning generalizes far beyond this one ability):**

1. **Original code:** `Ability: AfterThisCollides If IsAllyToCaster Storage TargetCube Storage HealXDamage DoubleConstant 1`. Shipped, mostly worked, silently failed to heal the cube it moved into when the Medic was enemy-AI-controlled.
2. **First fix attempt (also wrong):** switched `Storage` → `Target`, reasoning that `Cube.class`'s collision handler sets `EventClone.Target = Into` for `this.AfterThisCollidesTriggerQ` (true, confirmed by decompile) while only `AfterACubeCollides`'s global trigger gets `Storage` set. This produced a **worse** regression: the Medic started healing *itself* on every collision, ally or not.
3. **Root cause of why attempt 2 also failed, traced through `TriggerQ`/`Trigger`/`Event`:** the `EventClone.Target = Into` assignment in `Cube.class` happens on the event **before** it's handed to `TriggerQ.Act(E, ...)`. The very first thing `TriggerQ.Act` does is call `E.EventConversion(NeedsCulprit)` (`Event.class`), which runs `this.TriggCaster = this.Caster; this.TriggTarget = this.Target; this.Caster = null; this.Target = null;` — i.e. it **snapshots** the incoming `Caster`/`Target` into separate `TriggCaster`/`TriggTarget` fields, then nulls the originals out. Then, for each individual trigger firing, the base `Trigger.DO(Event E)` (`dw/game/dd/Code/CodeCore/Trigger.class`, inherited unmodified by `TriggerAfterThisCollides` and in fact by every `Trigger*` subclass checked — none override `DO`) unconditionally runs `E.Caster = this.OwnerC; E.Target = this.OwnerC;` **before** invoking the actual ability body — i.e. it resets both `Caster` and `Target` to the ability-owning cube itself (Medic), discarding whatever `Target` held coming in. **So `Target` inside any `AfterThis*`/`BeforeThis*` ability body is always the cube itself, full stop — it is never usably "the other cube," regardless of what an upstream engine method appeared to set it to.**
4. **What actually survives:** `TriggCaster`/`TriggTarget` are untouched by `Trigger.DO` (it only ever writes `.Caster`/`.Target`), so whatever `EventConversion` snapshotted into them before the reset is exactly what a script can still read — via `Culprit` (`CUBECulprit.Value(E)` → `E.TriggCaster`) and `Victim` (`CUBEVictim.Value(E)` → `E.TriggTarget`), both confirmed by decompiling `dw/game/dd/Code/CUBE/CUBEVictim.class`/`CUBECulprit.class`. Since `Cube.class` set `EventClone.Target = Into` *before* `EventConversion` ran, `Into` ends up in `TriggTarget` — readable as `Victim`.
5. **Real fix:** `Ability: AfterThisCollides If IsAllyToCaster Victim TargetCube Victim HealXDamage DoubleConstant 1`. Confirmed clean on a fresh launch. This also finally explains, mechanically, why the empirical tally in `SKILL.md`'s "Implicit target resolution" section holds so consistently (`AfterThisDies`/`BeforeThisDies`/`AfterThisTakesDamage` → `Culprit`, 34/34; `AfterThisKills` → `Victim`, 6/6): it isn't a loose convention, it's forced by this exact `EventConversion`-then-reset mechanism, which every self-referential trigger goes through identically. **`Storage` is the one implicit keyword genuinely immune to this reset** (`Trigger.DO` never touches `.Storage`), which is why the manual `SetStorage X ... Storage` idiom used elsewhere in this repo is safe, and why `AfterACubeCollides`'s auto-bound `Storage` (previous section) also survives — that trigger's owner is conceptually the reacting perk/player, not the colliding cube, so there's no analogous self-reset fighting over the same field.
6. **Practical rule of thumb going forward:** on any self-referential `AfterThis*`/`BeforeThis*` trigger, **never trust `Target` for "the other cube"** — reach for `Victim` (or `Culprit`, depending on which role fits the trigger's own semantics) instead, and confirm against real precedent or a decompile before shipping, per the general principle already stated above. `AfterThisCollides` had exactly one real usage in the entire base game + all mods (this `Medic` cube) both before and after this fix, so there is still no second example to cross-check against — treat this write-up itself as that precedent for the next mod that needs it.

## "Enemy/allied territory" (which side can *place* a cube here) vs. faction of a cube standing there

The board has no dedicated `IsInEnemyTerritory`-style BOOLEAN. The real idiom, confirmed via the base game's own `Explosive_Decay`/`Nuclear_Explosive_Decay` perks (`Characters/Classes/Pyromaniac.c.txt`, `ZUpgradeClassPerks.c.txt`) and user-confirmed as the intended meaning ("territory = the place where I can place cubes vs. where the opponent can place"):
```
Not IsEqual PlacabilityOfPosition <POSITION> FactionOfCube <reference-cube>
```
`PlacabilityOfPosition POSITION` (a `DOUBLE`) returns which faction is allowed to *place* a cube at that position — i.e. whose home half of the board it is, independent of who currently occupies it. Compare that against the *reference* cube's own faction (usually `Caster`/`Victim`, whichever cube's perspective "enemy territory" is relative to): if they differ, the position belongs to the other side. Real precedent uses the *observer's* faction (`FactionOfCube Caster`) as the reference even when checking an enemy `Victim`, since `Caster` reliably represents "the player who owns this perk" regardless of which side `Victim` is on. For a `CUBE:`'s own self-check (not perk-level), use `FactionOfThis` in place of `FactionOfCube Caster`.

For "is there an enemy *anywhere* in this direction, not just adjacent" (as opposed to `CubeInDirectionFromCube`, which only reads the immediately-touching tile), use the skip-searching `TheFirstCubeInDirectionFromPositionWhich DIRECTION POSITION BOOLEAN` — it scans outward past non-matching cubes and returns the nearest one that satisfies the predicate (`Test` inside the `BOOLEAN`, same binding convention as other `...Which` searches), e.g. `TheFirstCubeInDirectionFromPositionWhich South PositionOfThis IsEnemyToCaster Test`. Guard the result with `CubeExists` before using it, same as any other cube search that can come up empty.

**The `FactionOfCube Caster` territory idiom above is confirmed reliable inside a `CUBE:`'s own trigger and a `PERK:`'s event-reactive `Ability:` — but do NOT assume it "just works" the same way inside a `WorldAbility:` block without a specific reason to.** See `references/gotchas-grepped.md`'s `WorldAbility:`-vs-`Ability:` entry for the full incident: a `WorldAbility: AtTheStartOfTheBattle` computing territory boundaries via `FactionOfCube Caster` parsed clean but silently did nothing in real play, while the identical token sequence under plain `Ability: AtTheStartOfTheBattle` worked immediately. For a class/species perk's own self-directed per-battle territory logic, reach for `Ability:`, not `WorldAbility:`.

## Scanning/acting on your WHOLE territory (not just checking one position), and finding "which way is forward" without a leader reference

The single-position check above answers "is this one tile mine?" — a different, harder problem is "find every column that's currently mine, and which end of that range is closest to the enemy," needed for any effect that bulk-converts or measures a whole side of the board rather than one tile. Real usage, the General mod's class-perk battle-start territory-halving effect (`GameData/General/General_Perks.c.txt`):

- **Finding the boundary in one pass**: loop `X` from `0` to `MaxWorldX` (a plain counted `SetVariable`+`Until`+`ChangeVariable` loop, the `AddDepthRow`/`Map_Compression` idiom — see those for the loop skeleton), and at each `X` check `IsEqual PlacabilityOfPosition (PositionFromXAndY X 0) (FactionOfCube Caster)`. Track a running count (`GFRONT_N`, unconditional `ChangeVariable +1` on match) plus both a `GFRONT_MAXX` (unconditionally overwritten on every match — trivially ends up as the *last*/highest matching `X`) and a `GFRONT_MINX` (only written the *first* time, guarded by `IsEqual GFRONT_MINX -1` since it starts at a `-1` sentinel) — one full scan gives you the count and both ends of your territory's range for free.
- **Which end is "forward" (toward the enemy), without needing a leader or any hardcoded side**: don't reach for `ARandomAlliedLeader` for this — **it has zero confirmed real usage anywhere in this repo or the base game, only a bare listing in `ModdingInfo.txt`'s `CUBE:` section**, and was tried first here specifically for this purpose (get a known-mine anchor position), then abandoned when it turned out not to be the actual bug but also never got positively confirmed to work either — treat it as unverified, not proven-safe. The robust, fully-verified alternative needs no leader at all: once the scan above has found `GFRONT_MAXX` (a column *already confirmed to be yours*), compare `XOfPosition (PositionInDirectionFromPosition Forwards (PositionFromXAndY GFRONT_MAXX 0))` against `GFRONT_MAXX` itself — if stepping `Forwards` from your own highest-`X` column increases `X` further, `Forwards` means "increasing `X`" for your faction and `GFRONT_MAXX` is your front edge; if it decreases, `Forwards` means "decreasing `X`" and `GFRONT_MINX` is actually the front edge instead. This reuses `Forwards`'s own confirmed per-faction-relative meaning (see the `East`/`West`-vs-`Forwards`/`Backwards` section above) rather than introducing a second, unverified way to detect "my side."
- **Stacking a repeated-halving effect safely needs no explicit floor guard, because `RoundedDown` division already provides one.** "Remove half your columns, rounded down, never fewer than 1 remaining" sounds like it needs a special case at the boundary, but doesn't: computing `remaining = remaining - RoundedDown(remaining / 2)` (i.e. `CeilingDiv`) already fixes at `remaining = 1` once reached (`RoundedDown(1/2) = 0`, so `1 - 0 = 1`, stable under further repeats) — applying this update `N` times in a row (`N` = accumulated stacks, read once via `GetCampaignVariable`, looped with a plain counted `Until`) is safe to just repeat blindly without ever checking "are we already at the minimum."

## `TopPositionAboveCube CUBE` means the top of the WHOLE MAP column, not "the first free tile above this cube's own stack"

Easy to misread from its name alone. Real confirmed behavior (Broker mod, 2026-07-26): `Construction_Site`'s "every 2 minutes create a Skyscraper directly above this" ability was first written as `CreateCubeOnPosition CubeConstant Skyscraper TopPositionAboveCube Caster` — this parses clean and matches the function's one other real precedent in this repo (DJ's `Keyboard`, spawning a Note "at the top of a random enemy's column" via `TopPositionAboveCube <enemy>`), but in actual play every spawned Skyscraper appeared at the *ceiling of the entire map* and fell via gravity down to wherever it landed, "raining from the sky" instead of stacking neatly on top of `Construction_Site`. `TopPositionAboveCube` is the right tool for "drop something onto an enemy's column from above" (its one real precedent), but the wrong tool for "place this on top of my own current stack" — those are different positions unless the column is already full to the map's top edge.

**The fix for "first empty position directly above this cube's own stack" — and it turns out there IS a real base-game precedent for exactly this, missed on the first pass:** `Bee_Caller` (`Main/3GeneralCubes.c.txt:5223`, "every 5 seconds 50% chance to create a 2 damage homing bee in the first empty space above") does the identical thing:
```
IfElse IsPositionEmpty PositionInDirectionFromPosition North PositionOfThis
 CreateCubeOnPosition CubeConstant Bee PositionInDirectionFromPosition North PositionOfThis
 CreateCubeOnPosition CubeConstant Bee PositionInDirectionFromPosition North PositionOfCube TheFirstCubeInDirectionFromPositionWhich
  North PositionOfThis IsPositionEmpty PositionInDirectionFromPosition North PositionOfCube Test
```
Same core idea as below (find the first cube going north whose own north neighbor is empty = the top of the unbroken stack), just phrased via `IsPositionEmpty`+`PositionOfCube` instead of `Not CubeExists`+`CubeInDirectionFromCube` (logically equivalent — both are an occupancy check on the tile north of the loop candidate) and an `IfElse` upfront to skip the search entirely when the immediate tile is already free, rather than guarding with `SetStorage`+`CubeExists` after. Either phrasing works; `Bee_Caller`'s `IfElse`-first shape is marginally more idiomatic since it doesn't need the `CubeExists` guard on the search result (the search is only reached once the immediate-tile branch has already ruled out "already empty," so it's guaranteed to find something). Broker's `Construction_Site` uses the `SetStorage`-guarded phrasing:
```
Ability: EveryXMinutes DoubleConstant 2 SetStorage
 TheFirstCubeInDirectionFromPositionWhich North PositionOfThis Not CubeExists CubeInDirectionFromCube North Test
  IfElse CubeExists Storage
   CreateCubeOnPosition CubeConstant Skyscraper PositionInDirectionFromPosition North PositionOfCube Storage
   CreateCubeOnPosition CubeConstant Skyscraper PositionInDirectionFromPosition North PositionOfThis
```
**RUNTIME-CONFIRMED WORKING** (user playtest, 2026-07-26: Skyscrapers now land directly on top of the `Construction_Site` stack instead of falling from the ceiling).

## Teleporting to a random position, optionally filtered to an empty enemy-side tile

`TeleportToPosition POSITION` moves the ambient cube (or `TargetCube X TeleportToPosition ...`) to a position — real base usage `TeleportToPosition ARandomPosition` (`Main/2TokenCubes.c.txt:867`). For **a random empty tile on the enemy's half**, filter `ARandomPositionWhich BOOLEAN` (whose candidate is bound to `Test`, POSITION-typed here) with the empty-check plus the enemy-territory idiom from the section above:
```
TeleportToPosition ARandomPositionWhich And IsPositionEmpty Test Not IsEqual PlacabilityOfPosition Test FactionOfCube Victim
```
(`IsPositionEmpty Test` filter shape: `Main/3GeneralCubes.c.txt:6289`, `Characters/Synergies.c.txt:273`.) Real usage: the Unholy species (`GameData/Unholy/Unholy_Species.c.txt`) rescues a 0-hp ally by teleporting it here on creation instead of granting `ChargeEveryX`. **Caveat: PARSE-confirmed only, runtime UNVERIFIED** — no prior repo precedent combines `ARandomPositionWhich` with both an empty AND a territory predicate (see `cube-chaos-rule-text`'s note that empty+side searches are uncharted). Playtest whether it reliably lands on the enemy half, and what happens if no matching position exists (the search may return nothing → teleport to a null position).

## Counting cubes touching a position (`AmountOfCubesWhich IsPositionTouchingPosition`)

There is no `AmountOfCubesTouchingPosition` built-in. Count neighbors with `AmountOfCubesWhich (IsPositionTouchingPosition (PositionOfCube Test) <center>)` — `IsPositionTouchingPosition POSITION POSITION` (`ModdingInfo.txt:487`) is true when two positions are orthogonally adjacent; `Test` is the candidate cube. Two things this enables, both used by the Unholy `Plague_Ritual` (`GameData/Unholy/Unholy_Cubes.c.txt`):
- **It works from a death trigger on the dead cube itself**, since it reads `PositionOfCube Caster` (persists after death — see `references/death-fusion-reactive.md`'s death-context section) rather than the live cube. So an `AfterThisDies` chain can still count "what was around where I died."
- **Exclude the type you're spawning to keep an inline count stable.** If a chain both counts touching cubes and creates cubes on the touching tiles, each created cube inflates a naively re-evaluated count. Add `Not CubeHasName Test <TypeYouCreate>` to the count's predicate so freshly-created cubes don't count themselves — then the count can be written *inline* at each creation site (`GainAbilityStacking StrengthX 0 (AmountOfCubesWhich And (IsPositionTouchingPosition ...) (Not CubeHasName Test Plague_Imp))`) with no `SetVariable` snapshot needed.

## Custom-radius explosions: `ExplodesX` is fixed at "touching," not a configurable radius

`ExplodesX CONSTANT` (built-in) always means "before this dies, deal `CONSTANT` damage to the 4 touching cubes" — the radius is NOT a parameter, despite the name inviting that assumption. For a genuinely bigger blast radius, don't reach for `ExplodesX`; write a custom `BeforeThisDies`/`AfterThisDies` ability using `EveryCubeInRadiusXAroundTarget DOUBLE Action` instead — real base-game precedent (`Main/2TokenCubes.c.txt`'s `Blast_Mortar_Projectile`, several `3GeneralCubes.c.txt` cubes):
```
Ability: BeforeThisDies Both EveryCubeInRadiusXAroundTarget DoubleConstant 2 TakeXDamage DoubleConstant 4
 Both CreateAoEParticlesColourRadiusPosition DoubleConstant 16738816 DoubleConstant 2 PositionOfThis
 PlaySound Small_Explosion
```
**No `TargetCube`/`SetCaster` wrapper is needed when this is the cube's own self-trigger** (`BeforeThisDies`/`AfterThisDies`) — `EveryCubeInRadiusXAroundTarget`'s implicit center defaults to the ambient receiver, which is already "this cube" in a self-trigger context. The `SetCaster Victim TargetCube Victim` dance seen on a few cubes (`Explosive_Imbuement`) is only needed for the *global* variant `BeforeACubeDies`/`AfterACubeDies` (reacting to *any* cube dying, not just this one) — don't copy that wrapper onto a plain self-trigger, it's solving a different problem.

## Hardcoding `East`/`West` instead of `Forwards`/`Backwards` is a real, easy-to-miss bug class — audit for it whenever a cube/perk creates or targets something sideways

`East`/`West` are absolute map directions; `Forwards`/`Backwards` resolve relative to whichever faction owns the acting cube/perk (see the `EventDirection`/`Backwards` discussion below for the movement-specific version of this same distinction). Any effect that creates, targets, or checks something to one side — "spawn a Shell to the east," "fire east," "create a Note east of this" — silently breaks when the AI/opponent owns that cube or perk, since their forward is actually west: the effect fires backward into their own lines instead of toward the enemy. `North`/`South` are fine to hardcode (up/down doesn't flip per faction), only the left/right axis needs `Forwards`/`Backwards`.

This is not a rare mistake — a real audit of both mods in this repo (grep `\bEast\b|\bWest\b` across every `.c.txt`, excluding cube-name identifiers like `Bomber_West`) turned up 4 real instances, caught only when a user actually placed the affected cube as the opponent and watched it fire the wrong way: General's `Bunker` and `Artillery` (both hardcoded `East` for where they spawn/fire), and DJ's `Speaker` cube and `DJ-Dwarf` synergy perk (both hardcoded `East` for where they spawn a Note). All four were simple find-and-replace fixes to `Forwards`, confirmed safe via real base-game precedent for `Forwards` used inside a `PERK:`'s own `Ability:` chain too, not just a `CUBE:`'s self-trigger (`Main/Perks.c.txt`'s `Lashing_Out`: `TargetCube CubeInDirectionFromCube Forwards Caster TakeXDamage DoubleConstant 1`, and `Protectors_Shield`: `CubeInDirectionFromCube Forwards Victim`) — `Forwards` resolves relative to `Caster` (the perk-owning player) regardless of which cube in the chain (`Victim`/`Test`/etc.) it's being measured from.

**Whenever writing a new cube/perk that creates or targets something to one side, default to `Forwards`/`Backwards` and only reach for a literal `East`/`West` if there's a genuine reason the effect must be map-absolute** (rare — no real example of this need was found anywhere in either mod). When reviewing/debugging an existing sideways effect that seems to misbehave only for one player, grep for `East`/`West` in that ability chain before looking anywhere else.

## Simple forward-patrol with no directional sprite: use the built-in `RoamingX`, don't reach for the Charge/Flee-swap pattern below

The base game's own `Crow` (`Main/3GeneralCubes.c.txt:4836-4850`) does "move forward, turn around when blocked" with a single line, `Ability: RoamingX 120` — no custom `Ability:` chain at all. `RoamingX TIME` (`ModdingInfo.txt:213`) is a self-contained built-in whose tooltip text is already the idiomatic short phrasing: `"Every CODE 1 move forwards, turn around if there's no space"`. Reach for this on any new flying/patrol cube that doesn't need a directional sprite flip — it's one ability, one tooltip line, zero custom code.

**`RoamingX` is an opaque built-in with no exposed hook for a sprite-facing flip**, so it's the wrong tool if the cube needs to visually mirror its sprite when it turns around (there's no ability-presence flag or trigger to key a `SetSpriteToCube` off, unlike the Charge/Flee pattern below where `HasAbilityWithName Caster ChargeEveryX` doubles as exactly that flag). For that case, use the Charge/Flee-swap pattern below instead. Real precedent both ways in the General mod: `Bomber`/`Drop_Helicopter`/`Baby_War_Dragon` all have real mirrored `_West` sprite variants and use the Charge/Flee-swap; a cube with a single non-directional animated sprite (like `Crow`'s `Animation: Fly CLOCK`) should just use `RoamingX`.

When writing the `Text:` for a custom reversal ability that (unlike `RoamingX`) also needs to mention a real behavior `RoamingX` doesn't have (e.g. the sprite flip), keep it just as short — borrow `RoamingX`'s own phrasing style rather than restating which named sub-ability is currently active. Real example, shortened 2026-07-31 from a longer draft: `Text: Turns around when blocked or at the map's edge End` (the built-in `ChargeEveryX`/`FleeEveryX` tooltip lines already say "move forwards"/"move backwards" on their own, so the custom line doesn't need to repeat that).

## Reverse-movement patrol: swapping `ChargeEveryX` for `FleeEveryX`

`FleeEveryX TIME` (built-in, `Base_Core/1Compounds.c.txt`) is the real "move backwards every X" ability — the mirror image of `ChargeEveryX`. For a cube that should patrol back and forth (advance until some condition, then retreat, then re-advance), swap the two abilities in and out rather than granting both at once (having both active simultaneously fires opposing per-tick moves and the cube visually jitters in place instead of travelling).

**`IfElse BOOLEAN Action Action` is a real, self-chaining 2-branch conditional** (confirmed real precedent: `Characters/2TokenCubes.c.txt`'s `Robot_Remote` — `IfElse HasAbilityWithName Target ChargeEveryX (swap-to-Flee Action) (If HasAbilityWithName Target FleeEveryX (swap-to-Charge Action))`) — reach for it instead of two separate `If`-only `Ability:` blocks when a single trigger needs to pick exactly one of two mutually-exclusive branches, since it collapses what would otherwise be two guarded, near-duplicate `Ability:`/`Text:` pairs into one:
```
Ability: <trigger> If <blocked/other reversal condition>
 IfElse HasAbilityWithName Caster ChargeEveryX
  Both RemoveAbilityWithName ChargeEveryX GainAbility FleeEveryX 60
  If HasAbilityWithName Caster FleeEveryX
   Both RemoveAbilityWithName FleeEveryX GainAbility ChargeEveryX 60
```
The `HasAbilityWithName Caster ChargeEveryX`/`FleeEveryX` checks make the two branches mutually exclusive by construction (the cube is never in both states at once), so there's no listener-ordering concern. Remember any *other* ability that permanently removes the movement ability (e.g. a later "stop moving and become inert" effect) needs to strip **both** `ChargeEveryX` and `FleeEveryX` by name, since the cube could be in either state at the time that ability fires.

**For the reversal trigger itself, "blocked from moving" (a real, idiomatic condition) is often a better fit than positional detection** (checking for a specific cube/territory at some board coordinate), and composes cleanly with the `IfElse` pattern above via a single trigger instead of two separate `AfterThisMoves` abilities each re-deriving "am I currently charging or fleeing." The real DSL idiom for "about to be blocked," confirmed via the base game's own `Climbing` ability (`Extra_Mechanics/1Compounds.c.txt`: `Text: Climbing: Before this is blocked from moving horizontally move upwards`):
```
BeforeThisMoves If CubeExists CubeInDirectionFromCube EventDirection Caster
 <effect>
```
`EventDirection` is the direction of the attempted move, bound within `BeforeThisMoves`/`AfterThisMoves`; `CubeInDirectionFromCube DIRECTION CUBE` reads whatever's immediately touching in that direction (only the adjacent tile — for "anywhere further out," see `TheFirstCubeInDirectionFromPositionWhich` above). `Caster` refers to the cube itself inside a `CUBE:`'s own self-trigger, same as `This`. This check fires **before** the move resolves, whether or not the destination is actually occupied.

**By itself, this check misses being blocked by the edge of the map** — no cube exists off-board either, same as an empty movable tile, so `CubeInDirectionFromCube` alone can't distinguish "empty tile, will move fine" from "off the board, can't move at all." Caught the hard way: a first version of `Bomber`'s reversal used only this check and reversed correctly when blocked by another cube while charging forward, but never reversed back from fleeing, since fleeing heads toward the player's own board edge where nothing was there to trigger it — the cube just silently got stuck trying to flee forever. The fix is `PositionExists POSITION` (confirmed real, used by the base game's own `Star_Gift`/`Sky_Vine` cubes for exactly "is this the edge of the map" checks, e.g. `Main/2TokenCubes.c.txt`'s `Star_Gift`: `If Not PositionExists PositionInDirectionFromPosition North PositionOfThis Both Die ...`) — `Or` it alongside the `CubeInDirectionFromCube` check to catch both kinds of blocking.

**Confirmed via real in-game testing (both edges of the map): `EventDirection` does not reliably report `Backwards` for a `FleeEveryX`-driven move.** Wiring the combined check above through a shared `EventDirection` (one `Ability:` reacting to whichever direction the trigger reports) fixed the charging-direction/forward-edge case, but the fleeing-direction/backward-edge case silently never fired — confirmed fixed by switching to the literal `Backwards` constant instead of `EventDirection` (see below), with no other change, and user-confirmed working on both sides of the map afterward. Treat this as a real, load-bearing gap for any cube reacting to `BeforeThisMoves`/`EventDirection` on a cube that also holds `FleeEveryX` — don't rely on `EventDirection` alone once `FleeEveryX` is in play, even though it demonstrably works fine for the `Forwards`/`ChargeEveryX` case.

**The robust fix: derive the direction to check from which movement ability the cube currently holds, not from `EventDirection` at all.** Since `Forwards`/`Backwards` are themselves valid `DIRECTION` literals (same production list as `North`/`South`/`East`/`West`, confirmed via `Climbing`'s own `IsSameDirection EventDirection Forwards` check), every place `EventDirection` was used above can instead be replaced with the literal `Forwards` or `Backwards`, picked via whichever of `ChargeEveryX`/`FleeEveryX` is currently held — sidestepping `EventDirection` entirely:
```
Ability: BeforeThisMoves IfElse HasAbilityWithName Caster ChargeEveryX
 If Or CubeExists CubeInDirectionFromCube Forwards Caster
  Not PositionExists PositionInDirectionFromPosition Forwards PositionOfThis
  <effect when charging is about to be blocked>
 If HasAbilityWithName Caster FleeEveryX
  If Or CubeExists CubeInDirectionFromCube Backwards Caster
   Not PositionExists PositionInDirectionFromPosition Backwards PositionOfThis
   <effect when fleeing is about to be blocked>
```
Combining both patterns, a full "patrol until blocked, then reverse" cube needs only ONE reversal `Ability:` instead of two (real before/after comparison: General mod's `Bomber` cube originally used the two-`AfterThisMoves`-blocks shape above keyed on enemy-leader detection, then the `EventDirection`-based single-trigger shape, then this ability-state-keyed shape once the `EventDirection`/`Backwards` gap surfaced in actual play — see `GameData/General/General_Cubes.c.txt`).

## Gravity is a real, literal per-tick falling mechanic — not just flavor text, and there's no separate stacking/z-axis

There is **no cube-stacking/altitude/z-axis system at all** — "above"/"below" a cube always just means the North/South grid neighbor tile (confirmed via `NoCubeAbove`, `AboveExists`, `TopPositionAboveCube`, and dozens of real cubes like `Slime_Transport_Belt`/`Healing_Pillar` that read "the cube sitting on me" as `CubeInDirectionFromCube North Caster`). Don't reach for a stacking mechanic that doesn't exist when a mod concept sounds like it needs "layers."

`PERK: Gravity` (`Base_Core/GameRulePerks.c.txt`) is a real per-tick effect — a `WorldCube` moves every cube one tile in `GravityDirection` (South by default) ~15×/second unless negated — but it's technically opt-in per scenario (`SCENARIO:` blocks each list `PERK: Gravity` explicitly), not a hardcoded engine rule. In practice it's granted by every normal-play scenario checked (`Tutorial`, `Campaign`, `Random_Daily_Campaign`, `Mirror_Breaker`, the `Extra_Mechanics` node-map campaign) so treat it as baseline-on for any mod targeting normal play.

**The negation idiom**, used by every real gravity-immunity ability (`Flying`, `Hovering`/`Advanced_Hovering`, `Buoyant`): hook `BeforeThisMovesNegation` (self) or `BeforeACubeMovesNegation` (reacting to a *different* cube's fall) and check `If IsSameCube Culprit WorldCube` before negating — this specifically targets gravity-caused moves without blocking the cube's own `ChargeEveryX`/`FleeEveryX`-driven moves, since those have a different `Culprit`. Conditional/partial negation (rather than a flat permanent immunity like `Flying`) is a normal, precedented shape — `Hovering` only negates `If CubeExists CubeOfPosition PositionInDirectionFromPosition South PositionInDirectionFromPosition South PositionOfCube Caster` (i.e. only while something is 2 tiles below it):
```
COMPOUND: ABILITY
Hovering
BeforeThisMovesNegation If IsSameCube Culprit WorldCube If CubeExists CubeOfPosition PositionInDirectionFromPosition South PositionInDirectionFromPosition South PositionOfCube Caster
 NegateX DoubleConstant 1
Text: \C109 209 228 Hovering: \CN Doesn't fall if 2 spaces above another cube End
End
```
For reacting to a *different, dynamically-whichever* cube currently below (not a fixed reference), query the position fresh rather than tracking an identity — this also means the effect naturally stops mattering with no explicit "detach" logic once nothing is there to act on:
```
Ability: BeforeACubeMovesNegation If IsSameCube Victim CubeOfPosition PositionInDirectionFromPosition South PositionOfThis
 If IsSameCube Culprit WorldCube If X%Chance DoubleConstant 50 NegateX DoubleConstant 1
Text: Before the cube directly below this falls due to gravity, 50% chance to block that fall End
```
(Real usage: General mod's `Parachute` cube, `GameData/General/General_Cubes.c.txt` — a 50% chance to block the gravity-pull of whatever's currently south of it, giving that cube's own horizontal `ChargeEveryX` more ticks to fire before it lands, with no timer needed since a landed cube simply stops attempting to move south.)

**`FreePlacement` only bypasses the placement-support check, not gravity itself** (`Base_Core/1Compounds.c.txt`: `BeforeThisIsPlaced NegateX DoubleConstant -10`) — a `FreePlacement` cube dropped over open space with nothing under it will fall via gravity, tile by tile, until blocked by another cube or the map edge. This is what makes a cube like the General mod's `Paratrooper` (`IDENT` + `FreePlacement`, no `Flying`) actually work thematically as "dropped from height, falls to the ground" with zero extra DSL — the fall is the base game's own gravity doing the work, not something the cube's own ability chain needs to implement.

**"When the cube below moves, this moves too" already exists as a reusable base-game ability — don't reimplement it.** `Hat` (`Extra_Mechanics/1Compounds.c.txt`, not `LOCAL`-scoped so any package can reference it) is exactly this:
```
COMPOUND: ABILITY
Hat
AfterACubeMoves If IsSameCube Caster CubeOfPosition PositionInDirectionFromPosition North OriginalPosition MoveInDirection EventDirection
Text: After a cube moves from the space below, move in the same direction End
Visual: Target 0 1 0 254 255
NO_DUPLICATES
End
```
Just write `Ability: Hat` bare — it already carries its own `Text:`/`Visual:`, no custom chain needed.
