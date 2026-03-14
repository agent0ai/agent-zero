#!/usr/bin/env bash
set -euo pipefail

export AGENT_ZERO_LAPTOP_MODE=1
export TIER="${TIER:-free}"
export PERF_SLO_PROFILE="${PERF_SLO_PROFILE:-free}"
export ENABLE_PERSONA_SYSTEMS="${ENABLE_PERSONA_SYSTEMS:-false}"
export MAX_CONCURRENT_SESSIONS="${MAX_CONCURRENT_SESSIONS:-2}"

exec python3 run_ui.py "$@"
