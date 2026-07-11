---
name: cube-chaos-sprite-art
description: Use whenever creating or resizing pixel-art sprite sheets for a Cube Chaos mod (CUBE icons, PERK icons, or CLASSSPECIES synergy portraits) - covers the game's fixed tile-size convention, default colors, and the special combo border used only on class+species synergy perks. Trigger on "sprite sheet", "cube icon", "perk icon", "synergy portrait", "class+species border", or when a GameData/<Mod>/Sprites/*.c.png file needs to be created or fixed.
---

# Cube Chaos sprite sheet conventions

These facts were reverse-engineered empirically (by measuring real game files pixel-by-pixel), not guessed. Trust them over any formula involving `ceil(sqrt(count))` — that coincidentally matches some files but is NOT how the game actually slices sprites.

## Fixed tile sizes (confirmed across many independent real files)

- **CUBE icons: 17×17 px.** Confirmed via `Main/Sprites/3GeneralCubes.c.png` (714÷17=42), `Characters/Sprites/2TokenCubes.c.png` (306÷17=18), `Modding_Example/Sprites/GeneralCubes.c.png` (272÷17=16).
- **PERK icons (class perks, reward perks, AND class+species synergy perks): 27×27 px.** Confirmed via `Characters/Classes/Sprites/Priest.c.png` (108÷27=4), `Characters/Sprites/Synergies.c.png` (540÷27=20), `Main/Sprites/Perks.c.png` (621÷27=23), `Modding_Example/Sprites/Synergies.c.png` (270÷27=10).

Sheet dimensions = `tile_size * grid_dim`, where `grid_dim = ceil(sqrt(number_of_CUBE:_or_PERK:_definitions_in_the_matching_.txt_file))`. The sheet must be square. Icons are cropped in the order the `CUBE:`/`PERK:` blocks appear in the txt file (top to bottom), row-major. Extra unused grid cells are fine and normal (real game files often have far more cells than currently-defined content — that's expected headroom, not a bug).

**An `IsUpgradeFrom:` upgrade perk needs no *unique* sprite of its own — it visually reuses its base perk's icon in-game — but this is NOT the same as "skip it when computing slot positions."** Two genuinely different cases, easy to conflate:
- A `.c.txt` file that is **entirely** upgrade perks, with **no matching sprite sheet at all** (e.g. `Characters/Species/UpgradeSpeciesPerks.c.txt`, ~20 upgrade perks, zero corresponding `Sprites/*.c.png`): here there's no grid to speak of, so "doesn't need a sprite" trivially also means "doesn't need a slot."
- A `.c.txt` file that **mixes** regular and upgrade perks sharing one real sprite sheet (e.g. this mod's `DJ_Perks.c.txt`): here **every `PERK:` block, upgrade or not, still consumes one sequential slot in file order** — an upgrade's slot is just conventionally left blank (background only, no border even) since nothing ever displays it. Get this wrong and every regular perk *after* the first upgrade in the file silently lands one-or-more slots off from where the engine actually looks — the resulting warning is `WARNING: Perk <name> from package <pkg> with empty Image` (checkerboard/missing-texture in-game), and it can take several perks added over several sessions before the drift is even noticed, since the game doesn't error at load, just logs a warning per affected perk.

Real incident: the DJ mod's `Feedback`/`Final_Countdown`/`Grand_Finale` were all placed assuming upgrades don't consume a slot (following the *first* case above by mistake) — `Final_Countdown` silently got the *next* perk's would-be slot and vice versa, while the truly-blank upgrade slots sat one position further along than intended. Fixed by relocating the two swapped icons to their correct positions and blanking the (correctly) empty upgrade slots — confirmed via the exact `empty Image` warning disappearing from the affected non-upgrade perk and reappearing, harmlessly, on the upgrade perks whose slots are supposed to be blank.

**When sizing a sheet / picking a slot index for a `.c.txt` file with a real sprite sheet, count every `PERK:` block in file order, including `IsUpgradeFrom:` ones** — don't filter them out. (The "upgrade-only file, no sheet" case above is the one and only time it's correct to not think about slots for upgrades at all — because there's no sheet to place them in.)

**The sprite file must be named identically to its `.txt` file** (e.g. `Cubes.c.txt` → `Sprites/Cubes.c.png`). Two different mod folders must NOT reuse the same txt/png basename as any already-loaded package (e.g. don't create `Perks.c.txt` if `Main/Perks.c.txt` already exists) — the engine appears to key sprite sheets by filename, and a collision silently mis-maps your icons into the colliding file's sheet instead of erroring.

## Default background color

`RGB(0, 148, 255)` — confirmed as the overwhelmingly most-common pixel color in every real cube and perk sheet checked. Use this exact value for new sprite sheets, not an approximation.

## Border pattern library — every `PERK:` category has its own fixed border, generate it from scratch

Every 27×27 PERK sheet in the base game (and this mod) is genuinely rendered with a border tied to the perk's category — not just CLASSSPECIES. All of them share one universal outer ring (`RGB(255,0,220)` magenta, row/col 0, the same non-rendered-looking-but-actually-rendered guide color everywhere), then diverge inward. **None of this needs to be re-extracted from a reference file** — every pattern below is fully determined by fixed pixel positions plus at most one or two named colors, so it can be generated purely from code once you know which category you're drawing for. Re-verifying against a real file is still worth doing once per *new* category (see the empirical method at the end of this section), but for the categories already catalogued here, generate directly from the recipes below.

### Universal constants and a shared ring-drawing helper

```python
T = 27                        # perk tile size (17 for CUBE icons, which have no border convention at all)
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
| `BelongsTo: TerrainPerk` (Terrain perks) | brown `(105,48,0)` | `Extra_Mechanics/Sprites/TerrainPerks.c.png` |
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
| `BelongsTo: Nightmare` (or however Nightmares self-identify — check `Extra_Mechanics/Nightmares.c.txt`) | red `(255,0,0)` |
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
