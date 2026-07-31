# Great_Wall — a Cube Chaos battlefields mod

A mod for battlefields (Terrain perks). Right now it holds one: **Great Wall**, a barren field split by a great stone wall, with a spike trap guarding each flank and (on a Boss battle) enemy catapults perched on top.

## Preview — Great_Wall mod content

Each card below is rendered to match the game's own in-game tooltip style (same `dogicapixel` pixel font, same per-category icon border colors and layout) rather than just showing the bare sprite sheet, so you can read the name/rule text of every terrain without launching the game. Full-resolution sprite sheet originals are in `Sprites/`.

### Terrain

<img src="Preview/Great_Wall_TerrainPerks_Great_Wall.png" width="700" alt="Great Wall terrain perk card">

### In-game screenshot

_Not added yet — drop a screenshot in as `Screenshots/Great_Wall.png` and it'll show here:_

<img src="Screenshots/Great_Wall.png" width="700" alt="Great Wall terrain, in game">

## Installing this mod (to play it)

1. Find your Cube Chaos install folder (Steam → right-click Cube Chaos → Manage → Browse local files). It's the folder containing `Cube Chaos.exe` and a `GameData/` subfolder.
2. Copy this folder (`GameData/Great_Wall/`) into `<your Cube Chaos install>/GameData/Great_Wall/`.
3. Launch the game and enable the Mod.

---

**Monorepo-only note, not mod content:** everything above this line (mod files + this README + `Preview/`) is everything this mod actually needs, and is all that would move if `GameData/Great_Wall/` ever becomes its own repo. The regen command below depends on the `.claude/` skills that currently live one level up in the parent repo, not on anything in this folder — it stops working the moment this mod is split out on its own, unless the skill comes with it.

## Regenerating the preview cards (requires the parent repo's `.claude/` skills)

If this mod's content or sprites change, regenerate the images under `Preview/` with:

```
python3 .claude/skills/cube-chaos-sprite-art/scripts/render_preview_cards.py
```

(run from the parent repo's root — the script renders every registered mod, Great_Wall included, by default).
