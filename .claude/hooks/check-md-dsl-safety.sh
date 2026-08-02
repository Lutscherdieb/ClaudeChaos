#!/usr/bin/env bash
# PostToolUse hook (Write|Edit) for GameData/**/*.md files (README.md, etc).
#
# The game engine tokenizes EVERY file in a loaded mod package folder, not just
# .c.txt files (confirmed: .claude/skills/cube-chaos-mod-setup/SKILL.md's "real
# incident" writeups, Log.txt's own "Cut Into Words Test<...>" lines for .md
# content). Two known-dangerous patterns cause real parse errors at launch:
#
#   1. A bare word "end" (case-insensitive, whole-word, NOT inside a
#      backtick-wrapped span) anywhere in the doc -> "ERROR: excess 'End' in
#      package X". Real incident this session: a prose sentence containing
#      "...it's always meant to end up on the enemy side..." broke the whole
#      Unholy package until reworded.
#   2. A bare DSL keyword (cube/perk/compound/ability/text/description)
#      immediately followed by a colon, NOT backtick-wrapped -> cascading
#      "CANT READ"/"Couldn't figure out part of X" errors. Two prior real
#      incidents documented in the skill file above.
#
# This hook blocks (exit 2) with the offending line(s) and a fix suggestion so
# the edit gets corrected before the turn ends, rather than surfacing as an
# in-game parse error discovered later.

set -uo pipefail

input="$(cat)"

file_path="$(printf '%s' "$input" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed -E 's/.*:[[:space:]]*"(.*)"$/\1/')"

[ -n "$file_path" ] || exit 0

# Normalize backslashes to forward slashes for the pattern match (Windows paths).
norm_path="$(printf '%s' "$file_path" | tr '\\' '/')"

case "$norm_path" in
  GameData/*.md|*/GameData/*.md) ;;
  *) exit 0 ;;
esac

[ -f "$file_path" ] || exit 0

violations=""

# Strip backtick-wrapped spans from a line before pattern-checking it, so
# genuine inline-code references (`Text: ... End`, `Ability:`) don't trip
# either check.
strip_backticks() {
  printf '%s' "$1" | sed -E 's/`[^`]*`//g'
}

# Strip HTML comment spans (e.g. <!-- PREVIEW:START -->/<!-- PREVIEW:END -->,
# the sync_readme_preview.py region markers) before pattern-checking a line.
# Confirmed via a real launch (2026-08-02, Log.txt clean across all 8 mods'
# READMEs) that these markers do NOT trigger the engine's "excess End" error
# the way bare prose does -- see cube-chaos-mod-setup/SKILL.md's "How the game
# discovers content" section for the evidence. Single-line comments only,
# matching this repo's actual usage.
strip_html_comments() {
  printf '%s' "$1" | sed -E 's/<!--.*-->//g'
}

lineno=0
while IFS= read -r line || [ -n "$line" ]; do
  lineno=$((lineno + 1))
  stripped="$(strip_backticks "$line")"
  stripped="$(strip_html_comments "$stripped")"

  if printf '%s' "$stripped" | grep -qiE '\bend\b'; then
    violations="${violations}
  Line ${lineno} (bare 'end'): ${line}"
  fi

  if printf '%s' "$stripped" | grep -qiE '\b(cube|perk|compound|ability|text|description):'; then
    violations="${violations}
  Line ${lineno} (bare keyword+colon): ${line}"
  fi
done < "$file_path"

if [ -z "$violations" ]; then
  exit 0
fi

cat >&2 <<EOF
BLOCKED: ${file_path} contains DSL-unsafe patterns that will break the game's parser.

The engine tokenizes every file in a mod package folder, including .md docs (see
.claude/skills/cube-chaos-mod-setup/SKILL.md). Two patterns are dangerous even in
plain English prose:
  - a bare word "end" (case-insensitive, whole word) anywhere -> "ERROR: excess 'End' in package X"
  - a bare "cube:"/"perk:"/"compound:"/"ability:"/"text:"/"description:" (not backtick-wrapped) -> cascading CANT READ errors

Violations found:${violations}

Fix: reword each line to break the bare word/colon-adjacency (e.g. "meant to end up" -> "meant to land"; "cube: X" -> "cube lives in X" or wrap the keyword in backticks if it's a real DSL reference, e.g. \`Ability:\`). Then re-save.
EOF

exit 2
