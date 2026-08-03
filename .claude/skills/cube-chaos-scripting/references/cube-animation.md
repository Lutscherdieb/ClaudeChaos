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
first**. For what goes *inside* each tile (full-frame renditions, the background colour key, the magenta guide
ring), see `cube-chaos-sprite-art/SKILL.md`'s "Animated CUBE icons" section — this file owns the DSL grammar and
timing, that one owns the pixels.

**The grid does not need to be square — a flat single-row sheet works and is the simpler choice for a dedicated
animation file.** Confirmed from `ColourGrid.SplitSpriteGrid` itself (decompiled `dw/game/dd/BasicClasses/
ColourGrid.class`, `ColourGrid.java:363-369` in the 2026-07-30 re-decompile):
```java
public ColourGrid SplitSpriteGrid(int SpriteWidth, int SpriteDepth, int WhichOne, int Border) {
    int PerWidth = this.Width / (SpriteWidth += Border * 2);   // columns = image pixel width / 17, period
    int Row = WhichOne / PerWidth;
    int Column = WhichOne - Row * PerWidth;
    return this.CutoutAt(Column * SpriteWidth, Row * (SpriteDepth += Border * 2), SpriteWidth, SpriteDepth).takeOffBorders(Border);
}
```
Column count is derived purely from the PNG's own total pixel width divided by 17 — there's no dependency on `Amount`
being a perfect square, and no requirement the sheet be roughly square like the `grid_dim = ceil(sqrt(N))` convention
used for the main CUBE/PERK roster sheets (that convention is this repo's own choice for large multi-cube sheets, not
an engine requirement). For a single animation's dedicated file, a **flat 1×`Amount` row** (width `Amount*17`,
height `17`) is simpler to lay out and edit than a square grid, and parses identically: `PerWidth == Amount`, so
`Row` is always `0` and `Column` is the frame index directly. Recommended default for new animation files going
forward. Note also that `CutoutAt` silently zero-fills any read past the image's actual bounds (`if (j+x < Width &&
j2+y < Depth)`, `ColourGrid.java:392`) — an undersized sheet doesn't error, it just yields blank/garbage frames, so
still get the width arithmetic right rather than relying on this to fail loudly.

**For a `TRIGGER` animation, put the cube's own idle/resting art in the LAST frame slot, not index 0 — a `TRIGGER`
settles onto the last array index and stays there, never back onto index 0.** (**Scope matters: this is a `TRIGGER`
rule, not a universal one.** A `CLOCK` never settles anywhere — its frame tracks a cooldown bar that resets every
cycle — so a back-loaded `CLOCK` puts the resting art in **frame 0**, the slot it holds for most of the cycle, and
the *flourish* in the last frames. Getting this backwards inverts the whole animation. See "Picking the TYPE"
below for which frame is on screen when, and `cube-chaos-sprite-art/SKILL.md` for the same scoping note from the
pixel side. `HP` is a third case again: frame 0 is what shows at full HP.) This was wrong in an earlier version of
this doc (fixed 2026-07-30 after a live playtest showed a `TRIGGER`-animated cube sitting permanently 1px off its
resting pose) and is now confirmed
straight from `TriggerAnimation.AutoChangedCheck`/`ClockAnimation.AutoChangedCheck` (both identical in shape,
decompiled `dw/game/dd/BasicClasses/Animation/{Trigger,Clock}Animation.class`):
```java
int index = 0;
while (index < this.Frames.length && Current >= this.Thresholds[index]) {
    Current -= this.Thresholds[index];
    ++index;
}
if (index > 0 && this.LastFrame != index - 1) {
    this.OwnerCG.Changed = true;
    this.LastFrame = index - 1;
}
```
Walk through what this actually does: `LastFrame` only ever gets **written** when `index > 0`. Right when the bound
ability just fired (`Current`/`Ratio` ≈ 0), `index` stays `0`, so `LastFrame` is left completely untouched — it keeps
showing whatever it last settled on. As elapsed time crosses `Thresholds[0]`, `index` becomes `1` and `LastFrame`
jumps to `0` (the first real frame); crossing `Thresholds[1]` moves it to `1`; and so on. Once elapsed exceeds the
sum of **all** thresholds, `index` reaches `Frames.length` (the loop's own bound stops it there), so `LastFrame`
locks onto `Frames.length - 1` — **and stays there indefinitely**, since further elapsed time can't push `index`
past that bound. Net effect for a one-shot `TRIGGER` flourish: the cube sits on frame `N-1` at rest, briefly keeps
showing frame `N-1` for `Thresholds[0]` after firing (a startup delay — keep this small/near-zero), then plays
`0, 1, 2, ..., N-2` in order as elapsed time crosses each subsequent threshold, then locks back onto `N-1` once the
last threshold is crossed. So: **frame `N-1` = permanent idle pose, frames `0..N-2` = the transient flourish**, in
that literal order. (For `CLOCK`, the same mechanics read naturally the other way around — `Ratio` climbing 0→1 as
a cooldown fills means `N-1` = "fully charged/ready" and `0` = "just used", which is usually exactly the desired
reading, so this gotcha mainly bites `TRIGGER`.)

## Where to put an `Animation:` line

Inside the `CUBE:` block, same as `Ability:`/`Text:`. `CLOCK` and `TRIGGER` types bind to `lastAbility` — **the most
recently parsed `Ability:` in that same cube block** — so those two types must come *after* the `Ability:` they're
meant to key off. `HP`/`DOUBLE`/`BOOLEAN`/`TIME` don't bind to an ability and can go anywhere in the block.

**Put the `Animation:` line after the bound ability's own `Text:`, not squeezed between the `Ability:` and its
`Text:` — a `Text:` line does NOT reset `lastAbility`.** Real base-game precedent: `Main/3GeneralCubes.c.txt`'s
`CUBE: Mana_Leech` reads `Ability: AfterThisDealsDamage GenerateXMana DoubleConstant 1` / `Text: After this deals
damage generate 1 \CMANA mana \CN End` / `Animation: Drain TRIGGER 0 EQUAL 4 60`, and the flourish demonstrably
fires off that ability. Keeping ability+text adjacent also keeps the block readable as `cube-chaos-rule-text`
expects (its "rule text is never edited independently" principle).

**Bind straight to a stock COMPOUND attack ability — `EveryXMeleeY`/`EveryXAcidicY` expose a usable `Clock`, no
wrapper ability needed.** Confirmed by real base-game usage at `Main/3GeneralCubes.c.txt:4801-4806`:
```
CUBE: Acidic 40 10 10
Ability: Addon
Ability: EveryXAcidicY 60 1
Animation: Acid CLOCK 0 EQUAL 2
```
and re-confirmed 2026-08-02 by six new own-mod animations (Unholy `Imp`/`Plague_Imp`/`Molten_Brimstone`/
`Two_Headed_Demon`, General `Rocket_Silo`, Unholy `Hell_Portal`) all parsing and counting clean. Tick conversion for
picking thresholds: **60 ticks = 1 second** (base game's own `Grinding_Gun`, `EveryXTimes TimeConstant 60`, is
described in its own `Text:` as "Every second").

A cube can have **multiple** `Animation:` lines; they apply in sequence, each one further modifying the previous
one's result (`AnimatedCG.Recalculate`: `Result = A1.Affect(A2.Affect(Result))`-style fold) — e.g. one `HP`-driven
damage-crumble animation plus one `TIME`-driven idle shimmer can coexist on the same cube.

**When one cube carries two animations, draw them over strictly disjoint pixel regions, and state the column/row
split in a comment in whatever script generates the frames.** With the universal `EffectType 0`
(`OverrideWithBIfEqualC(Frame, OwnerCG.Base)`, see below), a pixel is only rewritten while it still matches the
cube's original art — so whichever animation the fold reaches first wins any contested pixel, and the other one's
write is **silently skipped** (its own frame still equals base there, so nothing signals the conflict). Disjoint
regions make the fold order irrelevant. Real case, 2026-08-02: Unholy's `Two_Headed_Demon` has one `CLOCK` bite per
head, tied to its two separate `EveryXMeleeY` abilities (`42 2` and `120 3`), with the left head confined to
columns x1–x5 and the right to x9–x13 — columns x6–x8 are left untouched by both.

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
  a short one-shot flourish that plays right after the ability triggers, **then locks onto the LAST frame index**
  (see the frame-ordering section above — it is not frame 0). `EQUAL`'s extra `<Total>` divides evenly across
  `<Amount>` frames (integer division — pick a `Total` that's a clean multiple of `Amount` or the last segment
  silently absorbs the remainder), which gives every phase (startup delay + each flourish frame) equal dwell time;
  use the explicit `<t0>...<t(n-1)>` form instead when you want a near-instant startup (`t0` small) followed by a
  snappier flourish and a longer settle. Real example: `Animation: Shoot CLOCK 0 EQUAL 4` style entries tied to
  attack abilities, and `Animation: Gift TRIGGER 0 EQUAL 4 20`.
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

## Picking the TYPE: `CLOCK` for a periodic ability, `TRIGGER` only for a reactive one

**Default to `CLOCK` whenever the animation is tied to an `EveryX...`/`EverySecond`/`EveryMinute`-style ability, and
reach for `TRIGGER` only when it's tied to an `After*` reactive trigger.** Two independent reasons:

1. **Timing.** `CLOCK`'s frame tracks how full the bound ability's cooldown bar is, so **the last frame lands
   exactly on the moment the ability fires** — that is the only way to get "the hatch is already open as the rocket
   launches" or "the portal is already open as the cube spawns". `TRIGGER` plays its flourish *after* the fact, so
   anything that must be in position *at* the firing instant is wrong with it.
2. **The base game's own split**, counted 2026-08-02 across `Main/`+`Characters/`+`Base_Core/`: 166 `CLOCK`, 53
   `TRIGGER`, 46 `HP`, 31 `DOUBLE`, 19 `TIME`, 9 `BOOLEAN`. Every `TRIGGER` binds to a reactive trigger
   (`Mana_Leech`'s `AfterThisDealsDamage`, `Cooling_Aggregate`'s `AfterACubeTakesDamage`); every periodic ability's
   animation is `CLOCK`.

**A `TRIGGER` bound to a heavily-conditional reactive ability fires only when that ability's action actually
executes — not on every evaluation of its trigger.** So it is safe to bind one to an `Ability:` whose trigger fires
constantly but whose guards rarely pass; you do **not** need to split the guarded branch into its own ability to get
a clean animation. `Ability.LastActionTime` (what `TriggerAnimation` divides by 16) is written on execution, not on
trigger evaluation. **User-confirmed in play, 2026-08-03**: Crusader's `Cardinal` carries
`Animation: Lift TRIGGER 0 4 1 10 10 10` on its pick-up ability — a `BeforeThisMoves` chain gated behind a sideways-
direction test, an "am I carrying nothing" test, and an ally-in-the-way test. `BeforeThisMoves` fires on *every*
move the Cardinal makes, yet the hoist flourish plays only on an actual pick-up ("correctly only plays on picking up
something"), never on ordinary movement. This had been flagged as an unknown worth watching for; it is now settled,
so don't re-derive it or pre-emptively restructure an ability around it.

**Write the threshold list back-loaded and starting with a literal `0`** — e.g. `Animation: Launch CLOCK 0 4 0 0.88
0.04 0.04`, matching the base game's own `Thump CLOCK 0 4 0 0.85 0.05 0.05`. That gives a long rest on frame 0 and
a short flourish that culminates as the ability fires, instead of `EQUAL <Amount>`'s uniform crawl (fine for a fast
1-second attack, unwatchable on a 45-second cooldown).

### Why the leading `0`, and which frame is on screen when

`ClockAnimation.AutoChangedCheck` walks `Ratio = Clock.Timer / DetermineClockThreshold()` (0..1) through the
threshold list cumulatively, exactly like `TriggerAnimation` does with elapsed ticks (loop quoted in the
frame-ordering section above). Reading off that loop, frame `i` is on screen while
`sum(t[0..i]) <= Ratio < sum(t[0..i+1])`, so:

- **frame `i`'s share of the cycle is `t[i+1]`**, not `t[i]` — the list is offset by one;
- while `Ratio < t[0]` the loop leaves `index == 0`, so `LastFrame` is never written and the cube keeps showing
  **frame `Amount-1`, carried over from the end of the previous cycle**. That leading `t[0]` slice belongs to the
  *last* frame, which is exactly why every real back-loaded list opens with `0` — to opt out of it;
- the thresholds need not sum to `1.0` (that real `Thump` example sums to `0.95`); the last frame absorbs the
  remainder. Net: **`share[Amount-1] = (1 - sum(t)) + t[0]`**.

This also explains `EQUAL <Amount>` (all thresholds `1/Amount`) coming out as `Amount` genuinely equal slices with
the sequence phase-shifted by one — `Amount-1, 0, 1, ... Amount-2` — rather than the last frame never showing.
`render_preview_cards.py`'s `clock_frame_shares()` is this formula, and is the executable copy of it.

### Verify it actually took: `Log.txt` counts CUBES, not `Animation:` lines

After a test launch, `Log.txt` prints `-N Animated Cubes`. **`N` is the number of cubes carrying at least one
animation, not the number of `Animation:` lines** — so check it against distinct cubes, not a raw `grep -c`:

```bash
grep -rh "^Animation:" GameData/<each package in Loading_Order.txt>/ | wc -l    # declared lines
grep -rl "^Animation:" ...                                                     # (minus any cube with 2+ lines)
```
Worked example, 2026-08-02: 371 declared lines across the loaded packages, of which `Two_Headed_Demon` accounts for
two on one cube → 370 distinct cubes, and the log read exactly `-370 Animated Cubes`. That match is what proves
every new line was accepted — a typo'd type or a mis-slotted line drops the count without printing any error.
A missing frame **file** does log (`Failed to find animation file: ...`), but is likewise non-fatal.

## Which type to pick, knowing how each one previews in a README (added 2026-08-01)

`cube-chaos-sprite-art/scripts/render_preview_cards.py` generates a companion `.gif` for a new animated cube's own
README preview card (see that skill's "Rendering README preview cards" section) — and how faithfully it can do that
depends entirely on which `Animation:` TYPE gets picked, not just on drawing good frames. Worth knowing **before**
authoring a new animated cube, not discovering after:

- **`TRIGGER` previews accurately.** Its frame is a self-contained countdown (ticks since `lastAbility` last fired) —
  fully computable with zero knowledge of the rest of the game, so the README gif is a real, correctly-timed playback
  of the actual flourish, captioned with the real trigger condition (e.g. DJ's `Speaker` → `Speaker_Beat.gif`,
  captioned `On Cube Creation`).
- **`DOUBLE` previews honestly, but not accurately — there is no deterministic playback to compute**, because its
  frame comes from evaluating a live production (current hp, an ability's stacking count, a custom per-cube variable
  built up over a whole `EveryTick` chain...) that has no value outside an actual running battle. The default preview
  is every frame in raw sheet order, at a flat pace, with **no claim about when each one appears** — correct as far
  as it goes ("here are the poses this animation has"), but it can't show a `DOUBLE` cube's real behavior the way a
  `TRIGGER` cube's gif can. A hand-picked multi-state override IS possible when a sheet's frames clearly split into
  a few recognizable, real conditions (real case: the Steam Workshop "Dinosaurs!" mod's `Red_Eye` — blink cycle
  visibly changes between above/below 50% hp, so its preview got two separate captioned gifs instead of one raw
  cycle; see `ThirdParty/Dinosaurs/render_dinosaurs_preview.py`'s `DOUBLE_ANIMATION_STATES` for the worked pattern),
  but that override has to be hand-derived by tracing the cube's own state-computing ability chain — there's no way
  to detect it mechanically from the `Animation:` line alone.
- **`CLOCK` previews in the right SHAPE but not at real speed** (`build_clock_gif()`, added 2026-08-02). Frame
  order and each frame's *relative* dwell come straight from the real threshold list via `clock_frame_shares()`
  above, so the flourish reads correctly — but a `CLOCK`'s thresholds are fractions of a cycle, and the cycle's
  real wall-clock length lives in the bound `Ability:` chain (45 seconds for `Rocket_Silo`, 0.7 for one of
  `Two_Headed_Demon`'s bites), which isn't reliably derivable from arbitrary DSL. So the whole cycle is compressed
  to a fixed `CLOCK_CYCLE_MS`, with a floor per frame so a 4%-share flourish frame doesn't flicker past and a cap on
  the long rest frame. **The cadence therefore belongs in the README caption, not the gif** — hence
  `sync_readme_preview.py`'s `ANIMATION_CAPTIONS` entries naming it outright ("Rocket Launch (every 45s)").
- **`HP`/`BOOLEAN`/`TIME` have no preview support at all yet** (`render_preview_cards.py`'s own documented gap) — a
  cube using one of these will render its static card with no animation gif until someone adds that playback logic.

**Practical takeaway when designing a new cube for this repo's own mods:** pick the type by engine semantics first
(the section above — `CLOCK` for a periodic ability, `TRIGGER` for a reactive one); preview fidelity is a
tiebreaker, not a reason to pick the wrong type. `TRIGGER` previews at true speed for free. `CLOCK` previews in the
correct shape and just needs its cadence stated in the caption. Reach for `DOUBLE` when the animation is genuinely
about reflecting live state (an idle pose that changes with stacking count, hp, etc) and accept that its README
preview will be a generic pose gallery unless you're willing to hand-write a state-override afterward.

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
