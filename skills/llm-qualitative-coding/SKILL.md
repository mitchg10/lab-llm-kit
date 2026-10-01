---
name: llm-qualitative-coding
description: Use local LLMs to help code qualitative data such as interview excerpts, open-ended survey responses or field notes against a codebook, or to suggest candidate themes, while researchers keep interpretive authority. Use when a user wants to apply a codebook with a model, pre-code or triage excerpts, draft code definitions, or compare model codes with human codes.
---

# LLM-assisted qualitative coding

The model helps you code; it doesn't do the coding for you. Start by following `lab-data-privacy`. Then use `reproducible-llm-analysis` if the results might be published.

## 1. Prepare the data

- Put de-identified excerpts in a CSV with columns `id,text`, plus any context columns such as `speaker` or `question`. Keep each excerpt short: one idea, usually 1–6 sentences.
- Run `lab-scan data/excerpts.csv` and don't go on until it is clean.

## 2. Write the prompts: system and user are separate files

**`prompts/system_coding.md`** is the system prompt: the role, the codebook and the rules. There is a starter in `$LAB_KIT/examples/prompts/`. Include:
- For each code: a **name**, a **definition**, **when to use it**, **when not to use it**, and one short example (**synthetic or already published**, never from this study's participants unless it is already de-identified).
- An explicit `none` / `uncertain` option, so the model isn't forced to pick a code.
- An instruction to quote the **exact** words from the excerpt that triggered each code. This makes the model's output easy to check.

**`prompts/code_excerpt.md`** is the user-prompt template, filled in for each row. Use `{text}`, and any other column such as `{speaker}`. To write a literal brace, double it: `{{` `}}`.

These are the only prompts sent: `labllm` adds no system prompt of its own. Commit both files before a real run.

## 3. Ask for structured output

`schema.json`:
```json
{"type":"object","additionalProperties":false,
 "required":["codes","evidence","confidence","note"],
 "properties":{
   "codes":{"type":"array","items":{"type":"string","enum":["CODE_A","CODE_B","none","uncertain"]}},
   "evidence":{"type":"array","items":{"type":"string"}},
   "confidence":{"type":"string","enum":["low","medium","high"]},
   "note":{"type":"string"}}}
```

## 4. Run it

```bash
labllm batch data/excerpts.csv --text-col text \
  --system prompts/system_coding.md --prompt prompts/code_excerpt.md \
  --schema prompts/schema.json -m qwen3:30b \
  --out outputs/coded_v1.csv --save-to outputs/calls_v1.jsonl
```
Start with about 20 rows, read every output, and refine the codebook before you run the full set. Each revision gets a new prompt version (`_v2`) and a commit.

## 5. Verify, don't trust

- **Evidence check:** each `evidence` string must appear exactly in the excerpt. Flag any that don't: that's a fabrication.
  ```python
  import pandas as pd, json
  df = pd.read_csv("outputs/coded_v1.csv")
  df["evidence_ok"] = [all(e in t for e in json.loads(r)["evidence"]) for t, r in zip(df.text, df.response)]
  ```
- Send every `low` confidence, `uncertain` and failed evidence check to human review.
- Compare against human coding of a random subset (see `reproducible-llm-analysis`).

## Inductive and thematic work

Models can suggest candidate themes from batches of excerpts. Treat these like a colleague's first-pass memo, not as findings:
- Ask for themes **with the IDs of supporting excerpts**, so every claim can be traced.
- Watch for smoothing. Models tend to produce tidy, generic themes and miss tensions, silences and minority views. Those often matter most in engineering education research.
- The researcher writes the final theme definitions and chooses the exemplar quotes, from the source data.
