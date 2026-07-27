# Workflow: a new campaign/world map (`NODEMAP:`)

Covers designing a new branching campaign map screen — the node graph the player walks between battles/shops/chests. Most asks in this space are "add a new map that follows the existing ones" (a 4th/5th map, an alternate branch) rather than a wholly new game mode (`SCENARIO: Campaign` itself) — this workflow assumes the former; flag to the user if they actually want a new game-mode entry point, since that's a bigger, less-precedented ask (only one real `SCENARIO: Campaign` exists to copy from).

## Gather before writing anything

- What node types should exist on this map, and roughly how often each should appear (weight) — start from an existing map's node list (`First_Map`/`Second_Map`/`Third_Map`) and note only the deltas (a new node type added, an existing one removed or reweighted, a new `SECRETMODIFIER:`/`EXTRA_DIFFICULTY:` on one).
- Where this map sits in the campaign flow — reached from an existing map's portal, a new perk's `ObtainAction:`, or a new `CHOICE:` branch (see `content-challenge-scenario.md`'s branching-menu section for the `CHOICE:` shape).
- A background colour not already used by an existing map (`0 100 0`/`0 100 100`/`100 100 0`/`110 100 100` are taken).

## Preview-and-approve gate (before the Sequence below)

Print the planned node-type list (name + weight + any `SECRETMODIFIER:`/`EXTRA_DIFFICULTY:`), which existing map's structure will be copied as the base, and how the map is reached/exited, then get the user's explicit OK before writing the file.

## Sequence

1. **`cube-chaos-scenario-scripting`**'s `references/nodemap-generation.md` — pick the closest existing real map, copy its entire `NODEMAP:` body (including the `LAYER:`/`REPLACEINLAYER:`/`REPLACEFIRSTINLAYER:`/`CONNECTION:` block verbatim — these fields have no confirmed derivable semantics, so don't hand-write new ones), and edit only the `MAP_NODE:` declarations plus `BACKGROUND_COLOUR:`/`DEAD_END_SCENARIO:`.
2. If any new `MAP_NODE:` type references a scenario that doesn't exist yet (a new battle type, a new reward node), build that scenario first via `content-battle-scenario.md`/`content-reward-scenario.md`/`content-challenge-scenario.md` as appropriate, then reference it here.
3. Wire the map's entry point (an existing portal's `START_ACTION:`, or a new one) and confirm `RESET_GLOBAL_MODIFIERS`/`ADD_CURRENT_TO_GLOBAL_MODIFIERS` are present if this map follows an earlier one in sequence.
4. **Test-launch** — `cube-chaos-mod-setup`'s loop, then actually play through to and across the new map at least once. Given how undocumented the layer/connection numbers are, a subtly broken graph (an unreachable node, a portal that never appears) won't throw a parse error — this is exactly the silent-failure risk the "copy wholesale" approach in step 1 is meant to avoid, but verify by actually playing it regardless.

## If this is an edit, not a fresh map

Read `workflows/editing-checklist.md` first.
