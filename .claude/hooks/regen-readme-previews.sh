#!/usr/bin/env bash
# PostToolUse hook (Write|Edit) that regenerates every already-opted-in mod's
# README.md Preview section (the <img> tag list under "## Preview") whenever
# a mod's CUBE:/PERK: source (.c.txt) or sprite sheet (.c.png) changes, so
# that list never goes stale the way it used to when it was hand-typed (see
# cube-chaos-mod-setup's sync_readme_preview.py).
#
# Runs after regen-preview-cards.sh/regen-terrain-screenshots.sh in the hook
# chain (see settings.json's ordering) since it reads THEIR freshly-written
# Preview/Screenshots output to decide .png vs .gif and to find screenshot
# files -- order matters here, unlike those two scripts which don't depend on
# each other.
#
# Non-blocking by design, same rationale as the other two regen hooks: a
# crash here is reported but never blocks the edit. Also safe by
# construction, not just by convention -- sync_readme_preview.py only ever
# rewrites the marked <!-- PREVIEW:START -->/<!-- PREVIEW:END --> region, so
# even a fully-automatic run on every edit can't clobber a mod's hand-written
# intro prose or its "## Installing this mod" section.

set -uo pipefail

input="$(cat)"

file_path="$(printf '%s' "$input" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed -E 's/.*:[[:space:]]*"(.*)"$/\1/')"

[ -n "$file_path" ] || exit 0

norm_path="$(printf '%s' "$file_path" | tr '\\' '/')"

case "$norm_path" in
  GameData/*.c.txt|*/GameData/*.c.txt|GameData/*.c.png|*/GameData/*.c.png) ;;
  *) exit 0 ;;
esac

if ! output="$(python3 .claude/skills/cube-chaos-mod-setup/scripts/sync_readme_preview.py 2>&1)"; then
  echo "WARNING: sync_readme_preview.py failed after editing ${file_path}:" >&2
  echo "$output" >&2
fi

exit 0
