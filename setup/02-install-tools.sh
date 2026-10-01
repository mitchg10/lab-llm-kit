#!/usr/bin/env bash
# Step 02: install every tool through a manager.
#   Homebrew -> Ollama, LM Studio, git, gh (GitHub CLI), jq
#   nvm      -> Node LTS -> OpenCode, Claude Code, Codex, Gemini CLI
#   uv       -> Python, Hugging Face CLI, mlx-lm, labllm
set -euo pipefail
. "$(dirname "$0")/lib.sh"
load_brew

NVM_VERSION="${NVM_VERSION:-v0.40.3}"
NPM_AGENTS=(opencode-ai @anthropic-ai/claude-code @openai/codex @google/gemini-cli)
PY_VERSION="${PY_VERSION:-3.12}"

# ---- Homebrew packages ------------------------------------------------------
brew install git gh jq ollama
if [ -d "/Applications/LM Studio.app" ]; then ok "LM Studio already installed"
else brew install --cask lm-studio; fi
# We run Ollama from our own LaunchAgent (step 03) — make sure brew's isn't also running.
brew services stop ollama >/dev/null 2>&1 || true
ok "Homebrew packages: $(ollama --version 2>/dev/null | tail -1)"

# ---- nvm + Node LTS + agent CLIs --------------------------------------------
load_nvm
if ! have nvm; then
  info "Installing nvm $NVM_VERSION"
  PROFILE=/dev/null bash -c "$(curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/$NVM_VERSION/install.sh)"
  load_nvm
fi
nvm install --lts >/dev/null
nvm alias default 'lts/*' >/dev/null
nvm use default >/dev/null
ok "Node $(node --version) via nvm"

for pkg in "${NPM_AGENTS[@]}"; do
  info "npm -g $pkg"
  npm install -g --no-fund --no-audit "$pkg@latest" >/dev/null
done
ok "Agents: opencode $(opencode --version 2>/dev/null || echo '?'), claude $(claude --version 2>/dev/null | awk '{print $1}'), codex $(codex --version 2>/dev/null | awk '{print $NF}'), gemini $(gemini --version 2>/dev/null || echo '?')"

# ---- uv + Python tools ------------------------------------------------------
export PATH="$HOME/.local/bin:$PATH"
if ! have uv; then
  info "Installing uv"
  curl -LsSf https://astral.sh/uv/install.sh | env UV_NO_MODIFY_PATH=1 sh
fi
uv self update >/dev/null 2>&1 || true
uv python install "$PY_VERSION" >/dev/null
ok "uv $(uv --version | awk '{print $2}'), Python $PY_VERSION"

uv tool install --force "huggingface_hub[cli]" >/dev/null   # provides `hf`
uv tool install --force mlx-lm >/dev/null                   # mlx_lm.generate / mlx_lm.server
uv tool install --force --editable "$LAB_ROOT/kit/labllm" >/dev/null   # provides `labllm`
ok "uv tools: hf, mlx-lm, labllm"
