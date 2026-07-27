#!/usr/bin/env bash
# PostToolUse hook (Write|Edit) that regenerates mod preview card PNGs
# whenever a mod's CUBE:/PERK: source (.c.txt) or sprite sheet (.c.png)
# changes, so GameData/<Mod>/Preview/*.png never goes stale after a content
# or sprite edit (see cube-chaos-sprite-art's render_preview_cards.py).
#
# Non-blocking by design: render_preview_cards.py does a full, stateless
# regen of every mod on every run (not an incremental diff), so there is no
# risk of stale tracking state -- a crash here is reported but never blocks
# the edit, since this hook only keeps preview images in sync and never
# gates content correctness (that's check-md-dsl-safety.sh's job).

set -uo pipefail

input="$(cat)"

file_path="$(printf '%s' "$input" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed -E 's/.*:[[:space:]]*"(.*)"$/\1/')"

[ -n "$file_path" ] || exit 0

norm_path="$(printf '%s' "$file_path" | tr '\\' '/')"

case "$norm_path" in
  GameData/*.c.txt|*/GameData/*.c.txt|GameData/*.c.png|*/GameData/*.c.png) ;;
  *) exit 0 ;;
esac

if ! output="$(python3 .claude/skills/cube-chaos-sprite-art/scripts/render_preview_cards.py 2>&1)"; then
  echo "WARNING: render_preview_cards.py failed after editing ${file_path}:" >&2
  echo "$output" >&2
fi

exit 0
