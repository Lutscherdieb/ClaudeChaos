#!/usr/bin/env bash
# Stop-hook nudge for CLAUDE.md's "cold-test a new/substantially-changed skill"
# rule: a new .claude/skills/**/*.md file, or a big edit to an existing one,
# isn't done until a scoped cube-chaos-doc-audit pass covers the changed files.
# This is a nudge, not a gate: it never blocks the stop, only surfaces the
# question via systemMessage. Silent no-op whenever there's nothing to flag.
# Threshold: any brand-new .claude/skills/**/*.md file (including one inside an
# entirely-new skill directory -- git collapses that to one "?? path/" entry
# rather than listing files inside it, handled separately below), or an
# existing one with 6+ changed lines (added+removed) this session. Lower than
# check-sprite-coverage.sh/check-workflow-overview.sh's deliberately blunt
# "any diff" nudges on purpose -- a skill file gets touched for small wording
# fixes far more often than GameData content does, and CLAUDE.md's own rule
# explicitly exempts those; 6 was picked from this hook's first real session
# (2026-08-02), where genuinely new structural additions landed at 6-10 changed
# lines and pure wording nits landed at 1-4 -- recalibrate here if a future
# session finds it too noisy or too quiet.

set -uo pipefail

THRESHOLD=6

status="$(git status --porcelain -- .claude/skills 2>/dev/null || true)"
[ -z "$status" ] && exit 0

flagged=""

# New (untracked) files or whole new directories.
while IFS= read -r entry; do
  [ -z "$entry" ] && continue
  code="${entry:0:2}"
  f="${entry:3}"
  [ "$code" = "??" ] || continue
  case "$f" in
    */)
      inner="$(find "$f" -name '*.md' 2>/dev/null | tr '\n' ' ')"
      [ -n "$inner" ] && flagged="$flagged ${f}(new dir: ${inner})"
      ;;
    *.md)
      flagged="$flagged $f(new)"
      ;;
  esac
done <<< "$status"

# Existing (modified) .md files with THRESHOLD+ changed lines this session.
paths="$(printf '%s\n' "$status" | grep -E '^ M' | cut -c4- | grep -E '\.md$' || true)"
while IFS= read -r f; do
  [ -z "$f" ] && continue
  [ -f "$f" ] || continue
  changed="$(git diff --numstat -- "$f" 2>/dev/null | awk '{print $1+$2}')"
  [ -z "$changed" ] && changed=0
  if [ "$changed" -ge "$THRESHOLD" ]; then
    flagged="$flagged $f(+${changed} lines)"
  fi
done <<< "$paths"

[ -z "$flagged" ] && exit 0

msg="Cold-test check: these skill files look new or substantially changed this session:${flagged}. Per CLAUDE.md, a new skill (or a structural edit to an existing one) isn't done until a scoped cube-chaos-doc-audit cold-test pass covers the changed files -- same weight as the launch-and-log gate for game content. Doesn't apply to small wording-only fixes. This is a reminder, not a block."

if command -v jq >/dev/null 2>&1; then
  jq -n --arg msg "$msg" '{systemMessage: $msg}'
else
  escaped="$(printf '%s' "$msg" | sed 's/\\/\\\\/g; s/"/\\"/g' | tr '\n' ' ')"
  printf '{"systemMessage": "%s"}\n' "$escaped"
fi

exit 0
