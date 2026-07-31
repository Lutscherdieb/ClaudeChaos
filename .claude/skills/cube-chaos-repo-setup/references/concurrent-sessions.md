# Running more than one Claude Code session against this repo at once

This is the procedure `session_git_workflow: worktree-gated` (see `SKILL.md`'s Step 4 questionnaire) points at. It only exists to solve one problem: **two sessions editing the same physical folder at the same time will corrupt each other's work, and git branching alone does not fix that** (see "Why a bare branch-per-session doesn't work" below) — this repo's own working directory *is* the live Steam game install, which raises a couple of install-specific wrinkles a normal repo wouldn't have.

**Hard requirement: needs at least local git (repo mode C or better from `SKILL.md` Step 2).** If this checkout is in mode D ("no git at all"), none of this is available — there is no branch/worktree primitive without git, and no safe way to isolate two sessions' concurrent writes to the same files. If you're in mode D and want to run sessions concurrently, the only fix is revisiting Step 2 and moving to at least mode C (`git init`, no remote required) — see that step's own cost/benefit notes. Don't attempt any of the below without git.

## Why a bare branch-per-session doesn't work

A git branch is a property of a working directory, not of a session — only one branch can be checked out in `e:\...\Cube Chaos` at a time. If Session A does `git checkout -b session/A` and Session B (pointed at the exact same folder) later does `git checkout -b session/B`, that second checkout swaps every tracked file in the folder out from under Session A, mid-edit if Session A happens to be between tool calls at that moment. Branching by itself provides zero isolation when both sessions share one physical folder — it only helps once each session also gets **its own folder** (a git *worktree*), so their concurrent file writes physically can't collide.

## When this actually kicks in

**Not every session needs this.** A normal solo session should keep editing the main tree directly (`e:\...\Cube Chaos`) exactly like today — that's what keeps live edits visible in the user's already-open IDE tabs immediately, with zero extra ceremony. Switching to an isolated worktree means the user's IDE (pointed at the original folder) won't show any of this session's edits until they're merged back — a real cost, not just overhead, so it should only be paid when there's an actual concurrency signal:

- The user explicitly says they're about to run (or are already running) another session in parallel.
- `git worktree list` already shows another `session/*` worktree that hasn't been merged/removed yet (a sign another session is mid-flight right now).

Check `git worktree list` once at session start (Step 0.5/0.6 in `cube-chaos-orchestrator`'s SKILL.md handles this). If it's empty (or only shows the main worktree), just work directly in the main tree as normal — no branch, no worktree, nothing to set up. Only set up an isolated worktree if one of the two signals above is actually true.

## Setting up this session's isolated worktree

Branch name: `session/<yyyyMMdd-HHmmss>` (timestamp at setup time — unique per session, sorts chronologically). Worktree location: a **sibling** folder next to the game install, not nested inside it — `../CubeChaos-worktrees/<branch-name>` relative to the main `Cube Chaos` folder. Keeping it outside the Steam game folder itself avoids Steam's own file-integrity/update scans (which operate on the actual appid folder) ever seeing it.

```bash
# From the main repo root (e:\...\Cube Chaos):
ts=$(date +%Y%m%d-%H%M%S)
branch="session/$ts"
worktree="../CubeChaos-worktrees/$branch"
git worktree add -b "$branch" "$worktree" master
```

### Linking in the untracked engine files (needed to actually launch the game from the worktree)

This repo's `.gitignore` tracks only `.claude/`, `README.md`, `WORKFLOW_OVERVIEW.md`, `CLAUDE.md`, `.gitignore`, and this repo's own mod folders under `GameData/`. Everything else — the actual game engine — is real files sitting in the same folder, untracked. A fresh `git worktree add` checkout only contains the tracked files, so the game can't launch from it as-is. Confirmed root-level contents as of 2026-08-01 that need linking in (re-verify with `ls -a` if this drifts — Steam updates could add/rename files):

- `Cube Chaos.exe`, `Cube Chaos.jar`, `jre/` (the bundled JRE the exe launches), `GeneralData/` (fonts etc.), `ModdingInfo.txt`, `ModdingExplanation.txt`
- Inside `GameData/`: `Base_Core/`, `Characters/`, `Main/`, `Extra_Mechanics/`, `Modding_Example/` (the base-game packages — read-only reference material, see `CLAUDE.md`'s hard rule, so linking instead of copying is not just an optimization, it's the only way to guarantee they can never accidentally diverge across worktrees), plus `Loading_Order.txt` (the local mod-list file, itself untracked/machine-specific)

Use Windows directory **junctions** for folders (no admin rights needed, unlike symlinks) and a hardlink for individual files:

```bash
# Directories -> junction; files -> hardlink. Run from the main repo root.
for p in "Cube Chaos.exe" "Cube Chaos.jar" "jre" "GeneralData" "ModdingInfo.txt" "ModdingExplanation.txt"; do
  src="$(cygpath -w "$(pwd)/$p")"
  dst="$(cygpath -w "$(pwd)/$worktree/$p")"
  if [ -d "$p" ]; then cmd //c mklink //J "$dst" "$src"; else cmd //c mklink //H "$dst" "$src"; fi
done
for p in Base_Core Characters Main Extra_Mechanics Modding_Example; do
  cmd //c mklink //J "$(cygpath -w "$(pwd)/$worktree/GameData/$p")" "$(cygpath -w "$(pwd)/GameData/$p")"
done
cmd //c mklink //H "$(cygpath -w "$(pwd)/$worktree/GameData/Loading_Order.txt")" "$(cygpath -w "$(pwd)/GameData/Loading_Order.txt")"
```

This is a **documented procedure to run and verify, not a pre-tested one-liner** — confirm `mklink` syntax/quoting actually behaves as expected the first time this runs for real (Git Bash's MSYS path-mangling around `cmd //c` is the usual gotcha; the doubled slashes above are the standard workaround), and fix forward here if it doesn't.

**Once set up, all of this session's file tool calls (Read/Edit/Write/Bash) should target paths under `$worktree`, not the original folder**, for the rest of the session — say so plainly to the user (their IDE, still pointed at the original folder, won't show this session's edits live until merge-back).

## Working inside the session branch

Standing authorization from this point on (this is the user's own explicit override of the general "don't commit without being asked" default, 2026-08-01): **commit freely within this session's own branch** at natural checkpoints (each completed user-facing task/change), without asking each time. This authorization is scoped to committing on the session's own branch — the merge-back into `master` below still has its own gate, and none of the general Git Safety Protocol's other rules relax (still no force-push, no history rewriting, no `--no-verify`, still ask before pushing to a shared remote unless told otherwise).

## Merging back into `master`

Do this when the session's work is done, not continuously — a mid-task partial state has no business landing on `master`.

1. `git fetch` isn't needed for a same-machine worktree (it already shares the same `.git`) — just `git -C <worktree> merge master` (or rebase) to pull in whatever any other session already merged, resolving it inside the session branch first rather than surprising `master` with a conflict later.
2. **Any conflict touching a `*.c.txt`/`*.c.png`/sprite file stops here — hand it to the user rather than auto-resolving.** A clean textual git merge is not proof of correctness for this repo's DSL/sprite files specifically — `cube-chaos-sprite-art`'s own SKILL.md documents repeated real bugs where a textually-clean insertion (e.g. two sessions each appending a new `CUBE:`/`PERK:` block, or each claiming "the next free sprite slot") silently desyncs slot numbering with zero parse error. A prose-only conflict (README.md, a skill's own `.md` file) can be resolved directly if the resolution is unambiguous, but still mention it in the session's own wrap-up so the user can glance at it.
3. If this session touched any `CUBE:`/`PERK:` DSL content, confirm a clean test-launch + `Log.txt` check already happened this session (the existing mandatory gate — see `cube-chaos-mod-setup`) before merging.
   **Caveat found while designing this workflow: `%APPDATA%/CubeChaos/Log.txt` is a single global path, not per-worktree** — the engine doesn't know or care which worktree launched it. Two sessions test-launching at literally the same moment will interleave/overwrite each other's log output, with no worktree-based fix possible (junctioning can't help here, this is an OS-appdata path, not a project file). Practical rule: **serialize the actual test-launch step** across concurrent sessions — don't launch if another session might be mid-launch — and sanity-check that the log lines you're reading actually postdate *this* session's launch (a fresh, empty-then-repopulated log, or a timestamp/line-count check against a note taken right before launching) rather than assuming every line belongs to you.
4. Merge: `git checkout master && git merge --no-ff <branch>`.
5. Clean up: `git worktree remove <worktree>`, `git branch -d <branch>`.
6. **Pushing the merged `master` to `origin` is not automatically part of this** — ask, unless the user has separately said to push automatically too. Merging locally and pushing to a shared remote are different blast radii (the latter is visible to anyone else with access to that remote).
