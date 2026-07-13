# Workflow: new mod

## What you actually need from the user

**Required:** the mod name. Everything else is derivable or has a sensible default.

**Optional:** a theme/tag or two (e.g. "DJ" mod uses tags describing its flavor). If the user doesn't offer one, either skip it or use one generic tag (e.g. "Custom Content") — don't block on this.

Don't ask about anything else at this stage: no starting cubes, no classes/species, no sprites. The scaffold is meant to be "as empty as can be" — the first real content workflow (a class, a cube, whatever comes next) is what actually populates it.

## What to do

1. Sanitize the mod name into a folder-safe form (spaces → underscores, no special characters) if needed — confirm with the user if the sanitized form differs noticeably from what they typed.
2. Generate a random 10-digit ID yourself (`random.randint(1000000000, 9999999999)` or equivalent) — don't ask the user for this.
3. Invoke `cube-chaos-mod-setup` for the actual mechanics (folder creation, `Description` file format, appending to `Loading_Order.txt`) — that skill is the source of truth for the exact file format and the filename-collision pitfall to check before naming anything. Don't re-derive or duplicate those steps here.
4. Create **only**: the mod folder itself and its `Description` file. No `Sprites/` folder, no `.c.txt` files yet — those get created lazily by whatever content workflow runs next, sized correctly for what's actually in them at that point rather than guessed upfront.
5. Confirm the mod is wired in: `GameData/Loading_Order.txt` has the new folder name appended as its own line.
6. **Do not create a `README.md` yet.** Per `cube-chaos-mod-setup`'s README governance section, a README is created late (on explicit request, or when a session's work reaches a genuinely feature-complete point — and even then, only after asking) — not as part of initial scaffolding. An empty new mod is the earliest possible point in a mod's life, the opposite of "feature-complete," so don't raise the README question yet either; there's nothing to preview.
7. Launch the game once and check `Log.txt` (`%APPDATA%/CubeChaos/Log.txt`) for `WARNING`/`ERROR` lines — an empty mod should load with zero new warnings; if it doesn't, something in the scaffold is wrong before any real content even exists.

## After this

Hand off to Step B of the orchestrator (`../SKILL.md`) — the mod now exists and is empty, so the next natural question is "what do you want to add to it?"
