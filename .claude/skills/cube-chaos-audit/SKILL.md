---
name: cube-chaos-audit
description: Use whenever a Cube Chaos mod - one of ours or a third party's - that already has content needs to be checked for correctness/convention issues rather than having something new added - "audit this mod", "check conventions", "review for consistency", "sanity-check the mod", "is everything up to spec", "check the ability guards", "check the rule text", "check the balancing", "check the sprite borders", "review someone else's mod", "check this workshop mod". Runs a cross-cutting scan against the checklist below (ability guards, rule-text wording, IDENT/Value: balancing, sprite border alignment, mod metadata), reports findings for the user to confirm before fixing anything - a mod's creator may have deliberately deviated from a convention, so a finding is a question, not an automatic edit. For a mod this repo didn't author, opens with a short scope questionnaire since several rows are this repo's own house style rather than universal correctness. Does not itself hold the convention rules; every row links to the one domain skill that owns that rule.
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

## Two tiers: Universal vs. house convention

This skill runs against this repo's own mods *and* against mods other people made (a Workshop download, a
friend's package, anything dropped into `GameData/` for review) — and those two cases don't warrant the
same checks. Every row in the checklist below carries a **Scope**:

- **Universal** — reflects the actual game engine's behavior or the base game's own real, reverse-engineered
  conventions (a guard the engine will genuinely no-op without, a keyword's real defined color, a border
  pattern confirmed against real base-game files, sprite-sheet math the parser requires). Broken here means
  broken for anyone, regardless of who wrote the mod or what style they were going for. **Always checked,
  never gated behind a question.**
- **House convention (bucket name)** — a style choice *this repo* settled on (a wording idiom, a balance
  curve calibrated against this repo's own empirical tables, an authoring-only guide-pixel marker, a file-
  layout preference). Real and worth following in our own mods, but a third-party mod's creator may have
  made a different, equally valid choice on purpose — flagging it as if it were a bug would be noise, not
  a finding. **Checked automatically for our own mods; asked about via questionnaire for anyone else's.**

The five house-convention buckets, asked about only when auditing a foreign mod: **Rule-text wording style**,
**Balance curve**, **Sprite authoring & polish conventions**, **File/folder organization conventions**,
**Design depth (stacking value / upgrade mechanical variety)**.

## Research protocol — same discipline, one extra step

1. **Check this skill's checklist first** for whether the thing you want to verify already has a row.
2. **If it doesn't, the owning domain skill is still the source of truth** for whether something is actually wrong — read that skill's relevant section (via its own Research protocol if needed) before treating a hunch as a finding.
3. **Write the finding back into the owning skill, exactly as any other domain-skill finding would be** (see `cube-chaos-orchestrator`'s Step D). **Then also add a one-line row to this file's checklist**, in the same edit, if the finding is the kind of thing that could silently go wrong in *already-shipped* content, not just something to get right while writing something new. A gotcha that only matters at authoring time (a parse-order quirk, an argument-count trap) doesn't need a checklist row here — it needs one only if it's realistically something a full-mod scan should catch after the fact.

This keeps the checklist growing at the same rate the domain skills do, without turning into a second place that drifts from them.

## Running an audit

1. **Identify the mod and detect authorship.** Confirm which mod folder (or all of them) is in scope. Then decide: is this one of *our* mods, or someone else's?
   - It's **ours** if the mod folder is one of this repo's own tracked mods (the custom entries in `GameData/Loading_Order.txt` once the base-game/example packages are dropped, per `cube-chaos-orchestrator` Step A) or the user is plainly asking to check their own in-progress work. Check `Loading_Order.txt` itself rather than trusting a remembered count or list here — it grows over time and a stale snapshot in this note would silently under-scope future audits.
   - It's **foreign** if the folder wasn't authored in this repo — a Workshop download, a mod folder copied in purely for review, or the user says as much ("check this mod I found", "review someone else's package"). A foreign mod doesn't need to appear in this repo's own `Loading_Order.txt` at all; it only needs to sit somewhere readable (typically still under `GameData/` since that's where the game loads packages from, but the audit itself just reads files — it doesn't require the mod to be wired into this repo's load order).
   - If genuinely ambiguous, ask directly rather than guessing ("is this a mod you're building here, or one you'd like reviewed as an outside package?").
2. **Scope it.**
   - **Own mod → check everything, no questionnaire.** Every row below (Universal and every house-convention bucket) is in scope by default, same as before this skill supported foreign mods — unless the user explicitly asked for a narrower slice ("just check the rule text").
   - **Foreign mod → run the scope questionnaire.** The Universal rows are always in scope and aren't asked about (that's "code correctness" and "image pixel correctness" — they're not a matter of taste). For the rest, ask one `AskUserQuestion` batch, one question per house-convention bucket, each framed as yes/no (the tool always allows a free-text "Other" too — take it as a scope refinement, e.g. "only the base-game keyword coloring, not our own idiom"):
     - *Rule-text wording style* — "Check this mod's Text:/Description: prose against our own wording idioms (\A keyword references, 'not X' phrasing, no-cosmetic-mentions, formatting nitpicks)? A foreign mod likely wasn't written in our voice on purpose."
     - *Balance curve* — "Check this mod's mana/hp/IDENT stats and perk Value:/BalanceCap: pricing against our own empirical ranges? A foreign mod may target a different power curve on purpose."
     - *Sprite authoring & polish conventions* — "Check this mod's sprites against our own authoring-guide markers and shading/color-count polish preference? (Real base-game border patterns and sheet math are checked regardless — this is just our extra house polish bar.)"
     - *File/folder organization conventions* — "Check this mod's file layout against our own per-category-file convention (dedicated UpgradePerks file, one file per perk category, Workshop Tag: hygiene)?"
     - *Design depth* — "Flag perks/abilities whose stacking behavior looks degenerate or no-op where a cheap fix would add value, and upgrade perks that are a plain stat bump where a mechanical twist looks available? This is a design-taste call, not a correctness bug — a foreign mod's creator may have made either choice on purpose."
   - Say up front, briefly, what ended up in scope either way (which buckets, plus the always-on Universal rows) before scanning.
3. **Detect.** For each in-scope checklist row, run its detection method (`references/detection-recipes.md` has the concrete grep/script for every row — load only the recipes for the categories actually in scope). Grep-based checks are cheap to run for everything; the judgment-based ones (rule-text-vs-ability accuracy, border-pixel-diff, balance-outlier lookup) need an actual read or a small script per hit.
4. **Filter false positives before reporting anything.** A raw grep hit is a candidate, not a finding — read the surrounding chain/context and cross-check it against the owning skill's exact rule (e.g. an `East`/`West` grep hit inside a cube's own *name* isn't a direction; a `TargetCube CubeOfPosition` hit that's a genuine name-guarded swap handler isn't a bug — see `cube-chaos-scripting/references/creation-and-copying.md`). Don't report noise.
5. **Compile one report, don't fix anything yet.** Group findings in two tiers:
   - **Likely bugs / silent-failure shapes** — missing guards, hardcoded East/West, mismatched sprite slot order, misaligned border pixels, a `Description:` placed before its `Ability:`. These are the ones worth fixing with high confidence.
   - **Convention/style deviations** — wording idioms, pricing outliers, color composition, keyword-reference styling. Real, but far more likely to be a deliberate choice the mod's creator already made on purpose — say so, don't frame these as errors.
   Each finding: `file:line`, what's there, what the owning skill says it should look like, and (for tier 1) the concrete fix. For a foreign mod, also note each finding's Scope (Universal vs. which house-convention bucket) so the user can tell at a glance which findings are "this is genuinely broken" vs. "this differs from how we'd write it." If a whole category came back clean, say that plainly too — it was checked, not skipped.
6. **Wait for the user before changing anything.** This is the same weight as `cube-chaos-orchestrator`'s Step C preview-and-approve gate, run in the opposite direction (over existing content instead of a new design) — some of what looks "off" may be exactly what the mod's own creator intended. Accept per-item feedback, not just an all-or-nothing verdict ("fix 1, 3 and 5, leave 2 and 4 — those are on purpose"). For a foreign mod, default to *not* fixing house-convention findings at all unless the user explicitly asks — those were reported as "here's how it differs from our style," not as a to-do list for someone else's mod.
7. **Implement only what's approved, through the owning domain skill.** A rule-text fix goes through `cube-chaos-rule-text`'s own conventions, a guard fix through `cube-chaos-scripting`, a border fix through `cube-chaos-sprite-art` — this skill orchestrates the pass, it doesn't reimplement anyone else's rules.
8. **Same gates as any other edit apply afterward**: a fix that touches an `Ability:`/`WorldAbility:` chain or a balance number still needs a test-launch and `Log.txt` check; a pure sprite-pixel or pure wording fix doesn't (see `cube-chaos-orchestrator`'s launch-loop exception). If this mod has a `README.md`, regenerate its preview cards once fixes land.
9. **If a fix reveals a genuinely new, not-yet-catalogued convention, write it back** — to the owning skill first, then a new row here (see Research protocol above).

## The checklist

Each table below adds a **Scope** column: `Universal` rows are always checked; anything else names the
house-convention bucket it belongs to (only checked for a foreign mod once that bucket is answered "yes" —
see "Running an audit" step 2).

### DSL & mechanical safety — `cube-chaos-scripting`

| Check | Owning section | Tier | Scope |
|---|---|---|---|
| Every `GainRandomAbilityOfCube`/`RemoveRandomAbility` call site is guarded against a zero-ability source cube | `references/creation-and-copying.md` — "Runtime gotcha: GainRandomAbilityOfCube on a zero-ability cube" | Bug | Universal |
| A cube re-acquired by position after creation (`TargetCube CubeOfPosition`/`CubeInDirectionFromCube`) is either a name-guarded swap handler or should be `CopyWithAction` instead | `references/creation-and-copying.md` — "Modifying a cube you just created" | Bug | Universal |
| No hardcoded `East`/`West` where `Forwards`/`Backwards` was meant (faction-relative direction) | `references/targeting-movement-board.md` — "Hardcoding East/West..." | Bug | Universal |
| A single-`Ability:` `PERK:`'s `Description:` sits immediately *after* its `Ability:` line, not before | `SKILL.md` — "The Text:/Description: requirement" | Bug | Universal |
| New `CUBE:`/`PERK:` blocks were appended at file end, not inserted mid-file (sprite slot order intact) | `SKILL.md` — "Block formats"; also `cube-chaos-sprite-art` slot-shifting section | Bug | Universal |
| A mod-defined `COMPOUND: ABILITY` reference resolves — not `LOCAL`-scoped from another package, and its package loads after the definer per `Loading_Order.txt` | `references/gotchas-grepped.md` (LOCAL scoping / load-order entries) | Bug | Universal |
| A renamed `PERK:`/`CUBE:` didn't leave a stale literal-string self-reference (`StringConstant <OldName>`, `CubeHasName ... <OldName>`) | `references/perk-economy.md` — perk self-reference section | Bug | Universal |
| `IsUpgradeFrom:` perks live in their own `<ModPrefix>_UpgradePerks.c.txt`, not mixed into the regular perks file (that file's sprite sheet, if any, is a real supported option, not required) | `cube-chaos-sprite-art` — upgrade-perk section | Bug | File/folder organization |
| Each perk category (Curse/Blight/Boon/Consumable/Golden/Neutral/CubeUpgrade/Terrain) has its own dedicated `.c.txt` + sprite sheet, never mixed into a generic `Perks.c.txt` | `cube-chaos-mod-setup` | Convention | File/folder organization |
| An `IsUpgradeFrom:` perk is a plain stat bump on its base perk (same effect shape, only a bigger number) where a mechanical twist looks reasonably available and wasn't considered | `references/perk-economy.md` — "Design quality: an upgrade should carry a mechanical twist" | Design | Design depth |
| A perk's stacking behavior (2+ owned copies) or an ability's re-grant behavior (same ability granted twice to one cube) is degenerate/no-op where a cheap fix (XTimes-by-count, STACKING constructor) would add real value | `references/perk-economy.md` — "Design quality: does stacking actually add value" | Design | Design depth |

### Rule text & wording — `cube-chaos-rule-text`

| Check | Owning section | Tier | Scope |
|---|---|---|---|
| Every `Text:`/`Description:` matches its `Ability:` chain token-for-token — nothing mechanical omitted, nothing cosmetic mentioned, right numbers, right referent for "it" | "Workflow for auditing existing text" | Bug | Universal |
| A base-game keyword (e.g. `Flying`, `Strength`) is referenced with its own real colour and name from `ModdingInfo.txt` (whether via `\A` or, when removed/tested, a bare coloured name), not a made-up or class-tinted colour | "Referencing a keyword: `\A` for any keyword being granted, ours or base-game's" | Bug | Universal |
| A granted keyword (this mod's own compound OR a base-game one) uses `\A <Name> <params>` rather than a hand-written parenthetical/plain-color mention duplicating the explanation at every reference site | "Referencing a keyword: `\A` for any keyword being granted, ours or base-game's" | Convention | Rule-text wording style |
| An exclusion condition reads as "a non-X ally/cube", never a bolted-on parenthetical ("(not your leader)", "(other than X)") | "Phrasing a 'not X' filter" | Convention | Rule-text wording style |
| Purely cosmetic effects (`PlaySound`, `Animation:`, `CubeColourShift:`, particles) are never described in prose | "Never mention purely cosmetic effects" | Convention | Rule-text wording style |
| No period before the closing `End`; first letter capitalized | "Hard formatting rules" | Convention | Rule-text wording style |
| A spawner's text names the created cube's allegiance but doesn't restate its stats/abilities (baked-in or dynamically granted) | "State a created cube's allegiance..." | Convention | Rule-text wording style |
| A stacking perk's "additional copies..." clarifying sentence is present only when the re-trigger is genuinely non-obvious, and absent when stacking is just the natural result of a "first cube matching X" search | "Describing perks whose stacked copies independently re-trigger" | Convention | Rule-text wording style |

### Numeric balance — `cube-chaos-balancing` / `cube-chaos-scripting`

| Check | Owning section | Tier | Scope |
|---|---|---|---|
| Every obtainable `CUBE:`'s `IDENT rarity aggressive defensive scaling weirdness` and mana/hp sit near the empirical range for that rarity, and were matched against a real analog of similar shape, not derived in isolation | `cube-chaos-balancing` — "Empirical ranges by rarity" | Balance | Balance curve |
| Every priced `PERK:`'s `Value:`/`BalanceCap:` was checked against the right reference class (same real `BelongsTo:` kind), not the mod's own earlier precedent | `references/perk-economy.md` — "Perk economy fields" | Balance | Balance curve |
| No `Value:` on a plain `BelongsTo: <class/species>` reward perk; every Curse/Blight/Boon/Consumable/Golden/Neutral/CubeUpgrade has one (Nightmares are the one category that never does) | `references/perk-economy.md` | Balance | Balance curve |
| Curse `Value:` clusters at round multiples of 50; Blight/Boon signs match category (Blight always negative, Boon always positive) | `references/perk-economy.md` — category sections | Balance | Balance curve |
| Every `CubeUpgrade` perk carries `GainRegeneratingUsesX <N>` as its mandatory downside | `references/perk-economy.md` — "CubeUpgrade-specific conventions" | Balance | Balance curve |

### Sprite & image conventions — `cube-chaos-sprite-art`

| Check | Owning section | Tier | Scope |
|---|---|---|---|
| No CUBE/PERK tile has real (non-background) content bleeding into the outer 1px ring the engine actually trims — content there is silently invisible in-game for any mod | "CUBE icon guide grid" / "Border pattern library" | Bug | Universal |
| Every CUBE tile's 1px `RGB(255,0,110)` guide ring sits exactly at the tile's outer edge (offset 0) on all 4 sides — our own authoring visualization of the trim above, not itself required for correctness | "CUBE icon guide grid" | Art | Sprite authoring & polish |
| Every PERK tile's 1px `RGB(255,0,220)` magenta guide ring sits exactly at offset 0 | "Border pattern library" | Art | Sprite authoring & polish |
| A tile's border matches the real pattern for its actual category (plain class/species / clean-3-ring / corner-bracket / CLASSSPECIES fancy frame / CubeUpgrade 5px ring) — confirmed against real base-game files, so this is a genuine rendering fact for any mod using a recognized category, not just our own taste | "Border pattern library" | Art | Universal |
| No border/ring pixel shows icon-content bleed (a sign it was color-matched from a reference tile instead of generated from fixed geometry) | "Never extract a reusable border by color-matching..." | Art | Universal |
| Ground-unit (non-Flying/non-Hovering) CUBE icons are flush to the tile's bottom row, no floating gap — matches how real base-game ground units are drawn | "Ground unit CUBE icons: draw the silhouette flush..." | Art | Universal |
| Every finished icon uses ~3–5 colors (base + outline + highlight + accent), never a flat single fill | "Color composition" | Art | Sprite authoring & polish |
| Sheet width/height are each an exact multiple of `tile_size` (any rectangle is valid, not just a square `ceil(sqrt(block count))` grid) and slot count covers every block in file order; sprite filename matches its `.txt` file's basename with no cross-mod collision | `SKILL.md` — tile-size / naming sections | Art | Universal |
| Workshop `Tag:` set matches the mod's actual content categories, re-audited whenever a new category was added since the tags were last set | `cube-chaos-mod-setup/references/workshop-publishing.md` | Art | File/folder organization |

## Reference index

| File | Load when you're... |
|---|---|
| `references/detection-recipes.md` | Actually running an audit — has the concrete grep command or script sketch for every row above, in the same order |
| `references/cross-skill-index.md` | Writing back a finding that might matter outside its own skill's domain (see `CLAUDE.md`'s research protocol), or working in a domain that might silently depend on a fact documented elsewhere. Also the target for `cube-chaos-doc-audit`'s `GAP` findings. |

## Notes for extending this checklist

- A new row always names the owning skill/section, never restates the rule. If a check doesn't cleanly belong to one existing domain skill, that's a signal the underlying convention itself hasn't been written down anywhere yet — go write it into the right domain skill first, then add the row here.
- A new row also always gets a **Scope**. Default test: would this be wrong/broken for *any* Cube Chaos mod, regardless of who wrote it or what style they were going for (engine behavior, a base-game-confirmed rendering fact, a genuine silent-failure shape)? If yes, `Universal`. If the "correct" answer only holds because it's how *this repo* chose to write things — and a different, equally functional mod could reasonably disagree — it's a house-convention bucket (`Rule-text wording style` / `Balance curve` / `Sprite authoring & polish` / `File/folder organization` / `Design depth`), reusing an existing bucket name rather than inventing a new one without updating the questionnaire in "Running an audit" step 2 to match.
- If a category above starts accumulating enough rows to feel unwieldy on its own, split its detection recipes further inside `references/detection-recipes.md` (per-category files) rather than growing this table's Tier/Check columns — the same "content shape, not line count" split rule every other skill here follows.
