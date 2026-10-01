#!/usr/bin/env bash
# Shared helpers for setup scripts. Sourced, not run.

KIT_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export LAB_ROOT="${LAB_ROOT:-/Users/Shared/lab-llm}"

bold() { printf '\033[1m%s\033[0m\n' "$*"; }
info() { printf '  \033[34m•\033[0m %s\n' "$*"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$*"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$*" >&2; }
die()  { printf '  \033[31m✗\033[0m %s\n' "$*" >&2; exit 1; }
step() { echo; bold "== $* =="; }

have() { command -v "$1" >/dev/null 2>&1; }

confirm() {  # confirm "question" -> 0 if yes. LAB_YES=1 answers yes automatically.
  [ "${LAB_YES:-0}" = 1 ] && return 0
  read -r -p "  ? $1 [y/N] " ans
  [[ "$ans" =~ ^[Yy] ]]
}

require_macos_arm() {
  [ "$(uname -s)" = Darwin ] || die "This kit targets macOS (Mac Studio). Detected $(uname -s)."
  [ "$(uname -m)" = arm64 ]  || die "Apple Silicon (arm64) required. Detected $(uname -m)."
}

load_brew() {
  if [ -x /opt/homebrew/bin/brew ]; then eval "$(/opt/homebrew/bin/brew shellenv)"; fi
}

load_nvm() {
  export NVM_DIR="$HOME/.nvm"
  # shellcheck disable=SC1091
  [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
}

load_lab_env() {
  load_brew; load_nvm
  export PATH="$HOME/.local/bin:$PATH"
  # shellcheck disable=SC1091
  [ -f "$LAB_ROOT/kit/config/lab.env" ] && . "$LAB_ROOT/kit/config/lab.env"
}

# Write a block between markers into a file, replacing any earlier copy.
ensure_block() {  # ensure_block FILE TAG CONTENT
  local file="$1" tag="$2" content="$3" tmp
  touch "$file"
  tmp="$(mktemp)"
  awk -v s="# >>> $tag >>>" -v e="# <<< $tag <<<" '
    $0==s {skip=1; next} $0==e {skip=0; next} !skip {print}' "$file" > "$tmp"
  { cat "$tmp"; printf '# >>> %s >>>\n%s\n# <<< %s <<<\n' "$tag" "$content" "$tag"; } > "$file"
  rm -f "$tmp"
}
