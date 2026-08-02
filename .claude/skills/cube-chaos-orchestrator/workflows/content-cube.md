# Workflow: a `CUBE:` (new or edited)

## Gather before writing anything

- Name, mana cost, hp/max hp.
- `TOKEN` (not randomly obtainable, e.g. a byproduct created by another cube's ability) vs `IDENT rarity aggressive defensive scaling weirdness` (a real obtainable cube — needs an `AiPlacementRule:` too). For an `IDENT` cube, use `cube-chaos-balancing` to pick these numbers (real empirical ranges by rarity, plus what aggressive/defensive/scaling/weirdness actually mean) rather than guessing — if rarity itself is unclear, ask the user; it's a drop-frequency/tone decision the ability chain alone can't answer.
- What the ability actually does, in plain language, before touching the DSL — this is what gets handed to `cube-chaos-scripting` and is also the basis for the `Text:` line, so getting it right once here saves a rewrite later.
- Which existing `.c.txt`/`Sprites/*.c.png` pair in the active mod this belongs in (or whether it needs a new one — check the filename-collision pitfall in `cube-chaos-mod-setup` before naming a new file).

## Preview-and-approve gate (before the Sequence below)

Before writing any file, run the orchestrator's **Step C preview-and-approve gate**: print the theoretical spec (rarity/mana/hp/IDENT stats + the real `Ability:` chain + the `Text:` *derived from that chain*, sprite as concept only) and get the user's explicit OK. Iterate on the printed table — not on files — until they approve. Sprites and the Sequence below happen only after that OK.

## Sequence

1. **`cube-chaos-scripting`** — write the `CUBE:` block, the `Ability:` chain, and its paired `Text:` (every custom `Ability:` needs one, immediately after it — not shared with a sibling ability). Add an `AiPlacementRule:` (required whenever `IDENT` is present), then run the `Visual:` step below.
1b. **`Visual:` placement previews — run the grep, don't eyeball it.** Run `grep -nE 'PositionInDirectionFromPosition|CubeInDirectionFromCube|TopPositionAboveCube' <file>` against the new/edited block, apply the required-vs-omit table in `cube-chaos-scripting/references/authoring-and-inheritance.md`'s `Visual:` section to each hit, and **verify the block's `Visual:` line count equals the number of distinct tile offsets that table produced** (4 touching tiles ⇒ 4 lines). Fixed offset from the cube ⇒ marker required; own tile or a random/dynamic destination ⇒ deliberately none. This is a default applied to every cube, not a judgement call — the earlier soft wording ("check whether it needs…") let 12 cubes ship without markers before it was tightened on 2026-08-02.
2. **`cube-chaos-rule-text`** — review the `Text:` wording against what the `Ability:` chain actually does, token by token. Don't skip this even if the wording "looks fine" — the skill's own workflow section exists because accurate-but-oddly-worded text passes every syntax check and still needs a wording pass.
3. **`cube-chaos-sprite-art`** — CUBE icons are 17×17, no border convention (that's a PERK-only thing). Figure out the correct grid slot (icons crop in `CUBE:` block order, top-to-bottom, row-major) and whether the sheet needs resizing to fit a new slot — if so, follow the "editing a single tile" scoping discipline: relocate existing tiles' exact pixels, don't redraw them, when the grid dimension changes.
4. **Test-launch** — `cube-chaos-mod-setup`'s loop. Check for `ABILITY WITHOUT TEXT`, `CANT READ`, `excess End` specifically — these are the errors a miscounted `Ability:` argument produces, and per `cube-chaos-scripting`'s debugging checklist the real mistake is often upstream of where the error is reported.

## After every test-launch you leave running: print the console command (mandatory, not optional)

**Every time you leave the game running for the user to test, print a ready-to-paste console command for each cube added or changed in this session** — including on a *re-launch* after a fix, not just the first launch of the session:

```
Both AddCubeToInventory CubeConstant <Name> AddCubeToDeck CubeConstant <Name>
```

(or just `AddCubeToInventory CubeConstant <Name>` for inventory only). It works mid-run and mid-battle — it only needs an active campaign — so the user never has to start a fresh run to see new content. Mention the one-time `CONSOLE` key binding (Options → Rebind Keys) if it may not be set up yet. Full grammar: `cube-chaos-mod-setup/references/console-commands.md`.

**Repeat it on every re-launch.** Real failure, 2026-08-02: the command was printed once, then two more launches followed (after a sprite-slot fix and a `SetVariable` fix) without repeating it, and the user had to ask. Printing it once per session is not the rule; printing it once per left-running launch is.

## Do NOT grant a new cube as a temporary starter for testing — use the console command instead

**Retired 2026-08-02 on the user's explicit call** ("we do not need this rule anymore as the console adding is a better approach"). An earlier version of this workflow told you to temporarily add `ObtainAction: AddCubeToInventory ...` to the mod's class/species perk plus a `TYPE Starter` line, then strip them later. **Don't do that anymore.** The console command above achieves the same thing strictly better:

| | Temporary starter grant | Console command |
|---|---|---|
| Files touched | 2 (perk + cube), both needing a later revert | 0 |
| Works mid-run | No — a starter only appears in a **new** run | Yes, mid-battle too |
| Risk if the revert is forgotten | Ships a cube as a permanent starter by accident | None |

So: a new `IDENT` cube gets its real `IDENT`/rarity from the start and stays obtainable-only. **`TYPE Starter` and a class-perk `ObtainAction:` now mean only one thing — "this is a deliberate, permanent starting cube of this class/species"** — never test scaffolding. If a cube genuinely should be a permanent starter, that's a design decision to raise with the user (note the base-game baseline is exactly **2** per class/species, see `cube-chaos-scripting`'s starting-cube baseline), not a testing convenience.

Testing the *real* acquisition flow (does it drop at the right rarity, does `AiPlacementRule:` behave under AI play) still needs real runs — but that was never something a starter grant tested either, since a granted starter bypasses the drop pool entirely.

## If this is an edit, not a fresh cube

Read `workflows/editing-checklist.md` first — the `Text:` re-check and sprite-scoping rules there are mandatory, not optional follow-ups.
