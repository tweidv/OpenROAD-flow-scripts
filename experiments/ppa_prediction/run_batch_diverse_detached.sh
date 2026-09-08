#!/usr/bin/env bash
# LHS diverse sweep (250 trajectories) — detached from terminal (survives Cursor/SSH disconnect).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
LOG="${BATCH_LOG:-/data/tmp/gcd_lhs250.log}"
PIDFILE="${BATCH_PIDFILE:-/data/tmp/gcd_lhs250.pid}"
MANIFEST="${BATCH_MANIFEST:-trajectories_lhs250.json}"
LIMIT="${BATCH_LIMIT:-250}"
JOBS="${BATCH_JOBS:-8}"
SEED="${BATCH_SEED:-43}"

cd "$ROOT"

if [[ -f "$PIDFILE" ]]; then
  old_pid="$(cat "$PIDFILE")"
  if kill -0 "$old_pid" 2>/dev/null; then
    echo "LHS batch already running (pid $old_pid). Log: $LOG"
    exit 1
  fi
fi

echo "Generating manifest ($LIMIT trajectories, seed=$SEED)..."
"$ROOT/.venv/bin/python" perturbations_diverse.py -n "$LIMIT" --seed "$SEED" --out-dir "$ROOT/generated/gcd"

{
  echo "=== GCD LHS batch start $(date -Iseconds) limit=$LIMIT jobs=$JOBS manifest=$MANIFEST ==="
  complete="$(find "$ROOT/../../flow/logs/nangate45/gcd" -maxdepth 2 -path '*/ppa_traj_lhs_*/6_report.json' 2>/dev/null | wc -l)"
  echo "lhs_complete_at_start=$complete"
} >> "$LOG"

nohup setsid "$ROOT/.venv/bin/python" run_trajectories.py \
  --design gcd \
  --manifest "$MANIFEST" \
  --jobs "$JOBS" \
  --skip-existing \
  >> "$LOG" 2>&1 &
batch_pid=$!
echo "$batch_pid" > "$PIDFILE"
echo "Started pid $batch_pid — log: $LOG"
echo "Monitor: tail -f $LOG"
echo "Count:   ls $ROOT/../../flow/logs/nangate45/gcd/ppa_traj_lhs_*/6_report.json 2>/dev/null | wc -l"
