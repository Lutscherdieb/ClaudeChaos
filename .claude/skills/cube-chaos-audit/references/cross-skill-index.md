# Cross-skill index — load this when writing back a finding, or before starting work in a domain that might depend on another

This is an index, not a rulebook: every row states a fact in one line and points at the ONE place
that actually explains it, exactly like this skill's main checklist does for mod-content
conventions. **Never copy a rule's explanation into this table** — if a row needs more than one
line, that content belongs in the owning file, not here.

## Why this exists

A 2026-08-02 audit of the whole skill tree found the same shape of gap repeatedly: a gotcha
discovered while working in skill A turned out to be just as relevant to skill B, but nothing in B
ever pointed to it — sometimes for months. The clearest example: `cube-chaos-rule-text` pointed back
to `cube-chaos-scripting` six separate times; `cube-chaos-scripting` had never once pointed forward
to `cube-chaos-rule-text`, despite `CLAUDE.md` explicitly pairing the two skills' own rules in the
same sentence. Each individual gap is a one-line fix; the actual problem was that nothing was
tracking them as a set, so the same asymmetry kept recurring skill after skill.

## How this stays current

- **Live, while working:** `CLAUDE.md`'s research protocol asks every write-back to also check "is
  this relevant to a different skill's domain," and if so, add a pointer there *and* a row here, in
  the same edit.
- **Periodic/batch:** `cube-chaos-doc-audit`'s `GAP` findings are exactly what this table tracks —
  every real doc-audit pass should reconcile its GAP findings against this file (new rows for newly
  found gaps, status updates for rows that got linked).
- **Link status** is one of: `needs link` (the fact exists in exactly one place, no pointer from the
  other relevant skill(s) yet), `linked` (a pointer now exists both ways, or one-way where only one
  direction makes sense), `resolved` (kept here only as a worked example/calibration, not an open
  item).

## Index

| Topic | Lives at | Also relevant to | Status |
|---|---|---|---|
| Faction numbers: `DoubleConstant 1` = player/allies, `2` = enemy, independent of caster | `cube-chaos-scripting/references/gotchas-grepped.md:43` | `cube-chaos-scenario-scripting` (`DATA:`/`DATARECT:` faction args), `cube-chaos-balancing` (curse `Value:` ranges keyed to which side is targeted) | needs link |
| A placed cube mirrors horizontally whenever its `DATA:`/`DATARECT:` faction argument isn't `1` | `cube-chaos-sprite-art/SKILL.md:45` | `cube-chaos-scenario-scripting/references/battle-and-terrain-maps.md` (the skill that actually authors those faction args) | needs link |
| Every `Ability:`/`WorldAbility:` needs a paired `Text:`/`Description:`, written in the same edit | `cube-chaos-rule-text/SKILL.md` (whole skill; `CLAUDE.md` states the pairing rule itself) | `cube-chaos-scripting/SKILL.md`'s own Text:/Description: section doesn't point back to `cube-chaos-rule-text` despite `cube-chaos-rule-text` pointing to `cube-chaos-scripting` 6+ times | needs link |
| `render_preview_cards.py` and `render_terrain_screenshot.py` share code (`render_terrain_screenshot.py` imports the former and reuses its chroma-key/icon-crop conventions) | `cube-chaos-sprite-art/SKILL.md` (preview-card section) and `cube-chaos-scenario-scripting/scripts/render_terrain_screenshot.py:270` (credits sprite-art in the script's own comments) | Neither skill's *prose* documents the pairing the way the code itself does | needs link |
| `PERK_REWARD: VALUE:` min/max ranges are concrete evidence of what pricing lands a perk in which reward tier | `cube-chaos-scenario-scripting/references/reward-and-economy-scenarios.md:53` | `cube-chaos-balancing` (this is exactly the kind of empirical pricing evidence that skill wants) | needs link |
| A fixed-percentage self-propagating `Both Die (create)` chain is a supercritical branching process — wipes a whole group once `p × (N-1) ≥ 1` | `cube-chaos-scripting/references/death-fusion-reactive.md` (`BeforeACubeDies`/death-context section) | `cube-chaos-balancing` (this is a balance-relevant fact about any % chance self-propagating effect, not just a DSL note) | needs link |
| A mod's own cube/perk name colliding with a base-game name silently resolves to the base-game one (zero errors) | `cube-chaos-mod-setup/SKILL.md` (filename/name-collision section) | `cube-chaos-audit`'s own checklist has no row for this despite it being a real, already-documented, silently-shipped-content-shaped incident | needs checklist row (not just a pointer) |
| A class/species's base perk and its reward perks split across files can break `BelongsTo:` resolution purely from alphabetical load order | `cube-chaos-mod-setup/SKILL.md` (real Voidling incident) | `cube-chaos-audit`'s checklist has no row for this either | needs checklist row |
| Decompiled `CubeImage:`/`CubeImageXY:` compositing geometry — a guaranteed 5px margin (`Perk.CubeDrawX`/`CubeDrawY`) | `cube-chaos-sprite-art/SKILL.md:287-302` | `cube-chaos-scripting` (`CubeImage:` is itself a `PERK:` DSL field — its own reference should at least point at the rendering consequences) | needs link |
| A gravity-fall trigger shape (`AfterACubeMoves` + `CubeInDirectionFromCube South`, "nothing solid below → fall one tile") | `cube-chaos-scenario-scripting/references/battle-and-terrain-maps.md:165` (found via a terrain trap cube) | `cube-chaos-scripting` — this is a general `Ability:`-chain pattern, not terrain-specific | needs link |
| `Burrowed` + `AiPlacementRule: And AiStacking AiDefense` + `Crumble` is the standard shape for a static ground/terrain-feature tile | `cube-chaos-scenario-scripting/references/battle-and-terrain-maps.md:174` | `cube-chaos-scripting` (general CUBE-authoring convention, not exclusively a terrain-mod concern) | needs link |
| `cube-chaos-orchestrator`'s Step D ground-truth table should list every skill with a `## Research protocol` section | `cube-chaos-orchestrator/SKILL.md` Step D | `cube-chaos-audit`, `cube-chaos-repo-setup`, `cube-chaos-doc-audit` all have one and are now listed | resolved 2026-08-02 |
