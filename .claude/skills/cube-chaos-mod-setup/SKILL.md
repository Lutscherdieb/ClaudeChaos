---
name: cube-chaos-mod-setup
description: The folder-scaffolding/load-order mechanics specifically - GameData folder structure, the Description file format, filename-collision pitfalls, and the launch-and-check-logs testing loop. For starting a full modding session (deciding new-vs-existing mod, routing to the right content workflow), use cube-chaos-orchestrator instead, which invokes this skill for the mechanical steps. Trigger directly on narrow asks like "Loading_Order", "mod not loading", "filename collision", or "how do I check the log".
---

# Cube Chaos mod scaffolding & testing workflow

For the DSL used inside the `.c.txt` files themselves (CUBE:/PERK:/Ability: syntax), see the `cube-chaos-scripting` skill. For sprite sheet sizing/coloring, see `cube-chaos-sprite-art`. This skill is just the surrounding plumbing: folder layout, activation, and the test loop.

**Always add new content inside the active mod's own package folder (e.g. `GameData/DJ/`), never into a base-game package (`Base_Core`, `Extra_Mechanics`, `Characters`, `Main`) or another mod's folder — even for content that's conceptually "attached" to a base-game class/species (a new reward perk `BelongsTo:` an existing species, a new synergy for an existing cube, etc).** Cross-package references work fine for this — `BelongsTo: <SpeciesName>` correctly attributes a perk to a species defined in a totally different package with no special syntax, confirmed by adding a DJ-mod perk with `BelongsTo: Fungus` (Fungus itself is defined in `Characters/Species/Fungus.c.txt`) and seeing it picked up cleanly, including the engine's own reward-perk count for that species going up by one. If you catch yourself editing a file under `Base_Core/`, `Characters/`, `Main/`, or `Extra_Mechanics/`, stop and re-home that change into the mod folder instead — do not leave modded content living in the base game's own files, and don't forget to revert any base-game file you already touched by mistake (including any sprite sheet you painted into) back to its original state.

## How the game discovers content

Every top-level folder under `GameData/` is a "package" (Base_Core, Extra_Mechanics, Characters, Main are the base game's own packages). `GameData/Loading_Order.txt` lists which package folders actually get loaded, **in order, one per line**. A folder that exists but isn't listed is completely inert — e.g. `GameData/Modding_Example/` ships with the game but is deliberately absent from `Loading_Order.txt`, so editing it has zero effect. This is a common trap: don't assume a folder is "the mod" just because it looks mod-shaped: check `Loading_Order.txt`.

To create a new mod:

1. Make a new folder: `GameData/<YourModName>/`.
2. Add a `Description` file (plain text, no extension) directly in that folder:
   ```
   ID: <random unique 10-digit number>
   Name: <YourModName>
   Tag: <FreeformTag>
   Tag: <AnotherTag>
   End
   ```
3. Add one or more `.c.txt` files containing your `CUBE:`/`PERK:` definitions (see `cube-chaos-scripting`).
4. Add a `Sprites/` subfolder with `.c.png` files matching each `.c.txt` file's basename (see `cube-chaos-sprite-art`).
5. **Append your folder name as a new line at the end of `GameData/Loading_Order.txt`.** Without this step nothing you wrote will ever load, no matter how correct it is.
6. Give the mod its own `GameData/<YourModName>/README.md` (see below) — every mod folder in this repo keeps one, not just a shared repo-root README.

## Each mod keeps its own `README.md` and `Preview/` folder

Every mod folder (e.g. `GameData/DJ/`) has its own `README.md` — a short description plus a `## Preview` section showing every cube/perk/curse/etc. rendered as a game-accurate tooltip card, not a shared write-up bolted onto the repo-root README. Category subheadings in that Preview section should be bare (`### Cubes`, `### Perks`, ...) rather than listing every item's name in the heading — the cards themselves already show each name, so repeating them in the heading is redundant. Keeping each mod's documentation and preview images inside its own folder means the mod folder stays self-contained (this repo may eventually split one mod per repo — a mod whose docs/images already live inside its own folder needs no rework to become its own repo).

**Keep mod content and monorepo-only tooling notes visually distinct within that README.** The mod's own files, its `README.md` text, and `Preview/` images are genuine mod content — everything that would move if this mod ever became its own repo. The regen command below is not: it depends on the `.claude/` skills living one level up in this monorepo, so it stops working the instant the mod folder is split out on its own. Mark it off clearly (a `---` rule plus an explicit "monorepo-only, not mod content" callout, as done in `GameData/DJ/README.md`) rather than blending it into the rest of the doc as if it were just another mod feature.

The preview images live in `GameData/<Mod>/Preview/` and are generated (never hand-drawn) by `cube-chaos-sprite-art`'s `scripts/render_preview_cards.py` — see that skill's "Rendering README preview cards..." section for what the script does and the reverse-engineered facts (font, border-cropping rules, keyword coloring) it encodes. Re-run it (`python3 .claude/skills/cube-chaos-sprite-art/scripts/render_preview_cards.py` from the repo root) whenever this mod's content or sprites change, so `Preview/` never drifts from what the `.c.txt`/`.c.png` files actually contain. The script defaults to the DJ mod; point its `MOD_DIR`/`OUT_DIR`/`MOD_PREFIX` constants at a different mod folder to reuse it there.

## Filename collisions (a silent, hard-to-diagnose bug)

The engine appears to key sprite/data association by **filename**, not full path. If your mod defines a file named e.g. `Perks.c.txt` and the base game (or another mod) already has `Main/Perks.c.txt`, your content can get silently mis-associated with the OTHER file's sprite sheet — no error, just wrong icons rendered from the wrong sheet. Before naming a file, grep the whole `GameData` tree for that exact basename:

```bash
find GameData -iname "YourProposedName.c.txt"
```

Prefix every file with your mod's name (`DJ_Perks.c.txt`, `DJ_Cubes.c.txt`, `DJ_Synergies.c.txt`) rather than using generic names like `Perks.c.txt`/`Cubes.c.txt`/`Synergies.c.txt` — those are exactly the names the base game itself tends to use.

## The test-and-iterate loop

There is no hot-reload: the game parses all `GameData` content fresh at startup. After every edit:

1. Kill any already-running game process first (`Get-Process -Name javaw | Stop-Process -Force` on Windows) — a stale running instance will not reflect new edits, and you'll waste a cycle thinking a fix didn't work.
2. Launch the game (`Cube Chaos.exe`), wait several seconds for full boot (loading + sprite-cutting takes a couple seconds, but give it ~10-15s margin before checking).
3. Check `%APPDATA%/CubeChaos/Log.txt` (Windows: `C:\Users\<user>\AppData\Roaming\CubeChaos\Log.txt`) for `WARNING`/`ERROR` lines, and check `CrashLog.txt`'s modification time to confirm no new crash occurred. Also check the launched process's own stdout if you redirected it to a file — some errors print there but not to Log.txt.
4. Close the game process again before making further edits (same command as step 1).

### Warnings you will see that are expected/harmless (not bugs)

- `WARNING: CLASS + X HAS 0 REWARD PERKS, BUT ATLEAST ONE HAS 9` — normal if your class only has its base class perk so far and no optional chest-obtainable reward perks yet.
- `WARNING: Missing: <YourClass>-<Species>` (once per species, ~12 lines) — normal until you've written `CLASSSPECIES` synergy perks for that class; each missing one just means that particular class+species combo has no special synergy defined yet.
- `WARNING: Couldn't innitiate steam API, is steam not on?` — unrelated to your mod, appears whenever Steam isn't running alongside the game.

### Scope sprite fixes to exactly the tile you're working on

A user may be hand-editing icons in the same shared sprite sheet PNG in parallel with your own edits in the same session. Confirmed real incident: while fixing one perk icon's border color, an earlier pass had reloaded and resaved a tile's full region instead of touching only that tile's own bounding box, which clobbered a user's in-progress hand-drawn art on that tile. When fixing/updating a single tile in a multi-icon sheet, restrict every read and write to exactly that tile's own `T`×`T` bounding box (including its own border pixels) — never touch, resample, or blanket-resave pixels outside the one tile you're intentionally changing. See `cube-chaos-sprite-art` for the tile-offset math and compositing recipes.

### Errors that mean a real bug in your files

- `WARNING: CUBE/PERK X IN PACKAGE Y ABILITY WITHOUT TEXT` — a custom `Ability:` line has no matching `Text:`/`Description:` right after it. See `cube-chaos-scripting`.
- `ERROR: CANT READ ACTION/ABILITY/GENERAL PERK PART (token) OF PERK X` and `ERROR: excess End in package X` / missing End — a real parse/argument-count bug, almost always located EARLIER in the same ability chain than where the error surfaces (a miscounted argument desyncs everything that follows). See `cube-chaos-scripting` for the common causes and how to hand-count tokens.
- `ERROR: CANT READ ABILITY(Source) <name>` with no "OF PERK X" tag — often means the referenced ability is declared `LOCAL` to a different package and can't be used from yours. See `cube-chaos-scripting`.

When an error message doesn't clearly point at the bug, don't guess blindly — grep `GameData/**/*.c.txt` for real working usages of the exact function/ability name in question and compare token-for-token against your own line.
