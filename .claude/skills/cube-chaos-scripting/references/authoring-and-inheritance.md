# Authoring custom compounds, undocumented fields, and ability inheritance/propagation

Load this when writing a new `COMPOUND: ABILITY` (keyword), using `Visual:`/`CubeColourShift:`, making
an effect propagate to created cubes, or building a battle-start/movement/creature-evolution primitive.

## `Visual:` — placement-preview markers (undocumented in ModdingInfo.txt/ModdingExplanation.txt)

### The rule: a fixed-offset positional effect ALWAYS gets a `Visual:` line — decide it mechanically, then verify

**Do this for every `CUBE:` you write or edit, before calling it done:**

1. **Run `grep -nE 'PositionInDirectionFromPosition|CubeInDirectionFromCube|TopPositionAboveCube' <file>`** over the block. Every hit is a candidate — do not eyeball the ability chain for "does this feel positional."
2. **Apply the table below to each hit** to get the required marker (or a decision to omit).
3. **Verify: the block's `Visual:` line count equals the number of distinct tile offsets the table produced.** A cube that affects 4 touching tiles needs 4 `Visual:` lines, not 1. This step is the point — "I checked and it looked fine" is exactly how `Hell_Portal` shipped without one.

| What the ability targets | Marker? | Write |
|---|---|---|
| Fixed offset from the cube — `PositionInDirectionFromPosition <Dir> PositionOfThis` / `... PositionOfCube Caster`, or `CubeInDirectionFromCube <Dir> Caster` | **Required** | `Visual: <Shape> X Y R G B`, one line per tile |
| Anywhere up/down a column — `TopPositionAboveCube`, "first empty space above" | **Required** | `Visual: Target 0 -1 96 96 96` then a bare `Visual: Infinite` |
| The cube's own tile — a **bare** `PositionOfThis`/`PositionOfCube Caster` used directly as the destination with no `PositionInDirectionFromPosition` wrapper around it, or `OriginalPosition` | **Omit** | Nothing. **Offset `0 0` appears in 0 of ~530 base-game `Visual:` lines** — there is no self-marker. (Don't confuse this with row 1: the wrapper is what makes it a *neighbouring* tile) |
| A dynamic/unpredictable tile — `ARandomPositionWhich`, above `ARandomEnemy`, a `Victim`'s position | **Omit** | Nothing. Base game omits here too (`Weed`, `Fungus_Heart`, `Growing_Worm`, `Green_Worm`) |
| An effect granted onto *another* cube via `Enchantment`/`GainAbilityText` | **Omit** | The marker would belong to the host cube, not this one (`Ring_Of_Shields`) |

**This is a house-wide default, not a per-cube judgement call.** Measured base-game ground truth, 2026-08-02: of the 23 base-game cubes that create a cube at a fixed offset, **18 carry a `Visual:`** — and the 5 that don't (`Piston_Leg`, `Ring_Of_Shields`, `Sky_Vine_Bulb`, `Boomerang`, `Container`) are base-game oversights of exactly the kind this rule exists to prevent, not a competing convention.

`TOKEN` cubes are included, not exempt — **65 base-game `TOKEN` cubes carry `Visual:` lines** (`Void`, `Mana_Node`, `Gift`, `Area_Heal`, …), because a `TOKEN` can still reach a hand via `AddCubeToHandOfFaction` or be placed by the AI under its `AiPlacementRule:`.

**Incident that forced this into a table (2026-08-02):** the user noticed `Hell_Portal` showed no spawn preview. A sweep then found **12** cubes across Broker/DJ/General/Unholy missing markers they should have had — `Hell_Portal`, `Baby_Bass_Dragon`, `Bass_Dragon`, `Baby_War_Dragon`, `War_Dragon`, `Plague_Ritual`, `Construction_Site`, `Brimstone`, `Blood_Totem`, `Bombardement`, `All_In`, `Skyscraper`. The rule already existed, as `content-cube.md`'s soft *"Check whether it needs `Visual:` placement-preview lines (any cube with a positional effect…)"* — a prompt to reflect, with no mechanical trigger and no verification step, so it was satisfiable by simply not thinking about it. `.claude/hooks/check-visual-coverage.sh` is the non-blocking backstop; the periodic one is `cube-chaos-audit`'s placement-preview row in its "DSL & mechanical safety" checklist, with the matching **"Placement-preview coverage"** recipe in that skill's `references/detection-recipes.md`.

### Syntax

```
Visual: <Shape> X Y R G B [N]
```

- `X Y` are tile offsets **relative to the cube**, in its default placed orientation: `+X` = Forwards/East, `-X` = Backwards/West, `+Y` = South (down), `-Y` = North (up). Confirmed by cross-referencing cubes whose actual `Ability:` targets `North`/`South`/`Forwards` against their own `Visual:` offsets (e.g. a "heal the cube below" cube uses `Visual: Plus 0 1 ...`).
- `R G B` is the marker color — reuse the game's existing color language rather than inventing one: gray `96 96 96` for "a cube will be created here", red `255 0 0` for damage/threat, green `0 254 33` for healing, ice-blue `109 209 228` or `155 238 255` for buff/utility/"related cube" markers.
- **Shape** picks the icon and argument count: `Square`/`Target`/`Plus`/`Mist` take exactly `X Y R G B` (5 args); `Sword`/`Arrow` take a 6th trailing number (reach/size, not fully decoded — copy an existing value like `1` or `2`). `Area N Mist R G B` is a different overload for radius-based AoE (N = radius, centered on the cube itself, no X/Y). A bare `Visual: Infinite` line directly after a `Target`/`Arrow` line extends that marker's ray to unlimited range (used for "any distance" abilities) instead of one fixed tile — 12 base-game usages, all on abilities whose own `Text:` says "any distance" or "in the row infront" (`Subtractor`, `Sky_Hungerer`, `Wood_Field_Projector`). That's why it's the correct rendering for a "top of this column" spawn.
- **"Touching" means the 4 orthogonal neighbors, not diagonals** — confirmed by a cube whose own tooltip says "all 4 touching positions" while its `Ability:` explicitly checks North/South/East/West only. For an ability using `EveryCubeTouchingPosition`, that's 4 markers: `1 0` / `-1 0` / `0 1` / `0 -1`.

## `CubeColourShift:` — tinting a cube's sprite via a granted ability (undocumented)

Like `Visual:`, `CubeColourShift:` is missing from both `ModdingInfo.txt` and `ModdingExplanation.txt` but is real and load-bearing. It's a field of a `COMPOUND: ABILITY` block (NOT a `CUBE:` block) — whichever cube instance currently *has* that ability gets its sprite tinted live, for as long as it holds the ability:

```
CubeColourShift: <strength 0-1> R G B
```

Confirmed real range for `<strength>`, from ~50 real usages: `0.1` for subtle status tints (`Slowed`, `TemporaryFlying`, `TemporaryStrength`) up to `0.9` for a strong/near-full recolor (base game's own `Golden` ability, and a blue status effect both use `0.9`). Nothing in the base game goes to `1.0` — treat `0.9` as the practical ceiling for "as visible as this field gets" rather than assuming `1.0` is safe/needed.

**`CubeColourShift` blends the tint against the sprite's existing colors, so multi-color art never reads as a fully clean/saturated tint no matter how high the strength goes** — a strength-0.8 blue tint over a gunmetal-gray-plus-olive-green cube (General mod's `Bomber`) still shows faint traces of the original hues, since the blend is per-pixel against whatever color was already there. Bumping `<strength>` toward the `0.9` ceiling is the cheap, zero-art-cost first lever (a one-number change, instantly reversible) — try this first. **If that's still not clean enough, repaint the underlying sprite in plain flat grayscale** (blending a tint against a grayscale image is the same math as a photo "colorize" filter — zero original-hue bleed-through at any strength): convert every non-background pixel to its own luminosity value (`0.299R+0.587G+0.114B`, R=G=B), nothing more. **Do not add a levels/contrast boost on top** (pushing bright/mid tones toward near-white while compressing dark tones toward near-black) — this was tried in the General mod (`Bomber`/`Bomber_West`/`Drop_Helicopter`/`Drop_Helicopter_West`/`Artillery`/`Recruit`/`Bunker`/`Airport`, all 8 tiles that can display the `Faction_Colours` tint) on the theory that a cleaner/more-white base would read as a more obviously-colored tint, and was explicitly reverted by the user ("way too white," "this is not as i intended") back to plain flat luminosity. Plain luminosity preserves the sprite's original shading/contrast relationships exactly — that's the point, and the correct target — rather than flattening most of the art into a narrow near-white band. Apply the LUT as a value-keyed dict built from the sprite's own actual observed grayscale values (sample first via a `Counter` per target tile) for precision, and verify the resulting tint by simulating the blend in a throwaway script (`pixel*(1-strength) + tint*strength` per channel) before trusting it looks right. Note the tint only applies once the granting ability is actually held — for an `AfterThisIsCreated`-granted tag like `Faction_Colours`, hand/inventory icons stay full original color; only placed-on-board instances show the shift.

**Pure cosmetic tag-ability pattern** — for "mark this specific cube instance with a color, no gameplay effect," copy the base game's own `Golden`/`Swarm`/`MyceliumGrowth` shape (all real, all `Nothing`-triggered):
```
COMPOUND: ABILITY
YourTag
Nothing
Text: \C<R> <G> <B> Your Tag Name \B : \CN \N \C96 96 96 (Cosmetic only, marks ...) \CN End
NO_DUPLICATES
NORANDOM
CubeColourShift: 0.9 <R> <G> <B>
End
```
- `Nothing` as the trigger body is valid syntax and means "no functional effect, this ability just exists as a flag/marker."
- The `Text:` follows this repo's standard keyword shape — colored name, `\B :`, `\N`, then a dim `96 96 96` parenthesised explanation opening with "Cosmetic only," so a player isn't left hunting for an effect that doesn't exist. See `cube-chaos-rule-text` for the full convention and the color vocabulary.
- `NO_DUPLICATES` stops the tag from stacking if granted more than once.
- `NORANDOM` excludes the ability from random-ability-grant pools. Confirmed by grepping every real `NORANDOM` usage in the base game: applied uniformly to internal AI-only scaffolding abilities (`AiPlacementAdd`, `AiWarrior` in `Base_Core/2AiCompounds.c.txt`) and to abilities explicitly marked deprecated ("no longer used... kept in case some mod uses it"). Reads as a general "never eligible to be handed out by any random-ability mechanic" flag rather than something narrower — apply it to your own tag abilities so a "steal a random ability from a hand/board cube" mechanic (`GainRandomAbilityOfCube`, see `references/creation-and-copying.md`'s Speaker-style pattern) doesn't spread your cosmetic marker onto unrelated cubes. (Caveat: not verified by decompiling the engine, just by convention — the base game's own `Golden` tag deliberately does NOT set `NORANDOM`, presumably because being copied is thematically fine for a "golden" bonus; decide per-case whether propagation is desirable for your tag.)
- **There is no known way to fully hide an ability's line from a cube's rules/tooltip panel.** Searched for a `HIDDEN`/`NOTEXT`-style flag across the complete undocumented all-caps flag vocabulary in every `GameData/**/*.c.txt` file and found only `NO_DUPLICATES`, `NORANDOM`, `LOCAL`, `TOKEN`, `IDENT` — nothing that suppresses tooltip rendering. Every granted ability shows at least its `Text:` line, even a minimal one like `Golden`'s (`Text: \C255 238 0 Golden End`). If you want a tag unobtrusive rather than fully gone, the only lever is giving its own `Text:` a low-contrast color against the tooltip's dark background — a deliberate visual trick, not a real hide.
- **The tooltip/rules-panel lists an ability's abilities in grant order, first-granted first.** When a chain grants 2+ abilities to the same cube via `Both (GainAbility A) (GainAbility B)` (or `GainAllAbilitiesOfPerk`/similar), whichever is granted first in the token sequence renders first in-game. Confirmed empirically on `DJ/DJ_Synergies.c.txt`'s `DJ-Moil` perk: swapping `Both (GainAllAbilitiesOfPerk ...) (GainAbility Moil_Blessed)` to `Both (GainAbility Moil_Blessed) (GainAllAbilitiesOfPerk ...)` moved `Moil_Blessed` from the bottom to the top of the rendered ability list, with no other change.

## Parameterized `COMPOUND: ABILITY` — `Generic*` placeholders + `CODE N` in the text

A mod compound can take arguments exactly like a built-in (`ExplodesX 4`, `ChargeEveryX 120`). There is **no parameter declaration line** — you write a typed `Generic*` placeholder in the body, and the engine infers the signature from it. The full placeholder vocabulary, by real usage count across `GameData/`: `GenericStacking`, `GenericCube`, `GenericAction`, `GenericDouble`, `GenericTime`, `GenericConstant`, `GenericPerk`, `GenericWord`, `GenericString`, `GenericBoolean`, `GenericAbility`, `GenericPosition`, `GenericName`, `GenericDirection`.

In the `Text:`, `CODE 1` / `CODE 2` substitute the parameters in declaration order (`STACKING 1` for a `GenericStacking`). Pair with `\B` to kill the space before punctuation:

```
COMPOUND: ABILITY
Rhythmic
EveryTick Both
 <effect using GenericConstant as the chance>
 RemoveThisAbility
Text: \C255 255 0 Rhythmic CODE 1 \B : \CN \N \C96 96 96 (... CODE 1 \B % chance to ...) \CN End
NORANDOM
End
```

Real precedents: `ExplodesX`/`EveryXMeleeY`/`ChargeEveryX` (`Base_Core/1Compounds.c.txt`), `MiseryX`/`EyeXY`/`JumpXY` (`Extra_Mechanics/1Compounds.c.txt`), `DelayedDamageX` (`Main/1Compounds.c.txt`), and `ReplicrabUpgradeX` (`Main/CubeUpgrades.c.txt:839`) for the specific `X%Chance GenericConstant` + `CODE 1 \B % chance` combination. Multi-parameter compounds order by first appearance in the body (`EveryXMeleeY` = `GenericTime` → `CODE 1`, `GenericConstant` → `CODE 2`).

See `cube-chaos-rule-text` for the standard keyword header/explanation text shape and for `\A`, which renders a compound's whole `Text:` inline at every site that grants it.

### A mod-authored `COMPOUND: ABILITY`'s own declared name should not contain `_`

Runtime-confirmed by isolation testing (Unholy mod, 2026-07-25, same session as the `GenericCube` finding below): a brand-new `COMPOUND: ABILITY` whose bare name line contains an underscore — tested with both `Soul_Memory` and a deliberately generic-word control, `Foo_Bar` — produces `ERROR: character: (_) cannot be represented numericly but is in one of the defined abilities` at boot (one instance for the definition, a second for each `GainAbility <Name>` grant site referencing it), **even with a minimal body that's a token-for-token copy of a real working `Ability:` line** (`AfterThisDies CreateCubeOnPosition CubeConstant Imp PositionOfCube Caster`, identical to `Ritual`'s own working ability in the same mod). Renaming to remove the underscore (`TESTFOO`, then the real `SoulMemory`) — no other change — made the error disappear completely, confirmed by a full clean 0-`ERROR` boot-to-exit log. File position (before vs. after the package's own `BelongsTo: SPECIES`/`CLASS` perk) was also tested and ruled out as a factor.

**This appears to contradict real underscored compound names that work fine elsewhere** (`Dragon_Egg`, `Take_Off`, `General_Inherited_Strength`, `Moil_Rhythm`) — the likely explanation is that this is a latent, silent, non-fatal parse-time error that's always been there for those too, just never isolated: the ability still registers and functions correctly (as the whole rest of this mod's history of underscored compounds confirms), so nobody had reason to grep `Log.txt` for an unlabeled `ERROR` line sitting harmlessly among hundreds of others. It has not been proven harmless for every case, so don't rely on that — it just hasn't been observed to break anything beyond the log line itself, in this specific isolation test.

**Practical rule: give any new mod-authored `COMPOUND: ABILITY` an underscore-free name** (`SoulMemory`, `PascalCase`/`CAPSNOSPACE`, matching `ARCING`/`OVAR`/`IDX`/`DJRMAX`-style `SetVariable` names elsewhere in this codebase) — cheap, zero downside, and confirmed clean. This does **not** apply to `CUBE:`/`PERK:` names (`Damned_Soul`, `Plague_Imp`, `Hell_Dragon_Egg` all coexist error-free in the very same file/test) or to `SetVariable` variable names (`MYCELIUM_DIR` in the base game's own `Fungus.c.txt` has an underscore and works) — isolation testing narrowed this specifically to a `COMPOUND: ABILITY`'s own declared name line, nothing else.

### `GenericCube` is NOT usable in a mod-authored `COMPOUND: ABILITY` — despite being a real, listed production

`ModdingInfo.txt:561` lists `GenericCube` in the CUBE production list alongside every other `Generic*` placeholder, and the base game's own `Dragon_Egg`/`GrowingUp` compounds (`Characters/1Compounds.c.txt:1-11`, used by every dragon-egg line including this repo's own `Hell_Dragon_Egg`) use it exactly like any other generic parameter — which reads as strong precedent that it's a normal, modder-usable mechanism. **It is not.** Runtime-confirmed by isolation testing (Unholy mod, 2026-07-25): defining a mod's own `COMPOUND: ABILITY` with a `GenericCube` placeholder —

```
COMPOUND: ABILITY
Soul_Memory
AfterThisDies CreateCubeOnPosition CopyWithAction GenericCube Nothing PositionOfCube Caster
Text: After this dies, create an allied CODE 1 on its position End
End
```

— produces `ERROR: character: (_) cannot be represented numericly but is in one of the defined abilities` at boot, **just from the definition existing**, whether or not anything ever grants it (`GainAbility Soul_Memory Victim` added one more instance of the same error on top; removing only that dynamic-grant call still left the error, and it only reached zero once the whole `COMPOUND:` block was deleted). The error text itself is the tell: the engine's generic-parameter storage is fundamentally numeric internally (works fine for `GenericConstant`/`GenericDouble`/`GenericStacking`/`GenericTime`), and a CUBE-typed value — or a name/identifier containing `_`, going by the exact wording — can't be encoded into it. `Dragon_Egg`/`GrowingUp` presumably work because they're hardcoded engine-side, not because `GenericCube` is a working general mechanism reachable from mod-authored DSL.

**Consequence for "remember which cube type X was, act on it later" mod mechanics: there is no working dynamic-parameter path for this.** Zero real usage of `GenericCube` exists anywhere in the base game or any mod in this repo (confirmed by grep before this incident) — that absence is now explained, not just unexplored. Reach for one of these instead:
- **A finite, known set of possible cube types**: define one non-parameterized helper compound per specific type (`AfterThisDies CreateCubeOnPosition CubeConstant <ThatOneType> ... PositionOfCube Caster`, no generic needed), then branch on `CubeHasName` at the grant site to pick which one to `GainAbility`. Scales linearly with roster size, zero risk, but only covers types you explicitly enumerated — needs a sensible fallback (e.g. a generic default) for anything outside that set. Real usage: Unholy's `Phylactery` perk (`Unholy_Species.c.txt`) — one `Soul_Memory_<CubeName>` compound per starter cube in its own species roster, defaulting to `Soul_Memory_Imp` for anything unrecognized.
- **If the recreation can happen immediately instead of after a delay** (same trigger, no need to survive to a *later*, independent death event), skip the whole generic-parameter problem: act on the live cube reference directly in the same chain (`CopyWithAction <live-cube-ref> Action`, per `references/creation-and-copying.md`'s "duplicating a specific live cube" section) rather than trying to bake its identity into a granted ability for later.

## Making an ability propagate to created cubes: the base-game `Inheritable` modifier

For "cubes created by this also get ability X (recursively)," don't hand-roll an `AfterThisCreates TargetCube Victim GainAbility X` grant — the base game already has a reusable modifier, `Inheritable` (`Base_Core/1Compounds.c.txt:567`, `NORANDOM`), whose tooltip (`Base_Core/ToolTipText.c.txt:73`) reads *"Cube created/added to a players hand by this also gain this ability"*:
```
COMPOUND: ABILITY
Inheritable
AfterThisCreates If Not IsPlaced TargetCube Victim GainThisAbility
ExtraTrigger: BeforeThisAddsACubeToHand TargetCube Victim GainThisAbility
NORANDOM
End
```

How it actually works — and the non-obvious parts that bit during the General mod's `General-Remnant` rewrite:

- **It's attached via `ExtraTrigger: Inheritable` placed on an ability line inside a `CUBE:` or `COMPOUND: ABILITY` definition — a *definition-time* composition, NOT something you dynamically bolt onto an existing ability at grant time.** Real base-game usage: `Main/CubeUpgrades.c.txt`'s `BurningDamage` (`AfterThisDealsDamage ... GainAbility Burning` then `ExtraTrigger: Inheritable`), and cube ability lines in `Main/3GeneralCubes.c.txt` (`ExtraTrigger: Inheritable` right after the `Ability:` it modifies). The convention is to also append `, Inheritable` to that ability's own `Text:`.
- **`GainThisAbility` propagates the *whole* ability the `ExtraTrigger: Inheritable` is part of — recursively** (the created cube gets the full compound, including its own `Inheritable`, so *its* creations inherit too), but **only to non-placed cubes** (`If Not IsPlaced`) plus cubes added to hand. So it fires for cubes *spawned by* the holder, not for cubes the player hand-places.
- **Granting `Inheritable` standalone (`GainAbility Inheritable`) does nothing useful** — its `GainThisAbility` would only re-propagate `Inheritable` itself, carrying no actual effect. To make some effect (e.g. `StrengthX`) inheritable you must define your *own* compound that bundles the effect body **and** `ExtraTrigger: Inheritable`, then grant/reference that compound.
- **A bare passive stat ability works fine as that compound's body** — confirmed by load-testing `StrengthX 1` as the body line of a mod compound under `ExtraTrigger: Inheritable` (parsed clean, no `CANT READ`). This matters because a passive stat is exactly what you want the *holder itself* to benefit from: the holder gets the stat via the body, and the whole compound cascades to its creations via the ExtraTrigger. Real usage, General mod's `General_Inherited_Strength` (`GameData/General/General_Synergies.c.txt`), granted to placed allies by the `General-Remnant` synergy (`AfterACubeIsCreated If And IsAllyToCaster Victim IsPlaced → TargetCube Victim GainAbility General_Inherited_Strength`) so the placed ally deals +1 and every cube in its creation tree inherits +1:
```
COMPOUND: ABILITY
General_Inherited_Strength
StrengthX 1
ExtraTrigger: Inheritable
Text: \C255 38 0 Strength 1 \CN , Inheritable End
NO_DUPLICATES
NORANDOM
End
```
- **The mod compound must be defined earlier in the same file than the perk/cube that references it** (the same single-pass ordering constraint documented in `references/gotchas-grepped.md`) — `General_Inherited_Strength` sits at the top of `General_Synergies.c.txt`, before the first perk. Defining it in the same file as its only user also sidesteps the cross-*package*/cross-*file* load-order trap entirely.
- **Semantic contrast to weigh before choosing this over a hand-rolled grant:** `Inheritable` makes the *holder itself* carry the effect and cascades it *recursively* down the whole creation tree. A plain `GainAbilityText AfterThisCreates TargetCube Victim GainAbility X` grant instead leaves the holder unaffected and only buffs its *direct* creations (non-recursive). These are genuinely different mechanics — pick per intent, and surface the difference to the user when a request ("cubes created by this gain X") is ambiguous about whether the holder benefits or whether it should cascade.
- **Inverse/opt-out exists:** `TheInheritor` (`Main/1Compounds.c.txt:72`, `Text: \C255 0 220 Inheritor: \CN Cubes created by this cube won't inherit abilities`) is a cube-side ability that blocks inheritance from happening on that cube's creations.

## Preserving a dynamically-granted ability through a "replace this cube with a different cube" cascade

A perk that intercepts cube creation and substitutes a different cube type (`AfterACubeIsCreated: If CubeHasName Victim X, Exile + CreateCubeOnPosition CubeConstant Y`, e.g. an ammo-tier upgrade chain) creates a **fresh** cube from `Y`'s own template — it does NOT inherit any ability that was dynamically granted to the specific `X` instance being replaced (e.g. `Arcing`/`ChargeEveryX` granted only to that one fired shot, not baked into `X`'s or `Y`'s `CUBE:` definition). Trying to thread that grant through every substitution rule (checking "did the replaced cube have Arcing, if so re-grant it onto the replacement") works but tightly couples the substitution perk to the granter's internal mechanics, and has to be repeated at every tier of the cascade.

**Cleaner: decouple the two concerns entirely.** Have the *original granter* (the cube/perk that dynamically granted the ability in the first place) apply it *after* creation, by looking up whatever cube currently occupies the target position — rather than attaching it to the specific instance being created:
```
Ability: EveryXSeconds DoubleConstant 20 Both CreateCubeOnPosition CubeConstant Shell PositionInDirectionFromPosition North PositionOfThis
 If CubeExists CubeOfPosition PositionInDirectionFromPosition North PositionOfThis
  TargetCube CubeOfPosition PositionInDirectionFromPosition North PositionOfThis
   Both GainAbility Arcing DoubleConstant 180
    Both GainAbility ChargeEveryX 15
     SetVariable ARCING RandomRoundBetweenXtoY DoubleConstant 17 DoubleConstant 25
```
This relies on the DSL's synchronous execution model: by the time the second half of the `Both` runs, any `AfterACubeIsCreated` reactions triggered by the `CreateCubeOnPosition` call above it (including a cascading substitution perk that itself replaces the cube one or more times) have already fully resolved, so `CubeOfPosition` at that same position reliably finds whatever the *final* cube ended up being — Shell, or whatever it got upgraded into — with no coordination needed between the granter and the substitution perk at all. Note this also means `GainAbilityText AfterThisIsCreated ...` (the usual idiom for initializing a variable like `ARCING` on a freshly-created cube, see `references/creation-and-copying.md`'s Speaker-style pattern) is the **wrong** tool here — the found cube was already created, so `AfterThisIsCreated` will never fire for it again. Use a bare, immediate `SetVariable` instead, since we're acting directly on an already-existing cube via `TargetCube`, not reacting to its creation.

**Corollary bug shape: don't bake a movement/behavior ability into just one cube of a substitution chain if its siblings don't share it.** A token cube meant to be swapped mid-chain (e.g. `Shot` → `Shell` → `Bomb` → `Rocket` via an `Arms_Race`-style ammo-tier perk) should either have ALL chain members share the ability, or none of them baked in (granting it dynamically at each creation site instead, per the pattern above) — never just one link. Real incident, an earlier version of the General mod's own `Bunker`/`Shot`: `Bunker` fires a burst of 3 `Shot`s from a fixed position, and `Shot` alone (not `Shell`/`Rocket`) had `Ability: ChargeEveryX 15` baked in to move it out of the spawn tile before the next burst-shot. This looked fine in isolation, but the moment the player also owned `Arms_Race` (Shot→Shell substitution), each fired `Shot` got `Exile`d and replaced by a fresh, immobile `Shell` (no `ChargeEveryX` baked into *its* block) — the substitution is a same-position replacement, so the baked ability never had a chance to matter, and the immobile Shell then blocked every subsequent burst (`IsPositionEmpty` never true again). That incident's fix at the time was the "dynamic grant at the spawn site" branch: strip `ChargeEveryX` from `Shot`'s own block, grant it via `Bunker`'s own post-creation lookup instead.

**A later session deliberately picked the other branch, and the reasoning is worth recording since both branches are legitimate depending on what's actually being asked.** When `Shot`/`Shell`/`Bomb`/`Rocket` were made independently obtainable/hand-placeable (real mana cost + `IDENT`), the ask was for all four to self-propel toward the enemy like a normal missile when placed directly from hand — which is only possible if the movement is baked into every one of them (a hand-placed cube has no spawner around to dynamically grant it anything). This reintroduced `Flying`+`ChargeEveryX 15` into all four `CUBE:` blocks uniformly (the "all chain members share it" branch, still satisfying the rule above), which made the *existing* per-spawner dynamic grants in `Bunker` (Shot), `Artillery` (Shell, alongside `Arcing`), and `Rocket_Silo` (Rocket, alongside `Take_Off`+`HomingX`) either purely redundant or actively conflicting (a second independent `ChargeEveryX` instance stacked on top of the baked one; or a baked forward-charge fighting `Rocket_Silo`'s intentionally-different vertical `Take_Off` launch).

**Before baking a new `Ability:` into a `CUBE:` that's already created by other cubes'/perks' abilities elsewhere in the codebase, grep every `CreateCubeOnPosition CubeConstant <ThatCube>` site first** (across the whole mod, not just the file being edited) — each hit is a place that might already dynamically grant something which now needs handling one of two ways:
- **Exactly duplicates the new baked ability** (e.g. `Bunker` granting the same `Flying`+`ChargeEveryX 15` `Shot` now has by default): delete the now-redundant grant from the spawner entirely.
- **Wants genuinely different behavior than the new default** (e.g. `Rocket_Silo` wants `Take_Off`'s vertical launch, not the new baked forward-charge; `Bomber`'s dropped `Bomb` needs to fall straight down, not fly off): keep the spawner's own grant, but first strip the now-unwanted baked ability at that one spawn site using the same `CubeOfPosition`-after-creation lookup, just with `RemoveAbilityWithName` in place of `GainAbility`:
```
Both CreateCubeOnPosition CubeConstant Bomb PositionInDirectionFromPosition South PositionOfThis
 If CubeExists CubeOfPosition PositionInDirectionFromPosition South PositionOfThis
  TargetCube CubeOfPosition PositionInDirectionFromPosition South PositionOfThis
   Both RemoveAbilityWithName Flying RemoveAbilityWithName ChargeEveryX
```
Real usage: `Bomb` got the same baked `Flying`+`ChargeEveryX` as its siblings for the direct-placement "flies like a missile" case, but `Bomber`'s own "drop a bomb below me" mechanic (and this mod's own `General-Shadow` synergy and `Bombardier` cube, both of which also create `Bomb` for a "drops from above" effect) all depend on that specific dropped `Bomb` falling straight down instead — all three of those spawn sites now strip `Flying`/`ChargeEveryX` off immediately after creating it, leaving the baked default (fly toward the enemy) intact for every *other* path a `Bomb` can come from (hand-placement, `General-Devourer`'s "add to hand" synergy, landing at the end of an `Arms_Race`-chain substitution). This scales to as many "opt this one spawn site out" cases as needed — each is independent and doesn't affect the others.

## Battle-start, movement, and creature-evolution primitives (from the Dragon-line work)

Discovered building the mods' Dragon evolution lines (see `cube-chaos-orchestrator`'s
`workflows/content-dragon-line.md` for the full recipe), but each is reusable well beyond dragons:

- **"Start each battle with a free X in hand"** — the base idiom is a self-removing battle-start grant:
  `Ability: AtTheStartOfTheBattle Both AddCubeToHandOfThis FreeCopy CubeConstant <X> RemoveThisAbility`
  (`Characters/Classes/Cryomancer.c.txt:67`). `FreeCopy CUBE` makes the added copy cost 0 mana;
  `CopyOfCube CUBE` is the plain-copy variant used by the equivalent *upgrade* perk
  (`ZUpgradeClassPerks.c.txt:590`). `RemoveThisAbility` fires once so it doesn't re-add every battle-start.
- **`ReferenceCube: <Name>`** is a real, repeatable `PERK:` field (`Cryomancer.c.txt:68-70`) that lists
  related cubes in the perk's tooltip — use it so a perk that grants/creates cubes can preview them (e.g.
  an egg perk showing the whole egg→baby→adult chain).
- **`RandomMovementX TIME`** (`ModdingInfo.txt:204`, "Every CODE 1 move in a random direction"; real
  usages `Main/2TokenCubes.c.txt:59,356,757`, `Main/3GeneralCubes.c.txt:1492,2516`) — layer it on top of
  a `ChargeEveryX`-driven cube to make its path drift organically instead of a dead-straight line. Unlike
  `ChargeEveryX`+`FleeEveryX` (which oppose and jitter — see `references/targeting-movement-board.md`'s
  patrol section), `RandomMovementX` composes fine with a directional mover.
- **`Burning`** (`ModdingInfo.txt:89`) is a **0-argument** keyword (colour `255 106 0`), NOT a stacking
  one — there is no `Burning N`. Its effect ("after 5s deal 1 damage to every touching cube **and this**")
  is fixed; `GainAbility Burning` is idempotent, so re-applying it faster doesn't increase the burn rate,
  it only re-ignites newly-arrived cubes. Granting it to all enemies makes them damage each other and
  themselves — a chaotic spread effect, not clean single-target damage. For fast *scaling* fire damage,
  use direct `TakeXDamage` on a short `EveryXSeconds` instead.
- **"Teleport (or spawn) at the top of a random enemy's column"** — the reusable idiom is
  `SetStorage ARandomEnemy` → guard `If CubeExists Storage` → act on `TopPositionAboveCube Storage`
  (`ModdingInfo.txt:718`, returns the top position of the column above a cube). With `TeleportToPosition
  POSITION` (`ModdingInfo.txt:307`) it repositions the acting cube into enemy territory; with
  `CreateCubeOnPosition` it drops a cube there (base precedent: the DJ mod's `Keyboard`,
  `DJ/DJ_Cubes.c.txt:56-60`, spawns a Note that way). Note **teleport-to-enemies is NOT a default on base
  dragons** — checked Icy/Anger/Magic/Iron/Robot/Ancient, none teleport; build it explicitly if wanted.
- **The `Dragon_Egg CUBE` and `GrowingUp CONSTANT CUBE` compounds** (`Characters/1Compounds.c.txt:1-5`
  and `7-11`) are the base game's stock "hatch after 4 min" and "transform when maxhp passes a threshold"
  mechanics. **Both are non-`LOCAL`** (the file's first `LOCAL` is at line 86, after them) and
  `Characters` loads before mod packages, so a mod cube may reference them directly. `GrowingUp` reads
  **maxhp** (pair with `GrowthX` to climb the threshold), and its transform is `Exile` +
  `CreateCubeOnPosition` in place.
