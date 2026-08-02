---
name: cube-chaos-doc-audit
description: Use for a periodic or on-demand cross-cutting audit of this repo's OWN skill/reference/README files, as a system - NOT a mod's game content (see cube-chaos-audit for that; the two names are easy to confuse on purpose, see the disambiguation note in cube-chaos-orchestrator). Checks for hardcoded-list drift (a mod roster or sample count baked into prose instead of derived), asymmetric or missing cross-references between skills, self-contradictions on the same fact, README prose that's drifted from actual GameData content, and orchestrator routing-table accuracy. Reports findings for the user's approval before fixing anything, same gate as cube-chaos-audit. Trigger on "audit our skills", "check the skill docs", "is our documentation up to date", "check for stale or duplicate gotchas", "review our documentation for consistency", "check the skill system", or whenever a skill file's own size/age suggests it's due for a check. Do not trigger this for "audit this mod" / "check conventions" on actual mod content - that's cube-chaos-audit.
---

# Cube Chaos documentation & skill-system audit

This is a QA pass over the skill/reference/README tree **as a system**, not over any mod's game
content. `cube-chaos-audit` asks "does this mod's `.c.txt`/`.c.png` content follow our own
conventions"; this skill asks "does our own knowledge base — the thing that *defines* those
conventions — still agree with itself and with reality." First run: 2026-08-02, prompted by the
repo owner noticing gotchas were scattered across skill files with no guarantee a fact relevant to
skill B was actually linked from skill B when it was only written down in skill A.

## Research protocol

1. **Check this skill's five categories and known patterns below first** for whether the drift/gap/
   contradiction in front of you already has a named shape.
2. **If it doesn't, the ground truth is the skill/reference/README tree itself and the real repo
   state — not the base game's own docs.** `ModdingInfo.txt`/`ModdingExplanation.txt` aren't the
   target here (this skill audits this repo's own writing, not the engine); cross-read the relevant
   files directly and `Grep`/`Glob` for real current state (`GameData/Loading_Order.txt`, real
   folder listings, real `.c.txt` content). **When a `CONTRADICTION` needs resolving rather than
   just flagging, fall back to the same evidence tools every other skill uses**: a real grep of
   actual usage, real paired `Description:`/`Text:` values (the `Cooldown` fix, 2026-08-02), or a
   real test launch and a fresh `Log.txt` (used directly to confirm the `check-md-dsl-safety.sh`
   HTML-comment fix was actually safe, same date) — never pick a side arbitrarily.
3. **Write the finding back**: report it per Procedure step 9, and once the user approves a fix,
   the fix itself needs its own citation the same way every other skill's write-back does — a fix
   without evidence is a guess wearing a fix's clothes (Procedure step 10 says the same thing).

## What this checks (five categories)

1. **Hardcoded-list drift.** A mod roster, mod count, or sample size baked into prose as a fixed
   list/number instead of derived from `GameData/Loading_Order.txt` or a live grep. This was the
   single biggest pattern in the first real run — found independently in four places
   (`.claude/hooks/check-launch-log.sh`'s `mods="DJ General Unholy"`, `cube-chaos-audit/SKILL.md`'s
   "DJ/General/Unholy as of this writing", `workshop-publishing.md`'s 4-of-8-mod table,
   `cube-chaos-balancing/SKILL.md`'s "546 cubes... both mods" sample). Grep skill/hook/script files
   for mod names or counts and diff against the real `GameData/*` folder list (minus
   `Base_Core`/`Extra_Mechanics`/`Characters`/`Main`/`Modding_Example`) — anything that reads like a
   frozen snapshot rather than a derivation is a finding, even if it isn't wrong *yet*.
2. **Missing or asymmetric cross-references.** A gotcha lives in skill A, is plainly relevant to
   skill B's domain, but nothing in B points to it (or only one direction of a two-skill
   relationship is linked — e.g. `cube-chaos-scripting/SKILL.md`'s own Text:/Description: section
   never pointed to `cube-chaos-rule-text`, despite `cube-chaos-rule-text` pointing back to
   `cube-chaos-scripting` six separate times). See `cube-chaos-audit/references/cross-skill-index.md`
   — this is exactly what that index tracks, and this skill's own GAP findings are how it grows.
3. **Self-contradictions.** Two files (or two places in one file) asserting different things about
   the same fact. Real example, resolved 2026-08-02: `gotchas-grepped.md` claimed `Cooldown
   DoubleConstant N` was plain seconds, `death-fusion-reactive.md` claimed ticks — resolved by
   grepping real `Cooldown`/Description: pairings (`Characters/Synergies.c.txt:1012` `Cooldown 3600`
   ↔ its own Description "Cooldown 1 minute", etc.), not by picking either file arbitrarily. When a
   contradiction like this turns up, re-derive from real evidence the same way — grep real usage,
   real paired Description:/Text:, or a real test launch — and cite that evidence in the fix.
4. **README-vs-actual-content staleness.** A mod's hand-written prose (not the auto-synced Preview
   image list — trust that part, a hook keeps it current) describing a mechanic that's since
   changed, been removed, or was never quite what the prose says. Cross-check every factual claim
   in a README's prose against the mod's real `.c.txt` `Ability:`/`Description:` content, not just
   against memory of what the mod does.
5. **Routing/table accuracy.** `cube-chaos-orchestrator`'s dispatch table, Step D ground-truth
   table, and skill/workflow-file lists, cross-checked against the skills/workflows that actually
   exist on disk (`Glob`), plus `WORKFLOW_OVERVIEW.md` cross-checked against `SKILL.md` for drift
   between the two.

## When to run it

**Two shapes: a scoped cold test, or a full periodic sweep. Never a hook** — even the scoped shape
spawns real parallel agents and takes real minutes, too expensive for every `Stop`/`PostToolUse`
event the way `check-md-dsl-safety.sh` or the regen hooks are.
`.claude/hooks/check-skill-cold-test.sh` nudges (non-blocking) when it looks like one is due, but
never runs one itself.

- **Scoped cold test — after creating a new skill, or making a structural edit to an existing one**
  (a new section, a reorganization, new cross-references). Per `CLAUDE.md`'s own rule, this isn't
  optional the way the periodic sweep is: it's the same weight as the launch-and-log gate, just for
  the skill system instead of game content. Scope it to the files that actually changed this
  session (git status/diff), not the whole tree — 2-4 chunks instead of the full pass's 4-6 is
  usually enough. Real precedent, 2026-08-02: cold-testing this skill and its companion
  `cross-skill-index.md` immediately after writing them caught this skill claiming a `Research
  protocol` section it didn't actually have, an overstated claim in its own text, an off-by-one
  citation, and a leftover contradiction in a file that had just been "fixed" minutes earlier — all
  invisible to the session that had just written them, because writing something and re-checking it
  fresh use different failure modes. Don't skip this step just because the work "feels" done; that
  feeling is exactly what this catches errors *despite*.
- **Full periodic sweep — 4-6 parallel agents across the whole skill tree** (the first run: ~3,800
  lines of skill/reference content plus 8 READMEs, about 10 minutes). Good moments: the user asks
  directly; a skill file has grown past roughly 2-3x the size of its peers (a real symptom found in
  the first run — `cube-chaos-sprite-art/SKILL.md` at 591 lines, ~10x every other skill's core file,
  had accumulated an actual self-contradiction that a size-driven split would have made harder to
  miss); after a big batch of new mods/content lands; or whenever the skill set "feels" stale or
  sprawling in general, not tied to one recent change. If the user
wants this on an actual recurring cadence, that's the `loop`/`schedule` Claude Code skills, not
something this skill sets up for itself.

## Procedure

1. **Inventory.** `Glob` every `.claude/skills/**/*.md`, every `GameData/*/README.md`, the root
   `README.md`/`WORKFLOW_OVERVIEW.md`/`CLAUDE.md`, and `.claude/hooks/*.sh`. Get line counts
   (`wc -l`) to gauge chunk sizes before splitting.
2. **Read the hooks and settings.json yourself, directly** (small, ~350-400 lines total across
   `.claude/hooks/*.sh` plus `.claude/settings.json`/`.claude/settings.local.json`) — this is the
   automated-enforcement ground truth every skill's claims about "the launch gate"/"the sprite
   check"/etc. need to be checked against, and it's cheap enough not to delegate.
3. **Split the rest into chunks along natural domain boundaries** — 4-6 for a full sweep (tightly-
   coupled skills together, e.g. scripting+rule-text; scenario-scripting+sprite-art;
   balancing+mod-setup+audit; orchestrator+workflows+repo-setup; plus one chunk specifically for
   READMEs-vs-actual-GameData-content), fewer (2-4) for a scoped cold test since there's simply less
   to cover — group by what actually changed, not by forcing the full sweep's boundaries onto a
   handful of files. Rebalance either grouping as skills are added/split/removed; the boundaries
   aren't fixed, just "roughly even, roughly coherent."
4. **Spawn one `general-purpose` agent per chunk, in parallel, foreground** (you need all of them
   back before synthesizing, and there's nothing else productive to do meanwhile — see the `Agent`
   tool's own foreground-vs-background guidance). **Not `Explore`** — this is explicitly a
   cross-file-consistency / design-doc-audit task, which `Explore`'s own description says it's not
   built for (it reads excerpts, not whole files). Each agent's prompt needs, self-contained (a
   fresh agent shares none of this conversation's context):
   - The distinction between this skill and `cube-chaos-audit` (mod content vs. the skill system).
   - The "one convention, one home" philosophy already established in this repo, so an agent doesn't
     flag every short cross-reference as a duplicate.
   - Its exact file list, with an instruction to read every one FULLY, not excerpts.
   - The structured report format below, and an explicit "read-only, do not edit anything" instruction.
   - A response-length cap (~150-220 lines) so five chunk reports don't blow the synthesizing
     session's own context.
5. **Structured report format**, one line per finding: `[CATEGORY] file:line — one-sentence
   description`. Categories: `GOTCHA` (a fact worth indexing, not every syntax detail), `XREF` (an
   explicit cross-reference already present — cite a few as calibration, don't enumerate all of
   them), `DUPLICATE` (same rule restated instead of linked, cite both locations), `GAP` (relevant
   to a different skill's domain, not linked there), `STALE`/`CONTRADICTION` (outdated, or
   disagrees with something else read), `ROUTING-BUG`/`TABLE-DRIFT` (orchestrator/WORKFLOW_OVERVIEW
   specific), `MISSING` (README omits real content), `OK-VERIFIED` (a handful of spot-checks that
   DID match — keeps the report honest about what's actually fine, not just a bug list).
6. **Synthesize centrally.** Only the orchestrating session sees all chunk reports — this is the
   actual reason to chunk-and-parallelize rather than have each agent try to cross-reference the
   whole tree itself. Correlate across chunks (a GAP flagged from skill A's side and the same GAP
   flagged from skill B's side is one finding, not two), de-duplicate, prioritize.
7. **Verify anything surprising before reporting it as fact.** A subagent's claim describes what it
   *intended* to find, not necessarily ground truth — real precedent, 2026-08-02: an agent reported
   `ThirdParty/Dinosaurs/` as entirely missing from disk, which was alarming enough to warrant
   stopping and checking directly (`git status`, `git reflog`, file timestamps) before relaying it —
   turned out to be the repo owner's own concurrent edit in the same working directory, not data
   loss or a rogue agent. If a finding looks like unexplained data loss or an unexpected commit,
   check `git status`/`git reflog`/`git stash list` yourself and ask the user directly rather than
   either alarming them over nothing or silently absorbing a real problem into a doc-quality bullet
   point.
8. **Any new GAP finding gets a row in `cube-chaos-audit/references/cross-skill-index.md`** as part
   of reporting it (once the user has seen it — don't pre-populate the index with unconfirmed
   findings). A GAP that gets fixed (the missing pointer actually gets added) updates that row's
   link-status instead of leaving a stale "needs link" next to a link that now exists.
9. **Report findings to the user, prioritized, before fixing anything** — the same
   "a finding is a question, not an automatic edit" gate `cube-chaos-audit` uses. A skill's phrasing
   may have been a deliberate choice, and a README's "inaccuracy" might actually be the mod's design
   intent that the code hasn't caught up to yet, not the other way around. Wait for approval,
   per-item is fine the same way `cube-chaos-audit`/Step C accept per-item feedback rather than an
   all-or-nothing block.
10. **When fixing an approved finding, follow the same evidence discipline as everything else in
    this repo** — `CLAUDE.md`'s write-back protocol, `cube-chaos-orchestrator`'s Step D. A fix that
    isn't backed by a grep/launch/decompile citation is a guess wearing a fix's clothes.

## Relationship to other skills

- **`cube-chaos-audit`** — sibling, not parent/child. That skill's own checklist can itself go stale
  or duplicate a rule instead of pointing to it; this skill's routing-table/cross-reference checks
  cover `cube-chaos-audit` too, same as any other skill.
- **`cube-chaos-orchestrator`** — not part of its Step A/B/C content-creation dispatch (this isn't
  "add or edit a mod," it's a different kind of session entirely, the same way
  `cube-chaos-repo-setup` mostly stands alone rather than living inside that dispatch table). See
  `cube-chaos-orchestrator`'s own disambiguation note for how a session should tell "audit this mod"
  and "audit our documentation" apart when a request is ambiguous.
- **`CLAUDE.md`'s research protocol** — this skill is the periodic/batch safety net for the same
  thing that protocol asks every skill to do live, in the moment, every time a finding is written
  back: check whether it's relevant elsewhere, and link it there instead of leaving it isolated.
