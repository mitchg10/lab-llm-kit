# Admin guide

This guide is for whoever maintains the Mac Studio. Students need only `STUDENT_QUICKSTART.md`.

## Design in one paragraph

Everyone logs in to **one shared macOS account**. Every tool is installed through a manager:
- **Homebrew** for Ollama and LM Studio
- **nvm** for Node and the agent CLIs
- **uv** for Python and Python tools

So nobody hand-installs anything, and each tool can be updated with one command. All model weights live once under `/Users/Shared/lab-llm/models`, and LM Studio sees Ollama's and Hugging Face's weights through symlinks.

One constitution file and one skills folder are symlinked into Claude Code, Codex, Gemini CLI and OpenCode as agent context. You can turn that off with `LAB_AGENT_CONSTITUTION=off`. The short **default chat prompt** is only a default for general chat: the LM Studio preset, the `lab-*` Ollama models and `labllm chat`. API calls through `labllm` send only the researcher's own system and user prompts, but still block text that looks identifiable.

Research projects are **not** stored in the lab tree. Each lives in `/Users/Shared/research/<netid>/<project>` as its own git repo with its own uv environment, a pinned `labllm` version and a pre-commit safety hook.

Nothing listens on the network: Ollama is bound to `127.0.0.1` and LM Studio's server is local-only by default.

## Layout on the Mac

```
/Users/Shared/lab-llm/
  kit/            ← this repository (ideally a git checkout; lab-update pulls it)
  models/
    ollama/       ← OLLAMA_MODELS
    huggingface/  ← HF_HOME
    lmstudio/     ← ~/.lmstudio/models is a symlink to here
  skills-local/   ← experimental skills, not yet in the kit
  build/AGENTS.md ← generated: agent context + constitution (every agent's global instructions link here)
  logs/           ← ollama.log, labllm.jsonl (metadata only)
  backups/        ← anything lab-sync replaced

/Users/Shared/research/<netid>/<project>/   ← each project: its own git repo + uv env (lab new)
  .githooks/pre-commit   data/ (ignored)   outputs/ (ignored)   prompts/   notebooks/   uv.lock
```

Agent wiring:

| Agent | Global instructions | Skills | Model config |
|---|---|---|---|
| Claude Code | `~/.claude/CLAUDE.md` → build/AGENTS.md | `~/.claude/skills/*` → kit/skills | `claude-local`, `claude-cornell` wrappers (env vars) |
| Codex | `~/.codex/AGENTS.md` → build/AGENTS.md | `~/.agents/skills/*` | `~/.codex/config.toml` (default = local; profiles `lmstudio`, `cornell`) |
| Gemini CLI | `~/.gemini/GEMINI.md` → build/AGENTS.md | `~/.agents/skills/*` | Google models only (see below) |
| OpenCode | `~/.config/opencode/AGENTS.md` → build/AGENTS.md | `~/.agents/skills/*` | `~/.config/opencode/opencode.json` (providers ollama, lmstudio, cornell; sharing disabled) |
| Ollama API | `lab-*` chat variants carry DEFAULT_CHAT_PROMPT (overridden by any system message); plain models carry nothing | — | — |
| LM Studio app | set a preset by hand (below) | — | — |
| labllm | sends only the user's prompts; `labllm chat`/`ask` default to DEFAULT_CHAT_PROMPT | — | env vars in lab.env |

## Installing

1. **Prepare.** Update macOS and turn on FileVault. Create the shared account with admin rights for the duration of setup. Unzip or clone the kit into its home folder.
2. **Fill in `config/lab.env`.** In particular, set `CORNELL_AI_BASE_URL`: the gateway shows it when you create a key.
3. **Run `./install.sh`.** It runs `setup/01…05` in order. You can run individual steps with `./install.sh 03`. Every step is safe to re-run.
   - **01:** Xcode CLT, Homebrew, `/Users/Shared/lab-llm`, and a copy of the kit into it.
   - **02:** brew (ollama, lm-studio, git, jq); nvm → Node LTS → `opencode-ai`, `@anthropic-ai/claude-code`, `@openai/codex`, `@google/gemini-cli`; uv → Python 3.12, `hf`, `mlx-lm`, `labllm`.
   - **03:** the `~/.zshrc` hook, the Ollama LaunchAgent, the LM Studio folder link, and `lab-sync`.
   - **04:** pulls `config/models.txt` (about 170 GB; it asks first), builds the `lab-*` variants, and links them into LM Studio.
   - **05:** `lab-status`.
4. **Open LM Studio once.** Then run `./install.sh 03` again so the `lms` CLI is set up. In LM Studio, check **My Models → Models Directory**: it should resolve to the shared folder.
5. **Set the LM Studio preset by hand.** LM Studio can't be configured from a script. In **Chat → system prompt**, paste `constitution/DEFAULT_CHAT_PROMPT.md` and save it as a preset named "Lab constitution". Set it as the default for new chats. Users can still switch presets or write their own system prompt.
6. **Get `cornell-models.txt` right.** Run `lab-login` with your key, then `lab-models cornell`. Copy the model IDs you want into `config/cornell-models.txt`, with tags `agent` and `claude`. Then run `lab sync`.
7. **GitHub for projects.**
   - Create a lab GitHub org, or use an existing Cornell one, with private repos by default.
   - Set `LAB_GIT_REMOTE_BASE` in `lab.env`.
   - Push the kit there. Tag `labllm` releases (`git tag labllm-v0.2.0`) and set `LABLLM_SOURCE` to `labllm @ git+https://github.com/<org>/lab-llm-kit@labllm-v0.2.0#subdirectory=labllm`. New projects then pin that version and can be cloned to laptops. Without it, projects point at the kit's folder on this Mac.
   - `lab-sync` configures git for a shared account. It sets no global identity (`user.useConfigOnly`), so `lab-login` supplies each person's name. It stores no credentials: pushes use the `GH_TOKEN` loaded by `lab-login`, through `gh`.
8. **Optional hardening.** Demote the shared account to Standard after setup. Its tools all live in user space, so they keep working. Only LM Studio cask upgrades then need an admin.

**Recommended: put the kit in git.** Push `/Users/Shared/lab-llm/kit` to a private lab GitHub repo. Then changes to the constitution and skills go through pull requests, and `lab update` pulls them. Without git, copy the new version over `kit/` and run `lab sync`.

## Keeping it running

| Task | Command |
|---|---|
| Health check | `lab status` |
| Update everything (monthly) | `lab update`. This covers brew, the nvm LTS, agent CLIs, uv tools, the kit and a sync. |
| Changed the constitution or a skill | `lab sync` |
| New labllm release for projects | bump `labllm/pyproject.toml`, tag `labllm-vX.Y.Z`, update `LABLLM_SOURCE`. Existing projects keep their pinned version until they run `uv add "$LABLLM_SOURCE"`. |
| Add or remove standard models | edit `config/models.txt`, then `lab-models pull-list && lab-models make-lab-variants && lab-models link-lmstudio` |
| Restart Ollama | `launchctl kickstart -k gui/$(id -u)/edu.lab.ollama` |
| Change Ollama settings | edit `config/edu.lab.ollama.plist`, then `./install.sh 03` |
| Disk | `lab-models du` |

Semester checklist:
- Review the constitution with the PI.
- Prune `projects/` of finished work.
- Rotate out old models.
- Check that `cornell-models.txt` still matches the gateway.
- Skim `logs/labllm.jsonl` for usage.

## Security model and its limits

Be honest with the lab about what this setup does and doesn't guarantee.

- **Local only.** Ollama is bound to 127.0.0.1 through `OLLAMA_HOST`. Don't change it to `0.0.0.0` without talking to IT.
- **Shared account means no privacy between users.** Anyone who logs in can read everything, including other people's agent histories (`~/.claude`, `~/.codex/sessions`, `~/.gemini`, `~/.local/share/opencode`). This setup is acceptable **only because** no identifiable data is allowed on the machine. If that rule ever changes, move to per-person macOS accounts first. The kit already keeps shared state under `/Users/Shared`, so that move is straightforward.
- **Keys.** Cornell keys and GitHub tokens are entered per window with `lab-login` and are never written to disk. On a shared account, Keychain would expose them to everyone, so `lab-sync` turns off git's Keychain credential helper.
- **GitHub.** Project repos ignore `data/` and `outputs/`, notebook outputs are stripped, and the pre-commit hook blocks data files, large files and possible identifiers. The scan only runs where `labllm` is installed, so commits made on laptops have only the `.gitignore` protecting them.
- **The identifier scan is a safety net, not a guarantee.** It catches emails, IDs, phone numbers, dates, addresses, name-like speaker labels and names from a list. It can't catch indirect identifiers. The real control is the rule that de-identification happens before data reaches this machine.
- **Telemetry.** Claude Code and Gemini CLI telemetry are turned off, and OpenCode sharing is disabled. The `claude-local` wrapper turns off Claude Code's non-essential network traffic.
- **Gemini CLI** only talks to Google's models, which means a personal Google account or an API key. It gets the constitution and skills, but under the constitution it can't be used with research data unless Cornell covers that Google service. Say so to students.
- **Claude Code or Codex with personal accounts.** The same rule applies. Use `claude-local` or `claude-cornell`, and `codex` (local by default) or `codex --profile cornell`.

## Memory and performance (192–256 GB)

- By default macOS lets the GPU wire about 75% of RAM. To allow more until the next reboot: `sudo sysctl iogpu.wired_limit_mb=180000` (for a 192 GB machine, leaving about 12 GB for the system). To make it permanent you need a LaunchDaemon; ask before doing this.
- The Ollama settings are 64k context, 3 loaded models, 2 parallel requests each, a 30-minute keep-alive, flash attention and a q8 KV cache. If people run big batches at the same time, raise `OLLAMA_NUM_PARALLEL`. If models get evicted, lower `OLLAMA_MAX_LOADED_MODELS`.
- LM Studio and Ollama don't coordinate memory. If someone loads a 120B model in LM Studio while Ollama holds two others, something will be swapped out. `lab status` shows what Ollama has loaded.
- MLX models, served by LM Studio or `mlx_lm.server`, are usually 20–40% faster than GGUF on Apple Silicon. They are the ones to use for large batch jobs.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `lab: command not found` | Open a new terminal. If that doesn't help, check that `~/.zshrc` has the `lab-llm-kit` block (`./install.sh 03`). |
| Ollama not answering | Look at `logs/ollama.log`. Quit the Ollama menu-bar app if it's running, run `brew services stop ollama`, then `launchctl kickstart -k gui/$(id -u)/edu.lab.ollama`. |
| Model missing in LM Studio | `lab-models link-lmstudio`, then refresh in LM Studio. Check that `~/.lmstudio/models` is a symlink. |
| Agent doesn't see a skill | Run `lab sync` and check it doesn't print "skip …". The folder name must equal the `name:` in the frontmatter. Restart the agent. In Gemini CLI, use `/skills reload`. |
| OpenCode shows duplicate skills | Check that `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1` is set (lab.env). |
| Claude Code hangs on startup with a local model | Use `claude-local`, which sets `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`. Use a model with a context of at least 32k. |
| Codex can't call tools on a local model | Use `qwen3-coder:30b` or `gpt-oss:120b`. Small models handle tool calls poorly. |
| Cornell calls fail with 401 | Keys expire every 90 days. Make a new key and run `lab-login` again. |
| `Author identity unknown` on commit | Run `lab-login` in that window. This is deliberate: the shared account has no git identity. |
| Commit blocked by the hook | Read its output. Unstage data files. Add confirmed false positives to the project's `.labscan-allow`. See `VERSION_CONTROL.md`. |
| `lab-sync` says "Backed up …" | A file you or a student edited was replaced. The previous version is in `backups/<timestamp>/`. Make permanent changes in `kit/config/agents/`. |

## Things that need a decision (not decided by this kit)

- Whether transcribing **raw interview audio** locally (for example with Whisper through `mlx-whisper`) is ever allowed. Under the current "no identifiers anywhere" rule it is **not**, because audio counts as identifiable.
- Whether the lab's IRB protocols need amendments that mention local LLM processing.
- Who can approve changes to the constitution. The table at its end is where approvals are recorded.
