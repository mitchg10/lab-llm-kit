---
name: local-llm-api
description: Call the lab's language models from code or the command line. This covers local Ollama and LM Studio and the Cornell AI Gateway, through the labllm library, the OpenAI SDK or curl, with the user's own system and user prompts. Use when a user wants to query a model from a script or notebook, set a system prompt, run a prompt over many rows, get JSON or structured output, make embeddings, or switch between local and Cornell models.
---

# Calling the lab's models

Every backend speaks the **OpenAI-compatible API**, so code written for one works on the others once you change the model string.

| Backend | Base URL | Key | Model string in `labllm` |
|---|---|---|---|
| Ollama (default) | `http://127.0.0.1:11434/v1` | any value | `qwen3:30b` |
| LM Studio (server must be started) | `http://127.0.0.1:1234/v1` | any value | `lmstudio:<id from lms ls>` |
| Cornell AI Gateway | `$CORNELL_AI_BASE_URL` | `$CORNELL_AI_API_KEY` (set with `lab-login`) | `cornell:<gateway id>` |

## Prompts belong to the user

- **Through the API** (`labllm` in Python, `labllm batch`, the OpenAI SDK, curl), **only the system and user prompts the user writes are sent.** Nothing is added.
- The lab's **default chat prompt** (`$LAB_DEFAULT_CHAT_PROMPT`) is only for general chat. It's used by LM Studio's preset, `labllm chat`/`ask` when no `--system` is given, and the `lab-*` Ollama models, where it is a default that any system message replaces. In Python, you can opt in with `system=DEFAULT`.
- For analysis, use the **plain** models (`qwen3:30b`, not `lab-qwen3:30b`). Otherwise a missing system prompt silently falls back to the chat default.
- Keep prompts in files in the project's `prompts/` folder, for example `system_coding.md` and `code_excerpt.md`, so they're versioned in git and citable in methods.

What `labllm` **does** add:
- It scans all message text for identifiers, and refuses to send if it finds any.
- It uses reproducible defaults (temperature 0, seed 42 on local models). You can override both.
- It writes one line of metadata to the log, never content.

## Python (in a project made with `lab new`)

```python
from pathlib import Path
from labllm import LabLLM, DEFAULT

llm = LabLLM("qwen3:30b", system="prompts/system_coding.md")      # client-wide system prompt (text or file)
r = llm.chat(Path("prompts/code_excerpt.md").read_text().format(speaker="P03", text=excerpt))
r.text, r.usage, r.seconds

llm.chat("…", system="A different system prompt for this one call.")
llm.chat(messages=[                                                # full control: few-shot, multi-turn
    {"role": "system", "content": "…"},
    {"role": "user", "content": "example input"}, {"role": "assistant", "content": "example output"},
    {"role": "user", "content": "real input"},
])
llm.chat("…", temperature=0.7, seed=3, top_p=0.9, stop=["\n\n"])   # any OpenAI parameter passes through

schema = {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"],
          "additionalProperties": False}
llm.chat("…", json_schema=schema).json()                           # structured output

LabLLM("qwen3:30b", save_to="outputs/calls.jsonl")                 # full prompt/response record (git-ignored)
LabLLM(system=DEFAULT).chat("…")                                   # opt in to the lab's chat prompt
llm.embed(["text one", "text two"])                                # $LAB_EMBED_MODEL
LabLLM("cornell:<gateway-model-id>", system="…").chat("…")         # after lab-login
```

## Command line

```bash
labllm chat -m qwen3:30b                          # terminal chat (lab default prompt; --system/--no-system to change)
labllm ask "Summarize this" -f excerpt.txt -s prompts/system.md
labllm batch data/excerpts.csv --text-col text \
       --system prompts/system_coding.md --prompt prompts/code_excerpt.md \
       --schema prompts/schema.json --out outputs/coded.csv --save-to outputs/calls.jsonl
```

In `batch`:
- `--prompt` is the **user** template. Use `{text}`, and any other `{column}` from the CSV.
- `--system` is optional. If it's left out, no system prompt is sent.
- Re-running the same command resumes where it left off.
- Rows with possible identifiers aren't sent, and are marked `NOT SENT` in the output.

## Plain OpenAI SDK or curl

These work, but there's no identifier scan, so run `lab-scan` on inputs first.
```python
from openai import OpenAI
client = OpenAI(base_url="http://127.0.0.1:11434/v1", api_key="ollama")
client.chat.completions.create(model="qwen3:30b", messages=[{"role": "system", "content": "…"},
                                                             {"role": "user", "content": "…"}])
```
```bash
curl http://127.0.0.1:11434/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"model":"qwen3:30b","messages":[{"role":"user","content":"hi"}]}'
```

## Choosing a model

- **Default for analysis:** `qwen3:30b`. It's fast and good.
- **Harder judgement calls:** `gpt-oss:120b`.
- **Replicating published work:** `llama3.3:70b`.
- **Images:** `gemma3:27b`.
- **Agents and code:** `qwen3-coder:30b`.
- **Embeddings:** `nomic-embed-text`, or `qwen3-embedding:8b` for higher quality.
- **Cornell frontier models:** useful for quality comparisons on data that is already de-identified.

## Troubleshooting

- *Connection refused on 11434:* run `lab status`.
- *Model not found:* run `lab-models list`, then `lab-models pull ollama <name>`.
- *First call is slow:* the model is loading into memory. Later calls are fast for 30 minutes.
- *Long inputs are cut off:* context is 64k tokens, so chunk long documents.
- *`KeyError` in batch:* the prompt template uses a `{name}` that isn't a CSV column. To write a literal brace, double it: `{{ }}`.
