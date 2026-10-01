"""git_ops tests against a temp repo with a local bare remote, incl. a rejecting pre-commit hook."""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ui" / "src"))

from lab_ui.git_ops import project_status, save_and_push  # noqa: E402

ENV = {**os.environ, "GIT_AUTHOR_NAME": "A", "GIT_AUTHOR_EMAIL": "a@b.c",
       "GIT_COMMITTER_NAME": "A", "GIT_COMMITTER_EMAIL": "a@b.c"}


def _git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, env=ENV)


def _repo(tmp_path, with_remote=True):
    repo = tmp_path / "proj"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    (repo / "a.txt").write_text("1")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    if with_remote:
        bare = tmp_path / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
        _git(repo, "remote", "add", "origin", str(bare))
        _git(repo, "push", "-q", "-u", "origin", "main")
    return repo


def test_status_clean_then_dirty(tmp_path):
    repo = _repo(tmp_path)
    s = project_status(repo, ENV)
    assert (s.dirty, s.ahead, s.has_remote) == (0, 0, True)
    (repo / "b.txt").write_text("2")
    assert project_status(repo, ENV).dirty == 1


def test_save_and_push(tmp_path):
    repo = _repo(tmp_path)
    (repo / "b.txt").write_text("2")
    r = save_and_push(repo, "add b", ENV)
    assert r.ok and not r.blocked_by_hook
    s = project_status(repo, ENV)
    assert (s.dirty, s.ahead) == (0, 0)


def test_save_without_remote_commits_locally(tmp_path):
    repo = _repo(tmp_path, with_remote=False)
    (repo / "b.txt").write_text("2")
    r = save_and_push(repo, "add b", ENV)
    assert r.ok and "GitHub" in r.message
    assert project_status(repo, ENV).dirty == 0


def test_nothing_to_save(tmp_path):
    repo = _repo(tmp_path)
    r = save_and_push(repo, "x", ENV)
    assert r.ok and "Nothing" in r.message


def test_hook_rejection_is_reported_not_bypassed(tmp_path):
    repo = _repo(tmp_path)
    hook = repo / ".githooks" / "pre-commit"
    hook.parent.mkdir()
    hook.write_text("#!/usr/bin/env bash\necho 'looks like data' >&2\nexit 1\n")
    hook.chmod(0o755)
    _git(repo, "config", "core.hooksPath", ".githooks")
    (repo / "b.txt").write_text("2")
    r = save_and_push(repo, "add b", ENV)
    assert not r.ok and r.blocked_by_hook
    assert "looks like data" in r.detail
    after = project_status(repo, ENV)
    assert after.dirty >= 1 and after.ahead == 0  # nothing was committed or pushed
