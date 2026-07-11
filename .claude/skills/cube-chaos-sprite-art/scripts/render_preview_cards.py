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
  upgrade's own (blank) slot.
"""
import os
import re
from PIL import Image, ImageDraw, ImageFont

ROOT = r"e:\Programme\Steam\steamapps\common\Cube Chaos"
MOD_DIR = os.path.join(ROOT, "GameData", "DJ")
SPRITES = os.path.join(MOD_DIR, "Sprites")
FONT_PATH = os.path.join(ROOT, "GeneralData", "dogicapixel.ttf")
OUT_DIR = os.path.join(MOD_DIR, "Preview")  # lives with the mod, e.g. for GameData/DJ/README.md
MOD_PREFIX = "DJ"  # this mod's .c.txt/.c.png basename prefix

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
    if s.startswith("- "):
        hang = "  "
        hang_w = text_width(d, hang, f)
        wrapped = wrap_to_width(d, s[2:], f, max_width - hang_w)
        return [("- " if i == 0 else hang) + line for i, line in enumerate(wrapped)]
    return wrap_to_width(d, s, f, max_width)


def draw_colored_line(d, pos, s, f, default_color):
    x, y = pos
    for part in re.split(r'(\bmana\b)', s, flags=re.IGNORECASE):
        if not part:
            continue
        color = MANA_BLUE if part.lower() == "mana" else default_color
        d.text((x, y), part, font=f, fill=color)
        x += text_width(d, part, f)


def render_card(title, description, value, icon_img, extra_lines=None):
    dummy = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    f_title, f_body = font(TITLE_SIZE), font(BODY_SIZE)

    icon_w, icon_h = icon_img.size
    text_area_w = W - MARGIN - 30 - icon_w - MARGIN

    body_lines = []
    if extra_lines:
        for p in extra_lines:
            body_lines.extend(wrap_paragraph(dummy, p, f_body, text_area_w))
    if description:
        body_lines.extend(wrap_to_width(dummy, description, f_body, text_area_w))

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


def stack(cards):
    w = max(c.width for c in cards)
    h = sum(c.height for c in cards) + PAD_BETWEEN_CARDS * (len(cards) - 1)
    out = Image.new("RGB", (w, h), BG)
    y = 0
    for c in cards:
        out.paste(c, (0, y))
        y += c.height + PAD_BETWEEN_CARDS
    return out


def pretty(name):
    return name.replace("_", " ").upper()


def build_curses():
    blocks = parse_blocks(os.path.join(MOD_DIR, f"{MOD_PREFIX}_Curses.c.txt"), PERK_HEADER)
    sheet = load_sheet(f"{MOD_PREFIX}_Curses.c.png")
    cards = []
    for i, b in enumerate(blocks):
        name = b["header"].group(1)
        desc = field(b["lines"], "Description:")
        val = field(b["lines"], "Value:")
        icon = upscale(crop_icon(sheet, i, TILE_PERK, 2, strip_guide=True), 7)
        cards.append(render_card(pretty(name), desc, val, icon))
    return stack(cards)


def build_consumables():
    blocks = parse_blocks(os.path.join(MOD_DIR, f"{MOD_PREFIX}_Consumables.c.txt"), PERK_HEADER)
    sheet = load_sheet(f"{MOD_PREFIX}_Consumables.c.png")
    cards = []
    for i, b in enumerate(blocks):
        name = b["header"].group(1)
        desc = field(b["lines"], "Description:")
        val = field(b["lines"], "Value:")
        icon = upscale(crop_icon(sheet, i, TILE_PERK, 1, strip_guide=True), 7)
        cards.append(render_card(pretty(name), desc, val, icon))
    return stack(cards)


def build_synergies():
    blocks = parse_blocks(os.path.join(MOD_DIR, f"{MOD_PREFIX}_Synergies.c.txt"), PERK_HEADER)
    sheet = load_sheet(f"{MOD_PREFIX}_Synergies.c.png")
    cards = []
    for i, b in enumerate(blocks):
        name = b["header"].group(1)
        desc = field(b["lines"], "Description:")
        icon = upscale(crop_icon(sheet, i, TILE_PERK, 4, strip_guide=False), 6)
        title = name.replace("_", " ").replace("-", " + ").upper()
        cards.append(render_card(title, desc, None, icon))
    return stack(cards)


def build_perks():
    blocks = parse_blocks(os.path.join(MOD_DIR, f"{MOD_PREFIX}_Perks.c.txt"), PERK_HEADER)
    sheet = load_sheet(f"{MOD_PREFIX}_Perks.c.png")
    name_to_idx = {b["header"].group(1): i for i, b in enumerate(blocks)}
    cards = []
    for i, b in enumerate(blocks):
        name = b["header"].group(1)
        desc = field(b["lines"], "Description:")
        upgrade_of = field(b["lines"], "IsUpgradeFrom:")
        icon_idx, extra = i, None
        if upgrade_of:
            base_name = upgrade_of.split()[0]
            icon_idx = name_to_idx[base_name]
            extra = [f"(Upgrade of {base_name.replace('_', ' ')})"]
        icon = upscale(crop_icon(sheet, icon_idx, TILE_PERK, 4, strip_guide=True), 7)
        cards.append(render_card(pretty(name), desc, None, icon, extra_lines=extra))
    return stack(cards)


def build_cubes():
    blocks = parse_blocks(os.path.join(MOD_DIR, f"{MOD_PREFIX}_Cubes.c.txt"), CUBE_HEADER)
    sheet = load_sheet(f"{MOD_PREFIX}_Cubes.c.png")
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
        icon = upscale(crop_icon(sheet, i, TILE_CUBE, 2, strip_guide=False), 10)
        cards.append(render_card(pretty(name), None, None, icon, extra_lines=extra))
    return stack(cards)


if __name__ == "__main__":
    build_curses().save(os.path.join(OUT_DIR, f"{MOD_PREFIX}_Curses_preview.png"))
    build_consumables().save(os.path.join(OUT_DIR, f"{MOD_PREFIX}_Consumables_preview.png"))
    build_synergies().save(os.path.join(OUT_DIR, f"{MOD_PREFIX}_Synergies_preview.png"))
    build_perks().save(os.path.join(OUT_DIR, f"{MOD_PREFIX}_Perks_preview.png"))
    build_cubes().save(os.path.join(OUT_DIR, f"{MOD_PREFIX}_Cubes_preview.png"))
    print("done")
