# ClaudeChaos

A set of Claude Code skills that build [Cube Chaos](https://store.steampowered.com/app/1958340/Cube_Chaos/) mods — classes, species, cubes, perks, curses, synergies, terrain, even whole battle/campaign scenarios — plus eight mods built with them.

## The mods

| Mod | What it is |
|---|---|
| [`GameData/DJ/`](GameData/DJ/README.md) | A full Class: a cube family, a stacking perk line, curses, a consumable, and a synergy portrait for every base-game species. |
| [`GameData/General/`](GameData/General/README.md) | A military-themed Class: Strength grows from the sacrifices and reinforcements of the front line. |
| [`GameData/Unholy/`](GameData/Unholy/README.md) | A winged-demon Species: any allied cube that would be created with 0 hp is instead rescued into a teleporting bomb. |
| [`GameData/Voidling/`](GameData/Voidling/README.md) | A Species built around one neutral cube at the center of the board: True Void. |
| [`GameData/Broker/`](GameData/Broker/README.md) | A gold-and-gambling Class: cube upgrades never run out of uses, and gold income doubles as mana income. |
| [`GameData/DJ_Voidling/`](GameData/DJ_Voidling/README.md) | A small crossover mod bridging DJ + Voidling — requires both to be installed. |
| [`GameData/Great_Wall/`](GameData/Great_Wall/README.md) | A battlefields mod (Terrain perks) — starts with one: a barren field split by a great wall. |
| [`GameData/Home_Turf_Advantage/`](GameData/Home_Turf_Advantage/README.md) | A standalone Neutral perk: in boss battles, the terrain's fortified advantage — and any structures on it — ends up on your side instead of the boss's. |

Each mod's own README has a full preview of its content, rendered to match the game's in-game tooltip style.

## What you need

- [Cube Chaos](https://store.steampowered.com/app/1958340/Cube_Chaos/) installed via Steam.
- To just **play a mod**: nothing else — see that mod's own README.
- To **build or edit mods with the Claude Code skills**: [Claude Code](https://claude.com/claude-code) installed, and this repo's `.claude/` folder placed at the root of your Cube Chaos install (see below).

## Using the Claude Code skills

1. Clone this repo directly into your Cube Chaos install folder (the one with `Cube Chaos.exe` in it) — or copy just the `.claude/` folder there if you don't want the mods too. Want your own fork instead of working straight off this one, or don't want git involved at all? Either's fine — the setup step below sorts that out.
2. Open that folder in Claude Code.
3. Say what you want to do — "create a mod", "add a new perk", "edit the DJ mod" — and the `cube-chaos-orchestrator` skill takes it from there. First time on a given machine, it'll offer a quick one-time setup pass first (git/GitHub mode, a check that the tools it needs are installed, and a few questions about how you like to work) before getting into the actual mod.

For how a request actually moves through that skill system (routing, gates, which skill does what), see **[`WORKFLOW_OVERVIEW.md`](WORKFLOW_OVERVIEW.md)**.
