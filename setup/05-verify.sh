#!/usr/bin/env bash
# Step 05: health check.
set -euo pipefail
. "$(dirname "$0")/lib.sh"
load_lab_env
"$LAB_KIT/bin/lab-status"
