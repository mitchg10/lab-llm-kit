"""bin/lab-key is sourced into the student's shell (zsh on the lab Mac), so test it in both shells."""
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

KEY_SCRIPT = Path(__file__).resolve().parent.parent / "bin" / "lab-key"
SHELLS = [s for s in ("bash", "zsh") if shutil.which(s)]


@pytest.fixture()
def lab(tmp_path):
    kit = tmp_path / "kit"
    (kit / "config").mkdir(parents=True)
    projects = tmp_path / "research"
    proj = projects / "ab123" / "study"
    (proj / "notebooks").mkdir(parents=True)
    return {"kit": kit, "projects": projects, "proj": proj, "tmp": tmp_path}


def teams(lab, *slugs):
    lines = ["# lab teams", *slugs]
    (lab["kit"] / "config" / "teams.txt").write_text("\n".join(lines) + "\n")


def run(lab, shell, args="", stdin="", cwd=None, env_extra=None, user="ab123", path=None):
    env = {"PATH": path or "/usr/bin:/bin", "HOME": str(lab["tmp"]), "LAB_KIT": str(lab["kit"]),
           "LAB_PROJECTS": str(lab["projects"])}
    if user:
        env["LAB_USER"] = user
    env.update(env_extra or {})
    script = f'source "{KEY_SCRIPT}" {args}; echo "rc=$?"; echo "KEY=${{CORNELL_AI_API_KEY:-}}"; echo "TEAM=${{LAB_TEAM:-}}"'
    p = subprocess.run([shutil.which(shell), "-c", script], input=stdin, capture_output=True,
                       text=True, cwd=cwd or lab["proj"], env=env, timeout=20)
    out = dict(line.split("=", 1) for line in p.stdout.splitlines() if line.split("=", 1)[0] in ("rc", "KEY", "TEAM"))
    return out, p.stdout + p.stderr


@pytest.mark.parametrize("shell", SHELLS)
def test_loads_key_for_team_found_in_parent_directory(lab, shell):
    teams(lab, "soc-media-2026")
    (lab["proj"] / ".lab-project").write_text("soc-media-2026\n")
    out, text = run(lab, shell, stdin="sk-abc123\n", cwd=lab["proj"] / "notebooks")
    assert out["KEY"] == "sk-abc123" and out["TEAM"] == "soc-media-2026" and out["rc"] == "0"
    assert "soc-media-2026" in text
    shown = "\n".join(l for l in text.splitlines() if not l.startswith("KEY="))  # KEY= is the harness's own echo
    assert "sk-abc123" not in shown  # lab-key never prints the key


@pytest.mark.parametrize("shell", SHELLS)
def test_no_project_file_loads_nothing(lab, shell):
    out, text = run(lab, shell, stdin="sk-abc123\n")
    assert out["KEY"] == "" and out["rc"] != "0"
    assert ".lab-project" in text


@pytest.mark.parametrize("shell", SHELLS)
def test_explicit_team_works_outside_a_project(lab, shell):
    teams(lab, "soc-media-2026", "other-team")
    out, _ = run(lab, shell, args="other-team", stdin="sk-xyz\n", cwd=lab["tmp"])
    assert out["KEY"] == "sk-xyz" and out["TEAM"] == "other-team"


@pytest.mark.parametrize("shell", SHELLS)
def test_unknown_team_is_refused_when_teams_are_listed(lab, shell):
    teams(lab, "soc-media-2026")
    (lab["proj"] / ".lab-project").write_text("rogue-team\n")
    out, text = run(lab, shell, stdin="sk-abc\n")
    assert out["KEY"] == "" and out["rc"] != "0"
    assert "teams.txt" in text


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("slug", ["../etc", "a b", "UPPER", "-x"])
def test_invalid_slug_is_refused(lab, shell, slug):
    (lab["proj"] / ".lab-project").write_text(slug + "\n")
    out, _ = run(lab, shell, stdin="sk-abc\n")
    assert out["KEY"] == "" and out["rc"] != "0"


@pytest.mark.parametrize("shell", SHELLS)
def test_switching_team_never_keeps_the_old_teams_key(lab, shell):
    teams(lab, "team-a", "team-b")
    (lab["proj"] / ".lab-project").write_text("team-b\n")
    out, _ = run(lab, shell, stdin="\n",
                 env_extra={"CORNELL_AI_API_KEY": "sk-from-a", "LAB_TEAM": "team-a"})
    assert out["KEY"] == "" and out["TEAM"] == ""


@pytest.mark.parametrize("shell", SHELLS)
def test_auto_is_silent_when_team_matches_or_not_logged_in(lab, shell):
    (lab["proj"] / ".lab-project").write_text("team-a\n")
    out, text = run(lab, shell, args="--auto", env_extra={"LAB_TEAM": "team-a"})
    assert text.count("team-a") == 1 and "lab-key" not in text  # only the TEAM= echo
    _, text = run(lab, shell, args="--auto", user="")
    assert "lab-key" not in text


@pytest.mark.parametrize("shell", SHELLS)
def test_auto_hints_but_does_not_prompt_or_load_when_team_differs(lab, shell):
    (lab["proj"] / ".lab-project").write_text("team-b\n")
    out, text = run(lab, shell, args="--auto", stdin="sk-should-not-be-read\n",
                    env_extra={"LAB_TEAM": "team-a", "CORNELL_AI_API_KEY": "sk-a"})
    assert "team-b" in text and "lab-key" in text
    assert out["KEY"] == "sk-a"  # untouched; the student decides when to switch


def _fake_age(tmp_path):
    """Stand-in for `age` that just stores/returns the plaintext (tests wiring, not crypto)."""
    bindir = tmp_path / "fakebin"
    bindir.mkdir()
    age = bindir / "age"
    age.write_text('#!/bin/sh\n'
                   'case "$1" in\n'
                   '  -p) cat > "$3";;\n'
                   '  -d) cat "$2";;\n'
                   'esac\n')
    age.chmod(age.stat().st_mode | stat.S_IEXEC)
    return f"{bindir}:/usr/bin:/bin"


@pytest.mark.parametrize("shell", SHELLS)
def test_age_backend_stores_once_then_unlocks_without_typing(lab, shell):
    teams(lab, "team-a")
    (lab["proj"] / ".lab-project").write_text("team-a\n")
    path = _fake_age(lab["tmp"])
    env = {"LAB_KEY_BACKEND": "age"}
    out, _ = run(lab, shell, stdin="sk-stored\n", env_extra=env, path=path)
    assert out["KEY"] == "sk-stored"
    stored = lab["projects"] / "ab123" / ".keys" / "team-a.age"
    assert stored.exists()
    out, _ = run(lab, shell, stdin="", env_extra=env, path=path)  # second window: nothing typed
    assert out["KEY"] == "sk-stored"


@pytest.mark.parametrize("shell", SHELLS)
def test_age_backend_needs_login_and_age_installed(lab, shell):
    (lab["proj"] / ".lab-project").write_text("team-a\n")
    out, text = run(lab, shell, env_extra={"LAB_KEY_BACKEND": "age"}, user="")
    assert out["KEY"] == "" and "lab-login" in text
    out, text = run(lab, shell, env_extra={"LAB_KEY_BACKEND": "age"})
    assert out["KEY"] == "" and "age" in text
