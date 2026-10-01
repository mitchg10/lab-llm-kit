# Project instructions for AI agents

This is a research project in its own git repository. The lab's global instructions and skills also apply.

## Layout
- `data/` holds de-identified inputs. It is git-ignored. **Run `lab scan <file>` before reading anything in here.**
- `outputs/` holds model outputs and call logs. It is git-ignored.
- `prompts/` holds system prompts and user-prompt templates. These are versioned; don't edit a used prompt, create `_v2` instead.
- `notebooks/` holds analysis notebooks. Outputs are stripped on commit.

## Conventions
- Python through uv only: `uv add <pkg>`, `uv run <script>`.
- Models through `labllm`. It sends only the prompts in `prompts/`, with no hidden system prompt.
- Commit small, meaningful steps with clear messages. Never commit data, outputs, keys or anything the pre-commit hook blocks. If the hook reports possible identifiers, stop and tell the user.
- Record every model run that might be reported in the README methods log, including the commit hash.
