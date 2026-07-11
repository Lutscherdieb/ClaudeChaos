---
name: cube-chaos-rule-text
description: Use whenever writing or reviewing the Text:/Description: prose that accompanies a CUBE:/PERK: Ability: in a Cube Chaos mod - covers phrasing/wording conventions distinct from DSL syntax (see cube-chaos-scripting for that). Trigger on "Text:", "Description:", "rule text", "ability text", "how should I word this", or when double-checking that written prose accurately and idiomatically matches what an Ability: chain actually does.
---

# Cube Chaos ability text (Text:/Description:) wording conventions

These are prose/wording conventions, reverse-engineered by grepping thousands of real `Text:`/`Description:` lines across the base game and comparing them against their paired `Ability:` code. For DSL syntax rules (argument counts, sequencing, implicit targets) see `cube-chaos-scripting`. For sprite/icon conventions see `cube-chaos-sprite-art`.

The core discipline: **always compare the prose against what the Ability: chain literally does**, token by token, not just against general style. Style-only checks miss real bugs (e.g. a description that names an ability but omits a real numeric effect it grants).

**Rule text is never edited independently — it always derives from the effect.** Whenever you change an existing `Ability:`/`WorldAbility:` chain (a direction, a number, a condition, anything mechanical), updating its paired `Text:`/`Description:` to match is part of the same edit, not a separate optional follow-up — never leave a changed effect with stale prose describing the old behavior, even for a one-word change (e.g. changing a spawn direction from `North` to `East` means the word "above" in the text must become "to the east", not just the DSL token). Treat "the effect changed" as the trigger for a text update, the same way "wrote a new custom Ability:" is the trigger for adding a `Text:`/`Description:` at all (see `cube-chaos-scripting`'s Text:/Description: requirement).

## Hard formatting rules

- **Never put a period before the closing `End`.** Checked ~3070 real `Text:`/`Description:` lines: only 1 has a period before `End`. End the sentence and put `End` directly after — e.g. `Text: Heals the cube in front for 2 hp End`.
- **Always capitalize the first letter.** 2965/2968 real lines do (the handful of exceptions are noise, not a real pattern).

## Never mention purely cosmetic effects

`PlaySound`, `CreateAoEParticlesColourRadiusPosition`, `Animation:`, `CubeColourShift:` (a granted ability's cube-tint field — see `cube-chaos-scripting`), and similar audio/visual-only effects are never described in `Text:`/`Description:` — confirmed against every `PlaySound`-using cube checked, including ones where the sound is bundled into a larger multi-step ability that DOES get text for its mechanical parts. Real case: `DJ-Moil`'s perk grants a purely-cosmetic black-tint tag ability (`Moil_Blessed`) alongside a real mechanical effect, and only the mechanical effect is mentioned in the `Description:` — the tint isn't. Only describe things that affect gameplay (damage, healing, stat/ability changes, creating cubes, etc). If an action doesn't change game state a player needs to track, leave it out of the prose.

## Spell out the numbers when granting a built-in parameterized ability

When your custom `Ability:` chain does `GainAbility SomeBuiltIn <TIME/STACKING/CONSTANT literal>` as part of a bigger effect, don't just name-drop the ability — state its concrete resulting effect. The base game's own `Forged_Coalition_Swords` grants `GainAbility EveryXMeleeY 60 1` and describes it as "a melee attack for 1 damage per second" (60 ticks = 1 second — see `cube-chaos-scripting` for the confirmed 60-ticks-per-second rate), not just "...and Melee". Convert the raw TIME value to "every N seconds" phrasing rather than leaving the reader to infer it from the ability's own separate tooltip.

## Referring back to a cube mentioned earlier in the same sentence

- Default to the pronoun **"it"** — overwhelmingly the norm. Real `AfterThisCreates` examples: "give it: Every 5 seconds move upwards", "give it a copy of every other ability of this".
- When the sentence involves **two different cubes** and "it" would be ambiguous, use a noun instead — most commonly **"the creation"** for a just-created cube (e.g. "apply ExtraLife to the creation"). Don't invent an awkward literal phrase like "the cube this just created" — no real base-game text does that, and a human player will find it reads oddly too (this was caught by ear, not by grep — if a phrase feels unfamiliar, it's worth checking against real examples).
- Prefer the verb **"give"** over "grant" — `"give it"` outnumbers `"grant it"` roughly 7:1 (113 vs 16 occurrences) in real text. "Grant" isn't wrong, just less idiomatic; default to "give".

## Common trigger → opening-phrase mappings (from real examples)

- `AfterThisIsCreated` → "After this is created..."
- `AfterACubeIsCreated` (+ `IsAllyToCaster` + `IsPlaced` checks) → "After you place an ally..." / "After an ally is placed/created..."
- `AfterThisCreates` → "After this creates a cube..." (then refer to the created cube as "it", or "the creation" if another cube is also in play)
- `BeforeACubeDies` → "Before a cube/an ally dies..."
- `AfterACubeDies` → "After an ally dies..." / "After any ally dies..."
- `EverySecond` / `EveryXSeconds N` / `Every10Seconds` → "Every second..." / "Every N seconds..."
- `AtTheStartOfTheBattle` → "At the start of the battle..." / "At the start of each battle..."
- `X%Chance N` → "N% chance..." — **default to placing it right after the trigger clause, not at the very start of the sentence.** Grepping `dies, \d+% chance` alone turns up 14 real examples, all "After X dies, N% chance to `<effect>`..." (e.g. "After a poisoned enemy dies, 50% chance you create an allied copy in its place") — none put the percentage before the trigger clause. Leading with "N% chance, `<trigger clause>`, `<effect>`" is grammatically valid but the rarer, less idiomatic form; only reach for it if the trigger clause itself is short enough that leading with it reads awkwardly (uncommon).
- **After the percentage, state the effect directly — don't insert a flavorful noun-phrase teaser before restating it.** A first pass on `Echo` wrote "10% chance for one more echo - a Note is created in its place," pairing a poetic aside with a dash-separated literal restatement. No real base-game text does this for an `X%Chance` clause; the established idiom goes straight from the percentage to the concrete mechanical effect: "chance you create X in its place" (`Characters/Synergies.c.txt`'s "50% chance you create an allied copy in its place", `Characters/Species/Undead.c.txt`'s "2% chance you create a zombie in its place"). Caught by the user, not by grep — a good reminder that an oddly-phrased line can pass every hard-formatting-rule check and still not match idiom; grep the closest real analog before trusting invented phrasing, even for a clause that looks small.

## Don't color a tag ability's own name to match a dark `CubeColourShift` tint

Real `Text:`/`Description:` lines wrap a name in `\C R G B ... \CN` to color it, and for a pure cosmetic tag ability (see `cube-chaos-scripting`'s tag-ability pattern) it's tempting to match that color to the ability's own `CubeColourShift:` sprite-tint value for visual consistency. Don't, if the tint is dark: this was tried with black (`\C0 0 0 Moil_Blessed \CN`) and the name became invisible against the tooltip's own dark background — it read as an empty bullet with no text rather than a named tag. Pick a color for the `\C.../\CN` name that's legible on a dark UI panel regardless of what the sprite tint itself is (e.g. `DJ-Moil`'s `Moil_Blessed` uses gold `\C255 238 0`, matching the base game's own `Golden` ability's text color, even though the sprite tint it applies is black).

## Parenthetical clarifications are a normal, expected pattern

Real examples: "(Bullets are 2 damage projectiles)", "(increasing its damage by 2)". Use a trailing parenthetical to spell out a non-obvious mechanical consequence — e.g. what a named stacking ability like Growth actually does numerically — rather than assuming the player already knows.

## Fixed term: a cube without `HasLimitedUses` is "a cube with infinite uses," not "unlimited use"

When prose needs to refer to `Not HasLimitedUses Test`/`RegeneratingUsesX`'s absence (see `cube-chaos-scripting`), the established phrase is **"cube with infinite uses"** — confirmed via 10+ real occurrences across `Characters/Species/Chaos.c.txt`, `Plant.c.txt`, `Extra_Mechanics/Blights.c.txt`, `Base_Core/GameRulePerks.c.txt`, etc. (e.g. "start each battle with a random cube with infinite uses in hand", "add growth 2 to a random cube with infinite uses in your hand"). Don't invent a synonym like "unlimited use cube" — caught on the DJ mod's `Inspiration` perk, corrected by the user.

## Fixed term: `ARandomLeftPosition`/`ARandomTopPosition`/`ARandomRightPosition` is "a random left/top/right_side_position" verbatim

`Base_Core/ToolTipText.c.txt` registers this as a real tooltip keyword: `TEXTTOOLTIP: LEFT_SIDE_POSITION A position on the left half of the map, not guaranteed to be empty unless otherwise stated`. Real prose always uses the underscored form as one unit, lowercase, straight after "a random": "create a bee in a random left_side_position" (`Main/Consumables.c.txt`), "create a Brown_Ant on a random left_side_position" (`Characters/Classes/PerkFragments.c.txt`), "in a random left_side_position" (`Main/GoldenPerks.c.txt`, `Main/CubeUpgrades.c.txt`). Don't paraphrase it as "a random position on the left side" or similar — same keyword-linking reasoning as `Silent`/"silently" below: the registered term drives the in-game tooltip.

## Fixed term: the `Silent` action wrapper is "silently" in prose, never a spelled-out paraphrase

When an `Ability:` wraps an effect in `Silent` (do it without triggering any ability — see `cube-chaos-scripting`), the prose term is the adverb **"silently"** placed before the verb: "20% chance it silently gains another copy", "it silently gains a random debuff" (`Main/UpgradePerks.c.txt:2431`), "silently gains 1 regeneration" (`ZUpgradeClassPerks.c.txt:543`), "this silently dies" (lasers/projectiles throughout `Main/3GeneralCubes.c.txt`). `SILENTLY` is a registered tooltip keyword (`Base_Core/ToolTipText.c.txt`: "Do something without triggering ANY ability"), so using the word links the explanation automatically — don't paraphrase it as "(without triggering anything)". Caught on the DJ mod's `Feedback` perk, corrected by the user: the parenthetical form was copied from `Rogue-Moil` (`Characters/Synergies.c.txt:678`), which turns out to be the lone non-idiomatic outlier against a dozen+ "silently" usages — a reminder that **matching a single closest-analog line isn't enough when the phrasing is a recurring term; grep the word itself across the codebase and follow the majority idiom**, especially when a tooltip keyword might exist for it.

## State a created cube's allegiance if it isn't the obvious default

A freshly created cube defaults to allied-to-caster unless the `Ability:` explicitly sets otherwise (see `cube-chaos-scripting`'s faction-defaults note) — this is a real mechanical fact, not a cosmetic detail, so state it whenever it isn't simply "allied" by default omission. Match the base game's own short phrasing rather than a wordy clause: **"an allied X"** for ally-to-caster, **"a neutral X"** for `SetFaction DoubleConstant 0`/`NeutralCopy`, or **"an X of the same faction"** when it inherits another cube's faction dynamically. Real examples: `Shadow.c.txt`'s "replace a random Solid_Shadow with an allied Solid_Shadow_Hive", `UpgradeSpeciesPerks.c.txt`'s "...with a neutral Solid_Shadow_Hive", `Main/3GeneralCubes.c.txt`'s "replace it with a Skewered_Corpse of the same faction".

## Describing perks whose stacked copies independently re-trigger

If a `PERK:`'s `Ability:` will independently re-fire once per owned copy (see `cube-chaos-scripting`'s perk-stacking section), the real idiom is a **plain trailing clarifying sentence**, not a "N% chance per copy"/"per copy you own" quantifier folded into the effect clause itself — grepped the whole codebase for that shape and it doesn't exist anywhere; a first pass invented it and had to be corrected back to the real pattern. Real precedent: `Main/Perks.c.txt`'s `Safety_Foam` ends its `Description:` with "...the foam is poisoned, additional copies of this perk can trigger on the foams creation". Match this shape — state the effect normally first, then add "Additional copies of this perk `<repeat/trigger on/etc>` ..." as its own separate sentence, rather than trying to quantify the scaling inline.

**Only add that sentence when the re-trigger is a genuinely separate/non-obvious mechanism** — e.g. `Safety_Foam`'s second copy triggers on a *different* foam-creation event than the reader would assume from the base description, and `Echo`'s stacking scales a hidden internal roll count via `XTimes AmountOfPerksInInventoryWhich...`, neither of which a reader could infer from the effect sentence alone. **Skip it when the stacking is just the mechanical consequence of a "first cube/target matching X" search that a marked/exiled cube then fails** (see `cube-chaos-scripting`'s "each copy affects a different cube" idiom) — the base game's own `Bird_Feather` (`Main/Perks.c.txt`) stacks exactly this way (2nd copy gives Flying to the *next* flightless cube) and its `Description:` has no such sentence at all, because "the first cube without X" already reads as self-evidently repeatable once you know it excludes cubes that already have X. Caught on the DJ mod's own `Inspiration` perk: a first pass added the clarifying sentence by analogy to `Safety_Foam`/`Echo` before checking whether this specific ability's stacking was actually the unremarkable kind — user corrected it back out.

## Workflow for auditing existing text

1. Read the `Ability:` chain token by token and write down, in plain terms, exactly what it does (every trigger, condition, and effect — including implicit-receiver targets, per `cube-chaos-scripting`).
2. Read the paired `Text:`/`Description:` and check every clause against that list — does it mention everything mechanical, nothing cosmetic, with correct numbers and correct referents (which cube is "it")?
3. Grep the base game for the closest real analog (same trigger, similar granted ability, similar loop-and-chance shape) and compare phrasing, not just correctness — an accurate-but-oddly-worded description is still worth fixing to match established idiom.
