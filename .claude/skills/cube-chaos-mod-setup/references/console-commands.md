# In-game console commands (cheats/debug), reverse-engineered 2026-08-01

Neither `ModdingInfo.txt` nor `ModdingExplanation.txt` mentions a console at all — this was entirely undiscoverable
from the docs and was resolved by decompiling `Game.class`/`InputHandler.class`/`ErrorScreen.class`/`Campaign.class`
from `Cube Chaos.jar` (see [[reference-jar-decompile-technique]] for the method: bundled `jre/bin/java.exe` + CFR).
Cross-checked against real `GameData/**/*.c.txt` usages to confirm exact syntax, not just the Java parsing logic.

## Enabling and using it

There is no default keybind (`InputHandler.class`: `new Input("CONSOLE", null, ...)` — the `null` is the default
key). Bind one yourself: in-game **Options → Rebind Keys**, bind any key to `CONSOLE` (confirmed working by the user
directly, matches the decompile). Once bound:

- Press the bound key to open a text field at the bottom of the screen.
- Type a command, **Enter** executes it (`ExecuteConsole` defaults to Enter).
- **Up arrow** re-fills the field with the last executed command if the field is currently empty (`RepeatConsole`
  defaults to Up) — handy for re-running the same cheat after each relaunch during a test session.
- **Ctrl+V** pastes from the system clipboard directly into the console field.
- The bound key again, or typing exactly the key's own bound character while the field is empty, closes the console.
- A failed parse flashes the console text red for ~2 seconds (`ConsoleErrorTime`) and does **not** close the console,
  so you can correct and resubmit without retyping.

## What a command actually is

The typed line is tokenized with the game's own word-splitter and handed to `Library.ReadAction()` — **the exact
same parser used for every `Ability:`/`ObtainAction:`/`ClickAction:` field in every `.c.txt` file**, base-game or
modded. This means: **one console command = one `Action:` expression in the normal prefix-notation DSL** (see
`cube-chaos-scripting`), including `CubeConstant <Name>`/`PerkConstant <Name>` for referencing any cube/perk (base
game or from any loaded mod, including one currently in development), and `Both <Action> <Action>` to chain more
than one effect in a single line. A bare number works for a `DOUBLE` argument without needing `DoubleConstant`
(confirmed real usage: `GameData/Characters/Classes/Programmer.c.txt:64`, `ChangeCurrency -20`).

One special non-DSL command exists: **`ERROR`** (aliases `SHOWERROR`/`SHOWERRORS`/`ERRORS`, case-insensitive) opens
the in-game `ErrorScreen`, listing `Library.Errors` and `Library.Warnings` — the exact same collection that produces
`Log.txt`'s `ERROR`/`WARNING` lines — colour-coded red/cyan, with a **"Copy to clipboard"** button. This is a live,
in-session way to check whether your mod's files parsed cleanly, without leaving the game or waiting for exit to
read `Log.txt`. Doesn't replace the `Log.txt` check in the test loop below (that's still what should be reported as
the pass/fail signal for automated verification), but useful for a human doing rapid manual iteration.

### Useful commands for testing content mid-development

```
AddCubeToInventory CubeConstant Armored_Eye
AddCubeToDeck CubeConstant Stone
ObtainPerk PerkConstant Elemental
ChangeCurrency 1000
GrantXP 500
Both AddCubeToInventory CubeConstant Your_New_Cube AddCubeToDeck CubeConstant Your_New_Cube
```

`CubeConstant`/`PerkConstant` resolve by the same name-lookup as everywhere else in the DSL — a cube/perk defined in
the mod currently being worked on (once it's loaded and parses cleanly) is addressable exactly the same as a
base-game one. **This has fully REPLACED the old "temporarily grant a new cube as a starter to make it findable"
test convention (retired 2026-08-02 by the user: "we do not need this rule anymore as the console adding is a
better approach").** Never edit a class/species perk's `ObtainAction:` just to make new content testable — bind the
console once and `AddCubeToInventory`/`AddCubeToDeck` it straight into the *current* run instead. The console wins
on every axis: zero files touched, nothing to revert, and it works mid-run and mid-battle whereas a starter grant
only takes effect in a brand-new run. `TYPE Starter` + a class-perk `ObtainAction:` now exclusively mean "a
deliberate, permanent starting cube," never test scaffolding — see `cube-chaos-orchestrator`'s `content-cube.md`
for the full comparison and the rule that replaced it.

Full `Action:`/`BOOLEAN:` grammar (all argument types, every built-in) is in `ModdingInfo.txt` from the `Action:`
header (~line 253) onward.

### Execution context

The console builds `Event E = new Event(Game)`; if a battle is currently running (`Game.World != null`), `E.Target`
and `E.Caster` are set to that battle's `WorldCube`. Outside of battle (e.g. on the campaign/node map), `E.Caster`
is a placeholder cube tied to the `Game` instance rather than `null`. Most of the cheat-relevant actions above
(`AddCubeToInventory`, `AddCubeToDeck`, `ObtainPerk`, ...) only require `E.Caster.Game.Campaign != null` to fire —
confirmed by decompiling `ActionAddCubeToInventory`/`ActionAddCubeToDeck` — so **they work both mid-battle and on
the campaign map**, as long as an actual campaign/run is loaded (not from the main menu, where there's no
`Campaign` yet).
