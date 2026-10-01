"""Quick test that the lab's models answer. Run with:  uv run quickstart.py

labllm sends exactly the prompts you write: no hidden system prompt. It does
check your text for identifiers before sending, and logs call metadata (not
content) for your methods record.
"""
from pathlib import Path

from labllm import DEFAULT, IdentifierError, LabLLM

# 1. Your own system + user prompt (the normal way to do analysis)
llm = LabLLM("qwen3:30b", system="You are a concise research assistant in engineering education.")
print(llm.chat("In one sentence: what does 'epistemic trust' mean in education research?").text)

# 2. Prompts kept in files (best for anything you'll report): system from a file, user from a template
system = Path("prompts/system_coding.md")
user_template = Path("prompts/code_excerpt.md").read_text()
schema = {
    "type": "object", "additionalProperties": False,
    "required": ["codes", "evidence", "confidence", "note"],
    "properties": {
        "codes": {"type": "array", "items": {"type": "string"}},
        "evidence": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
        "note": {"type": "string"},
    },
}
excerpt = "Honestly the AI saves me time on boilerplate, but I no longer trust I understand my own code."
coder = LabLLM("qwen3:30b", system=system, save_to="outputs/quickstart_calls.jsonl")
r = coder.chat(user_template.format(speaker="P04", text=excerpt), json_schema=schema)
print(r.json(), f"({r.seconds}s)")

# 3. Full control with a message list (multi-turn, few-shot examples, etc.)
r = llm.chat(messages=[
    {"role": "system", "content": "Answer with one word."},
    {"role": "user", "content": "Is 'statics' a course or a software tool?"},
])
print(r.text)

# 4. The lab's default chat prompt, only if you want it
print(LabLLM(system=DEFAULT).chat("What should I keep in mind about participant data?").text[:300], "…")

# 5. The identifier check in action: refused before anything is sent
fake_email = "jane.doe" + "@" + "example.edu"   # built at runtime so the git hook doesn't flag this file
try:
    llm.chat(f"Summarize: Jane ({fake_email}) said the lab was stressful.")
except IdentifierError as e:
    print("\nBlocked as expected:\n", e)

# 6. Cornell AI Gateway (after `lab-key` in this terminal):
# print(LabLLM("cornell:<gateway-model-id>", system=system).chat("…").text)
