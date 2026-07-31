---
name: cube-chaos-sprite-art
description: Use whenever creating or resizing pixel-art sprite sheets for a Cube Chaos mod (CUBE icons, PERK icons, or CLASSSPECIES synergy portraits) - covers the game's fixed tile-size convention, default colors, and the special combo border used only on class+species synergy perks. Trigger on "sprite sheet", "cube icon", "perk icon", "synergy portrait", "class+species border", or when a GameData/<Mod>/Sprites/*.c.png file needs to be created or fixed.
---

# Cube Chaos sprite sheet conventions

These facts were reverse-engineered empirically (by measuring real game files pixel-by-pixel), not guessed. Trust them over any formula involving `ceil(sqrt(count))` — that coincidentally matches some files but is NOT how the game actually slices sprites.

## Research protocol — this skill first, base game second, write back always

1. **Check this skill first.** Tile sizes, the safe interior zone, the border pattern library and the default colors are already settled below. If it's covered, use it and stop.
2. **If not covered, measure the base game's own sprite sheets** — they are the ground truth for anything visual, and neither `ModdingInfo.txt` nor `ModdingExplanation.txt` documents sprite conventions at all (`Visual:` and `CubeColourShift:` are undocumented there too — see `cube-chaos-scripting`). Sample actual pixels from `GameData/*/Sprites/*.c.png` with a throwaway script rather than eyeballing a screenshot, and confirm a measurement across **several independent files** before treating it as a rule — a single sheet can be an outlier.
3. **Write the finding back into this skill, in the same edit** — the measured numbers, which files you sampled, and how many agreed. A color or offset recorded without its source can't be re-verified.

Two standing constraints while researching: **base-game sprite sheets are read-only** (see `CLAUDE.md`), and **never derive a border by color-matching against a content-bearing reference tile** — generate it from the pattern library below instead.

## Fixed tile sizes (confirmed across many independent real files)

- **CUBE icons: 17×17 px on the sheet, but the engine only ever displays the inner 15×15 — the outer 1px on every side is trimmed at render time.** This reverses an earlier (wrong) conclusion in this same file that CUBE icons "have no border convention at all." Confirmed 2026-07-27 two independent ways: (1) a real user-vs-preview-card comparison — DJ's `Microphone` (untouched for a long time, ruling out a stale-edit explanation) showed visibly less padding in an actual gameplay screenshot than this skill's own preview-card renderer produced from the same tile, which was doing a full untrimmed 17×17 crop; (2) **the base game itself already marks this exact boundary with a drawn guide ring, just a color this repo's own mod sheets had never adopted** — `Base_Core/Sprites/3TokenCubes.c.png` and `Modding_Example/Sprites/GeneralCubes.c.png` both pixel-dump to a full 1px `RGB(255, 0, 110)` ring around all 4 sides of *every* 17×17 tile (not a shared single-pixel boundary between neighbors — each tile has its own complete ring, so two adjacent tiles show 2px of that color touching between their content areas), with real content only ever in the inner 15×15 (tile-local indices 1-15). This is the CUBE-icon equivalent of the PERK magenta guide ring below, just a different color code (`(255,0,110)` not `(255,0,220)`) and a fact this repo's own mod sheets happened to never carry over. See "CUBE icon guide grid" below for the generator recipe — **draw this by default on every CUBE sheet going forward**, existing or new. Tile size itself (17×17 on the sheet) also confirmed via `Main/Sprites/3GeneralCubes.c.png` (714÷17=42), `Characters/Sprites/2TokenCubes.c.png` (306÷17=18) — only the "no border to strip" half of the old claim was wrong.
- **PERK icons (class perks, reward perks, AND class+species synergy perks): 27×27 px.** Confirmed via `Characters/Classes/Sprites/Priest.c.png` (108÷27=4), `Characters/Sprites/Synergies.c.png` (540÷27=20), `Main/Sprites/Perks.c.png` (621÷27=23), `Modding_Example/Sprites/Synergies.c.png` (270÷27=10).

Sheet dimensions = `tile_size * columns` wide by `tile_size * rows` tall. Icons are cropped in the order the `CUBE:`/`PERK:` blocks appear in the txt file (top to bottom, wrapping left-to-right within each row), row-major. Extra unused grid cells are fine and normal (real game files often have far more cells than currently-defined content — that's expected headroom, not a bug).

**The sheet does NOT need to be square — a `ceil(sqrt(count))` square grid is one valid layout, not a requirement.** Corrected 2026-07-29 (`cube-chaos-audit` pass over the Steam Workshop "Dinosaurs!" mod, a well-regarded third-party mod): several of its real, apparently-functional sheets are single-row strips, not square grids — `PerkUpgrades.c.png` (297×27 = 11 columns × 1 row, exactly matching its 11 `IsUpgradeFrom:` perks with zero headroom) and `TokenCubes.c.png` (255×17 = 15×1 for 10 real `TOKEN` cubes). The user independently confirmed seeing single-row strips used this way elsewhere (e.g. one mod's worth of animation frames for a single cube). Row-major slicing only needs a *consistent column count*, which a single row trivially satisfies — square is just the shape you get if you compute `grid_dim = ceil(sqrt(n))` and use it for both axes, not something the engine checks for. Pick whatever rectangle is convenient to author (a square grid, a single row matching file order 1:1, or anything between) — just get the column count right and keep block file-order matching slot order (see the mid-file-insertion warning below, which is unaffected by this correction).

**Adding a new `CUBE:`/`PERK:` block anywhere except the end of the file shifts every later block's slot — even when the grid doesn't need to resize.** Slot assignment is pure file order, so inserting a new block between two existing ones (e.g. "put the new cube right after its thematic sibling" — a reasonable-looking place to put it in the `.txt`) pushes every subsequent block's slot index up by one, while their actual pixel tiles stay exactly where they were. The result isn't a load error — it's every displaced cube/perk silently showing the *previous* one's old art, one slot down the chain, with the last real slot now empty and whatever was drawn into the (assumed-last) new slot showing up on the wrong entry instead. Real incident, this mod (2026-07-25): a new `Hellstorm` `CUBE:` was inserted right after its thematic sibling `Brimstone` (not at the file's end) in `Unholy_Cubes.c.txt`, while its icon was drawn assuming it would be the *last* block (i.e. the last free grid cell) — caught by the user in actual play ("Plague Ritual has the dragon egg image"), confirmed via the preview cards showing `Hellstorm`'s card with `Plague_Ritual`'s real green pentagram and `Blood_Totem`'s card with the freshly-drawn meteor icon. **Recurred a second time, 2026-07-27** — General's `Claim`/`Retreat` `CUBE:` blocks were inserted right before their thematic neighbor `Bomber` in `General_Cubes.c.txt` (done via the `cube-chaos-scripting` skill alone, sprite-art never consulted since the task was framed as pure DSL work), shifting every cube after them by 2 and making `Retreat` display `Bomb`'s art — same failure shape, different session. This is exactly why the "append at the end, always" rule now also lives in `cube-chaos-scripting`'s own "Block formats" section, not just here — the mistake happens at CUBE:/PERK: authoring time, which doesn't always route through this skill. **Fix used: relocate the new block's *text* to the end of the file** (matching the slot its art was already drawn into) rather than relocating five tiles' worth of pixels — cheaper and lower-risk whenever the new content was drawn assuming an append-at-the-end slot. The general rule: **a new `CUBE:`/`PERK:` block's file position must match the grid slot its art is drawn into, always** — either append the block at the end (simplest, matches "next free slot" every time) or, if it must go elsewhere for readability, work out its real resulting slot index first and draw/relocate pixels for every block that shares or comes after that slot.

**An `IsUpgradeFrom:` upgrade perk doesn't *need* a unique sprite — if its dedicated file has no matching `Sprites/*.c.png`, it falls back to visually reusing its base perk's icon in-game.** That fallback is where the base game's own upgrade files land: `Characters/Classes/ZUpgradeClassPerks.c.txt`, `Characters/Species/UpgradeSpeciesPerks.c.txt`, and `Main/UpgradePerks.c.txt` all have zero matching sprite sheets. But **the fallback is not a hard limit — the engine also happily renders a real, unique sprite for an upgrade perk if one is given.** Corrected 2026-07-29 (`cube-chaos-audit` pass over the Steam Workshop "Dinosaurs!" mod): its `PerkUpgrades.c.png` gives all 11 of its `IsUpgradeFrom:` perks real, unique, multi-color (4–9 distinct colors) 27×27 art — not placeholders, and an exact 1:1 tile-to-perk match with zero spare slots. **Adopt this going forward: give a mod's `<ModPrefix>_UpgradePerks.c.txt` its own matching `<ModPrefix>_UpgradePerks.c.png` with real art**, the same as any other perk file, rather than leaving it sprite-less by default. (This is a going-forward preference, not a retrofit — existing upgrade perks in this repo's own mods that currently rely on the reused-base-icon fallback don't need art added retroactively just for this.)

**Regardless of whether the upgrade file ends up with its own sprite sheet, the base game never mixes upgrade perks into the same `.c.txt` file as the regular perks they upgrade — upgrades always live in their own dedicated file.** Confirmed exhaustively: `Characters/Classes/Priest.c.txt`/`Warrior.c.txt`/`Engineer.c.txt` (and every other class file checked) contain **zero** `IsUpgradeFrom:` lines — every one of those classes' upgrades instead lives in the single shared `Characters/Classes/ZUpgradeClassPerks.c.txt`. Same pattern for species and for the general reward-perk pool (`Main/Perks.c.txt`, 389 perks, 0 upgrades, vs. the separate `Main/UpgradePerks.c.txt`). **This file-separation is still the pattern to follow for new mod content, not an edge case** — put every `IsUpgradeFrom:` perk in a `<ModPrefix>_UpgradePerks.c.txt` alongside the regular one, whether or not that file also gets its own sprite sheet. This keeps a mod's regular-perks sheet fitting only real, iconned regular perks, with zero upgrade-shaped gaps to reason about — the upgrade file's own sheet (if any) is sized/sliced independently, on its own file-order count.

**Why the file-separation matters, not just as tidiness:** the alternative — mixing upgrade and regular perks in one file sharing one sheet — technically still works (every `PERK:` block, upgrade or not, consumes a sequential grid slot in file order, and an upgrade's slot is just conventionally left blank if unsprited), but it's a real footgun: get the slot-counting wrong and every regular perk *after* the first upgrade in the file silently lands one-or-more slots off from where the engine actually looks (`WARNING: Perk <name> from package <pkg> with empty Image`, i.e. a checkerboard/missing-texture in-game, with no load-time error to flag it). This is exactly what happened to this mod set before the fix: both the DJ mod's `Feedback`/`Final_Countdown`/`Grand_Finale` (swapped icons from a slot-counting mistake) and, independently, the General mod's `Arms_Race_Mk3` (whose preview card silently rendered as a *blank* icon — a chained-upgrade lookup bug in `render_preview_cards.py` resolving only one `IsUpgradeFrom:` hop instead of walking the full chain back to a real perk) trace back to upgrades sharing a sheet with regular perks. Both mods were restructured to split upgrades into their own `<ModPrefix>_UpgradePerks.c.txt` (`DJ_UpgradePerks.c.txt`, `General_UpgradePerks.c.txt`) specifically to eliminate this whole class of bug rather than keep managing it carefully — do the same for any new mod from the start.

**If a `.c.txt` file's `PERK:` blocks are a mix of regular and upgrade perks anyway** (e.g. auditing/fixing an existing file you don't want to restructure right now), the old careful-counting rule still applies as a fallback: **count every `PERK:` block in file order, including `IsUpgradeFrom:` ones**, when sizing the sheet or picking a slot index — don't filter them out, and don't skip reserving their slot just because nothing will ever be drawn there.

**The sprite file must be named identically to its `.txt` file** (e.g. `Cubes.c.txt` → `Sprites/Cubes.c.png`). Two different mod folders must NOT reuse the same txt/png basename as any already-loaded package (e.g. don't create `Perks.c.txt` if `Main/Perks.c.txt` already exists) — the engine appears to key sprite sheets by filename, and a collision silently mis-maps your icons into the colliding file's sheet instead of erroring.

## Default background color

`RGB(0, 148, 255)` — confirmed as the overwhelmingly most-common pixel color in every real cube and perk sheet checked. Use this exact value for new sprite sheets, not an approximation.

## CUBE icon guide grid — draw it by default now, same idea as the PERK magenta ring

Every CUBE icon tile gets a 1px `RGB(255, 0, 110)` ring around all 4 sides of its own 17×17 box (row 0, row 16, col 0, col 16), leaving real content in the inner 15×15 (tile-local indices 1-15) — this is the base game's own real convention (see the CUBE icon tile-size entry above for the two files that confirm it), never previously adopted by this repo's own mod sheets, and now the default going forward for every CUBE sheet, existing or new. Two concrete things this buys:
- Makes the engine's invisible 1px trim visually explicit while editing — an artist can see directly in the image, tile by tile, exactly where content will and won't render, instead of discovering the boundary via a screenshot-vs-preview comparison after the fact.
- Applied as the LAST step (same ordering as the PERK magenta ring), it naturally overwrites whatever content currently sits in that outer ring — which is fine, since that content was already invisible in-game. Nothing real is lost; the guide just makes the already-true boundary visible.

Recipe (pure code, no reference-file extraction needed — same "generate, don't color-match" principle as the PERK pattern library below):
```python
CUBE_GUIDE = (255, 0, 110)
T_CUBE = 17

def draw_cube_guide_ring(sheet, tile_index, cols):
    row, col = divmod(tile_index, cols)
    ox, oy = col * T_CUBE, row * T_CUBE
    px = sheet.load()
    for x in range(T_CUBE):
        px[ox + x, oy] = CUBE_GUIDE                # top row
        px[ox + x, oy + T_CUBE - 1] = CUBE_GUIDE   # bottom row
    for y in range(T_CUBE):
        px[ox, oy + y] = CUBE_GUIDE                # left col
        px[ox + T_CUBE - 1, oy + y] = CUBE_GUIDE   # right col
```
Apply once per tile, for **every** grid cell in the sheet (not just currently-defined cubes) — matches the real files' own convention of guiding every cell including unused headroom, so a sheet never has an inconsistent mix of guided and unguided tiles. `render_preview_cards.py`'s `build_cubes()` already crops this ring off before upscaling (`strip_guide=True`, fixed 2026-07-27) — that fix makes preview cards correct even without the ring drawn; the ring itself is what makes the boundary obvious to a human editing the raw sheet directly, the two are complementary, not redundant.

## Animated CUBE icons: a separate per-animation sprite sheet, not part of the main sheet

A `CUBE:` can have one or more `Animation:` lines (an undocumented but real, extensively-used DSL keyword — full
grammar in `cube-chaos-scripting/references/cube-animation.md`, `PERK:` has no equivalent). Each animation's frames
live in their own file, **not** the cube's main `<ModPrefix>_Cubes.c.png` sheet: `Sprites/Animations/<CubeName>_
<AnimationName>.png`, sliced with the exact same 17px-stride/15px-content/1px-trim convention as a normal CUBE icon,
one tile per frame in row-major order. Confirmed via `PnGReader.FindCGForCube` (see the cube-animation reference for
the full decompile writeup).

## Ground unit CUBE icons: draw the silhouette flush to the tile's bottom row, no gap

A non-flying/non-hovering cube's art must touch the very last pixel row of its 17×17 tile (row 16), with zero background gap underneath. Leaving even a 1px gap reads as the unit visibly hovering above the ground once placed on the board — caught by the user on the General mod's `Bunker` tile, which had its silhouette sitting 1px above the tile's bottom edge and looked wrong in actual play specifically because `Bunker` has no `Flying`/`Hovering` ability (a real flying unit floating slightly isn't a visual bug; a ground unit doing the same reads as an obvious error). This is the same bottom-anchoring principle as the CLASSSPECIES synergy portrait's "safe interior zone" rule above (bottom-pinned, not centered) — it applies here too, just without that section's separate horizontal-centering/safe-zone math since a CUBE icon has no border frame to stay clear of. When drawing or fixing a ground-unit icon, always check the silhouette's lowest non-background pixel lands on the tile's actual last row before calling it done.

**Default rule, not an ironclad one: a CUBE icon is a whole body, not a bust/portrait, unless the user asks for a bust.** A `CUBE:` is a unit that moves around the board in play, so its icon defaults to legs/a full silhouette reaching the bottom row — a head-and-shoulders portrait (the norm for a `PERK:` icon, which is static UI chrome) reads as visibly wrong once that same tile is actually walking across tiles in a real match, *if nothing else was requested*. Real incident, the Cubehammer40k mod: given a user-supplied reference image that happened to be a forward-facing bust (head + shoulder pauldrons, no legs), an early pass copied that composition directly onto 10 Space Marine `CUBE:` icons; the user hadn't asked for a bust specifically, just "make it look more like this image," so the full-body convention should have taken precedence and the reference used for style/color/detail cues only (helmet visor slit, chest crest, armor color) layered onto a full standing figure. Corrected accordingly. **This is the default to reach for absent other direction — if the user explicitly wants bust-style CUBE icons (or any other departure from flush-bottom full bodies), that's their call to make and should be followed, not overridden by this convention.**

## Dragon-egg CUBE icon: fixed 7×7 rounded-diamond mask, not a tall oval

Every base-game `<Theme>_Dragon_Egg` cube (`Characters/Sprites/2TokenCubes.c.png`) shares **one identical silhouette mask**, only the fill colors differ — confirmed byte-identical across `Icy_Dragon_Egg`, `Devouring_Dragon_Egg`, and `Holy_Dragon_Egg` (pixel-dumped independently, 3-for-3 agreement). It is **7 rows tall**, bottom-flush against the tile's last usable row, horizontally centered on the tile's middle column, with a per-row width sequence of **3, 5, 5, 7, 7, 7, 3** (a rounded diamond/hexagon, not an ellipse) — i.e. roughly as wide as it is tall, clearly compact and round rather than elongated. Concretely, on a 17×17 tile with the shape's bottom row on tile-row 16 and center on tile-col 8:

```
row10 (w3, cols7-9):   ...XXX...
row11 (w5, cols6-10):  ..XXXXX..
row12 (w5, cols6-10):  ..XXXXX..
row13 (w7, cols5-11):  .XXXXXXX.
row14 (w7, cols5-11):  .XXXXXXX.
row15 (w7, cols5-11):  .XXXXXXX.
row16 (w3, cols7-9):   ...XXX...
```

**This repo's own three dragon-egg cubes (`Hell_Dragon_Egg`/`War_Dragon_Egg`/`Bass_Dragon_Egg`, one per mod) originally shipped a 9-wide × 15-tall elongated-oval mask instead** (width sequence 3,5,7,7,9,9,9,9,9,9,9,7,7,5,3, spanning nearly the tile's full height) — visibly "too oval" compared to the base game's compact egg, caught by the user comparing side-by-side (2026-07-25). Fixed by redrawing all three to the mask above (rows 10-16, cols 4-12), keeping each mod's existing 4-color outline/base/highlight/accent palette unchanged — only the shape moved, not the colors. If a mod ever adds a new dragon-egg cube (see `cube-chaos-orchestrator`'s `content-dragon-line` workflow), reuse this exact mask rather than freehanding a new egg silhouette.

**The Baby and Adult stages have no equivalent shared mask — checked and ruled out (2026-07-25).** Bounding-boxed all 21 real `Baby_<Theme>_Dragon`/`<Theme>_Dragon` pairs in `2TokenCubes.c.png` (Holy, Anger, Magic, Iron, Explosive, Invasive, Stone, Shadow, Elemental, Plant, Crystal, Chaos, Temporal, Undead, Devouring, Icy, Moil, Programmed, Fungus, Robot, Ancient): widths, heights, and color counts vary widely and unsystematically (baby width 7-15px/height 6-15px/2-9 colors; adult width 11-15px/height 12-15px/1-50 colors) — each theme's baby/adult is genuinely unique freeform creature art, not a reused silhouette. The egg is the one stage that's a shared generic-object mask; babies and adults are meant to look like *that theme's* distinct creature. The only soft convention observed (not a hard rule): most are bottom-flush at tile row 15, matching the general ground-unit convention above — the two exceptions (`Icy`'s baby and adult, maxy 11/13) are drawn visibly hovering, consistent with `Icy_Dragon`/`Baby_Icy_Dragon` both having `Flying`. This repo's own three babies/adults already sit inside that same envelope (width 12-15px, height 15px, bottom-flush) — no shape fix needed for them, unlike the egg.

**Corollary, learned the hard way (2026-07-25): don't build a mod's Baby/Adult dragon trio by palette-remapping one shared silhouette across mods either.** This repo's original DJ/General/Unholy babies and adults were built as one silhouette with three different palettes applied (see "Themed variant of an existing cube" above for when palette-remapping *is* the right call — reskinning one cube within a mod) — confirmed byte-identical bounding boxes and per-color pixel counts across all three mods' babies, and again across all three adults. The user immediately flagged this as "these look too sameish" on sight. **A Dragon evolution line's Baby/Adult art must be genuinely unique per mod, matching that mod's own theme** — the same rule the base game already follows (previous paragraph), just easy to skip when three mods are built in the same session and a working silhouette is sitting right there to reuse. Concretely, this repo's fix (round 2 of that session) dropped the shared "front-facing creature with big spread wings + dangling tail" template entirely and gave each mod its own body plan grounded in its actual theme: DJ's `Bass_Dragon` reads as a subwoofer/amp/guitar beast (concentric-ring speaker-cone face, boxy amp-cabinet torso, guitar-neck tail with fret ticks, small sound-wave arcs floating off both sides — plus, once told the adult's `Ability:` chain spawns a `Note` cube directly above it, a small ripple mark placed above the head specifically to visually cue *where* the spawn happens, added identically to the baby since its own `Ability:` spawns the same way), General's `War_Dragon` reads as a heavily-armed flying mecha-jet (nose cone, swept delta wings, no legs since `Ability: Flying` means it's never grounded, a small rocket shape visibly dropping from underneath to match its actual `CreateCubeOnPosition CubeConstant Rocket` ability), and Unholy's `Hell_Dragon` reads as a demonic red lizard fire-dragon (curved horns, bat wings, flame-tipped tail — deliberately in the Pokémon Charmeleon→Charizard body-plan family per the user's own reference). **Tie the silhouette to the cube's actual `Ability:` chain, not just its name/color** — the DJ and General examples above only happened because the abilities were checked first; a name-only pass would have missed both.

**Practical build technique: construct the main silhouette as one contiguous blob, run the edge-outline pass, THEN layer small decorative extras on top.** A naive "any base-colored pixel touching background becomes the outline color" auto-outliner (see the edge-outline technique under "Color composition" below) is correct for a solid body but silently destroys small *isolated* decorative shapes — a 2-3px wing tip, a floating sound-wave tick, a flame wisp — because every pixel of a small disconnected shape touches background on most/all sides, so the whole shape gets swallowed into flat outline color instead of showing its intended base/highlight/accent colors. Real incident from the Hell_Dragon/Bass_Dragon builds above: the first pass ran the auto-outliner over the wings and sound-wave marks together with the main body, and both rendered as flat dark blobs with no visible color detail (caught by re-rendering at high zoom, not obvious at normal preview size). Fixed by splitting each build into two passes: (1) main body pixels only (torso/head/legs, using only the base+highlight colors) → call the auto-outliner → (2) decorative extras (wings, tail, sound-wave arcs, flame tips) painted directly in their final colors *after* that call, never touching the auto-outliner. A decorative shape that's genuinely meant to read as part of the silhouette (e.g. a wing attached at the shoulder) should instead be added to pass (1), drawn *contiguous* with the main body (sharing at least one edge with an already-placed body pixel) so the auto-outliner only rims its true outer boundary instead of swallowing the whole shape — this is what made the Hell_Dragon's bat wings finally read correctly once they were reworked to touch the torso instead of floating 1px away from it.

## Border pattern library — every `PERK:` category has its own fixed border, generate it from scratch

Every 27×27 PERK sheet in the base game (and this mod) is genuinely rendered with a border tied to the perk's category — not just CLASSSPECIES. All of them share one universal outer ring (`RGB(255,0,220)` magenta, row/col 0, the same non-rendered-looking-but-actually-rendered guide color everywhere), then diverge inward. **None of this needs to be re-extracted from a reference file** — every pattern below is fully determined by fixed pixel positions plus at most one or two named colors, so it can be generated purely from code once you know which category you're drawing for. Re-verifying against a real file is still worth doing once per *new* category (see the empirical method at the end of this section), but for the categories already catalogued here, generate directly from the recipes below.

### Universal constants and a shared ring-drawing helper

```python
T = 27                        # perk tile size (17 for CUBE icons -- but crop 1px in on all sides before use, see below)
BG      = (0, 148, 255)       # default background, used everywhere
GUIDE   = (255, 0, 220)       # magenta outer guide ring, row/col 0 of every PERK tile in every category
BLACK   = (0, 0, 0)           # inner ring color for every "clean 3-ring" and "corner-bracket" category below

def ring_positions(k, T):
    """Every (x,y) on the hollow 1px square outline at offset k from the tile edge."""
    lo, hi = k, T-1-k
    for y in range(T):
        for x in range(T):
            if (x in (lo, hi) and lo <= y <= hi) or (y in (lo, hi) and lo <= x <= hi):
                yield (x, y)
```

**Use `ring_positions`, don't reach for the shorter-looking `if x in (k, T-1-k) or y in (k, T-1-k)` shortcut** — that shortcut silently paints past the ring's own corners into whatever offset is *between* it and the tile edge, because it doesn't bound the other axis. It only happens to give the right answer when two rings sit at adjacent offsets with no gap between them (elif-chaining accidentally clips the bad corner pixels for you); it silently paints wrong pixels the moment there's a gap ring in between, like Style 1's "guide, gap, class-color" below. Caught empirically: a first draft of `plain_class_border` used the shortcut and painted 8 wrong corner pixels (e.g. `(2,1)`) purple that should have stayed background — verified byte-for-byte against `DJ_Perks.c.png`'s real DJ tile before and after the fix (8 mismatches → 0).

### Style 1 — plain class/species border (2-ring: guide / gap / class-color)

Used by exactly the one `BelongsTo: CLASS` and one `BelongsTo: SPECIES` perk per class/species (see "Base class/species icon style" below for the icon-fill convention that goes with it). Ring 1 (offset 1) is plain background, not a color — this is what makes it a "2-ring" style relative to the 3-ring styles below.

```python
def plain_class_border(class_color):
    """Returns {(x,y): rgb} for a T x T tile. class_color e.g. (170,0,255) for DJ."""
    px = {}
    for (x,y) in ring_positions(0, T):
        px[(x,y)] = GUIDE
    for (x,y) in ring_positions(2, T):
        px[(x,y)] = class_color
    # offset 1 (the gap ring) and the interior are left as BG (don't write them)
    return px
```
Verified byte-for-byte against the DJ mod's own `DJ_Perks.c.png` DJ tile (192 border positions, 0 mismatches).

### Style 2 — "clean 3-ring" category border (guide / category-color / black)

Confirmed identical structure across `Curses` and 4 other categories, differing only in the ring-1 color — a fixed lookup table, not something to re-derive per category:

| Category (no `BelongsTo:`, or `BelongsTo: <Category>`) | Ring 1 color | Source file |
|---|---|---|
| Curses (plain `PERK:`, no `BelongsTo:` at all) | red `(255,0,0)` | `Characters/Sprites/Curses.c.png` |
| `BelongsTo: Terrain` (Terrain perks — confirmed 2026-07-27 via `Extra_Mechanics/TerrainPerks.c.txt`'s 15 real entries; NOT `TerrainPerk`, a typo previously in this table) | brown `(105,48,0)` | `Extra_Mechanics/Sprites/TerrainPerks.c.png` |
| Consumables (`Main/Consumables.c.txt`) | orange `(255,106,0)` | `Main/Sprites/Consumables.c.png` |
| Golden perks (`Main/GoldenPerks.c.txt`) | yellow `(255,255,0)` | `Main/Sprites/GoldenPerks.c.png` |
| Neutral perks (`BelongsTo: Neutral`) | gray `(128,128,128)` | `Main/Sprites/NeutralPerks.c.png` |

```python
def clean_3ring_border(ring1_color):
    px = {}
    for (x,y) in ring_positions(0, T): px[(x,y)] = GUIDE
    for (x,y) in ring_positions(1, T): px[(x,y)] = ring1_color
    for (x,y) in ring_positions(2, T): px[(x,y)] = BLACK
    return px
```

If this mod ever adds a brand-new category-style perk collection of its own (not `BelongsTo:` an existing base-game category), picking a fresh, not-yet-used ring-1 color from this style and documenting it here (with the actual file it was verified in) keeps this table exhaustive rather than letting undocumented one-offs accumulate.

`clean_3ring_border` was verified byte-for-byte against a real guaranteed-blank cell for all 5 categories above and matched exactly, **except `Consumables`**, which has a tiny 8-pixel cosmetic flourish not produced by the formula: at tile rows 5 and 21 (not otherwise structurally significant), the black ring's positions at `x∈{1,2}`/`x∈{T-3,T-2}` are orange instead of black/orange — small 2px notches breaking the ring rather than a real 4th ring. Purely decorative and safe to skip; only replicate it if visual parity with the exact base-game Consumables sheet matters for a specific icon.

### Style 3 — "corner-bracket" border (guide / mostly-black jagged ring / single-pixel corner accent)

Confirmed identical shape across `Blights`, `Boons`, and `Nightmares` (all three are `Extra_Mechanics` "run-modifier" categories picked at campaign start, as opposed to the mid-run categories that use Style 2 — an observed grouping, not a confirmed engine rule since only these 3 examples exist). Differs from Style 2 in two ways: ring 1 isn't a clean full-perimeter line (it's thick black at the corners tapering to a single 1px line along each edge's middle), and there's a single-pixel accent dot at each of the 4 innermost corners `(1,1)`, `(1,25)`, `(25,1)`, `(25,25)`:

| Category | Corner-accent color |
|---|---|
| `BelongsTo: Blight` | red `(255,0,0)` |
| `BelongsTo: Nightmare` (confirmed 2026-07-27 via `Extra_Mechanics/Nightmares.c.txt`'s 11 real entries) | red `(255,0,0)` |
| `BelongsTo: Boon` | lime-green `(182,255,0)` |

The exact mask (confirmed byte-identical across all 3 real files, `.`=BG, `K`=black, `A`=corner accent, `M`=guide):
```
MMMMMMMMMMMMMMMMMMMMMMMMMMM
MAKKKK..KKKKKKKKKKK..KKKKAM
MKK.....................KKM
MK.......................KM
MK.......................KM
MK.......................KM
M.........................M
M.........................M
MK.......................KM
MK.......................KM
MK.......................KM
MK.......................KM
MK.......................KM
MK.......................KM
MK.......................KM
MK.......................KM
MK.......................KM
MK.......................KM
MK.......................KM
M.........................M
M.........................M
MK.......................KM
MK.......................KM
MK.......................KM
MKK.....................KKM
MAKKKK..KKKKKKKKKKK..KKKKAM
MMMMMMMMMMMMMMMMMMMMMMMMMMM
```
```python
CORNER_BRACKET_MASK = """\
MAKKKK..KKKKKKKKKKK..KKKKAM
MKK.....................KKM
MK.......................KM
MK.......................KM
MK.......................KM
M.........................M
M.........................M
MK.......................KM
MK.......................KM
MK.......................KM
MK.......................KM
MK.......................KM
MK.......................KM
MK.......................KM
MK.......................KM
MK.......................KM
MK.......................KM
MK.......................KM
M.........................M
M.........................M
MK.......................KM
MK.......................KM
MK.......................KM
MKK.....................KKM
MAKKKK..KKKKKKKKKKK..KKKKAM"""  # 25 rows; row 0 (all-M) and row 26 (all-M) added separately below

def corner_bracket_border(accent_color):
    px = {}
    for x in range(T):
        px[(x,0)] = GUIDE
        px[(x,T-1)] = GUIDE
    for y in range(T):
        px[(0,y)] = GUIDE
        px[(T-1,y)] = GUIDE
    for dy, row in enumerate(CORNER_BRACKET_MASK.split("\n")):
        y = dy + 1
        for dx, ch in enumerate(row):
            if ch == 'K':
                px[(dx,y)] = BLACK
            elif ch == 'A':
                px[(dx,y)] = accent_color
            # '.' and 'M' positions already covered by the guide-ring loop above / are BG
    return px
```

### Style 4 — CLASSSPECIES fancy frame (jagged/circuit-bracket, magenta only)

Already covered in detail below ("Repurposing the CLASSSPECIES fancy border" and "How to extract and apply the fancy border") — that mask is reproduced as literal data further down this file so it never needs re-extracting from a reference PNG either. **Confirmed the DJ mod's own `DJ_Synergies.c.png` uses this exact stock mask with no DJ-specific modification** — don't invent a "DJ-flavored" variant of it, just apply the standard recipe.

### No confirmed border style (don't force one)

`Main/Sprites/CubeUpgrades.c.png` does **not** use any of the 4 styles above — its blank/template cells show only the universal magenta guide ring plus a small centered white 17×17 square bracket (rows/cols 5–21, not touching the tile edge at all), unrelated to any of the nested-ring conventions. Since cube-upgrade perks (`Main/CubeUpgrades.c.txt`'s `SpecialAction:`-based perks) are a fairly different mechanic from the other categories here, treat this as its own unconfirmed one-off rather than assuming it generalizes — don't reuse the Style 1–3 recipes for a genuine `CubeUpgrade`-category perk without re-checking, and don't invent a 5th named style from a single ambiguous data point either.

**A `CubeUpgrade` perk still needs its own dedicated sprite tile — `CubeImage: CubeUpgradeImage` does NOT make it sprite-less.** Corrected 2026-07-28 (an earlier session had concluded the opposite, since that field does dynamically resolve to the *targeted cube's own icon* — but only for the small "Result:" preview box shown after a target cube is picked). The perk's own list entry and its own card header are separate UI elements that read from the normal `<ModPrefix>_CubeUpgrades.c.png` sheet like any other `PERK:` category; skip it and the engine falls back to its default missing-texture checkerboard (caught via Unholy's `Wildcard_Upgrade`, which shipped with no `Unholy_CubeUpgrades.c.png` at all).

**The compositing geometry is now measured exactly, not estimated — decompiled straight from `Cube Chaos.jar` on 2026-07-28** (this repo already has precedent for jar-bytecode reverse-engineering, see `cube-chaos-mod-setup/references/workshop-publishing.md`; method: downloaded the CFR decompiler — `org.benf:cfr` on Maven Central — and ran it against individual extracted `.class` files using the game's own bundled `jre/bin/java.exe`, no full JDK needed). Evidence, all cited by decompiled class/method:

- **PERK icons ALSO get their outer 1px trimmed at load time, exactly like CUBE icons — this corrects the "actually rendered" framing given to the magenta guide ring elsewhere in this file.** `PnGReader.FindCGForPerk` calls `SplitSpriteGrid(25, 25, P.Id, 1)`; `ColourGrid.SplitSpriteGrid` cuts the full 27×27 sheet slot (`SpriteWidth += Border*2` before the cutout) then immediately calls `.takeOffBorders(Border)` on it, physically discarding the outer 1px ring and returning a 25×25 grid as the Perk's real `CG`. (`FindCGForCube` does the identical thing at 15/17 for CUBE icons — `SplitSpriteGrid(15, 15, C.Id, 1)`.) **The magenta guide ring never reaches the renderer for either icon type — it is purely an editing-time aid in the source `.c.png`, full stop, not "non-rendered-looking-but-actually-rendered" as stated earlier in this file for PERK sheets.**
- **`CubeImage: <CUBE production>` parses into a `Perk.CubeSource` field (a lazily-evaluated `CUBE` production); an optional, previously-undocumented `CubeImageXY: <X> <Y>` line (confirmed in `Library`'s field-reading switch, right next to `CubeImage:`) overrides the draw offset — default is `Perk.CubeDrawX = Perk.CubeDrawY = 5` (a literal field initializer, not derived from anything).**
- **`Perk.Draw()` (called for the list entry AND the card header — anywhere a `Perk` renders, not some special "Result:" box) does exactly two draws when `CubeSource != null`:** first `PnG.AddImage(CX, CY, this.CG, Background=true, Scale)` — the perk's own 25×25 trimmed tile, full-size; then `PnG.AddImage(CX + CubeDrawX*Scale, CY + CubeDrawY*Scale, C.CG, Background=false, Scale)` — the resolved cube's own **static** 15×15 trimmed tile (`C.CG`, not the live-animated `C.DrawnCG` — see the `Animation:` writeup in `cube-chaos-scripting` for why that distinction matters), on top, offset by `(5,5)*Scale`.
- **The "transparency" is a hardcoded exact-RGB colour key, not a PNG alpha feature.** `PnGReader.AddImage`/`AddSafeImage`/`ShiftImage` all special-case any pixel whose packed RGB equals `38143` (`= 0*65536 + 148*256 + 255`, i.e. exactly `RGB(0,148,255)`, this whole skill's documented "default background colour", stored as the named constant `PnGReader.BackgroundColour`): with `Background=true` that pixel is painted (using the current battle's `World.BaseColour` if in one, else literal blue); with `Background=false` it is **skipped entirely** — nothing drawn, letting whatever was already painted underneath keep showing. Confirmed empirically too: real base-game sheets (`Base_Core/Sprites/3TokenCubes.c.png`, `Main/Sprites/3GeneralCubes.c.png`) store this background colour at full alpha=255 in the PNG itself — the see-through effect is 100% this runtime colour-key check, never the file's own alpha channel. **Never use exact `RGB(0,148,255)` for real foreground art in any sprite** — it isn't just this skill's default-background convention, it's a reserved value the renderer actively detects and special-cases everywhere `AddImage` is used, cube or perk, composited or not.
- **Net geometry: 5 (margin) + 15 (composited cube) + 5 (margin) = 25 — the trimmed Perk interior's full width/height, exactly.** The surviving visible margin around a composited cube is a **precise, guaranteed 5px on all four sides** of the tile's 25×25 usable interior (raw sheet-tile coordinates 1–5 and 21–25, since the outer guide ring at raw 0/26 is trimmed away first) — not the 2px this skill previously guessed, and not a vague "estimate around 5px" either. Design the ring at exactly that width.
- If a mod wants an asymmetric margin (e.g. a thicker top edge), that's what `CubeImageXY:` is for — it directly repositions where the 15×15 cube lands inside the 25×25 interior; the default (5,5) is what every mod perk gets without that line.

Consequences for drawing a `CubeUpgrade` tile:
- **Draw a distinct, saturated ring/border filling exactly the outer 5px of the trimmed interior** (raw tile positions 1–5 and 21–25) — not plain default `BG` blue, or an upgraded cube looks identical to a non-upgraded one (the user's stated goal: distinguish upgrades by their border alone, at a glance, once seen a few times). `Wildcard_Upgrade`'s own tile does this with 5 alternating 1px rings (`ring_positions(1..5, T)` from the border-pattern-library helper above) in Unholy red `(150,20,20)` / gold `(255,196,40)`.
- **Convention (user's call, 2026-07-28): leave the centre 15×15 zone (raw cols/rows 6–20) plain `BG` — draw nothing there at all.** Every real instance of a `CubeUpgrade` perk already has its own cached target cube (the same per-perk-name `SVariable` mechanism seen in `perk-economy.md`'s pricing section), so that centre is overpainted by the composited cube's own icon in every context this tile actually renders in (list row, header) — a glyph drawn there is wasted effort, never actually seen. (`Wildcard_Upgrade`'s tile was first drawn with a centred card+"?" glyph, then simplified down to just the ring once this was pointed out — don't reintroduce centre art on future `CubeUpgrade` tiles.) Only the ring matters; put all the design effort there.
- **Distinguish different `CubeUpgrade` perks in the same mod by FORM as well as colour, not colour alone** — a second upgrade recoloured onto the exact same ring pattern is still easy to confuse at a glance or for a colourblind player. Vary the actual geometry: dashed/segmented rings, corner-brackets-only (see the corner-bracket mask earlier in this file), diagonal hatching, a double-thin-ring-with-a-gap instead of 5 solid bands, etc. — pick a genuinely different shape, not just different `ring_colors`.
- **A ring segment can be made to actually punch through as a gap by painting it exact `RGB(0,148,255)` (the reserved background colour key documented above) instead of a real colour** — since that exact RGB is special-cased by `AddImage` everywhere, a "gap" pixel either renders as plain background fill (wherever this tile is drawn with `Background=true`) or is skipped entirely, revealing whatever's underneath (wherever drawn with `Background=false`) — either way it reads as an intentional gap, not a mistake, without needing to know which draw mode applies in a given UI context. This is the tool for building a genuinely dashed/perforated/segmented ring FORM rather than only ever drawing solid concentric bands.
- If this mod ever gets a second `CubeUpgrade` perk, give it a **different** ring colour pair AND a different ring form/pattern from every existing one in the same mod (same "don't reuse something already claimed" discipline as the class/species colour-picking section above) — the whole point is telling upgrades apart by border alone.
- Real `Main/CubeUpgrades.c.png` entries (a red spiral, gray/brown bell shapes, etc.) are freeform full-tile art rather than a deliberate ring — plausible the base game just accepts the standalone-icon-only tradeoff and never designed for the composited view at all. A deliberate 5px border ring remains the better default for new mod content now that the exact margin is known.

### Verifying/adding a new category empirically (only needed for a category not yet in this table)

Pick the grid's **last cell** (`row = col = grid_dim - 1`), which is guaranteed blank/template-only as long as the matching `.txt` file's real `PERK:`/`CUBE:` count is below `grid_dim²` (true for every base-game category checked — they all have well under 100 entries against a 10×10=100 grid). Don't use "the cell with the highest background fraction" as a blank-cell heuristic — it can still pick a cell with a small amount of real content bleeding in, corrupting the sample (a real mistake made once during this catalog's own research):

```python
from PIL import Image
T = 27
im = Image.open("Category/Sprites/File.c.png").convert("RGB")
w, h = im.size
grid_dim = w // T
px = im.load()
r = c = grid_dim - 1   # guaranteed-blank cell, NOT a "most background" heuristic
for y in range(T):
    print(''.join(str(px[c*T+x, r*T+y]) for x in range(T)))  # eyeball / diff against known styles above
```

## Base class/species icon style (plain single-color square border)

Every plain class perk (`BelongsTo: CLASS`) and species perk (`BelongsTo: SPECIES`) — i.e. NOT a class+species combo — uses a visual convention distinct from the CLASSSPECIES fancy border below: a plain 1px square outline inset 2px from the tile edge (spans rows/cols 2–24 of a 27×27 tile), drawn in one flat color unique to that class/species. The character icon inside is solid-filled (not just outlined) in that *exact same* color, centered in the ~19×19 interior. Confirmed by pixel-dumping real files: Engineer's wrench and its border are both exactly `(64,64,64)`, Priest's cross and border both `(0,254,33)`, Warrior's crosshair and border both `(255,0,0)`, etc. — icon and border always match.

Exception: `No_Class.c.png` / `No_Species.c.png` have NO border square, just a bare black X — that's a special case for the "nothing selected" fallback slot only. Don't copy that look for a real class/species.

**Never extract a reusable border by color-matching against a reference tile's pixels — extract by fixed geometric position instead.** This class/species style's own defining trait (icon fill == border color, confirmed just above) makes color-matching structurally unsafe: sampling "every pixel colored `(170,0,255)`" from e.g. the DJ mod's own base `DJ` class tile grabs the entire purple headphones glyph along with the actual border ring, since the icon was deliberately drawn in the same color as the border. A real incident: this exact mistake stamped DJ's headphones on top of two freshly-drawn reward-perk icons (`Added_Variance`/`Added_Focus` in `DJ/DJ_Perks.c.png`) when their border was "extracted" from the DJ tile by color, corrupting both — caught by the user, not by testing (the game loads such a tile without any warning/error, since color intrusion into the interior is visually wrong but not a parse error). The fix, and the correct approach from the start: build the border mask from `(x, y)` position alone, independent of any tile's actual content — for a 27×27 tile, `x/y == 0 or 25` → magenta outer guide, `x/y == 1 or T-2` → background gap, `x/y == 2 or T-3` → the class/border color, interior (`3..T-4`) left alone. This is exactly what the CLASSSPECIES fancy-frame extraction recipe below already does correctly (samples a *guaranteed-blank* cell specifically to sidestep this trap) — apply the same discipline (position-based, or a verified-blank reference) to the plain single-color border too, not just the fancy one.

Before picking a color for a new class/species, dump the dominant non-background color of every existing class's and species's first tile and avoid reusing one — two unrelated classes sharing a color reads as intentionally related:

```python
from PIL import Image
from collections import Counter
T = 27
BG, GUIDE = (0,148,255), (255,0,220)
im = Image.open(path).convert("RGB").crop((0,0,T,T))
cnt = Counter(im.getdata()); cnt.pop(BG, None); cnt.pop(GUIDE, None)
print(cnt.most_common(3))
```

## Optionally extending the class-color border to non-CLASS reward perk icons

The bordered/color-matched treatment above is engine convention only for the single `BelongsTo: CLASS`/`BelongsTo: SPECIES` perk — ordinary reward perks normally have no border at all (e.g. the base game's own Priest/Warrior reward perks are borderless). Nothing stops a mod from reusing the same 1px-inset colored border on other `BelongsTo: <ClassName>` reward perk icons too, as a deliberate style choice to visually tie a whole family of perks to their class. This is NOT a base-game requirement, just an available technique — if you do this, pull the exact RGB already used for that class's own base perk border/icon (see the color-dump snippet above) rather than inventing a new shade, so the whole family reads as visually related.

**Confirmed this mod set already does this consistently, not just DJ.** Pixel-sampled all 3 existing tiles of `GameData/Unholy/Sprites/Unholy_Species.c.png` (2026-07-26): `Unholy` (the base `BelongsTo: SPECIES` perk), `Hell_Dragon_Egg`, and `Phylactery` (both ordinary `BelongsTo: Unholy` reward perks) all carry the identical ring0/ring1/ring2 structure (`GUIDE`/`BG`/`(150,20,20)`), i.e. `plain_class_border((150,20,20))` applied to every perk in the file, not just the species-defining one. A 4th perk added to the same file (`Mutations`) was built matching this existing pattern rather than left borderless, keeping the whole file visually consistent. Also confirmed in the same session: a genuinely blank/unused sheet cell has zero pixels set at all (not even the magenta guide ring) — `729`/`729` pixels reading as plain background on the guaranteed-blank slot — matching the "Removing a block" section's claim below.

## Repurposing the CLASSSPECIES fancy border as a custom decorative frame at other sizes

The jagged/circuit-bracket border mask (documented above) isn't exclusively tied to its base-game magenta color or 27×27 CLASSSPECIES use — it can be recolored and rescaled to mark cubes/perks with some other custom meaning in your own mod (e.g. a project used it recolored white at 17×17 to visually flag a class's 0-HP utility cubes). Note this is **not** a real base-game "0-HP cube" convention — actual 0-HP base-game cubes (e.g. Cryomancer's `Freezing_Pain`) were checked and have no shared border pattern, just freeform art. Treat this purely as an available decorative asset, not evidence of an engine rule.

**Don't try to rescale the 27×27 mask's full density down to a 17×17 tile** — a first attempt did this via `Image.LANCZOS` + threshold downscaling and it came out much too thick/heavy at the smaller size (roughly 4px of border per side out of 17, eating nearly half the tile). At CUBE-icon scale, hand-draw a much lighter version instead: thin 1px viewfinder-style corner brackets plus a short 1px dash centered on each edge, e.g. (`Y`=border, `X`=clear, 15×15 inset by 1px into the 17×17 tile so row/col 0 and 16 stay plain background):
```
YYXXXXYYYXXXXYY
YXXXXXXXXXXXXXY
XXXXXXXXXXXXXXX
XXXXXXXXXXXXXXX
XXXXXXXXXXXXXXX
XXXXXXXXXXXXXXX
YXXXXXXXXXXXXXY
YXXXXXXXXXXXXXY
YXXXXXXXXXXXXXY
XXXXXXXXXXXXXXX
XXXXXXXXXXXXXXX
XXXXXXXXXXXXXXX
XXXXXXXXXXXXXXX
YXXXXXXXXXXXXXY
YYXXXXYYYXXXXYY
```
This leaves nearly the full tile clear for the icon itself (draw it large, not scaled down for a border that barely intrudes).

## Sprite art effort level

The rule below (never flat single-color icons) is a fixed quality bar, not a preference — it applies regardless of what follows. What *is* a preference is how much iteration/verification effort goes in per icon: check `.claude/preferences.local.md`'s `sprite_effort` setting (default: `full` — see `cube-chaos-repo-setup`). `full` means the complete shaded multi-technique pass described below, verified by reading the rendered PNG back before calling it done. `placeholder` means a quicker single pass the user intends to refine themselves later (per the "Concurrent sprite edits" convention of a user hand-editing sprites live) — still never flat single-color even in placeholder mode, just less iteration/polish per icon.

## Color composition: don't ship flat single-color icons — shade them like the real cubes

**A finished cube/perk icon should use ~3–5 colors, not one flat fill.** User-confirmed direction ("the image must not contain only one color, look at how color composition is in our other mods") after an early Unholy pass shipped flat single-blood-red icons. Verified by sampling real mod tiles (`GameData/General/Sprites/General_Cubes.c.png`, `GameData/DJ/Sprites/DJ_Cubes.c.png`): almost every real cube tile uses **3–5 distinct non-background colors** — e.g. General's tiles run gunmetal `(80,80,85)` + light-olive `(160,181,118)` + olive `(107,142,35)` + dark `(45,45,50)`; DJ's run gray `(70,70,75)` + white highlight `(255,255,255)` + light-gray + near-black outline + a blue-gray. The recurring recipe is **base body color + a darker outline/shadow + a lighter highlight + (often) one small bright accent** — pick shades within the mod's own palette family (see the mod's palette memory) rather than unrelated hues.

Two reliable techniques for turning a single silhouette mask into a shaded multi-color tile (both used for the Unholy `Imp`/`Cultist`, `scratchpad`-style generator):

- **Edge-outline + highlight/accent overlays (for filled silhouettes).** Paint the mask in the base color, but set any mask pixel that has a background 4-neighbour (or sits on the tile edge) to the dark outline color — this gives a clean 1px dark rim for free. Then overlay a separately-drawn highlight sub-mask (a lit region: forehead, shoulder, wing-top) in a lighter shade over *interior* pixels only, a `void` sub-mask (a shadowed recess like a hood interior) in a very dark shade, and a tiny `accent` sub-mask (glowing eyes) in a bright color painted last so it wins. Draw each sub-mask with the same high-res-`LANCZOS`-threshold pipeline; use a **lower threshold (~60) for very small accents** (1px eyes) so they survive the downscale, and if two tiny accents merge into one blob at 17px, post-process the row to keep only the outer pixels and re-void the middle (guarantees two distinct eyes).
- **Layered line widths (for line-art like a sigil/pentagram).** Draw the same path 2–3 times at *decreasing* stroke width, painting widest-first: widest in the dark outline color, a middle width in the base color, a thin core in a bright color — yields a glowing outlined line. Keep the widths genuinely thin at 17px (a black ~2px / red ~1px pair reads as a clean outlined line; go thicker and the strokes blob together and the shape is lost — a real first-attempt failure on the Unholy `Ritual` pentagram, fixed by thinning). **For dense line-art like a pentagram, stop at two tones (dark outline + base) — adding a third bright-core layer over-crowds the interior at 17px and reads worse, not richer** (user-rejected on the Unholy `Ritual`; the clean black-outline+red version was the keeper). The 3-layer glowing-core trick is for sparse/isolated lines, not a busy star-in-circle.

Still verify the result by reading the upscaled PNG back before calling it done (see the workflow below) — shading mistakes are visual, not logged.

**Exception: the single `BelongsTo: CLASS`/`BelongsTo: SPECIES` base perk icon stays flat single-color, matching its border exactly** — this is the one deliberate carve-out from the 3–5 color rule above, and it's not just taste: it's the same icon-fill-equals-border-color convention documented in "Base class/species icon style" below, confirmed against real base-game files (Engineer/Priest/Warrior all flat single-color). Tried shading DJ's own base `DJ` perk (headphones) with a 2-tone highlight during the 2026-07-29 audit — user tried it, then explicitly reverted to the flat single-color original ("the old image looked better") and asked that flat-single-color be kept as the standing convention for this one icon slot specifically. Don't shade this specific tile again without being asked; every other perk/cube icon in the mod still follows the normal 3–5 color rule.

## Themed variant of an existing cube: palette-remap its tile, don't redraw

When a new cube is a deliberate re-skin of an existing one (a "green plague version of the Imp", a "holy version of the Cultist"), the fastest and most consistent route is to **copy the existing tile's pixels and remap its palette** via a small `{old_rgb: new_rgb}` dict, rather than hand-drawing a fresh silhouette. It guarantees the variant reads as the same creature and keeps the shading structure (outline/base/highlight/accent relationships) intact. Real usage, the Unholy mod (`scratchpad`-style generator): `Plague_Imp` = the `Imp` tile with the blood-red family mapped to greens, `Martyr` = the `Cultist` tile mapped to white/gold, `Plague_Ritual` = the `Ritual` pentagram mapped to green. Sample the source tile's palette first (a `Counter` over its `T`×`T` box, minus background) so the map covers every real color, and keep any accent that should stay (e.g. gold eyes) unmapped or mapped to itself. This is the tile-relocation discipline's cousin: read only the source tile's box, write only the target tile's box.

## Getting clean icon silhouettes from vector shapes

A plain `Image.NEAREST` downscale of a hand-drawn high-res vector shape (arcs, rounded rects) tends to produce broken/noisy edges, since NEAREST just samples single points. Better: draw the shape at high resolution (e.g. 240×240) in PIL `ImageDraw` on an `"L"` (grayscale) mask, downscale with `Image.LANCZOS` (smooth antialiasing), then threshold (`mask.point(lambda p: 255 if p > 120 else 0)`) to get a crisp binary silhouette at the target pixel size. This reads far better than NEAREST for organic/curved shapes (arcs, circles) at tiny sizes.

Keep the silhouette solid/blocky like the game's existing icons (Engineer's wrench, Warrior's crosshair) — avoid hollow "donut" interiors unless reference art specifically calls for it. A first attempt at a headphones icon using two concentric circles for "ear cups" read as plain rings, not headphones; switching to solid flared rounded-rectangles (with a small notched bevel cut from the outer edge, matching common pixel-art headphone references) read correctly once verified in-game.

The same high-res-draw + `LANCZOS` downscale + threshold pipeline also works for thick partial-circle arcs (e.g. concentric "sound wave"/echo rings via `ImageDraw.arc(bbox, start, end, fill=255, width=...)`), not just filled shapes — draw at 10-12x scale before downscaling, or the ring thickness aliases away almost entirely at native size. For a multi-color icon that combines an arc motif with a separate glyph (e.g. echo rings next to a musical note, used for the DJ mod's `Echo` perk), build each element as its own separate high-res mask, downscale/threshold each independently, then composite by painting one color's mask first and the other color's mask on top — cleaner and more controllable than trying to draw multiple shapes into one shared mask.

## Reusable idiom: "two things merge into one" icon (fusion/combination abilities)

For any ability that merges/removes two cubes and replaces them with a combination (`Exile` + `CombinationOf2Cubes` — see `cube-chaos-scripting`), a composition that reads clearly even at 27×27: two small solid squares near the top (the two input cubes) connected by a short diagonal dotted line converging down into one larger shape (e.g. a diamond) in the lower-center, representing the merged result. Confirmed readable in-game via the DJ mod's `Forced_Fusion` and `Symphony` perk icons, which reuse this exact composition for two different fusion-flavored abilities. Keep it to 2-3 flat colors (e.g. a neutral shade for the two inputs/border, one accent color for the result) — this is a simple hand-authored pixel grid, not something that benefits from the high-res-and-downscale pipeline above.

## Curse icon border

Curses (plain `PERK:`, no `BelongsTo:` field at all — unlike Blights, which use `BelongsTo: Blight`) use the "clean 3-ring" pattern — see **Style 2** in the "Border pattern library" section near the top of this file (`clean_3ring_border(ring1_color=(255,0,0))`). That section is now the canonical source for this and 4 other categories sharing the same structure; this heading is kept only so a search for "curse border" still lands somewhere useful. Apply the border last, or first — unlike the CLASSSPECIES frame it doesn't intrude into the interior at all, so draw order relative to the curse art doesn't matter, just don't paint over rows/cols 0–2 or 24–26 with your own art.

## Two different magenta patterns — do not confuse them

Both use the same color `RGB(255, 0, 220)`, which is why it's easy to conflate them, but they are functionally opposite:

1. **Thin 1px guideline border** around each cell edge in some placeholder files (e.g. `Modding_Example/Sprites/GeneralCubes.c.png`). This is a non-rendered editing aid only — safe to include or omit, has zero effect in-game. Not required.
2. **The "fancy" class+species combo frame** — a thicker, jagged/circuit-bracket decorative pattern (looks almost like a QR code) that occupies roughly the outer 6px margin of a 27×27 tile. Unlike the guideline, **this one is genuinely rendered in-game**, and appears on every single cell (used or blank) of `Characters/Sprites/Synergies.c.png` and `Modding_Example/Sprites/Synergies.c.png`. This is the border that must be added to any new `PERK: <Class>-<Species>` (`BelongsTo: CLASSSPECIES`) sprite sheet. Do NOT add it to plain class perks, reward perks, or cube icons — only to class+species combo portraits.

### How to apply the fancy border — literal mask, no file access needed

Confirmed byte-identical (308 magenta pixels, exact same positions) across every cell of both `Characters/Sprites/Synergies.c.png` and `Modding_Example/Sprites/Synergies.c.png`, and reused unmodified by the DJ mod's own `DJ_Synergies.c.png` — so this mask is safe to treat as a fixed constant rather than something to re-extract per project:

```
###########################
#....#..#...#.#...#..#....#
#.##.##.##.##.##.##.##.##.#
#.##..#..#.#...#.#..#..##.#
#.....#..#.#.#.#.#..#.....#
###..#################..###
#.####...............####.#
#....#...............#....#
###..#...............#..###
#.####...............####.#
#....#...............#....#
#.####...............####.#
###..#...............#..###
#...##...............##...#
###..#...............#..###
#.####...............####.#
#....#...............#....#
#.####...............####.#
###..#...............#..###
#....#...............#....#
#.####...............####.#
###..#################..###
#.....#..#.#.#.#.#..#.....#
#.##..#..#.#...#.#..#..##.#
#.##.##.##.##.##.##.##.##.#
#....#..#...#.#...#..#....#
###########################
```

```python
from PIL import Image

T = 27
BORDER = (255, 0, 220, 255)
FANCY_FRAME_MASK = """\
###########################
#....#..#...#.#...#..#....#
#.##.##.##.##.##.##.##.##.#
#.##..#..#.#...#.#..#..##.#
#.....#..#.#.#.#.#..#.....#
###..#################..###
#.####...............####.#
#....#...............#....#
###..#...............#..###
#.####...............####.#
#....#...............#....#
#.####...............####.#
###..#...............#..###
#...##...............##...#
###..#...............#..###
#.####...............####.#
#....#...............#....#
#.####...............####.#
###..#...............#..###
#....#...............#....#
#.####...............####.#
###..#################..###
#.....#..#.#.#.#.#..#.....#
#.##..#..#.#...#.#..#..##.#
#.##.##.##.##.##.##.##.##.#
#....#..#...#.#...#..#....#
###########################"""

mask_positions = [(x, y) for y, row in enumerate(FANCY_FRAME_MASK.split("\n"))
                  for x, ch in enumerate(row) if ch == '#']

# Apply to every cell of YOUR sheet
sheet = Image.open("MySynergies.c.png").convert("RGBA")
px = sheet.load()
cols, rows = sheet.width // T, sheet.height // T
for r in range(rows):
    for c in range(cols):
        ox, oy = c*T, r*T
        for (mx, my) in mask_positions:
            px[ox+mx, oy+my] = BORDER
sheet.save("MySynergies.c.png")
```

Apply this as the LAST step, after all character art is drawn — it overwrites whatever was underneath at those pixel positions. (If ever in doubt whether a base-game file has since diverged from this mask, re-verify with the empirical method in "Border pattern library" above — pick the grid's last/guaranteed-blank cell, not a "most background" heuristic.)

### Safe interior zone (where character art must live)

The frame's decorative elements intrude unevenly — corners have thick brackets, and rows 0, 1, 5, 21, 26 (in a 27px tile) have near-full-width decorative bands. The reliably-clear interior is roughly **rows/cols 6–20** (a 15×15 area).

**Placement inside that zone is NOT simple centering — it's bottom-anchored, not vertically centered.** Confirmed by measuring the bounding box of every real character in `Characters/Sprites/Synergies.c.png` (131 combos):

- **Bottom: pinned.** 126/131 characters have their lowest non-background pixel at exactly **row 20** (the rest land at row 19, just shape variance from a rounded silhouette). Characters' feet touch the bottom of the safe zone — there should be **zero gap** between the art and row 20/the ground.
- **Top: free.** `miny` ranges anywhere from 6 to 14 with no consistent value — taller characters just use more of the box, shorter ones leave headroom. Do not stretch/pad short characters to fill the full height.
- **Left/right: centered.** 92% of characters have left-margin and right-margin within ±1px of each other (measuring margin from column 6 and column 20 respectively) — so horizontal placement should still be centered, unlike vertical.

Practical recipe: scale finished character art to fit within 15px width (cols 6–20) and however tall it naturally is (don't force a fixed height), then paste it so its **bottom row lands on tile row 20** and it's **horizontally centered** between cols 6 and 20 — not simply centered on all four sides like a logo. Use `Image.NEAREST` resampling when downscaling to keep pixel-art edges crisp (no blur/anti-aliasing).

A caught-in-the-wild bug from this: an earlier pass on a custom class+species sheet centered the art vertically (equal top/bottom padding), which left a visible 2px gap of "air" under every character's feet compared to every real portrait in the game. Always verify with the bounding-box measurement above (`miny`/`maxy` per tile) rather than eyeballing it — a 1-2px vertical gap is easy to miss visually at 27px but is immediately obvious once scaled up in-game.

## Removing a `PERK:`/`CUBE:` block from the middle of a file: every later tile shifts, the sheet doesn't

Deleting a block isn't a same-slot edit — since slots are assigned by file order (row-major, see above), removing block N shifts every block *after* it up by one slot, but the sprite sheet itself has no equivalent "delete and shift" operation; the pixels stay exactly where they were. Confirmed while removing the DJ mod's `Added_Focus` (slot 5 of 11 in `DJ_Perks.c.txt`) alongside redesigning slot 4 (`Added_Variance` → `Finetuning`, same slot, new art): the five perks after it (`Bass_Drop` slot 6→5, `Sampling` 7→6, `Feedback` 8→7, `Final_Countdown` 9→8, `Bass_Dragon_Egg` 10→9) all needed their existing tiles copied one slot earlier in `DJ_Perks.c.png`, and the now-unused last slot (10) needed clearing to plain background — otherwise every one of those five perks would silently render the *next* perk's old icon in-game (no parse error, since the sheet's dimensions/slot count are still valid, just pointing at the wrong art).

**Practical technique:** snapshot every tile of the sheet into memory first (crop each slot before writing anything), then rebuild the sheet slot-by-slot from that snapshot using the *new* file order — don't try to shift tiles in place on the live file, since a slot's source and destination can overlap partially depending on shift direction/distance. Any slot beyond the new (shorter) content count reverts to plain background — sampled as flat `(0,148,255)` with no border/guide ring across every already-blank cell checked in this sheet, confirming blank cells carry zero border styling, not even the magenta guide ring.

## Editing a single tile in an existing multi-icon sheet: scope the write to that tile only

When fixing/updating one icon in a sheet that already has other finished (or in-progress) icons, restrict every pixel read and write to exactly that tile's own `T`×`T` bounding box (`ox=col*T, oy=row*T` through `ox+T, oy+T`) — including its own border pixels, since the border is part of that tile, not a shared element. Loading the whole sheet into memory is fine (`Image.open(...).load()`), but only ever assign into pixel coordinates inside your target tile's box; never blanket-resave a region wider than the one tile you actually mean to change, and never regenerate/redraw a tile you weren't asked to touch just because it's in the same file. A real incident: a fix pass touched more than the intended tile's own pixels and silently clobbered a user's in-progress hand-drawn art on a different/adjacent tile of the same sheet — treat each tile as an independent atomic unit even though they live in one PNG.

## Recommended workflow for a new icon set

1. Draw each character/icon at a larger, detailed "working" canvas (e.g. 45×45) so fine details are easy to place with integer pixel coordinates.
2. Crop tightly around the design (removing excess background) and resize back up to fill the working canvas — this "zooms in" so the design reads clearly at tiny final sizes.
3. Downscale (NEAREST) to fit the target inner width (15px for the CLASSSPECIES safe zone described above, or fill nearly edge-to-edge for non-CLASSSPECIES sheets that have no frame) — let height follow naturally from the character's proportions rather than forcing a fixed square size.
4. Paste onto a tile pre-filled with the default background color `(0,148,255)`: for CLASSSPECIES sheets, horizontally center between cols 6–20 but pin the bottom row to row 20 (bottom-anchored, not centered — see above); for other sheets, center on all sides as usual.
5. Composite all tiles into one square sheet sized `tile_size * ceil(sqrt(n))`.
6. Only for CLASSSPECIES sheets: overlay the fancy border mask as the final step.
7. **Always verify by actually launching the game** and checking `%APPDATA%/CubeChaos/Log.txt` plus the process's stdout for `WARNING`/`ERROR`/`CANT READ` lines — sprite-sizing and DSL mistakes are frequently silent otherwise (no crash, just visually wrong or a logged warning).

## Directional cube icons: there is no sprite-rotation mechanism — use two sprite variants for a cube that's ever dynamically granted Arcing

There is no DSL-exposed way to rotate a cube's sprite to face its current movement/trajectory direction (confirmed: no `Rotate`/`Facing`/`Orient`-style keyword anywhere in `ModdingInfo.txt`; `RotateClock DIRECTION`/`RotateCounterClock DIRECTION` are POSITION-math helpers, not sprite transforms). The **only** sprite transform that exists is `FlipSprite BOOLEAN` — a vertical mirror, not a rotation — and it's baked into the shared `Arcing` `COMPOUND: ABILITY` itself (`ExtraTrigger: BeforeThisIsDrawn If IsSmaller GetVariableOnCube ARCING Caster DoubleConstant 0 FlipSprite True`), so **any cube granted `Arcing` gets this flip automatically for free**, no extra `CUBE:`/`Ability:` DSL needed from a mod.

**A cube's real motion under `Arcing` is diagonal, not purely vertical** — `Arcing` only ever gets added on top of a cube that's also moving horizontally (via `ProjectileX`/`ChargeEveryX`), so the actual trajectory is "diagonally up-and-forward, then (after the vertical flip) diagonally down-and-forward," a real parabola across the board, not a cube bobbing straight up and down in place. An earlier version of this guidance recommended drawing every `Arcing`-eligible projectile nose-**up** (pure north), reasoning that the automatic vertical flip alone would be enough — that produced a visibly wrong result for the General mod's `Shell` (nose pointing straight up while ascending, straight down while falling, despite visibly translating diagonally across the board the whole time). The nose-up trick only reads correctly for a cube that arcs *in place* with no horizontal component at all — not the normal case.

**And a cube name is frequently shared between an arcing context and a genuinely straight-line context**, so a single sprite — nose-up, nose-diagonal, or otherwise — usually can't be correct everywhere that name appears. Real example: the General mod's `Shell`/`Bomb`/`Rocket` are all created two different ways — straight, with no `Arcing` at all (`Bomb` dropped straight down by `Bomber`; a Paratrooper-fired `Bullet` swapped into a `Shell` by the `Arms_Race` perk, which never touches `Arcing`), *and* arcing (`Artillery` spawns a `Shell` to its own north and grants it `Arcing`, and per `Arms_Race`'s own upgrade chain that Shell may already have become a `Bomb`/`Rocket` by the time `Arcing` lands on it). One sprite can't serve both without looking wrong in at least one context.

### The fix: default nose-east sprite + a second `_Arc` icon-only variant, swapped in via `SetSpriteToCube`

1. **Keep the cube's normal sprite nose-east** (pointing in its travel direction) — this is already correct for `ChargeEveryX`/`FleeEveryX`/`ProjectileX`-only movement, i.e. every context where the cube never gets `Arcing`.
2. **Draw one additional icon per arcing-eligible cube with the nose diagonal, up-and-right at ~45°** (e.g. `Shell_Arc`, `Bomb_Arc`, `Rocket_Arc` for the General mod) — this is the "currently arcing" look. The existing automatic vertical `FlipSprite` then correctly turns "nose up-right while ascending" into "nose down-right while falling," matching a real diagonal parabola, with zero extra DSL needed for the flip itself.
3. **Each `_Arc` variant is its own zero-`Ability:` icon-only `TOKEN` `CUBE:` block** — same shape as the base game's own zero-ability `Note` cube (`CUBE: Note 0 0 0` / `TOKEN` / `End`, no `Ability:` line at all). It's never spawned as a real gameplay unit; it exists purely as a sprite-index source for step 4. This also means it needs no `Text:`, `Visual:`, or `AiPlacementRule:` — those only apply once a cube has an `Ability:`/`IDENT` to describe.
4. **At the exact point in the DSL where `Arcing` is granted, also call `SetSpriteToCube CubeConstant <Name>_Arc`** (`ModdingInfo.txt:376` — a real, documented action that swaps the *current* cube instance's displayed icon to another `CUBE:`'s icon) on the same cube. Since more than one cube name can end up in that spot (e.g. Artillery's own spawn point, after `Arms_Race` may have already swapped it), branch on `CubeHasName` per possible name and nest with `Both`, matching the DSL's usual terminal-action sequencing rules (see `cube-chaos-scripting`'s "Sequencing multiple effects").

**`SetSpriteToCube` had zero prior usage anywhere in this repo or the base game files before this pattern was introduced** — it's real per `ModdingInfo.txt`'s own action list, but treat any new usage as needing an actual runtime check (launch the game, trigger the grant, watch for the visual swap), not just a clean parse, the same as any other undocumented-in-practice engine action. If it turns out not to behave as expected, the documented fallback is the old single-diagonal-sprite approach (nose up-and-right at 45°, relying only on the automatic flip) — imperfect in a cube's straight-line contexts, but at least functional everywhere.

**Rule of thumb when drawing a projectile cube's icon:** if the cube is *never* granted `Arcing` anywhere in the mod, draw it facing east and stop there — no `_Arc` variant needed. If it's *ever* dynamically granted `Arcing` by anything, give it a second nose-diagonal `_Arc` variant and wire `SetSpriteToCube` at the grant site, even if the same cube is also used in a straight-line context elsewhere (especially then — that's exactly the case a single sprite can't cover).

## Rendering README preview cards styled like the game's own tooltips

`scripts/render_preview_cards.py` (in this skill's folder) renders a mod's `CUBE:`/`PERK:` content as PNG "cards" matching the game's actual in-game tooltip look (name, rule text, `VALUE:` line, and the real sprite icon with its category border) — used for this repo's own `README.md` previews under `Preview/`. Re-run it (`python3 .claude/skills/cube-chaos-sprite-art/scripts/render_preview_cards.py`) whenever a mod's content or sprites change and the README images need to stay in sync; it renders every mod registered in its own `render_mod(...)` calls at the bottom of the file.

**Output is one PNG per item, named `<ModPrefix>_<Category>_<ItemName>.png`** (e.g. `DJ_Perks_Echo.png`, `General_Cubes_Shell.png`), not one stacked image per whole category. An earlier version of this script concatenated every card in a category into a single tall image (`<ModPrefix>_<Category>_preview.png`); that made editing a single perk force a regen+diff of the *entire* category's image (every other card's pixels technically "changed" even though only one moved), which doesn't scale as a mod grows. Per-item files mean editing one perk's `Description:`/icon only touches that perk's own file — `git diff`/review stays scoped to what actually changed. `render_mod()` also deletes any stale output in `Preview/` on each run (old `_preview.png` combined images, or files for since-renamed/removed items), so `Preview/` never accumulates orphaned images. A mod's `README.md` embeds each category as a sequence of individual `<img>` tags in the same `.c.txt` file order, rather than one `<img>` per category.

Not every icon-only helper `CUBE:` block needs a README card — e.g. a zero-`Ability:` `_Arc` sprite-swap-target cube (see "Directional cube icons" above) never appears as a real entity anywhere a player sees it, so including it in the cube gallery would just be confusing; skip it from the README's `<img>` list even though `render_preview_cards.py` still (harmlessly) generates a card file for it like any other `CUBE:` block.

Key facts baked into that script, established by reverse-engineering the game's own compiled UI code and byte-diffing real sprite files (not guessed) — reuse these rather than re-deriving them:
- **Font**: `GeneralData/dogicapixel.ttf` is the confirmed real UI font (hardcoded by name in the game's compiled `TextPrinter` class), not a lookalike guess.
- **The outer 1px magenta `(255,0,220)` guide ring is invisible in-game and must be cropped off** before upscaling a PERK icon for a card — but only for style-1/style-2 bordered tiles (plain class border, clean-3-ring categories like Curses/Consumables). Do NOT strip it from CLASSSPECIES synergy tiles (their style-4 fancy frame genuinely renders that outer ring).
- **CUBE icons also need their outer 1px cropped on all sides before upscaling — a separate fact from the PERK guide-ring rule above, and easy to conflate since the fix (`crop((1,1,tile-1,tile-1))`) is identical code.** There's no drawn magenta marker on CUBE tiles (that part of the old "no border" claim holds) — the engine just trims 1px at render time regardless, with no visual indicator in the raw sheet file. Confirmed 2026-07-27 (see the tile-size section above for the evidence); `render_preview_cards.py`'s `build_cubes()` previously called `crop_icon(..., strip_guide=False)`, producing preview cards with visibly more padding around every cube icon than the real game shows. Fixed by passing `strip_guide=True` there too.
- **The engine auto-colors the literal word "mana" blue** in tooltip text (confirmed via a `Player.ManaColour` reference in the compiled UI code) — the only keyword-coloring rule confirmed from data; everything else in `Description:`/`Text:` renders plain white.
- **An `IsUpgradeFrom:` perk reuses its base perk's icon slot** (it has no sprite of its own — see the "upgrade perk needs no unique sprite" note above) — look up the base perk's icon index by name rather than the upgrade's own (blank) slot index.
- **`build_perks()` also reads `<ModPrefix>_UpgradePerks.c.txt` if present** (the dedicated sprite-less upgrade file described above) and generates cards for it too, alongside the regular `<ModPrefix>_Perks.c.txt` cards — no separate registration needed, this happens automatically whenever the "Perks" category runs for a mod. Icon resolution **walks the full `IsUpgradeFrom:` chain**, not just one hop: an upgrade can itself be the base of a further upgrade (e.g. `Grand_Finale`-style `Mk3 → Mk2 → <real base perk>`), and stopping at the first hop lands on another blank upgrade slot instead of real art. A first version of this script did stop at one hop and silently produced a blank-icon preview card for a multi-hop upgrade (`General_Perks_Arms_Race_Mk3.png` rendered solid background blue, no icon) with no error — caught by eye, not by a log warning, since this is a documentation-only script bug, not a game-parse issue.
- **`build_cubes()` falls back to `ModdingInfo.txt`'s own built-in-ability doc strings for any bare `Ability: Name arg1 arg2` line with no custom `Text:` right after it.** A CUBE whose abilities are ALL pre-registered built-ins (e.g. General's `Recruit`: just `ChargeEveryX`/`EveryXMeleeY`/`FreePlacement`/`Climbing`/`Faction_Colours`, zero custom `Ability:` chains) legitimately has zero `Text:` lines per the Text:/Description: requirement — the engine already has that ability's tooltip baked in, so the source file has nothing for this script to read either, and the card previously rendered with an empty ability list (not stale data, a genuine gap in the script, not the mod). The fix: `load_builtin_ability_docs()` parses every `Name TYPE1 TYPE2...     "template with CODE N / STACKING N"` line out of `ModdingInfo.txt` itself (the same doc-string format cited throughout this skill, e.g. `ChargeEveryX TIME     "... Every CODE 1 move forwards "`), and `resolve_builtin_ability_text()` substitutes a bare Ability: line's actual literal arguments into that template (converting `TIME`-typed args from ticks to "N second(s)" phrasing, matching `cube-chaos-rule-text`'s convention, and leaving `STACKING`/other args as literal numbers). `Faction_Colours`-style mod-defined `COMPOUND: ABILITY`s aren't in `ModdingInfo.txt` at all, so this lookup naturally returns nothing for them and they're silently skipped — which is also correct, since a purely cosmetic tag ability shouldn't appear in rule text anyway (see "Never mention purely cosmetic effects" in `cube-chaos-rule-text`). If a future card still shows a suspiciously short/empty ability list, check whether its abilities are all bare built-ins with no custom chain, rather than assuming the sprite/txt data itself is stale.
- **`\C<R> <G> <B>`/`\CN`/`\CMANA`/`\B` markup in a `Text:`/`Description:` now renders as actual on-card color, not stripped to plain text (fixed 2026-07-25 — an earlier version of this script rendered the raw escape codes as literal garbage text, e.g. `\C255 38 0 Strength \CN` showing up character-for-character on the card).** `tokenize_colored()` walks the string tracking color-span state and `\B` (suppress the space before the next token), `wrap_colored_tokens()` word-wraps while preserving each word's color (including the `\N`-segment "- " bullet hang-indent, same as before), and `draw_colored_tokens_line()` draws each wrapped line's words in their resolved colors. A bare "mana" still always renders in the engine's own mana-blue regardless of surrounding span color, matching real engine behavior.
- **`\A <AbilityName> [params]` references (this mod's own keyword idiom, see `cube-chaos-rule-text`) are now resolved inline instead of showing raw `\A Name` text (fixed 2026-07-25).** `load_mod_compound_docs()` scans every `.c.txt` file in the mod for `COMPOUND: ABILITY` blocks, indexing each by name with its own `Text:` template and its parameter types inferred from `Generic*` placeholders in the compound's body (in first-appearance order — `GenericStacking`→`STACKING`, `GenericTime`→`TIME`, everything else→a positional `CODE` slot, mirroring the built-in resolver above). `resolve_inline_abilities()` then expands `\A Name` plus exactly as many trailing whitespace-separated params as that ability declares placeholders for, substituting into its own `Text:` — this must run **before** `humanize()` (which would otherwise turn `Take_Off` into `Take Off` and break the name match) and **before** `tokenize_colored()` (so the resolved ability's own `\C`/`\N`/`\B` markup gets colored too, exactly like the base game's own inline-keyword rendering). An unresolvable name is left as literal `\A Name` text rather than crashing the render, so a genuine gap stays visible on the card instead of failing silently.
- **A species mod's perk file is conventionally named `<ModPrefix>_Species.c.txt`, not `<ModPrefix>_Perks.c.txt`** (e.g. `Unholy_Species.c.txt`) — `perks_source_basename()` checks for `_Perks.c.txt` first, then falls back to `_Species.c.txt`, so the "Perks" category (output filenames, upgrade-file lookup, everything else) works unmodified either way. If a new mod's perk-family content silently doesn't show up in its own preview cards, check which basename its perk file actually uses.
- **A `CUBE`-typed built-in arg (per `ModdingInfo.txt`'s own type annotations, e.g. `Dragon_Egg CUBE`, `GrowingUp CONSTANT CUBE`) is always spelled as two DSL tokens at the call site — a keyword (`CubeConstant`/`HiddenCubeConstant`) followed by the actual cube name — not one (fixed 2026-07-26).** `resolve_builtin_ability_text()` used to `zip()` `doc["types"]` 1:1 against the raw arg tokens, so a `CUBE`-typed slot consumed only the literal word `CubeConstant` and substituted *that* into `CODE N` — e.g. `Ability: Dragon_Egg CubeConstant Baby_Hell_Dragon` rendered "add a CubeConstant to your hand" instead of the dragon's name, and on 2-arg builtins like `GrowingUp` it also silently dropped the actual name token entirely (nothing left to zip it against). Fixed by walking `doc["types"]` with an explicit arg index that advances by 2 tokens for a `CUBE` type instead of 1. Affects every mod using the base game's `Dragon_Egg`/`GrowingUp` compounds.
- **A CUBE's own bare top-level `Ability: Name args` grant of *this mod's own* `COMPOUND: ABILITY` keyword (not a base-game built-in) needs no local `Text:` either — its compound's own `Text:` is the tooltip, exactly like a bare built-in grant — but `build_cubes()` only checked `load_builtin_ability_docs()` for this fallback, never the mod's own `COMPOUND_DOCS` (fixed 2026-07-26).** E.g. Voidling's `True_Void` CUBE grants `Ability: VoidExpansionX 1` and `Ability: VoidNova` directly (both mod-local compounds), and both rendered as nothing at all — not even garbled text, just silently absent — leaving a card that looked complete with only its one built-in ability (`Unmovable`) showing. Fixed by merging `{**load_builtin_ability_docs(), **COMPOUND_DOCS}` before calling `collect_ability_texts()` in `build_cubes()`. This is the same class of gap as the `\A`-reference fix above, just hitting a different call site (a bare grant, not an inline reference inside prose) — if a cube's ability list still looks suspiciously short after checking the built-in-only case above, check whether it grants one of its own mod's compounds directly.
- **CUBE cards use a dedicated `render_cube_card()` layout** (added 2026-07-31, after the user supplied a real gameplay screenshot of Unholy's `Brimstone` tooltip) **but the class/species + Referenced Cubes footer row is shared with every `PERK:` category's `render_card()`** via `compute_footer_row_h()`/`draw_footer_row()`, so the two card styles' footers can't drift apart. Differences from a plain `render_card()`, each traced to something the screenshot actually showed or later user feedback while eyeballing rendered cards:
  - **A plain stacked "50 MANA" text (no box/border) + a red HP bar** in a left stat column, instead of a `Mana Cost: X | HP: Y/Z` text line. HP always renders `current/max` even when equal (e.g. `6/6`, not collapsed to `6`). The mana value briefly had a blue box outline around it too (matching the HP bar's own boxed look) — dropped per follow-up feedback once compared against the reference screenshot again, which shows plain unboxed text for mana.
  - **One bullet glyph per top-level ability** — a hollow square for a one-shot/event trigger, a solid hourglass for a time-driven one (`draw_bullet`/`is_timed_trigger`) — instead of a plain `- ` dash. The classification is a name-substring heuristic (`Every` appears in every recurring built-in trigger checked: `ChargeEveryX`, `EverySecond`, `EveryXSeconds`, `EveryXMeleeY`, `EveryXAcidicY`, `EveryXTicks`; never in a one-shot one checked: `AfterThisDies`, `AfterThisCollides`, `AfterACubeCollides`, `AtTheStartOfTheBattle`, `BeforeThisIsDrawn`) since the two groups' own declared arg TYPEs don't reliably distinguish them (`EverySecond`/`EveryXSeconds` don't even declare a `TIME`-typed arg). **A mod's own `COMPOUND: ABILITY` granted directly as a top-level `Ability:` line is classified from ITS OWN root trigger line, not its name** — `load_mod_compound_docs()` records a `"timed"` field per compound from `block_lines[0]`'s first token, and `collect_ability_texts()` prefers that field when present. Real case this caught: Voidling's `VoidNova` doesn't contain "Every" in its own name, but its body's root line is `EveryXSeconds ...` — classifying by the compound's own name alone rendered the wrong (square) bullet before this fix.
  - **A faint steady grey outline around the icon** (not the game's own sprite border — a decoration this script itself draws, framing the icon like the in-game library screen's un-pinned card-slot outline the user pointed at, minus that screen's thicker corner-square accents which are an unrelated selection-state indicator). Gated behind the gitignored `.claude/preferences.local.md`'s `preview_card_icon_border: on|off` (see `cube-chaos-repo-setup`), default `on` — flip and regenerate to compare, no code change needed. Cube-only, not part of the shared footer row.
- **Shared footer row (both CUBE and PERK cards): class/species name (text only, no icon) on the left, referenced-cube icons (icon only, no name) to its right** — went through several rounds of user feedback while eyeballing rendered cards, each trimming it further:
  1. Started as two stacked blocks (a labeled "Referenced Cubes" section under a class/species icon+name line) — merged into one shared row since a long referenced-cubes list was growing the card's height too much (`footer_row_h` sized to whichever element is tallest, everything vertically centered against that one height).
  2. Dropped the "Referenced Cubes:" text label — icon(s) immediately next to the class/species entry read as self-explanatory without it.
  3. Dropped the class/species ICON (kept the name, in its own color) and dropped each referenced cube's NAME (kept the icon) — both name/icon pairs had become redundant once shown side-by-side with the other half of the row.
  - **Class/species name**, in that class/species's own color. `find_class_species()` reads slot 0 of whichever file `perks_source_basenames()` finds first — confirmed across every mod that has one (DJ/General/Broker's class perk, Unholy/Voidling's species perk) that this is always the file's first `PERK:` block, matching the "Base class/species icon style" fill-equals-border convention above. **Sample the color with `sample_dominant_color()`, which excludes the SHEET's own default background `(0,148,255)`, not this script's black card-canvas `BG`** — an early version of this popped the wrong background color and returned the sheet's blue as "the class color" for Unholy (verified: a guaranteed-blank/mostly-background tile is ~72% `(0,148,255)` pixels vs ~28% the real `(150,20,20)` icon/border color). Mods with no class/species of their own (`Great_Wall`, `Home_Turf_Advantage` — Terrain/Neutral-only) simply omit that half of the row. Computed once per mod into the `CLASS_SPECIES` global (`render_mod()`), not per card — every category shares the same value.
  - **Referenced cubes, from TWO sources (`referenced_cubes_for()`), declared names first:**
    1. **Explicit `ReferenceCube: <Name>` declarations — the actual authoritative mechanism, missed entirely until 2026-08-02.** `ReferenceCube:` is a real, repeatable `PERK:` field (see `cube-chaos-scripting/references/authoring-and-inheritance.md`, confirmed real usage e.g. `Characters/Classes/Cryomancer.c.txt:68-70`) that an author uses specifically to curate a perk's tooltip cube list — this repo's own mods already use it for every dragon-egg-line perk (e.g. General's `War_Dragon_Egg` declares `War_Dragon_Egg`/`Baby_War_Dragon`/`War_Dragon`, showing the whole evolution chain even though the perk's own `Ability:` only ever grants itself) and for perks that grant a cube from a random pool where no single literal `CubeConstant` token exists to scan (Unholy's `Lichdom` declares `Damned_Soul`/`Plague_Imp`/`Imp`, none of which appear as a literal `CubeConstant` anywhere in its body — the actual pick goes through an `ARandomCubeInLibraryWhich`-style production). **Not self-name-filtered** — `War_Dragon_Egg` legitimately declares `ReferenceCube: War_Dragon_Egg` (its own name) to show the exact cube it grants, unlike source 2 below. Real regression this fix caught: before it, `War_Dragon_Egg`'s card rendered with an EMPTY Referenced Cubes row despite 3 explicit declarations, because its only `CubeConstant` token (`FreeCopy CubeConstant War_Dragon_Egg`) was a self-reference the heuristic scan correctly excludes — the heuristic was never the real mechanism for this case, `ReferenceCube:` was.
    2. **The heuristic scan** (`find_referenced_cubes`): any cube a `CUBE:`/`PERK:` block's own lines create/copy/obtain via a `CubeConstant <Name>`/`HiddenCubeConstant <Name>` token pair (a `CUBE`-typed arg is always spelled as that keyword plus the name, never the name alone, same fact `resolve_builtin_ability_text` already relies on). Scans the WHOLE block body, not just top-level lines, since these references usually live on indented sub-lines of a chain (or, for a `PERK:`, an `ObtainAction: AddCubeToDeck/AddCubeToInventory CubeConstant <Name>` line — confirmed working via DJ's own `PERK: DJ`, which obtains `Microphone`/`Speaker` this way). **Also expands one hop into a bare top-level `Ability: <CompoundName>` grant's own body** — DJ's `Speaker` grants `Ability: SpeakerNoteSpawn` with zero inline args, and it's `SpeakerNoteSpawn`'s own body (not Speaker's) that contains `CubeConstant Note`. Not followed recursively past one hop. **Excludes any `SetSpriteToCube CubeConstant <Name>` target** — that's the "directional cube icon" sprite-swap pattern (`_Arc`/`_West` icon-only helper cubes, see below), not a cube actually being created; real case caught reading rendered cards back: General's `Bomber`/`Drop_Helicopter`/`Baby_War_Dragon` each swap to a `_West` icon-only twin when reversing direction, and that swap target was showing up as if it were a spawned cube. This heuristic is now purely a fallback for perks/cubes with no `ReferenceCube:` field of their own (most of them), self-name-excluded as before (a self-reference from an incidental copy operation isn't the same signal as an explicit author declaration).
    - A referenced name resolves to a real icon via the `CUBE_NAME_TO_ICON` global first (`build_cube_icon_index()`, this mod's own `_Cubes.c.txt`/sheet, computed once per mod in `render_mod()` and shared by every card category — a `PERK:` card resolves against the same pool as a `CUBE:` card, not a separate lookup), **then `base_game_cube_icon_index()` as a fallback** — a memoized (computed once total, not once per mod) index over the base game's own `CUBE:`-defining files (`BASE_GAME_CUBE_FILES`: `Base_Core/3TokenCubes`, `Characters/2TokenCubes`+`GeneralCubes`, `Main/2TokenCubes`+`3GeneralCubes`, `Extra_Mechanics/TokenCubes`, `Modding_Example/GeneralCubes`), read-only per `CLAUDE.md`'s hard rule (reading base-game files is always fine, only writing is not). Real case this fixed: General's `General-Undead` synergy perk creates `CubeConstant Zombie` — `Zombie` is a base-game `TOKEN` cube (`Extra_Mechanics/TokenCubes.c.txt`), not one of General's own, so it rendered with no icon at all until this fallback existed; same fix also resolved Great_Wall's own `ReferenceCube: Anchored_Basalt`/`Water`/`Catapult` (all base-game cubes) and two more Unholy synergy perks (`Rogue-Unholy`/`Warrior-Unholy`, referencing `Catapult`). **A name still unresolved after both lookups is dropped entirely, not kept as a name-less blank entry** — since this footer never shows text, an icon-less entry contributes zero visible content but would still reserve a full footer row's worth of blank vertical space (this is how the Great_Wall gap was originally caught, before the base-game fallback existed — now only a genuinely unresolvable name, e.g. one from a mod this repo doesn't have installed, hits this path).
- **A `CUBE` with a `TRIGGER`-type `Animation:` line also gets a looping `.gif` next to its static card** (`<ModPrefix>_Cubes_<CubeName>_<AnimName>.gif`, added 2026-07-30), so a README can actually show the flourish instead of just a static icon. `build_cube_animation_gifs()` reads the frame order/speed straight from the real `Animation:` line (see `cube-chaos-scripting`'s `cube-animation.md` for why the LAST frame is the idle pose, not frame 0, and why each flourish frame's duration is `Thresholds[i+1] * 16ms`) — the only liberty taken is compressing the idle pause between triggers to a fixed `GIF_IDLE_REST_MS` instead of the cube's real (often many-second) cadence, so the loop stays watchable. Only `TRIGGER` is handled; `CLOCK`/`HP`/`DOUBLE`/`BOOLEAN`/`TIME` would each need their own playback logic if a mod ever uses one. **README convention: a compact `<table>` right after the cube's static card, 2 animation entries per row** — each entry is a (trigger condition, gif) pair (e.g. `On Cube Creation` for DJ's `Speaker`, whose animation is tied to the ability that creates its Note), `valign="middle"` on every cell, and a new row starts after every 2nd entry (a mod with an odd number of animated cubes just leaves the last row's second pair absent — don't pad it with an empty cell). **No inline `style=` attribute for borders/padding — GitHub's README sanitizer strips the `style` attribute entirely, so any attempt to suppress or customize cell borders (e.g. `border: none`, a single divider line between the two entry-pairs) silently does nothing; what actually renders is GitHub's own default `.markdown-body table` CSS, which always draws a full grid line around every cell of every `<table>`, with no author override available.** Confirmed 2026-07-30: an earlier version of this doc/README specified inline `border-collapse`/`border: none` styling for an outline-only look, which looked right when read as raw HTML but rendered with full grid lines once pushed to GitHub. Plain unstyled `<table>`/`<tr>`/`<td valign="middle">` is now the deliberate convention — don't re-attempt CSS-based border control here, it cannot work on GitHub. **Size the gif's `<img width=...>` to match how big the icon actually renders inside the static card, not the gif's own native pixel size** — the static card is a fixed `W=1500`px canvas displayed at `width="700"` (a `700/1500` ≈ 0.467× shrink), so a `scale`-upscaled icon that's natively `150px` (15×10, DJ's cube scale) renders on-screen at only `150 × 700/1500 = 70px` inside that card. The gif itself is generated at the same native `150px`, so displaying it at `width="150"` makes it look ~2× bigger than the same icon looks in the card right above it — set `width="70"` (or recompute `icon_px * card_display_width / W` for a different mod's numbers) instead.
- **Every `IsUpgradeFrom:` perk's own card is itself an animated `.gif`** (`<ModPrefix>_Perks_<PerkName>.gif`, same name/slot a static `.png` would otherwise use — added 2026-08-01, corrected same day) — a white diagonal line, oriented like a `/` (one end lower-left, one end upper-right), that translates down-and-right across the perk's icon (entering near the top-left corner, exiting near the bottom-right), pausing a couple seconds between sweeps. This is the real in-game visual cue that a reward perk is an upgrade of a base one — described to this skill secondhand by the user (no DSL/sprite source to read, since it's a fixed engine UI effect applied to the whole "is an upgrade" category, not per-item data) and confirmed correct by reading the rendered gif's own frames back before calling it done. **Scope: `IsUpgradeFrom:` reward-perk chains specifically (the ones living in `<ModPrefix>_UpgradePerks.c.txt`, or occasionally mixed into a regular Perks/Species file) — NOT `BelongsTo: CubeUpgrade` perks** (a different, unrelated mechanic — a perk that upgrades a chosen cube, e.g. Unholy's `Wildcard_Upgrade`), confirmed explicitly with the user since both share the word "upgrade" and the request could have meant either.
  - **The whole card animates in place, not a separate companion file.** A first version generated a small standalone `_Shine.gif` of just the icon, shown as an *extra* image below the static card (mirroring the CUBE `Animation:` gif's own companion-file convention) — user feedback (2026-08-01) was that the shine belongs IN the existing preview image itself, not bolted on beside it. Fixed by re-rendering the FULL card once per shine frame inside `build_perks()`'s `render_block()` (varying only the icon argument, so title/desc/value/footer stay pixel-identical across frames — `render_card()` is deterministic in everything else) and returning `(name, ("gif", card_frames, durations))` instead of a plain `Image`. `render_mod()`'s generic per-category save loop now checks for that `("gif", ...)` tuple shape on ANY card (not just a `"Perks"`-category special case) and saves an animated `.gif` instead of a `.png` when it sees one — the stale-file cleanup already keyed on `written` filenames handles the extension switch for free (an old `.png` of the same perk, or the old separate `_Shine.gif`, both just stop appearing in `written` and get deleted like any other stale file). README convention is now simplest of all: no extra line needed, just the perk's existing `<img>` line's `.png` extension becomes `.gif` (GitHub renders an animated gif in a plain `<img>` tag same as a static one).
  - **The line must be drawn at the icon's own NATIVE (pre-upscale) resolution, then upscaled with NEAREST — not drawn on the already-upscaled card icon.** The first version drew directly on the final 175px-wide upscaled icon with a 5px-wide line, which is under 1 native pixel wide at that 7x scale — it rendered smooth and anti-aliased-looking, wrong for what's actually a chunky ~25x25-native pixel-art effect in the real game (user feedback: too smooth, should be roughly twice as big and pixelated). Fixed: `draw_shine_line_native()` draws a 2-native-pixel-wide line directly on the raw pre-upscale icon crop, and `build_shine_icon_frames()` upscales each finished native frame with `upscale()` (`Image.NEAREST`, same as every other sprite in this file) — the line now inherits the same blocky look as the rest of the icon.
  - `build_shine_icon_frames()`/`draw_shine_line_native()` synthesize the sweep purely in code (`SHINE_SWEEP_STEPS`/`SHINE_FRAME_MS`/`SHINE_IDLE_REST_MS`/`SHINE_LINE_WIDTH_NATIVE` constants) rather than reading anything from the mod's own files, unlike the CUBE `Animation:` gif above. The line's endpoints are both shifted by the same `(offset, offset)` vector along the tile's own corner-to-corner diagonal, sweeping `offset` from `-tile_width` to `+tile_width` so the line is genuinely off-canvas (not abruptly appearing mid-tile) at both ends of the sweep — Pillow's own GIF writer auto-merges some of those frames on save (observed 15 authored frames landing as 8 in the saved file, since a few sweep steps land fully off-canvas and are pixel-identical to the idle frame), which is harmless, just a smaller file.
