"""labllm client: one interface for Ollama, LM Studio and the Cornell AI Gateway.

    from labllm import LabLLM
    llm = LabLLM("qwen3:30b", system="prompts/system.md")         # YOUR system prompt (text or file)
    llm.chat("…user prompt…")                                     # sent exactly as you wrote it
    llm.chat(messages=[{"role": "system", …}, {"role": "user", …}])   # or full control

    LabLLM("lmstudio:qwen/qwen3-30b-a3b")                           # LM Studio
    LabLLM("cornell:<gateway-model-id>")                            # Cornell gateway (after lab-login)

What labllm does to your prompts: nothing. There is no hidden system prompt.
The lab's default chat prompt is added ONLY if you ask (`system=DEFAULT`), and
the `labllm ask` chat command uses it when you don't give your own.

What labllm does add:
  1. an identifier scan of user/system text before sending (refuses if it finds any),
  2. reproducible defaults (temperature 0, seed 42 on local models) that you can override,
  3. a metadata-only log line (hashes, model, params; no content) in $LAB_LOGS/labllm.jsonl.
"""
from __future__ import annotations

import getpass
import hashlib
import json
import os
import time
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .scan import IdentifierError, load_terms, scan_text

ENV = os.environ
LAB_ROOT = Path(ENV.get("LAB_ROOT", "/Users/Shared/lab-llm"))


class _Default:
    """Sentinel: use the lab's default chat prompt as the system prompt."""

    def __repr__(self):
        return "DEFAULT"


DEFAULT = _Default()


def _backends() -> dict[str, dict[str, str]]:
    return {
        "ollama": {"base_url": ENV.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/") + "/v1",
                   "api_key": "ollama", "local": "1"},
        "lmstudio": {"base_url": ENV.get("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234").rstrip("/") + "/v1",
                     "api_key": "lm-studio", "local": "1"},
        "cornell": {"base_url": ENV.get("CORNELL_AI_BASE_URL", "").rstrip("/"),
                    "api_key": ENV.get("CORNELL_AI_API_KEY", ""), "local": ""},
    }


BACKEND_NAMES = ("ollama", "lmstudio", "cornell")


def resolve_model(model: str | None, backend: str | None = None) -> tuple[str, str]:
    """'cornell:gpt-x' -> ('cornell', 'gpt-x'); 'qwen3:30b' -> ('ollama', 'qwen3:30b')."""
    model = model or ENV.get("LAB_DEFAULT_MODEL", "qwen3:30b")
    head, sep, rest = model.partition(":")
    if sep and head in BACKEND_NAMES:
        return head, rest
    return (backend or ENV.get("LABLLM_BACKEND", "ollama")), model


def default_chat_prompt() -> str:
    """The lab's default system prompt for general chat use (constitution/DEFAULT_CHAT_PROMPT.md)."""
    p = Path(ENV.get("LAB_DEFAULT_CHAT_PROMPT", LAB_ROOT / "kit/constitution/DEFAULT_CHAT_PROMPT.md"))
    return p.read_text(encoding="utf-8").strip() if p.is_file() else ""


def load_prompt(value: str | Path | _Default | None) -> str | None:
    """Text, a path to a prompt file (.md/.txt), DEFAULT, or None."""
    if value is None:
        return None
    if isinstance(value, _Default):
        return default_chat_prompt()
    if isinstance(value, Path):
        return value.read_text(encoding="utf-8").strip()
    if "\n" not in value and len(value) < 300 and value.endswith((".md", ".txt")) and Path(value).is_file():
        return Path(value).read_text(encoding="utf-8").strip()
    return value


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


_digest_cache: dict[str, str] = {}


def ollama_digest(model: str) -> str:
    """Exact weights digest for an Ollama model, recorded for reproducibility."""
    if model in _digest_cache:
        return _digest_cache[model]
    try:
        url = ENV.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/") + "/api/tags"
        with urllib.request.urlopen(url, timeout=3) as r:
            for m in json.load(r).get("models", []):
                _digest_cache[m["name"]] = m.get("digest", "")
    except Exception:
        pass
    return _digest_cache.get(model, "")


@dataclass
class Result:
    text: str
    model: str
    backend: str
    usage: dict[str, Any] = field(default_factory=dict)
    seconds: float = 0.0
    raw: Any = None

    def json(self) -> Any:
        """Parse the reply as JSON (strips ``` fences if the model added them)."""
        t = self.text.strip()
        if t.startswith("```"):
            t = t.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(t)

    def __str__(self) -> str:
        return self.text


class LabLLM:
    """Client for the lab's models.

    model         'name' (Ollama), 'lmstudio:name' or 'cornell:name'. Default $LAB_DEFAULT_MODEL.
    system        default system prompt for this client: text, a prompt file path, DEFAULT
                  (the lab's default chat prompt) or None (no system prompt). Per-call `system=`
                  or a system message in `messages=` overrides it.
    scan          refuse to send text with possible identifiers (default True)
    ignore/allow  scanner tuning: finding kinds to skip / terms that are fine (pseudonyms)
    names_file    file of real names to look for (keep it off this machine when you can)
    save_to       optional JSONL file in YOUR project that stores full prompts and replies
    """

    def __init__(self, model: str | None = None, *, backend: str | None = None,
                 system: str | Path | _Default | None = None, scan: bool = True,
                 ignore: list[str] | tuple[str, ...] = (), allow: list[str] | None = None,
                 names_file: str | None = None, save_to: str | Path | None = None, log: bool = True):
        self.backend, self.model = resolve_model(model, backend)
        self.system = system
        self.scan = scan
        self.ignore = tuple(ignore)
        self.allow = list(allow or []) + load_terms(ENV.get("LABLLM_ALLOW_FILE"))
        self.names = load_terms(names_file)
        self.save_to = Path(save_to) if save_to else None
        self.log = log
        self._clients: dict[str, Any] = {}

    # -- plumbing ---------------------------------------------------------
    def _client(self, backend: str):
        if backend not in self._clients:
            from openai import OpenAI
            cfg = _backends()[backend]
            if backend == "cornell" and (not cfg["base_url"] or "[" in cfg["base_url"] or not cfg["api_key"]):
                raise RuntimeError("Cornell gateway not configured: run `lab-login` in this terminal "
                                   "(and make sure CORNELL_AI_BASE_URL is set in config/lab.env).")
            self._clients[backend] = OpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"], timeout=600)
        return self._clients[backend]

    def check(self, text: str, *, ignore=(), allow=None):
        if not self.scan:
            return
        findings = scan_text(text, names=self.names, allow=self.allow + list(allow or []),
                             ignore=self.ignore + tuple(ignore))
        if findings:
            raise IdentifierError(findings)

    def _log(self, rec: dict):
        if not self.log:
            return
        try:
            logs = Path(ENV.get("LAB_LOGS", LAB_ROOT / "logs"))
            logs.mkdir(parents=True, exist_ok=True)
            with open(logs / "labllm.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
        except OSError:
            pass

    # -- API --------------------------------------------------------------
    def chat(self, prompt: str | None = None, *, messages: list[dict] | None = None,
             system: str | Path | _Default | None = None, model: str | None = None,
             temperature: float = 0.0, seed: int | None = None, max_tokens: int | None = None,
             json_schema: dict | None = None, ignore: list[str] | tuple[str, ...] = (),
             allow: list[str] | None = None, **extra) -> Result:
        """Send one chat request, with exactly the prompts you give.

        prompt    the user message (string)
        messages  a full OpenAI-style message list (system/user/assistant); combined with prompt if both
        system    system prompt for this call (text, file path, DEFAULT or None). Used only when
                  `messages` has no system message; otherwise falls back to the client's `system`.
        **extra   any other OpenAI parameter (top_p, stop, tools, …) is passed through unchanged.
        """
        backend, mdl = resolve_model(model, self.backend) if model else (self.backend, self.model)
        msgs = [dict(m) for m in (messages or [])]
        if prompt is not None:
            msgs.append({"role": "user", "content": prompt})
        if not msgs:
            raise ValueError("Nothing to send: pass prompt=... or messages=[...]")

        if any(m.get("role") == "system" for m in msgs):
            source = "messages"
        else:
            chosen = system if system is not None else self.system
            text = load_prompt(chosen)
            source = "lab-default" if isinstance(chosen, _Default) else ("custom" if text else "none")
            if text:
                msgs.insert(0, {"role": "system", "content": text})

        all_text = "\n".join(m["content"] for m in msgs if isinstance(m.get("content"), str))
        self.check(all_text, ignore=ignore, allow=allow)

        local = bool(_backends()[backend]["local"])
        params: dict[str, Any] = {"model": mdl, "messages": msgs, "temperature": temperature, **extra}
        if seed is None and local:
            seed = 42
        if seed is not None:
            params["seed"] = seed
        if max_tokens:
            params["max_tokens"] = max_tokens
        if json_schema:
            params["response_format"] = {"type": "json_schema",
                                         "json_schema": {"name": "output", "schema": json_schema, "strict": True}}

        t0 = time.time()
        resp = self._client(backend).chat.completions.create(**params)
        secs = round(time.time() - t0, 2)
        text = resp.choices[0].message.content or ""
        usage = resp.usage.model_dump() if getattr(resp, "usage", None) else {}
        sys_text = next((m["content"] for m in msgs if m["role"] == "system"), "")

        rec = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "user": ENV.get("LAB_USER") or getpass.getuser(),
            "backend": backend, "model": mdl, "served_model": getattr(resp, "model", mdl),
            "model_digest": ollama_digest(mdl) if backend == "ollama" else "",
            "temperature": temperature, "seed": seed, "json_schema": bool(json_schema),
            "system_source": source, "system_sha256": _sha(sys_text) if sys_text else "",
            "prompt_sha256": _sha(json.dumps(msgs)), "response_sha256": _sha(text),
            "usage": usage, "seconds": secs,
        }
        self._log(rec)
        if self.save_to:
            self.save_to.parent.mkdir(parents=True, exist_ok=True)
            with open(self.save_to, "a", encoding="utf-8") as f:
                f.write(json.dumps({**rec, "messages": msgs, "response": text}) + "\n")
        return Result(text=text, model=mdl, backend=backend, usage=usage, seconds=secs, raw=resp)

    def embed(self, texts: list[str] | str, *, model: str | None = None) -> list[list[float]]:
        """Embeddings (default $LAB_EMBED_MODEL on Ollama). Texts are scanned first."""
        texts = [texts] if isinstance(texts, str) else list(texts)
        self.check("\n".join(texts))
        backend, mdl = resolve_model(model or ENV.get("LAB_EMBED_MODEL", "nomic-embed-text"), "ollama")
        resp = self._client(backend).embeddings.create(model=mdl, input=texts)
        self._log({"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   "user": ENV.get("LAB_USER") or getpass.getuser(), "backend": backend, "model": mdl,
                   "kind": "embedding", "n": len(texts), "prompt_sha256": _sha(json.dumps(texts))})
        return [d.embedding for d in resp.data]

    def models(self, backend: str | None = None) -> list[str]:
        return sorted(m.id for m in self._client(backend or self.backend).models.list().data)


_default: LabLLM | None = None


def chat(prompt: str | None = None, **kw) -> Result:
    """Quick one-off call. No system prompt unless you pass system=… (or system=DEFAULT)."""
    global _default
    if _default is None:
        _default = LabLLM()
    return _default.chat(prompt, **kw)


def embed(texts, **kw):
    global _default
    if _default is None:
        _default = LabLLM()
    return _default.embed(texts, **kw)
