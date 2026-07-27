---
name: cube-chaos-repo-setup
description: First-run session bootstrap for a Cube Chaos modding repo on a machine that hasn't been set up yet - decides how git/GitHub should work (your own fork, a branch on a shared repo, local-only git, or no git at all), checks that the tools every other skill assumes (git, python3+Pillow, bash, optionally gh/jq) are actually present, and runs a one-time personal-preferences questionnaire (preview-gate strictness, sprite effort, naming/color check-ins, README timing, proactive write-back, test-launch behavior) into a gitignored `.claude/preferences.local.md`. Trigger on "set up this repo", "new device", "new machine", "I'm new here", "fork this", "work on a branch", "work without git", "no git", "change my preferences", or whenever `cube-chaos-orchestrator`'s Step 0.5 detects `.claude/preferences.local.md` doesn't exist yet.
---

# Cube Chaos repo & session setup

This is a *process* skill, not a DSL/art/balancing one — it exists so a session on a brand-new machine (a stranger cloning this repo, or the repo owner on a second device) doesn't silently inherit the previous machine's git assumptions, missing tools, or one person's working-style preferences as if they were universal defaults. Run it once per machine/checkout; re-run only if the user explicitly wants to change git mode or preferences later.

## Research protocol

Ground truth here is **what's actually on this machine right now**, never an assumption carried over from another session or another skill's memory. Check by running the actual command (`git remote -v`, `python3 -c "import PIL"`, etc.), not by asking the user to self-report or by trusting what a previous machine had. If this skill doesn't cover a tool/path question that comes up, the fallback is the same as every other domain skill: figure it out empirically, then write the finding back into this file (which command, which platform quirk, what the fix was) so the next machine's setup is faster.

## Step 1 — detect current state

Run these and summarize the results as a short checklist, not raw command dumps:

- `git rev-parse --is-inside-work-tree` (and if yes, `git remote -v`, `git status --porcelain`, `git branch --show-current`) — is there a repo at all, does it have a remote, is it clean, what branch.
- Does `.claude/preferences.local.md` already exist? If yes, this machine/checkout has already been through this skill — read it back, tell the user what's currently set, and ask only whether they want to change anything (skip straight to Step 4, offer the option to also revisit Steps 2-3 if they mention a new machine or missing tool).
- Tool availability: `git --version`, `python3 --version`, `python3 -c "import PIL; print(PIL.__version__)"`, `bash --version` (or confirm the current shell tool already *is* bash/PowerShell-with-git-bash-available), `gh --version` (optional), `jq --version` (optional).
- Confirm the working directory looks like the actual game root (`GameData/`, `ModdingInfo.txt`, `Cube Chaos.exe` present) — this duplicates orchestrator Step 0's own check; if Step 0 already ran this session, don't re-ask, just note it.

## Step 2 — choose a repo mode

Skip this step entirely if git is already configured the way the user wants (e.g. the repo owner's own machine, already cloned with the right remote) — confirm in one sentence and move on rather than forcing the question. Otherwise ask via `AskUserQuestion`, one question, these options:

1. **Fork & go independent (Recommended for a new contributor or a stranger)** — your own GitHub repo, decoupled from anyone else's. Best if you want to build your own mods and don't need to send changes back.
2. **Branch on an existing shared repo** — only real if you already have push/collaborator access to that repo (e.g. the repo owner setting up a second machine). Never commit straight to its default branch.
3. **Local git, no GitHub remote** — full commit history and all safety-net hooks work identically to a repo with a remote; you just don't have a cloud backup or a way to share commits yet. Can add a remote later at any time.
4. **No git at all** — fastest to start, but see the cost below before picking this.

### A) Fork & go independent

- If `gh` is available and authenticated (`gh auth status`): `gh repo create <name> --private --source=. --remote=origin --push` (or `--public` if they want it visible). If they cloned the original repo directly and want to keep pulling future skill improvements from it, rename the old remote first: `git remote rename origin upstream`.
- If `gh` isn't available (or isn't authenticated): create an empty repo on github.com manually, then `git remote add origin <url>` (or `git remote set-url origin <url>` if one already points at the wrong place), `git push -u origin <branch>`.
- Ask for the repo name/visibility via `AskUserQuestion` only if it isn't obvious from context (e.g. the user already named their fork).

### B) Branch on an existing shared repo

- `git fetch origin`, `git checkout -b <branch-name> origin/<default-branch>`.
- Never push directly to the shared default branch — open a PR (`gh pr create` if `gh` is set up, otherwise the GitHub web UI) once the branch is ready.
- **If the user doesn't actually have push access to that repo** (the common case for "a stranger" rather than the owner on a second machine), this mode isn't real for them — steer to mode A instead. `gh repo fork <owner>/<repo> --clone` is the simplest single-command path for that case (creates the fork, sets `origin` to the fork and `upstream` to the original, in one step) — mention it as a shortcut over the manual remote-juggling in mode A if `gh` is available.

### C) Local git, no remote

- If no repo yet: `git init`, then a first commit of the current tree.
- Nothing else needed — every hook that reads `git status`/`git diff` (see the cost note below) works fully off local working-tree state; a remote is not involved in any hook.

### D) No git at all

**Cost, stated plainly before finalizing this choice:** three of the five hooks wired up in `.claude/settings.json` (`check-launch-log.sh`, `check-sprite-coverage.sh`, `check-workflow-overview.sh`) key entirely off `git status --porcelain`/`git diff` to figure out what changed this session. Without a repo those commands fail, the scripts' own `|| true` swallows the error, and the hook silently no-ops forever — not an error, just a permanently-quiet safety net. The other two hooks (`check-md-dsl-safety.sh`, the blocking one; `regen-preview-cards.sh`) work entirely off the single file just written/edited and need no git at all, so those keep working regardless.

If the user's actual goal is just "don't make me deal with a *remote*" rather than "no history at all," steer them to mode C instead — `git init` with no remote costs nothing, loses nothing, and keeps all five hooks live. Only pick D if they genuinely don't want local version control either (e.g. a very short-lived experiment).

## Step 3 — tool/path preflight

| Tool/path | Needed for | If missing |
|---|---|---|
| `git` | Modes A/B/C (any git-backed mode); the three git-dependent hooks | Required for anything but mode D. Install via the platform's normal git installer. |
| `python3` + Pillow (`python3 -c "import PIL"`) | `regen-preview-cards.sh` hook, `render_preview_cards.py`, every sprite-generation script under `cube-chaos-sprite-art/scripts/` | If `python3` exists but `import PIL` fails: `pip install Pillow`. If `python3` itself is missing, install it first — nothing in this skill set has a non-Python sprite path. |
| `bash` | Every hook in `.claude/settings.json` is declared `"shell": "bash"` | On Windows this means Git Bash (ships with Git for Windows) must be installed and reachable — a plain `git` install without Git Bash won't provide it. Confirm with `bash --version`. |
| `gh` (GitHub CLI) | Smooths repo-mode A/B's remote-creation steps only | Optional — every git-mode step above has a manual (github.com web UI) fallback spelled out. |
| `jq` | Hook scripts use it to build their `systemMessage` JSON if present | Optional — every hook has a `sed`-based fallback when `jq` is absent (see any hook's `if command -v jq` branch); nothing breaks without it, messages are just built less robustly. |
| Game root (`GameData/`, `ModdingInfo.txt`, `Cube Chaos.exe`) | Every path in every skill is relative to this | Delegated to `cube-chaos-orchestrator` Step 0 — don't duplicate that check here if it already ran this session. |
| `%APPDATA%/CubeChaos/Log.txt` | The launch-and-check-log loop (`cube-chaos-mod-setup`) | Fine if it doesn't exist yet — it's created by the game's first-ever launch, not by setup. Only a problem if it's still missing *after* a real test launch. |

## Step 4 — personal preferences questionnaire

These are working-style preferences, not correctness rules — the sprite-art skill's "never ship flat single-color icons" or the DSL gotchas in `cube-chaos-scripting` are hard rules that apply to everyone regardless of taste, and stay exactly as strict as written elsewhere. What's below is genuinely a matter of how a given user likes to collaborate, so it lives in a **personal, gitignored file**, `.claude/preferences.local.md` — same treatment as `.claude/settings.local.json` (see `CLAUDE.md`'s "no personal data" rule): every contributor keeps their own, nobody's personal taste gets forced on anyone else who works from this same shared repo.

If `.claude/preferences.local.md` already exists (checked in Step 1), read it back to the user and ask only what they'd like to change, rather than re-running the full questionnaire.

Ask via `AskUserQuestion` (batch across as many calls as needed, max 4 questions per call). The "Recommended" option in each is the default this skill set has been built and tested around — presented first, but never auto-picked without the user seeing and confirming it:

1. **Preview-and-approve gate** — "Always show the full design spec (ability, numbers, derived rule text) and wait for an explicit OK before writing any new/edited cube or perk (Recommended)" vs. "Just implement it and show me the result after."
2. **Naming/color check-ins** — "Always ask before inventing a new perk/cube name or a new class/mod color (Recommended)" vs. "Use your own judgment and pick something reasonable."
3. **Sprite art effort** — "Full multi-pass shaded pixel art (base + outline + highlight + accent), verified by reading the rendered PNG back before calling it done (Recommended)" vs. "Quick single-pass placeholder icons — I'll refine the art myself."
4. **README timing** — "Create a mod's README only when asked, or when a session's work has clearly reached a feature-complete point — ask first even then (Recommended)" vs. "Set one up right away when a mod is created."
5. **Proactive write-back** — "After finishing a task to my satisfaction, write learnings back into the relevant skill/memory unprompted (Recommended)" vs. "Only write things back when I explicitly ask."
6. **Test-launch behavior** — "Leave the game running after a clean `Log.txt` check so I can pick up manual testing right away (Recommended)" vs. "Close the game automatically once the check passes."

Write the answers to `.claude/preferences.local.md`:

```markdown
# Personal Cube Chaos session preferences (local, gitignored — not shared)

- preview_gate: on | off
- ask_before_naming_colors: on | off
- sprite_effort: full | placeholder
- readme_timing: late-ask-first | early
- proactive_writeback: on | off
- test_launch_behavior: leave-running | auto-close
```

## Reference: where each preference is actually consulted

| Preference | Consumed by |
|---|---|
| `preview_gate` | `cube-chaos-orchestrator` Step C (the design-preview gate) |
| `ask_before_naming_colors` | `cube-chaos-orchestrator` Step C item 3; `cube-chaos-sprite-art` (new class/mod colors) |
| `sprite_effort` | `cube-chaos-sprite-art` |
| `readme_timing` | `cube-chaos-mod-setup`'s README/`Preview/` governance section |
| `proactive_writeback` | `cube-chaos-orchestrator` Step D (the write-back-always rule) |
| `test_launch_behavior` | `cube-chaos-mod-setup`'s test-and-iterate loop |

**If `.claude/preferences.local.md` doesn't exist for whatever reason (a quick drive-by session that skipped setup), every skill above defaults to the "Recommended" option in Step 4** — the questionnaire is how a user *changes* the default, not a prerequisite for sane behavior.

## Step 5 — wrap-up

- Confirm `.claude/preferences.local.md` is covered by `.gitignore` (it already is, alongside `settings.local.json`, as of this skill's own setup — don't re-add it if already listed).
- Hand back to `cube-chaos-orchestrator` to continue with whatever content task the user actually came here for.
