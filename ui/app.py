"""Streamlit app behind `lab ui`. Run via bin/lab-ui, not directly."""
import os
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from lab_ui.git_ops import project_status, save_and_push  # noqa: E402
from lab_ui.notebook_proc import start_notebook, stop_notebook  # noqa: E402
from lab_ui.projects import create_project, list_projects, read_teams, validate_name  # noqa: E402
from lab_ui.session import Identity, subprocess_env  # noqa: E402

KIT = Path(os.environ["LAB_KIT"])
PROJECTS = Path(os.environ["LAB_PROJECTS"])
TEAMS = read_teams(KIT / "config" / "teams.txt")
GITHUB_READY = "[" not in os.environ.get("LAB_GIT_REMOTE_BASE", "[")

st.set_page_config(page_title="Lab projects", page_icon="🧪")


def current_env(team=None) -> dict:
    s = st.session_state
    return subprocess_env(s["identity"], os.environ, s.get("cornell_key"), s.get("gh_token"), team)


def sign_in() -> None:
    st.title("Sign in")
    st.caption("Your details stay in this window only. Nothing is saved to the shared computer.")
    with st.form("signin"):
        netid = st.text_input("NetID").strip().lower()
        name = st.text_input("Full name").strip()
        email = st.text_input("Email (leave blank for NetID@cornell.edu)").strip()
        gh = st.text_input("GitHub token (optional, lets you save to GitHub)", type="password")
        key = st.text_input("Cornell AI key (optional, only for Cornell models)", type="password")
        if st.form_submit_button("Sign in"):
            if not netid or not name:
                st.error("NetID and full name are required.")
                return
            st.session_state["identity"] = Identity(netid, name, email or f"{netid}@cornell.edu")
            st.session_state["gh_token"] = gh or None
            st.session_state["cornell_key"] = key or None
            st.rerun()


def new_project_form() -> None:
    st.subheader("New project")
    with st.form("new"):
        name = st.text_input("Project name", placeholder="my-study")
        team = st.selectbox("Cornell team (who pays for model use)", [""] + TEAMS) if TEAMS else None
        notebook = st.checkbox("Include a starter notebook", value=True)
        github = st.checkbox(
            "Also create a private GitHub repo", value=GITHUB_READY, disabled=not GITHUB_READY,
            help=None if GITHUB_READY else "The lab's GitHub organization isn't set up yet.")
        if st.form_submit_button("Create project"):
            problem = validate_name(name)
            if problem:
                st.error(problem)
                return
            with st.spinner("Setting up your project (the first one takes a few minutes)..."):
                result = create_project(KIT, name, team or None, notebook, github, current_env(team or None))
            (st.success if result.ok else st.error)("Project ready." if result.ok else "Couldn't create it.")
            with st.expander("Details"):
                st.code(result.output)


def project_card(project) -> None:
    key = f"nb-{project.name}"
    env = current_env(project.team)
    with st.container(border=True):
        st.markdown(f"**{project.name}**" + (f" · team `{project.team}`" if project.team else ""))
        status = project_status(project.path, env)
        if status.dirty or status.ahead:
            st.caption(f"{status.dirty} changed file(s), {status.ahead} not yet uploaded")
        else:
            st.caption("All saved" + ("" if status.has_remote else " (this Mac only)"))
        notebook_col, save_col = st.columns(2)
        with notebook_col:
            running = st.session_state.get(key)
            if running is None:
                if st.button("Open notebook", key=f"open-{key}"):
                    with st.spinner("Starting Jupyter..."):
                        started = start_notebook(KIT, project.path, env)
                    if started is None:
                        st.error("The notebook didn't start. Try creating the project with a notebook.")
                    else:
                        st.session_state[key] = started
                        st.rerun()
            else:
                st.link_button("Go to notebook", running.url)
                if st.button("Stop notebook", key=f"stop-{key}"):
                    stop_notebook(running.process)
                    st.session_state.pop(key)
                    st.rerun()
        with save_col:
            message = st.text_input("Note", f"Save from lab UI {datetime.now():%Y-%m-%d %H:%M}",
                                    key=f"msg-{key}", label_visibility="collapsed")
            if st.button("Save to GitHub", key=f"save-{key}"):
                result = save_and_push(project.path, message, env)
                (st.success if result.ok else st.error)(result.message)
                if result.detail:
                    st.code(result.detail)


def main() -> None:
    if "identity" not in st.session_state:
        sign_in()
        return
    who = st.session_state["identity"]
    st.sidebar.write(f"Signed in as **{who.netid}**")
    if st.sidebar.button("Sign out"):
        for running in [v for k, v in st.session_state.items() if k.startswith("nb-")]:
            stop_notebook(running.process)
        st.session_state.clear()
        st.rerun()
    st.title("Lab projects")
    new_project_form()
    st.subheader("My projects")
    projects = list_projects(PROJECTS, who.netid)
    if not projects:
        st.info("No projects yet. Create one above.")
    for project in projects:
        project_card(project)


main()
