#!/usr/bin/env bash
# PostToolUse hook (Write|Edit) that regenerates Great_Wall's own data-driven
# battlefield screenshots whenever its terrain source changes, so
# GameData/Great_Wall/Screenshots/*.png never goes stale after a map-data
# edit (see cube-chaos-scenario-scripting's render_terrain_screenshot.py).
#
# Non-blocking by design, same rationale as regen-preview-cards.sh: the
# script does a full, stateless regen of both outputs on every run (not an
# incremental diff), so there is no risk of stale tracking state -- a crash
# here is reported but never blocks the edit.
#
# Scoped to GameData/Great_Wall/*.c.txt specifically (not every mod, unlike
# regen-preview-cards.sh) since render_terrain_screenshot.py's own
# __main__/GREAT_WALL_OUTPUTS are hardcoded to this one mod -- same
# "hardcoded list, extend when a new terrain needs it" convention already
# used for render_preview_cards.py's own render_mod() call list.

set -uo pipefail

input="$(cat)"

file_path="$(printf '%s' "$input" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed -E 's/.*:[[:space:]]*"(.*)"$/\1/')"

[ -n "$file_path" ] || exit 0

norm_path="$(printf '%s' "$file_path" | tr '\\' '/')"

case "$norm_path" in
  GameData/Great_Wall/*.c.txt|*/GameData/Great_Wall/*.c.txt) ;;
  *) exit 0 ;;
esac

if ! output="$(python3 .claude/skills/cube-chaos-scenario-scripting/scripts/render_terrain_screenshot.py 2>&1)"; then
  echo "WARNING: render_terrain_screenshot.py failed after editing ${file_path}:" >&2
  echo "$output" >&2
fi

exit 0
