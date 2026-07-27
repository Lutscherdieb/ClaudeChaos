# ClaudeChaos

A set of Claude Code skills that build [Cube Chaos](https://store.steampowered.com/app/1958340/Cube_Chaos/) mods — classes, species, cubes, perks, curses, synergies, terrain, even whole battle/campaign scenarios — plus five mods built with them.

## The mods

| Mod | What it is |
|---|---|
| [`GameData/DJ/`](GameData/DJ/README.md) | A full Class: a cube family, a stacking perk line, curses, a consumable, and a synergy portrait for every base-game species. |
| [`GameData/General/`](GameData/General/README.md) | A military-themed Class: Strength grows from the sacrifices and reinforcements of the front line. |
| [`GameData/Unholy/`](GameData/Unholy/README.md) | A winged-demon Species: any allied cube that would be created with 0 hp is instead rescued into a teleporting bomb. |
| [`GameData/Voidling/`](GameData/Voidling/README.md) | A Species built around one neutral cube at the center of the board: True Void. |
| [`GameData/Broker/`](GameData/Broker/README.md) | A gold-and-gambling Class: cube upgrades never run out of uses, and gold income doubles as mana income. |

Each mod's own README has a full preview of its content, rendered to match the game's in-game tooltip style.

## What you need

- [Cube Chaos](https://store.steampowered.com/app/1958340/Cube_Chaos/) installed via Steam.
- To just **play a mod**: nothing else — see that mod's own README.
- To **build or edit mods with the Claude Code skills**: [Claude Code](https://claude.com/claude-code) installed, and this repo's `.claude/` folder placed at the root of your Cube Chaos install (see below).

## Using the Claude Code skills

1. Clone this repo directly into your Cube Chaos install folder (the one with `Cube Chaos.exe` in it) — or copy just the `.claude/` folder there if you don't want the mods too.
2. Open that folder in Claude Code.
3. Say what you want to do — "create a mod", "add a new perk", "edit the DJ mod" — and the `cube-chaos-orchestrator` skill takes it from there.

For how a request actually moves through that skill system (routing, gates, which skill does what), see **[`WORKFLOW_OVERVIEW.md`](WORKFLOW_OVERVIEW.md)**.
