#!/usr/bin/env bash
# =============================================================================
# Lab LLM kit installer for the Mac Studio.
#
#   ./install.sh            run every step (safe to re-run; each step is idempotent)
#   ./install.sh 03 04      run only the named steps
#   LAB_YES=1 ./install.sh  answer "yes" to every prompt
#
# Run from the shared lab macOS account. Steps 01–02 need that account to be an
# administrator (Homebrew). See docs/ADMIN_GUIDE.md.
# =============================================================================
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=setup/lib.sh
. "$here/setup/lib.sh"

steps=(01-prereqs 02-install-tools 03-configure 04-models 05-verify)
[ $# -gt 0 ] && steps=("$@")

require_macos_arm

for s in "${steps[@]}"; do
  f=$(ls "$here"/setup/"$s"*.sh 2>/dev/null | head -1) || true
  [ -n "$f" ] || die "No setup step matching '$s'"
  step "$(basename "$f" .sh)"
  bash "$f"
done

echo
bold "Done. Open a NEW terminal window, then run:  lab status"
