#!/usr/bin/env bash
# Step 04: download the starter models once, build `lab-` variants with the
# constitution built in, and link everything into LM Studio without copying.
set -euo pipefail
. "$(dirname "$0")/lib.sh"
load_lab_env

list="$LAB_KIT/config/models.txt"
info "Model list: $list"
grep -Ev '^\s*(#|$)' "$list" | sed 's/#.*//' | sed 's/^/    /'
info "Disk free: $(df -h "$LAB_MODELS" | awk 'NR==2{print $4}')"
if confirm "Download these now? (large; can take an hour+)"; then
  lab-models pull-list "$list"
else
  info "Skipped. Later: lab-models pull-list"
fi
lab-models make-lab-variants
lab-models link-lmstudio
"$LAB_KIT/bin/lab-sync" --quiet   # refresh OpenCode's model list
