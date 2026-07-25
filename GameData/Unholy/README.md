# Unholy — a Cube Chaos Species mod

A winged-demon Species: any allied cube that would be created with 0 hp is instead rescued into a teleporting bomb, delivered straight into the enemy backline where it explodes.

## Preview — Unholy mod content

Each card below is rendered to match the game's own in-game tooltip style (same `dogicapixel` pixel font, same per-category icon border colors and layout) rather than just showing the bare sprite sheet, so you can read the name/rule text/value of every cube and perk without launching the game. Full-resolution sprite sheet originals are in `Sprites/`.

### Cubes

<img src="Preview/Unholy_Cubes_Ritual.png" width="700" alt="Ritual cube card">
<img src="Preview/Unholy_Cubes_Imp.png" width="700" alt="Imp cube card">
<img src="Preview/Unholy_Cubes_Cultist.png" width="700" alt="Cultist cube card">
<img src="Preview/Unholy_Cubes_Hellhound.png" width="700" alt="Hellhound cube card">
<img src="Preview/Unholy_Cubes_Plague_Imp.png" width="700" alt="Plague Imp cube card">
<img src="Preview/Unholy_Cubes_Damned_Soul.png" width="700" alt="Damned Soul cube card">
<img src="Preview/Unholy_Cubes_Martyr.png" width="700" alt="Martyr cube card">
<img src="Preview/Unholy_Cubes_Molten_Brimstone.png" width="700" alt="Molten Brimstone cube card">
<img src="Preview/Unholy_Cubes_Brimstone.png" width="700" alt="Brimstone cube card">
<img src="Preview/Unholy_Cubes_Plague_Ritual.png" width="700" alt="Plague Ritual cube card">
<img src="Preview/Unholy_Cubes_Hell_Dragon_Egg.png" width="700" alt="Hell Dragon Egg cube card">
<img src="Preview/Unholy_Cubes_Baby_Hell_Dragon.png" width="700" alt="Baby Hell Dragon cube card">
<img src="Preview/Unholy_Cubes_Hell_Dragon.png" width="700" alt="Hell Dragon cube card">

### Perks

<img src="Preview/Unholy_Perks_Unholy.png" width="700" alt="Unholy species perk card">
<img src="Preview/Unholy_Perks_Hell_Dragon_Egg.png" width="700" alt="Hell Dragon Egg perk card">
<img src="Preview/Unholy_Perks_Baby_Hell_Dragon.png" width="700" alt="Baby Hell Dragon perk card (upgrade of Hell Dragon Egg)">
<img src="Preview/Unholy_Perks_Phylactery.png" width="700" alt="Phylactery perk card">
<img src="Preview/Unholy_Perks_Lichdom.png" width="700" alt="Lichdom perk card (upgrade of Phylactery)">

## Installing this mod (to play it)

1. Find your Cube Chaos install folder (Steam → right-click Cube Chaos → Manage → Browse local files). It's the folder containing `Cube Chaos.exe` and a `GameData/` subfolder.
2. Copy this folder (`GameData/Unholy/`) into `<your Cube Chaos install>/GameData/Unholy/`.
3. Launch the game and enable the Mod.

---

**Monorepo-only note, not mod content:** everything above this line (mod files + this README + `Preview/`) is everything this mod actually needs, and is all that would move if `GameData/Unholy/` ever becomes its own repo. The regen command below depends on the `.claude/` skills that currently live one level up in the parent `ClaudeChaos` repo, not on anything in this folder — it stops working the moment this mod is split out on its own, unless the skill comes with it.

## Regenerating the preview cards (requires the parent repo's `.claude/` skills)

If this mod's content or sprites change, regenerate the images under `Preview/` with:

```
python3 .claude/skills/cube-chaos-sprite-art/scripts/render_preview_cards.py
```

(run from the parent repo's root — the script renders the DJ, General, and Unholy mods by default).
