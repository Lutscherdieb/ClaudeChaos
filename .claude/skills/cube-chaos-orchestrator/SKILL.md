---
name: cube-chaos-orchestrator
description: Entry point for any Cube Chaos modding session - use whenever the user wants to create or edit a mod, or asks for a new/changed Class, Species, Perk, Cube, Curse, Blight, Boon, Nightmare, Terrain perk, Consumable, Golden perk, Neutral perk, CubeUpgrade, or Class+Species synergy. Routes to the right workflow file under workflows/ and sequences the domain skills (cube-chaos-scripting, cube-chaos-rule-text, cube-chaos-sprite-art, cube-chaos-mod-setup) so nothing is created half-finished. Trigger on "create a mod", "edit a mod", "new cube", "new perk", "new class", "new species", "new curse", "new synergy", or generally "let's work on the Cube Chaos mod".
---

# Cube Chaos mod orchestrator

This is the entry point for modding work in this repo. It doesn't hold DSL/prose/sprite knowledge itself — that lives in the four domain skills — it holds the *process*: what order things happen in, what's mandatory before something counts as "done," and which workflow file to read for a given content type.

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
| A `CUBE:` (new or edited) | `workflows/content-cube.md` | `cube-chaos-scripting` → `cube-chaos-rule-text` → `cube-chaos-sprite-art` |
| A reward perk, Curse, Blight, Boon, Nightmare, Terrain perk, Consumable, Golden perk, Neutral perk, or CubeUpgrade | `workflows/content-perk-family.md` | `cube-chaos-scripting` → `cube-chaos-rule-text` → `cube-chaos-sprite-art` |
| A Class or Species base perk, or a Class+Species synergy | `workflows/content-class-species.md` | `cube-chaos-scripting` → `cube-chaos-rule-text` → `cube-chaos-sprite-art` |
| *Editing* something that already exists (any type above) | Same workflow file as the content type, but read `workflows/editing-checklist.md` first — it has rules that only apply to edits, not fresh creation | Same as above |

Every path ends the same way: **`cube-chaos-mod-setup`'s launch-and-check-`Log.txt` loop, at least once since the last edit, before anything is reported as done.** A change that "should work" but hasn't been launched and checked is not done.

**After that passes, regenerate the mod's own README preview.** Every mod folder keeps a `GameData/<Mod>/README.md` with a card-style preview of its content (see `cube-chaos-sprite-art`'s "Rendering README preview cards..." section) — re-run `python3 .claude/skills/cube-chaos-sprite-art/scripts/render_preview_cards.py` (from the repo root) whenever content or sprites changed this session, so the preview images under `GameData/<Mod>/Preview/` never drift from what's actually in the mod. Skip this only if the session made no content/sprite changes at all (e.g. a pure DSL refactor with no visible/textual change).

## Notes for extending this orchestrator

- If a genuinely new content type shows up that doesn't fit the dispatch table (the game adds something new, or this mod needs a mechanic none of the existing categories cover), don't force it into an existing workflow file — add a new one and a new dispatch-table row, the same way `cube-chaos-sprite-art`'s border-pattern-library table is meant to grow as new categories get confirmed.
- Keep this file and the domain skills in sync the way this whole skill set has been maintained so far: when something is discovered the hard way (a DSL gotcha, a wording convention, a border pattern), write it back to the relevant skill before ending the session, not just into the conversation.
