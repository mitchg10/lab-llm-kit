---
name: reproducible-llm-analysis
description: Make LLM-assisted research analysis reproducible and reportable. That means fixed settings, versioned prompts, model digests, repeated runs, human validation and a methods write-up. Use when a user runs models over research data for a paper or thesis, asks how to report model use, compares models or prompts, or needs to check the consistency of model outputs.
---

# Reproducible LLM analysis

Treat the model as an **instrument**. Record its settings, check that it behaves consistently, and validate it against people.

## Setup checklist for any analysis that might be published

1. **Project repo:** `lab new <study>`. It creates a separate git repo with `prompts/`, `outputs/` and a README with a methods-log table. See the `research-version-control` skill.
2. **Version the prompts.** Keep the **system prompt and the user-prompt template** in `prompts/` as separate files, and commit them. Never edit a prompt once it has been used for results; copy it to `_v2` instead. `labllm` sends exactly these prompts and nothing else, so the files *are* the method. Commit and tag before any run you might report (`git tag -a run-1 -m "…"`).
3. **Pin the model.** Record `backend:name` and the **digest** (`ollama show <model> --modelfile` or the `model_digest` field in `$LAB_LOGS/labllm.jsonl`). Local models are the most reproducible. Gateway models can change without notice, so record the date of each run.
4. **Use deterministic settings.** `labllm` defaults to temperature 0 and seed 42 on local models. Even so, results can differ slightly across hardware or versions, so say so in the paper.
5. **Keep full records.** Use `LabLLM(..., save_to="outputs/calls.jsonl")` or `labllm batch --save-to …`. The shared log only keeps hashes. It records `system_source` (none, custom, messages or lab-default) and a hash of the system prompt, so you can show which prompt was used.

## Check consistency before trusting results

- **Repeat runs.** Run a sample (for example, 50 items) 3 times with different seeds (`seed=1,2,3`, temperature around 0.7). Items that change label are unstable. Report the proportion.
- **Sensitivity to the prompt.** Test 2 wordings of the prompt. Report the agreement between them.
- **Model comparison.** If it matters, run a second model family, such as Qwen compared with Llama, or local compared with a Cornell gateway model.

## Validate against humans

- Have at least one researcher independently code a **random** subset (commonly 10–20%, or at least 50 items) without seeing the model's output.
- Report the agreement between the model and each human, and between the humans, using Cohen's κ or Krippendorff's α for categorical codes. Include a confusion table, and read the disagreements. Disagreements are often where the analytic insight is.
- Python with uv:
  ```bash
  uv add scikit-learn krippendorff
  ```
  ```python
  from sklearn.metrics import cohen_kappa_score
  cohen_kappa_score(human, model)
  ```

## Methods write-up template

> We used [model name, parameter size, quantization] (digest `[first 12 chars]`) served locally via [Ollama x.y / LM Studio] on an Apple M-series Mac Studio; no data left the machine. The system prompt and user-prompt template (Appendix X; repository tag `[tag]`) were fixed before analysis. Settings: temperature [t], seed [s], context [n] tokens. All inputs were de-identified under [IRB protocol #] before model use. We assessed stability across [k] runs ([p]% of items identical) and agreement with human coders on a random [n]-item subset (κ = [ ]). Model outputs were treated as suggestions; final codes were assigned by [researchers].

Report the exact system prompt you used. Don't describe the lab's default chat prompt as part of your method unless you deliberately opted in to it (`system_source: lab-default` in the logs).
