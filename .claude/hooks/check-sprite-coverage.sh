#!/usr/bin/env bash
# Stop-hook sanity check for cube-chaos-orchestrator's sprite-art Sequence step:
# a NEW CUBE:/PERK: block added this session should come with a touch to its
# matching Sprites/<Basename>.c.png in the same working tree. IsUpgradeFrom:
# upgrade perks live in their own *_UpgradePerks.c.txt file and are deliberately
# sprite-less (see cube-chaos-sprite-art's upgrade-perk section) — that file
# pattern is excluded entirely, not flagged as missing.
# This is a nudge, not a gate: it never blocks the stop, only surfaces the
# question via systemMessage. Silent no-op whenever there's nothing to flag.
# Known limitation: this only sees the CURRENT uncommitted working tree — if a
# new PERK:/CUBE: block was added and then committed earlier in the same
# session (before this hook fires again), it's no longer visible here.

set -uo pipefail

status="$(git status --porcelain -- GameData 2>/dev/null || true)"
if [ -z "$status" ]; then
  exit 0
fi
paths="$(printf '%s\n' "$status" | cut -c4-)"

sprite_touched="$(printf '%s\n' "$paths" | grep -E '\.c\.png$' || true)"

files="$(printf '%s\n' "$paths" | grep -E '\.c\.txt$' | grep -vE '_UpgradePerks\.c\.txt$' || true)"

flagged=""
while IFS= read -r f; do
  [ -z "$f" ] && continue
  [ -f "$f" ] || continue

  new_block=0
  if git diff --unified=0 -- "$f" 2>/dev/null | grep -qE '^\+(PERK:|CUBE:) '; then
    new_block=1
  elif printf '%s\n' "$status" | grep -qE "^\?\? ${f}\$" && grep -qE '^(PERK:|CUBE:) ' "$f" 2>/dev/null; then
    new_block=1
  fi
  [ "$new_block" -eq 1 ] || continue

  # Matching sprite sheet: GameData/<Mod>/Sprites/<Basename>.c.png
  sheet="$(printf '%s' "$f" | sed -E 's#^(GameData/[^/]+)/([^/]+)\.c\.txt$#\1/Sprites/\2.c.png#')"

  if ! printf '%s\n' "$sprite_touched" | grep -qF "$sheet"; then
    flagged="$flagged $f(-> $sheet)"
  fi
done <<< "$files"

if [ -z "$flagged" ]; then
  exit 0
fi

msg="Sprite check: these files have a new PERK:/CUBE: block added this session, but their matching sprite sheet wasn't touched in the working tree:${flagged}. Per cube-chaos-orchestrator's content-perk-family.md/content-cube.md Sequence (sprite-art step), a fresh non-upgrade PERK:/CUBE: needs a drawn icon in its own grid slot before the change is done. If this block is actually IsUpgradeFrom: living in the regular (non-_UpgradePerks) file, or a zero-Ability: helper cube deliberately excluded from the README gallery, that's fine to ignore. This is a reminder, not a block."

if command -v jq >/dev/null 2>&1; then
  jq -n --arg msg "$msg" '{systemMessage: $msg}'
else
  escaped="$(printf '%s' "$msg" | sed 's/\\/\\\\/g; s/"/\\"/g' | tr '\n' ' ')"
  printf '{"systemMessage": "%s"}\n' "$escaped"
fi

exit 0
