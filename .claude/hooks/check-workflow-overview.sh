#!/usr/bin/env bash
# Stop-hook nudge for cube-chaos-orchestrator's own "Notes for extending" rule:
# an edit to cube-chaos-orchestrator/SKILL.md (dispatch table, Step B menu,
# gate sequence, domain-skill list) should come with a regenerated
# WORKFLOW_OVERVIEW.md (repo root) in the same working tree, since that doc is
# a rendering of exactly this file's routing logic.
# This is a nudge, not a gate: it never blocks the stop, only surfaces the
# question via systemMessage. Silent no-op whenever there's nothing to flag.
# Known limitation (shared with the other Stop hooks): only sees the CURRENT
# uncommitted working tree via `git status --porcelain`. Also blunt on
# purpose, like check-sprite-coverage.sh: ANY diff to the orchestrator's
# SKILL.md triggers this, even a wording-only change unrelated to routing --
# a false-positive nudge costs nothing since it's non-blocking.

set -uo pipefail

status="$(git status --porcelain -- .claude/skills/cube-chaos-orchestrator/SKILL.md WORKFLOW_OVERVIEW.md 2>/dev/null || true)"
[ -z "$status" ] && exit 0

orchestrator_changed="$(printf '%s\n' "$status" | grep -F '.claude/skills/cube-chaos-orchestrator/SKILL.md' || true)"
[ -z "$orchestrator_changed" ] && exit 0

overview_changed="$(printf '%s\n' "$status" | grep -F 'WORKFLOW_OVERVIEW.md' || true)"
[ -n "$overview_changed" ] && exit 0

msg="Workflow-overview check: cube-chaos-orchestrator/SKILL.md changed in the working tree, but WORKFLOW_OVERVIEW.md (repo root) doesn't show up as also changed. Per that skill's own \"Notes for extending this orchestrator\" section, an edit to the dispatch table, Step B menu, gate sequence, or domain-skill list isn't finished until WORKFLOW_OVERVIEW.md's diagram/table is regenerated to match. If this SKILL.md edit was wording-only and didn't touch any of those, this reminder doesn't apply. This is a reminder, not a block."

if command -v jq >/dev/null 2>&1; then
  jq -n --arg msg "$msg" '{systemMessage: $msg}'
else
  escaped="$(printf '%s' "$msg" | sed 's/\\/\\\\/g; s/"/\\"/g' | tr '\n' ' ')"
  printf '{"systemMessage": "%s"}\n' "$escaped"
fi

exit 0
