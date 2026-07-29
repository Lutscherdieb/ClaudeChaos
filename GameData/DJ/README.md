# DJ — a Cube Chaos Class mod

A full Class built with the skills in this repo's `.claude/` folder: a cube family, a stacking perk line, curses, a consumable, and a synergy portrait for every base-game species.

## Preview — DJ mod content

Each card below is rendered to match the game's own in-game tooltip style (same `dogicapixel` pixel font, same per-category icon border colors and layout) rather than just showing the bare sprite sheet, so you can read the name/rule text/value of every cube, perk, curse, consumable, and synergy without launching the game. Full-resolution sprite sheet originals are in `Sprites/`.

### Cubes

<img src="Preview/DJ_Cubes_Microphone.png" width="700" alt="Microphone cube card">
<img src="Preview/DJ_Cubes_Speaker.png" width="700" alt="Speaker cube card">

<table>
<tr>
<td valign="middle">On Cube Creation</td>
<td valign="middle"><img src="Preview/DJ_Cubes_Speaker_Beat.gif" width="70" alt="Speaker recoil animation"></td>
</tr>
</table>

<img src="Preview/DJ_Cubes_Record.png" width="700" alt="Record cube card">
<img src="Preview/DJ_Cubes_Note.png" width="700" alt="Note cube card">
<img src="Preview/DJ_Cubes_Keyboard.png" width="700" alt="Keyboard cube card">
<img src="Preview/DJ_Cubes_Bass_Dragon_Egg.png" width="700" alt="Bass Dragon Egg cube card">
<img src="Preview/DJ_Cubes_Baby_Bass_Dragon.png" width="700" alt="Baby Bass Dragon cube card">
<img src="Preview/DJ_Cubes_Bass_Dragon.png" width="700" alt="Bass Dragon cube card">

### Perks

<img src="Preview/DJ_Perks_DJ.png" width="700" alt="DJ perk card">
<img src="Preview/DJ_Perks_Echo.png" width="700" alt="Echo perk card">
<img src="Preview/DJ_Perks_Symphony.png" width="700" alt="Symphony perk card">
<img src="Preview/DJ_Perks_Inspiration.png" width="700" alt="Inspiration perk card">
<img src="Preview/DJ_Perks_Finetuning.png" width="700" alt="Finetuning perk card">
<img src="Preview/DJ_Perks_Mastering.png" width="700" alt="Mastering perk card (upgrade of Finetuning)">
<img src="Preview/DJ_Perks_Bass_Drop.png" width="700" alt="Bass Drop perk card">
<img src="Preview/DJ_Perks_Sampling.png" width="700" alt="Sampling perk card">
<img src="Preview/DJ_Perks_Super_Sampling.png" width="700" alt="Super Sampling perk card (upgrade of Sampling)">
<img src="Preview/DJ_Perks_Feedback.png" width="700" alt="Feedback perk card">
<img src="Preview/DJ_Perks_Final_Countdown.png" width="700" alt="Final Countdown perk card">
<img src="Preview/DJ_Perks_Grand_Finale.png" width="700" alt="Grand Finale perk card (upgrade of Final Countdown)">
<img src="Preview/DJ_Perks_Bass_Dragon_Egg.png" width="700" alt="Bass Dragon Egg perk card">
<img src="Preview/DJ_Perks_Baby_Bass_Dragon.png" width="700" alt="Baby Bass Dragon perk card (upgrade of Bass Dragon Egg)">

### Curses

<img src="Preview/DJ_Curses_Curse_Of_Atrophy.png" width="700" alt="Curse Of Atrophy curse card">
<img src="Preview/DJ_Curses_Wobbly_Knee.png" width="700" alt="Wobbly Knee curse card">

### Consumable

<img src="Preview/DJ_Consumables_Mixtape.png" width="700" alt="Mixtape consumable card">

### Class+Species synergies

<img src="Preview/DJ_Synergies_DJ-Dwarf.png" width="700" alt="DJ + Dwarf synergy card">
<img src="Preview/DJ_Synergies_DJ-Plant.png" width="700" alt="DJ + Plant synergy card">
<img src="Preview/DJ_Synergies_DJ-Crystal.png" width="700" alt="DJ + Crystal synergy card">
<img src="Preview/DJ_Synergies_DJ-Shadow.png" width="700" alt="DJ + Shadow synergy card">
<img src="Preview/DJ_Synergies_DJ-Devourer.png" width="700" alt="DJ + Devourer synergy card">
<img src="Preview/DJ_Synergies_DJ-Remnant.png" width="700" alt="DJ + Remnant synergy card">
<img src="Preview/DJ_Synergies_DJ-Undead.png" width="700" alt="DJ + Undead synergy card">
<img src="Preview/DJ_Synergies_DJ-Moil.png" width="700" alt="DJ + Moil synergy card">
<img src="Preview/DJ_Synergies_DJ-Chaos.png" width="700" alt="DJ + Chaos synergy card">
<img src="Preview/DJ_Synergies_DJ-Fungus.png" width="700" alt="DJ + Fungus synergy card">
<img src="Preview/DJ_Synergies_DJ-Elemental.png" width="700" alt="DJ + Elemental synergy card">
<img src="Preview/DJ_Synergies_DJ-No_Species.png" width="700" alt="DJ + No Species synergy card">

## Installing this mod (to play it)

1. Find your Cube Chaos install folder (Steam → right-click Cube Chaos → Manage → Browse local files). It's the folder containing `Cube Chaos.exe` and a `GameData/` subfolder.
2. Copy this folder (`GameData/DJ/`) into `<your Cube Chaos install>/GameData/DJ/`.
3. Launch the game and enable the Mod.

---

**Monorepo-only note, not mod content:** everything above this line (mod files + this README + `Preview/`) is everything this mod actually needs, and is all that would move if `GameData/DJ/` ever becomes its own repo. The regen command below depends on the `.claude/` skills that currently live one level up in the parent `ClaudeChaos` repo, not on anything in this folder — it stops working the moment this mod is split out on its own, unless the skill comes with it.

## Regenerating the preview cards (requires the parent repo's `.claude/` skills)

If this mod's content or sprites change, regenerate the images under `Preview/` with:

```
python3 .claude/skills/cube-chaos-sprite-art/scripts/render_preview_cards.py
```

(run from the parent repo's root — the script renders the DJ, General, Unholy, Voidling, and Broker mods by default).
