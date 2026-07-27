# Reward / economy scenarios (chests, shops, the Forge, curse-trades)

Load this when building a new non-combat map-node screen — a chest, a shop, a forge, a curse-trade, or any scenario using `PERK_REWARD:`/`CUBE_REWARD:`/`SHOP:`/`CURSED_TRADE:`/`PERK_SELECTION:`/`CLASS_SELECTION`/`DOUBLE_SIDED_PERK_SELECTION:`. All real examples are from `Extra_Mechanics/Reward_Scenarios.c.txt` and the `Blight_Boon_Selection`/`Secondary_Blight_Boon_Selection` scenarios in `Extra_Mechanics/Nightmares.c.txt` — the sole source in the base game (see the parent skill's Ground truth section).

## The simplest reward node: flavor text + a `START_ACTION:`, nothing else

The easiest on-ramp for a new reward-node type — no dedicated body keyword at all, just an effect and (usually) a redirect into a real reward block:

```
SCENARIO: Heal
Info: Gain 1 life and 5 gold End
CubeImage: A_Life
End
START_ACTION: Both Both GainALife ChangeCurrency 5
ChangeDifficulty DoubleConstant 1
SEnd
```

```
SCENARIO: Painfull_Perk_Chest
Info: Perk Chest, but if you have more than 1 life lose 1 End
CubeImage: Evil_Chest
End
START_ACTION: Both If IsLarger RemainingLives DoubleConstant 1 LoseALife 
Both ChangeDifficulty DoubleConstant 1
ReadAScenario Basic_Perk_Reward
SEnd
```

**For a genuinely new reward-node idea (a twist on an existing reward, a new one-shot effect), this shape is usually enough** — apply the twist's own effect in `START_ACTION:`, then `ReadAScenario` into whichever real `PERK_REWARD:`/`CUBE_REWARD:`/`SHOP:` block below matches the underlying reward. Every real "chest but with a catch" scenario (`Painfull_Perk_Chest`, `Coin_Nightmare`) follows exactly this pattern rather than redefining the reward block itself.

## `PERK_REWARD:` — perk chests and curse/perk trade-offs

```
SCENARIO: Basic_Perk_Reward
Info: Perk Chest End
CubeImage: Chest
End
PERK_REWARD: 
OPTIONS: Highest 1 Addition 3 GetCampaignVariable PERKREWARDCHOICES
VALUE: Addition DoubleConstant 10 GetCampaignVariable CHESTMINVALUEADD
 Addition DoubleConstant 50 GetCampaignVariable CHESTMAXVALUEADD
REROLLS: Addition DoubleConstant 1 GetCampaignVariable ADDITIONALREROLLS
HOWMANY: Addition DoubleConstant 1 GetCampaignVariable ADDITIONALPERKSINCHESTS
BELONGSTO: IfElse IsLarger GetCampaignVariable CHESTCHAOS DoubleConstant 0 StringConstant All StringConstant Default
End
SEnd
```

Fields, confirmed across `Basic_Perk_Reward`/`Basic_Curse_Reward`/`Terrain_Exchange_Reward` (all `PERK_REWARD:`):

- **`OPTIONS: DOUBLE`** — how many perks are shown to choose from (usually `3` + a campaign-variable bonus).
- **`VALUE: DOUBLE DOUBLE`** — min/max `Value:` range the pool is filtered to. `Basic_Curse_Reward` uses a literal `VALUE: -50 -10` (curses only); `Basic_Perk_Reward` computes both ends from campaign variables (so late-game chests offer higher-value perks).
- **`REROLLS: DOUBLE`** — free rerolls offered.
- **`HOWMANY: DOUBLE`** — how many of the shown options are actually *granted* (as opposed to just offered) — omit for the default of 1.
- **`BELONGSTO: STRING`** — restricts the candidate pool to one literal `BelongsTo:` string. `Terrain_Exchange_Reward` uses a bare `BELONGSTO: StringConstant Terrain` to build a terrain-only reward; `Basic_Perk_Reward` computes it conditionally between `"All"`/`"Default"` based on a chaos-mode campaign variable.
- **`PERKREQ: BOOLEAN`** — an arbitrary predicate filter on candidates (`Test`-scoped, same as an `Ability:` chain's cube predicates but over perks) — used by `Trash_Positive` (a `PERK_SELECTION:` block, see below) to restrict to `IsLarger ValueOfPerk Target 0`.

**A new "exchange one category of perk for another" scenario** (the `Terrain_Exchange_Reward` shape: `BELONGSTO:` restricts the *offer*, a separate `START_ACTION: LosePerkWithScreen ARandomPerkInInventoryWhich PerkIsType Test <Category>` removes an old one first) is the real pattern for a themed reward pool — copy `Terrain_Exchange_Reward` directly and swap the category string and lose-predicate.

## `PERK_SELECTION:` — a broader selection-screen mechanism, keyed by `TYPE:`

Distinct from `PERK_REWARD:` (which is specifically "offer N perks from a filtered pool, grant some"). `PERK_SELECTION:` is a more general selection-screen block; its exact shape depends on `TYPE:` (confirmed values `0`, `1`, `2` — no confirmed 4th value):

**`TYPE: 0` — the Forge (upgrade perks/cubes for gold):**
```
SCENARIO: Forge
Info: Forge: Upgrade your perks and random cubes End
CubeImage: Forge
End
PERK_SELECTION: 
TYPE: 0
COST: Addition Multiplication 20 GetCampaignVariable FORGEDALREADY
 Addition Minus 20
  Subtraction ValueOfPerk UpgradeOfPerk Target ValueOfPerk Target 
ACTION: SetCampaignVariable FORGEDALREADY 1
COSTMULT: 1 
CUBEUPGRADEAMOUNT: RoundedDown Division AmountOfCubesInInventoryWhich True 2
CUBECOST: Addition Multiplication 20 GetCampaignVariable FORGEDALREADY
 Addition Minus 20
  ValueOfPerk Target
INFO: Spend gold to upgrade perks and random cubes (first each run costs 20 less) End
End
SEnd
```
`COST:`/`CUBECOST:` are gold-price formulas (see `cube-chaos-scripting`'s perk-economy `IsUpgradeFrom:` pricing note — `COST:` here is exactly `ValueOfPerk(upgrade) - ValueOfPerk(base)`, minus a one-time 20g discount tracked via the `FORGEDALREADY` campaign variable, flipped off by `ACTION:` after first use). `COSTMULT:` is a global multiplier, `CUBEUPGRADEAMOUNT:` caps how many random cubes get upgraded alongside perks, `INFO:` is flavor text for the selection screen itself (distinct from the scenario header's own `Info:`). `NoCube_Forge` is the same shape with `CUBEUPGRADEAMOUNT:`/`CUBECOST:` omitted (perks only).

**`TYPE: 2` — destroy/trash a perk:**
```
SCENARIO: Trash_Positive
Info: Trash perks with positive value End
PerkImage: Void
End
PERK_SELECTION: 
TYPE: 2 
PERKREQ: IsLarger ValueOfPerk Target 0
BACKOUT: true
RESULT: TRASH End
End
SEnd
```
`PERKREQ:` filters which owned perks are eligible, `BACKOUT: true` lets the player cancel out without picking one, `RESULT: TRASH` destroys the chosen perk instead of granting anything.

**`TYPE: 1`** appears once, inside `SCENARIO: Campaign` itself (`PERK_SELECTION: TYPE: 1 End`, no other fields) — its exact role isn't independently confirmed from this one example; don't extrapolate a shape for it beyond copying that literal usage if a new game-mode-level `Campaign` scenario needs it.

## `CUBE_REWARD:` — cube chests

```
SCENARIO: Basic_Cube_Reward
Info: Cube Chest End
End
CUBE_REWARD:
DoubleConstant 2
Addition DoubleConstant 3 GetCampaignVariable CUBEREWARDCHOICES
Addition DoubleConstant 1 GetCampaignVariable ADDITIONALREROLLS
SEnd

SCENARIO: Rare_Cube_Reward
Info: Rare Cube Chest End
End
CUBE_REWARD: 
DoubleConstant 1
Addition DoubleConstant 3 GetCampaignVariable CUBEREWARDCHOICES
Addition DoubleConstant 1 GetCampaignVariable ADDITIONALREROLLS
SEnd
```
Three positional `DOUBLE` arguments, no field labels. By comparing the "Basic" (`2`) vs "Rare" (`1`) first argument against the game's own rarity numbering (`1`=common..`4`=legendary), this is very likely a **maximum-rarity-index-eligible** value read in the opposite direction from `IDENT`'s own rarity field (lower number = *more* exclusive/rare pool, not a literal rarity floor) — plausible but not confirmed against engine source. The 2nd/3rd args match `CUBE_REWARD:`'s shown-choices-count and rerolls, consistent with every other reward block's pattern. **For a new cube-reward tier, copy whichever of these two literally is closer to the intent** (`Basic_Cube_Reward` for a normal chest, `Rare_Cube_Reward` for a better one) rather than inventing a new first-argument value.

## `SHOP:`

```
SCENARIO: Shop
Info: Shop: Buy stuff End
CubeImage: Shop
End
SHOP: 

PERKS: Addition DoubleConstant 2 GetCampaignVariable SHOPADDEDROWS
DoubleConstant 3
DoubleConstant 1

CUBES: Addition DoubleConstant 2 GetCampaignVariable SHOPADDEDROWS
DoubleConstant 1
DoubleConstant 2

REROLLS: Addition DoubleConstant 1 GetCampaignVariable ADDITIONALREROLLS
PRICE_ADD: GetCampaignVariable SHOPPRICEADD
PRICE_MULT: Addition DoubleConstant 1 GetCampaignVariable SHOPPRICEMULT
PRICE_FLUCTUATION: Addition Division DoubleConstant 1 DoubleConstant 5 GetCampaignVariable SHOPPRICEFLUCTUATION
MIN_BUY: GetCampaignVariable SHOPMINBUY
End
SEnd
```
`PERKS:`/`CUBES:` each take 3 positional `DOUBLE`s (first is rows, confirmed via `Boons.c.txt`'s `Big_Shop` perk which literally adds to `SHOPADDEDROWS`; the other two are unconfirmed further, plausibly item-count/rarity-weight per row). `REROLLS:`/`PRICE_ADD:`/`PRICE_MULT:`/`PRICE_FLUCTUATION:`/`MIN_BUY:` are single `DOUBLE`s each, all reading from dedicated campaign variables — this is the only real `SHOP:` in the base game, so a second shop-flavored scenario should copy this structure wholesale and only change which campaign variables (or literals) feed each field.

## `CURSED_TRADE:`

```
SCENARIO: Cursed_Trade
Info: Get curses and perks in equal measures End
CubeImage: Cursed_Trade
End
CURSED_TRADE: Addition Division DoubleConstant 3 DoubleConstant 10 GetCampaignVariable CURSEDTRADEDOUBLECHANCE
Addition DoubleConstant 1 GetCampaignVariable ADDITIONALREROLLS
SEnd
```
Two positional `DOUBLE`s: a chance fraction (whether the trade doubles up) and a reroll count.

## `DOUBLE_SIDED_PERK_SELECTION:` — the Blight/Boon trade screen

This is how Blight/Boon perks (`cube-chaos-scripting`'s perk-economy Blight/Boon/Nightmare section) actually reach the player:
```
SCENARIO: Blight_Boon_Selection
Info: Choose some amount of blights and boons remaining turning into difficulty and gold End
CubeImage: Cursed_Trade
End
DOUBLE_SIDED_PERK_SELECTION: 
 BlightValue: GetCampaignVariable BLIGHT_VALUE
 BoonValue: Addition GetCampaignVariable BOON_VALUE Power GetCampaignVariable INFINITE_BOON_VALUE Division 6 10
 End
SEnd
```
`BlightValue:`/`BoonValue:` are `DOUBLE` "budgets" — how much negative/positive perk value the player can pick from that screen (fed by the `BLIGHT_VALUE`/`BOON_VALUE`/`INFINITE_BOON_VALUE` campaign variables that Blight/Boon/Nightmare perks themselves bump — see the perk-economy reference). `Secondary_Blight_Boon_Selection` is the same shape plus `ShopBoon: False` (an optional `BOOLEAN` field, presumably toggling whether a shop-flavored boon option is included).

## `CLASS_SELECTION`

```
SCENARIO: Class_Species_Selection
End

CLASS_SELECTION

SEnd
```
A bare keyword with no fields — the standard class/species-picking screen. Reuse this scenario directly (`ReadAScenario Class_Species_Selection`) rather than redefining it; there's no confirmed use case in the real files for a second, differently-configured class-selection screen.
