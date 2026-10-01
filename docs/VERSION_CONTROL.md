# Version control for lab projects

Git keeps every saved version of your project, so you can see what changed, undo mistakes and show exactly which prompts and code produced a result. Every project made with `lab new` is a git repository from its first minute.

## Why projects live outside the lab tools

```
/Users/Shared/lab-llm/          ← the lab's tools: models, kit, skills (admins maintain this)
/Users/Shared/research/<netid>/ ← your projects; each one is its own repo, with its own environment
```

Keeping them apart has three benefits:
- The lab tools don't grow as projects pile up.
- Each project can be pushed, shared, cloned to a laptop or archived on its own.
- Each project pins its own `labllm` version in `uv.lock`, so updating the lab tools can't silently change an old analysis.

## What goes in git, and what never does

| In git ✓ | Never in git ✗ |
|---|---|
| code, notebooks (outputs are stripped automatically) | `data/` (even de-identified data) |
| `prompts/` (system prompts and user templates), codebooks, schemas | `outputs/` (model responses, call logs) |
| `README.md` with the methods log | keys, tokens, `.env` files |
| `pyproject.toml`, `uv.lock` | recordings, .docx, .xlsx and PDF documents |

Three things enforce this:
- `.gitignore`
- a **pre-commit safety hook** that blocks data files, files over 5 MB, and text that looks like identifiers
- the rule in the constitution: GitHub is an external service, so only code, prompts and documentation go there

## First-time setup (once per session)

`lab-login` sets your name and email for git in that window. The shared account deliberately has no git identity, so commits can't be misattributed. If you see `Author identity unknown`, run `lab-login`.

To push to GitHub you also need a **GitHub token**:
1. Go to GitHub → Settings → Developer settings → Fine-grained tokens.
2. Give it access to the lab org's repos, with *Contents: read and write*.
3. Paste it when `lab-login` asks.

It's kept only in that window. Nothing is stored on the shared Mac.

## Daily commands

```bash
git status                           # what's changed?
git diff                             # the exact changes
git add prompts/system_coding_v2.md  # choose what to save (or: git add -A for everything allowed)
git commit -m "Codebook v2: split TRUST_CONCERN"
git push                             # send to GitHub (if connected)
git log --oneline                    # history
```

Commit whenever you finish a meaningful step. Write messages your future self will understand.

## Connecting a project to GitHub

- New project: `lab new my-study --github`. This creates a private repo in the lab org and pushes to it.
- Existing project: run `lab init --github` in its folder.
- Or create an empty **private** repo on github.com, then run `lab init --remote https://github.com/<org>/<repo>.git`.

## Tag the versions behind your results

Before a run you might report:
```bash
git add -A && git commit -m "Prompts and script for coding pass 1"
git tag -a coding-pass-1 -m "qwen3:30b (digest …), temp 0, seed 42"
git push --tags
```
Write the tag in your README methods log. Once a prompt has produced results you report, never edit it. Copy it to `_v2`.

## Undo cheatsheet

| I want to… | Command |
|---|---|
| throw away uncommitted edits to a file | `git restore <file>` |
| unstage a file but keep my edits | `git restore --staged <file>` |
| fix the message of my last commit (not pushed yet) | `git commit --amend` |
| undo a commit I already pushed | `git revert <hash>` |
| look at an old version of a file | `git show <hash>:<file>` |
| experiment without risk | `git switch -c try-something`, then `git switch main` to go back |

If you're unsure, ask an agent: *"use the research-version-control skill and help me undo …"*. It will explain before it acts.

## When the safety hook blocks your commit

It tells you which file and line. Then:
- **Data file or recording:** `git restore --staged <file>`. It stays in `data/` and isn't committed.
- **Real identifier:** remove it from the file. If identifying data was *already* committed or pushed, stop and tell the PI (constitution §8).
- **False positive,** such as a pseudonym, a course code or your own NetID: add the exact term to `.labscan-allow` in the project, and commit again.

Don't use `git commit --no-verify` to get around the hook.

## Working on a laptop too

```bash
git clone https://github.com/<org>/<repo>.git
cd <repo> && uv sync          # recreates the environment from uv.lock
```
If `labllm` came from the lab Mac's local copy, set `LABLLM_SOURCE` to the lab's git URL first (ask the admin). Off the Mac, the hook can't run the identifier scan, so be careful. Data never goes to your laptop unless your protocol allows it.

## Collaborating

- Everyone runs `lab-login` in their own window.
- Work on a branch (`git switch -c <netid>/<topic>`), push it, and open a pull request on GitHub.
- Reviewers read prompts and code, never data.
