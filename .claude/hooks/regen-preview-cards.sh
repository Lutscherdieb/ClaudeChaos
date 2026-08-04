#!/usr/bin/env bash
# PostToolUse hook (Write|Edit) that regenerates every derived image whenever
# a mod's CUBE:/PERK: source (.c.txt) or sprite sheet (.c.png) changes:
#
#   1. GameData/<Mod>/Preview/*.png  -- the README tooltip cards
#      (cube-chaos-sprite-art's render_preview_cards.py)
#   2. GameData/<Mod>/Image.png      -- the Steam Workshop thumbnail, a 20x
#      blow-up of the mod's namesake perk tile
#      (cube-chaos-mod-setup's render_workshop_image.py)
#
# (2) was added 2026-08-04. It had been a manual "remember to also regenerate
# Image.png" step in cube-chaos-orchestrator's workflows/editing-checklist.md,
# and it was silently skipped exactly as you'd predict: Crusader's thumbnail
# sat stale against a later sprite touch-up until someone noticed by eye. Both
# scripts do a full, stateless regen of every mod on every run rather than an
# incremental diff, so running them unconditionally here is cheap and there is
# no tracking state to go stale.
#
# Non-blocking by design: a crash in either script is reported but never blocks
# the edit, since this hook only keeps derived images in sync and never gates
# content correctness (that's check-md-dsl-safety.sh's job).

set -uo pipefail

input="$(cat)"

file_path="$(printf '%s' "$input" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed -E 's/.*:[[:space:]]*"(.*)"$/\1/')"

[ -n "$file_path" ] || exit 0

norm_path="$(printf '%s' "$file_path" | tr '\\' '/')"

case "$norm_path" in
  GameData/*.c.txt|*/GameData/*.c.txt|GameData/*.c.png|*/GameData/*.c.png) ;;
  *) exit 0 ;;
esac

for script in \
  .claude/skills/cube-chaos-sprite-art/scripts/render_preview_cards.py \
  .claude/skills/cube-chaos-mod-setup/scripts/render_workshop_image.py
do
  if ! output="$(python3 "$script" 2>&1)"; then
    echo "WARNING: $(basename "$script") failed after editing ${file_path}:" >&2
    echo "$output" >&2
  fi
done

exit 0
