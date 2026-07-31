# Detection recipes — one per checklist row, same order as SKILL.md

Load this when actually running an audit. Each recipe finds *candidates* — always filter against the
owning skill's exact rule before treating a hit as a finding (see SKILL.md step 5). Run recipes against
`GameData/<Mod>/*.c.txt` and `GameData/<Mod>/Sprites/*.c.png` only — never against the base-game folders,
whether `<Mod>` is one of ours or a foreign mod dropped in for review. Only run the recipes for rows that
are actually in scope (Universal rows always; house-convention rows only once SKILL.md's scope
questionnaire put that bucket in scope) — a recipe below tagged "(Universal — always check)" or naming a
bucket says which.

## DSL & mechanical safety

- **Zero-ability-guard**: grep the mod for `GainRandomAbilityOfCube` and `RemoveRandomAbility`. For each hit, check the enclosing chain for an `IsLarger AmountOfAbilitiesOfCubeWhich ... DoubleConstant 0` (or unfiltered `AmountOfAbilitiesOfCube`) guard somewhere upstream in the same trigger. No guard = finding.
- **Re-acquire-by-position**: grep `TargetCube CubeOfPosition` and `TargetCube CubeInDirectionFromCube`. For each hit, check whether the surrounding chain branches on a cube name the *originally created* cube couldn't have (the tell for a legitimate name-guarded swap handler). No such branch = likely the silent-no-op bug; should probably be `CreateCubeOnPosition CopyWithAction` instead.
- **East/West**: grep `\bEast\b|\bWest\b` across the mod's `.c.txt` files, excluding matches that are part of a cube/perk *name* (e.g. `Bomber_West`). Any real hit inside an `Ability:`/`WorldAbility:` chain that creates, targets, or checks a position sideways is a candidate — check whether `Forwards`/`Backwards` was actually meant.
- **Description: placement**: for every `PERK:` block with exactly one `Ability:` line, check that its `Description:` line appears after that `Ability:` line, not before, in file order.
- **Block-append-order**: for each `.c.txt`, compare the file's `CUBE:`/`PERK:` block order against the sprite sheet's slot order (row-major crop order). A mismatch means a block was inserted mid-file after the sheet was already drawn — cross-check against `cube-chaos-sprite-art`'s slot math.
- **LOCAL/load-order**: for any `Ability: <Name>` referencing a compound this mod didn't itself define, grep the base game and other mod packages for `COMPOUND: ABILITY \n <Name>` (or `COMPOUND: ACTION`), check it isn't tagged `LOCAL`, and check `Loading_Order.txt` lists the defining package before this mod's own.
- **Stale self-reference**: grep the mod for `StringConstant <PerkOrCubeName>` and `CubeHasName ... <Name>`/`IsSameString NameOfPerk ...` literals, and diff each literal against that perk/cube's actual current name in its own `PERK:`/`CUBE:` header.
- **Upgrade-file separation**: grep each mod `.c.txt` for `IsUpgradeFrom:` and confirm the file it's in is a dedicated `_UpgradePerks.c.txt`, not mixed into the regular (non-upgrade) perks file. Whether that dedicated file also has its own matching `Sprites/*.c.png` is a free choice (real art or the reused-base-icon fallback are both valid) — not itself a finding either way.
- **Perk-category-own-file**: list every distinct `BelongsTo:`/no-`BelongsTo:` category actually used across the mod's `PERK:` blocks, and confirm each category has its own `.c.txt` (and sprite sheet where applicable) rather than sharing a file with a different category.

## Rule text & wording

These need an actual read, not a grep — for every `Ability:`/`WorldAbility:` chain with its own `Text:`/`Description:`/`AbilityText:`, follow `cube-chaos-rule-text`'s own "Workflow for auditing existing text" (read the chain token by token, write down what it does, compare against the prose clause by clause). The narrower checks below can pre-filter candidates before that full read:

- **Base-game keyword color (Universal — always check)**: for every `\C<R> <G> <B> <Name>` reference to a base-game ability inside `Text:`/`Description:`, look up that ability's real color/name in `ModdingInfo.txt` and diff it. A mismatch (wrong RGB, or the mod's own class color used instead) is a finding regardless of who wrote the mod.
- **`\A` idiom for granted keywords, ours or base-game's (house convention — Rule-text wording style)**: grep the mod's `Text:`/`Description:` fields for a lowercase mention of any ability name (this mod's own `COMPOUND: ABILITY` or a real `ModdingInfo.txt` entry), or a hand-written parenthetical/bare-colour mention of a *granted* keyword, instead of `\A <Name> <params>`. Only the removed/tested case (see the owning section's caution) is exempt and should stay bare-coloured, number-before-name. Either shape is a candidate — only worth flagging when this bucket is in scope.
- **"Not X" phrasing**: grep for `\(not |\(other than|excluding` inside `Text:`/`Description:` fields.
- **Cosmetic mentions**: for every `Text:`/`Description:` field, check whether it names `PlaySound`/`Animation:`/`CubeColourShift:`/particle effects that are cosmetic-only in the paired `Ability:` chain.
- **Formatting**: grep for `\. End` (period directly before `End`) and check the first character of every `Text:`/`Description:` field is capitalized.
- **Spawner restatement**: for every `Ability:`/`AbilityText:` that creates a cube, check whether the prose also restates that cube's own baked-in or dynamically-granted stats/abilities (redundant — the game already previews the created cube).
- **Stacking-sentence fit**: for every perk whose stacked copies re-trigger, check whether an "additional copies of this perk..." sentence is present, and whether the mechanism is actually the non-obvious kind that warrants it (see the owning section for the two real examples of each case).

## Numeric balance

- **IDENT range check**: for every obtainable `CUBE:`, pull its `manacost`/`hp`/`IDENT rarity agg def scale weird` line and compare against `cube-chaos-balancing`'s empirical range table for that rarity; flag anything well outside the range column, then check whether a real matched analog justifies it.
- **Value:/BalanceCap: reference-class check**: for every priced `PERK:`, note its actual `BelongsTo:` (or lack thereof) and compare its `Value:`/`BalanceCap:` against the real base-game range for that *same* category (`references/perk-economy.md`'s tables) — not against this mod's own other perks.
- **Illegal/missing Value:**: grep for `Value:` inside any `PERK:` block whose `BelongsTo:` names an actual class/species (should have none), and grep every Curse/Blight/Boon/Consumable/Golden/Neutral/CubeUpgrade block for a missing `Value:` (should have one; Nightmares are the sole exception).
- **Sign/clustering check**: for Curses, check `Value:` is a negative multiple of 50; for Blight/Boon, check the sign matches category.
- **CubeUpgrade downside check**: grep every `BelongsTo: CubeUpgrade`-pool perk's `SpecialAction:` for `GainRegeneratingUsesX` — flag any that lack it.

## Sprite & image conventions

Pixel-level checks need a small script (PIL), not a grep. General pattern: crop each tile at its known offset, read its border-ring pixels, and diff against the expected mask/colors from `cube-chaos-sprite-art`'s recipes (reuse those recipe functions directly rather than re-deriving the mask here).

```python
from PIL import Image

def check_cube_guide_ring(sheet_path, cols, rows, T=17, GUIDE=(255,0,110)):
    im = Image.open(sheet_path).convert("RGB")
    px = im.load()
    mismatches = []
    for idx in range(cols * rows):
        row, col = divmod(idx, cols)
        ox, oy = col * T, row * T
        for x in range(T):
            for (cx, cy) in ((ox + x, oy), (ox + x, oy + T - 1)):
                if px[cx, cy] != GUIDE:
                    mismatches.append((idx, cx, cy, px[cx, cy]))
        for y in range(T):
            for (cx, cy) in ((ox, oy + y), (ox + T - 1, oy + y)):
                if px[cx, cy] != GUIDE:
                    mismatches.append((idx, cx, cy, px[cx, cy]))
    return mismatches  # every entry is a misaligned/missing guide-ring pixel
```

Run the equivalent check for PERK tiles at `T=27`, `GUIDE=(255,0,220)`, then layer in the category-specific ring(s) using the exact `ring_positions`/`clean_3ring_border`/`corner_bracket_border`/`plain_class_border` functions already defined in `cube-chaos-sprite-art/SKILL.md` — generate the *expected* pixel dict for that tile's real category and diff it against the actual crop, rather than hand-rolling a second copy of the mask logic here. A non-empty diff on a real (non-blank) tile is a finding; an entirely blank/unused grid cell is expected to differ (it has no border at all) and isn't one.

`check_cube_guide_ring`'s raw mismatch list serves two different findings depending on scope, so split it before reporting:
- **Universal — trimmed-content check**: keep only mismatches where the actual pixel is neither the guide color nor the tile's plain background color (`BG`, `(0,148,255)` by default) — that's real content sitting where the engine trims it, invisible in-game for any mod. Always check this, own mod or foreign.
- **Sprite authoring & polish bucket — guide-marker check**: keep the mismatches where the pixel *is* background (i.e. the guide marker itself is simply missing, not overwritten by content) — that's our own authoring convention not being followed. Only check this for our own mods, or a foreign mod that opted into the bucket.

- **Border-bleed check**: for any mismatch found above where the wrong pixel is a color that also appears in the tile's own interior/icon art (not a neighboring category's border color), that's the color-matching-bleed failure mode specifically — flag it as such rather than as a generic misalignment.
- **Ground-unit flush check**: for each non-`Flying`/non-`Hovering` CUBE tile, find the lowest non-background pixel row and confirm it's the tile's actual last content row (row 15 of the inner 15×15).
- **Color-count check**: for each finished tile, count distinct non-background, non-guide colors; flag anything at 1–2 (below the ~3–5 convention).
- **Sheet math check**: for each `.c.png`, confirm `width` and `height` are each an exact multiple of `tile_size` (a square `ceil(sqrt(n))` grid is one valid layout, not a requirement — a single-row strip or any other rectangle is equally valid, confirmed via the Dinosaurs! Workshop mod's real, functional non-square sheets) and that `(width / tile_size) * (height / tile_size) >= block count in the matching .txt`; confirm the basename matches its `.txt` file and doesn't collide with any already-loaded base-game or other-mod package name.
- **Tag: check**: read the mod's `Description` file's `Tag:` lines against the actual content categories present (grep for `BelongsTo: Curse/Blight/Boon/Terrain/Consumable/...` etc. across the mod's own files) and flag any category present in content but missing from `Tag:`, or vice versa.

## Design depth

These are judgment calls, not greps — read each candidate's actual `Ability:`/`SpecialAction:` chain before deciding it's a finding, and hold the bar loosely (a "no twist available" or "stacking deliberately left flat" call is a legitimate answer, not a miss):

- **Upgrade mechanical-twist check**: for every `IsUpgradeFrom:` perk, diff its `Ability:`/`SpecialAction:` chain against the base perk it upgrades. If the only difference is a bigger literal number in an otherwise-identical chain shape, check whether a natural twist (new trigger branch, secondary effect, changed target selection) was available and skipped — if the effect genuinely has nothing to hook a twist onto (a plain hp/mana/economy buff), that's a legitimate stat-only upgrade, not a finding.
- **Stacking-value check**: for every non-`Unique` `PERK:`, read what 2+ owned copies actually do (does the re-trigger compound, race on a shared position/resource, or produce no perceptible difference?). For every ability that could plausibly be granted twice to the same cube (from two different sources, or the same source firing more than once), check whether it's a bare/flag ability (redundant regrant, harmless but flat) where a `STACKING`-parameterized version would read as more satisfying, versus one where flat redundancy is fine because a player would never expect it to compound (e.g. a one-time cosmetic tag). Flag only the cases where a cheap fix is plausible and the current behavior would plausibly read as a bug or missed opportunity to a player — not every non-stacking effect.
