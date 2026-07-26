# Broker — a Cube Chaos Class mod

A gold-and-gambling Class: cube upgrades you buy never run out of uses, every map opens with a free Forge offering only Cube Upgrades, and gold income doubles as mana income.

## Preview — Broker mod content

Each card below is rendered to match the game's own in-game tooltip style (same `dogicapixel` pixel font, same per-category icon border colors and layout) rather than just showing the bare sprite sheet, so you can read the name/rule text/value of every cube and perk without launching the game. Full-resolution sprite sheet originals are in `Sprites/`.

### Cubes

<img src="Preview/Broker_Cubes_All_In.png" width="700" alt="All In cube card">
<img src="Preview/Broker_Cubes_Skyscraper.png" width="700" alt="Skyscraper cube card">
<img src="Preview/Broker_Cubes_Construction_Site.png" width="700" alt="Construction Site cube card">

### Perks

<img src="Preview/Broker_Perks_Broker.png" width="700" alt="Broker class perk card">

## Installing this mod (to play it)

1. Find your Cube Chaos install folder (Steam → right-click Cube Chaos → Manage → Browse local files). It's the folder containing `Cube Chaos.exe` and a `GameData/` subfolder.
2. Copy this folder (`GameData/Broker/`) into `<your Cube Chaos install>/GameData/Broker/`.
3. Launch the game and enable the Mod.

---

**Monorepo-only note, not mod content:** everything above this line (mod files + this README + `Preview/`) is everything this mod actually needs, and is all that would move if `GameData/Broker/` ever becomes its own repo. The regen command below depends on the `.claude/` skills that currently live one level up in the parent `ClaudeChaos` repo, not on anything in this folder — it stops working the moment this mod is split out on its own, unless the skill comes with it.

## Regenerating the preview cards (requires the parent repo's `.claude/` skills)

If this mod's content or sprites change, regenerate the images under `Preview/` with:

```
python3 .claude/skills/cube-chaos-sprite-art/scripts/render_preview_cards.py
```

(run from the parent repo's root — the script renders the DJ, General, Unholy, Voidling, and Broker mods by default).
