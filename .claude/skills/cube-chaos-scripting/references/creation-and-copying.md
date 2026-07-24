# Creation & copying: spawning cubes, granting abilities at creation time, hand/library search

Load this when writing anything that creates a cube, copies a cube, grants an ability at or after
creation time, or scans a hand/library for a cube to act on.

## There is no `BeforeACubeIsCreated` trigger — so an `AfterThisIsCreated` ability can never be granted after the fact

The complete `Before*` production list (`ModdingInfo.txt:57-85`) has `BeforeACubeDies`, `BeforeACubeMoves`, `BeforeACubeIsAddedToAHand`, `BeforeACubeGainsAnAbility` and so on, but **nothing fires ahead of a cube's creation**. The creation-adjacent triggers are all `After*`: `AfterACubeIsCreated`, `AfterThisIsCreated`, `AfterThisCreates`, `AfterAnotherAllyIsCreated`, `AfterACubeCreationIsBlocked`, `AfterThisBlocksCreation`.

**Consequence, and it's a silent-failure shape:** an ability whose body is `AfterThisIsCreated ...` only ever works if the cube already had it *at* creation — via its own `CUBE:` block, or via `CopyWithAction` at the creation site. Granting it to an already-created cube (`TargetCube Victim GainAbility ThatAbility` inside an `AfterACubeIsCreated` reaction) parses clean, shows up in the tooltip, and **never fires**. No error, no log line.

This bites specifically when reacting to a cube created by something you don't control — e.g. a perk reacting to the Fungus species' `Mycelium`, whose `MyceliumGrowth` creator is `LOCAL`-scoped and can't be hooked upstream either.

**To make a one-shot creation-time ability genuinely grantable at any moment, trigger it on a self-removing tick instead:**
```
COMPOUND: ABILITY
YourKeyword
EveryTick Both
 <the one-shot effect>
 RemoveThisAbility
...
End
```
`EveryTick Action` is a real bare trigger (`ModdingInfo.txt:132`, many real usages without the usual `EveryXTimes` wrapper), and periodic-trigger-plus-`RemoveThisAbility` is the base game's standard one-shot idiom (`Main/1Compounds.c.txt:64,119,126,134,176`). It fires on the next tick whether the ability was baked in at creation or handed over later, which makes the ability uniformly grantable — and 1/60 s later than `AfterThisIsCreated` is invisible in play.

**One caveat this repo has not yet resolved:** whether cubes sitting in a *hand* tick. If they do, an `EveryTick` one-shot baked into a cube that can be held would fire while in hand rather than on arrival. `AfterThisIsCreated` is immune to that by construction, so it remains the safer choice when the ability only ever needs to work on cubes you create yourself.

## Runtime gotcha: `GainRandomAbilityOfCube` on a zero-ability cube

`GainRandomAbilityOfCube CUBE` (pick and grant ONE random ability from a cube) crashes at runtime — not at load/parse time — if the source cube happens to have zero `Ability:` lines (e.g. a bare `TOKEN` cube like DJ's `Record`, `CUBE: Record 0 1 1 / TOKEN`, no `Ability:` lines at all). It surfaces as a vague, unlabeled `ERROR: FILE ENDED BUT STILL LOOKING FOR ACTION / OFF NOTHING? / IN PACKAGE: GainStringResolved` in `Log.txt`, interleaved with battle-simulation lines (`AI STATS`, `Total delays`) since it only fires when that specific random pick actually happens mid-battle — never at boot, so a clean load doesn't mean this is safe. This is an easy trap for any "grab a random ability from a random cube/hand-card" mechanic (`ARandomCubeInLibraryWhich True`, scanning hand for cheap/token cubes, etc.).

Guard every such call site with a "has at least one ability" filter: `IsLarger AmountOfAbilitiesOfCubeWhich <CUBE> True DoubleConstant 0`. The "gain **all** abilities" variants (`GainAllAbilitiesOfCube`, `GainAllAbilitiesOfPerk`) don't need this guard — looping over zero abilities is just a no-op, not a crash.

**`RemoveRandomAbility` needs the identical guard, for the identical reason.** It's a bare terminal Action (no arguments, applies to the ambient receiver) that internally expands to `RemoveAbility ARandomAbilityOfCubeWhich Target True` (`Base_Core/1Compounds.c.txt`'s own `COMPOUND: ACTION` definition for it) — picking a random ability from zero is the same crash-shaped problem as `GainRandomAbilityOfCube`. The base game's own `Voids_Price` perk (`Main/NeutralPerks.c.txt`) guards it exactly like this: `If X%Chance DoubleConstant 90 If IsLarger AmountOfAbilitiesOfCube Victim DoubleConstant 0 ...RemoveRandomAbility...`. Note it uses the bare `AmountOfAbilitiesOfCube CUBE` (unfiltered total count) rather than the `...Which CUBE BOOLEAN` filtered variant — either works for a plain "has at least one ability" check, `AmountOfAbilitiesOfCube` is just fewer tokens when you don't need a filter predicate.

**Adding any `Ability:` to a previously zero-ability `TOKEN` cube silently changes what these guards mean — check every one before doing it.** The guard `IsLarger AmountOfAbilitiesOfCubeWhich Test True DoubleConstant 0` is doing double duty: it prevents the crash, *and* it is why bare token cubes are excluded from ability-donor pools in the first place. Bake one ability into such a token and it starts passing the guard everywhere — as a hand-scan donor, as an `ARandomCubeInLibraryWhich` pick, anywhere the pattern appears.

The dangerous case is baking a single **`NORANDOM`** ability (a cosmetic tag, or a keyword you want kept out of random-grant pools). `AmountOfAbilitiesOfCubeWhich Test True` counts it, so the guard passes, but `NORANDOM` makes it ineligible for the actual random pick — landing back in exactly the pick-from-nothing state the guard exists to prevent. Real case: an earlier version of the DJ mod's `Note` (then `0 0 0`, `TOKEN`, no abilities — `Note` has since been redesigned into a `0 1 1` homing projectile, see `GameData/DJ/DESIGN.md`) had a `NORANDOM` keyword baked in and immediately became a passing-but-unpickable donor at five separate sites. The failure shape applies to any zero-ability `NORANDOM` token, not specifically to `Note`.

Two fixes, both real:
- **Exclude the specific ability by name in the guard** — `IsLarger AmountOfAbilitiesOfCubeWhich Test Not AbilityHasName Test <TheAbility> DoubleConstant 0`. `AbilityHasName ABILITY WORD` takes a compile-time literal name; the ability-typed `Test` inside the predicate and the cube-typed `Test` outside it resolve independently because they're different types (see `cube-chaos-scripting/SKILL.md`'s "Implicit target resolution" section). Real base-game shape: `Characters/Synergies.c.txt:1120`, `EveryAbilityOfCubeWhich Storage Not AbilityHasName Test ChargeEveryX ...`.
- **Drop `NORANDOM`**, making the ability genuinely pickable. Safe from crashes, but the ability then spreads onto unrelated cubes via any random-ability mechanic.

When auditing, `grep` for `AmountOfAbilitiesOfCubeWhich` and `AmountOfAbilitiesOfCube` across the whole mod, not just the file being edited — the guards are usually written far from the cube whose ability count just changed.

## Faction numbers and default allegiance of created cubes

- Factions are numbered `0` = neutral, `1` = one player, `2` = the other (confirmed via dozens of `SetFaction DoubleConstant 1`/`2`/`0` calls, e.g. `Main/Perks.c.txt`'s `Both SetFaction DoubleConstant 1 ...` / `Both SetFaction DoubleConstant 2 ...` pair for "give a copy to each side"). To affect "everyone's hand" (both players) rather than one side relative to the caster, loop `EveryCubeInHandOfFactionWhich DoubleConstant 1 ...` and `EveryCubeInHandOfFactionWhich DoubleConstant 2 ...` explicitly — simpler and more literal than `FactionOfThis`/`InvertedFaction FactionOfThis`, which only get you "mine" vs "the opponent's" relative to the current Caster.
- `CreateCubeOnPosition`/`CopyWithAction` on a bare `CubeConstant X` **defaults to allied-to-Caster**, not neutral — confirmed by `Characters/Species/Shadow.c.txt`'s `Shadow_Hive` perk, which creates `CubeConstant Solid_Shadow_Hive` with no `SetFaction` call at all and its own `Description:` calls the result "an allied Solid_Shadow_Hive". The base game explicitly wraps in `NeutralCopy CUBE` (a different function) or appends `SetFaction DoubleConstant 0` when a spawned cube needs to be neutral instead. Don't assume a freshly created cube inherits the faction of whatever triggered its creation (e.g. `Victim`'s faction) — it won't, unless you explicitly `SetFaction FactionOfCube Victim` (or similar) yourself.

## Modifying a cube you just created: `CopyWithAction` at creation, never re-acquire it by position

**The single most common real bug shape in this repo.** To create a cube and give it something, it is tempting to create it and then look up whatever is now standing on that square:

```
Both CreateCubeOnPosition CubeConstant Rocket PositionInDirectionFromPosition North PositionOfThis
 If CubeExists CubeOfPosition PositionInDirectionFromPosition North PositionOfThis
  TargetCube CubeOfPosition PositionInDirectionFromPosition North PositionOfThis
   GainAbility HomingX 15
```

This is wrong, and it fails **silently and intermittently** — it looks correct in every test where the square happened to be free. `CreateCubeOnPosition` on an occupied square does not create anything and does not abort the surrounding chain; the following `CubeExists` check then passes against the **pre-existing blocker**, and the grant lands on that unrelated cube. User-reported symptom, found on `Rocket_Silo` and then `Airport`: "the cube blocking the spawn position is getting homing." A `Burrowing`/`AiEmptyNorth` cube is *more* exposed to this, not less — it spends its life adjacent to whatever it failed to burrow through.

**The fix is `CreateCubeOnPosition CopyWithAction CUBE ACTION POSITION`** — the action applies to the copy *before* placement, so it can only ever touch the cube being created, and a blocked creation grants nothing to nobody:

```
CreateCubeOnPosition CopyWithAction CubeConstant Bomb
 Both RemoveAbilityWithName Flying RemoveAbilityWithName ChargeEveryX
 PositionInDirectionFromPosition South PositionOfThis
```

Note the surrounding `Both` disappears — there is no longer a second action to sequence. This is overwhelmingly the base game's own idiom (71+ `CreateCubeOnPosition CopyWithAction` sites across every base file; the risky re-acquire shape appears essentially once, at `Characters/Classes/PerkFragments.c.txt:924`). **A guard-first shape (`If Not CubeExists <pos>` before creating) has zero occurrences in the base game** — don't invent it; it also doesn't help, since the interesting failure is "creation silently no-ops," not "we forgot to check."

**The one legitimate reason to re-acquire by position: another perk may have replaced your cube after creation.** `Arms_Race`-style perks (`AfterACubeIsCreated ... Exile` + create a different cube at `PositionOfCube Victim`) swap the cube out between your `CreateCubeOnPosition` and the next line, so a chain that must affect the *replacement* has to look it up by position. The tell is branching on names the created cube can't possibly have — the General mod's `Artillery` creates `CubeConstant Shell` yet branches on `CubeHasName Target Bomb`/`Rocket`, which are reachable only via that swap. Converting such a site to `CopyWithAction` silently turns those branches into dead code. Guard it with a name check instead of converting it:

```
TargetCube CubeOfPosition <pos>
 If Or Or CubeHasName Target Shell CubeHasName Target Bomb CubeHasName Target Rocket
  Both GainAbility Arcing DoubleConstant 180
   ...
```

So: **`CopyWithAction` by default; re-acquire only when a post-creation swap is genuinely being handled, and then always name-guarded.** When auditing a mod for this, grep for `TargetCube CubeOfPosition` and `TargetCube CubeInDirectionFromCube` — every hit is either a bug or a deliberate swap-handler, and the two are easy to tell apart by whether the chain branches on foreign cube names.

## Duplicating a specific live cube (e.g. pulled from hand) without consuming the original

`CreateCubeOnPosition CUBE POSITION` on a CUBE expression that's a **freshly-instantiated template** (`CubeConstant X`, or a value already built via `SetStorage CopyWithAction CubeConstant X ...` and reused across multiple positions) needs no special handling — every real example of that shape just calls `CreateCubeOnPosition Storage <position>` directly, since `Storage` there holds a template value, not a specific board/hand object.

But when the CUBE expression is a **specific live cube reference** picked out of hand (`ARandomCubeInHandOfFactionWhich`, `SetStorage ARandomCubeInHandOfFactionWhich ... Action`, etc.) and you want to place a duplicate of it while leaving the original sitting in hand untouched, wrap it in `CopyWithAction CUBE Action` — real precedent, `Modding_Example/GeneralCubes.c.txt`'s `Subwoofer` cube: `SetStorage ARandomCubeInHandOfFactionWhich FactionOfThis DoubleConstant 1 CreateCubeOnPosition CopyWithAction Storage PositionOfThis ...`. If there's no extra modification to apply to the copy (no `SetFaction`/`GainAbility` needed — a copy of an already-allied hand cube stays allied on its own), `Nothing` is a real, valid bare 0-argument `Action` (confirmed in `ModdingInfo.txt`'s Action production list, also used as a bare `Trigger:`/`Ability:` body meaning "no functional effect" — see `references/authoring-and-inheritance.md`'s tag-ability pattern) and works as `CopyWithAction`'s required trailing argument: `CopyWithAction Storage Nothing`.

`ARandomCubeInHandOfFactionWhich`/`ARandomCubeInLibraryWhich` can return "no match," so guard any read of the result: `SetStorage (search) Action`, then `If CubeExists Storage <use Storage>` inside that Action — real precedent, the DJ mod's own `DJ-No_Species` perk (`DJ/DJ_Synergies.c.txt`). Don't skip this guard just because the search happened inside a loop that already filtered candidates elsewhere; the search itself can still legitimately come up empty (e.g. no 0-mana cube currently in hand).

## "Scan a hand, maybe graft a random ability onto a cube" — check for a built-in analog first

`DJ/DJ_Cubes.c.txt`'s `Speaker` cube already implements almost exactly this shape and is the canonical real example to copy, via `AfterThisCreates` (fires on the cube that DID the creating, with `Victim` = the thing it just created — a stable trigger-bound reference, immune to loop rebinding, so no `SetStorage`/`TargetCube` juggling needed to keep pointing at it):

```
Ability: AfterThisCreates EveryCubeInHandOfFactionWhich FactionOfThis And IsSmaller ManaCostOfCube Test DoubleConstant 1
 IsLarger AmountOfAbilitiesOfCubeWhich Test True DoubleConstant 0
 SetStorage Test If X%Chance DoubleConstant 50 TargetCube Victim GainRandomAbilityOfCube Storage
Text: For each 0 mana cost cube in your hand that has an ability, 50% chance to give the creation one random ability of that cube End
```

Two idioms worth lifting from this: **fold a guard filter (like the zero-ability crash guard) directly into the loop's own `BOOLEAN` argument** (`EveryCubeInHandOfFactionWhich FactionOfThis IsLarger AmountOfAbilitiesOfCubeWhich Test True DoubleConstant 0 ...`) instead of nesting a separate `If` inside the Action body — fewer tokens, same effect. And **`FactionOfThis` inside `EveryCubeInHandOfFactionWhich` means "your hand"** — reach for this by default over hardcoded `DoubleConstant 1`/`2` faction literals unless you genuinely need both hands or a specific absolute side.

If `AfterThisCreates` isn't available (e.g. the creation happens inside a `PERK:`'s `Ability:` via `CreateCubeOnPosition`, not inside a `CUBE:`'s own ability, so there's no stable `Victim`-as-the-creation binding to reuse), fall back to granting the *created* cube a one-shot ad-hoc ability instead: `GainAbilityText ABILITY List` (not `GainAbility`, which only takes a pre-registered named ability — a custom chain needs `GainAbilityText` so it carries its own inline tooltip text, terminated by the literal word `End` just like `Text:`/`Description:`, e.g. `Characters/Classes/ZUpgradeClassPerks.c.txt`'s `Individual_Thought_Time` perk) an `AfterThisIsCreated ... RemoveThisAbility` chain. Inside that granted ability's own trigger body, `Caster` refers to the newly created cube itself (confirmed by `Base_Core/1Compounds.c.txt`'s `UpToXEfficiency` compound), giving you the same kind of stable, loop-proof reference `Victim` provides for `AfterThisCreates`. Real example (DJ-Shadow synergy perk, `DJ/DJ_Synergies.c.txt`): creates an allied Note in place of a dying Solid_Shadow, then runs the same Speaker-style scan against the caster's own hand:

```
CreateCubeOnPosition CopyWithAction CubeConstant Note
 Both SetFaction FactionOfThis
 GainAbilityText AfterThisIsCreated Both
  EveryCubeInHandOfFactionWhich FactionOfThis And IsSmaller ManaCostOfCube Test DoubleConstant 1
   IsLarger AmountOfAbilitiesOfCubeWhich Test True DoubleConstant 0
   SetStorage Test If X%Chance DoubleConstant 50 TargetCube Caster GainRandomAbilityOfCube Storage
  RemoveThisAbility
 For each 0 mana cost cube in your hand that has an ability, 50% chance to give this one random ability of that cube End
PositionOfCube Victim
```

Either way, the `SetStorage Test ...` step is required whenever the receiver (`Victim` or `Caster`) differs from the loop candidate: snapshot the loop candidate into `Storage` *before* switching the ambient receiver via `TargetCube`, since `Target`/`Test` used as a CUBE argument *inside* a `TargetCube` block resolves to that `TargetCube`'s own binder, not the outer loop's candidate. See `cube-chaos-scripting/SKILL.md`'s "Implicit target resolution" section for why.
