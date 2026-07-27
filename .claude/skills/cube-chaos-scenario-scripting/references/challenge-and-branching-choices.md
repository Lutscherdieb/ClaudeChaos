# Bespoke challenge battles and branching `CHOICE:` menus

Load this when building a fixed-hand gauntlet battle (a "challenge" or superboss fight) or any branching decision menu (`CHOICE:`/`Choice:`/`Condition:`). All real examples are from `Extra_Mechanics/Challenge_Scenarios.c.txt` and the `CHOICE:`-bodied scenarios scattered through `Extra_Mechanics/NodeMap_Scenarios.c.txt` (`Boss_Repeat`, `End_Of_Everything`, `Nowhere_To_Go`, `Secret_Ending_1`) — the sole source in the base game (see the parent skill's Ground truth section).

## `CHOICE:` — a branching decision menu

```
SCENARIO: Boss_Repeat
 End
CHOICE: 
Another try End
You lost against the boss but your lives allow you to try again End
CubeImage: Death_Ball
Choice: \C66 180 0 Retry the boss fight with new enemy cubes End 
 ReadAScenario Boss_Battle
 Condition: Not HasPerkOrUpgrade PerkConstant Curse_Of_The_Time_Loop
Choice: \C66 180 0 The time loop warps you away! End 
 Nothing
 Condition: HasPerkOrUpgrade PerkConstant Curse_Of_The_Time_Loop
SEnd
```

Shape: `SCENARIO: Name` header (`Info:`/`CubeImage:` optional in the header — real examples put `CubeImage:` in either the header, right after the `CHOICE:` subtitle, or both; it's flexible, not a strict single-location field) → `CHOICE:` → a title line ending `End` → a subtitle/flavor line ending `End` → optionally `CubeImage:` here too → one or more repeatable `Choice:` entries → `SEnd`.

Each `Choice:` entry is:
```
Choice: <label text, may use \C colour codes> End
 <ACTION to run if this option is picked>
 Condition: <BOOLEAN>          (optional — omit for "always available")
```
Both a compact single-line form (`Choice: Hold onto hope: Nothing End Nothing`, from `Nowhere_To_Go`) and the multi-line form above are real and equivalent — use whichever reads more clearly for the action's length. **`Condition:` gates whether that option is even offered** (`Boss_Repeat`'s two options are mutually exclusive via opposite `Not`/plain conditions on the same perk check — the standard idiom for "show option A xor option B depending on state," not two independently-gated options that could both appear). Omitting `Condition:` entirely (every option in `End_Of_Everything`) means the option is unconditionally available.

**This is a general-purpose branching-menu mechanism, not endgame-specific** — any new decision point (a mid-run event with 2-3 outcomes, a themed reward-or-curse trade-off) is a `CHOICE:` scenario, reached the same way any other scenario is (`ReadAScenario <Name>` from a map node's `START_ACTION:`, a perk's `ObtainAction:`, etc.).

## Bespoke fixed-hand challenge battles

The four real "Challenges" (`The_Rich`, `The_Dream`, `The_Eternal`, `The_Replacement`, reached via `End_Of_Everything`'s third choice → `The_Challenges` `NODEMAP:` → one of these) are ordinary battle-type scenarios (same shape as `references/battle-and-terrain-maps.md`'s base `Battle` wrapper) with exactly two differences:

1. **`HAND: faction slot amount CubeName` replaces `RANDOMFITTINGSETUP:`** to give the enemy (always faction `2` in every real example) a fixed, scripted hand instead of a random one:
   ```
   HAND: 2 1 -1 Drill
   HAND: 2 2 -1 Dwarven_Warrior
   HAND: 2 4 -1 Disease
   HAND: 2 5 -1 Fractal_Expansion
   HAND: 2 6 -1 Summer_Winds
   HAND: 2 3 -1 POWERINFLUX
   ```
   `slot` is the hand position (1-6, matching the standard 6-card hand). The `amount` field is `-1` in every real example with no counterexample — reads as "unlimited/no usage cap" for a permanent scripted boss card, but isn't independently confirmed beyond that consistency.

2. **Exactly one extra, thematically-bespoke `WORLDABILITY:` line implements the challenge's actual twist**, on top of the standard `NormalWinLoss` + win/loss redirects:
   - `The_Rich`: `WORLDABILITY: BeforeManaIsGenerated If IsEnemy Culprit If IsLarger EventAmount DoubleConstant 0 NegateX Multiplication DoubleConstant -3 EventAmount` (enemy mana generation ×4).
   - `The_Dream`: `WORLDABILITY: BeforeACubeDies If IsEnemy Victim NegateX DoubleConstant 1` (enemies can't die).
   - `The_Eternal`: `WORLDABILITY: EveryXSeconds DoubleConstant 10 EveryCubeWhich And IsEnemy Test IsALeader Test ChangeHp Subtraction DoubleConstant 1000 HpOfCube Target` (enemy leaders' hp reset to 1000 every 10s).
   - `The_Replacement`: two extra lines — one `AfterACubeIsCreated` granting new enemy cubes +300 hp/leader status/mana generation, one `AtTheStartOfTheBattle` that exiles every non-ally cube and replaces it with a random enemy cube.

   **A new challenge is this same shape: copy a real challenge's structure, keep `HAND:`, and replace only that one bespoke `WORLDABILITY:` line with the new twist.**

`WORLDABILITY: AfterYouLose`/`AfterYouWin` both redirect straight to **`ReadAScenario End_Of_Everything_NO_CHALLENGE`** in every real challenge (not the normal cube-reward `AfterYouWin` payout a standard `Battle` gives) — `End_Of_Everything_NO_CHALLENGE` is the same `CHOICE:` shape as `End_Of_Everything` minus its third "challenge again" option (avoids an infinite challenge-into-challenge loop). A new challenge should redirect the same way on both outcomes, since winning or losing a challenge is meant to return the player to the same ending-choice screen rather than continue the run.
