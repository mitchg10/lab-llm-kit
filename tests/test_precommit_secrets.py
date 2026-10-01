"""The project pre-commit hook must refuse credentials, and must not need labllm to do so."""
import shutil
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent.parent / "config" / "git-hooks" / "pre-commit"
FAKE_KEY = "sk-" + "a1B2c3D4e5F6g7H8i9J0k1L2"          # built in pieces so this file isn't itself flagged
FAKE_GH = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7"


@pytest.fixture()
def repo(tmp_path):
    def git(*a):
        return subprocess.run(["git", *a], cwd=tmp_path, capture_output=True, text=True,
                              env={"PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin", "HOME": str(tmp_path),
                                   "GIT_CONFIG_NOSYSTEM": "1"})
    git("init", "-q", "-b", "main")
    shutil.copy(HOOK, tmp_path / "hook")
    return tmp_path, git


def try_commit(repo, name, text):
    path, git = repo
    f = path / name
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text)
    git("add", "-A")
    r = subprocess.run(["bash", str(path / "hook")], cwd=path, capture_output=True, text=True,
                       env={"PATH": "/usr/bin:/bin"})
    return r.returncode, r.stdout + r.stderr


@pytest.mark.parametrize("text", [
    f'client = OpenAI(api_key="{FAKE_KEY}")\n',
    f"export CORNELL_AI_API_KEY={FAKE_KEY}\n",
    f"CORNELL_AI_API_KEY = 'abcdef0123456789abcdef'\n",
    f"GH_TOKEN={FAKE_GH}\n",
    f"token: {FAKE_GH}\n",
    "-----BEGIN OPENSSH PRIVATE KEY-----\nabc\n",
])
def test_blocks_credentials_in_code(repo, text):
    code, out = try_commit(repo, "analysis.py", text)
    assert code == 1 and "analysis.py" in out and "credential" in out.lower()
    assert FAKE_KEY not in out and FAKE_GH not in out  # the report never repeats the secret


@pytest.mark.parametrize("text", [
    'key = os.environ["CORNELL_AI_API_KEY"]\n',
    "export CORNELL_AI_API_KEY=$(lab-key)\n",
    "Run lab-key to load your Cornell key; keys look like sk-... and are per team.\n",
    "uses {env:CORNELL_AI_API_KEY}\n",
])
def test_allows_code_that_only_mentions_the_key(repo, text):
    code, out = try_commit(repo, "notes.md", text)
    assert code == 0, out
