# Quickstart: using AI models on the lab Mac

This guide takes about 10 minutes. You don't need to install anything, because it's all set up already.

## 0. The one rule

**Never give any AI model data that could identify a person.** That includes local models on this Mac and the Cornell gateway. Identifying data covers:
- names, emails, NetIDs and student IDs
- grades linked to a person
- exact dates, locations and recordings
- details that single someone out, such as "the only woman in section 2"

Only data that has been de-identified under your IRB protocol comes to this machine. If something goes wrong, tell the PI the same day. The full rules are in `$LAB_KIT/constitution/LAB_CONSTITUTION.md`, and you should read them once.

Everyone shares this Mac account, so **everyone can see your files and chat histories.** Keep that in mind.

## 1. Start a session

Open **Terminal** and type:
```
lab-login
```
It asks for:
- your NetID
- your name and email, so your git commits are yours and not the shared account's
- optionally, your Cornell gateway key and a GitHub token

These only last for that one window, and nothing is saved. Type `lab` any time to see the menu.

## 2. Make a project (its own git repo)

```
lab new my-study              # or: lab new my-study --github   (also creates a private repo in the lab org)
cd /Users/Shared/research/<netid>/my-study
```
This gives you a project that is separate from the lab's tools:
- a Python environment (uv) with `labllm`, pandas and Jupyter
- starter prompts in `prompts/`
- a git repo with its first commit already made

The `data/` and `outputs/` folders are **never** committed. A safety check blocks commits that contain identifiers, data files or recordings.

Save a version whenever you reach a meaningful step:
```
git add -A
git commit -m "Codebook v2: clearer TRUST_CONCERN definition"
git push        # if you connected GitHub
```
Git is new to a lot of people, so there's help in **[VERSION_CONTROL.md](VERSION_CONTROL.md)**. You can also ask any agent to "use the research-version-control skill".

## 3. Check your data

```
lab scan data/my_excerpts.csv
```
A green ✓ means the automatic check found nothing. You still need to read the data yourself for details that could single someone out. A red ✗ lists line numbers to fix at the source.

## 4. Pick how you want to work

**Chat app.** Open **LM Studio**. It uses the lab's default chat prompt (the "Lab constitution" preset). You can replace that with your own system prompt at any time.

**Your own prompts, through the API.** This is the normal way to do analysis. Only the system and user prompts you write are sent; nothing is added. Keep them as files in `prompts/` so they're versioned:
```python
from pathlib import Path
from labllm import LabLLM

llm = LabLLM("qwen3:30b", system="prompts/system_coding.md", save_to="outputs/calls.jsonl")
user = Path("prompts/code_excerpt.md").read_text().format(speaker="P03", text="…excerpt…")
print(llm.chat(user).text)
```
Run it with `uv run my_script.py`, or open `uv run jupyter lab`. Need a package? Use `uv add <package>`, never `pip install`.

**A whole spreadsheet of excerpts:**
```
labllm batch data/excerpts.csv --text-col text \
       --system prompts/system_coding.md --prompt prompts/code_excerpt.md \
       --schema prompts/schema.json --out outputs/coded.csv --save-to outputs/calls.jsonl
```

**Terminal chat:** `labllm chat`. It uses the lab default prompt; pass `--system my_prompt.md` or `--no-system` to change that.

**AI agents.** These can read files, write code, run analyses and help with git. Run them from inside your project folder:
```
opencode            # choose a model with /models: "Ollama (this Mac)" or "Cornell AI Gateway"
claude-local        # Claude Code on a local model
claude-cornell      # Claude Code via the Cornell gateway (after lab-login)
codex               # Codex on a local model;  codex --profile cornell  for the gateway
```

## 5. Which model?

| Model | Use for |
|---|---|
| `qwen3:30b` | the default for analysis: fast and good |
| `gpt-oss:120b` | harder judgement calls (slower) |
| `llama3.3:70b` | when you want to match published methods |
| `gemma3:27b` | when your input includes images |
| `qwen3-coder:30b` | agents and code |
| `lab-…` versions (e.g. `lab-qwen3:30b`) | general chat: the same model with the lab's default chat prompt. Don't use these for analysis. |
| `cornell:<model>` | frontier models via the gateway, for de-identified data only |

## 6. For your methods section

Record:
- the model and its digest (`ollama show <model>`)
- the temperature and seed
- the **exact prompt files**
- the git commit or tag you ran

`labllm` logs the model details automatically, and the `reproducible-llm-analysis` skill has a write-up template. When your project ends, delete `data/` and `outputs/` here. The repo on GitHub keeps your code and prompts.

**Stuck?** Run `lab status` and send the output to [admin contact].
