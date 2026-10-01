"""UI backend tests: name validation, project listing, subprocess env (no secrets on disk)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ui" / "src"))

from lab_ui.projects import list_projects, read_teams, validate_name  # noqa: E402
from lab_ui.session import Identity, subprocess_env  # noqa: E402
from lab_ui.notebook_proc import extract_url  # noqa: E402


def test_validate_name():
    assert validate_name("my-study_1.0") is None
    assert validate_name("") is not None
    assert validate_name("has space") is not None
    assert validate_name("../evil") is not None


def test_list_projects_only_lab_projects(tmp_path):
    root = tmp_path / "ab123"
    (root / "one").mkdir(parents=True)
    (root / "one" / ".lab-project").write_text("teamx\n")
    (root / "two").mkdir()
    (root / "two" / "pyproject.toml").write_text("")
    (root / ".keys").mkdir()
    (root / "stray").mkdir()
    found = list_projects(tmp_path, "ab123")
    assert [(p.name, p.team) for p in found] == [("one", "teamx"), ("two", None)]


def test_list_projects_missing_user(tmp_path):
    assert list_projects(tmp_path, "nobody") == []


def test_read_teams_skips_comments(tmp_path):
    f = tmp_path / "teams.txt"
    f.write_text("# header\nalpha  Alpha team\n\nbeta # inline\n")
    assert read_teams(f) == ["alpha", "beta"]
    assert read_teams(tmp_path / "missing.txt") == []


def test_subprocess_env_sets_identity_and_secrets_without_mutating_base():
    base = {"PATH": "/bin"}
    ident = Identity(netid="ab123", name="Ada B", email="ab123@cornell.edu")
    env = subprocess_env(ident, base, cornell_key="k", gh_token="t", team="alpha")
    assert env["LAB_USER"] == "ab123"
    assert env["GIT_AUTHOR_NAME"] == env["GIT_COMMITTER_NAME"] == "Ada B"
    assert env["GIT_AUTHOR_EMAIL"] == env["GIT_COMMITTER_EMAIL"] == "ab123@cornell.edu"
    assert env["CORNELL_AI_API_KEY"] == "k" and env["GH_TOKEN"] == "t" and env["LAB_TEAM"] == "alpha"
    assert base == {"PATH": "/bin"}


def test_subprocess_env_omits_unset_secrets():
    env = subprocess_env(Identity("ab123", "Ada", "a@b.c"), {}, None, None, None)
    assert "CORNELL_AI_API_KEY" not in env and "GH_TOKEN" not in env


def test_extract_url():
    line = "    http://127.0.0.1:8890/lab?token=abc123"
    assert extract_url(line) == "http://127.0.0.1:8890/lab?token=abc123"
    assert extract_url("no url here") is None
