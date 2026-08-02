#!/usr/bin/env bash
# Stop-hook sanity check for CLAUDE.md/cube-chaos-orchestrator's launch-and-check-Log.txt
# gate: an Ability:/WorldAbility: change in a tracked mod's .c.txt should be followed by an
# actual game launch (Log.txt on disk newer than the changed file) before being called done.
# Pure Text:/Description:-only rewording is exempt, matching the orchestrator's own exception.
# This is a nudge, not a gate: it never blocks the stop, only surfaces the question via
# systemMessage. Silent no-op whenever there's nothing to flag.

set -uo pipefail

# Base-game packages this repo never edits (per CLAUDE.md) -- excluded below
# since they're not "our" content. Everything else under GameData/ is a real
# mod folder and gets covered automatically -- a hardcoded mod list here
# (`mods="DJ General Unholy"`) previously went stale and silently skipped 5
# of 8 real mods (Broker/DJ_Voidling/Great_Wall/Home_Turf_Advantage/Voidling
# had no launch-check nudge at all); found and fixed 2026-08-02.
base_game_dirs="Base_Core|Extra_Mechanics|Characters|Main|Modding_Example"

# Locate Log.txt via $APPDATA (a Windows path in this git-bash environment).
logpath=""
if [ -n "${APPDATA:-}" ]; then
  if command -v cygpath >/dev/null 2>&1; then
    logpath="$(cygpath -u "$APPDATA")/CubeChaos/Log.txt"
  else
    logpath="$(printf '%s' "$APPDATA" | sed 's#\\#/#g; s#^\([A-Za-z]\):#/\L\1#')/CubeChaos/Log.txt"
  fi
fi

status="$(git status --porcelain -- GameData 2>/dev/null || true)"
if [ -z "$status" ]; then
  exit 0
fi
paths="$(printf '%s\n' "$status" | cut -c4-)"

# Any changed *.c.txt under GameData/<mod>/ whose <mod> isn't a base-game
# package -- derived from the actual changed paths, not a fixed mod list.
files="$(printf '%s\n' "$paths" | grep -E "^GameData/[^/]+/.*\.c\.txt\$" | grep -vE "^GameData/(${base_game_dirs})/" || true)"

flagged=""
while IFS= read -r f; do
  [ -z "$f" ] && continue
  [ -f "$f" ] || continue

  touched=0
  if git diff --unified=0 -- "$f" 2>/dev/null | grep -qE '^[+-](Ability:|WorldAbility:)'; then
    touched=1
  elif printf '%s\n' "$status" | grep -qE "^\?\? ${f}\$" && grep -qE '^(Ability:|WorldAbility:)' "$f" 2>/dev/null; then
    touched=1
  fi
  [ "$touched" -eq 1 ] || continue

  if [ -z "$logpath" ] || [ ! -f "$logpath" ] || [ "$f" -nt "$logpath" ]; then
    flagged="$flagged $f"
  fi
done <<< "$files"

if [ -z "$flagged" ]; then
  exit 0
fi

msg="Launch-check: these files have an Ability:/WorldAbility: change newer than Log.txt (no launch on disk since the edit):${flagged}. Per CLAUDE.md/cube-chaos-orchestrator, a content change with a real ability/logic change isn't done until launched and Log.txt is checked for warnings/errors — this doesn't apply to pure Text:/Description: wording edits. This is a reminder, not a block."

if command -v jq >/dev/null 2>&1; then
  jq -n --arg msg "$msg" '{systemMessage: $msg}'
else
  escaped="$(printf '%s' "$msg" | sed 's/\\/\\\\/g; s/"/\\"/g' | tr '\n' ' ')"
  printf '{"systemMessage": "%s"}\n' "$escaped"
fi

exit 0
