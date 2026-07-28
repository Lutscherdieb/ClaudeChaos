---
name: cube-chaos-audit
description: Use whenever a Cube Chaos mod that already has content needs to be checked for convention/consistency issues rather than having something new added - "audit this mod", "check conventions", "review for consistency", "sanity-check the mod", "is everything up to spec", "check the ability guards", "check the rule text", "check the balancing", "check the sprite borders". Runs a cross-cutting scan against the checklist below (ability guards, rule-text wording, IDENT/Value: balancing, sprite border alignment, mod metadata), reports findings for the user to confirm before fixing anything - a mod's creator may have deliberately deviated from a convention, so a finding is a question, not an automatic edit. Does not itself hold the convention rules; every row links to the one domain skill that owns that rule.
---

# Cube Chaos convention audit

This skill is a **QA pass over content that already exists**, not a source of new conventions. Every
domain skill (`cube-chaos-scripting`, `cube-chaos-rule-text`, `cube-chaos-balancing`, `cube-chaos-sprite-art`,
`cube-chaos-mod-setup`) already documents "what correct looks like," usually with its own grep recipe
for finding violations, discovered one incident at a time. The problem this skill solves is that those
recipes are scattered one-per-skill with no single place listing all of them — so a full-mod check means
either remembering every one from memory or re-deriving them. **The checklist below is that single place.**
It is an index, not a second copy: each row states the check in one line and points at the skill section
that owns the actual rule and its reasoning. If you find yourself typing out *why* a check matters here,
stop — that sentence belongs in the owning skill, not in this table.

## Research protocol — same discipline, one extra step

1. **Check this skill's checklist first** for whether the thing you want to verify already has a row.
2. **If it doesn't, the owning domain skill is still the source of truth** for whether something is actually wrong — read that skill's relevant section (via its own Research protocol if needed) before treating a hunch as a finding.
3. **Write the finding back into the owning skill, exactly as any other domain-skill finding would be** (see `cube-chaos-orchestrator`'s Step D). **Then also add a one-line row to this file's checklist**, in the same edit, if the finding is the kind of thing that could silently go wrong in *already-shipped* content, not just something to get right while writing something new. A gotcha that only matters at authoring time (a parse-order quirk, an argument-count trap) doesn't need a checklist row here — it needs one only if it's realistically something a full-mod scan should catch after the fact.

This keeps the checklist growing at the same rate the domain skills do, without turning into a second place that drifts from them.

## Running an audit

1. **Scope it.** Confirm which mod (or all mods) and which categories from the checklist below to run — default to *all categories* unless the user asked for a narrow one ("just check the rule text", "just the ability guards"). Say up front, briefly, what's about to be scanned.
2. **Detect.** For each in-scope checklist row, run its detection method (`references/detection-recipes.md` has the concrete grep/script for every row — load only the recipes for the categories actually in scope). Grep-based checks are cheap to run for everything; the judgment-based ones (rule-text-vs-ability accuracy, border-pixel-diff, balance-outlier lookup) need an actual read or a small script per hit.
3. **Filter false positives before reporting anything.** A raw grep hit is a candidate, not a finding — read the surrounding chain/context and cross-check it against the owning skill's exact rule (e.g. an `East`/`West` grep hit inside a cube's own *name* isn't a direction; a `TargetCube CubeOfPosition` hit that's a genuine name-guarded swap handler isn't a bug — see `cube-chaos-scripting/references/creation-and-copying.md`). Don't report noise.
4. **Compile one report, don't fix anything yet.** Group findings in two tiers:
   - **Likely bugs / silent-failure shapes** — missing guards, hardcoded East/West, mismatched sprite slot order, misaligned border pixels, a `Description:` placed before its `Ability:`. These are the ones worth fixing with high confidence.
   - **Convention/style deviations** — wording idioms, pricing outliers, color composition, keyword-reference styling. Real, but far more likely to be a deliberate choice the mod's creator already made on purpose — say so, don't frame these as errors.
   Each finding: `file:line`, what's there, what the owning skill says it should look like, and (for tier 1) the concrete fix. If a whole category came back clean, say that plainly too — it was checked, not skipped.
5. **Wait for the user before changing anything.** This is the same weight as `cube-chaos-orchestrator`'s Step C preview-and-approve gate, run in the opposite direction (over existing content instead of a new design) — some of what looks "off" may be exactly what the mod's own creator intended. Accept per-item feedback, not just an all-or-nothing verdict ("fix 1, 3 and 5, leave 2 and 4 — those are on purpose").
6. **Implement only what's approved, through the owning domain skill.** A rule-text fix goes through `cube-chaos-rule-text`'s own conventions, a guard fix through `cube-chaos-scripting`, a border fix through `cube-chaos-sprite-art` — this skill orchestrates the pass, it doesn't reimplement anyone else's rules.
7. **Same gates as any other edit apply afterward**: a fix that touches an `Ability:`/`WorldAbility:` chain or a balance number still needs a test-launch and `Log.txt` check; a pure sprite-pixel or pure wording fix doesn't (see `cube-chaos-orchestrator`'s launch-loop exception). If this mod has a `README.md`, regenerate its preview cards once fixes land.
8. **If a fix reveals a genuinely new, not-yet-catalogued convention, write it back** — to the owning skill first, then a new row here (see Research protocol above).

## The checklist

### DSL & mechanical safety — `cube-chaos-scripting`

| Check | Owning section | Tier |
|---|---|---|
| Every `GainRandomAbilityOfCube`/`RemoveRandomAbility` call site is guarded against a zero-ability source cube | `references/creation-and-copying.md` — "Runtime gotcha: GainRandomAbilityOfCube on a zero-ability cube" | Bug |
| A cube re-acquired by position after creation (`TargetCube CubeOfPosition`/`CubeInDirectionFromCube`) is either a name-guarded swap handler or should be `CopyWithAction` instead | `references/creation-and-copying.md` — "Modifying a cube you just created" | Bug |
| No hardcoded `East`/`West` where `Forwards`/`Backwards` was meant (faction-relative direction) | `references/targeting-movement-board.md` — "Hardcoding East/West..." | Bug |
| A single-`Ability:` `PERK:`'s `Description:` sits immediately *after* its `Ability:` line, not before | `SKILL.md` — "The Text:/Description: requirement" | Bug |
| New `CUBE:`/`PERK:` blocks were appended at file end, not inserted mid-file (sprite slot order intact) | `SKILL.md` — "Block formats"; also `cube-chaos-sprite-art` slot-shifting section | Bug |
| A mod-defined `COMPOUND: ABILITY` reference resolves — not `LOCAL`-scoped from another package, and its package loads after the definer per `Loading_Order.txt` | `references/gotchas-grepped.md` (LOCAL scoping / load-order entries) | Bug |
| A renamed `PERK:`/`CUBE:` didn't leave a stale literal-string self-reference (`StringConstant <OldName>`, `CubeHasName ... <OldName>`) | `references/perk-economy.md` — perk self-reference section | Bug |
| `IsUpgradeFrom:` perks live in their own sprite-less `<ModPrefix>_UpgradePerks.c.txt`, not mixed into the regular perks file | `cube-chaos-sprite-art` — upgrade-perk section | Bug |
| Each perk category (Curse/Blight/Boon/Consumable/Golden/Neutral/CubeUpgrade/Terrain) has its own dedicated `.c.txt` + sprite sheet, never mixed into a generic `Perks.c.txt` | `cube-chaos-mod-setup` | Convention |

### Rule text & wording — `cube-chaos-rule-text`

| Check | Owning section | Tier |
|---|---|---|
| Every `Text:`/`Description:` matches its `Ability:` chain token-for-token — nothing mechanical omitted, nothing cosmetic mentioned, right numbers, right referent for "it" | "Workflow for auditing existing text" | Bug |
| Keyword references use `\A <Name> <params>` for this mod's own compounds and colour-only for base-game keywords, never a hand-written parenthetical duplicating a base tooltip | "Referencing a keyword: \A for our own, colour-only for base-game ones" | Convention |
| An exclusion condition reads as "a non-X ally/cube", never a bolted-on parenthetical ("(not your leader)", "(other than X)") | "Phrasing a 'not X' filter" | Convention |
| Purely cosmetic effects (`PlaySound`, `Animation:`, `CubeColourShift:`, particles) are never described in prose | "Never mention purely cosmetic effects" | Convention |
| No period before the closing `End`; first letter capitalized | "Hard formatting rules" | Convention |
| A spawner's text names the created cube's allegiance but doesn't restate its stats/abilities (baked-in or dynamically granted) | "State a created cube's allegiance..." | Convention |
| A stacking perk's "additional copies..." clarifying sentence is present only when the re-trigger is genuinely non-obvious, and absent when stacking is just the natural result of a "first cube matching X" search | "Describing perks whose stacked copies independently re-trigger" | Convention |

### Numeric balance — `cube-chaos-balancing` / `cube-chaos-scripting`

| Check | Owning section | Tier |
|---|---|---|
| Every obtainable `CUBE:`'s `IDENT rarity aggressive defensive scaling weirdness` and mana/hp sit near the empirical range for that rarity, and were matched against a real analog of similar shape, not derived in isolation | `cube-chaos-balancing` — "Empirical ranges by rarity" | Balance |
| Every priced `PERK:`'s `Value:`/`BalanceCap:` was checked against the right reference class (same real `BelongsTo:` kind), not the mod's own earlier precedent | `references/perk-economy.md` — "Perk economy fields" | Balance |
| No `Value:` on a plain `BelongsTo: <class/species>` reward perk; every Curse/Blight/Boon/Consumable/Golden/Neutral/CubeUpgrade has one (Nightmares are the one category that never does) | `references/perk-economy.md` | Balance |
| Curse `Value:` clusters at round multiples of 50; Blight/Boon signs match category (Blight always negative, Boon always positive) | `references/perk-economy.md` — category sections | Balance |
| Every `CubeUpgrade` perk carries `GainRegeneratingUsesX <N>` as its mandatory downside | `references/perk-economy.md` — "CubeUpgrade-specific conventions" | Balance |

### Sprite & image conventions — `cube-chaos-sprite-art`

| Check | Owning section | Tier |
|---|---|---|
| Every CUBE tile's 1px `RGB(255,0,110)` guide ring sits exactly at the tile's outer edge (offset 0) on all 4 sides, with real content only in the inner 15×15 | "CUBE icon guide grid" | Art |
| Every PERK tile's 1px `RGB(255,0,220)` magenta guide ring sits exactly at offset 0, and the category-specific ring(s) inside it sit at the exact offsets the pattern library specifies | "Border pattern library" | Art |
| A tile's border matches the pattern for its actual category (plain class/species / clean-3-ring / corner-bracket / CLASSSPECIES fancy frame / CubeUpgrade 5px ring) — not a different category's pattern, not freehand | "Border pattern library" | Art |
| No border/ring pixel shows icon-content bleed (a sign it was color-matched from a reference tile instead of generated from fixed geometry) | "Never extract a reusable border by color-matching..." | Art |
| Ground-unit (non-Flying/non-Hovering) CUBE icons are flush to the tile's bottom row, no floating gap | "Ground unit CUBE icons: draw the silhouette flush..." | Art |
| Every finished icon uses ~3–5 colors (base + outline + highlight + accent), never a flat single fill | "Color composition" | Art |
| Sheet dimensions are square and equal `tile_size * ceil(sqrt(block count))`; sprite filename matches its `.txt` file's basename with no cross-mod collision | `SKILL.md` — tile-size / naming sections | Art |
| Workshop `Tag:` set matches the mod's actual content categories, re-audited whenever a new category was added since the tags were last set | `cube-chaos-mod-setup/references/workshop-publishing.md` | Art |

## Reference index

| File | Load when you're... |
|---|---|
| `references/detection-recipes.md` | Actually running an audit — has the concrete grep command or script sketch for every row above, in the same order |

## Notes for extending this checklist

- A new row always names the owning skill/section, never restates the rule. If a check doesn't cleanly belong to one existing domain skill, that's a signal the underlying convention itself hasn't been written down anywhere yet — go write it into the right domain skill first, then add the row here.
- If a category above starts accumulating enough rows to feel unwieldy on its own, split its detection recipes further inside `references/detection-recipes.md` (per-category files) rather than growing this table's Tier/Check columns — the same "content shape, not line count" split rule every other skill here follows.
