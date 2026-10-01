# labllm

`labllm` is the lab's model client. It gives you one API for local Ollama, LM Studio and the Cornell AI Gateway. **It sends exactly the system and user prompts you write.** It adds an identifier check, reproducible defaults and metadata logging. The lab's default chat prompt is used only by `labllm chat`/`ask`, or when you pass `system=DEFAULT`.

```python
from labllm import LabLLM, DEFAULT
llm = LabLLM("qwen3:30b", system="prompts/system.md")     # your system prompt (text or file)
llm.chat("your user prompt")
llm.chat(messages=[{"role": "system", "content": "…"}, {"role": "user", "content": "…"}])
LabLLM("lmstudio:qwen/qwen3-30b-a3b")                      # LM Studio
LabLLM("cornell:<id>")                                     # Cornell gateway (after lab-key)
LabLLM(system=DEFAULT)                                     # opt in to the lab's default chat prompt
```

On the command line:

```bash
labllm chat
labllm ask "…" -f file.txt
labllm batch in.csv --system system.md --prompt user.md --text-col text --out out.csv
labllm scan files…
labllm models
```

See `skills/local-llm-api/SKILL.md` for the full guide.

To run the tests:

```bash
cd labllm && uv run --with pytest pytest ../tests
```
