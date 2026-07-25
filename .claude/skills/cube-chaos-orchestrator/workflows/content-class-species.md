# Workflow: Class/Species base perk, or a Class+Species synergy

**Before writing any file, run the orchestrator's Step C preview-and-approve gate** for either flow below: print the theoretical spec (granted cubes + the real passive/synergy `Ability:` chain + the `Text:` *derived from that chain*) and get the user's explicit OK, iterating on the printed table until they approve. Two wrinkles specific to this workflow: (1) a class/species color is itself a gated decision — confirm it with the user (per the "ask before picking colors" memory) as part of the spec, not silently; (2) the base-perk flow's color-pick step happens *before drawing* by necessity, but the actual sprite pixels — like every other content type — are still drawn only after the design OK.

## Class or Species base perk (`BelongsTo: CLASS` / `BelongsTo: SPECIES`)

Exactly one of these per class/species — it's what grants the starting cubes.

1. Gather: class/species name, starting cube(s) it grants (`ObtainAction: AddCubeToInventory CubeConstant X`), `LevelRequirement:` if any, what its passive `Ability:` (if any) does.
2. **`cube-chaos-sprite-art`** first this time, not last — before writing anything, pick an unused color via the color-dump snippet (dump the dominant non-background color of every existing class's/species's first tile, avoid reusing one). This color is used in *two* places (the icon fill and the border), so nail it down before drawing.
3. **`cube-chaos-scripting`** — the `PERK:` block, `Ability:` + `Text:` if it has a passive effect, `ObtainAction:` lines for starting cubes.
4. **`cube-chaos-rule-text`** — review the `Description:`.
5. **`cube-chaos-sprite-art`** — draw the icon: solid-filled in the chosen color, centered in the ~19×19 interior, then Style 1 border (`plain_class_border(chosen_color)`) from the border-pattern library — generate it, don't hand-copy pixels from another tile.
6. **Generate/refresh `GameData/<Mod>/Image.png` from this same tile** — this is the mod's Steam Workshop thumbnail, and for a single-class/single-species mod it defaults to that class/species's own base-perk icon (the tile just drawn in step 5), not something separately commissioned. Crop the tile, strip the 1px magenta guide-ring border (fine as an in-game tile edge, reads as an unwanted pink frame standalone), nearest-neighbor upscale to ~500×500 — exact recipe and rationale in `cube-chaos-mod-setup`'s `references/workshop-publishing.md`, don't duplicate it here, just follow it. Re-run this step any time the base-perk icon itself changes. If the mod already has more than one class/species (no single obvious "default" icon), skip the auto-default and ask the user what `Image.png` should show instead.
7. **Test-launch.**

If this mod wants to extend the class color as a family-branding border onto its *other* reward perks too (not just the one base perk), that's a deliberate, optional style choice — see `cube-chaos-sprite-art`'s "Optionally extending the class-color border" section — reuse the exact same RGB, don't invent a near-miss shade.

## Class+Species synergy (`BelongsTo: CLASSSPECIES`)

Named exactly `<ClassName>-<SpeciesName>` (e.g. `DJ-Plant`) — that naming, not a separate field, is what makes the engine recognize it as the synergy for that pair.

1. Gather: which class+species pair, what the synergy effect does.
2. **`cube-chaos-scripting`** — the `PERK:` block and `Ability:`/`Text:`.
3. **`cube-chaos-rule-text`** — review the `Description:`.
4. **`cube-chaos-sprite-art`** — this one's mandatory border is the CLASSSPECIES fancy frame (Style 4 in the border-pattern library — apply the literal baked mask, don't re-extract it from a reference file), and character art placement is **bottom-anchored, not centered**: horizontally centered between cols 6–20, but the lowest non-background pixel must land on row 20 with zero gap. This is the single most commonly-missed detail in this style — verify with an actual bounding-box measurement, not by eye.
5. **Test-launch.**

## If this is an edit, not fresh content

Read `workflows/editing-checklist.md` first.
