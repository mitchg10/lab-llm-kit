#!/usr/bin/env bash
# Step 03: shell environment, Ollama service, shared LM Studio folder,
# then `lab-sync` (constitution + skills + agent configs).
set -euo pipefail
. "$(dirname "$0")/lib.sh"
load_brew
KIT="$LAB_ROOT/kit"

# ---- Shell environment ------------------------------------------------------
ensure_block "$HOME/.zshrc" "lab-llm-kit" "[ -f \"$KIT/config/lab.env\" ] && source \"$KIT/config/lab.env\""
ok "~/.zshrc sources $KIT/config/lab.env"
load_lab_env

# ---- Ollama as a LaunchAgent (shared model store, localhost only) ------------
if pgrep -xq Ollama; then
  warn "The Ollama menu-bar app is running. Quit it and remove it from Login Items —"
  warn "the lab uses its own background service so settings are consistent."
fi
brew services stop ollama >/dev/null 2>&1 || true
plist="$HOME/Library/LaunchAgents/edu.lab.ollama.plist"
mkdir -p "$(dirname "$plist")"
sed -e "s#__OLLAMA_BIN__#$(command -v ollama)#g" -e "s#__LAB_ROOT__#$LAB_ROOT#g" \
    "$KIT/config/edu.lab.ollama.plist" > "$plist"
launchctl bootout "gui/$(id -u)/edu.lab.ollama" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$plist"
for _ in $(seq 1 20); do curl -fsS "$OLLAMA_BASE_URL/api/version" >/dev/null 2>&1 && break; sleep 1; done
curl -fsS "$OLLAMA_BASE_URL/api/version" >/dev/null && ok "Ollama service running on $OLLAMA_HOST (models in $OLLAMA_MODELS)" \
  || warn "Ollama did not answer yet — check $LAB_ROOT/logs/ollama.log"

# ---- LM Studio: point its model folder at the shared store ------------------
lmdir="$HOME/.lmstudio/models"
if [ -L "$lmdir" ]; then ok "LM Studio models folder already linked → $(readlink "$lmdir")"
else
  mkdir -p "$HOME/.lmstudio"
  if [ -d "$lmdir" ] && [ -n "$(ls -A "$lmdir" 2>/dev/null)" ]; then
    info "Moving existing LM Studio models into the shared store"
    rsync -a "$lmdir"/ "$LMSTUDIO_MODELS"/ && rm -rf "$lmdir"
  else
    rm -rf "$lmdir"
  fi
  ln -s "$LMSTUDIO_MODELS" "$lmdir"
  ok "LM Studio models folder → $LMSTUDIO_MODELS"
fi
info "In LM Studio: My Models › models directory should show $LMSTUDIO_MODELS (or ~/.lmstudio/models)."
if [ -x "$HOME/.lmstudio/bin/lms" ]; then
  "$HOME/.lmstudio/bin/lms" bootstrap >/dev/null 2>&1 || true
  ok "lms CLI available"
else
  warn "Open LM Studio once, then re-run './install.sh 03' to enable the 'lms' command."
fi

# ---- Constitution, skills, agent configs -----------------------------------
"$KIT/bin/lab-sync"
