#!/usr/bin/env bash
# Stop-hook sanity check for the CLAUDE.md/cube-chaos-orchestrator writeback rule:
# a GameData/<Mod> content or sprite change should usually come with a matching
# GameData/<Mod>/DESIGN.md update or a .claude/skills/**/*.md writeback in the same
# session. This is a nudge, not a gate: it never blocks the stop, it only surfaces
# the question via systemMessage when the working tree looks like it might have been
# skipped. Silent no-op (exit 0, no output) whenever there's nothing to flag.

set -uo pipefail

mods="DJ General Unholy"

status="$(git status --porcelain -- GameData .claude/skills 2>/dev/null || true)"
if [ -z "$status" ]; then
  exit 0
fi

# Strip the leading "XY " porcelain status prefix (always 3 chars) to get bare paths.
paths="$(printf '%s\n' "$status" | cut -c4-)"

skill_touched=0
if printf '%s\n' "$paths" | grep -qE '^\.claude/skills/.*\.md$'; then
  skill_touched=1
fi

warn_mods=""
for mod in $mods; do
  content_touched="$(printf '%s\n' "$paths" | grep -E "^GameData/${mod}/.*\.c\.(txt|png)$" || true)"
  if [ -z "$content_touched" ]; then
    continue
  fi
  design_touched="$(printf '%s\n' "$paths" | grep -E "^GameData/${mod}/DESIGN\.md$" || true)"
  if [ -z "$design_touched" ] && [ "$skill_touched" -eq 0 ]; then
    warn_mods="$warn_mods $mod"
  fi
done

if [ -z "$warn_mods" ]; then
  exit 0
fi

msg="Writeback check: GameData content/sprite files changed this session for:${warn_mods} — but no matching DESIGN.md (that mod) or .claude/skills/**/*.md diff was found in the working tree. Per CLAUDE.md's per-edit consistency rules and cube-chaos-orchestrator's Step D, confirm whether a design/balance decision or a scripting/rule-text/sprite-art finding from this session still needs to be recorded — or that this change (bugfix, straightforward balance tweak matching an existing pattern, pure refactor) genuinely needs none. This is a reminder, not a block."

if command -v jq >/dev/null 2>&1; then
  jq -n --arg msg "$msg" '{systemMessage: $msg}'
else
  # Minimal manual JSON-string escaping fallback if jq isn't on PATH.
  escaped="$(printf '%s' "$msg" | sed 's/\\/\\\\/g; s/"/\\"/g' | tr '\n' ' ')"
  printf '{"systemMessage": "%s"}\n' "$escaped"
fi

exit 0
