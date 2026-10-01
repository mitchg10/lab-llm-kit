---
name: research-version-control
description: Help researchers put analysis projects under git from the start, and keep them there safely. This covers creating a project repo, committing, writing messages, pushing to the lab's private GitHub org, tagging the versions behind reported results, undoing mistakes, and handling the lab's pre-commit safety hook. Use when a user mentions git, GitHub, commits, versions, backups, "save my work", reverting changes, collaborating on a project, or a blocked commit.
---

# Version control for lab research projects

Many users are new to git, so explain each step in plain language before running it. Show the command you ran, and keep it to one or two commands at a time.

## The lab setup, which you should rely on

- Each project is **its own repo** under `$LAB_PROJECTS/<netid>/<project>`, outside the lab tools. `lab new <name>` creates one. `lab init` adopts the current folder.
- **Committed:** code, `prompts/`, codebooks, notebooks (outputs are stripped automatically), `README.md`, `pyproject.toml` and `uv.lock`.
- **Never committed:** `data/`, `outputs/`, keys, recordings and documents. The `.gitignore` and the `.githooks/pre-commit` hook enforce this.
- **Identity on the shared account:** there is no global git user. `lab-login` sets the name and email for the current window. The error `Author identity unknown` means the user hasn't run `lab-login` in this window.
- **Credentials are never stored.** `lab-login` can load a GitHub token for the window, and git and `gh` use it.

## Everyday loop

```bash
git status                         # what changed?
git add prompts/system_coding_v2.md analysis.py
git commit -m "Codebook v2: split TRUST_CONCERN into output vs. self-understanding"
git push                           # if the repo has a remote
```

Good messages say *what changed and why*, in words the user will understand in six months. Commit after each meaningful step, such as a new prompt version, a working script or a finished analysis pass.

## Connecting to GitHub

The repos are private, in the lab org (`$LAB_GIT_REMOTE_BASE`):
- New project: `lab new <name> --github`.
- Existing project: in the project folder, run `lab init --github`.
- Or create an empty private repo on the website, then `lab init --remote <url>`.
- Needs a GitHub token loaded with `lab-login`. It's a fine-grained token with *Contents: read/write* on the lab org's repos.
- On a laptop: `git clone <url>`, then `uv sync`. The hook's identifier scan only runs where `labllm` is installed, so be extra careful committing from elsewhere.

## Versions behind reported results

Before a run that might end up in a paper, commit everything, then tag it:
```bash
git tag -a coding-pass-1 -m "Full coding run: qwen3:30b digest abc123…, temp 0, seed 42"
git push --tags
```
Record the tag or commit hash in the README methods log, next to the model digest and the prompt files. Never edit a prompt that produced reported results. Copy it to `_v2` and commit it.

## Undoing things (explain the difference first)

| Situation | Command |
|---|---|
| Discard uncommitted edits to one file | `git restore <file>` |
| Unstage a file (keep the edits) | `git restore --staged <file>` |
| Fix the last commit message (not yet pushed) | `git commit --amend` |
| Undo a pushed commit safely | `git revert <hash>` |
| See an old version | `git log --oneline`, then `git show <hash>:<file>` |
| Try something risky | `git switch -c experiment` … and later `git switch main` |

Avoid `reset --hard` and force-push unless the user understands that they destroy history. **If identifiable data was ever committed,** stop and follow constitution §8: tell the PI. Removing it from history, and from GitHub if it was pushed, needs to happen under their direction.

## When the pre-commit hook blocks a commit

Read its output with the user.
- **Data or recordings staged:** unstage them with `git restore --staged <file>`. They belong in `data/` or on protocol storage.
- **Possible identifiers:** open the file at the line shown. If it really is an identifier, remove it and tell the user. If it's a false positive, such as a pseudonym or a researcher's own NetID, and the user confirms that, add the exact term to `.labscan-allow` and commit again.
- **Never suggest `--no-verify` as a routine fix.** It's only for a confirmed false positive that can't be allow-listed, and the user has to make that call.

## Collaborating

- Each person runs `lab-login` in their own window, so commits are attributed correctly even on the shared account.
- For shared projects, each person works on a branch (`git switch -c <netid>/<topic>`) and merges through a pull request on GitHub. Reviewers check the prompts and code, never the data.
