# How a modding request moves through the workflow

One entry point (`cube-chaos-orchestrator`) routes every request to a content-type workflow, which pulls in whichever domain skills it needs. Two hard gates bookend the actual writing: a design preview before anything is written, and a launch-and-log check before anything is called done.

```mermaid
flowchart TD
    Start(["Request"]) --> Root{"In the game root?"}
    Root -- no --> AskRoot["Ask for install path"]
    Root -- yes --> ModQ{"New or existing mod?"}
    ModQ -- new --> NewMod["new-mod.md"]
    ModQ -- existing --> TypeQ{"What content type?"}

    TypeQ --> Cube["Cube"]
    TypeQ --> Perk["Perk-family:<br/>reward &middot; Curse &middot; Blight &middot; Boon<br/>Nightmare &middot; Consumable &middot; Golden &middot; Neutral &middot; CubeUpgrade"]
    TypeQ --> ClassSp["Class &middot; Species &middot; Synergy &middot; Dragon line"]
    TypeQ --> Scenario["Terrain &middot; Battle type<br/>Node-map &middot; Challenge &middot; Reward screen"]

    Cube --> WCube["content-cube.md"]
    Perk --> WPerk["content-perk-family.md"]
    ClassSp --> WClass["content-class-species.md<br/>content-dragon-line.md"]
    Scenario --> WScenario["content-terrain.md &middot; content-battle-scenario.md<br/>content-nodemap.md &middot; content-challenge-scenario.md<br/>content-reward-scenario.md"]

    WCube --> Skills["Domain skills<br/>scripting &middot; scenario-scripting<br/>rule-text &middot; sprite-art &middot; balancing"]
    WPerk --> Skills
    WClass --> Skills
    WScenario --> Skills

    Skills --> GateC{{"Step C &middot; preview &amp; approve"}}
    GateC -- revise spec --> Skills
    GateC -- OK'd --> Write["Write the files"]
    Write --> ResearchNote["Step D &middot; if base game was consulted,<br/>write the finding back into the skill"]
    ResearchNote --> GateLaunch{{"Launch &amp; check Log.txt"}}
    GateLaunch -- errors --> Skills
    GateLaunch -- clean --> Done(["Done &middot; regen README previews if any exist"])
```

Shapes carry the meaning, so this reads the same whether GitHub renders it light or dark: **rounded ends** are the start/end of a request, **diamonds** are questions/branches, **plain rectangles** are workflow files or write/research steps, and **hexagons** are the two hard gates.

## The two hard gates

- **Before writing (Step C):** no obtainable content gets written until the design is previewed as plain text (ability chain, numbers, rule text derived from that chain) and explicitly OK'd. Catches "that's not the trigger I meant" while it's still a one-line fix, not a re-implementation.
- **After writing (launch & log):** every content change ends with an actual game launch and a `Log.txt` check. Skipped only for a pure sprite-pixel repaint or a pure wording reword — nothing mechanical for either to break.

## Domain skills

| Skill | Covers |
|---|---|
| `cube-chaos-scripting` | `CUBE:`/`PERK:` blocks and the `Ability:`/`WorldAbility:` chain DSL |
| `cube-chaos-scenario-scripting` | `SCENARIO:`/`MAP:`/`NODEMAP:`/`CHOICE:` — battle maps, terrain, campaign maps, challenges, shops/chests |
| `cube-chaos-rule-text` | `Text:`/`Description:` wording and tooltip escape codes |
| `cube-chaos-sprite-art` | Sheet sizing, default colors, the full border-pattern library |
| `cube-chaos-balancing` | Mana/hp/`IDENT` stats and perk `Value:`/`BalanceCap:` pricing |
| `cube-chaos-mod-setup` | Folder scaffolding, `Loading_Order.txt`, the launch-and-log test loop |

---

Source of truth: [`.claude/skills/cube-chaos-orchestrator/SKILL.md`](.claude/skills/cube-chaos-orchestrator/SKILL.md) and its [`workflows/`](.claude/skills/cube-chaos-orchestrator/workflows/) — this page is a reading aid, not a replacement for it.
