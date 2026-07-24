---
name: cube-chaos-orchestrator
description: Entry point for any Cube Chaos modding session - use whenever the user wants to create or edit a mod, or asks for a new/changed Class, Species, Perk, Cube, Curse, Blight, Boon, Nightmare, Terrain perk, Consumable, Golden perk, Neutral perk, CubeUpgrade, or Class+Species synergy. Routes to the right workflow file under workflows/ and sequences the domain skills (cube-chaos-scripting, cube-chaos-rule-text, cube-chaos-sprite-art, cube-chaos-balancing, cube-chaos-mod-setup) so nothing is created half-finished. Trigger on "create a mod", "edit a mod", "new cube", "new perk", "new class", "new species", "new curse", "new synergy", or generally "let's work on the Cube Chaos mod".
---

# Cube Chaos mod orchestrator

This is the entry point for modding work in this repo. It doesn't hold DSL/prose/sprite/balancing knowledge itself — that lives in the domain skills — it holds the *process*: what order things happen in, what's mandatory before something counts as "done," and which workflow file to read for a given content type.

## The one hard rule (full version in `CLAUDE.md`)

**Never edit, move, or delete anything under `GameData/Base_Core/`, `GameData/Characters/`, `GameData/Main/`, `GameData/Extra_Mechanics/`, `GameData/Modding_Example/`, or the root `ModdingInfo.txt`/`ModdingExplanation.txt`.** Reading them (grepping for real examples, sampling sprite colors) is fine and encouraged. Writing to them is not — if a request seems to need it, **stop and explicitly warn the user** rather than doing it or quietly working around it by editing a base file "just this once."

## Step 0 — confirm the game folder root

This skill set and the git repo both live inside the actual Cube Chaos game install (the folder containing `GameData/`, `ModdingInfo.txt`, and `Cube Chaos.exe`), not in some separate project directory. If the current working directory doesn't look like that root (no `GameData/` folder, no `ModdingInfo.txt` alongside it), don't guess — ask the user for the game's install path via `AskUserQuestion` before doing anything else, since every path in this skill set (`GameData/<Mod>/...`, `%APPDATA%/CubeChaos/Log.txt`, etc.) is relative to it.

## Step A — new mod, or editing an existing one?

Ask with `AskUserQuestion` unless it's already obvious from the request (e.g. the user names an existing mod folder or an existing perk to edit).

To find existing mods: read `GameData/Loading_Order.txt`, then drop the known base-game/example package names (`Base_Core`, `Extra_Mechanics`, `Characters`, `Main`, `Modding_Example`) from that list — what's left is the custom mod(s) in this repo. If exactly one remains, confirm it with the user rather than asking which one ("I'll work in the `DJ` mod — let me know if you meant a different one"). If several remain, ask which.

If "new mod" → go to `workflows/new-mod.md`.
If "existing mod" → note which mod folder is active for the rest of the session, **read its `GameData/<Mod>/DESIGN.md` if one exists** (mod-specific design/balance decisions live there — read them so you don't re-litigate settled calls), then go to Step B.

## Step B — what does the user want to do?

Skip the menu if the request already names a clear content type ("add a new Curse called X" goes straight to the matching workflow file below — don't force a wizard step the user already skipped past themselves). Otherwise ask via `AskUserQuestion`, broad first (max 4 options per question):

1. Cube
2. A perk-like thing (reward perk, Curse, Blight, Boon, Nightmare, Terrain perk, Consumable, Golden perk, Neutral perk, or CubeUpgrade)
3. Class, Species, or a Class+Species synergy
4. Not sure / something else — ask them to describe it in their own words instead of forcing a category

If they picked "perk-like thing" and it's still unclear which exact category, ask a second, narrower question (reward perk vs. curse-family vs. CubeUpgrade) — the workflow file itself can usually resolve the last bit of ambiguity through normal conversation instead of another forced menu.

### Dispatch table

| User wants... | Workflow file | Domain skills it will invoke, roughly in order |
|---|---|---|
| A new mod | `workflows/new-mod.md` | `cube-chaos-mod-setup` |
| A `CUBE:` (new or edited) | `workflows/content-cube.md` | `cube-chaos-balancing` (mana/hp/IDENT stats, `IDENT` cubes only) → `cube-chaos-scripting` → `cube-chaos-rule-text` → `cube-chaos-sprite-art` |
| A reward perk, Curse, Blight, Boon, Nightmare, Terrain perk, Consumable, Golden perk, Neutral perk, or CubeUpgrade | `workflows/content-perk-family.md` | `cube-chaos-balancing` (`Value:`/`BalanceCap:`, categories that carry one) → `cube-chaos-scripting` → `cube-chaos-rule-text` → `cube-chaos-sprite-art` |
| A Class or Species base perk, or a Class+Species synergy | `workflows/content-class-species.md` | `cube-chaos-scripting` → `cube-chaos-rule-text` → `cube-chaos-sprite-art` |
| A themed **Dragon evolution line** for a class/species (Egg → Baby → Adult, mimicking the base game's per-class dragons) | `workflows/content-dragon-line.md` | `cube-chaos-scripting` → `cube-chaos-rule-text` → `cube-chaos-sprite-art` (balancing is light — stats anchor to base dragons) |
| *Editing* something that already exists (any type above) | Same workflow file as the content type, but read `workflows/editing-checklist.md` first — it has rules that only apply to edits, not fresh creation | Same as above |

**Suggestible pattern — reach for this when a user asks "what should I add?"** A themed **Dragon
evolution line** (`workflows/content-dragon-line.md`) is a strong, self-contained suggestion for any
class/species mod: it's a high-impact late-game payoff, reuses proven base-game machinery (the stock
`Dragon_Egg`/`GrowingUp` compounds), and instantly brings a mod class to parity with the base roster
(every base class/species ships one). All three of this repo's mods now have one — good precedent to point at.

Every path ends the same way: **`cube-chaos-mod-setup`'s launch-and-check-`Log.txt` loop, at least once since the last edit, before anything is reported as done.** A change that "should work" but hasn't been launched and checked is not done.

**Also part of "done": any mod-specific design/balance decision made this session is recorded in `GameData/<Mod>/DESIGN.md`** (create it if the mod doesn't have one yet). This is a governance rule from `CLAUDE.md` — the core concept, deliberate design choices, per-cube/perk balance anchors, and palette/sprite conventions belong there so the next session inherits them instead of re-deriving them. It's the mod-scoped counterpart to the skill-writeback rule (Step D): skills hold *general* modding knowledge, `DESIGN.md` holds *this mod's* specific decisions.

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

3. Then wait for the user's own words. "OK / go" → implement. "Cost's too high / that's not the trigger I meant / make it simpler" → adjust the *spec table* (not files), reprint the changed item(s), and wait again. Loop until the user OKs. **Ask via `AskUserQuestion` only if genuinely blocked on a design decision** (per the existing "ask ambiguous mechanics" / "ask for content names" / "ask before picking colors" memories) — otherwise plain iteration on the printed table is enough.

4. **Only sprites and file writes happen after the OK.** Mechanics (ability + numbers + rule text) are what the gate approves; the sprite is drawn *after*, once the design is locked, so no pixel work is wasted on a design that gets reshaped. The per-workflow "Sequence" steps run only past this point.

5. **Sanity-check the logic before showing it, and pre-empt silent-failure shapes in the preview itself.** Don't just transcribe the user's literal ask into DSL and wait for them to catch a mechanical break — actively ask "does this actually make sense in play?" If the design has a known silent-failure pattern (create-on-occupied-tile no-op, two spawns targeting the same tile, `Forwards`/`East` faction-flip, an order-of-operations trap — see `cube-chaos-scripting`), **flag it AND print a concrete already-fixed rule that circumvents it**, so the user approves a de-risked design rather than the naive one. Real precedent: `Ritual` first spawned both Imps on the tile above (the on-death one silently no-op'd onto the occupied tile) — that should have been caught and fixed in the preview, not left for the user to spot. See the `feedback_sanity_check_spawn_logic` memory.

6. **If a "simple" approach balloons into unexpected complexity, stop and ask before building the complex version.** The moment an approach crosses from a small edit into a new compound / new state / notably more moving parts than assumed, surface the tradeoff at that fork and let the user choose — "the clean version needs a custom compound because <reason>; the simpler option is <X> with <minor downside>; which do you want?" (via `AskUserQuestion` for a clean either/or). Don't silently build the complex thing. Real precedent: turning "3x Explode 1" into a single "Explode X" quietly required a whole custom `GenericStacking` clone compound; that complexity should have been raised before implementing, not after the user intervened to revert it. See the `feedback_escalate_when_simple_turns_complex` memory (and note the game *does* auto-collapse repeated identical instances into one `Nx <ability>` tooltip line, so "just repeat the stock ability" is usually the simpler right answer anyway).

This gate sits *before* the launch-and-check gate — approve the design, then implement, then launch-and-check.

## Step D — the research protocol every domain skill shares

Each domain skill opens with a `## Research protocol` section, and they all follow the same three steps: **check that skill first → if it doesn't cover the question, go to the base game (read-only) → write the finding back into the skill in the same edit.** Only the middle step differs, because each skill has a different ground truth:

| Skill | Ground truth when this skill comes up short |
|---|---|
| `cube-chaos-scripting` | `ModdingInfo.txt` production lists → `ModdingExplanation.txt` → a real working example grepped from `GameData/**/*.c.txt` |
| `cube-chaos-rule-text` | `ModdingInfo.txt`'s quoted tooltip string for each built-in (canonical phrasing *and* colour) → real `Text:`/`Description:` lines, compared by frequency |
| `cube-chaos-sprite-art` | Pixels measured from real `GameData/*/Sprites/*.c.png`, confirmed across several files (nothing about sprites is documented) |
| `cube-chaos-balancing` | The distribution of real values across the right comparison class, not two or three sampled cubes |
| `cube-chaos-mod-setup` | Real package layouts, then `%APPDATA%/CubeChaos/Log.txt` after an actual launch — the log outranks what the files imply |

**Enforce the write-back.** The research step is only worth its cost once, so a session that had to go to the base game for an answer does not end until that answer is a section in the relevant skill, with its evidence (`file:line`, error text, sample size, or occurrence counts as appropriate). Treat an un-written-back finding the same as an unlaunched content change — the work isn't finished. This is what makes step 1 progressively cheaper instead of every session re-deriving the same conventions.

Note the two root reference files are small enough to consult freely — `ModdingInfo.txt` is ~760 lines and `ModdingExplanation.txt` ~75. Reading them is cheap; the expensive part is rediscovering what they *don't* say, which is exactly what the skills accumulate.

## Domain skill structure: core + `references/`, one shape for every skill

Every domain skill (`cube-chaos-scripting`, `cube-chaos-rule-text`, `cube-chaos-sprite-art`, `cube-chaos-balancing`, `cube-chaos-mod-setup`) follows the same two-tier shape as it grows, regardless of how big it currently is:

- **`SKILL.md` (core)** holds only what a *typical* trigger of that skill needs: the primary syntax/format/convention, the Research protocol section, and anything genuinely needed on nearly every use.
- **`references/<topic>.md`** holds anything situational or deep-dive — a category of gotchas, an undocumented-field deep-dive, a specific mechanic's edge cases — split out as its own file, with a one-line "load this when..." note at the top so it's readable standalone.
- **The split trigger is content shape, not a line-count threshold.** The moment a new section is "you'd only load this if you're doing X specifically," it goes straight into a reference file — don't let it accumulate in the core file first and wait for a size crisis to justify moving it. A skill that's currently 60 lines and a skill that's currently 600 lines follow the identical rule; the only difference is how many reference files exist yet (zero is a completely normal state for a small skill).
- **Once any `references/` files exist, `SKILL.md` gets a "Reference index" table** (file → one-line "load when" description) so a session loads only what it needs instead of the whole skill. `cube-chaos-scripting/SKILL.md` is the canonical example — copy its shape (core sections, then the index table, then the debugging/wrap-up section) rather than reinventing the layout per skill.
- **Every reference file is self-contained**: a title, a one-line "load this when" blurb, then the content — readable via a direct grep/read even by a session that never looked at the index table first.

This is a standing convention, not a one-time cleanup — apply it to any domain skill (existing or new) the first time it grows a genuinely situational section, not retroactively once a skill "feels big."

## Notes for extending this orchestrator

- If a genuinely new content type shows up that doesn't fit the dispatch table (the game adds something new, or this mod needs a mechanic none of the existing categories cover), don't force it into an existing workflow file — add a new one and a new dispatch-table row, the same way `cube-chaos-sprite-art`'s border-pattern-library table is meant to grow as new categories get confirmed.
- Keep this file and the domain skills in sync the way this whole skill set has been maintained so far: when something is discovered the hard way (a DSL gotcha, a wording convention, a border pattern), write it back to the relevant skill before ending the session, not just into the conversation.
