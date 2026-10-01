# Lab LLM Kit: self-hosted models on the lab Mac Studio

This kit sets up a Mac Studio so that grad students and postdocs can log in and use local LLMs, the Cornell AI Gateway and coding agents. All of these share one model store, one set of skills and one lab constitution. The Mac doesn't act as a network server: everything is bound to `127.0.0.1`.

The design rests on two principles:
- **Prompts belong to the researcher.** API calls send only the system and user prompts you write. The lab's default chat prompt applies only to general chat, as a default you can replace.
- **Projects live outside the tooling.** Each project is its own git repo under `/Users/Shared/research/<netid>/`, with its own uv environment and a safety hook.

```
     lab constitution → agent context        default chat prompt → LM Studio preset, lab-* models, `labllm chat`
                         │                     (API calls: only YOUR system + user prompts)
  Claude Code ─┐   OpenCode ─┐   Codex ─┐   Gemini CLI       labllm (Python/CLI)
               │             │          │                         │
               ├── local ────┴──────────┴──► Ollama :11434 ◄───────┤
               │                            LM Studio :1234 ◄──────┤
               └── cornell ────────────────► Cornell AI Gateway ◄──┘   (your key for the project's team, lab-key)

  /Users/Shared/lab-llm/   tools: models (stored once; LM Studio sees them via symlinks),
                           kit, skills (linked into every agent), logs
  /Users/Shared/research/  projects: <netid>/<project>/, each its own git repo + uv env
```

## What's in the box

| Path | What it is |
|---|---|
| `install.sh`, `setup/` | Idempotent installer: Homebrew → Ollama + LM Studio; **nvm** → Node → OpenCode, Claude Code, Codex, Gemini CLI; **uv** → Python, `hf`, `mlx-lm`, `labllm` |
| `constitution/` | `LAB_CONSTITUTION.md` (full rules for people and agents) and `DEFAULT_CHAT_PROMPT.md` (default system prompt for general chat only) |
| `config/` | `lab.env` (all paths and settings), the Ollama LaunchAgent, `models.txt` (the standard model set), `cornell-models.txt`, and agent config templates |
| `bin/` | `lab` (menu), `lab-login`, `lab-key`, `lab new` / `lab init` (project repos), `lab-scan`, `lab-models`, `lab-sync`, `lab-status`, `lab-update`, `claude-local`, `claude-cornell` |
| `config/project-template/`, `config/git-hooks/` | What every new project gets: .gitignore, README with a methods log, AGENTS.md, and the pre-commit safety hook |
| `labllm/` | Small Python library and CLI. It works the same across Ollama, LM Studio and Cornell, sends your prompts unchanged, blocks identifiers and logs metadata. |
| `skills/` | Cross-agent skills: data privacy, API use, model management, reproducibility, qualitative coding, version control, plus a template |
| `docs/` | `ADMIN_GUIDE.md`, `STUDENT_QUICKSTART.md`, `VERSION_CONTROL.md`, `SKILLS_GUIDE.md` |
| `examples/`, `tests/` | A quickstart script, a coding prompt and schema, synthetic practice data, and tests |

## Install (admin, about 30 minutes plus model downloads)

1. Copy the site values into `config/lab.local.env` (gitignored; it overrides `config/lab.env`): the lab name, the PI, `CORNELL_AI_BASE_URL`, and the lab's GitHub org (`LAB_GIT_REMOTE_BASE`, `LABLLM_SOURCE`).
2. Log in to the Mac as the shared lab account. It needs admin rights for this step.
3. Run:
   ```bash
   cd lab-llm-kit && ./install.sh
   ```
4. Open LM Studio once, then run `./install.sh 03`. This enables the `lms` CLI.
5. Open a new terminal and run `lab status`.

Details, the security model and troubleshooting are in **[docs/ADMIN_GUIDE.md](docs/ADMIN_GUIDE.md)**. Students start with **[docs/STUDENT_QUICKSTART.md](docs/STUDENT_QUICKSTART.md)**.

## Before first use: fill in the placeholders

Search the kit for `[`:
```bash
grep -rn '\[[A-Z]' config constitution
```
The placeholders are the lab and PI names, the Cornell gateway URL, the GitHub org, the IRB contact, the constitution approval date, and `cornell-models.txt`.

The PI should read and approve `constitution/LAB_CONSTITUTION.md` before anyone uses the machine.
