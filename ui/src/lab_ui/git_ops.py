"""Save-to-GitHub for a project: status, then add + commit + push.

The repo's pre-commit hook always runs; we never pass --no-verify.
"""
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

GIT_TIMEOUT_S = 120


@dataclass(frozen=True)
class GitStatus:
    dirty: int
    ahead: int
    has_remote: bool


@dataclass(frozen=True)
class SaveResult:
    ok: bool
    message: str
    detail: str = ""
    blocked_by_hook: bool = False


def _git(repo: Path, env: Mapping[str, str], *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=repo, env=dict(env), stdin=subprocess.DEVNULL,
        capture_output=True, text=True, timeout=GIT_TIMEOUT_S,
    )


def project_status(repo: Path, env: Mapping[str, str]) -> GitStatus:
    dirty = len([ln for ln in _git(repo, env, "status", "--porcelain").stdout.splitlines() if ln])
    has_remote = bool(_git(repo, env, "remote").stdout.strip())
    ahead = 0
    if has_remote:
        counted = _git(repo, env, "rev-list", "--count", "@{u}..HEAD")
        ahead = int(counted.stdout.strip() or 0) if counted.returncode == 0 else 0
    return GitStatus(dirty, ahead, has_remote)


def save_and_push(repo: Path, message: str, env: Mapping[str, str]) -> SaveResult:
    _git(repo, env, "add", "-A")
    if _git(repo, env, "diff", "--cached", "--quiet").returncode == 0:
        return SaveResult(True, "Nothing new to save.")
    commit = _git(repo, env, "commit", "-q", "-m", message)
    if commit.returncode != 0:
        return SaveResult(
            False,
            "Your files weren't saved: the lab safety check found something that looks like "
            "data or an identifier. Review the details below and take those files out.",
            (commit.stdout + commit.stderr).strip(),
            blocked_by_hook=True,
        )
    if not _git(repo, env, "remote").stdout.strip():
        return SaveResult(True, "Saved on this Mac. This project isn't on GitHub yet.")
    push = _git(repo, env, "push", "-u", "origin", "HEAD")
    if push.returncode != 0:
        return SaveResult(False, "Saved here, but the upload to GitHub failed.",
                          (push.stdout + push.stderr).strip())
    return SaveResult(True, "Saved and uploaded to GitHub.")
