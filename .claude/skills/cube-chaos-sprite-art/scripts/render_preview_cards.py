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
  4) genuinely renders that outer ring. See the main SKILL.md's border
  pattern library for the full styles 1-4 reference.
- CUBE icons (17x17) also need 1px cropped off every side before upscaling,
  same as PERK icons -- but for a different reason: there's no drawn magenta
  guide marker on a CUBE tile, the engine just trims 1px at render time
  regardless, invisibly. Confirmed 2026-07-27 via a real user-vs-preview-card
  comparison (DJ's Microphone, untouched for a long time, showed less padding
  in an actual gameplay screenshot than this script's own un-cropped render).
  An earlier version of this script (and this skill's docs) claimed CUBE
  icons have "no border convention at all" -- true for the drawn-marker
  half of that claim, wrong for the render-trim half.
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
MODDING_INFO_PATH = os.path.join(ROOT, "ModdingInfo.txt")
OUT_DIR = os.path.join(MOD_DIR, "Preview")  # lives with the mod, e.g. for GameData/DJ/README.md
MOD_PREFIX = "DJ"  # this mod's .c.txt/.c.png basename prefix
COMPOUND_DOCS = {}  # built-ins + this mod's own COMPOUND: ABILITY name -> doc, set by render_mod()

# A bare `Ability: Name arg1 arg2` line that grants a pre-registered built-in
# ability (StrengthX, ChargeEveryX, FreePlacement, ...) needs no Text: of its
# own in the source .c.txt (see cube-chaos-scripting's Text:/Description:
# requirement) -- the engine already has that ability's tooltip text baked
# in. But that means THIS script has nothing to read for it either, and a
# cube whose abilities are all built-ins (e.g. General's own Recruit: just
# ChargeEveryX/EveryXMeleeY/FreePlacement/Climbing/Faction_Colours, no custom
# Ability: chains at all) previously rendered with an empty ability list --
# not stale data, a genuine gap. Fix: parse ModdingInfo.txt's own doc-string
# list for these exact same built-in abilities (real registered tooltip
# templates, e.g. `ChargeEveryX TIME     "... Every CODE 1 move forwards "`)
# and substitute the bare Ability: line's actual literal arguments into the
# template's CODE N / STACKING N placeholders, same convention the base game
# itself uses in ModdingInfo.txt.
ABILITY_DOC_RE = re.compile(r'^(\w+)((?:\s+[A-Za-z]+)*)\s+"(.*)"\s*$')


def load_builtin_ability_docs():
    docs = {}
    for line in open(MODDING_INFO_PATH, encoding="utf-8").read().split("\n"):
        m = ABILITY_DOC_RE.match(line)
        if not m:
            continue
        name, types_blob, template = m.group(1), m.group(2), m.group(3)
        docs[name] = {"types": types_blob.split(), "template": template}
    return docs


def resolve_builtin_ability_text(name, args, ability_docs):
    doc = ability_docs.get(name)
    if not doc or not doc["template"]:
        return None
    text = doc["template"]
    code_i = stacking_i = ai = 0
    for t in doc["types"]:
        if ai >= len(args):
            break
        if t == "CUBE":
            # A CUBE-typed arg is always spelled as a keyword (CubeConstant,
            # HiddenCubeConstant, ...) followed by the actual cube name in
            # real DSL call sites (see e.g. `GrowingUp 40 CubeConstant
            # Hell_Dragon` in Unholy_Cubes.c.txt) -- it consumes 2 raw
            # tokens, not 1. Consuming only 1 (the old zip()-based behavior)
            # paired CODE N with the literal word "CubeConstant" instead of
            # the cube name, rendering e.g. "add a CubeConstant to your
            # hand" on preview cards instead of the actual cube's name.
            raw_val = args[ai + 1] if ai + 1 < len(args) else args[ai]
            ai += 2
        else:
            raw_val = args[ai]
            ai += 1
        if t == "STACKING":
            stacking_i += 1
            text = text.replace(f"STACKING {stacking_i}", raw_val)
        elif t == "TIME":
            code_i += 1
            # TIME literals are in ticks (60/sec) -- convert to the same
            # "N second(s)" phrasing real Text:/Description: prose uses
            # (see cube-chaos-rule-text) rather than showing a raw tick count.
            secs = float(raw_val) / 60
            if secs == int(secs):
                secs = int(secs)
                val_str = f"{secs} second" + ("" if secs == 1 else "s")
            else:
                val_str = f"{secs:.2g} seconds"
            text = text.replace(f"CODE {code_i}", val_str)
        else:
            code_i += 1
            text = text.replace(f"CODE {code_i}", raw_val)
    # \C/\CN/\CMANA/\B markup is deliberately left intact here (unlike the
    # old strip-to-plain-text behavior) -- tokenize_colored resolves it into
    # actual on-card color, the same as any other Text:/Description: source.
    return text


GENERIC_RE = re.compile(r'\bGeneric(\w+)\b')


def load_mod_compound_docs(mod_dir):
    """Index this mod's own COMPOUND: ABILITY blocks by name, so \\A <Name>
    [params] references to them (cube-chaos-rule-text: \\A is now used for
    any granted keyword, this mod's own or a base-game built-in -- the
    caller merges this with load_builtin_ability_docs() for the latter) can
    be resolved the same way resolve_builtin_ability_text resolves a bare
    built-in Ability: line. Placeholder types are inferred from the compound's own
    body (GenericStacking -> STACKING, GenericTime -> TIME, everything else
    -> a positional CODE slot) in first-appearance order, matching the
    scripting skill's documented "order by first appearance" convention."""
    docs = {}
    for fname in sorted(os.listdir(mod_dir)):
        if not fname.endswith(".c.txt"):
            continue
        lines = open(os.path.join(mod_dir, fname), encoding="utf-8").read().split("\n")
        i = 0
        while i < len(lines):
            if lines[i].strip() != "COMPOUND: ABILITY":
                i += 1
                continue
            name = lines[i + 1].strip() if i + 1 < len(lines) else None
            j = i + 2
            block_lines, text_tpl = [], None
            while j < len(lines) and lines[j].strip() != "End":
                line = lines[j]
                if line.strip().startswith("Text:"):
                    content = line.strip()[len("Text:"):].strip()
                    if content.endswith(" End"):
                        content = content[:-4].strip()
                    text_tpl = content
                else:
                    block_lines.append(line)
                j += 1
            if name and text_tpl is not None:
                types = []
                for line in block_lines:
                    for g in GENERIC_RE.findall(line):
                        types.append({"Stacking": "STACKING", "Time": "TIME"}.get(g, "CODE"))
                docs[name] = {"types": types, "template": text_tpl}
            i = j + 1
    return docs


A_REF_RE = re.compile(r'\\A (\w+)')


def resolve_inline_abilities(s, compound_docs):
    """Expand \\A <Name> [params...] references into that ability's own
    registered Text:, consuming exactly as many trailing whitespace-separated
    params as the ability's own body declares Generic* placeholders for. An
    unknown name (shouldn't happen for well-formed content) is left as
    literal text rather than crashing the render, so the gap stays visible
    in the generated card instead of failing silently."""
    out, pos = [], 0
    for m in A_REF_RE.finditer(s):
        out.append(s[pos:m.start()])
        name = m.group(1)
        doc = compound_docs.get(name)
        if doc is None:
            out.append(m.group(0))
            pos = m.end()
            continue
        n, consumed, rest = len(doc["types"]), 0, s[m.end():]
        params = []
        while len(params) < n:
            stripped = rest.lstrip(" ")
            leading_ws = len(rest) - len(stripped)
            wm = re.match(r'^(\S+)', stripped)
            if not wm:
                break
            params.append(wm.group(1))
            consumed += leading_ws + len(wm.group(1))
            rest = stripped[len(wm.group(1)):]
        resolved = resolve_builtin_ability_text(name, params, {name: doc}) or ""
        out.append(resolved)
        pos = m.end() + consumed
    out.append(s[pos:])
    return "".join(out)


def collect_ability_texts(lines, ability_docs):
    """Top-level Ability:/Text: pairs, in file order. A custom ability's own
    immediately-following Text: is used verbatim (existing behavior); a bare
    built-in-only Ability: line (no Text: right after it) falls back to
    resolve_builtin_ability_text instead of being silently dropped."""
    top = [l for l in lines if l and not l[0].isspace()]
    texts = []
    i = 0
    while i < len(top):
        line = top[i]
        if line.startswith("Ability:"):
            if i + 1 < len(top) and top[i + 1].startswith("Text:"):
                content = top[i + 1][len("Text:"):].strip()
                if content.endswith(" End"):
                    content = content[:-4].strip()
                texts.append(content)
                i += 2
                continue
            tokens = line[len("Ability:"):].strip().split()
            if tokens:
                resolved = resolve_builtin_ability_text(tokens[0], tokens[1:], ability_docs)
                if resolved:
                    texts.append(resolved)
        i += 1
    return texts

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


# --- Animated-cube preview GIFs -------------------------------------------
# A CUBE: with a TRIGGER-type Animation: line (cube-chaos-scripting's
# cube-animation.md) gets a looping .gif next to its static card:
# <Mod>_Cubes_<CubeName>_<AnimName>.gif, same folder, same upscale factor.
# Frame order/speed is read from the real Animation: line, not guessed --
# TriggerAnimation.AutoChangedCheck locks onto the LAST frame as the
# permanent idle pose and plays frames 0..N-2 as the flourish, each held for
# its own Thresholds[i+1] * 16ms (see cube-animation.md). The one liberty
# taken: the idle pause between triggers is fixed at GIF_IDLE_REST_MS rather
# than the cube's real (often many-second) trigger cadence, so the preview
# loop stays watchable -- the flourish itself plays at true speed.
# Only TRIGGER is implemented: it's the only type any mod here uses yet.
TICK_MS = 16
GIF_IDLE_REST_MS = 1500
ANIMATION_RE = re.compile(r'^Animation:\s*(\S+)\s+(\S+)\s+(-?\d+)\s+(.*)$')


def parse_animation_lines(lines):
    out = []
    for l in lines:
        if l.startswith("Animation:"):
            m = ANIMATION_RE.match(l.strip())
            if m:
                name, atype, effect, rest = m.group(1), m.group(2), int(m.group(3)), m.group(4).split()
                out.append((name, atype, effect, rest))
    return out


def load_animation_frames(mod_dir, cube_name, anim_name, tile=TILE_CUBE):
    path = os.path.join(mod_dir, "Sprites", "Animations", f"{cube_name}_{anim_name}.png")
    sheet = Image.open(path).convert("RGB")
    amount = sheet.width // tile
    return [crop_icon(sheet, i, tile, amount, strip_guide=True) for i in range(amount)]


def build_trigger_gif(mod_dir, cube_name, anim_name, rest_tokens, scale, out_path):
    if rest_tokens[0] == "EQUAL":
        amount, total = int(rest_tokens[1]), int(rest_tokens[2])
        thresholds = [total / amount] * amount
    else:
        amount = int(rest_tokens[0])
        thresholds = [float(t) for t in rest_tokens[1:1 + amount]]
    frames = load_animation_frames(mod_dir, cube_name, anim_name)
    assert len(frames) == amount, (
        f"{cube_name}_{anim_name}.png has {len(frames)} frames, Animation: declares {amount}")
    order = [amount - 1] + list(range(0, amount - 1))
    durations = [GIF_IDLE_REST_MS + thresholds[0] * TICK_MS] + [t * TICK_MS for t in thresholds[1:]]
    imgs = [upscale(frames[i], scale) for i in order]
    imgs[0].save(out_path, save_all=True, append_images=imgs[1:],
                 duration=[int(d) for d in durations], loop=0, disposal=2)


def build_cube_animation_gifs(mod_dir, mod_prefix, out_dir):
    txt_path = os.path.join(mod_dir, f"{mod_prefix}_Cubes.c.txt")
    if not os.path.exists(txt_path):
        return []
    blocks = parse_blocks(txt_path, CUBE_HEADER)
    written = []
    for b in blocks:
        cube_name = b["header"].group(1)
        for anim_name, atype, effect, rest in parse_animation_lines(b["lines"]):
            if atype != "TRIGGER":
                continue  # only TRIGGER's playback shape is implemented so far
            out_name = f"{mod_prefix}_Cubes_{cube_name}_{anim_name}.gif"
            build_trigger_gif(mod_dir, cube_name, anim_name, rest, 10,
                               os.path.join(out_dir, out_name))
            written.append(out_name)
    return written


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


COLOR_START_RE = re.compile(r'\\C(\d+) (\d+) (\d+)')
MANA_WORD_RE = re.compile(r'\bmana\b', re.IGNORECASE)


def tokenize_colored(s, default_color):
    """Split a raw Text:/Description: string (with \\A already resolved) into
    a flat stream of ('WORD', word, color, glue) and ('BREAK',) tokens,
    tracking \\C R G B / \\CMANA / \\CN color-span state and \\B
    no-space-before-next-token markers as we go -- these are real tooltip
    escapes the game's own renderer honors (see cube-chaos-rule-text), not
    plain characters, so they're resolved into actual on-card color/spacing
    here rather than stripped. A bare 'mana' word always renders in the
    engine's own mana-blue, overriding any active span -- matches real
    observed engine behavior (see cube-chaos-rule-text)."""
    tokens = []
    color = default_color
    glue_next = False
    for chunk in re.split(r'(\\C\d+ \d+ \d+|\\CMANA|\\CN|\\B|\\N)', s):
        if not chunk:
            continue
        m = COLOR_START_RE.fullmatch(chunk)
        if m:
            color = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
            continue
        if chunk == '\\CMANA':
            color = MANA_BLUE
            continue
        if chunk == '\\CN':
            color = default_color
            continue
        if chunk == '\\B':
            glue_next = True
            continue
        if chunk == '\\N':
            tokens.append(('BREAK',))
            glue_next = False
            continue
        for word in chunk.split(' '):
            if word == '':
                continue
            word_color = MANA_BLUE if MANA_WORD_RE.search(word) else color
            tokens.append(('WORD', word, word_color, glue_next))
            glue_next = False
    return tokens


def wrap_colored_tokens(d, tokens, f, max_width):
    """Word-wrap a tokenize_colored() stream to max_width, preserving each
    word's color/glue. A ('BREAK',) token (from \\N) always starts a new
    segment; a segment whose first word is a literal '-' gets its wrapped
    continuation lines hang-indented 2 spaces, matching real base-game
    bullet-list Text:/Description: usage (see cube-chaos-rule-text's \\N
    section) -- same behavior the old plain-string wrap_paragraph had.
    Returns a list of (indent_px, [(word, color, glue), ...]) lines."""
    if not tokens:
        return [(0, [])]
    space_w = text_width(d, ' ', f)
    hang_w = text_width(d, '  ', f)

    segments, cur_seg = [], []
    for tok in tokens:
        if tok[0] == 'BREAK':
            segments.append(cur_seg)
            cur_seg = []
        else:
            cur_seg.append(tok)
    segments.append(cur_seg)

    out_lines = []
    for seg in segments:
        if not seg:
            out_lines.append((0, []))
            continue
        hang = seg[0][1] == '-'
        cur, cur_width, first_line_of_seg = [], 0, True
        for _, word, color, glue in seg:
            w = text_width(d, word, f)
            is_first_tok = not cur
            gap = 0 if (is_first_tok or glue) else space_w
            indent = hang_w if (hang and not first_line_of_seg) else 0
            if not is_first_tok and cur_width + gap + w > max_width - indent:
                out_lines.append((hang_w if (hang and not first_line_of_seg) else 0, cur))
                first_line_of_seg = False
                cur, cur_width = [], 0
                is_first_tok, gap = True, 0
            cur.append((word, color, glue and not is_first_tok))
            cur_width += gap + w
        out_lines.append((hang_w if (hang and not first_line_of_seg) else 0, cur))
    return out_lines


def draw_colored_tokens_line(d, pos, indent, tokens, f):
    x, y = pos[0] + indent, pos[1]
    space_w = text_width(d, ' ', f)
    for i, (word, color, glue) in enumerate(tokens):
        if i > 0 and not glue:
            x += space_w
        d.text((x, y), word, font=f, fill=color)
        x += text_width(d, word, f)


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

    def prep(raw):
        # \A must resolve before humanize() (it matches on the literal
        # underscored ability name, e.g. \A Take_Off) -- humanize() then
        # underscore->space's the fully-resolved text, same as it always has.
        resolved = resolve_inline_abilities(raw, COMPOUND_DOCS)
        return tokenize_colored(humanize(resolved), WHITE)

    body_lines = []
    if extra_lines:
        for p in extra_lines:
            body_lines.extend(wrap_colored_tokens(dummy, prep(p), f_body, text_area_w))
    if description:
        body_lines.extend(wrap_colored_tokens(dummy, prep(description), f_body, text_area_w))

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
    for indent, line in body_lines:
        draw_colored_tokens_line(d, (MARGIN, y), indent, line, f_body)
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


CSVARIABLE_RE = re.compile(r'\bCSVARIABLE\s+\S+\b')


def build_cubeupgrades():
    """CubeUpgrade perks (see cube-chaos-scripting's perk-economy.md) live in
    their own <ModPrefix>_CubeUpgrades.c.txt + matching sprite sheet, same
    shape as Curses/Consumables. Their Description: commonly uses the
    engine's own CSVARIABLE <VarName> tooltip placeholder (real base-game
    usage: Main/CubeUpgrades.c.txt's VotikiumUpgrade) to substitute in
    whatever cube is actually cached for that perk instance at runtime --
    meaningless for a static preview card with no live game state, so it's
    replaced with a generic "(the upgraded cube)" placeholder instead of
    rendering the literal token text."""
    blocks = parse_blocks(os.path.join(MOD_DIR, f"{MOD_PREFIX}_CubeUpgrades.c.txt"), PERK_HEADER)
    sheet = load_sheet(f"{MOD_PREFIX}_CubeUpgrades.c.png")
    cols = grid_cols(len(blocks))
    cards = []
    for i, b in enumerate(blocks):
        name = b["header"].group(1)
        desc = field(b["lines"], "Description:")
        if desc:
            desc = CSVARIABLE_RE.sub("(the upgraded cube)", desc)
        val = field(b["lines"], "Value:")
        icon = upscale(crop_icon(sheet, i, TILE_PERK, cols, strip_guide=True), 7)
        cards.append((name, render_card(pretty(name), desc, val, icon)))
    return cards


def build_terrain_perks():
    """Terrain perks (BelongsTo: Terrain) live in their own
    <ModPrefix>_TerrainPerks.c.txt + matching sprite sheet, same shape as
    Curses/Consumables -- except they never carry Value:/BalanceCap: (see
    cube-chaos-balancing's TOKEN/Terrain note), so the card has no value
    line, same as a synergy card."""
    blocks = parse_blocks(os.path.join(MOD_DIR, f"{MOD_PREFIX}_TerrainPerks.c.txt"), PERK_HEADER)
    sheet = load_sheet(f"{MOD_PREFIX}_TerrainPerks.c.png")
    cols = grid_cols(len(blocks))
    cards = []
    for i, b in enumerate(blocks):
        name = b["header"].group(1)
        desc = field(b["lines"], "Description:")
        icon = upscale(crop_icon(sheet, i, TILE_PERK, cols, strip_guide=True), 7)
        cards.append((name, render_card(pretty(name), desc, None, icon)))
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


def perks_source_basenames():
    """DJ/General name their perk file `_Perks.c.txt`; a species mod (e.g.
    Unholy, Voidling) folds its base species perk AND its ordinary reward
    perks into `_Species.c.txt` instead -- `cube-chaos-mod-setup` now documents
    this as a hard rule (a class/species's own reward perks must share ONE
    file with its base perk, never split into a second file, since the game
    loads .c.txt files alphabetically within a package and a reward perk's
    `BelongsTo: <Name>` fails to resolve if its class/species hasn't been
    parsed yet -- real incident, Voidling's Void_Growth, 2026-07-30: a separate
    `Voidling_Perks.c.txt` sorted before `Voidling_Species.c.txt` and broke at
    load time, fixed by merging it into the Species file instead). Both
    basenames are still checked independently here (rather than one-or-the-
    other) purely as defense-in-depth for whatever this function is fed --
    a mod violating the one-file rule would otherwise silently lose one
    basename's preview cards, the same regression this caused once already
    before the checks were made independent."""
    basenames = []
    if os.path.exists(os.path.join(MOD_DIR, f"{MOD_PREFIX}_Species.c.txt")):
        basenames.append("Species")
    if os.path.exists(os.path.join(MOD_DIR, f"{MOD_PREFIX}_Perks.c.txt")):
        basenames.append("Perks")
    return basenames


def build_perks():
    basenames = perks_source_basenames()
    # Each basename has its own file + sprite sheet + slot numbering -- keep
    # them keyed separately rather than assuming one shared sheet/cols pair.
    sources = {}
    name_to_slot = {}  # perk name -> (basename, idx-within-that-basename's-sheet)
    for basename in basenames:
        blocks = parse_blocks(os.path.join(MOD_DIR, f"{MOD_PREFIX}_{basename}.c.txt"), PERK_HEADER)
        sheet = load_sheet(f"{MOD_PREFIX}_{basename}.c.png")
        cols = grid_cols(len(blocks))
        sources[basename] = {"blocks": blocks, "sheet": sheet, "cols": cols}
        for i, b in enumerate(blocks):
            name_to_slot[b["header"].group(1)] = (basename, i)

    # Upgrades live in their own sprite-less file, matching base-game
    # convention (e.g. ZUpgradeClassPerks.c.txt) -- read it too, if present.
    upgrade_path = os.path.join(MOD_DIR, f"{MOD_PREFIX}_UpgradePerks.c.txt")
    upgrade_blocks = parse_blocks(upgrade_path, PERK_HEADER) if os.path.exists(upgrade_path) else []
    upgrade_by_name = {b["header"].group(1): b for b in upgrade_blocks}

    def resolve_icon_slot(target_name, seen=frozenset()):
        # Walk the IsUpgradeFrom chain -- an upgrade can itself be the base
        # of a further upgrade (e.g. Mk3 -> Mk2 -> the real Mk1 perk) -- until
        # landing on a name with a real slot in one of the source sheets.
        if target_name in name_to_slot:
            return name_to_slot[target_name]
        if target_name in seen or target_name not in upgrade_by_name:
            raise KeyError(f"Cannot resolve icon: no real perk at the end of the "
                            f"IsUpgradeFrom chain starting at {target_name!r}")
        next_target = field(upgrade_by_name[target_name]["lines"], "IsUpgradeFrom:").split()[0]
        return resolve_icon_slot(next_target, seen | {target_name})

    def render_block(b, slot):
        basename, idx = slot
        src = sources[basename]
        name = b["header"].group(1)
        # A PERK's Description: is a single whole-perk field (unlike CUBE's
        # per-Ability Text:, which stacks) -- multiple Ability: lines share
        # one Description at the end, each with its own AbilityText: instead.
        # Fall back to the first AbilityText: if a perk has no top-level
        # Description: of its own.
        desc = field(b["lines"], "Description:") or field(b["lines"], "AbilityText:")
        upgrade_of = field(b["lines"], "IsUpgradeFrom:")
        extra = [f"(Upgrade of {upgrade_of.split()[0].replace('_', ' ')})"] if upgrade_of else None
        icon = upscale(crop_icon(src["sheet"], idx, TILE_PERK, src["cols"], strip_guide=True), 7)
        return name, render_card(pretty(name), desc, None, icon, extra_lines=extra)

    cards = []
    for basename in basenames:
        for i, b in enumerate(sources[basename]["blocks"]):
            cards.append(render_block(b, (basename, i)))
    for b in upgrade_blocks:
        base_name = field(b["lines"], "IsUpgradeFrom:").split()[0]
        cards.append(render_block(b, resolve_icon_slot(base_name)))
    return cards


def build_cubes():
    blocks = parse_blocks(os.path.join(MOD_DIR, f"{MOD_PREFIX}_Cubes.c.txt"), CUBE_HEADER)
    sheet = load_sheet(f"{MOD_PREFIX}_Cubes.c.png")
    cols = grid_cols(len(blocks))
    # A bare top-level `Ability: SomeCompound args` line can grant this mod's
    # own COMPOUND: ABILITY keyword directly (its own Text: acts as the
    # tooltip, same convention as a bare built-in grant -- see e.g.
    # Voidling's True_Void CUBE granting `VoidExpansionX`/`VoidNova`
    # directly). COMPOUND_DOCS must be layered in here too, not just
    # resolve_inline_abilities' \A path, or these render as silently missing
    # lines instead of their real tooltip text.
    ability_docs = {**load_builtin_ability_docs(), **COMPOUND_DOCS}
    cards = []
    for i, b in enumerate(blocks):
        h = b["header"]
        name, mana, hp, maxhp = h.group(1), int(h.group(2)), int(h.group(3)), int(h.group(4))
        is_token = any(l.strip() == "TOKEN" for l in b["lines"])
        texts = collect_ability_texts(b["lines"], ability_docs)
        stat_bits = [f"Mana Cost: {mana}"]
        if hp or maxhp:
            stat_bits.append(f"HP: {hp}" if hp == maxhp else f"HP: {hp}/{maxhp}")
        if is_token:
            stat_bits.append("Token (not independently obtainable)")
        extra = ["  |  ".join(stat_bits)]
        if texts:
            extra.append("")
            extra.extend(f"- {t}" for t in texts)
        icon = upscale(crop_icon(sheet, i, TILE_CUBE, cols, strip_guide=True), 10)
        cards.append((name, render_card(pretty(name), None, None, icon, extra_lines=extra)))
    return cards


BUILDERS = {
    "Curses": build_curses,
    "Consumables": build_consumables,
    "CubeUpgrades": build_cubeupgrades,
    "TerrainPerks": build_terrain_perks,
    "Synergies": build_synergies,
    "Perks": build_perks,
    "Cubes": build_cubes,
}


def render_mod(mod_dir, mod_prefix):
    global MOD_DIR, SPRITES, OUT_DIR, MOD_PREFIX, COMPOUND_DOCS
    MOD_DIR, MOD_PREFIX = mod_dir, mod_prefix
    SPRITES = os.path.join(MOD_DIR, "Sprites")
    OUT_DIR = os.path.join(MOD_DIR, "Preview")
    # Merge base-game built-ins with this mod's own compounds so \A resolves
    # either kind (cube-chaos-rule-text, revised 2026-07-29: \A is now used
    # for any granted keyword, not just this mod's own COMPOUND: ABILITY
    # ones) -- mod-own docs take precedence on a name collision.
    COMPOUND_DOCS = {**load_builtin_ability_docs(), **load_mod_compound_docs(MOD_DIR)}
    os.makedirs(OUT_DIR, exist_ok=True)
    # One PNG per item (not one stacked image per category) -- editing a
    # single perk/cube then only touches that one file, instead of forcing
    # a regen+diff of the whole category's combined image.
    seen_prefixes = set()
    written = set()
    for category, builder in BUILDERS.items():
        # "Perks" may be spread across `_Species.c.txt` and/or `_Perks.c.txt`
        # (see perks_source_basenames) -- skip only if neither exists.
        if category == "Perks":
            if not perks_source_basenames():
                continue
        else:
            txt_path = os.path.join(MOD_DIR, f"{MOD_PREFIX}_{category}.c.txt")
            if not os.path.exists(txt_path):
                continue  # this mod has no content of this category -- skip it
        prefix = f"{MOD_PREFIX}_{category}_"
        seen_prefixes.add(prefix)
        for name, card in builder():
            fname = f"{prefix}{name}.png"
            card.save(os.path.join(OUT_DIR, fname))
            written.add(fname)
        if category == "Cubes":
            written.update(build_cube_animation_gifs(MOD_DIR, MOD_PREFIX, OUT_DIR))
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
    render_mod(os.path.join(ROOT, "GameData", "Unholy"), "Unholy")
    render_mod(os.path.join(ROOT, "GameData", "Voidling"), "Voidling")
    render_mod(os.path.join(ROOT, "GameData", "Broker"), "Broker")
    render_mod(os.path.join(ROOT, "GameData", "DJ_Voidling"), "DJ_Voidling")
    render_mod(os.path.join(ROOT, "GameData", "Great_Wall"), "Great_Wall")
