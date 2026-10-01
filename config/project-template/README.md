# __NAME__

Owner: __OWNER__ · Created: __DATE__ · IRB protocol: [number] · Status: active

## What this project is
[One paragraph: research question, data, what the models are used for.]

## Data (not in git)
- Raw data lives at: [protocol-approved location]. Never on this Mac.
- De-identified working copy: `data/` (git-ignored). De-identified by [who], [how], on [date].
- `lab scan data/*` last run: [date, result]

## How to run
```bash
uv sync                      # recreate the environment from uv.lock
uv run quickstart.py         # sanity check
lab notebook                 # notebooks in your browser (model dropdown, autosave)
```

## Prompts
System prompts and user-prompt templates live in `prompts/` and are versioned in git.
Never edit a prompt that produced reported results; copy it to a new version (`_v2`).

## Methods log (model use)
| Date | Commit | Task | Model (backend:name, digest) | Temp/seed | System prompt | User prompt | Output |
|---|---|---|---|---|---|---|---|

Call metadata: `$LAB_LOGS/labllm.jsonl`. Full prompts/replies: `outputs/*calls*.jsonl` (git-ignored).

## When the project ends
Delete `data/` and `outputs/` on the lab Mac, note the date here, and archive the repo.
