# DJ — a Cube Chaos Class mod

A full Class built with the skills in this repo's `.claude/` folder: a Microphone/Speaker/Record/Note cube family, a stacking Echo/Symphony perk line, curses, a consumable, and a synergy portrait for every base-game species.

## Preview — DJ mod content, as the game displays it

Each card below is rendered to match the game's own in-game tooltip style (same `dogicapixel` pixel font, same per-category icon border colors and layout) rather than just showing the bare sprite sheet, so you can read the name/rule text/value of every cube, perk, curse, consumable, and synergy without launching the game. Full-resolution sprite sheet originals are in `Sprites/`.

### Cubes — Microphone, Speaker, Record, Note

<img src="Preview/DJ_Cubes_preview.png" width="700" alt="DJ cube cards: Microphone, Speaker, Record, Note">

### Perks — DJ, Echo, Symphony, Inspiration, Bass Drop, Sampling, Feedback, Final Countdown, Grand Finale, and more

<img src="Preview/DJ_Perks_preview.png" width="700" alt="DJ perk cards">

### Curses — Curse of Atrophy, Wobbly Knee

<img src="Preview/DJ_Curses_preview.png" width="700" alt="DJ curse cards">

### Consumable — Mixtape

<img src="Preview/DJ_Consumables_preview.png" width="700" alt="DJ consumable card: Mixtape">

### Class+Species synergies — one card per base-game species

<img src="Preview/DJ_Synergies_preview.png" width="700" alt="DJ class+species synergy cards">

## Installing this mod (to play it)

1. Find your Cube Chaos install folder (Steam → right-click Cube Chaos → Manage → Browse local files). It's the folder containing `Cube Chaos.exe` and a `GameData/` subfolder.
2. Copy this folder (`GameData/DJ/`) into `<your install>/GameData/DJ/`.
3. Launch the game — Cube Chaos scans `GameData/` for mod folders on startup, so no separate "enable" step is needed.
4. If something doesn't show up, check `%APPDATA%/CubeChaos/Log.txt` for parse errors.

## Regenerating the preview cards

If this mod's content or sprites change, regenerate the images under `Preview/` with:

```
python3 .claude/skills/cube-chaos-sprite-art/scripts/render_preview_cards.py
```

(run from the repo root — the script's `MOD_DIR`/`OUT_DIR`/`MOD_PREFIX` constants point at this mod by default).
