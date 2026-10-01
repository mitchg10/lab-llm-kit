#!/usr/bin/env bash
# Step 01: Xcode command-line tools, Homebrew, and the shared lab folder.
set -euo pipefail
. "$(dirname "$0")/lib.sh"
require_macos_arm

info "macOS $(sw_vers -productVersion), $(sysctl -n hw.memsize | awk '{printf "%.0f GB", $1/1073741824}') unified memory"

# Xcode Command Line Tools (git, compilers needed by some Python wheels)
if xcode-select -p >/dev/null 2>&1; then ok "Xcode command-line tools present"
else
  info "Installing Xcode command-line tools (a macOS dialog will appear)…"
  xcode-select --install || true
  read -r -p "  Press Return once the Command Line Tools install has finished… " _
fi

# Homebrew: only used for Ollama, LM Studio and a few CLI utilities.
load_brew
if have brew; then ok "Homebrew present ($(brew --version | head -1))"
else
  info "Installing Homebrew (you'll be asked for this account's password)…"
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  load_brew
fi
ensure_block "$HOME/.zprofile" "homebrew" 'eval "$(/opt/homebrew/bin/brew shellenv)"'

# Shared lab root (under /Users/Shared so a later move to per-person accounts is painless)
if [ ! -d "$LAB_ROOT" ]; then
  info "Creating $LAB_ROOT (admin password may be requested)…"
  mkdir -p "$LAB_ROOT" 2>/dev/null || sudo mkdir -p "$LAB_ROOT"
fi
[ -w "$LAB_ROOT" ] || sudo chown "$(id -un)":staff "$LAB_ROOT"
mkdir -p "$LAB_ROOT"/{models/{ollama,huggingface,lmstudio},logs,skills-local,build,backups}
ok "Lab root ready at $LAB_ROOT"

# Research projects live OUTSIDE the lab-llm tree (each is its own git repo)
LAB_PROJECTS="$(LAB_ROOT="$LAB_ROOT" bash -c '. "$1/config/lab.env" >/dev/null 2>&1; echo "$LAB_PROJECTS"' _ "$KIT_SRC")"
LAB_PROJECTS="${LAB_PROJECTS:-/Users/Shared/research}"
[ -d "$LAB_PROJECTS" ] || mkdir -p "$LAB_PROJECTS" 2>/dev/null || sudo mkdir -p "$LAB_PROJECTS"
[ -w "$LAB_PROJECTS" ] || sudo chown "$(id -un)":staff "$LAB_PROJECTS"
ok "Projects folder ready at $LAB_PROJECTS"

# Copy the kit into place (skip if we're already running from there)
if [ "$KIT_SRC" != "$LAB_ROOT/kit" ]; then
  if [ -d "$LAB_ROOT/kit/.git" ]; then
    warn "$LAB_ROOT/kit is a git checkout — leaving it alone. Run setup from there."
  else
    info "Copying kit to $LAB_ROOT/kit"
    mkdir -p "$LAB_ROOT/kit"
    rsync -a --delete --exclude '.venv' --exclude '__pycache__' "$KIT_SRC"/ "$LAB_ROOT/kit"/
  fi
fi
chmod +x "$LAB_ROOT"/kit/bin/* "$LAB_ROOT"/kit/install.sh "$LAB_ROOT"/kit/setup/*.sh
ok "Kit installed at $LAB_ROOT/kit"

# FileVault check (data at rest)
if fdesetup status 2>/dev/null | grep -q "On"; then ok "FileVault is on"
else warn "FileVault appears OFF. Turn it on in System Settings › Privacy & Security."; fi
