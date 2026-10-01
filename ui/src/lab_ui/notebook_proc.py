"""Start and stop `lab-notebook` for a project, and find the link it prints."""
import re
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional

URL_RE = re.compile(r"https?://127\.0\.0\.1:\d+\S*token=\w+")
START_TIMEOUT_S = 90


def extract_url(line: str) -> Optional[str]:
    found = URL_RE.search(line)
    return found.group(0) if found else None


@dataclass(frozen=True)
class RunningNotebook:
    process: subprocess.Popen
    url: str


def _drain(stream) -> None:
    for _ in stream:  # keep reading so the child never blocks on a full pipe
        pass


def start_notebook(kit: Path, project: Path, env: Mapping[str, str]) -> Optional[RunningNotebook]:
    """Launch lab-notebook; return once Jupyter prints its link, or None if it never does."""
    proc = subprocess.Popen(
        [str(kit / "bin" / "lab-notebook")], cwd=project, env=dict(env),
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    found: list = []

    def reader() -> None:
        for line in proc.stdout:
            url = extract_url(line)
            if url:
                found.append(url)
                break
        _drain(proc.stdout)

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()
    thread.join(START_TIMEOUT_S)
    if found:
        return RunningNotebook(proc, found[0])
    stop_notebook(proc)
    return None


def stop_notebook(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(10)
        except subprocess.TimeoutExpired:
            proc.kill()
