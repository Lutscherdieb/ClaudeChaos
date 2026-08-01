"""Render a Terrain perk's battlefield as a top-down grid image, straight
from its own ADDITIONALMAP:/DATA:/DATARECT: map data -- no game launch or
manual screenshot needed. Every real in-game visual quirk below was
reverse-engineered from the game's own compiled classes (CFR-decompiled
Cube Chaos.jar -- see reference_jar_decompile_technique in this repo's
memory / cube-chaos-scenario-scripting/references/battle-and-terrain-maps.md
for the general method), not guessed from screenshots:

1. **A placed cube's battlefield look is NOT always its tooltip icon.** A
   TOKEN cube with `Animation: <Name> HP <effect> ...` (e.g. Great_Wall's own
   `Anchored_Basalt`/`Stable_Plates`, both `Animation: Crumble HP 0 EQUAL 4`)
   swaps its drawn sprite based on current HP -- decompiled
   `HPAnimation.AutoChangedCheck`/`Animation.LastFrame` (default `0`) confirm
   FRAME 0 (leftmost frame in `<CubeName>_<AnimName>.png`) is what shows at
   full HP, i.e. a freshly-generated, undamaged battlefield -- not the last
   frame (that's only true for TRIGGER-type animations' idle pose, a
   different mechanism -- see cube-animation.md). Confirmed visually: frame 0
   of `Anchored_Basalt_Crumble.png`, tiled, pixel-matches the real wall
   texture in a genuine screenshot; the plain `TokenCubes.c.png` tooltip icon
   for the same cube does not (it's a mismatched brown/orange dirt-like
   tile -- the real Anchored_Basalt tooltip icon and its battlefield look are
   simply two different pieces of art, both legitimate, used in different
   UI contexts).
2. **The engine treats the sprite sheets' own default background,
   RGB(0,148,255) -- packed as the int 38143, confirmed via
   `ColourGrid.ApplyLightingGrid`/`Cube.DrawLightingStep`'s literal `38143`
   argument -- as a hard chroma-key: fully transparent, not a visible color.**
   Composited here the same way: background pixels get alpha=0 instead of
   being pasted as an opaque blue square.
3. **`CAMPAIGNSETUP: X Y` (inside the shared `Battle_*_Player` partial) takes
   two literal tile coordinates, not `faction x`** -- decompiled
   `ScenarioReader`'s `"CAMPAIGNSETUP:"` case reads exactly two ints and
   calls `Game.Campaign.GetLeader().CreateInWorld(WorldGrid[X][Y], ...)`,
   i.e. it places the player's own campaign leader cube at that literal
   tile. `cube-chaos-scenario-scripting/references/battle-and-terrain-maps.md`
   previously mis-documented this as a per-faction starting column; fixed
   there in the same edit as this script. Since the actual leader sprite is
   whichever class the player picked (not static terrain data), this script
   stands in the generic base-game `Leader` token cube (real sprite,
   `Base_Core/3TokenCubes.c.txt`) as a placeholder at that tile instead of
   guessing a class.
4. **Placed cubes get a per-pixel ambient-occlusion-style darkening based on
   distance to the nearest open/background pixel, searched only upward
   (straight up or diagonally up) -- never sideways within the same row or
   from below.** Decompiled `ColourGrid.UpdateLighting`'s DP recurrence only
   ever reads `Result[x-1][y-1]`/`Result[x][y-1]`/`Result[x+1][y-1]` (the row
   above), and its brute-force fallback (triggered at each cube's own tile
   edges, to reach into neighbor cubes) only ever looks at row offsets `-d`
   (i.e. also strictly upward, via `GridPoint.NorthG`/`EastG`/`WestG` --
   never `SouthG`). `ColourGrid.ApplyLightingGrid` then shifts each non-
   background pixel's HSV: distance-15-or-more (capped, `Cap = 15.0`) halves
   brightness (`V *= 0.5`); distance-0 (touching open air) leaves it
   ~unchanged; saturation drifts up to 9% toward `(distance/Cap)`. Computing
   this per-pixel over the WHOLE assembled map (rather than per-tile plus
   cross-tile neighbor lookups, which is what the engine does to avoid
   recomputing a whole map's worth of pixels every frame) reproduces the
   identical result in far less code, since tile boundaries are just
   ordinary adjacent pixels once the map is one big array.

Usage (from the repo root, or anywhere -- paths below are absolute):
    python3 render_terrain_screenshot.py

Scope: only renders the terrain's OWN ground-layout partial(s) plus the
shared Battle_*_Player/Enemy partials' explicit leader placements (the
player's `CAMPAIGNSETUP:` tile and the enemy's own `Difficulty_Leader`
`DATA:` line, where present) -- NOT the AI's own randomized starting hand
(`RANDOMFITTINGSETUP:`), which places additional units unpredictably and
isn't map DSL data at all.

Reusable for any terrain mod, not just Great_Wall: `render_terrain_mod()`
takes the map file, output dir, and output list as plain arguments, plus an
optional `mod_dir`/`mod_prefix` pair so a terrain's own ground TOKEN cubes
(if it defines any of its own, rather than reusing Extra_Mechanics/
TokenCubes.c.txt ones the way Great_Wall does) resolve correctly. Add a new
call at the bottom of this file for a new terrain mod rather than repointing
the Great_Wall-specific call -- see the "Registered terrain mods" comment
there. This is wired into `content-terrain.md`'s own workflow (run it right
after writing a new terrain's ground-layout partial(s), show the PNG to the
user, and iterate on tile coordinates before moving on to sprites/test-
launch -- much faster than a full game launch for catching a misplaced
`DATARECT:`) and into `.claude/hooks/regen-terrain-screenshots.sh`, which
reruns every registered terrain mod after any `GameData/*.c.txt` edit.

Boss-battle compositing (see battle-and-terrain-maps.md for the full
derivation): a `*_Boss_Terrain`-flavored battle fires
Battle_Terrain_Generation + Battle_Boss_Generation + Battle_Player_Generation
only (never Battle_Enemy_Generation), which resolves to the terrain's ground
partial AND its boss-ground partial BOTH being composited (not the boss
partial alone) plus the player's own leader -- but no enemy Difficulty_Leader.
"""
import colorsys
import math
import os
import re
import sys
from PIL import Image

ROOT = r"e:\Programme\Steam\steamapps\common\Cube Chaos"
sys.path.insert(0, os.path.join(ROOT, ".claude", "skills", "cube-chaos-sprite-art", "scripts"))
import render_preview_cards as rpc  # noqa: E402 -- reuse its base-game file list/block parser

NATIVE_TILE = 15  # a cube's own real content resolution (17x17 sheet slot minus the 1px guide ring)
SCALE = 2  # NATIVE_TILE * SCALE = 30, matching the real reference screenshots' own 30px/tile
BG_RGB = (0, 148, 255)  # the engine's universal chroma-key background (int 38143 in the decompiled code)
CAP = 15.0  # ColourGrid's own Cap = sqrt[225] = 15.0

# Sampled at x=5 from GameData/Great_Wall/Screenshots/GreatWall.png (a column
# with no map content, pure sky) at y=0,100,...,650 -- the real game's own
# vertical sky gradient, top (dark navy) to horizon (bright blue).
SKY_STOPS = [
    (0, (30, 48, 101)), (100, (32, 63, 136)), (200, (29, 77, 166)),
    (300, (24, 92, 192)), (400, (18, 108, 213)), (500, (11, 124, 230)),
    (600, (6, 140, 242)), (650, (4, 149, 247)),
]


def sky_color(y):
    if y <= SKY_STOPS[0][0]:
        return SKY_STOPS[0][1]
    if y >= SKY_STOPS[-1][0]:
        return SKY_STOPS[-1][1]
    for (y0, c0), (y1, c1) in zip(SKY_STOPS, SKY_STOPS[1:]):
        if y0 <= y <= y1:
            t = (y - y0) / (y1 - y0)
            return tuple(round(c0[i] + (c1[i] - c0[i]) * t) for i in range(3))


# --- Terrain map DSL parsing (ADDITIONALMAP:/CUBE:/DATA:/DATARECT:/CAMPAIGNSETUP:) ---

SCENARIO_RE = re.compile(r'^SCENARIO:\s*(\S+)')
CUBE_LOCAL_RE = re.compile(r'^CUBE:\s*(\d+)\s+(\S+)')
DATA_RE = re.compile(r'^DATA:\s*(\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)')
DATARECT_RE = re.compile(r'^DATARECT:\s*(\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)')
ADDITIONALMAP_RE = re.compile(r'^ADDITIONALMAP:\s*//\s*(\d+)\s+(\d+)\s*//')
CAMPAIGNSETUP_RE = re.compile(r'^CAMPAIGNSETUP:\s*(-?\d+)\s+(-?\d+)')
PLACERECT_RE = re.compile(r'^PLACERECT:\s*(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)')


def parse_scenarios(path):
    """name -> {'w', 'h', 'ops': [(x, y, w, h, cube_name_or_None, faction), ...],
    'placerects': [(x, y, w, h, faction), ...]} for every ADDITIONALMAP:-bodied
    SCENARIO: block in the file. ops are kept in file order (a DATA:/
    CAMPAIGNSETUP: line becomes a 1x1 op) so compositing them onto a grid in
    order naturally reproduces the DSL's own last-write-wins overlap
    behavior. `CAMPAIGNSETUP: X Y` places the generic `Leader` token cube
    directly at faction 1 (see module docstring point 3/5) -- it has no
    local CUBE: index of its own, and the engine hardcodes its faction to 1
    regardless (decompiled ScenarioReader's own CreateInWorld call site)."""
    lines = open(path, encoding="utf-8").read().split("\n")
    scenarios, name, local, w, h, ops, placerects, in_map = {}, None, {}, None, None, [], [], False
    for line in lines:
        s = line.strip()
        m = SCENARIO_RE.match(s)
        if m:
            name = m.group(1)
            continue
        m = ADDITIONALMAP_RE.match(s)
        if m:
            in_map, w, h, local, ops, placerects = True, int(m.group(1)), int(m.group(2)), {}, [], []
            continue
        if not in_map:
            continue
        if s == "EndMapData":
            scenarios[name] = {"w": w, "h": h, "ops": ops, "placerects": placerects}
            in_map = False
            continue
        m = CUBE_LOCAL_RE.match(s)
        if m:
            local[int(m.group(1))] = m.group(2)
            continue
        m = DATA_RE.match(s)
        if m:
            idx, x, y, faction = (int(g) for g in m.groups())
            ops.append((x, y, 1, 1, local.get(idx), faction))
            continue
        m = DATARECT_RE.match(s)
        if m:
            idx, faction, x, y, rw, rh = (int(g) for g in m.groups())
            ops.append((x, y, rw, rh, local.get(idx), faction))
            continue
        m = CAMPAIGNSETUP_RE.match(s)
        if m:
            x, y = int(m.group(1)), int(m.group(2))
            ops.append((x, y, 1, 1, "Leader", 1))
            continue
        m = PLACERECT_RE.match(s)
        if m:
            x, y, rw, rh, faction = (int(g) for g in m.groups())
            placerects.append((x, y, rw, rh, faction))
    return scenarios


# --- Resolving a cube name to its real native-resolution battlefield art ---

_BLOCK_CACHE = None


def _all_base_game_blocks():
    """package/basename/cube_name -> (block_lines, sheet_path, index, cols),
    built once. Mirrors render_preview_cards.base_game_cube_icon_index's own
    file list/first-package-wins order, but keeps the block's raw lines
    (for Animation: detection) and the sheet path (for the animation-frame
    fallback's own Sprites/Animations/ lookup) instead of just the final
    icon."""
    global _BLOCK_CACHE
    if _BLOCK_CACHE is not None:
        return _BLOCK_CACHE
    index = {}
    for package, basename in rpc.BASE_GAME_CUBE_FILES:
        base_dir = os.path.join(ROOT, "GameData", package)
        txt_path = os.path.join(base_dir, f"{basename}.c.txt")
        png_path = os.path.join(base_dir, "Sprites", f"{basename}.c.png")
        if not (os.path.exists(txt_path) and os.path.exists(png_path)):
            continue
        blocks = rpc.parse_blocks(txt_path, rpc.CUBE_HEADER)
        for i, b in enumerate(blocks):
            name = b["header"].group(1)
            if name not in index:
                index[name] = {
                    "lines": b["lines"], "base_dir": base_dir, "sheet": png_path, "index": i,
                }
    _BLOCK_CACHE = index
    return index


_MOD_BLOCK_CACHE = {}


def _mod_own_blocks(mod_dir, mod_prefix):
    """Same shape as _all_base_game_blocks(), but for one terrain mod's own
    `<ModPrefix>_Cubes.c.txt` -- checked FIRST (see resolve_tile_rgba below)
    so a new terrain's own decorative TOKEN ground cubes (content-terrain.md
    step 2 -- these go through the normal CUBE: workflow, which for a mod
    that isn't Extra_Mechanics means this file, not a base-game one) resolve
    to real art instead of silently rendering blank. Mirrors
    render_preview_cards.py's own CUBE_NAME_TO_ICON-before-base-game-
    fallback order for a PERK card's Referenced Cubes row. Great_Wall itself
    needs none of this -- its own ground tokens (Anchored_Basalt,
    Stable_Plates) live in Extra_Mechanics/TokenCubes.c.txt, already covered
    by _all_base_game_blocks() -- so this is a no-op ({}) until a future
    terrain mod actually defines its own ground TOKEN cubes."""
    key = (mod_dir, mod_prefix)
    if key in _MOD_BLOCK_CACHE:
        return _MOD_BLOCK_CACHE[key]
    index = {}
    txt_path = os.path.join(mod_dir, f"{mod_prefix}_Cubes.c.txt")
    png_path = os.path.join(mod_dir, "Sprites", f"{mod_prefix}_Cubes.c.png")
    if os.path.exists(txt_path) and os.path.exists(png_path):
        blocks = rpc.parse_blocks(txt_path, rpc.CUBE_HEADER)
        for i, b in enumerate(blocks):
            name = b["header"].group(1)
            if name not in index:
                index[name] = {
                    "lines": b["lines"], "base_dir": mod_dir, "sheet": png_path, "index": i,
                }
    _MOD_BLOCK_CACHE[key] = index
    return index


_CURRENT_MOD = (None, None)  # (mod_dir, mod_prefix) of the terrain mod currently being rendered, set by render_terrain_mod()


ANIMATION_HP_RE = re.compile(r'^Animation:\s*(\S+)\s+HP\b')


def _strip_and_key_alpha(tile_rgba):
    """Crop the 1px guide-ring border (same convention as
    render_preview_cards.crop_icon's strip_guide) and chroma-key BG_RGB
    pixels to alpha=0 -- both the main sheet and animation-frame strips use
    the same convention (cube-chaos-sprite-art SKILL.md's "Default
    background color")."""
    w, h = tile_rgba.size
    inner = tile_rgba.crop((1, 1, w - 1, h - 1)).convert("RGBA")
    px = inner.load()
    for y in range(inner.height):
        for x in range(inner.width):
            r, g, b, a = px[x, y]
            if (r, g, b) == BG_RGB:
                px[x, y] = (r, g, b, 0)
    return inner


_TILE_CACHE = {}


def _resolve_tile_rgba_unflipped(cube_name):
    mod_dir, mod_prefix = _CURRENT_MOD
    cache_key = (mod_dir, cube_name)
    if cache_key in _TILE_CACHE:
        return _TILE_CACHE[cache_key]
    info = None
    if mod_dir and mod_prefix:
        info = _mod_own_blocks(mod_dir, mod_prefix).get(cube_name)
    if info is None:
        info = _all_base_game_blocks().get(cube_name)
    result = None
    if info is not None:
        for l in info["lines"]:
            m = ANIMATION_HP_RE.match(l.strip())
            if not m:
                continue
            anim_name = m.group(1)
            anim_path = os.path.join(info["base_dir"], "Sprites", "Animations",
                                      f"{cube_name}_{anim_name}.png")
            if os.path.exists(anim_path):
                strip = Image.open(anim_path).convert("RGBA")
                tile17 = strip.crop((0, 0, 17, strip.height))  # frame 0 (leftmost) -- full HP, see docstring point 1
                result = _strip_and_key_alpha(tile17)
            break
        if result is None:
            sheet = Image.open(info["sheet"]).convert("RGBA")
            cols = sheet.width // 17
            row, col = divmod(info["index"], cols)
            tile17 = sheet.crop((col * 17, row * 17, col * 17 + 17, row * 17 + 17))
            result = _strip_and_key_alpha(tile17)
    _TILE_CACHE[cache_key] = result
    return result


def resolve_tile_rgba(cube_name, faction=1):
    """Native-resolution (NATIVE_TILE x NATIVE_TILE) RGBA art for a cube
    name, with the chroma-key background already made transparent. None for
    a name with no resolvable sprite (engine-hardcoded placement-only names
    like Empty -- see battle-and-terrain-maps.md's own note on this).

    **Mirrored left-right whenever faction is not 1 or -1** -- decompiled
    `Cube.DrawFactionStep`: `if (Faction != 1 && Faction != -1) FactionCG =
    Input2.FlipYAchse();`. This is why an enemy-faction (2) Catapult faces
    the opposite way from a player-faction one; every real `DATA:`/
    `DATARECT:` op's own faction argument (0 for neutral terrain fill too --
    only faction 1 and the special -1 are ever left unflipped) is passed
    straight through to this, not just enemy units specifically."""
    if cube_name is None:
        return None
    base = _resolve_tile_rgba_unflipped(cube_name)
    if base is None:
        return None
    if faction == 1 or faction == -1:
        return base
    key = (_CURRENT_MOD[0], cube_name, "flipped")
    if key not in _TILE_CACHE:
        _TILE_CACHE[key] = base.transpose(Image.FLIP_LEFT_RIGHT)
    return _TILE_CACHE[key]


# --- Grid compositing + per-pixel lighting ---

def build_native_grid(scenario_names, all_scenarios, w, h):
    """w x h grids of (cube_name, faction) -- later-scenario ops overwrite
    earlier ones at the same cell, matching real map-DSL overlap behavior
    (see module docstring's boss-compositing note)."""
    cube_grid = [[None] * w for _ in range(h)]
    faction_grid = [[1] * w for _ in range(h)]
    for name in scenario_names:
        for x, y, rw, rh, cube_name, faction in all_scenarios[name]["ops"]:
            for gy in range(y, min(y + rh, h)):
                for gx in range(x, min(x + rw, w)):
                    if 0 <= gx < w and 0 <= gy < h:
                        cube_grid[gy][gx] = cube_name
                        faction_grid[gy][gx] = faction
    return cube_grid, faction_grid


def placement_zone_boundaries(scenario_names, all_scenarios):
    """Tile-x boundaries between adjacent PLACERECT: zones, from whichever
    of scenario_names is the LAST to declare any placerects (matching the
    same last-write-wins convention as cube ops -- Great_Wall_Boss_Terrain's
    own PLACERECT: pair, boundary at x=24, supersedes Great_Wall_Terrain's
    x=26 pair for the boss output). Real in-game evidence this line exists
    at all: GameData/Great_Wall/Screenshots/GreatWall.png (pre-regen,
    recovered via `git show HEAD:...`) has a 1px-wide ~16%-white-blended
    vertical highlight in the open sky at exactly this x, sampled at
    multiple y rows (delta ~(37,34,24) over the sky gradient's own base
    color at every row checked -- consistent with a flat alpha blend, not a
    gradient-following overlay of its own)."""
    rects = None
    for sname in scenario_names:
        pr = all_scenarios[sname].get("placerects")
        if pr:
            rects = pr
    if not rects:
        return []
    rects = sorted(rects, key=lambda r: r[0])
    boundaries = []
    for a, b in zip(rects, rects[1:]):
        ax, aw = a[0], a[2]
        bx = b[0]
        if ax + aw == bx:
            boundaries.append(bx)
    return boundaries


def apply_lighting(canvas_rgba, is_air):
    """Reproduces ColourGrid.UpdateLighting + ApplyLightingGrid (see module
    docstring point 4) over the whole assembled native-resolution canvas at
    once. `is_air[y][x]` is True for a background/unfilled pixel. Mutates
    canvas_rgba in place."""
    H, W = len(is_air), len(is_air[0])
    SQRT2 = math.sqrt(2)
    dist = [[0.0] * W for _ in range(H)]
    for y in range(H):
        row_air, row_dist = is_air[y], dist[y]
        prev_dist = dist[y - 1] if y > 0 else None
        for x in range(W):
            if row_air[x]:
                row_dist[x] = 0.0
                continue
            if prev_dist is None:
                row_dist[x] = CAP
                continue
            best = CAP
            if x > 0:
                best = min(best, prev_dist[x - 1] + SQRT2)
            best = min(best, prev_dist[x] + 1.0)
            if x < W - 1:
                best = min(best, prev_dist[x + 1] + SQRT2)
            row_dist[x] = best

    px = canvas_rgba.load()
    for y in range(H):
        row_air, row_dist = is_air[y], dist[y]
        for x in range(W):
            if row_air[x]:
                continue
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            h_, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            L = row_dist[x]
            s = (L / CAP - s) * 0.09 + s
            v = (CAP - L) / CAP * 0.5 * (v * 0.9 + 0.1) + v * 0.5
            s, v = max(0.0, min(1.0, s)), max(0.0, min(1.0, v))
            nr, ng, nb = colorsys.hsv_to_rgb(h_, s, v)
            px[x, y] = (round(nr * 255), round(ng * 255), round(nb * 255), a)


DIVIDER_BLEND = 0.164  # fraction white-blended into whatever's underneath -- see placement_zone_boundaries' evidence


def render_grid(scenario_names, all_scenarios, w, h):
    cube_grid, faction_grid = build_native_grid(scenario_names, all_scenarios, w, h)

    canvas = Image.new("RGBA", (w * NATIVE_TILE, h * NATIVE_TILE), (0, 0, 0, 0))
    is_air = [[True] * (w * NATIVE_TILE) for _ in range(h * NATIVE_TILE)]
    for gy in range(h):
        for gx in range(w):
            tile = resolve_tile_rgba(cube_grid[gy][gx], faction_grid[gy][gx])
            if tile is None:
                continue
            canvas.paste(tile, (gx * NATIVE_TILE, gy * NATIVE_TILE), tile)
            tpx = tile.load()
            for ly in range(NATIVE_TILE):
                py = gy * NATIVE_TILE + ly
                row = is_air[py]
                for lx in range(NATIVE_TILE):
                    if tpx[lx, ly][3] != 0:
                        row[gx * NATIVE_TILE + lx] = False

    apply_lighting(canvas, is_air)

    out_w, out_h = w * NATIVE_TILE * SCALE, h * NATIVE_TILE * SCALE
    sky = Image.new("RGB", (out_w, out_h))
    for py in range(out_h):
        row_color = sky_color(py)
        for px in range(out_w):
            sky.putpixel((px, py), row_color)

    # Placement-zone divider: drawn into the sky layer BEFORE cube tiles are
    # pasted on top, so solid terrain naturally occludes it -- matches the
    # real screenshot, where the line is only visible through open sky, not
    # painted over the wall.
    sky_px = sky.load()
    for boundary_tile in placement_zone_boundaries(scenario_names, all_scenarios):
        line_x = boundary_tile * NATIVE_TILE * SCALE - 1
        if 0 <= line_x < out_w:
            for py in range(out_h):
                r, g, b = sky_px[line_x, py]
                sky_px[line_x, py] = (
                    round(r + (255 - r) * DIVIDER_BLEND),
                    round(g + (255 - g) * DIVIDER_BLEND),
                    round(b + (255 - b) * DIVIDER_BLEND),
                )

    upscaled = canvas.resize((out_w, out_h), Image.NEAREST)
    sky.paste(upscaled, (0, 0), upscaled)
    return sky


# (output_filename, [scenario names to composite, in order]) -- see module
# docstring for why a boss output includes the normal ground+player-leader
# scenarios too, and never the enemy-leader one.
GREAT_WALL_OUTPUTS = [
    ("GreatWall.png", ["Great_Wall_Terrain", "Battle_Normal_Player", "Battle_Normal_Enemy"]),
    ("GreatWall_Boss.png", ["Great_Wall_Terrain", "Great_Wall_Boss_Terrain", "Battle_Normal_Player"]),
]


def render_terrain_mod(map_file, out_dir, outputs, shared_map_file=None, mod_dir=None, mod_prefix=None):
    """mod_dir/mod_prefix (both required together) let a terrain's own
    ground TOKEN cubes -- when it isn't Extra_Mechanics itself -- resolve
    via `_mod_own_blocks()` above; omit both for a terrain whose ground
    cubes are all base-game ones (Great_Wall's own case)."""
    global _CURRENT_MOD
    _CURRENT_MOD = (mod_dir, mod_prefix)
    all_scenarios = parse_scenarios(map_file)
    if shared_map_file:
        all_scenarios.update({k: v for k, v in parse_scenarios(shared_map_file).items()
                               if k not in all_scenarios})
    os.makedirs(out_dir, exist_ok=True)
    for fname, scenario_names in outputs:
        w = all_scenarios[scenario_names[0]]["w"]
        h = all_scenarios[scenario_names[0]]["h"]
        im = render_grid(scenario_names, all_scenarios, w, h)
        im.convert("RGB").save(os.path.join(out_dir, fname))
        print(f"wrote {fname} ({w}x{h} tiles, {im.width}x{im.height}px)")


# Registered terrain mods -- mirrors render_preview_cards.py's own
# render_mod(...) call-list convention (see cube-chaos-mod-setup SKILL.md's
# "Each mod keeps its own README.md..." section for that convention's
# rationale): add a new render_terrain_mod(...) call here for a new terrain
# mod's own <Name>_Maps.c.txt rather than repointing GREAT_WALL_OUTPUTS.
# Every real terrain scenario's shared Battle_*_Player/Battle_*_Enemy leader
# partials live in Extra_Mechanics/Battle_Maps.c.txt regardless of which mod
# owns the terrain itself, so shared_map_file is the same for every entry.
SHARED_MAP_FILE = os.path.join(ROOT, "GameData", "Extra_Mechanics", "Battle_Maps.c.txt")

if __name__ == "__main__":
    render_terrain_mod(
        os.path.join(ROOT, "GameData", "Great_Wall", "Great_Wall_Maps.c.txt"),
        os.path.join(ROOT, "GameData", "Great_Wall", "Screenshots"),
        GREAT_WALL_OUTPUTS,
        shared_map_file=SHARED_MAP_FILE,
    )
