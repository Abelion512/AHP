#!/usr/bin/env bash
# Integration point for the opt-in auto-fix lane.
# This script is reached only when AUTOFIX_ENABLED=true and after the PR passed
# fail-closed eligibility. It never runs code from the PR itself.
set -euo pipefail

task_file="$1"

if [[ -z "${AUTOFIX_API_KEY:-}" ]]; then
  echo 'Auto-fix skipped: AUTOFIX_API_KEY is not set.'
  exit 0
fi

runtime="$GITHUB_WORKSPACE/hermes-core/.venv/bin/hermes"
if [[ ! -x "$runtime" ]]; then
  echo 'Pinned Hermes runtime is missing; refusing to run an unpinned agent.' >&2
  exit 1
fi

export OPENAI_API_KEY="$AUTOFIX_API_KEY"
"$runtime" -z "$(cat "$task_file")" --yolo
