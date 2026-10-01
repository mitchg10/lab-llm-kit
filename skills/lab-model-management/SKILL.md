---
name: lab-model-management
description: Download, share, remove and size models on the lab Mac Studio across Ollama, Hugging Face (MLX) and LM Studio without duplicate copies. Use when a user wants a new model, asks what fits in memory, can't see a model in LM Studio, wants MLX or GGUF weights from Hugging Face, or is running low on disk.
---

# Managing models on the lab Mac

Each model is stored **once** under `$LAB_MODELS`. The other tools get links to it, not copies.

```
$LAB_MODELS/ollama       Ollama store (GGUF blobs)          ← `ollama pull`
$LAB_MODELS/huggingface  HF cache (MLX, safetensors, GGUF)  ← `hf download`
$LAB_MODELS/lmstudio     LM Studio's folder: symlinks to both of the above, plus LM Studio's own downloads
```

## Common tasks

| Goal | Command |
|---|---|
| See everything | `lab-models list` · `lab-models du` |
| Add an Ollama model | `lab-models pull ollama qwen3:30b` |
| Add a GGUF from Hugging Face into Ollama | `ollama pull hf.co/<org>/<repo>-GGUF:Q4_K_M` |
| Add MLX weights, which are fastest on Apple Silicon | `lab-models pull hf mlx-community/<repo>` |
| Make new models appear in LM Studio | `lab-models link-lmstudio`, then refresh **My Models** in LM Studio |
| Make a chat variant with the lab's default chat prompt | `lab-models make-lab-variants qwen3:30b` creates `lab-qwen3:30b`. This takes almost no extra disk. It's a *default*: any request with its own system prompt replaces it. For analysis, use the plain model. |
| Remove a model | `ollama rm <name>` or `hf cache delete`, then `lab-models link-lmstudio` to clear the dead links |
| What fits in memory? | `lab-models recommend` |
| Change the lab's standard set | edit `$LAB_KIT/config/models.txt`, then run `lab-models pull-list` |

**Prefer Ollama or HF downloads over LM Studio's own downloader.** Those can be shared with every tool. Anything downloaded inside LM Studio can only be used by LM Studio.

## Memory rules of thumb (4-bit quantization)

- Parameter count in billions × about 0.6 gives GB, plus a few GB for context. For example, 30B ≈ 20 GB and 70B ≈ 45 GB.
- By default macOS lets the GPU use about 75% of unified memory. An admin can raise that until the next reboot: `sudo sysctl iogpu.wired_limit_mb=<MB>`.
- Ollama keeps up to 3 models loaded for 30 minutes (`OLLAMA_MAX_LOADED_MODELS`, `OLLAMA_KEEP_ALIVE` in `~/Library/LaunchAgents/edu.lab.ollama.plist`). If LM Studio is also running a large model, the two compete for memory. Unload one of them (`ollama stop <model>` or `lms unload --all`).

## Ollama service

Ollama runs as the LaunchAgent `edu.lab.ollama`, bound to 127.0.0.1 only. Don't also start the Ollama menu-bar app or `brew services`.
- Restart: `launchctl kickstart -k gui/$(id -u)/edu.lab.ollama`
- Log: `$LAB_ROOT/logs/ollama.log`
- Change settings (context length, parallel requests): edit `$LAB_KIT/config/edu.lab.ollama.plist`, then run `$LAB_KIT/install.sh 03`.

## Reproducibility

Record the **digest** as well as the name. Tags like `qwen3:30b` can be updated upstream. `ollama show <name>` and `labllm` logs both include the digest. Don't re-pull a model in the middle of a study without noting it in the project README.
