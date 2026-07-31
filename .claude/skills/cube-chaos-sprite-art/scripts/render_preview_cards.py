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
- CUBE cards (only) now match several more real in-game tooltip elements,
  added 2026-07-31 after the user supplied an actual gameplay screenshot of
  Unholy's Brimstone tooltip: a boxed mana value, a red HP bar, a small
  bullet glyph per ability (hollow square, or an hourglass for a
  time-driven ability), a "Referenced Cubes" row for any cube this cube's
  own abilities create/copy, and a class/species name+icon footer in that
  class/species's own color. See render_cube_card() below and this skill's
  own "Rendering README preview cards" section for the full rationale,
  evidence, and the known heuristic/scope caveats each of these carries.
- Every IsUpgradeFrom: perk's own card (added 2026-08-01) is itself an
  animated .gif, not a separate static .png -- a white diagonal line,
  drawn pixelated at the icon's native resolution then NEAREST-upscaled,
  translating across the icon every few seconds, matching the real in-game
  upgrade-perk visual cue. See build_shine_icon_frames()/
  draw_shine_line_native() and this skill's own "Rendering README preview
  cards" section for the full writeup.
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
PREFERENCES_PATH = os.path.join(ROOT, ".claude", "preferences.local.md")
OUT_DIR = os.path.join(MOD_DIR, "Preview")  # lives with the mod, e.g. for GameData/DJ/README.md
MOD_PREFIX = "DJ"  # this mod's .c.txt/.c.png basename prefix
COMPOUND_DOCS = {}  # built-ins + this mod's own COMPOUND: ABILITY name -> doc, set by render_mod()
CLASS_SPECIES = None  # this mod's find_class_species() result, set by render_mod()
CUBE_NAME_TO_ICON = {}  # this mod's own CUBE: name -> small icon, for PERK cards' Referenced Cubes row

PREF_LINE_RE = re.compile(r'^-\s*(\S+):\s*(\S+)\s*$')


def read_preference(name, default):
    """Read a `- key: value` line from .claude/preferences.local.md (gitignored
    personal settings, see cube-chaos-repo-setup). Missing file/key falls back
    to `default` rather than erroring, since the file is optional/gitignored --
    a fresh clone or a contributor who skipped setup shouldn't crash a preview
    regen over it."""
    if not os.path.exists(PREFERENCES_PATH):
        return default
    for line in open(PREFERENCES_PATH, encoding="utf-8").read().split("\n"):
        m = PREF_LINE_RE.match(line)
        if m and m.group(1) == name:
            return m.group(2)
    return default

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
                # The compound's OWN root trigger (block_lines[0]'s first
                # token) decides whether a bare top-level grant of this
                # compound (see build_cubes' COMPOUND_DOCS fallback) gets a
                # timed bullet -- the compound's own NAME is not a reliable
                # signal (see is_timed_trigger's own caveat). Real case:
                # Voidling's `VoidNova` doesn't contain "Every" in its own
                # name, but its body's root line is `EveryXSeconds ...` --
                # confirmed via a rendered card showing the wrong (square,
                # not hourglass) bullet before this fix.
                primary_trigger = block_lines[0].strip().split()[0] if block_lines else ""
                docs[name] = {"types": types, "template": text_tpl,
                              "timed": is_timed_trigger(primary_trigger),
                              "body": "\n".join(block_lines)}
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


TIMED_TRIGGER_RE = re.compile(r'Every')


def is_timed_trigger(name):
    """Heuristic for the game's own "recurring timer vs one-shot event"
    bullet-icon distinction (hourglass vs plain square) -- confirmed real
    in-game via a user-supplied Brimstone tooltip screenshot: its
    `ChargeEveryX`/`EveryXSeconds` abilities get an hourglass bullet, its
    `AfterThisDies` ability gets a plain square. Every recurring built-in
    trigger name checked in ModdingInfo.txt contains the substring "Every"
    (`ChargeEveryX`, `EverySecond`, `EveryXSeconds`, `EveryXMeleeY`,
    `EveryXAcidicY`, `EveryXTicks`) while every one-shot trigger checked does
    not (`AfterThisDies`, `AfterThisCollides`, `AfterACubeCollides`,
    `AtTheStartOfTheBattle`, `BeforeThisIsDrawn`) -- and neither group's own
    declared arg TYPEs (TIME vs not) line up consistently enough to use
    instead (`EverySecond`/`EveryXSeconds` don't even declare a TIME-typed
    arg). Classifying on the trigger name substring is therefore the more
    reliable signal of the two, not just the simpler one. This only
    classifies BUILT-IN trigger names by name -- a mod's own COMPOUND:
    ABILITY granted directly as a top-level Ability: line is instead
    classified from ITS OWN root trigger line (see load_mod_compound_docs'
    "timed" field), not this function, precisely because a compound's own
    name is not a reliable signal (real case caught rendering Voidling's
    `True_Void`: `VoidNova` doesn't contain "Every" in its own name, but its
    body's root line is `EveryXSeconds ...` -- classifying by name alone
    showed the wrong square bullet instead of an hourglass)."""
    return bool(TIMED_TRIGGER_RE.search(name))


def collect_ability_texts(lines, ability_docs):
    """Top-level Ability:/Text: pairs, in file order, each paired with
    whether its own trigger is time-driven (for the bullet-glyph choice on
    cube cards). A custom ability's own immediately-following Text: is used
    verbatim (existing behavior); a bare built-in-only Ability: line (no
    Text: right after it) falls back to resolve_builtin_ability_text instead
    of being silently dropped. Returns a list of (text, is_timed) tuples.
    `is_timed` prefers `ability_docs[trigger]["timed"]` when present (set by
    load_mod_compound_docs for this mod's own compounds, from the compound's
    OWN root trigger rather than its name) and falls back to
    is_timed_trigger(trigger) by name otherwise (built-ins have no "timed"
    key at all, but their names are a reliable signal -- see
    is_timed_trigger)."""
    top = [l for l in lines if l and not l[0].isspace()]
    entries = []
    i = 0
    while i < len(top):
        line = top[i]
        if line.startswith("Ability:"):
            tokens = line[len("Ability:"):].strip().split()
            trigger = tokens[0] if tokens else ""
            doc_for_trigger = ability_docs.get(trigger)
            if doc_for_trigger is not None and "timed" in doc_for_trigger:
                timed = doc_for_trigger["timed"]
            else:
                timed = bool(tokens) and is_timed_trigger(trigger)
            if i + 1 < len(top) and top[i + 1].startswith("Text:"):
                content = top[i + 1][len("Text:"):].strip()
                if content.endswith(" End"):
                    content = content[:-4].strip()
                entries.append((content, timed))
                i += 2
                continue
            if tokens:
                resolved = resolve_builtin_ability_text(tokens[0], tokens[1:], ability_docs)
                if resolved:
                    entries.append((resolved, timed))
        i += 1
    return entries

# Grid columns are derived from the actual tile count (ceil(sqrt(n)), matching
# the game's own square-sheet convention -- see SKILL.md) rather than
# hardcoded per category, so this script works unmodified for any mod's own
# tile counts, not just DJ's.
def grid_cols(n):
    return max(1, math.ceil(math.sqrt(n)))

BG = (0, 0, 0)
WHITE = (255, 255, 255)
MANA_BLUE = (80, 140, 255)
DIM_GRAY = (96, 96, 96)  # this repo's standing "dimmed explanation" gray, see cube-chaos-rule-text
GREY_BORDER = (130, 130, 130)  # faint steady grey icon-slot outline, cube cards only (icon_border preference)
HP_RED = (190, 30, 30)
HP_RED_DARK = (110, 15, 15)
TIMED_BULLET_COLOR = (155, 238, 255)  # matches ChargeEveryX's own "Charging:" header color in ModdingInfo.txt
SQUARE_BULLET_COLOR = (150, 150, 150)

TILE_PERK = 27
TILE_CUBE = 17

STAT_COL_W = 150
MANA_BOX_H = 62
HP_BAR_H = 40
STAT_GAP = 10
BULLET_SIZE = 7
BULLET_COL_W = 28

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


# --- IsUpgradeFrom: "shine sweep" animated card -----------------------------
# Every IsUpgradeFrom: perk gets a white diagonal shine sweeping across its
# icon every few seconds in-game, signalling "this is an upgrade" -- unlike
# the CUBE Animation: gif above, this isn't per-item DSL data at all, just a
# fixed UI effect the engine applies to any upgrade perk, so the frames are
# synthesized here rather than read from the mod's own files. Geometry per
# the user's own description (2026-08-01): the line is oriented like a "/"
# (one end lower-left, one end upper-right) and that whole line translates
# diagonally down-and-right across the icon over the sweep, entering near
# the top-left corner and exiting near the bottom-right.
#
# This animates the perk's OWN preview card in place (a .gif instead of a
# .png at the exact same name/position), not a separate companion file --
# an earlier version generated a small standalone "_Shine.gif" shown as an
# extra image below the static card; user feedback (2026-08-01) was that
# the shine belongs IN the existing preview image, not bolted on beside it.
#
# The line must be drawn at the icon's own NATIVE (pre-upscale) resolution,
# not on the already-upscaled card icon -- drawing it post-upscale (the
# first attempt) produced a smooth, sub-pixel-thin line (width 5 screen-px
# at a 7x scale is well under 1 native pixel), which reads as anti-aliased
# and "too smooth" for what's actually a ~25x25-native pixel-art effect in
# the real game (user feedback: should be chunkier/pixelated and about
# twice as big). Drawing at native resolution with a 2-native-pixel width,
# THEN upscaling with NEAREST (same as every other sprite in this file),
# gives the same blocky look as the rest of the icon.
SHINE_SWEEP_STEPS = 14
SHINE_FRAME_MS = 45
SHINE_IDLE_REST_MS = 2200
SHINE_LINE_WIDTH_NATIVE = 2  # native pixels, pre-upscale
SHINE_LINE_COLOR = (255, 255, 255)


def draw_shine_line_native(native_icon, offset):
    """One sweep frame at native resolution: `native_icon` (the raw,
    pre-upscale cropped icon) with a white "/"-oriented line drawn at
    `offset` -- both endpoints shifted by the same (offset, offset) vector
    along the tile's own down-right diagonal, so at offset=0 the line runs
    corner-to-corner (bottom-left to top-right); increasing offset slides
    it toward the bottom-right corner, decreasing toward/off the top-left.
    PIL clips a line's off-canvas portion automatically."""
    im = native_icon.copy()
    d = ImageDraw.Draw(im)
    w, h = im.size
    d.line([(offset, (h - 1) + offset), ((w - 1) + offset, offset)],
           fill=SHINE_LINE_COLOR, width=SHINE_LINE_WIDTH_NATIVE)
    return im


def build_shine_icon_frames(native_icon, scale):
    """Idle frame (plain icon, no line) held for SHINE_IDLE_REST_MS, then
    SHINE_SWEEP_STEPS quick frames sweeping the line from fully off-canvas
    top-left to fully off-canvas bottom-right, then loop -- each frame
    drawn at `native_icon`'s own raw resolution and NEAREST-upscaled by
    `scale` only afterward (see the module note above for why). Sweeping a
    full tile-width beyond each side (offset range -w..+w) guarantees the
    line is genuinely invisible at the sweep's start/end, not abruptly
    appearing already mid-tile. Returns (upscaled_icon_frames, durations)."""
    w = native_icon.width
    native_frames = [native_icon.copy()]
    for i in range(SHINE_SWEEP_STEPS):
        offset = -w + i * (2 * w) // (SHINE_SWEEP_STEPS - 1)
        native_frames.append(draw_shine_line_native(native_icon, offset))
    durations = [SHINE_IDLE_REST_MS] + [SHINE_FRAME_MS] * SHINE_SWEEP_STEPS
    return [upscale(f, scale) for f in native_frames], durations


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


FOOTER_GAP = 20
FOOTER_TEXT_H = 24  # class/species name's own text line height


def compute_footer_row_h(class_species, ref_cubes):
    """Shared sizing for the class/species + referenced-cubes footer row,
    used by both render_card (PERK categories) and render_cube_card
    (CUBE:s) so the two card styles' footers stay pixel-identical and this
    math only needs fixing in one place. See draw_footer_row for the
    matching draw-time logic."""
    h = 0
    if class_species:
        h = max(h, FOOTER_TEXT_H)
    if ref_cubes:
        h = max(h, FOOTER_TEXT_H, *(ic.size[1] for _, ic in ref_cubes if ic is not None))
    return h


def draw_footer_row(d, im, class_x, ref_x, y, footer_row_h, class_species, ref_cubes):
    """Class/species name (text only, no icon) at `class_x`, referenced-cube
    icons (icon only, no name) starting at their OWN `ref_x` rather than
    wherever the class/species text happens to end -- per user feedback
    (2026-08-02), on a CUBE card `ref_x` is `ability_x` so the icons line up
    with the ability bullets' own column above them, instead of drifting
    with the class name's text width. (Name/icon trimmed from an earlier
    icon+name version per separate 2026-08-01 feedback: the icon was
    redundant next to the class/species name, and referenced-cube names
    were redundant next to a real icon of the thing itself.)"""
    if class_species:
        name_font = font(24)
        d.text((class_x, y + (footer_row_h - 24) // 2),
               class_species["name"], font=name_font, fill=class_species["color"])
    x = ref_x
    if ref_cubes:
        for ref_name, ref_icon in ref_cubes:
            if ref_icon is not None:
                rw, rh = ref_icon.size
                im.paste(ref_icon, (x, y + (footer_row_h - rh) // 2))
                x += rw + 8
    return x


def render_card(title, description, value, icon_img, extra_lines=None,
                 class_species=None, ref_cubes=None):
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
    content_h = max(text_block_h, icon_block_h)
    footer_row_h = compute_footer_row_h(class_species, ref_cubes)
    footer_h = (FOOTER_GAP + footer_row_h) if (class_species or ref_cubes) else 0
    H = TOP_MARGIN + content_h + footer_h + BOTTOM_MARGIN

    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)

    icon_x = W - MARGIN - icon_w
    icon_y = TOP_MARGIN + (content_h - icon_block_h) // 2
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

    if class_species or ref_cubes:
        # No separate stat/ability column on a PERK card to align ref_cubes
        # with (unlike render_cube_card's own call below, which uses
        # ability_x) -- so ref_cubes still flows immediately after the
        # class name's own text width, same as before that change.
        ref_x = MARGIN
        if class_species:
            ref_x += text_width(d, class_species["name"], font(24)) + 40
        draw_footer_row(d, im, MARGIN, ref_x, TOP_MARGIN + content_h + FOOTER_GAP,
                         footer_row_h, class_species, ref_cubes)

    return im


def draw_bullet(d, x, cy, timed):
    """Small bullet glyph drawn before an ability's first wrapped line only
    (continuation lines just hang-indent under it, no repeated bullet) --
    a solid hourglass silhouette for a time-driven trigger, a hollow square
    otherwise. Matches the real in-game tooltip distinction confirmed via a
    user-supplied Brimstone screenshot: `ChargeEveryX`/`EveryXSeconds` get
    an hourglass, `AfterThisDies` gets a plain square (see is_timed_trigger
    for the actual classification rule)."""
    s = BULLET_SIZE
    if timed:
        top, bot = cy - s, cy + s
        d.polygon([(x, top), (x + 2 * s, top), (x + s, cy)], fill=TIMED_BULLET_COLOR)
        d.polygon([(x, bot), (x + 2 * s, bot), (x + s, cy)], fill=TIMED_BULLET_COLOR)
    else:
        d.rectangle((x, cy - s, x + 2 * s, cy + s), outline=SQUARE_BULLET_COLOR, width=2)


def render_cube_card(title, mana, hp, maxhp, is_token, ability_entries, icon_img,
                      ref_cubes, class_species, icon_border):
    """CUBE-only card layout (see the module docstring's 2026-07-31 entry) --
    a boxed mana value + red HP bar in a left stat column, one bullet glyph
    per top-level ability (see draw_bullet), an optional "Referenced Cubes"
    row for any cube this one creates/copies (see find_referenced_cubes),
    and a class/species name+icon footer in that class/species's own color
    (see find_class_species). Unlike the shared render_card(), the icon is
    pinned to the top-right corner rather than vertically centered over the
    whole card -- this card can grow tall below the title (referenced
    cubes/footer rows), and the real in-game tooltip's icon doesn't drift
    down to re-center when that happens either."""
    dummy = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    f_title, f_body = font(TITLE_SIZE), font(BODY_SIZE)
    f_stat_big, f_stat_small = font(34), font(16)
    f_dim = font(18)

    icon_w, icon_h = icon_img.size
    border_pad = 6 if icon_border else 0
    icon_x = W - MARGIN - icon_w
    icon_y = TOP_MARGIN

    stat_col_x = MARGIN
    ability_x = stat_col_x + STAT_COL_W + 24
    ability_w = icon_x - border_pad - 20 - ability_x

    def prep(raw):
        # \A must resolve before humanize()/tokenize_colored(), same reasons
        # as render_card's own prep() above.
        resolved = resolve_inline_abilities(raw, COMPOUND_DOCS)
        return tokenize_colored(humanize(resolved), WHITE)

    # Wrap each ability entry independently (not concatenated into one flat
    # body like render_card does) so exactly one bullet can be drawn per
    # ability, positioned against that entry's own first line.
    entry_lines = []
    for text, timed in ability_entries:
        lines = wrap_colored_tokens(dummy, prep(text), f_body, ability_w - BULLET_COL_W)
        entry_lines.append((timed, lines))
    ability_h = sum(len(lines) * (BODY_SIZE + LINE_GAP) for _, lines in entry_lines)
    if entry_lines:
        ability_h += (len(entry_lines) - 1) * 6  # small gap between separate abilities

    stat_h = MANA_BOX_H
    if hp or maxhp:
        stat_h += STAT_GAP + HP_BAR_H
    if is_token:
        stat_h += STAT_GAP + BODY_SIZE

    content_h = max(stat_h, ability_h, icon_h)

    # Class/species + referenced-cubes share ONE footer row (not two stacked
    # blocks) specifically to cap how much a long referenced-cubes list can
    # grow the card's height -- user feedback 2026-07-31 after the first
    # (stacked) version. Sizing/drawing both come from the shared
    # compute_footer_row_h/draw_footer_row helpers (also used by render_card
    # for PERK cards) so the two card styles' footers can't drift apart.
    footer_row_h = compute_footer_row_h(class_species, ref_cubes)
    footer_h = (FOOTER_GAP + footer_row_h) if (class_species or ref_cubes) else 0

    H = TOP_MARGIN + TITLE_SIZE + TITLE_GAP + content_h + footer_h + BOTTOM_MARGIN

    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)

    d.text((MARGIN, TOP_MARGIN), title.upper(), font=f_title, fill=WHITE)

    im.paste(icon_img, (icon_x, icon_y))
    if icon_border:
        d.rectangle((icon_x - border_pad, icon_y - border_pad,
                      icon_x + icon_w + border_pad - 1, icon_y + icon_h + border_pad - 1),
                     outline=GREY_BORDER, width=2)

    body_top = TOP_MARGIN + TITLE_SIZE + TITLE_GAP

    # --- stat column: mana box + hp bar ---
    y = body_top
    mana_s = str(mana)
    # No box outline here -- matches the real in-game tooltip, which shows
    # "50 MANA" as plain stacked text with no border (user feedback
    # 2026-08-01, comparing against the reference screenshot again).
    box_w = max(STAT_COL_W, text_width(d, mana_s, f_stat_big) + 24)
    num_w = text_width(d, mana_s, f_stat_big)
    d.text((stat_col_x + (box_w - num_w) // 2, y + 4), mana_s, font=f_stat_big, fill=WHITE)
    label_w = text_width(d, "MANA", f_stat_small)
    d.text((stat_col_x + (box_w - label_w) // 2, y + MANA_BOX_H - 20), "MANA",
           font=f_stat_small, fill=MANA_BLUE)
    y += MANA_BOX_H

    if hp or maxhp:
        y += STAT_GAP
        d.rounded_rectangle((stat_col_x, y, stat_col_x + box_w, y + HP_BAR_H),
                             radius=6, fill=HP_RED, outline=HP_RED_DARK, width=2)
        # Always "current/max", even when equal -- confirmed via the real
        # Brimstone screenshot showing "6/6" rather than a collapsed "6".
        hp_s = f"{hp}/{maxhp}"
        hp_w = text_width(d, hp_s, f_body)
        d.text((stat_col_x + (box_w - hp_w) // 2, y + (HP_BAR_H - BODY_SIZE) // 2),
               hp_s, font=f_body, fill=WHITE)
        y += HP_BAR_H

    if is_token:
        y += STAT_GAP
        d.text((stat_col_x, y), "TOKEN", font=f_dim, fill=DIM_GRAY)

    # --- ability list: one bullet glyph per ability ---
    y = body_top
    for timed, lines in entry_lines:
        first = True
        for indent, tokens in lines:
            if first:
                draw_bullet(d, ability_x, y + BODY_SIZE // 2, timed)
                first = False
            draw_colored_tokens_line(d, (ability_x + BULLET_COL_W, y), indent, tokens, f_body)
            y += BODY_SIZE + LINE_GAP
        y += 6

    if class_species or ref_cubes:
        # Referenced-cube icons align with ability_x -- the same x the
        # ability bullets themselves start at above -- not with wherever
        # the class name's text happens to end.
        draw_footer_row(d, im, MARGIN, ability_x, body_top + content_h + FOOTER_GAP,
                         footer_row_h, class_species, ref_cubes)

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
        ref_cubes = referenced_cubes_for(b["lines"], name)
        cards.append((name, render_card(pretty(name), desc, val, icon,
                                         class_species=CLASS_SPECIES, ref_cubes=ref_cubes)))
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
        ref_cubes = referenced_cubes_for(b["lines"], name)
        cards.append((name, render_card(pretty(name), desc, val, icon,
                                         class_species=CLASS_SPECIES, ref_cubes=ref_cubes)))
    return cards


def build_neutral():
    """Neutral perks (BelongsTo: Neutral) live in their own
    <ModPrefix>_Neutral.c.txt + matching sprite sheet, same shape as
    Curses/Consumables (Style 2 clean-3-ring border, gray ring 1 --
    cube-chaos-sprite-art's border pattern library)."""
    blocks = parse_blocks(os.path.join(MOD_DIR, f"{MOD_PREFIX}_Neutral.c.txt"), PERK_HEADER)
    sheet = load_sheet(f"{MOD_PREFIX}_Neutral.c.png")
    cols = grid_cols(len(blocks))
    cards = []
    for i, b in enumerate(blocks):
        name = b["header"].group(1)
        desc = field(b["lines"], "Description:")
        val = field(b["lines"], "Value:")
        icon = upscale(crop_icon(sheet, i, TILE_PERK, cols, strip_guide=True), 7)
        ref_cubes = referenced_cubes_for(b["lines"], name)
        cards.append((name, render_card(pretty(name), desc, val, icon,
                                         class_species=CLASS_SPECIES, ref_cubes=ref_cubes)))
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
        ref_cubes = referenced_cubes_for(b["lines"], name)
        cards.append((name, render_card(pretty(name), desc, val, icon,
                                         class_species=CLASS_SPECIES, ref_cubes=ref_cubes)))
    return cards


def build_terrain_perks():
    """Terrain perks (BelongsTo: Terrain) live in their own
    <ModPrefix>_TerrainPerks.c.txt + matching sprite sheet, same shape as
    Curses/Consumables -- except they never carry Value:/BalanceCap: (see
    cube-chaos-balancing's TOKEN/Terrain note), so the card has no value
    line, same as a synergy card. No Referenced Cubes row either (user
    feedback 2026-08-02): a Terrain perk's own ReferenceCube:/CubeConstant
    hits are battlefield-decoration cubes it PLACES on the map (e.g.
    Great_Wall's Anchored_Basalt/Water/Catapult), not cubes granted/
    created for a player's deck the way a normal perk/cube's Referenced
    Cubes row means -- showing them read as misleading in this category."""
    blocks = parse_blocks(os.path.join(MOD_DIR, f"{MOD_PREFIX}_TerrainPerks.c.txt"), PERK_HEADER)
    sheet = load_sheet(f"{MOD_PREFIX}_TerrainPerks.c.png")
    cols = grid_cols(len(blocks))
    cards = []
    for i, b in enumerate(blocks):
        name = b["header"].group(1)
        desc = field(b["lines"], "Description:")
        icon = upscale(crop_icon(sheet, i, TILE_PERK, cols, strip_guide=True), 7)
        cards.append((name, render_card(pretty(name), desc, None, icon,
                                         class_species=CLASS_SPECIES)))
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
        ref_cubes = referenced_cubes_for(b["lines"], name)
        cards.append((name, render_card(title, desc, None, icon,
                                         class_species=CLASS_SPECIES, ref_cubes=ref_cubes)))
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
        raw_icon = crop_icon(src["sheet"], idx, TILE_PERK, src["cols"], strip_guide=True)
        icon = upscale(raw_icon, 7)
        ref_cubes = referenced_cubes_for(b["lines"], name)
        if upgrade_of:
            # Any IsUpgradeFrom: perk gets its own card animated in place
            # (a .gif at this exact name/slot, not a separate companion
            # file) -- regardless of which file it lives in (the dedicated
            # UpgradePerks file, or a regular Perks/Species file that mixes
            # one in as a documented fallback). Re-render the full card once
            # per shine frame, varying only the icon -- title/desc/value/
            # footer are identical across frames since every other render_card
            # input is unchanged, so only the icon area actually animates.
            icon_frames, durations = build_shine_icon_frames(raw_icon, 7)
            card_frames = [render_card(pretty(name), desc, None, f, extra_lines=extra,
                                        class_species=CLASS_SPECIES, ref_cubes=ref_cubes)
                           for f in icon_frames]
            return name, ("gif", card_frames, durations)
        return name, render_card(pretty(name), desc, None, icon, extra_lines=extra,
                                  class_species=CLASS_SPECIES, ref_cubes=ref_cubes)

    cards = []
    for basename in basenames:
        for i, b in enumerate(sources[basename]["blocks"]):
            cards.append(render_block(b, (basename, i)))
    for b in upgrade_blocks:
        base_name = field(b["lines"], "IsUpgradeFrom:").split()[0]
        cards.append(render_block(b, resolve_icon_slot(base_name)))
    return cards


REF_CUBE_RE = re.compile(r'\b(?:CubeConstant|HiddenCubeConstant)\s+(\w+)')
SET_SPRITE_RE = re.compile(r'SetSpriteToCube\s+(?:CubeConstant|HiddenCubeConstant)\s+(\w+)')


def find_referenced_cubes(lines, self_name, compound_docs):
    """Cube names this CUBE's own Ability: chains create/copy/reference via
    a `CubeConstant <Name>`/`HiddenCubeConstant <Name>` token pair (see
    ModdingInfo.txt's CUBE: production grammar -- a CUBE-typed arg is always
    spelled as that keyword plus the literal name, never the name alone;
    same fact `resolve_builtin_ability_text` already relies on for its own
    CODE-substitution). Scans the WHOLE block body (not just top-level
    lines, unlike collect_ability_texts) since these references live on
    indented sub-lines of a chain, e.g. Brimstone's
    `CreateCubeOnPosition CopyWithAction CubeConstant Molten_Brimstone ...`.
    Self-references are excluded (a cube mentioning its own name isn't a
    "referenced cube" in the sense the card footer means), order is
    file-order-of-first-mention, and duplicates are collapsed.

    A bare top-level `Ability: <CompoundName> args` grant of this mod's own
    COMPOUND (no inline CubeConstant token at the call site itself) is also
    expanded into that compound's own body -- one hop only, via
    `compound_docs[name]["body"]` (see load_mod_compound_docs). Real gap
    this closes: DJ's `Speaker` grants `Ability: SpeakerNoteSpawn` bare, and
    `SpeakerNoteSpawn`'s own body is what actually contains
    `CubeConstant Note` -- scanning only Speaker's own block missed it
    entirely, a real miss caught reading the rendered card back (no "Note"
    in Speaker's Referenced Cubes row despite it visibly spawning one).
    Compounds granting further compounds aren't followed recursively; no
    such case exists in this repo's mods yet.

    A `SetSpriteToCube CubeConstant <Name>` target is excluded entirely --
    this is the "directional cube icon" sprite-swap pattern (see
    cube-chaos-sprite-art's `_Arc`/`_West` icon-only helper cubes), not a
    cube actually being created/copied/referenced. Real case caught
    reading rendered cards back: General's `Bomber`/`Drop_Helicopter`/
    `Baby_War_Dragon` each swap to a `_West` icon-only twin via
    `SetSpriteToCube` when reversing direction, and that swap target was
    showing up in the Referenced Cubes row as if it were a spawned cube."""
    seen, out = set(), []
    sprite_swap_targets = set()

    def scan(text):
        sprite_swap_targets.update(SET_SPRITE_RE.findall(text))
        for name in REF_CUBE_RE.findall(text):
            if name != self_name and name not in seen:
                seen.add(name)
                out.append(name)

    for l in lines:
        scan(l)
        if l.startswith("Ability:"):
            tokens = l[len("Ability:"):].strip().split()
            doc = compound_docs.get(tokens[0]) if tokens else None
            if doc and doc.get("body"):
                scan(doc["body"])
    return [n for n in out if n not in sprite_swap_targets]


def sample_dominant_color(im):
    """Most common non-background, non-guide color in a tile -- for a
    class/species base perk tile this is reliably that class/species's own
    color, since "Base class/species icon style" (this skill's SKILL.md)
    confirms the icon fill and its border ring are always the identical
    color for that one perk. Never use this against a content-bearing
    REWARD perk tile -- only the single BelongsTo: CLASS/SPECIES tile has
    this fill-matches-border guarantee."""
    from collections import Counter
    SPRITE_BG = (0, 148, 255)  # the sheet's own default background (cube-chaos-sprite-art SKILL.md) --
    # NOT this script's card-canvas BG (0,0,0), a real bug caught rendering Unholy's own
    # footer: the tile is mostly SPRITE_BG pixels, which dominated the count and got
    # returned as "the class color" instead of the actual (150,20,20) icon/border color.
    cnt = Counter(im.getdata())
    cnt.pop(SPRITE_BG, None)
    cnt.pop((255, 0, 220), None)  # magenta guide ring
    if not cnt:
        return WHITE
    return cnt.most_common(1)[0][0]


def find_class_species(mod_dir, mod_prefix):
    """This mod's own class/species name+color+icon, for the cube-card
    footer -- read from slot 0 of its own `_Species.c.txt`/`_Perks.c.txt`
    (whichever perks_source_basenames() finds first), which is always the
    single `BelongsTo: CLASS`/`BelongsTo: SPECIES` perk by this repo's own
    file-ordering convention (confirmed 2026-07-31 across every mod that has
    one: DJ/General/Broker's own class perk and Unholy/Voidling's own
    species perk are each literally the first PERK: block in their file).
    Returns None for a mod with neither file, or whose first block isn't
    actually a CLASS/SPECIES perk (Great_Wall/Home_Turf_Advantage are
    Terrain/Neutral-only mods with no class or species of their own) --
    the cube-card footer is simply omitted in that case, not left blank."""
    for basename in perks_source_basenames():
        path = os.path.join(mod_dir, f"{mod_prefix}_{basename}.c.txt")
        blocks = parse_blocks(path, PERK_HEADER)
        if not blocks:
            continue
        b = blocks[0]
        if not any(l.strip() in ("BelongsTo: CLASS", "BelongsTo: SPECIES") for l in b["lines"]):
            continue
        name = b["header"].group(1)
        sheet = load_sheet(f"{mod_prefix}_{basename}.c.png")
        cols = grid_cols(len(blocks))
        tile = crop_icon(sheet, 0, TILE_PERK, cols, strip_guide=True)
        color = sample_dominant_color(tile)
        return {"name": name, "color": color, "icon": upscale(tile, 2)}
    return None


def build_cube_icon_index(mod_dir, mod_prefix):
    """name -> small upscaled icon for every one of this mod's own CUBE:s --
    computed once per mod (set into the CUBE_NAME_TO_ICON global by
    render_mod()) so every card category's Referenced Cubes row (not just
    build_cubes' own cross-references) can resolve a cube name to its real
    icon without each category builder re-loading the cube sheet itself.
    Returns {} for a mod with no _Cubes.c.txt at all (e.g. Great_Wall,
    Home_Turf_Advantage) -- Referenced Cubes then just never finds a match,
    same as a genuinely cross-mod/base-game reference."""
    path = os.path.join(mod_dir, f"{mod_prefix}_Cubes.c.txt")
    if not os.path.exists(path):
        return {}
    blocks = parse_blocks(path, CUBE_HEADER)
    sheet = load_sheet(f"{mod_prefix}_Cubes.c.png")
    cols = grid_cols(len(blocks))
    return {b["header"].group(1): upscale(crop_icon(sheet, i, TILE_CUBE, cols, strip_guide=True), 4)
            for i, b in enumerate(blocks)}


# Base-game packages that define their own CUBE:s, for resolving a
# ReferenceCube:/CubeConstant reference to a cube this mod doesn't own
# itself -- e.g. General's `General-Undead` synergy perk creates a
# CubeConstant Zombie, but Zombie is a base-game TOKEN cube
# (Extra_Mechanics/TokenCubes.c.txt), not one of General's own. Read-only
# (see CLAUDE.md's hard rule -- reading base-game files is always fine,
# only writing to them is not). Fixed list of known files rather than a
# directory scan, since these packages' own filenames are stable and this
# avoids accidentally picking up something unrelated.
BASE_GAME_CUBE_FILES = [
    ("Base_Core", "3TokenCubes"),
    ("Characters", "2TokenCubes"),
    ("Characters", "GeneralCubes"),
    ("Main", "2TokenCubes"),
    ("Main", "3GeneralCubes"),
    ("Extra_Mechanics", "TokenCubes"),
    ("Modding_Example", "GeneralCubes"),
]
_BASE_GAME_CUBE_ICON_INDEX = None


def base_game_cube_icon_index():
    """name -> small upscaled icon for every CUBE: in the base game's own
    packages (see BASE_GAME_CUBE_FILES) -- computed once total (not once
    per mod, unlike CUBE_NAME_TO_ICON, since this is shared read-only
    reference data with no per-mod variation) and memoized in
    _BASE_GAME_CUBE_ICON_INDEX. Consulted as a fallback after a mod's own
    CUBE_NAME_TO_ICON comes up empty for a given name."""
    global _BASE_GAME_CUBE_ICON_INDEX
    if _BASE_GAME_CUBE_ICON_INDEX is not None:
        return _BASE_GAME_CUBE_ICON_INDEX
    index = {}
    for package, basename in BASE_GAME_CUBE_FILES:
        txt_path = os.path.join(ROOT, "GameData", package, f"{basename}.c.txt")
        png_path = os.path.join(ROOT, "GameData", package, "Sprites", f"{basename}.c.png")
        if not (os.path.exists(txt_path) and os.path.exists(png_path)):
            continue
        blocks = parse_blocks(txt_path, CUBE_HEADER)
        sheet = Image.open(png_path).convert("RGB")
        # cols MUST come from the sheet's own real width, not
        # grid_cols(len(blocks)) -- unlike every mod file in this repo (which
        # this script itself generated as a square ceil(sqrt(n)) grid), the
        # base game's own sheets are NOT reliably square (see this skill's
        # own "sheet does NOT need to be square" correction). Confirmed by
        # measuring all 7 files here: 6 of 7 have real_cols != ceil(sqrt(n))
        # (e.g. Extra_Mechanics/TokenCubes.c.png is a real 10-wide sheet for
        # 78 cubes, not the 9-wide square grid_cols() assumed) -- using the
        # wrong column count silently landed on a neighboring cube's tile
        # instead (caught: Zombie showed a different cube's art entirely).
        cols = sheet.width // TILE_CUBE
        for i, b in enumerate(blocks):
            name = b["header"].group(1)
            if name not in index:  # first package wins on a same-name collision
                index[name] = upscale(crop_icon(sheet, i, TILE_CUBE, cols, strip_guide=True), 4)
    _BASE_GAME_CUBE_ICON_INDEX = index
    return index


REFERENCE_CUBE_RE = re.compile(r'^ReferenceCube:\s*(\w+)')


def referenced_cubes_for(lines, self_name):
    """The common path every card category (CUBE and PERK alike) uses to
    build its `ref_cubes` list for render_card/render_cube_card's footer
    row. Two sources, combined:
    1. Explicit `ReferenceCube: <Name>` declarations -- a real, repeatable
       `PERK:` field (see cube-chaos-scripting's authoring-and-inheritance.md,
       confirmed real usage e.g. Cryomancer.c.txt:68-70) that an author uses
       specifically to curate a perk's tooltip cube list -- e.g. an egg perk
       declaring its whole egg/baby/adult chain (General's `War_Dragon_Egg`
       declares all 3 stages), or a perk that grants a RANDOM cube from a
       pool declaring every possible pick (Unholy's `Lichdom` declares
       `Damned_Soul`/`Plague_Imp`/`Imp`, none of which appear as a literal
       `CubeConstant` token anywhere in its own Ability: chain -- the actual
       selection goes through `ARandomCubeInLibraryWhich`-style productions
       the heuristic scan below has no way to enumerate). These are
       AUTHORITATIVE and NOT self-name-filtered -- a perk can and does
       legitimately declare a `ReferenceCube:` matching its own name (e.g.
       `War_Dragon_Egg` itself lists `ReferenceCube: War_Dragon_Egg`, to
       show the exact cube it grants), unlike the heuristic scan's
       self-exclusion. Missed entirely until 2026-08-02 -- this script had
       no `ReferenceCube:` support at all, so any perk whose own Ability:
       chain only referenced ITSELF (e.g. `War_Dragon_Egg`'s
       `FreeCopy CubeConstant War_Dragon_Egg`) rendered with an empty
       Referenced Cubes row despite explicitly declaring 3 relevant cubes.
    2. The `find_referenced_cubes` heuristic scan (`CubeConstant`/
       `HiddenCubeConstant` tokens), for cubes a perk creates/copies/obtains
       but never explicitly declared -- still useful as a fallback for
       perks with no `ReferenceCube:` field of their own (most of them).
    Declared names come first (file-declaration order), then any
    heuristic-found names not already covered, deduped."""
    declared = []
    for l in lines:
        m = REFERENCE_CUBE_RE.match(l)
        if m:
            declared.append(m.group(1))
    seen = set(declared)
    names = list(declared)
    for n in find_referenced_cubes(lines, self_name, COMPOUND_DOCS):
        if n not in seen:
            seen.add(n)
            names.append(n)
    # Resolve each name to an icon: this mod's own CUBE:s first, then the
    # base game's own packages as a fallback (see base_game_cube_icon_index
    # -- real case: General's `General-Undead` synergy perk creates a
    # CubeConstant Zombie, a base-game TOKEN cube General doesn't own
    # itself; it rendered with no icon for Zombie until this fallback was
    # added). Drop any name still unresolved (a genuinely different mod's
    # own cube, or -- as with Great_Wall's ReferenceCube: Anchored_Basalt/
    # Water/Catapult -- a terrain-scenario TOKEN cube defined inline
    # somewhere this doesn't scan) rather than keeping a name-less blank
    # entry: since this footer never shows text (see draw_footer_row), an
    # icon-less entry contributes nothing visible but would still reserve a
    # full footer row's worth of vertical space (caught on Great_Wall's card).
    base_icons = base_game_cube_icon_index()
    result = []
    for n in names:
        icon = CUBE_NAME_TO_ICON.get(n) or base_icons.get(n)
        if icon is not None:
            result.append((n, icon))
    return result


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
    icon_border = read_preference("preview_card_icon_border", "on") == "on"
    cards = []
    for i, b in enumerate(blocks):
        h = b["header"]
        name, mana, hp, maxhp = h.group(1), int(h.group(2)), int(h.group(3)), int(h.group(4))
        is_token = any(l.strip() == "TOKEN" for l in b["lines"])
        ability_entries = collect_ability_texts(b["lines"], ability_docs)
        ref_cubes = referenced_cubes_for(b["lines"], name)
        icon = upscale(crop_icon(sheet, i, TILE_CUBE, cols, strip_guide=True), 10)
        card = render_cube_card(pretty(name), mana, hp, maxhp, is_token, ability_entries,
                                 icon, ref_cubes, CLASS_SPECIES, icon_border)
        cards.append((name, card))
    return cards


BUILDERS = {
    "Curses": build_curses,
    "Consumables": build_consumables,
    "CubeUpgrades": build_cubeupgrades,
    "TerrainPerks": build_terrain_perks,
    "Neutral": build_neutral,
    "Synergies": build_synergies,
    "Perks": build_perks,
    "Cubes": build_cubes,
}


def render_mod(mod_dir, mod_prefix):
    global MOD_DIR, SPRITES, OUT_DIR, MOD_PREFIX, COMPOUND_DOCS, CLASS_SPECIES, CUBE_NAME_TO_ICON
    MOD_DIR, MOD_PREFIX = mod_dir, mod_prefix
    SPRITES = os.path.join(MOD_DIR, "Sprites")
    OUT_DIR = os.path.join(MOD_DIR, "Preview")
    # Merge base-game built-ins with this mod's own compounds so \A resolves
    # either kind (cube-chaos-rule-text, revised 2026-07-29: \A is now used
    # for any granted keyword, not just this mod's own COMPOUND: ABILITY
    # ones) -- mod-own docs take precedence on a name collision.
    COMPOUND_DOCS = {**load_builtin_ability_docs(), **load_mod_compound_docs(MOD_DIR)}
    # Computed once per mod (not per category) since every category's cards
    # share the same mod-wide class/species footer and the same pool of this
    # mod's own CUBE:s to resolve a Referenced Cubes icon against.
    CLASS_SPECIES = find_class_species(MOD_DIR, MOD_PREFIX)
    CUBE_NAME_TO_ICON = build_cube_icon_index(MOD_DIR, MOD_PREFIX)
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
        # A card is normally a plain PIL Image (saved as .png), but
        # build_perks() returns ("gif", frames, durations) for an
        # IsUpgradeFrom: perk (its own shine-sweep animation, see
        # build_shine_icon_frames) -- saved as an animated .gif at the same
        # name/slot instead, no separate companion file.
        for name, card in builder():
            if isinstance(card, tuple) and card[0] == "gif":
                _, frames, durations = card
                fname = f"{prefix}{name}.gif"
                frames[0].save(os.path.join(OUT_DIR, fname), save_all=True,
                                append_images=frames[1:], duration=durations,
                                loop=0, disposal=2)
            else:
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
    render_mod(os.path.join(ROOT, "GameData", "Home_Turf_Advantage"), "Home_Turf_Advantage")
