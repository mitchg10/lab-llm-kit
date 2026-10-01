# Skills guide: one skill, every agent

A **skill** is a folder containing a `SKILL.md` file, and optionally some scripts or reference files. It teaches an agent how to do one kind of task. Claude Code, Codex, Gemini CLI and OpenCode all support the same open [Agent Skills](https://agentskills.io) format. So the lab writes each skill once and links it into every agent.

## How the linking works

```
$LAB_KIT/skills/<name>/          reviewed lab skills (in git)
$LAB_ROOT/skills-local/<name>/   experiments, not yet reviewed
        │  lab sync
        ├──► ~/.agents/skills/<name>   read by Codex, Gemini CLI, OpenCode
        └──► ~/.claude/skills/<name>   read by Claude Code
```

The links point at the source folders, so **an edit to a skill takes effect in each agent's next session**. You only need `lab sync` when you **add, rename or remove** a skill. OpenCode also scans `~/.claude/skills`, so lab.env turns that off (`OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1`) to avoid listing every skill twice.

At session start, each agent reads only the `name` and `description` of every skill. It loads the full `SKILL.md` when a task matches the description, or when you ask for the skill by name. That's why **the description is the most important line in the file.**

## Writing a new skill

```bash
cp -R "$LAB_KIT/skills/_template" "$LAB_ROOT/skills-local/interview-summary"
open -e "$LAB_ROOT/skills-local/interview-summary/SKILL.md"    # or any editor
lab sync
```

The rules:
1. The folder name and `name:` must match exactly: lowercase letters, digits and hyphens.
2. `description:` says **what** the skill does and **when** to use it, in the words users actually type. For example: *"Summarise a de-identified interview transcript into a contact summary sheet. Use when a user asks for an interview summary, contact summary or case memo."*
3. Keep `SKILL.md` under about 150 lines. Put long material, like codebooks or examples, in extra files next to it and link them.
4. Scripts go in `scripts/` and should use `uv run` (with inline dependencies) or `labllm`, never a bare `pip install`.
5. **Don't put participant data, real names or keys in a skill.** Skills are shared with every agent and every lab member. Examples must be synthetic.
6. Start from `lab-data-privacy` for any skill that touches data. You can say "first follow the lab-data-privacy skill".

**Test it** by opening a fresh session in each agent and asking something that should trigger the skill:
- Claude Code: `/skills`
- Gemini CLI: `/skills list`
- Codex and OpenCode: ask *"what skills do you have?"*

If the agent doesn't pick the skill up, improve the description.

## Promoting a skill to the lab set

When a `skills-local` skill has proved useful:
1. Move it into `kit/skills/`, in a branch or pull request if the kit is in git.
2. Have someone else read it. Check that it has no data, and that it doesn't contradict the constitution.
3. Merge, then run `lab update` (or `lab sync`) on the Mac.

## Changing the constitution

1. Edit `kit/constitution/LAB_CONSTITUTION.md`, and `DEFAULT_CHAT_PROMPT.md` if the default chat prompt should change too.
2. Record the change in the table at the end, including who approved it.
3. Run `lab sync`. This rebuilds `build/AGENTS.md`, which every agent links to.
4. If `DEFAULT_CHAT_PROMPT.md` changed, rebuild the Ollama chat variants with `lab-models make-lab-variants`, and update the LM Studio preset by hand. API users are unaffected, because their own prompts are what gets sent.

## Per-project instructions

For instructions that apply to one project only, edit the `AGENTS.md` that `lab new` puts in the project folder. It's versioned with the project. Codex and OpenCode read it directly. For Claude Code, add a `CLAUDE.md` containing `@AGENTS.md`, or a symlink. Project skills can go in `<project>/.agents/skills/` (Codex, Gemini, OpenCode) or `<project>/.claude/skills/` (Claude Code). The lab constitution still applies on top of both.
