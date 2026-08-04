# ClaudeChaos

A set of Claude Code skills that build [Cube Chaos](https://store.steampowered.com/app/1958340/Cube_Chaos/) mods — classes, species, cubes, perks, curses, synergies, terrain, even whole battle/campaign scenarios — plus eight mods built with them.

## The mods

| | Mod | What it is |
|---|---|---|
| <img src="GameData/DJ/Image.png" width="64" alt="DJ mod icon"> | [`GameData/DJ/`](GameData/DJ/README.md) | A full Class: a cube family, a stacking perk line, curses, a consumable, and a synergy portrait for every base-game species. |
| <img src="GameData/General/Image.png" width="64" alt="General mod icon"> | [`GameData/General/`](GameData/General/README.md) | A military-themed Class: Strength grows from the sacrifices and reinforcements of the front line. |
| <img src="GameData/Unholy/Image.png" width="64" alt="Unholy mod icon"> | [`GameData/Unholy/`](GameData/Unholy/README.md) | A winged-demon Species: any allied cube that would be created with 0 hp is instead rescued into a teleporting bomb. |
| <img src="GameData/Voidling/Image.png" width="64" alt="Voidling mod icon"> | [`GameData/Voidling/`](GameData/Voidling/README.md) | A Species built around one neutral cube at the center of the board: True Void. |
| <img src="GameData/Broker/Image.png" width="64" alt="Broker mod icon"> | [`GameData/Broker/`](GameData/Broker/README.md) | A gold-and-gambling Class: cube upgrades never run out of uses, and gold income doubles as mana income. |
| <img src="GameData/DJ_Voidling/Image.png" width="64" alt="DJ_Voidling mod icon"> | [`GameData/DJ_Voidling/`](GameData/DJ_Voidling/README.md) | A small crossover mod bridging DJ + Voidling — requires both to be installed. |
| <img src="GameData/Great_Wall/Image.png" width="64" alt="Great_Wall mod icon"> | [`GameData/Great_Wall/`](GameData/Great_Wall/README.md) | A battlefields mod (Terrain perks) — starts with one: a barren field split by a great wall. |
| <img src="GameData/Crusader/Image.png" width="64" alt="Crusader mod icon"> | [`GameData/Crusader/`](GameData/Crusader/README.md) | A holy-war Class: half the battles on every map become boss battles, and every boss you beat leaves your whole inventory a little harder to kill. |

### A couple of things worth knowing

- **A mod's README isn't hand-assembled — ask for one and its `Preview/` folder gets rendered as real, game-accurate tooltip cards**, not raw sprite sheets: same font, borders, mana coloring, and keyword highlighting as the actual in-game tooltip. Regenerate anytime with:

  ```
  python3 .claude/skills/cube-chaos-sprite-art/scripts/render_preview_cards.py
  ```

  (run from this repo's root — renders every mod registered in its own `render_mod(...)` calls, one PNG per cube/perk/curse/etc. See `cube-chaos-sprite-art`'s "Rendering README preview cards..." section for the details.)

- **Those icons above are the mods' actual Steam Workshop thumbnails**, and they're generated too — each one is that mod's own namesake perk sprite, blown up 20× with no smoothing. Nothing to hand-crop, and nothing to go stale when a sprite gets touched up:

  ```
  python3 .claude/skills/cube-chaos-mod-setup/scripts/render_workshop_image.py
  ```

- **A Terrain perk's battlefield layout can be rendered as a screenshot straight from its map data — no game launch required.** `cube-chaos-scenario-scripting/scripts/render_terrain_screenshot.py` reproduces the real in-game look (chroma-keyed backgrounds, HP-based sprite swaps, and more) so a wrong tile coordinate shows up in seconds, not after a full test-launch.

## What you need

- [Cube Chaos](https://store.steampowered.com/app/1958340/Cube_Chaos/) installed via Steam.
- To just **play a mod**: nothing else — see that mod's own README.
- To **build or edit mods with the Claude Code skills**: [Claude Code](https://claude.com/claude-code) installed, and this repo's `.claude/` folder placed at the root of your Cube Chaos install (see below). I personally recommend using [VS Code](https://code.visualstudio.com/download?_exp_download=d53503e735) with [Claude Code for VS Code](https://marketplace.visualstudio.com/items?itemName=anthropic.claude-code)

## Using the Claude Code skills

1. Clone this repo directly into your Cube Chaos install folder (you can find it in your Steam Library → right-click Cube Chaos → Manage → Browse local files) — or copy just the `.claude/` folder there if you don't want the mods too. Want your own fork instead of working straight off this one, or don't want git involved at all? Either's fine — the setup step below sorts that out.
2. Open that folder in Claude Code.
3. Say what you want to do — "create a mod", "add a new perk", "edit the DJ mod" — and the `cube-chaos-orchestrator` skill takes it from there. First time on a given machine, it'll offer a quick one-time setup pass first (git/GitHub mode, a check that the tools it needs are installed, and a few questions about how you like to work) before getting into the actual mod.

For how a request actually moves through that skill system (routing, gates, which skill does what), see **[`WORKFLOW_OVERVIEW.md`](WORKFLOW_OVERVIEW.md)**.
