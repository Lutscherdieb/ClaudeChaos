# Publishing a mod to the Steam Workshop

There is no external upload tool, CLI, or SteamCMD step for this game — publishing is entirely an **in-game** feature built on `steamworks4j` (`com.codedisaster.steamworks.SteamUGC`). None of this is documented in `ModdingInfo.txt`/`ModdingExplanation.txt` or discoverable from data files; everything below was reverse-engineered from the shipped `Cube Chaos.jar` bytecode (class/method names cited as evidence, per the research protocol) since there is no log line or launch behaviour to grep for a UI-only feature like this. Confirmed against `Cube Chaos.jar` as of the 2025-09-01 build (`dw/game/dd/ModManager.class`, `dw/game/dd/Screens/PackageSelectScreen.class`, `dw/game/dd/Screens/ModTaggingScreen.class`, `dw/game/dd/Screens/StartScreen.class`).

## Where the feature lives in-game

Main menu → **MODDING** button (`StartScreen.class` references `PackageSelectScreen`) → opens the "Select Packages" screen. Per mod folder listed there, the relevant buttons are:

- **OPEN FOLDER** — opens `GameData/<Mod>/` in the OS file explorer (`java.awt.Desktop.open`).
- **MODIFY TAGS** — opens `ModTaggingScreen` ("APPLY TAGS"), a checklist UI built from the fixed `CorrectTags` list (see below), which rewrites the mod's `Description` file's `Tag:` lines.
- **NEW PROJECT** — tooltip *"Turns this folder into a new workshop mod"*. Calls `ModManager.CreateNewItem`, which creates a Steam UGC item (`SteamRemoteStorage.WorkshopFileType.Community`) and then **overwrites the mod's `Description` file**, replacing `ID:` with the real Steam `PublishedFileID` (a large Steam-assigned number, not the small local placeholder) and rewriting `Name:`. This is one-shot: only use it the first time a mod is published, never again for the same mod.
- **UPDATE WORKSHOP** — tooltip *"Update this workshop mod, fails if your not the owner"*. Calls `ModManager.UpdateItem`, which reads the existing `ID:` from `Description` (via `NextLong`, so it must already be a real Steam ID from a prior `NEW PROJECT`) and pushes an update to that same Steam item.
- Both actions are preceded by a link to `https://steamcommunity.com/sharedfiles/workshoplegalagreement` with the label *"By submitting this item, you agree to the workshop terms of service (LINK)"* — read/accept this before actually publishing.
- **SAVE AND CLOSE** writes `GameData/Loading_Order.txt` from the screen's current package order — the normal way this file gets written, confirming `Loading_Order.txt` edits are also achievable by hand (as this skill already assumes) or via this screen.

Steam must be running for any of this (`SteamAPI.isSteamRunning()` gate, same as the existing `Couldn't innitiate steam API` warning already documented above).

## Requirements to have ready before clicking "NEW PROJECT"

1. **`GameData/<Mod>/Image.png`** — a top-level image file (sibling of `Description`, *not* inside `Sprites/`) used as the Workshop thumbnail via `setItemPreview`, only if the file exists (`new File(FolderName + "/Image.png").exists()` gates the call — no image means no preview set, not a crash). No in-game size/dimension check was found; treat Steam's own Workshop image constraints (square-ish, reasonable file size) as the practical limit since validation happens server-side, not in this code path.

   **This repo's convention (established 2026-07-25, DJ/General/Unholy; baked into the orchestrator's `workflows/content-class-species.md` as a standard step, not a one-off backfill):** for a single-class/single-species mod, source `Image.png` from that class/species's own base-perk icon — sprite-sheet tile `(0,0)` of the `PERK:` file where the class/species's own name is the *first* `PERK:` block (confirmed: `PERK: DJ` is line 1 of `DJ_Perks.c.txt`, `PERK: General` is the first `PERK:` block of `General_Perks.c.txt`, `PERK: Unholy` the first of `Unholy_Species.c.txt`). Crop the 27×27 tile, **then strip the outermost 1px on all four sides** (that's the universal magenta `RGB(255,0,220)` guide ring from `cube-chaos-sprite-art`'s border-pattern library — it renders fine as an in-game tile border but reads as an unwanted pink frame on a standalone thumbnail), leaving a 25×25 image, then upscale with **nearest-neighbor** (no smoothing) to keep pixel art crisp — 20x lands at 500×500, a reasonable Workshop thumbnail size. A mod with multiple classes/species or no single obvious icon needs a human call on what to show instead; don't assume this recipe generalizes past the single-class/species case.
2. **Valid `Tag:` values in `Description`.** The engine validates tags against a fixed array (`ModManager.CorrectTags`, populated in its static initializer) — exactly these 12 values, case-sensitive:
   ```
   Classes/Species
   Perks
   Cubes
   Terrain
   Scenarios
   Curses
   Events
   Consumables
   Modding
   Resprite
   Balance
   NodeMap
   ```
   Anything else logs `Unknown tag <X> detected while uploading your mod` (`ModManager` → `Library.PrintWarning`) at publish/update time. This skill's own scaffolding template previously said `Tag: <FreeformTag>` — that's wrong for Workshop purposes; tags are freeform only in the sense that the *file format* doesn't restrict them, but the *Workshop upload path* does. Pick from the list above (a class/species mod almost always wants `Classes/Species` plus whichever content categories it actually has — `Perks`, `Cubes`, `Curses`, `Consumables`, etc.).
3. **A real, not-yet-consumed local `ID:`.** The scaffolding-time `ID: <random unique 10-digit number>` (see main skill body) is exactly what `NEW PROJECT` expects to find and overwrite the first time. Don't hand-edit `ID:` after a mod has ever been published — `UPDATE WORKSHOP` trusts it to name the correct existing Steam item, and Steam will reject an update from a non-owner/wrong-ID.
4. **No in-game field sets the Workshop item's description/body text** — `ModManager` calls `setItemTitle`, `setItemPreview`, `setItemTags`, `setItemContent`, `submitItemUpdate`, but never `setItemDescription`. After `NEW PROJECT` creates the item, its Community page (the `steam://url/CommunityFilePage/<id>` overlay the game opens on success) still needs its description filled in manually via Steam's own web UI — the in-game tool only handles title/tags/thumbnail/content, not marketing copy.

## TODO: required-items/dependency declaration for a crossover mod (unconfirmed, needs a jar decompile pass)

A "bridge" mod that only makes sense with two other mods both installed (e.g. `DJ_Voidling`, which pairs the `DJ` and `Voidling` mods via a `BelongsTo: CLASSSPECIES` perk — see the project memory on cross-mod synergy perks) should ideally declare `DJ` and `Voidling` as required Workshop items, so subscribing to the bridge mod auto-subscribes to both. **Whether `ModManager`/`SteamUGC` actually exposes this is not yet confirmed** — none of the reverse-engineering that produced this file's other sections (`NEW PROJECT`/`UPDATE WORKSHOP`/tags/thumbnail) turned up a call to Steam's `addDependency`/required-items API, but that reverse-engineering was never specifically looking for one either. Before actually publishing any crossover mod: re-run the same CFR-decompile approach used elsewhere in this repo (see `reference_jar_decompile_technique` in project memory) against `ModManager.class` looking for `SteamUGC.addDependency`/`addRequiredTag`-style calls, or check whether the in-game "Select Packages" screen exposes any dependency UI at all. If no such mechanism exists, the fallback is just documenting the requirement prominently in the crossover mod's own `README.md` (already done for `DJ_Voidling`) and its Workshop page description, since there's no automatic enforcement.

## What "UPDATE WORKSHOP" actually uploads

`setItemContent` is pointed at the mod's own `GameData/<Mod>/` folder (`Path: ` + the folder), so the whole folder — `.c.txt` files, `Sprites/`, `Description`, `README.md`, `Preview/` — goes up as the Workshop item's content, not a hand-picked subset. Nothing in this skill's existing file-layout guidance needs to change for that; it just means anything sitting in the mod folder ships to players, so don't leave scratch/debug files there.

## This repo's current publish-readiness (last updated 2026-08-02, all 8 mods)

`ID:` is still an untouched local placeholder for every mod below (none published yet). Only 4 of 8 have satisfied every *file-level* requirement (an `Image.png`, specifically) — this table previously only tracked 3 plus `DJ_Voidling` and went stale as `Voidling`/`Broker`/`Great_Wall`/`Home_Turf_Advantage` were added; re-audited against real `GameData/<Mod>/Image.png`/`Description` state on 2026-08-02, not assumed. (`Home_Turf_Advantage` was absorbed into `Crusader` later the same day and its row replaced — a mod that disappears must be *removed* from this table, not left as a phantom row.)

| Mod | `Image.png` | `Tag:` values | Still needed to actually publish |
|---|---|---|---|
| `DJ` | ✅ headphones (base class perk) | `Classes/Species`, `Perks`, `Cubes`, `Curses`, `Consumables` | MODDING → NEW PROJECT → fill in description on the Community Page it opens |
| `General` | ✅ grenade-flask (base class perk) | `Classes/Species`, `Perks`, `Cubes` | same |
| `Unholy` | ✅ demon head (base species perk) | `Classes/Species`, `Perks`, `Cubes` | same |
| `Voidling` | not yet generated (single-species mod — the standard recipe applies: crop `PERK: Voidling`'s icon, the first `PERK:` block in `Voidling_Species.c.txt`) | `Classes/Species`, `Perks`, `Cubes` | `Image.png`, then NEW PROJECT |
| `Broker` | not yet generated (single-class mod — the standard recipe applies: crop `PERK: Broker`'s icon, the first `PERK:` block in `Broker_Perks.c.txt`) | `Classes/Species`, `Perks`, `Cubes`, `Scenarios` | `Image.png`, then NEW PROJECT |
| `Great_Wall` | not yet generated (a Terrain mod, no class/species base perk to source from — needs a human call, same as `DJ_Voidling`) | `Terrain` | `Image.png` + a human call on source art, then NEW PROJECT |
| `Crusader` | ✅ gold Latin cross (base class perk) | `Classes/Species`, `Perks`, `Cubes` | MODDING → NEW PROJECT → fill in description on the Community Page it opens |
| `DJ_Voidling` | not yet generated (single-synergy-perk mod, no obvious single default — see the class/species workflow's Image.png step) | `Classes/Species`, `Perks` | `Image.png` + the required-items TODO above, then NEW PROJECT |

Re-audit the `Tag:` row whenever a mod gains a genuinely new content category (a `_Curses.c.txt`, `_Consumables.c.txt`, a terrain/event/scenario file, etc.) — General and Unholy were checked against every `CorrectTags` category on 2026-07-25 and confirmed to have no curse/consumable/terrain/event/scenario content, so their 3-tag set is deliberately minimal, not an oversight. The 5 newer rows' `Tag:` values above are only transcribed from each mod's real `Description` file, not independently re-audited against `CorrectTags` category-by-category the way DJ/General/Unholy were.

Once any mod actually goes through `NEW PROJECT`, update its row here with the real Workshop item URL/ID and drop it from "still needed."
