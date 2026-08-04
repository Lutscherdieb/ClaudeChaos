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

   **Never hand-crop this. Run the script, for every mod, after any edit to a mod's namesake perk tile:**

   ```
   python3 .claude/skills/cube-chaos-mod-setup/scripts/render_workshop_image.py            # all mods
   python3 .claude/skills/cube-chaos-mod-setup/scripts/render_workshop_image.py Broker     # just one
   ```

   **Verify it worked** by checking the printed `wrote <Mod>/Image.png (500x500, from `PERK: <X>` in <sheet>)` line names the perk you expected — a mod whose namesake perk isn't the *first* `PERK:` in its own file prints a `skip` line instead of silently picking the wrong tile.

   The script implements this repo's convention (established 2026-07-25 for DJ/General/Unholy; baked into the orchestrator's `workflows/content-class-species.md` as a standard step): source `Image.png` from the mod's own namesake perk icon — sprite-sheet tile `(0,0)` of the `PERK:` file where the mod's own name is the *first* `PERK:` block. Crop the 27×27 tile, **strip the outermost 1px on all four sides** (the universal magenta `RGB(255,0,220)` guide ring from `cube-chaos-sprite-art`'s border-pattern library — fine as an in-game tile border, an unwanted pink frame on a standalone thumbnail), then upscale the remaining 25×25 with **nearest-neighbor** (no smoothing) — 20× lands at 500×500. The script verifies the ring really is uniform magenta before stripping and warns rather than cropping real art if it isn't; it matches a perk name to its folder with `_` and `-` treated as equivalent, so a bridge mod's `PERK: DJ-Voidling` resolves to `GameData/DJ_Voidling/`.

   **Why it's a script now (2026-08-04):** the recipe lived here as prose and was executed by hand three times. That is exactly long enough for it to rot — `Crusader/Image.png` had gone stale against a later sprite touch-up (commit `3b0746d`) with nothing to catch it, and four newer mods had no `Image.png` at all. The script was validated by confirming it reproduces the three hand-made images **pixel-identically** (`ImageChops.difference(...).getbbox() is None` for DJ/General/Unholy) while correctly flagging Crusader as differing — so a re-run is provably a no-op on anything already correct.

   **The "needs a human call" caveat is retired.** This file previously said the recipe didn't generalize past the single-class/species case, and marked `Great_Wall` (Terrain) and `DJ_Voidling` (synergy bridge) as needing hand-picked art. Checked 2026-08-04: both have exactly one distinguishing perk sitting at tile `(0,0)` (`PERK: Great_Wall`, `PERK: DJ-Voidling`), and the identical rule covers them with no special-casing. Only a mod with genuinely *several* equally-central perks, or none whose name matches its folder, still needs a human call — and the script says so with a `skip` line rather than guessing.

   One known cosmetic tradeoff, accepted rather than fixed: a `CLASSSPECIES` synergy portrait carries `cube-chaos-sprite-art`'s multi-pixel magenta combo border *inside* the 1px guide ring, so `DJ_Voidling/Image.png` keeps a busy pink frame that the single-pixel strip doesn't remove. It's legible at thumbnail size and it's the mod's real in-game icon; stripping it would mean teaching the script a second, border-pattern-specific crop for one mod.
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

## This repo's current publish-readiness (last updated 2026-08-04, all 8 mods)

`ID:` is still an untouched local placeholder for every mod below (none published yet). **All 8 now satisfy every *file-level* requirement** — `render_workshop_image.py` generated the 4 missing `Image.png` files and regenerated the stale `Crusader` one on 2026-08-04, so the `Image.png` column is no longer a per-mod checklist item at all: it is whatever the script most recently wrote, for every mod, and re-running it is the fix if that's ever in doubt. (This table previously tracked only 3 mods plus `DJ_Voidling` and went stale as `Voidling`/`Broker`/`Great_Wall`/`Home_Turf_Advantage` were added. `Home_Turf_Advantage` was later absorbed into `Crusader` and its row replaced — a mod that disappears must be *removed* from this table, not left as a phantom row.)

| Mod | `Image.png` source perk | `Tag:` values | Still needed to actually publish |
|---|---|---|---|
| `DJ` | headphones (`PERK: DJ`) | `Classes/Species`, `Perks`, `Cubes`, `Curses`, `Consumables` | MODDING → NEW PROJECT → fill in description on the Community Page it opens |
| `General` | grenade-flask (`PERK: General`) | `Classes/Species`, `Perks`, `Cubes` | same |
| `Unholy` | demon head (`PERK: Unholy`) | `Classes/Species`, `Perks`, `Cubes` | same |
| `Voidling` | void orb (`PERK: Voidling`) | `Classes/Species`, `Perks`, `Cubes` | same |
| `Broker` | gold dollar sign (`PERK: Broker`) | `Classes/Species`, `Perks`, `Cubes`, `Scenarios` | same |
| `Great_Wall` | the wall itself (`PERK: Great_Wall`) | `Terrain` | same |
| `Crusader` | gold Latin cross (`PERK: Crusader`) | `Classes/Species`, `Perks`, `Cubes` | same |
| `DJ_Voidling` | synergy portrait (`PERK: DJ-Voidling`) | `Classes/Species`, `Perks` | the required-items TODO above, then NEW PROJECT |

Re-audit the `Tag:` row whenever a mod gains a genuinely new content category (a `_Curses.c.txt`, `_Consumables.c.txt`, a terrain/event/scenario file, etc.) — General and Unholy were checked against every `CorrectTags` category on 2026-07-25 and confirmed to have no curse/consumable/terrain/event/scenario content, so their 3-tag set is deliberately minimal, not an oversight. The 5 newer rows' `Tag:` values above are only transcribed from each mod's real `Description` file, not independently re-audited against `CorrectTags` category-by-category the way DJ/General/Unholy were.

Once any mod actually goes through `NEW PROJECT`, update its row here with the real Workshop item URL/ID and drop it from "still needed."
