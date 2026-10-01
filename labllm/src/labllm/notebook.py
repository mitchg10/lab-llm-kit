"""Notebook helper: a model dropdown for beginners.

    from labllm.notebook import pick_model
    llm = pick_model()          # shows a dropdown; use llm.chat("...") as usual

The choice is saved in .lab-notebook.json in your project, so it is still selected next time.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .client import ENV, LabLLM

CONFIG_NAME = ".lab-notebook.json"
_PREFIX = {"ollama": "", "lmstudio": "lmstudio:", "cornell": "cornell:"}


def model_choices() -> tuple[list[str], list[str]]:
    """(model names ready for LabLLM, notes about backends we couldn't reach)."""
    backends = ["ollama", "lmstudio"] + (["cornell"] if ENV.get("CORNELL_AI_API_KEY") else [])
    choices: list[str] = []
    notes: list[str] = []
    for backend in backends:
        try:
            names = LabLLM(backend=backend, log=False).models(backend)
        except Exception:
            notes.append(f"Couldn't reach {backend}: is it running? (check with `lab status`)")
            continue
        choices = choices + [_PREFIX[backend] + n for n in names]
    return choices, notes


def default_config_path(start: str | Path | None = None) -> Path:
    """The config file in the project root (nearest folder with pyproject.toml), else the start folder."""
    start = Path(start or Path.cwd()).resolve()
    root = next((d for d in (start, *start.parents) if (d / "pyproject.toml").is_file()), start)
    return root / CONFIG_NAME


def _read(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def load_choice(path: str | Path, choices: list[str], default: str) -> str:
    """The saved model if it is still available, otherwise the default."""
    saved = _read(Path(path)).get("model")
    if choices and saved in choices:
        return saved
    return default


def save_choice(model: str, path: str | Path) -> None:
    """Write the chosen model, keeping any other settings. Atomic: never leaves a half-written file."""
    path = Path(path)
    merged = {**_read(path), "model": model}
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


class NotebookLLM:
    """Behaves like a LabLLM; the dropdown swaps in a new client when the model changes."""

    def __init__(self, model: str, **llm_kwargs: Any):
        self._kwargs = llm_kwargs
        self._llm = LabLLM(model, **llm_kwargs)

    def select(self, model: str) -> None:
        self._llm = LabLLM(model, **self._kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._llm, name)

    def __repr__(self) -> str:
        return f"<model: {self._llm.backend}:{self._llm.model}>"


def pick_model(config_path: str | Path | None = None, **llm_kwargs: Any) -> NotebookLLM:
    """Show a model dropdown and return a client that follows it. Extra arguments go to LabLLM."""
    import ipywidgets as widgets
    from IPython.display import display

    config_path = Path(config_path) if config_path else default_config_path()
    default = ENV.get("LAB_DEFAULT_MODEL", "qwen3:30b")
    choices, notes = model_choices()
    start = load_choice(config_path, choices, default)
    llm = NotebookLLM(start, **llm_kwargs)

    for note in notes:
        print(note)
    if not choices:
        print(f"No models found, so using {default}. Start a model server, then re-run this cell.")
        return llm

    dropdown = widgets.Dropdown(options=choices, value=start, description="Model:",
                                style={"description_width": "auto"}, layout=widgets.Layout(width="auto"))

    def on_change(change: dict) -> None:
        llm.select(change["new"])
        save_choice(change["new"], config_path)

    dropdown.observe(on_change, names="value")
    display(dropdown)
    return llm
