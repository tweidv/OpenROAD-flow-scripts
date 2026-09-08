#!/usr/bin/env bash
# Run expanded sweep, rebuild dataset, retrain.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
EXP="$ROOT/experiments/ppa_prediction"
JOBS="${1:-8}"

source "$ROOT/env.sh"
source "$ROOT/dev_env.sh"
export TMPDIR="${TMPDIR:-/data/tmp}"

cd "$EXP"
echo "[1/3] Running trajectories (jobs=$JOBS, skip-existing)..."
.venv/bin/python3 run_trajectories.py --jobs "$JOBS" --skip-existing

echo "[2/3] Building dataset..."
.venv/bin/python3 build_dataset.py

echo "[3/3] Training..."
.venv/bin/python3 train.py

echo "Done. See $EXP/output/"
