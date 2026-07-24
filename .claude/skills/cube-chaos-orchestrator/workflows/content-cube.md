# Workflow: a `CUBE:` (new or edited)

## Gather before writing anything

- Name, mana cost, hp/max hp.
- `TOKEN` (not randomly obtainable, e.g. a byproduct created by another cube's ability) vs `IDENT rarity aggressive defensive scaling weirdness` (a real obtainable cube — needs an `AiPlacementRule:` too). For an `IDENT` cube, use `cube-chaos-balancing` to pick these numbers (real empirical ranges by rarity, plus what aggressive/defensive/scaling/weirdness actually mean) rather than guessing — if rarity itself is unclear, ask the user; it's a drop-frequency/tone decision the ability chain alone can't answer.
- What the ability actually does, in plain language, before touching the DSL — this is what gets handed to `cube-chaos-scripting` and is also the basis for the `Text:` line, so getting it right once here saves a rewrite later.
- Which existing `.c.txt`/`Sprites/*.c.png` pair in the active mod this belongs in (or whether it needs a new one — check the filename-collision pitfall in `cube-chaos-mod-setup` before naming a new file).

## Preview-and-approve gate (before the Sequence below)

Before writing any file, run the orchestrator's **Step C preview-and-approve gate**: print the theoretical spec (rarity/mana/hp/IDENT stats + the real `Ability:` chain + the `Text:` *derived from that chain*, sprite as concept only) and get the user's explicit OK. Iterate on the printed table — not on files — until they approve. Sprites and the Sequence below happen only after that OK.

## Sequence

1. **`cube-chaos-scripting`** — write the `CUBE:` block, the `Ability:` chain, and its paired `Text:` (every custom `Ability:` needs one, immediately after it — not shared with a sibling ability). Check whether it needs `Visual:` placement-preview lines (any cube with a positional effect — deals damage in front, heals below, etc.) and an `AiPlacementRule:` (required whenever `IDENT` is present).
2. **`cube-chaos-rule-text`** — review the `Text:` wording against what the `Ability:` chain actually does, token by token. Don't skip this even if the wording "looks fine" — the skill's own workflow section exists because accurate-but-oddly-worded text passes every syntax check and still needs a wording pass.
3. **`cube-chaos-sprite-art`** — CUBE icons are 17×17, no border convention (that's a PERK-only thing). Figure out the correct grid slot (icons crop in `CUBE:` block order, top-to-bottom, row-major) and whether the sheet needs resizing to fit a new slot — if so, follow the "editing a single tile" scoping discipline: relocate existing tiles' exact pixels, don't redraw them, when the grid dimension changes.
4. **Test-launch** — `cube-chaos-mod-setup`'s loop. Check for `ABILITY WITHOUT TEXT`, `CANT READ`, `excess End` specifically — these are the errors a miscounted `Ability:` argument produces, and per `cube-chaos-scripting`'s debugging checklist the real mistake is often upstream of where the error is reported.

## Default: make a new obtainable cube testable-first (grant it as a starter during development)

**For a new `IDENT` cube in a mod that has its own class/species, default to temporarily granting it as a starting cube of that class/species while it's being built and tuned**, then narrow it to obtainable-only once the user is satisfied. A freshly-added `IDENT` cube is effectively unfindable in play — it competes against the entire global drop pool, so the user can iterate for a long time without ever seeing it. Granting it as a starter guarantees it's in hand every run, immediately.

- **How:** add `ObtainAction: AddCubeToInventory CubeConstant <Name>` to the mod's class/species base perk (the `BelongsTo: CLASS`/`BelongsTo: SPECIES` perk), and give the cube a `TYPE Starter` line (inventory-sorting only, matches the base-game starter convention). The cube keeps its `IDENT` — it's *both* a starter and obtainable during this phase.
- **The revert is trivial and that's the whole point:** converting to obtainable-only later is just deleting those `ObtainAction:` lines (and the `TYPE Starter`). So bias toward starter-first every time — the cost of "too accessible while testing" is one throwaway line per cube, whereas the cost of "can't find it to test" is unbounded iteration time.
- **When the user is satisfied, ask** whether to (a) keep it as a permanent starter, or (b) narrow to obtainable-only — don't silently strip it. Note the base-game convention is exactly **2** starters per class/species (see `cube-chaos-scripting`'s starting-cube baseline); a mod that keeps many starters sits above that power/variety baseline, which is a legitimate choice but worth surfacing.
- **Doesn't apply** if the mod has no class/species of its own to hang starters on (a pure cube-pool mod) — there's nothing to attach an `ObtainAction:` to. Fall back to the user testing via drops, or temporarily bumping rarity, in that case.
- **Record the eventual decision** (permanent starters vs. obtainable-only) in the mod's `DESIGN.md`, per the governance rule.

## If this is an edit, not a fresh cube

Read `workflows/editing-checklist.md` first — the `Text:` re-check and sprite-scoping rules there are mandatory, not optional follow-ups.
