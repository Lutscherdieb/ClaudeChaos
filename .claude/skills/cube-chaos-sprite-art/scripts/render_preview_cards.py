"""Render a mod's CUBE:/PERK: content as preview images styled like the
game's own in-game tooltip cards (name, rule text, value, and the real
sprite icon with its category border), instead of a bare sprite-sheet grid.
Output lands in the mod's own GameData/<Mod>/Preview/ folder, for that mod's
own GameData/<Mod>/README.md to embed.

Usage (from the repo root, or anywhere -- paths below are absolute):
    python3 render_preview_cards.py

Regenerate whenever a mod's content or sprites change and its README preview
images need to stay in sync. Edit MOD_DIR/OUT_DIR/MOD_PREFIX below to reuse
for another mod folder.

Card design notes (reverse-engineered once so future regens don't redo this):
- Font: GeneralData/dogicapixel.ttf -- confirmed (not guessed) as the game's
  actual UI font, hardcoded by name in the game's own compiled TextPrinter
  class.
- The outer 1px magenta (255,0,220) ring baked into PERK sprite tiles is an
  invisible editing guide, NOT rendered in-game -- strip it (crop 1px in on
  all sides) before upscaling for style-1 (plain class border, e.g. all DJ
  perks) and style-2 ("clean 3-ring", e.g. Curses/Consumables) tiles. Do NOT
  strip it for CLASSSPECIES synergy tiles -- their fancy jagged frame (style
  4) genuinely renders that outer ring; and CUBE icons (17x17) have no guide
  ring to strip at all. See the main SKILL.md's border pattern library for
  the full styles 1-4 reference.
- The engine auto-colors the literal word "mana" blue in tooltip text
  (confirmed via the compiled TextPrinter's Player.ManaColour reference) --
  replicated here as the one keyword auto-colored; no other keyword-coloring
  rule could be confirmed from data files, so everything else stays white.
- An `IsUpgradeFrom:` perk has no sprite slot of its own (engine reuses the
  base perk's icon) -- look up the base perk's icon index instead of the
  upgrade's own (blank) slot. The base game itself never mixes upgrade and
  regular perks in one file -- upgrades live in a separate, sprite-less
  `..._UpgradePerks.c.txt` (see SKILL.md's "Upgrade perks live in their own
  sprite-less file" section) -- so this script reads that file too, if
  present, and resolves each upgrade's icon by walking its `IsUpgradeFrom:`
  chain until it lands on a name with a real slot in the main sheet (a chain
  can be several hops long, e.g. Mk3 upgrades from Mk2 which upgrades from
  the real base perk -- resolving only one hop was a real bug here, fixed
  alongside adding the separate-file support).
"""
import math
import os
import re
from PIL import Image, ImageDraw, ImageFont

ROOT = r"e:\Programme\Steam\steamapps\common\Cube Chaos"
MOD_DIR = os.path.join(ROOT, "GameData", "DJ")
SPRITES = os.path.join(MOD_DIR, "Sprites")
FONT_PATH = os.path.join(ROOT, "GeneralData", "dogicapixel.ttf")
OUT_DIR = os.path.join(MOD_DIR, "Preview")  # lives with the mod, e.g. for GameData/DJ/README.md
MOD_PREFIX = "DJ"  # this mod's .c.txt/.c.png basename prefix

# Grid columns are derived from the actual tile count (ceil(sqrt(n)), matching
# the game's own square-sheet convention -- see SKILL.md) rather than
# hardcoded per category, so this script works unmodified for any mod's own
# tile counts, not just DJ's.
def grid_cols(n):
    return max(1, math.ceil(math.sqrt(n)))

BG = (0, 0, 0)
WHITE = (255, 255, 255)
MANA_BLUE = (80, 140, 255)

TILE_PERK = 27
TILE_CUBE = 17

W = 1500
MARGIN = 40
TOP_MARGIN = 24
BOTTOM_MARGIN = 24
TITLE_SIZE = 40
BODY_SIZE = 22
LINE_GAP = 10
TITLE_GAP = 16
PAD_BETWEEN_CARDS = 14

PERK_HEADER = re.compile(r"^PERK:\s*(\S+)")
CUBE_HEADER = re.compile(r"^CUBE:\s*(\S+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)")


def font(size):
    return ImageFont.truetype(FONT_PATH, size)


def load_sheet(name):
    return Image.open(os.path.join(SPRITES, name)).convert("RGB")


def crop_icon(sheet, index, tile, grid_cols, strip_guide):
    row, col = divmod(index, grid_cols)
    ox, oy = col * tile, row * tile
    im = sheet.crop((ox, oy, ox + tile, oy + tile))
    if strip_guide:
        im = im.crop((1, 1, tile - 1, tile - 1))
    return im


def upscale(im, scale):
    return im.resize((im.width * scale, im.height * scale), Image.NEAREST)


def parse_blocks(path, header_re):
    """Split a .c.txt file into top-level CUBE:/PERK: blocks. Nested action
    chains never emit a bare 'End' line of their own (only inline '... End'
    terminators on Text:/Description: fields), so matching a standalone
    'End' line reliably closes each top-level block."""
    lines = open(path, encoding="utf-8").read().split("\n")
    blocks, cur = [], None
    for line in lines:
        m = header_re.match(line)
        if m:
            if cur is not None:
                blocks.append(cur)
            cur = {"header": m, "lines": []}
        elif cur is not None:
            if line.strip() == "End":
                blocks.append(cur)
                cur = None
            else:
                cur["lines"].append(line)
    if cur is not None:
        blocks.append(cur)
    return blocks


def field(lines, prefix):
    for l in lines:
        if l.startswith(prefix):
            content = l[len(prefix):].strip()
            if content.endswith(" End"):
                content = content[:-4].strip()
            elif content == "End":
                content = ""
            return content
    return None


def all_top_level(lines, prefix):
    """Only unindented (column-0) lines -- these are a CUBE's own per-ability
    Text: fields. Nested Text-like strings inside an Ability: chain (e.g. a
    granted sub-ability's own tooltip) are always indented, so this filter
    naturally excludes them without needing to track nesting depth."""
    out = []
    for l in lines:
        if l.startswith(prefix):
            content = l[len(prefix):].strip()
            if content.endswith(" End"):
                content = content[:-4].strip()
            out.append(content)
    return out


def text_width(d, s, f):
    bbox = d.textbbox((0, 0), s, font=f)
    return bbox[2] - bbox[0]


def wrap_to_width(d, s, f, max_width):
    words, lines, cur = s.split(" "), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_width(d, trial, f) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def wrap_paragraph(d, s, f, max_width):
    if s == "":
        return [""]
    # "\N" is the game's own real forced-line-break marker inside Text:/
    # Description: fields (confirmed via real base-game usage, e.g.
    # Main/3GeneralCubes.c.txt) -- split on it first so each point renders
    # as its own line here too, matching what the actual tooltip shows,
    # rather than printing the two literal characters "\N".
    lines = []
    for segment in s.split("\\N"):
        segment = segment.strip()
        if segment.startswith("- "):
            hang = "  "
            hang_w = text_width(d, hang, f)
            wrapped = wrap_to_width(d, segment[2:], f, max_width - hang_w)
            lines.extend(("- " if i == 0 else hang) + line for i, line in enumerate(wrapped))
        else:
            lines.extend(wrap_to_width(d, segment, f, max_width))
    return lines


def draw_colored_line(d, pos, s, f, default_color):
    x, y = pos
    for part in re.split(r'(\bmana\b)', s, flags=re.IGNORECASE):
        if not part:
            continue
        color = MANA_BLUE if part.lower() == "mana" else default_color
        d.text((x, y), part, font=f, fill=color)
        x += text_width(d, part, f)


def humanize(s):
    """Body text embeds identifiers verbatim from the DSL source -- cube/perk
    names (Drop_Helicopter) and registered tooltip keywords
    (left_side_position) alike -- as underscored tokens. Replace underscores
    with spaces for readability, same as pretty() already does for titles;
    this is a documentation-readability choice for these cards, not a claim
    about exactly how the compiled game's own tooltip renderer displays it."""
    return s.replace("_", " ")


def render_card(title, description, value, icon_img, extra_lines=None):
    dummy = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    f_title, f_body = font(TITLE_SIZE), font(BODY_SIZE)

    icon_w, icon_h = icon_img.size
    text_area_w = W - MARGIN - 30 - icon_w - MARGIN

    body_lines = []
    if extra_lines:
        for p in extra_lines:
            body_lines.extend(wrap_paragraph(dummy, humanize(p), f_body, text_area_w))
    if description:
        body_lines.extend(wrap_paragraph(dummy, humanize(description), f_body, text_area_w))

    text_block_h = TITLE_SIZE + TITLE_GAP + len(body_lines) * (BODY_SIZE + LINE_GAP)
    icon_block_h = icon_h + ((BODY_SIZE + 16) if value is not None else 0)
    H = TOP_MARGIN + max(text_block_h, icon_block_h) + BOTTOM_MARGIN

    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)

    icon_x = W - MARGIN - icon_w
    icon_y = TOP_MARGIN + (max(text_block_h, icon_block_h) - icon_block_h) // 2
    im.paste(icon_img, (icon_x, icon_y))

    if value is not None:
        val_s = f"VALUE: {value}"
        vw = text_width(d, val_s, f_body)
        d.text((icon_x + icon_w - vw, icon_y + icon_h + 8), val_s, font=f_body, fill=WHITE)

    d.text((MARGIN, TOP_MARGIN), title.upper(), font=f_title, fill=WHITE)

    y = TOP_MARGIN + TITLE_SIZE + TITLE_GAP
    for line in body_lines:
        draw_colored_line(d, (MARGIN, y), line, f_body, WHITE)
        y += BODY_SIZE + LINE_GAP

    return im


def pretty(name):
    return name.replace("_", " ").upper()


def build_curses():
    blocks = parse_blocks(os.path.join(MOD_DIR, f"{MOD_PREFIX}_Curses.c.txt"), PERK_HEADER)
    sheet = load_sheet(f"{MOD_PREFIX}_Curses.c.png")
    cols = grid_cols(len(blocks))
    cards = []
    for i, b in enumerate(blocks):
        name = b["header"].group(1)
        desc = field(b["lines"], "Description:")
        val = field(b["lines"], "Value:")
        icon = upscale(crop_icon(sheet, i, TILE_PERK, cols, strip_guide=True), 7)
        cards.append((name, render_card(pretty(name), desc, val, icon)))
    return cards


def build_consumables():
    blocks = parse_blocks(os.path.join(MOD_DIR, f"{MOD_PREFIX}_Consumables.c.txt"), PERK_HEADER)
    sheet = load_sheet(f"{MOD_PREFIX}_Consumables.c.png")
    cols = grid_cols(len(blocks))
    cards = []
    for i, b in enumerate(blocks):
        name = b["header"].group(1)
        desc = field(b["lines"], "Description:")
        val = field(b["lines"], "Value:")
        icon = upscale(crop_icon(sheet, i, TILE_PERK, cols, strip_guide=True), 7)
        cards.append((name, render_card(pretty(name), desc, val, icon)))
    return cards


def build_synergies():
    blocks = parse_blocks(os.path.join(MOD_DIR, f"{MOD_PREFIX}_Synergies.c.txt"), PERK_HEADER)
    sheet = load_sheet(f"{MOD_PREFIX}_Synergies.c.png")
    cols = grid_cols(len(blocks))
    cards = []
    for i, b in enumerate(blocks):
        name = b["header"].group(1)
        desc = field(b["lines"], "Description:")
        icon = upscale(crop_icon(sheet, i, TILE_PERK, cols, strip_guide=False), 6)
        title = name.replace("_", " ").replace("-", " + ").upper()
        cards.append((name, render_card(title, desc, None, icon)))
    return cards


def build_perks():
    blocks = parse_blocks(os.path.join(MOD_DIR, f"{MOD_PREFIX}_Perks.c.txt"), PERK_HEADER)
    sheet = load_sheet(f"{MOD_PREFIX}_Perks.c.png")
    cols = grid_cols(len(blocks))
    name_to_idx = {b["header"].group(1): i for i, b in enumerate(blocks)}

    # Upgrades live in their own sprite-less file, matching base-game
    # convention (e.g. ZUpgradeClassPerks.c.txt) -- read it too, if present.
    upgrade_path = os.path.join(MOD_DIR, f"{MOD_PREFIX}_UpgradePerks.c.txt")
    upgrade_blocks = parse_blocks(upgrade_path, PERK_HEADER) if os.path.exists(upgrade_path) else []
    upgrade_by_name = {b["header"].group(1): b for b in upgrade_blocks}

    def resolve_icon_idx(target_name, seen=frozenset()):
        # Walk the IsUpgradeFrom chain -- an upgrade can itself be the base
        # of a further upgrade (e.g. Mk3 -> Mk2 -> the real Mk1 perk) -- until
        # landing on a name with a real slot in the main sheet.
        if target_name in name_to_idx:
            return name_to_idx[target_name]
        if target_name in seen or target_name not in upgrade_by_name:
            raise KeyError(f"Cannot resolve icon: no real perk at the end of the "
                            f"IsUpgradeFrom chain starting at {target_name!r}")
        next_target = field(upgrade_by_name[target_name]["lines"], "IsUpgradeFrom:").split()[0]
        return resolve_icon_idx(next_target, seen | {target_name})

    def render_block(b, icon_idx):
        name = b["header"].group(1)
        # A PERK's Description: is a single whole-perk field (unlike CUBE's
        # per-Ability Text:, which stacks) -- multiple Ability: lines share
        # one Description at the end, each with its own AbilityText: instead.
        # Fall back to the first AbilityText: if a perk has no top-level
        # Description: of its own.
        desc = field(b["lines"], "Description:") or field(b["lines"], "AbilityText:")
        upgrade_of = field(b["lines"], "IsUpgradeFrom:")
        extra = [f"(Upgrade of {upgrade_of.split()[0].replace('_', ' ')})"] if upgrade_of else None
        icon = upscale(crop_icon(sheet, icon_idx, TILE_PERK, cols, strip_guide=True), 7)
        return name, render_card(pretty(name), desc, None, icon, extra_lines=extra)

    cards = [render_block(b, i) for i, b in enumerate(blocks)]
    for b in upgrade_blocks:
        base_name = field(b["lines"], "IsUpgradeFrom:").split()[0]
        cards.append(render_block(b, resolve_icon_idx(base_name)))
    return cards


def build_cubes():
    blocks = parse_blocks(os.path.join(MOD_DIR, f"{MOD_PREFIX}_Cubes.c.txt"), CUBE_HEADER)
    sheet = load_sheet(f"{MOD_PREFIX}_Cubes.c.png")
    cols = grid_cols(len(blocks))
    cards = []
    for i, b in enumerate(blocks):
        h = b["header"]
        name, mana, hp, maxhp = h.group(1), int(h.group(2)), int(h.group(3)), int(h.group(4))
        is_token = any(l.strip() == "TOKEN" for l in b["lines"])
        texts = all_top_level(b["lines"], "Text:")
        stat_bits = [f"Mana Cost: {mana}"]
        if hp or maxhp:
            stat_bits.append(f"HP: {hp}" if hp == maxhp else f"HP: {hp}/{maxhp}")
        if is_token:
            stat_bits.append("Token (not independently obtainable)")
        extra = ["  |  ".join(stat_bits)]
        if texts:
            extra.append("")
            extra.extend(f"- {t}" for t in texts)
        icon = upscale(crop_icon(sheet, i, TILE_CUBE, cols, strip_guide=False), 10)
        cards.append((name, render_card(pretty(name), None, None, icon, extra_lines=extra)))
    return cards


BUILDERS = {
    "Curses": build_curses,
    "Consumables": build_consumables,
    "Synergies": build_synergies,
    "Perks": build_perks,
    "Cubes": build_cubes,
}


def render_mod(mod_dir, mod_prefix):
    global MOD_DIR, SPRITES, OUT_DIR, MOD_PREFIX
    MOD_DIR, MOD_PREFIX = mod_dir, mod_prefix
    SPRITES = os.path.join(MOD_DIR, "Sprites")
    OUT_DIR = os.path.join(MOD_DIR, "Preview")
    os.makedirs(OUT_DIR, exist_ok=True)
    # One PNG per item (not one stacked image per category) -- editing a
    # single perk/cube then only touches that one file, instead of forcing
    # a regen+diff of the whole category's combined image.
    seen_prefixes = set()
    written = set()
    for category, builder in BUILDERS.items():
        txt_path = os.path.join(MOD_DIR, f"{MOD_PREFIX}_{category}.c.txt")
        if not os.path.exists(txt_path):
            continue  # this mod has no content of this category -- skip it
        prefix = f"{MOD_PREFIX}_{category}_"
        seen_prefixes.add(prefix)
        for name, card in builder():
            fname = f"{prefix}{name}.png"
            card.save(os.path.join(OUT_DIR, fname))
            written.add(fname)
    # Clean out stale files from a previous run: renamed/removed individual
    # items (same category prefix, but not written this run), leftover
    # combined per-category images from before the per-item switch, or a
    # whole category that no longer has any content.
    for fname in os.listdir(OUT_DIR):
        if fname.endswith("_preview.png"):
            os.remove(os.path.join(OUT_DIR, fname))
        elif any(fname.startswith(p) for p in seen_prefixes) and fname not in written:
            os.remove(os.path.join(OUT_DIR, fname))
        elif not any(fname.startswith(p) for p in seen_prefixes):
            os.remove(os.path.join(OUT_DIR, fname))
    print(f"done: {mod_prefix}")


if __name__ == "__main__":
    render_mod(os.path.join(ROOT, "GameData", "DJ"), "DJ")
    render_mod(os.path.join(ROOT, "GameData", "General"), "General")
