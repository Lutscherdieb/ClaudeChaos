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
If "existing mod" → note which mod folder is active for the rest of the session, then go to Step B.

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
| *Editing* something that already exists (any type above) | Same workflow file as the content type, but read `workflows/editing-checklist.md` first — it has rules that only apply to edits, not fresh creation | Same as above |

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

3. Then wait for the user's own words. "OK / go" → implement. "Cost's too high / that's not the trigger I meant / make it simpler" → adjust the *spec table* (not files), reprint the changed item(s), and wait again. Loop until the user OKs. **Ask via `AskUserQuestion` only if genuinely blocked on a design decision** (per the existing "ask ambiguous mechanics" / "ask for content names" / "ask before picking colors" memories) — otherwise plain iteration on the printed table is enough.

4. **Only sprites and file writes happen after the OK.** Mechanics (ability + numbers + rule text) are what the gate approves; the sprite is drawn *after*, once the design is locked, so no pixel work is wasted on a design that gets reshaped. The per-workflow "Sequence" steps run only past this point.

This gate sits *before* the launch-and-check gate — approve the design, then implement, then launch-and-check.

## Notes for extending this orchestrator

- If a genuinely new content type shows up that doesn't fit the dispatch table (the game adds something new, or this mod needs a mechanic none of the existing categories cover), don't force it into an existing workflow file — add a new one and a new dispatch-table row, the same way `cube-chaos-sprite-art`'s border-pattern-library table is meant to grow as new categories get confirmed.
- Keep this file and the domain skills in sync the way this whole skill set has been maintained so far: when something is discovered the hard way (a DSL gotcha, a wording convention, a border pattern), write it back to the relevant skill before ending the session, not just into the conversation.
