"""List and create projects by calling the same scripts the terminal uses."""
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Mapping, Optional

NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")
CREATE_TIMEOUT_S = 600  # uv has to download Python and packages on first use


@dataclass(frozen=True)
class Project:
    name: str
    path: Path
    team: Optional[str]


@dataclass(frozen=True)
class CommandResult:
    ok: bool
    output: str


def validate_name(name: str) -> Optional[str]:
    """Return a plain-language problem with `name`, or None if it is fine."""
    if not name:
        return "Give the project a name."
    if not NAME_RE.match(name):
        return "Use only letters, digits, - _ and . (no spaces)."
    return None


def read_teams(teams_file: Path) -> List[str]:
    """Team slugs from config/teams.txt (comments and blank lines ignored)."""
    try:
        lines = teams_file.read_text().splitlines()
    except OSError:
        return []
    cleaned = (line.split("#", 1)[0].split() for line in lines)
    return [parts[0] for parts in cleaned if parts]


def _team_of(project_dir: Path) -> Optional[str]:
    try:
        first = (project_dir / ".lab-project").read_text().splitlines()[0].strip()
    except (OSError, IndexError):
        return None
    return first or None


def list_projects(projects_root: Path, netid: str) -> List[Project]:
    """Folders under <root>/<netid> that look like lab projects, sorted by name."""
    user_dir = projects_root / netid
    if not user_dir.is_dir():
        return []
    return [
        Project(d.name, d, _team_of(d))
        for d in sorted(user_dir.iterdir())
        if d.is_dir() and not d.name.startswith(".")
        and ((d / ".lab-project").exists() or (d / "pyproject.toml").exists())
    ]


def create_project(
    kit: Path, name: str, team: Optional[str], notebook: bool, github: bool, env: Mapping[str, str]
) -> CommandResult:
    """Run bin/lab-new-project non-interactively. stdin is closed so it can never prompt."""
    cmd = [str(kit / "bin" / "lab-new-project"), name]
    cmd += ["--team", team] if team else []
    cmd += ["--notebook"] if notebook else []
    cmd += ["--github"] if github else []
    try:
        done = subprocess.run(
            cmd, env=dict(env), stdin=subprocess.DEVNULL, capture_output=True, text=True,
            timeout=CREATE_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return CommandResult(False, "Creating the project took too long and was stopped.")
    return CommandResult(done.returncode == 0, (done.stdout + done.stderr).strip())
