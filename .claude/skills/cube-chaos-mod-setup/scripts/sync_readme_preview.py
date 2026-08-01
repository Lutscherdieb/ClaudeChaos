"""Regenerate each per-mod README.md's Preview section (the <img> tag list
under `## Preview`) straight from the mod's OWN current .c.txt content and
whatever files render_preview_cards.py / render_terrain_screenshot.py most
recently wrote into Preview//Screenshots/ -- so that list can never silently
drift out of sync with the mod's real cubes/perks/curses/etc, the same
"recreatable from just the mod content" guarantee those two scripts already
give the PNG/GIF files themselves. Before this script existed, the <img> list
itself was hand-typed by whoever last edited the README -- easy to forget on
a quiet content edit, which is exactly the kind of staleness this repo's own
render_preview_cards.py/render_terrain_screenshot.py were already built to
prevent for the images themselves.

Usage (from the repo root, or anywhere -- paths below are absolute):
    python3 sync_readme_preview.py                # every opted-in mod
    python3 sync_readme_preview.py DJ Great_Wall   # only these mods

Scope, deliberately narrow (see cube-chaos-mod-setup SKILL.md's README
governance -- "create late, not at mod creation"): this script only ever
touches a mod that ALREADY has a README.md. Creating a brand-new README is a
deliberate, ask-first action a human (or Claude, after asking) takes once --
never something a hook silently does. Discovery needs no registration list at
all either (unlike render_preview_cards.py/render_terrain_screenshot.py's own
hardcoded per-mod call lists at the bottom of those files): every
`GameData/<X>/` folder that already has BOTH a `README.md` and a `Preview/`
folder is treated as opted in, full stop -- add a README once, the sync
happens forever after with zero registration step.

Only the region between `<!-- PREVIEW:START -->` / `<!-- PREVIEW:END -->` is
ever rewritten -- a mod's own hand-written intro paragraph(s) above that and
the closing `## Installing this mod` section below it are never touched. A
README predating this script has no markers yet: the first run locates the
existing `## Preview ... (next "## " heading or EOF)` block, replaces it, and
wraps the replacement in markers so every later run is a precise, safe
in-place swap instead of a heading-text guess.

Known simplifications versus the hand-written READMEs this replaces (all
cosmetic, never functional -- alt text has no in-game effect):
- Category order/headings are canonicalized (see CATEGORY_ORDER below) even
  where an older hand-written README used a different order or a slightly
  different heading spelling (e.g. DJ's old singular "Consumable" vs the
  plural "Consumables" every other mod already used) -- this canonicalization
  is the point: one predictable shape, not eight hand-drifted ones.
- A terrain's own battlefield Screenshots/*.png get an alt caption derived
  mechanically from the filename (camelCase/underscore -> spaced words), not
  the exact hand-picked wording an older README used (e.g. "Boss Battle" for
  a screenshot literally named `..._Boss.png`).

A CUBE's own companion animation gif(s) are NOT simplified, unlike the two
points above -- they keep the bespoke captioned <table> a human originally
hand-authored (DJ's "On Cube Creation" label for Speaker's Beat animation),
per cube-chaos-sprite-art/SKILL.md's own documented convention (width="70"
-- matches how big the icon actually renders inside the static card, not
the gif's native pixel size; plain unstyled <table>/<tr>/<td
valign="middle">, no inline style= -- GitHub's sanitizer strips it). A
2026-08-01 version of this script DID replace it with a plain wide <img
width="120">, reasoning the caption couldn't be mechanically derived from
the .c.txt -- reverted the same day once the width math turned out wrong too
(120 is nearly double the icon's actual ~70px on-card size) and the caption
turned out to just need a small hand-maintained lookup (ANIMATION_TRIGGER_
CAPTIONS below), the same one-time judgment call a human already made once
for Speaker. Update that dict whenever a new TRIGGER-animated cube is added;
a missing entry falls back to a generic caption plus a printed warning
(never a hard error -- this runs inside a non-blocking PostToolUse hook, so
a missing caption should be visible, not fatal to every other edit).

A DOUBLE-type animation (added 2026-08-01, see cube-chaos-sprite-art/
SKILL.md's own DOUBLE bullet and cube-chaos-scripting/references/
cube-animation.md) gets the same <table> treatment but a DIFFERENT default
caption -- its own animation name (e.g. "Shoot"), not an
ANIMATION_TRIGGER_CAPTIONS lookup -- since a DOUBLE's frame is picked from
live game state with no single trigger event to name; falling back to "On
Trigger" for one (the TRIGGER-only code path's original fallback) would be
actively wrong, not just generic. cube_animation_types() reads each cube's
real Animation: TYPE straight from its own .c.txt to tell the two apart --
no own-mod cube needs a hand-picked multi-state caption override yet (see
ThirdParty/Dinosaurs/render_dinosaurs_preview.py's DOUBLE_ANIMATION_STATES
for that pattern, third-party-only for now), so this script has no override
dict of its own; add one the same way if/when an own-mod cube needs it.
"""
import glob
import importlib.util
import os
import re
import sys

ROOT = r"e:\Programme\Steam\steamapps\common\Cube Chaos"
GAME_DATA = os.path.join(ROOT, "GameData")
BASE_GAME_DIRS = {"Base_Core", "Characters", "Main", "Extra_Mechanics", "Modding_Example"}

RENDER_PREVIEW_SCRIPT = os.path.join(
    ROOT, ".claude", "skills", "cube-chaos-sprite-art", "scripts", "render_preview_cards.py")


def _load_rpc():
    """Import render_preview_cards.py as a module so this script reuses its
    exact same parsing (parse_blocks/field/perks_source_basenames/PERK_HEADER/
    CUBE_HEADER) instead of re-deriving a second, potentially-drifting copy of
    those rules -- this script only needs ITEM NAMES/ORDER/IsUpgradeFrom, not
    the full rendered-image machinery, so it never calls that module's own
    builder/render_* functions."""
    spec = importlib.util.spec_from_file_location("render_preview_cards", RENDER_PREVIEW_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


RPC = _load_rpc()

PREVIEW_START = "<!-- PREVIEW:START -->"
PREVIEW_END = "<!-- PREVIEW:END -->"


def pretty(name):
    return name.replace("_", " ")


# Hand-authored per-(mod_prefix, cube_name, anim_name) caption describing
# WHEN a cube's own TRIGGER animation fires -- not mechanically derivable
# from the .c.txt (it's a judgment call about which ability the flourish is
# tied to, same call a human already made once for DJ's Speaker: "On Cube
# Creation", tied to the ability that creates its Note). See module
# docstring for why this exists instead of a plain <img>.
ANIMATION_TRIGGER_CAPTIONS = {
    ("DJ", "Speaker", "Beat"): "On Cube Creation",
}


def animation_table_lines(entries):
    """entries: list of (caption, rel_path, alt). Renders the <table>
    convention documented in cube-chaos-sprite-art/SKILL.md's "Rendering
    README preview cards" section -- plain unstyled table/tr/td (no inline
    style=, GitHub's README sanitizer strips it), valign="middle" on every
    cell, width="70" per gif (matches how big the icon actually renders
    inside the static card above it, not the gif's own native pixel size),
    2 (caption, gif) entries per row -- a lone trailing entry (the common
    case: most cubes have exactly one TRIGGER animation) just gets its own
    row, not padded with an empty cell."""
    lines = ["<table>"]
    for i in range(0, len(entries), 2):
        lines.append("<tr>")
        for caption, rel, alt in entries[i:i + 2]:
            lines.append(f'<td valign="middle">{caption}</td>')
            lines.append(f'<td valign="middle"><img src="{rel}" width="70" alt="{alt}"></td>')
        lines.append("</tr>")
    lines.append("</table>")
    return lines


def discover_mods():
    """Every GameData/<X>/ with both a README.md and a Preview/ folder --
    see module docstring's "Scope" section for why this needs no separate
    registration list the way the image/screenshot regen scripts do."""
    mods = []
    for name in sorted(os.listdir(GAME_DATA)):
        if name in BASE_GAME_DIRS:
            continue
        mod_dir = os.path.join(GAME_DATA, name)
        if not os.path.isdir(mod_dir):
            continue
        if os.path.exists(os.path.join(mod_dir, "README.md")) and \
           os.path.isdir(os.path.join(mod_dir, "Preview")):
            mods.append(name)
    return mods


def is_icon_only_helper(header_match, block_lines):
    """A CUBE: block that's pure sprite-swap plumbing (see
    render_preview_cards.py's find_referenced_cubes docstring on
    SetSpriteToCube targets, e.g. General's Bomber_West/Shell_Arc): TOKEN,
    zero mana/hp/maxhp, and no Ability: line of its own -- nothing a real
    tooltip card would show, and not a cube a player ever sees as itself,
    only as another cube's directional/arc reskin. render_preview_cards.py
    still renders a (near-blank) card for it -- this only controls whether
    the README's own list bothers linking that card. A real 0/0/0 no-ability
    TOKEN cube that's still meant to be seen (e.g. DJ's own `Record`) always
    has nonzero hp/maxhp, so this stays narrow rather than excluding every
    ability-less TOKEN cube."""
    mana, hp, maxhp = int(header_match.group(2)), int(header_match.group(3)), int(header_match.group(4))
    if mana or hp or maxhp:
        return False
    if any(l.strip().startswith("Ability:") for l in block_lines):
        return False
    return any(l.strip() == "TOKEN" for l in block_lines)


def gather_simple_category(mod_dir, prefix, category):
    """Cubes/Curses/Consumables/CubeUpgrades/TerrainPerks/Synergies all share
    this shape: one `<Prefix>_<Category>.c.txt`, blocks in file order, no
    IsUpgradeFrom chain to resolve. Returns [] if the mod has no file for
    this category (same as render_preview_cards.py's own per-category skip)."""
    header_re = RPC.CUBE_HEADER if category == "Cubes" else RPC.PERK_HEADER
    path = os.path.join(mod_dir, f"{prefix}_{category}.c.txt")
    if not os.path.exists(path):
        return []
    blocks = RPC.parse_blocks(path, header_re)
    if category == "Cubes":
        blocks = [b for b in blocks if not is_icon_only_helper(b["header"], b["lines"])]
    return [b["header"].group(1) for b in blocks]


def gather_perks(mod_dir, prefix):
    """Perks (+ Neutral, folded into the same README heading) -- mirrors
    render_preview_cards.py's build_perks(): perks_source_basenames() decides
    whether to read `_Species.c.txt`, `_Perks.c.txt`, or both, plus an
    optional dedicated `_UpgradePerks.c.txt`. Each item also records whether
    its own block declares `BelongsTo: CLASS`/`BelongsTo: SPECIES` (for the
    "class/species perk card" alt-text special case) and its immediate
    IsUpgradeFrom: target, if any (one hop only -- same as the real card's
    own "(Upgrade of X)" line, not the fully-resolved chain)."""
    RPC.MOD_DIR, RPC.MOD_PREFIX = mod_dir, prefix
    items = []

    def collect(blocks, file_category):
        for b in blocks:
            name = b["header"].group(1)
            belongs_to = None
            if any(l.strip() == "BelongsTo: CLASS" for l in b["lines"]):
                belongs_to = "class"
            elif any(l.strip() == "BelongsTo: SPECIES" for l in b["lines"]):
                belongs_to = "species"
            upgrade_of = RPC.field(b["lines"], "IsUpgradeFrom:")
            items.append({
                "name": name,
                "belongs_to": belongs_to,
                "upgrade_of": upgrade_of.split()[0] if upgrade_of else None,
                # The actual `<Prefix>_<X>_<Name>.png` file render_preview_cards.py
                # wrote this item under -- "Perks" for every basename/UpgradePerks
                # item regardless of which source file it came from (that script
                # registers ALL of them under one "Perks" BUILDERS key), but
                # "Neutral" for a Neutral perk (a separate BUILDERS key/output
                # prefix) even though it's folded into this README's own "Perks"
                # heading. Using the README heading's category instead of this
                # per-item source category was a real bug caught by testing
                # against Home_Turf_Advantage: it produced an <img> pointing at a
                # `..._Perks_...png` file that render_preview_cards.py never wrote.
                "file_category": file_category,
            })

    for basename in RPC.perks_source_basenames():
        collect(RPC.parse_blocks(os.path.join(mod_dir, f"{prefix}_{basename}.c.txt"), RPC.PERK_HEADER),
                "Perks")

    upgrade_path = os.path.join(mod_dir, f"{prefix}_UpgradePerks.c.txt")
    if os.path.exists(upgrade_path):
        collect(RPC.parse_blocks(upgrade_path, RPC.PERK_HEADER), "Perks")

    neutral_path = os.path.join(mod_dir, f"{prefix}_Neutral.c.txt")
    if os.path.exists(neutral_path):
        collect(RPC.parse_blocks(neutral_path, RPC.PERK_HEADER), "Neutral")

    return interleave_upgrades(items)


def interleave_upgrades(items):
    """Place each upgrade item immediately after its own base item
    (recursively, so a 3-hop chain like Mk3->Mk2->Mk1 reads Mk1, Mk2, Mk3 in
    a row), regardless of which source file it was actually collected from.
    Every hand-written README already reads this way -- a mod that keeps its
    upgrades inline in the same file as their base (e.g. DJ) gets this for
    free from file order alone, but a mod using the dedicated
    `_UpgradePerks.c.txt` file (e.g. General) previously had every upgrade
    dumped at the end of the whole list instead of next to its own base,
    since that file is collected as a separate, later batch."""
    by_name = {i["name"]: i for i in items}
    children = {}
    for i in items:
        if i["upgrade_of"] and i["upgrade_of"] in by_name:
            children.setdefault(i["upgrade_of"], []).append(i)

    ordered, placed = [], set()

    def emit(item):
        ordered.append(item)
        placed.add(item["name"])
        for child in children.get(item["name"], []):
            emit(child)

    for i in items:
        if not i["upgrade_of"] or i["upgrade_of"] not in by_name:
            emit(i)
    # Any item whose upgrade_of target isn't itself in this list (shouldn't
    # happen for well-formed content) still gets shown, appended at the end,
    # rather than silently dropped.
    for i in items:
        if i["name"] not in placed:
            emit(i)
    return ordered


def img_tag(rel_path, width, alt):
    return f'<img src="{rel_path}" width="{width}" alt="{alt}">'


def cube_animation_gifs(mod_dir, prefix, cube_name):
    """This cube's own companion trigger-animation gif(s), if any (see
    render_preview_cards.py's build_cube_animation_gifs) -- a real, separate
    file next to the cube's own static card, not the card itself animated
    (unlike an IsUpgradeFrom: perk's shine-sweep gif, which replaces its own
    card in place)."""
    pattern = os.path.join(mod_dir, "Preview", f"{prefix}_Cubes_{cube_name}_*.gif")
    out = []
    for path in sorted(glob.glob(pattern)):
        fname = os.path.basename(path)
        stem = fname[:-len(".gif")]
        anim_name = stem[len(f"{prefix}_Cubes_{cube_name}_"):]
        out.append((fname, anim_name))
    return out


def cube_animation_types(mod_dir, prefix):
    """cube_name -> {anim_name: atype}, read directly from <Prefix>_Cubes.c.txt --
    lets the caption-selection logic below tell a TRIGGER animation (needs a
    real ANIMATION_TRIGGER_CAPTIONS entry, since its caption names a specific
    in-game event) apart from a DOUBLE one (whose correct default caption is
    just its own animation name, not a "missing caption" warning -- a DOUBLE's
    frame is picked from live game state with no single trigger event to name,
    see cube-chaos-scripting/references/cube-animation.md's "which type to
    pick" section). Without this check, a future own-mod DOUBLE-animated cube
    would silently get the wrong "On Trigger" fallback caption, which doesn't
    even make sense for a DOUBLE (there is no trigger)."""
    path = os.path.join(mod_dir, f"{prefix}_Cubes.c.txt")
    if not os.path.exists(path):
        return {}
    out = {}
    for b in RPC.parse_blocks(path, RPC.CUBE_HEADER):
        cube_name = b["header"].group(1)
        for anim_name, atype, effect, rest in RPC.parse_animation_lines(b["lines"]):
            out.setdefault(cube_name, {})[anim_name] = atype
    return out


CAMEL_RE = re.compile(r'(?<!^)(?=[A-Z])')


def humanize_screenshot_stem(stem):
    """Best-effort spacing for a Screenshots/*.png filename with no
    guaranteed word-separator convention (existing screenshots are plain
    CamelCase, e.g. `GreatWall_Boss.png`) -- see module docstring's "Known
    simplifications" for why this won't always match an older hand-picked
    caption verbatim."""
    spaced = stem.replace("_", " ")
    spaced = CAMEL_RE.sub(" ", spaced)
    return re.sub(r'\s+', ' ', spaced).strip()


CATEGORY_ORDER = [
    ("Cubes", "Cubes"),
    ("Perks", "Perks"),
    ("Curses", "Curses"),
    ("Consumables", "Consumables"),
    ("CubeUpgrades", "Cube Upgrades"),
    ("TerrainPerks", "Terrain"),
    ("Synergies", "Class+Species synergies"),
]


def build_section(mod_dir, prefix):
    sprite_dir = os.path.join(mod_dir, "Sprites")
    sheet_count = len(glob.glob(os.path.join(sprite_dir, "*.c.png"))) if os.path.isdir(sprite_dir) else 0
    original_word = "original" if sheet_count == 1 else "originals"

    lines = [f"## Preview — {prefix} mod content", "",
             "Each card below is rendered to match the game's own in-game tooltip style. "
             f"Full-resolution sprite sheet {original_word} {'is' if sheet_count == 1 else 'are'} in `Sprites/`.",
             ""]

    anim_types = cube_animation_types(mod_dir, prefix)
    any_category = False
    for category, heading in CATEGORY_ORDER:
        if category == "Perks":
            items = gather_perks(mod_dir, prefix)
        else:
            items = gather_simple_category(mod_dir, prefix, category)
        if not items:
            continue
        any_category = True
        lines.append(f"### {heading}")
        lines.append("")
        for item in items:
            name = item if isinstance(item, str) else item["name"]
            title = pretty(name)
            # Perks/Neutral share one README heading but two different real
            # output-file prefixes (see gather_perks' "file_category" note) --
            # every other category's file prefix always matches its own
            # README heading category, so file_category falls back to it.
            file_category = item["file_category"] if isinstance(item, dict) and "file_category" in item else category
            gif_path = os.path.join(mod_dir, "Preview", f"{prefix}_{file_category}_{name}.gif")
            ext = "gif" if os.path.exists(gif_path) else "png"
            rel = f"Preview/{prefix}_{file_category}_{name}.{ext}"

            if category == "Cubes":
                alt = f"{title} cube card"
            elif category == "Perks":
                belongs_to = item["belongs_to"]
                alt = f"{title} {belongs_to} perk card" if belongs_to else f"{title} perk card"
            elif category == "Curses":
                alt = f"{title} curse card"
            elif category == "Consumables":
                alt = f"{title} consumable card"
            elif category == "CubeUpgrades":
                alt = f"{title} card"
            elif category == "TerrainPerks":
                alt = f"{title} terrain perk card"
            elif category == "Synergies":
                a, _, b_ = name.partition("-")
                alt = f"{pretty(a)} + {pretty(b_)} synergy card"
            else:
                alt = f"{title} card"

            if not isinstance(item, str) and item.get("upgrade_of"):
                alt += f" (upgrade of {pretty(item['upgrade_of'])})"

            lines.append(img_tag(rel, 700, alt))

            if category == "Cubes":
                anims = cube_animation_gifs(mod_dir, prefix, name)
                if anims:
                    entries = []
                    for fname, anim_name in anims:
                        atype = anim_types.get(name, {}).get(anim_name)
                        if atype == "DOUBLE":
                            # No "missing caption" warning here -- a DOUBLE's
                            # correct default IS just its own animation name
                            # (see cube_animation_types' docstring), not a
                            # gap that needs a hand-authored entry the way a
                            # TRIGGER's real trigger-condition caption does.
                            caption = pretty(anim_name)
                        else:
                            caption = ANIMATION_TRIGGER_CAPTIONS.get((prefix, name, anim_name))
                            if caption is None:
                                print(f"WARNING: no trigger caption for {prefix}/{name}/{anim_name} -- "
                                      f"add one to ANIMATION_TRIGGER_CAPTIONS in sync_readme_preview.py")
                                caption = "On Trigger"
                        alt = f"{title} {pretty(anim_name)} animation"
                        entries.append((caption, f"Preview/{fname}", alt))
                    lines.extend(animation_table_lines(entries))

        if category == "TerrainPerks":
            shots_dir = os.path.join(mod_dir, "Screenshots")
            if os.path.isdir(shots_dir):
                for path in sorted(glob.glob(os.path.join(shots_dir, "*.png"))):
                    fname = os.path.basename(path)
                    stem = fname[:-len(".png")]
                    caption = humanize_screenshot_stem(stem)
                    lines.append(img_tag(f"Screenshots/{fname}", 700, f"{caption} - terrain, in game"))

        lines.append("")

    if not any_category:
        lines.append("_(no content yet)_")
        lines.append("")

    return "\n".join(lines).rstrip("\n")


PREVIEW_HEADING_RE = re.compile(r'(^## Preview.*?)(?=\n## |\Z)', re.S | re.M)


def sync_one(mod_dir, prefix):
    readme_path = os.path.join(mod_dir, "README.md")
    text = open(readme_path, encoding="utf-8").read()
    new_block = build_section(mod_dir, prefix)
    wrapped = f"{PREVIEW_START}\n{new_block}\n{PREVIEW_END}"

    if PREVIEW_START in text and PREVIEW_END in text:
        pre, rest = text.split(PREVIEW_START, 1)
        _, post = rest.split(PREVIEW_END, 1)
        new_text = pre + wrapped + post
    else:
        m = PREVIEW_HEADING_RE.search(text)
        if not m:
            print(f"skip {prefix}: no '## Preview' heading found and no markers either "
                  f"-- README doesn't match the expected shape, not touching it")
            return False
        new_text = text[:m.start()] + wrapped + "\n\n" + text[m.end():].lstrip("\n")

    if new_text != text:
        with open(readme_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(new_text)
        print(f"synced {prefix}/README.md")
        return True
    print(f"unchanged {prefix}/README.md")
    return False


if __name__ == "__main__":
    requested = sys.argv[1:]
    mods = requested if requested else discover_mods()
    for prefix in mods:
        mod_dir = os.path.join(GAME_DATA, prefix)
        if not os.path.isdir(mod_dir):
            print(f"skip {prefix}: no such GameData folder")
            continue
        if not os.path.exists(os.path.join(mod_dir, "README.md")):
            print(f"skip {prefix}: no README.md yet (create one first -- see "
                  f"cube-chaos-mod-setup's README governance)")
            continue
        sync_one(mod_dir, prefix)
