#!/usr/bin/env bash
# Ibex fixed-CLK (2.2 ns) LHS sweep — detached from terminal.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
LOG="${BATCH_LOG:-/data/tmp/ibex_fixedclk250.log}"
PIDFILE="${BATCH_PIDFILE:-/data/tmp/ibex_fixedclk250.pid}"
MANIFEST="${BATCH_MANIFEST:-trajectories_ibex_fixedclk250_v3.json}"
LIMIT="${BATCH_LIMIT:-250}"
JOBS="${BATCH_JOBS:-6}"
SEED="${BATCH_SEED:-46}"

cd "$ROOT"

if [[ -f "$PIDFILE" ]]; then
  old_pid="$(cat "$PIDFILE")"
  if kill -0 "$old_pid" 2>/dev/null; then
    echo "Ibex batch already running (pid $old_pid). Log: $LOG"
    exit 1
  fi
fi

echo "Generating ibex fixed-CLK manifest ($LIMIT trajectories, CLK=2.2 ns, seed=$SEED)..."
"$ROOT/.venv/bin/python" perturbations_diverse.py \
  --design ibex \
  -n "$LIMIT" \
  --seed "$SEED" \
  --strict \
  --manifest-name "$MANIFEST" \
  --id-prefix traj_ibex_fclk3

{
  echo "=== Ibex fixed-CLK batch start $(date -Iseconds) limit=$LIMIT jobs=$JOBS manifest=$MANIFEST ==="
  complete="$(find "$ROOT/../../flow/logs/nangate45/ibex" -maxdepth 2 -path '*/ppa_traj_ibex_fclk3_*/2_1_floorplan.json' 2>/dev/null | wc -l)"
  echo "ibex_fclk3_floorplan_at_start=$complete"
} >> "$LOG"

nohup setsid "$ROOT/.venv/bin/python" run_trajectories.py \
  --design ibex \
  --manifest "$MANIFEST" \
  --target floorplan \
  --jobs "$JOBS" \
  --skip-existing \
  >> "$LOG" 2>&1 &
batch_pid=$!
echo "$batch_pid" > "$PIDFILE"
echo "Started ibex batch pid $batch_pid — log: $LOG"
echo "Monitor: tail -f $LOG"
echo "Count:   find $ROOT/../../flow/logs/nangate45/ibex -path '*/ppa_traj_ibex_fclk3_*/2_1_floorplan.json' | wc -l"
