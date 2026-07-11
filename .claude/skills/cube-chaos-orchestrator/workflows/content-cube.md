# Workflow: a `CUBE:` (new or edited)

## Gather before writing anything

- Name, mana cost, hp/max hp.
- `TOKEN` (not randomly obtainable, e.g. a byproduct created by another cube's ability) vs `IDENT rarity aggressive defensive scaling weirdness` (a real obtainable cube — needs an `AiPlacementRule:` too). If unsure which, ask; don't guess a rarity/stat spread.
- What the ability actually does, in plain language, before touching the DSL — this is what gets handed to `cube-chaos-scripting` and is also the basis for the `Text:` line, so getting it right once here saves a rewrite later.
- Which existing `.c.txt`/`Sprites/*.c.png` pair in the active mod this belongs in (or whether it needs a new one — check the filename-collision pitfall in `cube-chaos-mod-setup` before naming a new file).

## Sequence

1. **`cube-chaos-scripting`** — write the `CUBE:` block, the `Ability:` chain, and its paired `Text:` (every custom `Ability:` needs one, immediately after it — not shared with a sibling ability). Check whether it needs `Visual:` placement-preview lines (any cube with a positional effect — deals damage in front, heals below, etc.) and an `AiPlacementRule:` (required whenever `IDENT` is present).
2. **`cube-chaos-rule-text`** — review the `Text:` wording against what the `Ability:` chain actually does, token by token. Don't skip this even if the wording "looks fine" — the skill's own workflow section exists because accurate-but-oddly-worded text passes every syntax check and still needs a wording pass.
3. **`cube-chaos-sprite-art`** — CUBE icons are 17×17, no border convention (that's a PERK-only thing). Figure out the correct grid slot (icons crop in `CUBE:` block order, top-to-bottom, row-major) and whether the sheet needs resizing to fit a new slot — if so, follow the "editing a single tile" scoping discipline: relocate existing tiles' exact pixels, don't redraw them, when the grid dimension changes.
4. **Test-launch** — `cube-chaos-mod-setup`'s loop. Check for `ABILITY WITHOUT TEXT`, `CANT READ`, `excess End` specifically — these are the errors a miscounted `Ability:` argument produces, and per `cube-chaos-scripting`'s debugging checklist the real mistake is often upstream of where the error is reported.

## If this is an edit, not a fresh cube

Read `workflows/editing-checklist.md` first — the `Text:` re-check and sprite-scoping rules there are mandatory, not optional follow-ups.
