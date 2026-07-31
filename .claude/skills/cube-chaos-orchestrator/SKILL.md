---
name: cube-chaos-orchestrator
description: Entry point for any Cube Chaos modding session - use whenever the user wants to create or edit a mod, audit an existing mod for convention issues, or asks for a new/changed Class, Species, Perk, Cube, Curse, Blight, Boon, Nightmare, Terrain perk, Consumable, Golden perk, Neutral perk, CubeUpgrade, Class+Species synergy, battle scenario, campaign/node-map, challenge battle, or reward/economy screen. Routes to the right workflow file under workflows/ (or straight to cube-chaos-audit for a consistency check) and sequences the domain skills (cube-chaos-scripting, cube-chaos-scenario-scripting, cube-chaos-rule-text, cube-chaos-sprite-art, cube-chaos-balancing, cube-chaos-mod-setup) so nothing is created half-finished. Trigger on "create a mod", "edit a mod", "new cube", "new perk", "new class", "new species", "new curse", "new synergy", "new terrain", "battle map", "node map", "campaign map", "challenge scenario", "audit this mod", "check conventions", or generally "let's work on the Cube Chaos mod".
---

# Cube Chaos mod orchestrator

This is the entry point for modding work in this repo. It doesn't hold DSL/prose/sprite/balancing knowledge itself — that lives in the domain skills — it holds the *process*: what order things happen in, what's mandatory before something counts as "done," and which workflow file to read for a given content type.

## The one hard rule (full version in `CLAUDE.md`)

**Never edit, move, or delete anything under `GameData/Base_Core/`, `GameData/Characters/`, `GameData/Main/`, `GameData/Extra_Mechanics/`, `GameData/Modding_Example/`, or the root `ModdingInfo.txt`/`ModdingExplanation.txt`.** Reading them (grepping for real examples, sampling sprite colors) is fine and encouraged. Writing to them is not — if a request seems to need it, **stop and explicitly warn the user** rather than doing it or quietly working around it by editing a base file "just this once."

## Step 0 — confirm the game folder root

This skill set and the git repo both live inside the actual Cube Chaos game install (the folder containing `GameData/`, `ModdingInfo.txt`, and `Cube Chaos.exe`), not in some separate project directory. If the current working directory doesn't look like that root (no `GameData/` folder, no `ModdingInfo.txt` alongside it), don't guess — ask the user for the game's install path via `AskUserQuestion` before doing anything else, since every path in this skill set (`GameData/<Mod>/...`, `%APPDATA%/CubeChaos/Log.txt`, etc.) is relative to it.

## Step 0.5 — first-time repo/preferences setup (once per machine/checkout)

Check whether `.claude/preferences.local.md` exists. If it does, this machine/checkout has already been through setup — say nothing and go straight to Step A. **If it doesn't exist yet**, this is likely the first session on this machine or checkout: don't force a full setup wizard on someone who just wants to get one quick thing done, but do offer it via `AskUserQuestion` ("Looks like this machine hasn't been set up yet — want to run through git-mode and preference setup first (a few minutes), or skip for now and use the recommended defaults?"). Either answer is fine — "skip" just means every preference-driven step later in this session (Step C's gate, sprite effort, README timing, etc.) uses the "Recommended" default documented in `cube-chaos-repo-setup`, not a hard requirement to run setup before doing anything. If they want to run it, hand off to `cube-chaos-repo-setup` before continuing to Step A; it covers git/GitHub mode (own fork, branch on a shared repo, local-only git, or no git at all), a tool/path preflight (git, python3+Pillow, bash, optionally gh/jq), and the personal-preferences questionnaire.

## Step 0.6 — concurrent-session check (only if `session_git_workflow: worktree-gated`)

Skip this entirely if `.claude/preferences.local.md` doesn't exist, or sets `session_git_workflow: off` (or isn't set at all) — normal solo behavior, edit the main tree directly, nothing below applies.

Otherwise, run `git worktree list` once. If it shows nothing beyond the main worktree, and the user hasn't said another session is about to run in parallel, there's no concurrency to isolate against — work directly in the main tree as normal, same as any other session. **Only if `git worktree list` already shows another `session/*` worktree still checked out, or the user says one's coming**, follow `cube-chaos-repo-setup/references/concurrent-sessions.md` to set up this session's own isolated worktree+branch before making any edits, and say so plainly (the user's already-open IDE tabs won't reflect this session's edits until it's merged back).

## Step A — new mod, or editing an existing one?

Ask with `AskUserQuestion` unless it's already obvious from the request (e.g. the user names an existing mod folder or an existing perk to edit).

To find existing mods: read `GameData/Loading_Order.txt`, then drop the known base-game/example package names (`Base_Core`, `Extra_Mechanics`, `Characters`, `Main`, `Modding_Example`) from that list — what's left is the custom mod(s) in this repo. If exactly one remains, confirm it with the user rather than asking which one ("I'll work in the `DJ` mod — let me know if you meant a different one"). If several remain, ask which.

If "new mod" → go to `workflows/new-mod.md`.
If "existing mod" → note which mod folder is active for the rest of the session, then go to Step A.5.

## Step A.5 — add/edit content, or audit what's already there?

Skip this if the request already makes it obvious (naming a specific new perk/cube to add, or explicitly asking to "audit"/"check conventions"/"review for consistency"). Otherwise ask via `AskUserQuestion`, two options: **add or edit content** (goes to Step B), or **audit existing content for convention/consistency issues** (hands off to `cube-chaos-audit` for the rest of the session — it has its own scoping question, its own findings-then-approve gate mirroring Step C below, and its own rules for which fixes need the launch-and-log gate afterward). An audit session doesn't need Step B/C's content-type menu or preview gate at all; it runs entirely inside `cube-chaos-audit`, invoking whichever domain skill owns a given fix once the user approves it.

**The mod being audited doesn't have to be one of this repo's own.** `cube-chaos-audit` also handles a third-party/Workshop mod dropped in purely for review — it detects authorship itself and, for a foreign mod, runs its own short scope questionnaire first (since several checklist rows are this repo's own house style, not universal correctness). Step A's own mod-discovery logic (reading `Loading_Order.txt`) is about *this repo's* mods and doesn't need to find a foreign mod there.

## Step B — what does the user want to do?

Skip the menu if the request already names a clear content type ("add a new Curse called X" goes straight to the matching workflow file below — don't force a wizard step the user already skipped past themselves). Otherwise ask via `AskUserQuestion`, broad first (max 4 options per question):

1. Cube
2. A perk-like thing (reward perk, Curse, Blight, Boon, Nightmare, Consumable, Golden perk, Neutral perk, or CubeUpgrade)
3. Class/Species/synergy, OR a battlefield/map/campaign-screen mechanic (Terrain perk, a new battle type, a campaign node-map, a challenge battle, or a reward/economy screen)
4. Not sure / something else — ask them to describe it in their own words instead of forcing a category

If they picked "perk-like thing" and it's still unclear which exact category, ask a second, narrower question (reward perk vs. curse-family vs. CubeUpgrade) — the workflow file itself can usually resolve the last bit of ambiguity through normal conversation instead of another forced menu. Same for option 3: if it's unclear whether they mean Class/Species/synergy content versus one of the scenario/map mechanics, ask a second question naming the 5 scenario-side options directly (Terrain perk / new battle type / campaign map / challenge battle / reward screen) alongside Class/Species/synergy.

### Dispatch table

| User wants... | Workflow file | Domain skills it will invoke, roughly in order |
|---|---|---|
| A new mod | `workflows/new-mod.md` | `cube-chaos-mod-setup` |
| A `CUBE:` (new or edited) | `workflows/content-cube.md` | `cube-chaos-balancing` (mana/hp/IDENT stats, `IDENT` cubes only) → `cube-chaos-scripting` → `cube-chaos-rule-text` → `cube-chaos-sprite-art` |
| A reward perk, Curse, Blight, Boon, Nightmare, Consumable, Golden perk, Neutral perk, or CubeUpgrade | `workflows/content-perk-family.md` | `cube-chaos-balancing` (`Value:`/`BalanceCap:`, categories that carry one) → `cube-chaos-scripting` → `cube-chaos-rule-text` → `cube-chaos-sprite-art` |
| A Class or Species base perk, or a Class+Species synergy | `workflows/content-class-species.md` | `cube-chaos-scripting` → `cube-chaos-rule-text` → `cube-chaos-sprite-art` |
| A themed **Dragon evolution line** for a class/species (Egg → Baby → Adult, mimicking the base game's per-class dragons) | `workflows/content-dragon-line.md` | `cube-chaos-scripting` → `cube-chaos-rule-text` → `cube-chaos-sprite-art` (balancing is light — stats anchor to base dragons) |
| A **Terrain perk** (a perk that swaps the whole battlefield layout) | `workflows/content-terrain.md` | `cube-chaos-scenario-scripting` (battle-map DSL) → `cube-chaos-scripting` (the `TOKEN` cubes + the `PERK:` wrapper) → `cube-chaos-rule-text` → `cube-chaos-sprite-art` |
| A new **battle-type scenario** (a new kind of normal-ish battle node, not a Terrain swap or a fixed-hand challenge) | `workflows/content-battle-scenario.md` | `cube-chaos-scenario-scripting` → `cube-chaos-rule-text` |
| A new **campaign/world map** (`NODEMAP:` — a branching node-map screen) | `workflows/content-nodemap.md` | `cube-chaos-scenario-scripting` (may fan out to the battle-scenario/reward-scenario/challenge-scenario workflows for any new node types it references) |
| A bespoke **challenge battle** (fixed-hand gauntlet, or a new `CHOICE:` branching menu) | `workflows/content-challenge-scenario.md` | `cube-chaos-scenario-scripting` → `cube-chaos-rule-text` |
| A new **reward/economy map-node** (chest, shop, forge, curse-trade variant) | `workflows/content-reward-scenario.md` | `cube-chaos-scenario-scripting` → `cube-chaos-rule-text` |
| *Editing* something that already exists (any type above) | Same workflow file as the content type, but read `workflows/editing-checklist.md` first — it has rules that only apply to edits, not fresh creation | Same as above |

**Auditing existing content is handled entirely by `cube-chaos-audit`, not this dispatch table** — Step A.5 routes there directly for "does this mod follow its own conventions" requests, as opposed to "add/change this specific thing" requests which go through the table below.

**Suggestible pattern — reach for this when a user asks "what should I add?"** A themed **Dragon
evolution line** (`workflows/content-dragon-line.md`) is a strong, self-contained suggestion for any
class/species mod: it's a high-impact late-game payoff, reuses proven base-game machinery (the stock
`Dragon_Egg`/`GrowingUp` compounds), and instantly brings a mod class to parity with the base roster
(every base class/species ships one). All three of this repo's mods now have one — good precedent to point at.

Every path ends the same way: **`cube-chaos-mod-setup`'s launch-and-check-`Log.txt` loop, at least once since the last edit, before anything is reported as done.** A change that "should work" but hasn't been launched and checked is not done.

**Exception: a pure sprite-pixel edit or a pure `Text:`/`Description:` wording edit needs no test-launch.** If the session's only changes are (a) repainting pixels inside an already-correctly-sized/sliced sheet (no resize, no new/removed tile, no slot-count change) and/or (b) rewording the *content* of an existing `Text:`/`Description:` field while leaving its structure intact (same field keyword, same trailing `End`, no argument/token change) — there is no DSL parse path or mechanical logic for either edit to break. The launch loop exists to catch parse errors and silent logic bugs in `Ability:`/`WorldAbility:` chains and sheet-slot mismatches; neither of those exists for a content-only pixel or wording change. Still launch-and-check whenever the same edit touches sheet dimensions/slot count, or any `Ability:`/trigger-chain/argument-count territory, even if it also happens to touch a sprite or some text.

**After that passes, check whether this mod already has a `GameData/<Mod>/README.md`.** If it does, regenerate its preview cards: re-run `python3 .claude/skills/cube-chaos-sprite-art/scripts/render_preview_cards.py` (from the repo root) whenever content or sprites changed this session, so `GameData/<Mod>/Preview/` never drifts from what's actually in the mod. Skip this only if the session made no content/sprite changes at all (e.g. a pure DSL refactor with no visible/textual change).

**If the mod does NOT yet have a `README.md`, don't create one as part of finishing this change.** Per `cube-chaos-mod-setup`'s README governance section: a README is created late and only on explicit request or your own judgment call that a session's work has landed at a genuinely feature-complete point — and even then, ask the user first rather than creating it silently. Don't let "every path ends with a README regen" become "every path ends with a README" — those are different rules for different situations (an existing README must stay in sync; a nonexistent one is not owed to every change).

## Step C — preview-and-approve gate (before any file is written)

**No obtainable content gets written to a `.c.txt` until its design is previewed and the user has explicitly OK'd it.** This is a hard gate, the same weight as the launch-and-check-`Log.txt` gate at the other end of the flow — the launch gate catches implementation bugs *after* writing; this gate catches design/intent mismatches *before* writing, where a fix is a table edit instead of a re-implementation. The single highest-value thing it catches: **rule text derived from the ability I would actually write, not paraphrased from the user's prompt** — that's exactly where "that's not the trigger I meant" hides, and it's near-free to catch here.

**What triggers the gate:** any *new or edited* CUBE: or PERK-family item whose design is changing — i.e. the change creates or alters an `Ability:`/`WorldAbility:`/`SpecialAction:` chain, or a balance number (mana/hp, `IDENT` rarity/aggressive/defensive/scaling/weirdness, `Value:`/`BalanceCap:`). Class/Species base perks and Class+Species synergies count too (they carry an `Ability:`+`Text:`). It does **not** fire for the pure-cosmetic edits that also skip the launch loop — a pure `Text:`/`Description:` reword with no mechanical change, or a pure sprite-pixel repaint — because there's no *design* being decided, only wording or pixels.

**How to run it (plain preview + free feedback — no plan-mode ceremony, no forced-choice menus):**

1. For each triggered item, before invoking `cube-chaos-scripting` to write anything, build the full theoretical spec and print it as a plain-text preview block:

   ```
   <Mod>_<File> — "<Name>"   [proposed]
     Type / rarity:  CUBE, IDENT, Uncommon        (or PERK category, etc.)
     Cost / stats:   4 mana · 3/3 hp · aggressive   (Value:/BalanceCap: for perk-family)
     Ability (as I'd actually write it):
        Ability: ...the real DSL chain...
     Rule text (DERIVED from that ability, not from your prompt):
        "..."
     Sprite:  concept only, drawn after OK — palette/border named, no pixels yet
   ```

   The ability line is the *real* chain (run `cube-chaos-scripting`/`cube-chaos-balancing` first), and the rule text is generated from that chain via `cube-chaos-rule-text`, **not** a restatement of what the user asked for. If the two diverge, that divergence is the whole point of showing it.

2. If the session creates several items (e.g. a synergy batch), present them **together in one plan**, but accept **per-item feedback** — the user shouldn't have to re-approve nine good items to adjust the tenth.

3. Then wait for the user's own words. "OK / go" → implement. "Cost's too high / that's not the trigger I meant / make it simpler" → adjust the *spec table* (not files), reprint the changed item(s), and wait again. Loop until the user OKs. **Ask via `AskUserQuestion` only if genuinely blocked on a design decision**, and check `.claude/preferences.local.md`'s `ask_before_naming_colors` setting first if it exists (default: on) — otherwise plain iteration on the printed table is enough. This whole gate is itself controlled by `.claude/preferences.local.md`'s `preview_gate` setting (default: on, i.e. exactly as described here) — see `cube-chaos-repo-setup` for where that file comes from.

4. **Only sprites and file writes happen after the OK.** Mechanics (ability + numbers + rule text) are what the gate approves; the sprite is drawn *after*, once the design is locked, so no pixel work is wasted on a design that gets reshaped. The per-workflow "Sequence" steps run only past this point.

5. **Sanity-check the logic before showing it, and pre-empt silent-failure shapes in the preview itself.** Don't just transcribe the user's literal ask into DSL and wait for them to catch a mechanical break — actively ask "does this actually make sense in play?" If the design has a known silent-failure pattern (create-on-occupied-tile no-op, two spawns targeting the same tile, `Forwards`/`East` faction-flip, an order-of-operations trap — see `cube-chaos-scripting`), **flag it AND print a concrete already-fixed rule that circumvents it**, so the user approves a de-risked design rather than the naive one. Real precedent: `Ritual` first spawned both Imps on the tile above (the on-death one silently no-op'd onto the occupied tile) — that should have been caught and fixed in the preview, not left for the user to spot. See the `feedback_sanity_check_spawn_logic` memory.

6. **If a "simple" approach balloons into unexpected complexity, stop and ask before building the complex version.** The moment an approach crosses from a small edit into a new compound / new state / notably more moving parts than assumed, surface the tradeoff at that fork and let the user choose — "the clean version needs a custom compound because <reason>; the simpler option is <X> with <minor downside>; which do you want?" (via `AskUserQuestion` for a clean either/or). Don't silently build the complex thing. Real precedent: turning "3x Explode 1" into a single "Explode X" quietly required a whole custom `GenericStacking` clone compound; that complexity should have been raised before implementing, not after the user intervened to revert it. See the `feedback_escalate_when_simple_turns_complex` memory (and note the game *does* auto-collapse repeated identical instances into one `Nx <ability>` tooltip line, so "just repeat the stock ability" is usually the simpler right answer anyway).

This gate sits *before* the launch-and-check gate — approve the design, then implement, then launch-and-check.

## Step D — the research protocol every domain skill shares

Each domain skill opens with a `## Research protocol` section, and they all follow the same three steps: **check that skill first → if it doesn't cover the question, go to the base game (read-only) → write the finding back into the skill in the same edit.** Only the middle step differs, because each skill has a different ground truth:

| Skill | Ground truth when this skill comes up short |
|---|---|
| `cube-chaos-scripting` | `ModdingInfo.txt` production lists → `ModdingExplanation.txt` → a real working example grepped from `GameData/**/*.c.txt` |
| `cube-chaos-scenario-scripting` | `GameData/Extra_Mechanics/`'s 6 scenario files — the sole and complete implementation of the whole `SCENARIO:`/`MAP:`/`NODEMAP:` layer, not just a convenient example (neither root reference `.txt` documents it) |
| `cube-chaos-rule-text` | `ModdingInfo.txt`'s quoted tooltip string for each built-in (canonical phrasing *and* colour) → real `Text:`/`Description:` lines, compared by frequency |
| `cube-chaos-sprite-art` | Pixels measured from real `GameData/*/Sprites/*.c.png`, confirmed across several files (nothing about sprites is documented) |
| `cube-chaos-balancing` | The distribution of real values across the right comparison class, not two or three sampled cubes |
| `cube-chaos-mod-setup` | Real package layouts, then `%APPDATA%/CubeChaos/Log.txt` after an actual launch — the log outranks what the files imply |

**Enforce the write-back.** The research step is only worth its cost once, so a session that had to go to the base game for an answer does not end until that answer is a section in the relevant skill, with its evidence (`file:line`, error text, sample size, or occurrence counts as appropriate). Treat an un-written-back finding the same as an unlaunched content change — the work isn't finished. This is what makes step 1 progressively cheaper instead of every session re-deriving the same conventions.

Note the two root reference files are small enough to consult freely — `ModdingInfo.txt` is ~760 lines and `ModdingExplanation.txt` ~75. Reading them is cheap; the expensive part is rediscovering what they *don't* say, which is exactly what the skills accumulate.

## Domain skill structure: core + `references/`, one shape for every skill

Every domain skill (`cube-chaos-scripting`, `cube-chaos-scenario-scripting`, `cube-chaos-rule-text`, `cube-chaos-sprite-art`, `cube-chaos-balancing`, `cube-chaos-mod-setup`, `cube-chaos-audit`) follows the same two-tier shape as it grows, regardless of how big it currently is:

- **`SKILL.md` (core)** holds only what a *typical* trigger of that skill needs: the primary syntax/format/convention, the Research protocol section, and anything genuinely needed on nearly every use.
- **`references/<topic>.md`** holds anything situational or deep-dive — a category of gotchas, an undocumented-field deep-dive, a specific mechanic's edge cases — split out as its own file, with a one-line "load this when..." note at the top so it's readable standalone.
- **The split trigger is content shape, not a line-count threshold.** The moment a new section is "you'd only load this if you're doing X specifically," it goes straight into a reference file — don't let it accumulate in the core file first and wait for a size crisis to justify moving it. A skill that's currently 60 lines and a skill that's currently 600 lines follow the identical rule; the only difference is how many reference files exist yet (zero is a completely normal state for a small skill).
- **Once any `references/` files exist, `SKILL.md` gets a "Reference index" table** (file → one-line "load when" description) so a session loads only what it needs instead of the whole skill. `cube-chaos-scripting/SKILL.md` is the canonical example — copy its shape (core sections, then the index table, then the debugging/wrap-up section) rather than reinventing the layout per skill.
- **Every reference file is self-contained**: a title, a one-line "load this when" blurb, then the content — readable via a direct grep/read even by a session that never looked at the index table first.

This is a standing convention, not a one-time cleanup — apply it to any domain skill (existing or new) the first time it grows a genuinely situational section, not retroactively once a skill "feels big."

## Notes for extending this orchestrator

- If a genuinely new content type shows up that doesn't fit the dispatch table (the game adds something new, or this mod needs a mechanic none of the existing categories cover), don't force it into an existing workflow file — add a new one and a new dispatch-table row, the same way `cube-chaos-sprite-art`'s border-pattern-library table is meant to grow as new categories get confirmed.
- Keep this file and the domain skills in sync the way this whole skill set has been maintained so far: when something is discovered the hard way (a DSL gotcha, a wording convention, a border pattern), write it back to the relevant skill before ending the session, not just into the conversation.
- **Any edit to this file's dispatch table, Step B menu, gate sequence (Step C/the launch gate), or the domain-skill list is not finished until `WORKFLOW_OVERVIEW.md` (repo root) is regenerated to match** — its Mermaid diagram and domain-skills table are a rendering of exactly this file's routing logic, and a stale diagram is actively misleading rather than merely incomplete. Treat this the same weight as the write-back rule above: don't end a session that touched this file's routing/gates without also updating `WORKFLOW_OVERVIEW.md` in the same edit. Adding a new workflow file is the common case that touches this: it always adds/changes a dispatch-table row here, which always means a new/changed node in that diagram.
