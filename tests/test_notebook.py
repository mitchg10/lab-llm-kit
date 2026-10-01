"""Notebook helper tests: model choices, saved selection (fake /v1/models servers, no real model)."""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from labllm.notebook import load_choice, model_choices, save_choice


def _serve(model_ids):
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            data = json.dumps({"object": "list", "data": [
                {"id": m, "object": "model", "created": 0, "owned_by": "x"} for m in model_ids]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


@pytest.fixture()
def backends(monkeypatch):
    servers = []

    def start(ollama=None, lmstudio=None):
        for var, ids in (("OLLAMA_BASE_URL", ollama), ("LMSTUDIO_BASE_URL", lmstudio)):
            if ids is None:   # nothing listening here: connection refused
                monkeypatch.setenv(var, "http://127.0.0.1:9")
            else:
                srv = _serve(ids)
                servers.append(srv)
                monkeypatch.setenv(var, f"http://127.0.0.1:{srv.server_port}")

    monkeypatch.delenv("CORNELL_AI_API_KEY", raising=False)
    yield start
    for s in servers:
        s.shutdown()


def test_ollama_models_are_bare_names(backends):
    backends(ollama=["qwen3:30b", "llama3:8b"])
    choices, notes = model_choices()
    assert choices == ["llama3:8b", "qwen3:30b"]
    assert any("lmstudio" in n.lower() for n in notes)   # unreachable backend: a note, not a traceback


def test_lmstudio_models_are_prefixed(backends):
    backends(ollama=["qwen3:30b"], lmstudio=["qwen/qwen3"])
    choices, notes = model_choices()
    assert choices == ["qwen3:30b", "lmstudio:qwen/qwen3"]
    assert notes == []


def test_cornell_only_with_key(backends, monkeypatch):
    backends(ollama=["qwen3:30b"], lmstudio=[])
    srv = _serve(["gpt-x"])
    monkeypatch.setenv("CORNELL_AI_BASE_URL", f"http://127.0.0.1:{srv.server_port}/v1")
    assert model_choices()[0] == ["qwen3:30b"]
    monkeypatch.setenv("CORNELL_AI_API_KEY", "k")
    assert model_choices()[0] == ["qwen3:30b", "cornell:gpt-x"]
    srv.shutdown()


def test_all_backends_down_gives_empty_list(backends):
    backends()
    choices, notes = model_choices()
    assert choices == [] and len(notes) == 2


def test_save_and_load_roundtrip(tmp_path):
    cfg = tmp_path / ".lab-notebook.json"
    save_choice("qwen3:30b", cfg)
    assert json.loads(cfg.read_text()) == {"model": "qwen3:30b"}
    assert load_choice(cfg, ["qwen3:30b", "llama3:8b"], "llama3:8b") == "qwen3:30b"


def test_save_keeps_other_settings_and_leaves_no_temp_files(tmp_path):
    cfg = tmp_path / ".lab-notebook.json"
    cfg.write_text(json.dumps({"model": "a", "keep": 1}))
    save_choice("b", cfg)
    assert json.loads(cfg.read_text()) == {"model": "b", "keep": 1}
    assert [p.name for p in tmp_path.iterdir()] == [".lab-notebook.json"]


def test_load_falls_back_when_saved_model_gone_or_file_bad(tmp_path):
    cfg = tmp_path / ".lab-notebook.json"
    assert load_choice(cfg, ["a"], "a") == "a"                 # no file
    cfg.write_text(json.dumps({"model": "removed"}))
    assert load_choice(cfg, ["a", "b"], "b") == "b"            # no longer installed
    cfg.write_text("{not json")
    assert load_choice(cfg, ["a", "b"], "b") == "b"            # corrupt file
    assert load_choice(cfg, [], "b") == "b"                    # nothing listed: keep the default


def test_default_config_lives_in_project_root(tmp_path):
    from labllm.notebook import default_config_path
    proj, other = tmp_path / "proj", tmp_path / "other"
    (proj / "notebooks").mkdir(parents=True)
    other.mkdir()
    (proj / "pyproject.toml").write_text("")
    assert default_config_path(proj / "notebooks") == proj / ".lab-notebook.json"
    assert default_config_path(other) == other / ".lab-notebook.json"   # no project: stay put
