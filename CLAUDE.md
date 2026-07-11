# Cube Chaos modding — project rules

This repo holds one or more Cube Chaos mods plus the Claude Code skills used to build them. It is meant to be shared (git repo, possibly with strangers), so it deliberately contains **no personal data** — see `.gitignore` for what's kept out (local permission files, etc). Keep it that way: don't put real names, emails, absolute machine-specific paths, or session IDs into anything under version control.

## The one hard rule: never edit base-game files

`GameData/Base_Core/`, `GameData/Characters/`, `GameData/Main/`, `GameData/Extra_Mechanics/`, `GameData/Modding_Example/`, and the root `ModdingInfo.txt` / `ModdingExplanation.txt` are the game's own files, not this repo's mod content. **Never edit, move, or delete anything under those paths — including sprite sheets.** If a task seems to require it (e.g. "just tweak this one base cube," "add my sprite into the base game's own sheet"), **stop and explicitly warn the user instead of proceeding**, even if only part of a larger task touches them. Read from them freely (grepping for real DSL examples, sampling colors, checking conventions) — reading is always fine, writing never is.

All mod content lives under `GameData/<ModName>/`, one folder per mod. `BelongsTo:` can reference base-game classes/species/perks across packages with no special syntax — that's the correct way to "attach" content to base-game systems, never editing the base files themselves.

## Where to start

Use the `cube-chaos-orchestrator` skill (or just say what you want to do — "create a mod", "edit a mod", "add a new perk," etc.) as the entry point for any modding session. It asks new-mod-vs-existing, routes to the right content-type workflow, and makes sure the domain skills below get invoked in the right order and nothing gets marked "done" without a test-launch and log check.

The four domain skills hold the actual technical knowledge and are usually invoked *by* the orchestrator, but are also fine to use directly for a narrow question:
- `cube-chaos-scripting` — the `CUBE:`/`PERK:`/`Ability:` DSL itself.
- `cube-chaos-rule-text` — `Text:`/`Description:` prose conventions.
- `cube-chaos-sprite-art` — sprite sheet sizing, colors, and the full border-pattern library (generate borders from scratch, no reference-file extraction needed).
- `cube-chaos-mod-setup` — mod folder scaffolding, `Loading_Order.txt`, filename-collision pitfalls, the launch-and-check-logs test loop.

## Non-negotiable per-edit consistency rules

- Any `Ability:`/`WorldAbility:` change (new or edited) gets its paired `Text:`/`Description:` written or re-checked in the *same* edit, never as a follow-up. See `cube-chaos-scripting`'s Text:/Description: requirement and `cube-chaos-rule-text`'s "rule text is never edited independently" principle.
- Every content change (new or edited `CUBE:`/`PERK:`) ends with an actual game launch and a `Log.txt` check (`%APPDATA%/CubeChaos/Log.txt`) before being reported as done — silent visual/logic bugs are common and don't always throw parse errors.
- Sprite edits are scoped to exactly the one tile being changed (its full bounding box, including its own border pixels) — never a wider redraw of a shared sheet, and never extract a border by color-matching against a content-bearing reference tile (see `cube-chaos-sprite-art`'s border pattern library for why, and the from-scratch generators that avoid the problem entirely).
