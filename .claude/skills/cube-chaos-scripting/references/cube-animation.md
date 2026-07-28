# Cube animation via `Animation:` — undocumented, CUBE-only, real and extensively used

`Animation:` is a genuine `.c.txt` keyword the parser accepts — confirmed via `Library.ReadAnimation` and 250+ real
usages across `Main/3GeneralCubes.c.txt` and other base-game `CUBE:` files (`grep -c "Animation:" GameData/**/*.c.txt`).
It is **completely undocumented** in `ModdingInfo.txt`/`ModdingExplanation.txt` — the only reason we know the exact
grammar is a 2026-07-28 decompile of `Cube Chaos.jar` (see the "How this was researched" section at the end for the
reusable method). Log.txt reports a running total at every launch: `"-N Animated Cubes"`.

**This is a `CUBE:`-only feature.** `Perk.class` has no `AnimatedCG` field at all, and `Library`'s `"Animation:"` case
only exists inside `CUBE:` parsing (`ReadAnimation(Ability lastAbility, Cube C)`) — there is no equivalent for `PERK:`
blocks. A `CubeUpgrade` (or any other) perk's own icon/border **cannot** be animated this way; see
`cube-chaos-sprite-art`'s CubeUpgrade compositing section for what actually can and can't move on a perk tile. If a
"Result:" cube preview (or any other place a `Cube` gets fully drawn) appears to animate, that's the underlying
**cube's own** `Animation:` playing out live — `Cube.Draw()` renders the fully processed `DrawnCG` pipeline, not a
static sprite — not anything to do with the perk compositing it.

## File convention

Frame art lives in a **separate PNG per animation**, not the cube's main sprite sheet:

```
<PackageFolder>/Sprites/Animations/<CubeName>_<AnimationName>.png
```

e.g. a `CUBE: Hell_Dragon` with `Animation: Fire ...` needs `GameData/Unholy/Sprites/Animations/Hell_Dragon_Fire.png`.
Confirmed via `PnGReader.FindCGForCube`: `Before + "/Sprites/Animations/" + C.Name + "_" + A.Name + ".png"` (`Before`
is the package's own root folder, derived from the cube's own `.Path`). Missing file → `Failed to find animation
file: ...` printed to the log, non-fatal (the cube just never animates).

That PNG is sliced **exactly like a normal CUBE sprite sheet** — `SplitSpriteGrid(15, 15, i, 1)`, i.e. 17px-stride
tiles (15×15 usable content after the same 1px trim every CUBE icon gets), one tile per frame, **row-major, index 0
first**, sized to fit the animation's declared frame count (`Amount`, see grammar below) — same
`grid_dim = ceil(sqrt(Amount))` sizing convention as any other sheet.

## Where to put an `Animation:` line

Inside the `CUBE:` block, same as `Ability:`/`Text:`. `CLOCK` and `TRIGGER` types bind to `lastAbility` — **the most
recently parsed `Ability:` in that same cube block** — so those two types must come *after* the `Ability:` they're
meant to key off. `HP`/`DOUBLE`/`BOOLEAN`/`TIME` don't bind to an ability and can go anywhere in the block.

A cube can have **multiple** `Animation:` lines; they apply in sequence, each one further modifying the previous
one's result (`AnimatedCG.Recalculate`: `Result = A1.Affect(A2.Affect(Result))`-style fold) — e.g. one `HP`-driven
damage-crumble animation plus one `TIME`-driven idle shimmer can coexist on the same cube.

## Grammar, per type

`Animation: <Name> <TYPE> <EffectType> ...` — `Name` becomes the `_<Name>.png` suffix above. `EffectType` is an int;
**every single real base-game usage is `0`** (full-frame swap — see "EffectType" below). All six types share an
`EQUAL <Amount>` shorthand vs. an explicit-thresholds form; both allocate `Frames[Amount]`, filled later from the
sliced PNG, indices 0..Amount-1 in file/sheet order.

- **`CLOCK <EffectType> [EQUAL <Amount> | <Amount> <t0> <t1> ... <t(n-1)>]`** — tied to `lastAbility`'s own `Clock`
  (a stock cooldown/limited-uses timer). Each tick, `Ratio = Clock.Timer / DetermineClockThreshold()` (0..1), then
  walks the threshold list cumulatively (`while Ratio >= Thresholds[i]: Ratio -= Thresholds[i]; i++`) to land on a
  frame — i.e. a literal "how full is the cooldown bar" animation. `EQUAL <Amount>` divides into `Amount` equal
  segments. Real example: `Animation: ManaGen CLOCK 0 EQUAL 3` (right after a mana-generating `Ability:`).
- **`TRIGGER <EffectType> [EQUAL <Amount> <Total> | <Amount> <t0>...<t(n-1)>]`** — also tied to `lastAbility`, but
  driven by `(System.currentTimeMillis() - Ability.LastActionTime) / 16` (~frames since that ability last fired) —
  a short one-shot flourish that plays right after the ability triggers, then settles back to frame 0. `EQUAL`'s
  extra `<Total>` divides evenly across `<Amount>` frames (integer division — pick a `Total` that's a clean multiple
  of `Amount` or the last segment silently absorbs the remainder). Real example: `Animation: Shoot CLOCK 0 EQUAL 4`
  style entries tied to attack abilities, and `Animation: Gift TRIGGER 0 EQUAL 4 20`.
- **`HP <EffectType> [EQUAL <Amount> | <Amount> <t0>...<t(n-1)>]`** — no ability binding. `Ratio = 1 - Health/MaxHealth`
  (0 at full HP, →1 near death), same cumulative-threshold walk. The base game's whole `Crumble` family (walls,
  rocks, structures visibly cracking as they take damage) is this: `Animation: Crumble HP 0 EQUAL 4`.
- **`DOUBLE <EffectType> [EQUAL <Amount> | <Amount> <t0>...<t(n-1)>] <DOUBLE-production> <DefaultFrame:int>`** —
  the fully general case: any `DOUBLE` production at all (stacking count, mana, distance, whatever) is evaluated live
  and walked against the thresholds, **only while the cube is actually placed on a board (`Zone > 0`)** — otherwise
  it falls back to `<DefaultFrame>`. Real example: `Animation: Armor DOUBLE 0 8 0 1 1 1 1 1 1 1
  GetStackingOfAbilityOnCube ArmorX Caster 6` (frame reflects current Armor-ability stack count, capped at 8 frames,
  default frame 6 when not in play).
- **`BOOLEAN <EffectType> <BOOLEAN-production> <DefaultFrame:int>`** — exactly 2 frames (index 0 = false, 1 = true),
  picked from a live `BOOLEAN` production while `Zone > 0`, else `<DefaultFrame>`. No thresholds/`Amount` at all.
- **`TIME <EffectType> <Amount> <t0> <t1> ... <t(n-1)>`** — a free-running, **unconditional** loop: `Tick()` always
  advances a counter regardless of `Zone`/battle state, holding each frame for `t_i` ticks (~60/sec) before moving to
  the next, wrapping back to frame 0 after the last. **This is the only type that animates outside of battle too** —
  in an inventory list, a library/compendium screen, a Forge "Result:" preview, anywhere the cube is drawn at all —
  since it never checks `Zone`. If something looked like it was animating/cycling colour in a non-battle UI screen,
  it was almost certainly a `TIME` animation on that specific cube, not anything to do with a perk border. Real
  examples: `Animation: Fly TIME 0 3 20 20 20`, `Animation: Rotate TIME 0 3 20 20 20`.

## `EffectType` — how a picked frame actually gets applied

From `Animation.AffectType(CG, Frame)`:
- **`1`**: `CG.Combine(Frame, 38143)` — overlay `Frame`'s non-background-colour pixels on top of the current image,
  leaving everything else untouched. Good for a small decorative detail (a blinking light, a colour-cycling gem)
  without touching the rest of the sprite.
- **any other value, including the default `0` every real cube uses**: `CG.OverrideWithBIfEqualC(Frame,
  OwnerCG.Base)` — replace pixels that still match the cube's original un-animated art with `Frame`'s pixels; a full
  masked frame-swap. `0` is a 100%-consistent choice across the entire base game (no real file uses anything else),
  so default to `0` for new animated cubes unless there's a specific reason to try `1`.

## How this was researched (reusable method for future undocumented-mechanism questions)

`ModdingInfo.txt`/`ModdingExplanation.txt` document nothing about `Animation:`, `CubeImage:`'s exact draw offset, or
the `AddImage`/background-colour-key mechanism (see `cube-chaos-sprite-art`'s CubeUpgrade section) — these were only
discoverable by decompiling the shipped `Cube Chaos.jar` (this repo already had precedent for this, see
`cube-chaos-mod-setup/references/workshop-publishing.md`'s Workshop-upload reverse-engineering). Concretely:

1. The game ships its own trimmed JRE at `jre/bin/java.exe` (Java 8, **no `javac`/`javap`** — runtime only).
2. Downloaded the CFR decompiler (`org.benf:cfr`, MIT-licensed, single jar, no install) from Maven Central:
   `https://repo1.maven.org/maven2/org/benf/cfr/<version>/cfr-<version>.jar`.
3. Extracted only the specific `.class` files of interest from `Cube Chaos.jar` (`unzip <path.class>`) rather than
   decompiling the whole jar (much faster, avoids a slow whole-jar run) — start from `dw/game/dd/Screens/*.class` for
   UI/rendering questions, `dw/game/dd/Library.class` for anything about how `.c.txt` fields get parsed, `dw/game/dd/
   Cube.class`/`Perk.class` for per-object behaviour, `dw/game/dd/PnGReader.class` for sprite loading/drawing, and
   `dw/game/dd/BasicClasses/Animation/*.class` for anything animation-related.
4. Ran `jre/bin/java.exe -jar cfr.jar <extracted.class> --extraclasspath "Cube Chaos.jar" > out.java` per class.
5. **Grep the real `.c.txt` files for actual usages of whatever keyword the decompile turns up** (e.g. `grep -rn
   "Animation:" GameData`) — this both confirms the grammar against ground truth and supplies real example values
   for every parameter, which is far more useful than the bare Java parsing logic alone.
6. Clean up: delete extracted `.class` files and decompiled `.java` output from the game's install root when done —
   they're research scratch, not part of any mod, and don't belong under version control (this repo's `.gitignore`
   is an allowlist, so they won't show up in `git status` either way, but tidy up the actual filesystem regardless).

This same method is the way to resolve any future "the modding docs don't cover X but the base game clearly does it"
question — cheaper and far more reliable than guessing from observed in-game behaviour alone.
