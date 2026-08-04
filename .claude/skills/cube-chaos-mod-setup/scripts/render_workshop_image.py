"""Generate a mod's `GameData/<Mod>/Image.png` -- the Steam Workshop thumbnail
(see cube-chaos-mod-setup/references/workshop-publishing.md, requirement 1) --
mechanically from the mod's OWN namesake perk icon, so it can never drift out of
sync with the sprite it's supposed to be a blow-up of.

Usage (from anywhere -- paths below are absolute):
    python3 render_workshop_image.py             # every discoverable mod
    python3 render_workshop_image.py Broker DJ   # only these mods

Why this exists as a script rather than prose: the recipe (crop tile (0,0),
strip the 1px magenta guide ring, 20x nearest-neighbour upscale) was documented
in workshop-publishing.md and executed by hand three times (DJ/General/Unholy,
2026-07-25). By 2026-08-04 Crusader's Image.png had gone stale against a later
sprite touch-up (commit 3b0746d) with nothing to catch it, and four newer mods
had no Image.png at all -- exactly the "recreatable from mod content" guarantee
render_preview_cards.py/sync_readme_preview.py already give everything else.
Re-run this after ANY edit to a mod's namesake perk tile.

Source selection: the mod's namesake `PERK:` block, which must be the FIRST
`PERK:` in its own file (so it lands on sprite tile (0,0)). "Namesake" compares
the perk name to the folder name with `_` and `-` treated as equivalent, which
covers both the plain case (`PERK: Broker` in `GameData/Broker/`) and a
synergy-bridge mod (`PERK: DJ-Voidling` in `GameData/DJ_Voidling/`). Workshop
publishing docs previously called Great_Wall and DJ_Voidling "needs a human
call" because neither is a class/species mod -- in practice each has exactly one
distinguishing perk icon sitting at (0,0), so the same rule covers them with no
special-casing (verified 2026-08-04).

The guide-ring strip is verified, not assumed: if a sheet's outer 1px ring
isn't uniformly the magenta RGB(255,0,220) guide colour from
cube-chaos-sprite-art's border-pattern library, this refuses to strip it and
says so, rather than silently cropping a pixel of real art off every side.
"""
import os
import re
import sys

from PIL import Image

ROOT = r"e:\Programme\Steam\steamapps\common\Cube Chaos"
GAME_DATA = os.path.join(ROOT, "GameData")
BASE_GAME_DIRS = {"Base_Core", "Characters", "Main", "Extra_Mechanics", "Modding_Example"}

TILE = 27                      # cube-chaos-sprite-art's fixed tile size
GUIDE_COLOUR = (255, 0, 220)   # the universal magenta guide ring
SCALE = 20                     # 25px content * 20 = a 500x500 Workshop thumbnail

PERK_HEADER = re.compile(r'^PERK:\s+(\S+)', re.M)


def normalize(name):
    """`_` and `-` are interchangeable when matching a perk to its mod folder --
    a synergy-bridge mod's perk is `DJ-Voidling` but its folder is `DJ_Voidling`."""
    return name.replace("-", "_").lower()


def find_namesake_sheet(mod_dir, mod_name):
    """-> (sprite_sheet_path, perk_name) for the mod's namesake perk, or None.

    Only the FIRST `PERK:` of each file is considered: sprite tiles are assigned
    by pure file order, so only the first block is guaranteed to sit at tile
    (0,0), which is the tile this script crops."""
    want = normalize(mod_name)
    for fname in sorted(os.listdir(mod_dir)):
        if not fname.endswith(".c.txt"):
            continue
        text = open(os.path.join(mod_dir, fname), encoding="utf-8", errors="replace").read()
        m = PERK_HEADER.search(text)
        if not m or normalize(m.group(1)) != want:
            continue
        sheet = os.path.join(mod_dir, "Sprites", fname[:-len(".c.txt")] + ".c.png")
        if os.path.exists(sheet):
            return sheet, m.group(1)
    return None


def has_guide_ring(tile):
    """True only if every pixel of the outer 1px ring is the guide colour."""
    w, h = tile.size
    ring = [tile.getpixel((x, y)) for x in range(w) for y in range(h)
            if x in (0, w - 1) or y in (0, h - 1)]
    return all(px == GUIDE_COLOUR for px in ring)


def render_one(mod_name):
    mod_dir = os.path.join(GAME_DATA, mod_name)
    if not os.path.isdir(mod_dir):
        print(f"skip {mod_name}: no such GameData folder")
        return False

    found = find_namesake_sheet(mod_dir, mod_name)
    if not found:
        print(f"skip {mod_name}: no sprite sheet whose FIRST `PERK:` block is named "
              f"`{mod_name}` -- pick a source tile by hand (see workshop-publishing.md)")
        return False
    sheet_path, perk_name = found

    tile = Image.open(sheet_path).convert("RGB").crop((0, 0, TILE, TILE))
    if has_guide_ring(tile):
        tile = tile.crop((1, 1, TILE - 1, TILE - 1))
    else:
        print(f"WARNING {mod_name}: tile (0,0) of {os.path.basename(sheet_path)} has no "
              f"uniform {GUIDE_COLOUR} guide ring -- keeping all {TILE}px rather than "
              f"cropping real art; check the tile's border")

    size = tile.size[0] * SCALE
    out_path = os.path.join(mod_dir, "Image.png")
    tile.resize((size, size), Image.NEAREST).save(out_path)
    print(f"wrote {mod_name}/Image.png  ({size}x{size}, from `PERK: {perk_name}` "
          f"in {os.path.basename(sheet_path)})")
    return True


def discover_mods():
    return [n for n in sorted(os.listdir(GAME_DATA))
            if n not in BASE_GAME_DIRS and os.path.isdir(os.path.join(GAME_DATA, n))]


if __name__ == "__main__":
    for mod in (sys.argv[1:] or discover_mods()):
        render_one(mod)
