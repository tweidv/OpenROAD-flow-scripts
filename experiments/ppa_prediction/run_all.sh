#!/usr/bin/env bash
# End-to-end PPA prediction experiment on GCD.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
EXP="$ROOT/experiments/ppa_prediction"
cd "$ROOT"

source env.sh
source dev_env.sh
export TMPDIR="${TMPDIR:-/data/tmp}"

python3 -m venv "$EXP/.venv" 2>/dev/null || true
"$EXP/.venv/bin/pip" install -q -r "$EXP/requirements.txt"

cd "$EXP"
"$EXP/.venv/bin/python3" run_trajectories.py "$@"
"$EXP/.venv/bin/python3" build_dataset.py
"$EXP/.venv/bin/python3" train.py

echo "Results: $EXP/output/"
