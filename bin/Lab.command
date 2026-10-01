#!/usr/bin/env bash
# Double-click to open the lab project manager (no terminal commands needed).
# shellcheck disable=SC1091
source "${LAB_ROOT:-/Users/Shared/lab-llm}/kit/config/lab.env"
exec "$LAB_KIT/bin/lab-ui"
