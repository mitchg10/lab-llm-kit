"""Who the student is, and the environment handed to every subprocess.

Nothing here touches disk: the shared account means identity and keys live only in this
process (the Streamlit session) and in the env of the commands it launches.
"""
from dataclasses import dataclass
from typing import Mapping, Optional


@dataclass(frozen=True)
class Identity:
    netid: str
    name: str
    email: str


def subprocess_env(
    identity: Identity,
    base: Mapping[str, str],
    cornell_key: Optional[str],
    gh_token: Optional[str],
    team: Optional[str],
) -> dict:
    """Return a new env dict: `base` plus identity and any secrets that are set."""
    extra = {
        "LAB_USER": identity.netid,
        "GIT_AUTHOR_NAME": identity.name,
        "GIT_COMMITTER_NAME": identity.name,
        "GIT_AUTHOR_EMAIL": identity.email,
        "GIT_COMMITTER_EMAIL": identity.email,
    }
    optional = {"CORNELL_AI_API_KEY": cornell_key, "GH_TOKEN": gh_token, "LAB_TEAM": team}
    return {**base, **extra, **{k: v for k, v in optional.items() if v}}
