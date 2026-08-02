#!/usr/bin/env bash
# Stop-hook backstop for the Visual: placement-preview rule owned by
# cube-chaos-scripting/references/authoring-and-inheritance.md ("Visual: — placement-preview markers").
#
# Flags a CUBE: block that affects a FIXED tile offset relative to itself but carries
# ZERO Visual: lines — the exact shape that let Hell_Portal (and 11 other cubes across
# Broker/DJ/General/Unholy) ship with no spawn preview until 2026-08-02.
#
# Deliberately narrow, to stay quiet enough to be trusted:
#  - Only fires on blocks with NO Visual: line at all. A block that already has one is
#    assumed to have been thought about; a stale/wrong offset is the periodic audit's job
#    (cube-chaos-audit's "Placement-preview coverage" recipe), not this hook's.
#  - Only matches a destination anchored to the cube ITSELF (PositionOfThis / PositionOfCube
#    Caster / CubeInDirectionFromCube ... Caster). Dynamic destinations (above ARandomEnemy,
#    ARandomPositionWhich, a Victim's position) correctly don't match and are never flagged.
#  - TopPositionAboveCube is NOT matched — it is genuinely ambiguous (own column vs a random
#    enemy's column), so it's named in the message as a manual check instead of guessed at.
# This is a nudge, not a gate: it never blocks the stop, only surfaces the question via
# systemMessage. Silent no-op whenever there's nothing to flag.
#
# Known limitation, same as check-sprite-coverage.sh: it only sees the CURRENT uncommitted
# working tree, and it scans every block in a touched file, not only the block that changed.

set -uo pipefail

status="$(git status --porcelain -- GameData 2>/dev/null || true)"
if [ -z "$status" ]; then
  exit 0
fi

files="$(printf '%s\n' "$status" | cut -c4- | grep -E '\.c\.txt$' || true)"
if [ -z "$files" ]; then
  exit 0
fi

flagged=""
while IFS= read -r f; do
  [ -z "$f" ] && continue
  [ -f "$f" ] || continue

  hits="$(awk '
    function flush() {
      if (name == "" ) return
      if (visual == 0 && blob ~ /PositionInDirectionFromPosition (North|South|East|West|Forwards|Backwards) (PositionOfThis|PositionOfCube Caster)/) {
        print name " (line " start ")"
      } else if (visual == 0 && blob ~ /CubeInDirectionFromCube (North|South|East|West|Forwards|Backwards) (Caster|This)/) {
        print name " (line " start ")"
      }
      name = ""; blob = ""; visual = 0
    }
    /^CUBE: / { flush(); name = $2; start = NR; blob = ""; visual = 0; next }
    name != "" && /^Visual:/ { visual = 1 }
    name != "" && /^End[[:space:]]*$/ { flush(); next }
    name != "" { line = $0; gsub(/[[:space:]]+/, " ", line); blob = blob " " line }
    END { flush() }
  ' "$f" || true)"

  if [ -n "$hits" ]; then
    compact="$(printf '%s' "$hits" | tr '\n' ';' | sed 's/;$//')"
    flagged="$flagged
  - $f: $compact"
  fi
done <<< "$files"

if [ -z "$flagged" ]; then
  exit 0
fi

msg="Placement-preview check: these CUBE: blocks affect a fixed tile offset relative to themselves but have no Visual: line at all, so they will show no placement preview in-game:${flagged}
Per cube-chaos-scripting/references/authoring-and-inheritance.md's Visual: required-vs-omit table, a fixed-offset effect (spawns/damages/buffs/heals a specific neighbouring tile) needs one Visual: line per affected offset — gray 96 96 96 for a cube being created there, red 255 0 0 for damage, green 0 254 33 for healing, ice-blue 155 238 255 for a buff. Verify by count: Visual: lines must equal distinct affected offsets. Legitimately exempt: a destination on the cube's own tile (offset 0 0 is never used), a random/dynamic destination, or an effect granted onto another cube via Enchantment/GainAbilityText. Separately check by hand any block using TopPositionAboveCube — if it means this cube's OWN column it wants 'Visual: Target 0 -1 96 96 96' followed by a bare 'Visual: Infinite'. This is a reminder, not a block."

if command -v jq >/dev/null 2>&1; then
  jq -n --arg msg "$msg" '{systemMessage: $msg}'
else
  escaped="$(printf '%s' "$msg" | sed 's/\\/\\\\/g; s/"/\\"/g' | tr '\n' ' ')"
  printf '{"systemMessage": "%s"}\n' "$escaped"
fi

exit 0
