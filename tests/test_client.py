"""Client tests with a fake OpenAI-compatible server (no real model needed)."""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from labllm import IdentifierError, LabLLM, resolve_model

SEEN = []


class Fake(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        SEEN.append(body)
        out = {"id": "x", "object": "chat.completion", "created": 0, "model": body["model"],
               "choices": [{"index": 0, "finish_reason": "stop",
                            "message": {"role": "assistant", "content": '{"code": "workload"}'}}],
               "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8}}
        data = json.dumps(out).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


@pytest.fixture()
def server(monkeypatch, tmp_path):
    srv = HTTPServer(("127.0.0.1", 0), Fake)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    monkeypatch.setenv("OLLAMA_BASE_URL", f"http://127.0.0.1:{srv.server_port}")
    monkeypatch.setenv("LAB_LOGS", str(tmp_path / "logs"))
    sp = tmp_path / "sp.md"
    sp.write_text("LAB DEFAULT CHAT PROMPT")
    monkeypatch.setenv("LAB_DEFAULT_CHAT_PROMPT", str(sp))
    SEEN.clear()
    yield tmp_path
    srv.shutdown()


def test_resolve_model():
    assert resolve_model("qwen3:30b") == ("ollama", "qwen3:30b")
    assert resolve_model("cornell:gpt-x") == ("cornell", "gpt-x")
    assert resolve_model("lmstudio:qwen/qwen3") == ("lmstudio", "qwen/qwen3")


def test_api_sends_only_your_prompts(server):
    llm = LabLLM("qwen3:30b", save_to=server / "run.jsonl")
    r = llm.chat("Code this excerpt: P01 said the workload doubled.")
    assert r.json() == {"code": "workload"}
    sent = SEEN[-1]
    assert [m["role"] for m in sent["messages"]] == ["user"]          # no hidden system prompt
    assert sent["temperature"] == 0 and sent["seed"] == 42
    log = [json.loads(l) for l in (server / "logs/labllm.jsonl").read_text().splitlines()]
    assert log[-1]["system_source"] == "none" and "P01" not in json.dumps(log[-1])   # metadata only
    assert "P01" in (server / "run.jsonl").read_text()                                 # full record where asked


def test_system_prompt_options(server):
    f = server / "system.md"
    f.write_text("You are a careful qualitative coder.")
    llm = LabLLM("qwen3:30b", system=str(f))                    # client default from a file
    llm.chat("hi")
    assert SEEN[-1]["messages"][0] == {"role": "system", "content": "You are a careful qualitative coder."}
    llm.chat("hi", system="Per-call override.")                 # per call beats client default
    assert SEEN[-1]["messages"][0]["content"] == "Per-call override."
    llm.chat(messages=[{"role": "system", "content": "From messages."}, {"role": "user", "content": "hi"}])
    assert [m["content"] for m in SEEN[-1]["messages"] if m["role"] == "system"] == ["From messages."]
    from labllm import DEFAULT
    LabLLM("qwen3:30b", system=DEFAULT).chat("hi", temperature=0.3, top_p=0.9)
    assert SEEN[-1]["messages"][0]["content"] == "LAB DEFAULT CHAT PROMPT"
    assert SEEN[-1]["top_p"] == 0.9 and SEEN[-1]["temperature"] == 0.3


def test_ask_cli_uses_default_unless_overridden(server, capsys):
    from labllm.cli import main
    main(["ask", "hello", "-m", "qwen3:30b"])
    assert SEEN[-1]["messages"][0]["content"] == "LAB DEFAULT CHAT PROMPT"
    main(["ask", "hello", "-m", "qwen3:30b", "--no-system"])
    assert SEEN[-1]["messages"][0]["role"] == "user"
    main(["ask", "hello", "-m", "qwen3:30b", "-s", "Be terse."])
    assert SEEN[-1]["messages"][0]["content"] == "Be terse."


def test_identifiers_block_the_request(server):
    with pytest.raises(IdentifierError):
        LabLLM("qwen3:30b").chat("Jane (jd123@cornell.edu) said the workload doubled.")
    assert SEEN == []   # nothing reached the server


def test_cornell_needs_login(monkeypatch):
    monkeypatch.delenv("CORNELL_AI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="lab-login"):
        LabLLM("cornell:any").chat("hello")


def test_batch_resumable_and_blocks_identifier_rows(server):
    import csv
    from pathlib import Path
    from labllm.cli import main
    kit = Path(__file__).resolve().parents[1] / "examples"
    out = server / "coded.csv"
    args = [ "batch", str(kit / "data/synthetic_excerpts.csv"), "--text-col", "text",
             "--prompt", str(kit / "prompts/code_excerpt.md"), "--schema", str(kit / "prompts/schema.json"),
             "--out", str(out), "-m", "qwen3:30b", "--system", str(kit / "prompts/system_coding.md")]
    assert main(args) == 1                      # row 5 has an email -> flagged
    rows = list(csv.DictReader(open(out)))
    assert len(rows) == 5 and rows[4]["_status"].startswith("NOT SENT")
    assert len(SEEN) == 4 and "{text}" not in SEEN[0]["messages"][1]["content"]
    assert SEEN[0]["response_format"]["type"] == "json_schema"
    assert SEEN[0]["messages"][0]["role"] == "system" and "codebook" in SEEN[0]["messages"][0]["content"].lower()
    n = len(SEEN); main(args)                   # resume: nothing re-sent
    assert len(SEEN) == n and len(list(csv.DictReader(open(out)))) == 5
