---
name: cube-chaos-rule-text
description: Use whenever writing or reviewing the Text:/Description: prose that accompanies a CUBE:/PERK: Ability: in a Cube Chaos mod - covers phrasing/wording conventions distinct from DSL syntax (see cube-chaos-scripting for that). Also covers the tooltip escape codes (\C \CN \CMANA \B \N \A \D), the \A inline-ability idiom that keeps a keyword's explanation attached everywhere it is referenced, and the standard keyword header + dim parenthesised explanation shape. Trigger on "Text:", "Description:", "rule text", "ability text", "keyword", "tooltip formatting", "how should I word this", or when double-checking that written prose accurately and idiomatically matches what an Ability: chain actually does.
---

# Cube Chaos ability text (Text:/Description:) wording conventions

These are prose/wording conventions, reverse-engineered by grepping thousands of real `Text:`/`Description:` lines across the base game and comparing them against their paired `Ability:` code. For DSL syntax rules (argument counts, sequencing, implicit targets) see `cube-chaos-scripting`. For sprite/icon conventions see `cube-chaos-sprite-art`.

The core discipline: **always compare the prose against what the Ability: chain literally does**, token by token, not just against general style. Style-only checks miss real bugs (e.g. a description that names an ability but omits a real numeric effect it grants).

**Rule text is never edited independently — it always derives from the effect.** Whenever you change an existing `Ability:`/`WorldAbility:` chain (a direction, a number, a condition, anything mechanical), updating its paired `Text:`/`Description:` to match is part of the same edit, not a separate optional follow-up — never leave a changed effect with stale prose describing the old behavior, even for a one-word change (e.g. changing a spawn direction from `North` to `East` means the word "above" in the text must become "to the east", not just the DSL token). Treat "the effect changed" as the trigger for a text update, the same way "wrote a new custom Ability:" is the trigger for adding a `Text:`/`Description:` at all (see `cube-chaos-scripting`'s Text:/Description: requirement).

## Research protocol — this skill first, base game second, write back always

Follow this order every time you need to word something and aren't certain of the convention. The point is to stop re-deriving the same answers: each trip to the base game must leave this skill richer than it found it.

1. **Check this skill first.** The Fixed-term sections, the hard formatting rules, and the trigger→opening-phrase table below already settle most questions. If it's covered here, use it and stop — don't re-research something already decided.
2. **If this skill doesn't cover it, go to the base game.** Two sources, in this order:
   - **`ModdingInfo.txt` (repo root, ~760 lines).** Every registered built-in is listed as `Name [ARGTYPES]` followed by **its exact tooltip string in quotes** — e.g. `StrengthX STACKING     "\C255 38 0 Strength STACKING 1 \B : \CN This deals \C255 38 0 STACKING 1 \CN more damage "`. This is the canonical phrasing *and* canonical colour for every concept the game already has a word for, and it's the fastest possible lookup. Use it before grepping anything. `ModdingExplanation.txt` (~75 lines) is a prose walkthrough of how a definition is parsed — useful for structure, not phrasing.
   - **Real `Text:`/`Description:` lines under `GameData/Base_Core|Main|Characters|Extra_Mechanics`.** Grep for the closest analog by *trigger and effect shape*, not by topic, and prefer a pattern with many occurrences over a single example. Counts matter: "113 vs 16" is what makes "give it" the idiom rather than a coin flip.
3. **Write the finding back into this skill, in the same edit that uses it.** Add a `## Fixed term:` section for a settled word choice, or a new convention section for a pattern, and **record the evidence** — file:line for a decisive example, and the occurrence counts if the conclusion rests on frequency. A finding recorded without its evidence can't be re-checked later and will get re-litigated.

Step 3 is not optional bookkeeping — it's the mechanism that keeps step 1 useful. Skipping it means the next session repeats step 2 from scratch.

**Never edit `ModdingInfo.txt`/`ModdingExplanation.txt` or anything under the base-game `GameData/` folders** — they're read-only ground truth (see `CLAUDE.md`).

## Forcing a real line break for a multi-point list: `\N`

`\N` (literal backslash + capital N, as two plain characters embedded in the field's text) is a real, confirmed forced-line-break marker the tooltip renderer honors — not a paraphrase, an actual mechanism. Confirmed via dozens of real base-game examples (`Main/3GeneralCubes.c.txt`, `Main/UpgradePerks.c.txt`, `Characters/Classes/PerkFragments.c.txt`, `Extra_Mechanics/Blights.c.txt`, etc.), e.g.:
```
Text: After this deals damage, if empty above, create a Flesh_Ball above, otherwise if there is a Flesh_Ball:
\N -give it 1 extra hp 
\N -every 5 times give it Regeneration 2 
\N -every 25 times give it a Melee attack End
```
Use it whenever a `Text:`/`Description:` needs to read as a genuine list of separate points rather than one run-on sentence — e.g. an upgrade perk (`IsUpgradeFrom:`) whose `Description:` restates 2-3 independent effect clauses, since `Description:` is a single whole-perk field that doesn't stack per-`Ability:` the way `Text:` does (see `cube-chaos-scripting`'s Text:/Description: requirement) and so has no other way to visually separate multiple points. Real pattern for a list of short independent clauses (as opposed to a set of sub-items continuing one sentence, which real examples instead write without a dash, e.g. `Characters/2TokenCubes.c.txt:659`'s "the cube below: \N Gains FrozenX 10 \N Gains 1 extra hp \N Loses Temporary"): put each full clause on its own line, joined by ` \N `, no period before `\N` (same "no period before a terminator" discipline as `End` — see the hard formatting rules below).

**You do not need the source `.txt` file's own physical line breaks to match the rendered ones.** `\N` is just a two-character marker inside the field's string content — write the whole field on one physical source line with `\N` embedded inline wherever you want a break (e.g. `Description: Point one \N Point two End`). This also matters for this repo's own tooling: `render_preview_cards.py` (`cube-chaos-sprite-art`) only extracts a `Description:`/`Text:` field from a single physical source line (see that script's `field()` function) — a field genuinely split across physical source lines (as some real base-game examples are) would silently lose its continuation when parsed by our own script, even though the real game engine's own parser tolerates it. Keeping the whole field on one physical line with inline `\N` sidesteps that gap entirely and is simpler to write besides. The script itself now splits on `\N` before word-wrapping (so generated preview cards show the same line breaks the real tooltip would) — if you ever see literal `\N` characters in a generated preview card image, that split logic has regressed.

## The complete escape-code vocabulary — there is no italic and no font size

Grepping every escape sequence across `Base_Core/`, `Main/` and `Extra_Mechanics/` turns up exactly seven, and nothing else exists:

| Code | Meaning |
|---|---|
| `\C<R> <G> <B>` | start colored text |
| `\CN` | reset to normal color |
| `\CMANA` | the game's own mana-colored word (used as `\CMANA mana \CN`) |
| `\B` | suppress the space before the next character — `CODE 1 \B %` renders `50%`, `Name \B :` renders `Name:` |
| `\N` | forced line break (see above) |
| `\A <Ability> <params>` | render that ability's own registered `Text:` inline |
| `\D <DOUBLE expr>` | render a computed number inline (e.g. `\D AmountOfCubesInInventoryWhich True`) |

**There is no italic, bold, or font-size control.** If a request asks for "smaller" or "cursive" text to visually de-emphasize a block, the only levers are color (a dimmer gray) and a `\N` break to make it a separate block — say so rather than approximating, because there is no code to find.

## Referencing a keyword: `\A` for any keyword being granted, ours or base-game's

**Revised 2026-07-29** (superseding the earlier "our own only" rule below, per a `cube-chaos-audit` pass over the Steam Workshop "Dinosaurs!" mod plus a re-read of the base game's own usage): **`\A <Name> <params>` is now the default for referencing *any* keyword being granted, regardless of who defined it** — this mod's own `COMPOUND: ABILITY` or a base-game built-in (`StrengthX`, `GrowthX`, `Swarm`, `ChargeEveryX`, …) alike.

| Keyword defined by | How to reference it in prose (granting it) |
|---|---|
| **This mod** (`COMPOUND: ABILITY` in `GameData/<Mod>/`) | `\A <Name> <params>` — pulls in the full dim explanation |
| **The base game** (`StrengthX`, `GrowthX`, `Swarm`, `ChargeEveryX`, …) | Also `\A <Name> <params>` — pulls in the base game's own real tooltip text |

This reverses the previous "colour-only for base-game keywords" rule. Two things changed the call:
- **`\A` on a base-game ability is confirmed as the base game's *own* real idiom, not a mod-only trick** — `Characters/GeneralCubes.c.txt:399` uses `\A PoisonX 1` to reference `PoisonX`, a base-game built-in, inside a base-game file. If the base game itself is comfortable pointing `\A` at its own built-ins, there's no real reason for a mod to avoid doing the same.
- **The Dinosaurs! Workshop mod does exactly this throughout** (`\A RetaliateX 1`, `\A EveryXMeleeY 240 4`, `\A ChargeEveryX 90`, all in `GeneralCubes.c.txt`) — one rule instead of two, and it reads correctly in a genuinely well-regarded third-party mod.

**The original concern this rule now accepts as a tradeoff, not a blocker:** `\A` renders the *defining* file's own text, so a base-game keyword still arrives in base-game (undimmed) styling next to our own compounds' dimmed-parenthetical styling (see "Keyword abilities: header line, then a dim parenthesised explanation" below — that pattern is unchanged, still our house style for **our own** compound headers). A tooltip that grants both kinds of keyword can now show one dimmed explanation and one plain one. This was the exact reason the rule was tightened on 2026-07-25 (caught on a General class perk) — reconsidered now because the "plain" style is just what every vanilla tooltip already looks like everywhere else in the game; a base-game reference reading like a base-game tooltip isn't a foreign inconsistency, it only ever looked inconsistent against our own mod's private dimming convention, which the player has no baseline for anyway.

Grab the exact colour and display name from the ability's own entry in `ModdingInfo.txt` when double-checking a rendered `\A` result (not for hand-writing it — `\A` renders the whole thing) — real values include `StrengthX` `255 38 0` "Strength N", `GrowthX` `0 127 14` "Growth N", `ChargeEveryX` `155 238 255` "Charging", `Swarm` `255 0 220` "Swarm", `Flying` `109 209 228` "Flying", `Burning` `255 106 0` "Burning" (`ModdingInfo.txt:89`, a 0-arg keyword), `RetaliateX` `198 27 33` "Retaliate CODE 1" (`ModdingInfo.txt:209`), `ExplodesX` `182 0 0` "Explodes CODE 1" (`ModdingInfo.txt:143`), `FervorX` `255 38 0` "Fervor STACKING 1" (`ModdingInfo.txt:146`), `SplinterX` `197 204 112` "Splinter STACKING 1" (`ModdingInfo.txt:224`), `DoubleTimeX` `197 204 112` "Double Time" (`ModdingInfo.txt:110`), `Undead` `0 50 0` "Undead" (`ModdingInfo.txt:239`, a 0-arg keyword), `ProjectileX` `250 150 150` "Projectile CODE 1" (`ModdingInfo.txt:201`). **Don't append a hand-written parenthetical explaining a keyword** — `\A` (granting) or the bare coloured name (removing/testing, see below) replace that duplication entirely; never hand-copy the explanation either way.

**Historical incident, from when this repo used colour-only for base-game keywords (2026-07-25 audit):** five General-mod perks had hand-written parentheticals or plain uncoloured mentions instead of the then-current colour-only convention (`General-Dwarf`/`General-Crystal`/`Believer`/`Blinding_Faith`/`General-Undead`/`DJ-Undead`). Kept here as a reminder of the general failure shape (duplicated or missing explanation text) even though the specific fix now applied to base-game references has changed from "colour-only" to `\A` — see "apply to existing mods" note below for the current pass.

### Why `\A` at all

`\A <AbilityName> <params>` substitutes that ability's own registered `Text:`, parameters resolved per call site. Two things go wrong without it:

- **The explanation silently goes missing at the reference site.** A description that hand-colors a keyword name (`gains \C255 255 0 Rhythmic 50 \CN`) shows the player a bare word with no indication of what it does. Caught by the user reading the DJ class perk tooltip in-game — the keyword's own definition had a full explanation, but nothing carried it across to the perk that grants it.
- **The explanation drifts.** Hand-written parentheticals duplicate text that already exists on the ability, so tuning the ability leaves every reference stale. `\A Rhythmic 50` can't drift; editing the compound's own `Text:` updates every site that grants it.

`\A` also resolves parameters per call site, so one definition serves every caller: `\A Rhythmic 50` and `\A Rhythmic 20` render the same sentence with different numbers.

Three mechanical cautions:
- **Don't use `\A` when the granted value is COMPUTED rather than a literal.** `\A` substitutes the
  parameters exactly as written at the call site, so `\A StrengthX 1` renders the hard number "Strength 1"
  even when the chain actually grants `maxHp`-many stacks — quietly telling the player the wrong number.
  Use the **bare coloured name with no number, followed by `\B ,` and the value in prose**:
  `give it \C255 38 0 Strength \CN \B , equal to this cube's max hp`. This is the base game's own idiom
  for the same situation — `Main/3GeneralCubes.c.txt:2817`: *"After a differently named ally is placed
  give it `\C255 38 0 Strength \CN \B ,` equal to the energy on this, then this dies"*. Note this is a
  **third** case alongside the granted-with-a-literal (`\A`) and removed/tested (bare name) cases below,
  and unlike the removed/tested case it takes **no number at all** — there's no count to put before the
  name, which is the whole reason prose has to carry it.
  *Verify by reading the rendered card* (`render_preview_cards.py` → `GameData/<Mod>/Preview/...`), not
  the source: a wrong-number `\A` renders perfectly happily and `Log.txt` stays clean.
- **Never leave punctuation glued to the ability name.** `\A Take_Off, cooldown 10 seconds` risks the parser reading `Take_Off,` as the name. Separate it and close the gap visually with `\B`: `\A Take_Off \B , cooldown 10 seconds`.
- **Don't use `\A` for an ability being *removed* or *tested* rather than granted** (`lose Swarm`, `an ally without Charging`) — the inline text is phrased as an effect the cube currently has, which reads wrong under "loses" or "without". Use the bare coloured name there instead, regardless of who defined the ability — and if a stack count is included, put the **number before the name**: `\C255 38 0 1 Strength \CN`, not `\C255 38 0 Strength 1 \CN`. **Corrected 2026-07-29** (same Dinosaurs! audit): the mod consistently writes inline mid-sentence references number-first ("grants 1 Holy", "gain 1 Strength" — `\C0 254 33 1 Holy \CN`, `\C255 0 0 1 Fervor \CN`), which is the more natural English word order for a quantity ("gain 1 X", same as "gain 1 mana" or "gain 1 hp"); this repo's own prior example (`\C255 38 0 Strength 1 \CN`, name-then-number) copied the *header* word order (real base-game headers like `StrengthX`'s own `ModdingInfo.txt` string are genuinely name-then-number, e.g. `"Strength STACKING 1 :"`) into an inline-sentence context where it doesn't fit — headers and inline mid-sentence mentions call for different word order, and the header-style example was applied to the wrong context. **This does not affect the compound-header pattern below**, which is still name-then-number by design (matching real base-game headers) — this fix is scoped to the bare-name, non-`\A`, mid-sentence case only.

**Apply to existing mods:** this repo's DJ/General/Unholy mods currently follow the old rules (colour-only for base-game keywords; name-then-number in bare inline references) — both need a pass to bring existing `Text:`/`Description:` fields in line with the corrected conventions above.

## Keyword abilities: header line, then a dim parenthesised explanation

The standard shape for any mod-defined `COMPOUND: ABILITY` meant to read as a named keyword:

```
Text: \C<R> <G> <B> <Keyword Name> [CODE 1] \B : \CN \N \C96 96 96 (<full explanation>) \CN End
```

The colored name plus `\B :` gives the header; `\N` drops the explanation onto its own line; `96 96 96` (the game's own marker gray) dims it so a player who already knows the keyword can skip the whole block, while a player who doesn't can read it. Parenthesised, and the parentheses stay inside the gray.

Pick the header color from the base game's existing vocabulary rather than inventing one — `155 238 255` movement, `255 0 0` / `182 0 0` damage, `0 254 33` healing, `255 255 0` and `255 238 0` yellow for tag/status keywords, `255 0 220` magenta for meta/system abilities (`LEADER`, `TheInheritor`, `ElementalFriend`). For a **parameterized** compound the placeholder in the text matches the body's generic: `CODE 1` for `GenericConstant`/`GenericDouble`/`GenericTime`, `STACKING 1` for `GenericStacking`.

**A keyword that modifies another ability (rather than having its own effect) still uses this exact header shape — but its `COMPOUND: ABILITY` is a never-granted text-only twin of a separate `COMPOUND: ACTION` that holds the mechanic.** `\A <Name>` resolves against the text-only twin, so nothing about the wording changes; see `cube-chaos-scripting/references/authoring-and-inheritance.md`'s "A keyword that MODIFIES another ability" section for why the split is forced and where to wrap the payload. Real example: Crusader's `Spiritual`.

**A purely cosmetic tag ability still gets the treatment**, with the explanation opening "Cosmetic only," so the player knows there's no effect to hunt for — e.g. `(Cosmetic only, marks a Note that gained all abilities of a random perk)`. This is not a contradiction of "never mention purely cosmetic effects" below: that rule is about not cluttering a *mechanical* ability's text with its sound/particle side effects. A tag ability whose entire existence is the marker has nothing else to describe, and its tooltip line renders whether you like it or not (there is no way to hide an ability from the tooltip — see `cube-chaos-scripting`), so the honest move is to say what the marker means.

### A keyword with 2+ mechanically distinct effects: one dim parenthetical per effect, same shade, no per-effect color

When a single `COMPOUND: ABILITY` keyword bundles multiple genuinely separate effects (e.g. two different triggers, like an `AfterThisIsCreated` one-shot plus an `ExtraTrigger: BeforeThisTakesDamage` passive), give each effect its own `(...)` parenthetical on its own line, all in the same `96 96 96` dim gray — not one dimmed and one full-color/standout:
```
Text: \C<R> <G> <B> <Keyword Name> \B : \CN \N \C96 96 96 (<effect 1>) \CN \N \C96 96 96 (<effect 2>) \CN End
```
**Decided against giving any individual effect its own standout color**, even one that seems like the "headline" effect (e.g. a damage-immunity clause) — tried on the Voidling mod's `VoidTouched` keyword (colored `Cannot be damaged by True Void` on its own full-color line, separate from the dimmed creation-effect parenthetical) and the user reverted it back to matching-gray-parentheses for both. The header's own color is what marks the keyword as a keyword; every effect underneath it is equally "the definition" and dims uniformly, the same as a single-effect keyword's one parenthetical would. This applies to any reference site that restates the keyword's effects in prose too (e.g. a perk `Description:` naming a cube/leader as holding that keyword) — match the same one-gray-parenthetical-per-effect shape there, not just in the compound's own `Text:`.

## Hard formatting rules

- **Never put a period before the closing `End`.** Checked ~3070 real `Text:`/`Description:` lines: only 1 has a period before `End`. End the sentence and put `End` directly after — e.g. `Text: Heals the cube in front for 2 hp End`.
- **Always capitalize the first letter.** 2965/2968 real lines do (the handful of exceptions are noise, not a real pattern).

## Phrasing a "not X" filter: "non-X", never a parenthetical

When a condition excludes one specific thing — `Not IsALeader Victim/Culprit/Target`, or `Not CubeHasName Victim <SomeCube>` — phrase it as **"a non-X ally/cube/enemy"**, folding the exclusion into the noun phrase, never as a bolted-on parenthetical like "(not your leader)" or "(other than a Damned Soul)". Confirmed twice independently, same fix both times (2026-07-25, both user-flagged):
- **`Not IsALeader`**: General's `General_Perks.c.txt`/`General_UpgradePerks.c.txt` ("a non leader ally") and DJ's `DJ_Cubes.c.txt`/`DJ_Synergies.c.txt`/`DJ_UpgradePerks.c.txt` ("non-leader cubes", "non-leader allies") already used this noun-phrase form. Unholy's `Blood_Totem` read "Before an ally (not your leader) collides with this..." and was corrected to "Before a non-leader ally collides with this...".
- **`Not CubeHasName Victim Damned_Soul`**: Unholy's `Phylactery` ("Whenever an allied cube (other than a Damned Soul) dies...") and its upgrade `Lichdom` ("Whenever a cube (other than a Damned Soul) dies...") were both corrected to "a non-Damned Soul ally"/"a non-Damned Soul cube" respectively — keep the excluded cube's display name spaced as normal ("Damned Soul", not the DSL's underscored `Damned_Soul`) since the rest of the sentence already refers to it that way ("...add a Damned Soul to your hand").

Hyphenate ("non-leader", "non-Damned Soul") by default — DJ's cube/synergy text hyphenates while its two older upgrade-perk lines don't, so hyphenated is the slightly more common and more standard-English form; either reads fine in-game, but don't introduce a third phrasing (a parenthetical, "excluding the leader", "that isn't a Damned Soul", etc.). This generalizes to any future single-exclusion filter, not just these two cases — check here first before reaching for a parenthetical.

## Never mention purely cosmetic effects

`PlaySound`, `CreateAoEParticlesColourRadiusPosition`, `Animation:`, `CubeColourShift:` (a granted ability's cube-tint field — see `cube-chaos-scripting`), and similar audio/visual-only effects are never described in `Text:`/`Description:` — confirmed against every `PlaySound`-using cube checked, including ones where the sound is bundled into a larger multi-step ability that DOES get text for its mechanical parts. Real case: `DJ-Moil`'s perk grants a purely-cosmetic black-tint tag ability (`Moil_Blessed`) alongside a real mechanical effect, and only the mechanical effect is mentioned in the `Description:` — the tint isn't. Only describe things that affect gameplay (damage, healing, stat/ability changes, creating cubes, etc). If an action doesn't change game state a player needs to track, leave it out of the prose.

## Spell out the numbers when granting a built-in parameterized ability

When your custom `Ability:` chain does `GainAbility SomeBuiltIn <TIME/STACKING/CONSTANT literal>` as part of a bigger effect, don't just name-drop the ability — state its concrete resulting effect. The base game's own `Forged_Coalition_Swords` grants `GainAbility EveryXMeleeY 60 1` and describes it as "a melee attack for 1 damage per second" (60 ticks = 1 second — see `cube-chaos-scripting` for the confirmed 60-ticks-per-second rate), not just "...and Melee". Convert the raw TIME value to "every N seconds" phrasing rather than leaving the reader to infer it from the ability's own separate tooltip.

**This applies only to abilities granted *inside* a larger custom effect that you are describing in your own words** — e.g. a chain that creates a cube and also gives it a melee attack. It does **not** override the keyword-reference rule above: a sentence whose whole point is "it gains \<keyword\>" uses `\A` regardless of who defined the keyword, never a hand-written restatement of what the keyword does.

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

**Every real usage of `ARandomLeftPosition` across the entire game (base game and every mod in this repo, ~6 confirmed sites: `Main/Consumables.c.txt`'s `Bottled_Bees`, `Characters/Classes/PerkFragments.c.txt`'s `Effect:_Left_Side_Copy`, and this mod's own `Revenge`/`Blood_for_Blood`/`Sampling`/`Super_Sampling`) is bare and unfiltered — none of them check `IsPositionEmpty` first.** There is no real precedent anywhere for combining "left side" with "empty" in one position search, even though the individual pieces to build one exist (`IsPositionEmpty`, `ARandomPositionWhich BOOLEAN`, `PositionExists` as a guard). If a future ask wants a guaranteed-empty spawn position, default to matching this established (if seemingly loose) idiom rather than assuming a custom filtered search is expected — confirm with the user first if the ask explicitly says "empty," since building the custom version is real, uncharted DSL territory (see `cube-chaos-scripting`'s general discipline about matching proven patterns over deriving from the grammar alone).

## Fixed term: `cooldown N seconds`/`cooldown N minutes` for a `Cooldown`-gated effect

When an `Ability:`/`AbilityText:`/`Description:` chain uses the `Cooldown DOUBLE Action` gate (see `cube-chaos-scripting`), state it as a trailing clause: lowercase `cooldown`, comma before it, no leading capital, converted from ticks to seconds/minutes (60 ticks = 1 second, matching the rest of this DSL's time conversions). Confirmed by tallying every real `cooldown ... second/minute` occurrence in the base game (~28 lowercase vs. ~6 capitalized) — lowercase mid-sentence is the dominant idiom, e.g. `Main/Perks.c.txt`'s `Blood_Scavenger`: "...add a free full hp allied copy of that enemy to your hand, cooldown 1 minute End", and `Main/UpgradePerks.c.txt`'s `Rapid_Lightning_Collector`-style "...gain 1 mana, cooldown half a second End" (sub-1-second values spell out as "half a second", not "0.5 seconds" or "30 ticks").

## Fixed term: the `Silent` action wrapper is "silently" in prose, never a spelled-out paraphrase

When an `Ability:` wraps an effect in `Silent` (do it without triggering any ability — see `cube-chaos-scripting`), the prose term is the adverb **"silently"** placed before the verb: "20% chance it silently gains another copy", "it silently gains a random debuff" (`Main/UpgradePerks.c.txt:2431`), "silently gains 1 regeneration" (`ZUpgradeClassPerks.c.txt:543`), "this silently dies" (lasers/projectiles throughout `Main/3GeneralCubes.c.txt`). `SILENTLY` is a registered tooltip keyword (`Base_Core/ToolTipText.c.txt`: "Do something without triggering ANY ability"), so using the word links the explanation automatically — don't paraphrase it as "(without triggering anything)". Caught on the DJ mod's `Feedback` perk, corrected by the user: the parenthetical form was copied from `Rogue-Moil` (`Characters/Synergies.c.txt:678`), which turns out to be the lone non-idiomatic outlier against a dozen+ "silently" usages — a reminder that **matching a single closest-analog line isn't enough when the phrasing is a recurring term; grep the word itself across the codebase and follow the majority idiom**, especially when a tooltip keyword might exist for it.

## State a created cube's allegiance if it isn't the obvious default

A freshly created cube defaults to allied-to-caster unless the `Ability:` explicitly sets otherwise (see `cube-chaos-scripting`'s faction-defaults note) — this is a real mechanical fact, not a cosmetic detail, so state it whenever it isn't simply "allied" by default omission. Match the base game's own short phrasing rather than a wordy clause: **"an allied X"** for ally-to-caster, **"a neutral X"** for `SetFaction DoubleConstant 0`/`NeutralCopy`, or **"an X of the same faction"** when it inherits another cube's faction dynamically. Real examples: `Shadow.c.txt`'s "replace a random Solid_Shadow with an allied Solid_Shadow_Hive", `UpgradeSpeciesPerks.c.txt`'s "...with a neutral Solid_Shadow_Hive", `Main/3GeneralCubes.c.txt`'s "replace it with a Skewered_Corpse of the same faction".

**But name the spawned cube only — do NOT restate its own stats or abilities in the spawner's text.** The game already shows the spawned cube's card in-game (when a cube/perk creates another cube, that cube is previewed and can be selected to see its own hp/mana/abilities), so restating any of that in the parent's `Text:`/`Description:` is redundant. This covers **both** stats (mana cost, hp) **and** abilities, and abilities **whether baked into the spawned cube's own `CUBE:` block or granted dynamically at the moment of creation** (`GainAbility`/`GainAbilityText` inside the spawning chain) — the created-cube preview surfaces a dynamic grant exactly the same way it surfaces a baked one, so there's no case where restating helps the reader. The base game's own `Ritual` says "create an allied Imp above" — not "create an allied charging acidic hovering Imp." Real correction, the Unholy mod: `Brimstone`'s text first read "create a neutral \C255 106 0 Burning \CN \C155 55 134 Acidic \CN Molten_Brimstone..." and the user cut the keyword restatement down to just "create a neutral Molten_Brimstone..." because `Molten_Brimstone` carries `Burning`/`Acidic` by default and the game surfaces them. Second real correction, also Unholy: `Phylactery`'s `Description:` first read "...add a Damned Soul to your hand — a 0 hp, 5 mana Flying token which, when it dies, creates an allied copy of the cube that died" (`Damned_Soul` is granted its recreate-ability dynamically, via `GainAbility Soul_Memory Victim`, not baked into its `CUBE:` block) — the user cut it to just "...add a Damned Soul to your hand," full stop, since every one of those details (stats, Flying, and the dynamically-granted death effect) is visible by selecting the previewed `Damned_Soul` card. So: name + allegiance (per above) + *what the spawn does that isn't already on its own card* (positioning like "at the top of its column, which falls from there" is fair game since that's the spawner's placement choice, not the cube's intrinsic ability) — but never re-enumerate the spawned cube's stats or abilities, baked-in or dynamically granted.

## Describing perks whose stacked copies independently re-trigger

If a `PERK:`'s `Ability:` will independently re-fire once per owned copy (see `cube-chaos-scripting`'s perk-stacking section), the real idiom is a **plain trailing clarifying sentence**, not a "N% chance per copy"/"per copy you own" quantifier folded into the effect clause itself — grepped the whole codebase for that shape and it doesn't exist anywhere; a first pass invented it and had to be corrected back to the real pattern. Real precedent: `Main/Perks.c.txt`'s `Safety_Foam` ends its `Description:` with "...the foam is poisoned, additional copies of this perk can trigger on the foams creation". Match this shape — state the effect normally first, then add "Additional copies of this perk `<repeat/trigger on/etc>` ..." as its own separate sentence, rather than trying to quantify the scaling inline.

**Only add that sentence when the re-trigger is a genuinely separate/non-obvious mechanism** — e.g. `Safety_Foam`'s second copy triggers on a *different* foam-creation event than the reader would assume from the base description, and `Echo`'s stacking scales a hidden internal roll count via `XTimes AmountOfPerksInInventoryWhich...`, neither of which a reader could infer from the effect sentence alone. **Skip it when the stacking is just the mechanical consequence of a "first cube/target matching X" search that a marked/exiled cube then fails** (see `cube-chaos-scripting`'s "each copy affects a different cube" idiom) — the base game's own `Bird_Feather` (`Main/Perks.c.txt`) stacks exactly this way (2nd copy gives Flying to the *next* flightless cube) and its `Description:` has no such sentence at all, because "the first cube without X" already reads as self-evidently repeatable once you know it excludes cubes that already have X. Caught on the DJ mod's own `Inspiration` perk: a first pass added the clarifying sentence by analogy to `Safety_Foam`/`Echo` before checking whether this specific ability's stacking was actually the unremarkable kind — user corrected it back out.

## Workflow for auditing existing text

1. Read the `Ability:` chain token by token and write down, in plain terms, exactly what it does (every trigger, condition, and effect — including implicit-receiver targets, per `cube-chaos-scripting`).
2. Read the paired `Text:`/`Description:` and check every clause against that list — does it mention everything mechanical, nothing cosmetic, with correct numbers and correct referents (which cube is "it")?
3. Grep the base game for the closest real analog (same trigger, similar granted ability, similar loop-and-chance shape) and compare phrasing, not just correctness — an accurate-but-oddly-worded description is still worth fixing to match established idiom.
