---
name: cube-chaos-balancing
description: Use whenever picking numeric stats for a new or edited CUBE (mana cost, hp/maxhp, IDENT rarity/aggressive/defensive/scaling/weirdness) or the pricing fields for a new PERK-family item (Value:/BalanceCap:) in a Cube Chaos mod. Covers what these numbers actually mean and empirical ranges by rarity/category, so numbers get chosen deliberately instead of copied from one arbitrarily-picked analog cube or guessed. Trigger on "how much mana should this cost", "what rarity", "what hp", "is this too strong/weak", "balance", "IDENT stats", "Value:", "BalanceCap:", or generally whenever a new obtainable CUBE:/PERK: needs numbers and it's not obvious what they should be.
---

# Cube Chaos numeric balancing (CUBE stats and PERK economy fields)

This skill is about **picking the actual numbers**, not the DSL that uses them (see `cube-chaos-scripting` for `Ability:` syntax) or the wording that describes them (see `cube-chaos-rule-text`). It exists because "what mana cost/hp/rarity should this be" is a real design question this repo used to answer by ad hoc analogy to one or two existing cubes (or by asking the user each time) rather than from any systematic reference — this catalogs the actual empirical distribution across all 546 real `IDENT` cubes in the base game plus both mods (`Modding_Example` excluded — its stats are deliberately absurd teaching placeholders, e.g. a 188,000 hp cube), so a new cube's numbers can be chosen deliberately, and checked against the whole population, not just whichever cube happened to be open at the time.

## Research protocol — this skill first, base game second, write back always

1. **Check this skill first.** The `IDENT` field meanings and the empirical ranges by rarity are below. If the question is covered, use it and stop.
2. **If not covered, derive it from real numbers, not intuition.** Neither `ModdingInfo.txt` nor `ModdingExplanation.txt` says anything about what a *good* value is — they only define the fields — so the ground truth is the distribution across real base-game entries. Grep the whole corpus for the relevant field and aggregate (`sort | uniq -c | sort -rn`) rather than reading two or three cubes; and **filter to the right comparison class first** — same rarity, same `TYPE`, same `BelongsTo:` kind. Matching against the wrong class is the failure mode this skill exists to prevent (see the `Value:` audit in `cube-chaos-scripting`, where 167 real class perks disproved a pattern copied from an unrelated category).
3. **Write the finding back into this skill, in the same edit** — the number, the sample size it came from, and the filter that defined the comparison class. A range without its N can't be trusted or refined later.

**Never edit base-game files** while researching (see `CLAUDE.md`) — read freely, write never.

## `IDENT rarity aggressive defensive scaling weirdness` — what each number actually means

Straight from `ModdingExplanation.txt`'s own worked example (`Dwarven_Warrior`, `IDENT 1 20 0 0 0`, manacost 25): **rarity does NOT affect power** — it only controls how often the cube is offered (1 = common ... 4 = legendary). The other four numbers are the *designer's own estimate*, in mana-equivalent units, of how much of this cube's manacost is realized as each flavor of value to the AI's own cube-evaluation logic:

- **aggressive** — offensive/damage-dealing value. `Dwarven_Warrior` (a melee attacker) gets "almost its full manacost" here (20 of 25).
- **defensive** — survivability/tanking/blocking value.
- **scaling** — long-term/compounding value (grows more valuable the longer the battle runs).
- **weirdness** — high-variance/situational value (powerful sometimes, useless other times).

These four are **not required to sum to the manacost** — `Dwarven_Warrior` "doesn't really provide any" of the other three, so they're all 0 even though its manacost is 25 and its aggressive value is only 20 (a 5-mana "gap" is normal, not an error). Treat them as your own honest self-assessment of the cube's realized value breakdown, not a budget that must balance to zero.

**Because rarity is mechanically decoupled from power, don't reach for "make it rarer" as a way to justify a stronger effect** — the engine won't compensate for that on its own the way it might in a game where rarity directly gates power. That said, every real rarity tier in the base game still *empirically* skews toward higher mana cost at higher rarity (see table below) — this is a **design convention the base game follows voluntarily, not an engine rule**, and new mod content should probably follow it too for the same reason the base game does: a player's intuition ("legendary = big/exciting") gets violated if a rarity-1 cube quietly outperforms a rarity-4 one, even though nothing stops that from working. Pick rarity for "how often should this be offered / does this feel like a signature effect", then sanity-check the resulting mana cost against that rarity's real range below — don't pick rarity *because* you want more power out of it.

## Empirical ranges by rarity (546 real `IDENT` cubes, `Modding_Example` and 4 extreme joke-stat outliers excluded — see below)

| Rarity | n | Mana (median / range) | HP (median / range) | agg+def+scale+weird sum (median / range) | Typical agg/def/scale/weird (medians) |
|---|---|---|---|---|---|
| 1 (common) | 132 | 25 / 3–100 | 7 / 0–200 | 20 / 3–100 | 0 / 4 / 0 / 1 |
| 2 (uncommon) | 200 | 42.5 / 5–100 | 8 / 0–99 | 40 / 1–160 | 0 / 0 / 5 / 10 |
| 3 (rare) | 160 | 60 / 3–100 | 7 / 0–100 | 50 / 3–300 | 0 / 0 / 10 / 15 |
| 4 (legendary) | 50 | 75 / 10–100 | 8.5 / 0–43 | 75 / 5–300 | 0 / 0.5 / 10 / 40 |

A rough population-wide linear fit: `hp + (agg+def+scale+weird) ≈ 0.95 × manacost + 12`. Useful as a sanity check on a finished stat line (does the total realized value roughly track the mana cost, or is it wildly over/under), **not** as a formula to solve for numbers from scratch — real cubes scatter widely around this line (the range columns above are wide for a reason: a cheap-but-weird rarity-3 cube and an expensive-but-straightforward one can have the same total). The four excluded outliers (`Erode` `10000/10000`, `Reality_Weirding`, both `Forbidden_Research:` cubes) are real base-game cubes with deliberately joke/thematic-extreme stats (a genuinely build-breaking "erodes everything" effect) — evidence that the engine tolerates extreme numbers when the effect is genuinely that extreme, not evidence that such numbers are normal to reach for.

**Notice `defensive` medians at 0 for rarities 2–4** — high explicit `defensive` values are the exception, not the norm, across the whole population (rarity 1's median of 4 is the outlier, likely reflecting cheap "reference me" chaff cubes). Don't default to splitting value evenly across all four categories; most real cubes lean hard into one or two and leave the rest at 0, matching `Dwarven_Warrior`'s own worked example.

## The actual method: match a real analog first, use the table as a sanity check second

Consistent with this whole skill set's core discipline (`cube-chaos-scripting`: "grep a real working example before writing from scratch") — **don't compute a new cube's numbers from the table above in isolation.** Grep `GameData/**/*.c.txt` for the closest existing cube by role/shape (similar `TYPE`, similar `Ability:` pattern — a stationary periodic-spawner, a melee attacker, a flying harasser, etc.) and start from its exact `IDENT` line, adjusting only for genuine differences in power. This is what `Rocket_Silo` did in practice: matched `Artillery`'s full stat line (`30 mana, 3/3 hp, IDENT 1 20 5 0 5`) since both are stationary rarity-1 `Shooter`-type cubes that periodically launch a token projectile cube — copying a proven real analog beats deriving from the population table, the same way copying a real `Ability:` chain beats deriving syntax from the grammar list alone. Use the table above only to catch a result that's an outlier against the *whole* population for its rarity (e.g. a rarity-1 cube with a mana cost of 90 should prompt a second look, even if its one chosen analog happened to also be expensive).

**If unsure which rarity to pick at all (not just which mana cost), ask the user rather than guessing** — this is a real design/tone decision (how often should this feel available), not something derivable from the ability chain alone, matching this repo's established practice of asking before inventing a stat spread (see the orchestrator's `content-cube.md` "don't guess a rarity/stat spread" note).

## `TOKEN` cubes need none of this

A `TOKEN` cube (not randomly obtainable — created only as a byproduct of another cube/perk's own ability, e.g. `Bomb`, `Shot`, `Rocket`) has no `IDENT` line at all, hence no rarity/aggressive/defensive/scaling/weirdness numbers to choose. Its manacost is conventionally `0` (every real base-game and mod `TOKEN` cube checked uses `0`) since it's never bought from mana, only spawned. hp/maxhp still matter (how tanky the spawned cube is) and should be balanced by analogy the same way as an `IDENT` cube's hp — just without the rarity/AI-value fields.

## `PERK:`-side pricing: `Value:`/`BalanceCap:` — see `cube-chaos-scripting`, don't duplicate here

The reward-perk-vs-priced-category distinction (`Value:` is illegal on a plain class/species reward perk, required on Curses/Blights/Boons/Consumables/Golden/Neutral/CubeUpgrade perks), the real `Value:` ranges per category, the curse round-multiples-of-50 clustering, the `IsUpgradeFrom:` pricing-ladder table, and the `BalanceCap:` inverse-relationship-to-Value heuristic are all already fully cataloged in `cube-chaos-scripting`'s "Perk economy fields" and "Curse-specific `PERK:` conventions" sections, with real audited counts (e.g. 167:0 for class perks never carrying `Value:`). Read those directly rather than treating this skill as a second source for perk pricing — this skill's own table above is CUBE-side (`IDENT` stats) specifically because that side had no systematic reference before now.
