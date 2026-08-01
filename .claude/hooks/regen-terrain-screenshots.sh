#!/usr/bin/env bash
# PostToolUse hook (Write|Edit) that regenerates every registered terrain
# mod's data-driven battlefield screenshots whenever any GameData .c.txt
# changes, so GameData/<Mod>/Screenshots/*.png never goes stale after a
# map-data edit (see cube-chaos-scenario-scripting's
# render_terrain_screenshot.py).
#
# Non-blocking by design, same rationale as regen-preview-cards.sh: the
# script does a full, stateless regen of every registered terrain mod's
# outputs on every run (not an incremental diff), so there is no risk of
# stale tracking state -- a crash here is reported but never blocks the
# edit.
#
# Scope matches regen-preview-cards.sh's own universal GameData/*.c.txt
# scope (not just the edited mod's own folder) since a terrain's ground
# layout can also depend on Extra_Mechanics/Battle_Maps.c.txt (the shared
# Battle_*_Player/Enemy leader partials every terrain reads). Which mods
# actually get re-rendered is controlled by render_terrain_screenshot.py's
# own "Registered terrain mods" call list at the bottom of that file, not by
# this hook -- extend that list, not this case statement, when a new
# terrain mod needs screenshots.

set -uo pipefail

input="$(cat)"

file_path="$(printf '%s' "$input" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed -E 's/.*:[[:space:]]*"(.*)"$/\1/')"

[ -n "$file_path" ] || exit 0

norm_path="$(printf '%s' "$file_path" | tr '\\' '/')"

case "$norm_path" in
  GameData/*.c.txt|*/GameData/*.c.txt) ;;
  *) exit 0 ;;
esac

if ! output="$(python3 .claude/skills/cube-chaos-scenario-scripting/scripts/render_terrain_screenshot.py 2>&1)"; then
  echo "WARNING: render_terrain_screenshot.py failed after editing ${file_path}:" >&2
  echo "$output" >&2
fi

exit 0
