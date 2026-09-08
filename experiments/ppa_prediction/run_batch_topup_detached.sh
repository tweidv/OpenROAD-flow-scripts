#!/usr/bin/env bash
# Top-up LHS batch: retry failed IDs + extra strict trajectories (detached).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
LOG="${BATCH_LOG:-/data/tmp/gcd_lhs_topup.log}"
PIDFILE="${BATCH_PIDFILE:-/data/tmp/gcd_lhs_topup.pid}"
MANIFEST="${BATCH_MANIFEST:-trajectories_lhs_topup.json}"
JOBS="${BATCH_JOBS:-8}"
EXTRA_N="${BATCH_EXTRA_N:-100}"

cd "$ROOT"

if [[ -f "$PIDFILE" ]]; then
  old_pid="$(cat "$PIDFILE")"
  if kill -0 "$old_pid" 2>/dev/null; then
    echo "Top-up batch already running (pid $old_pid). Log: $LOG"
    exit 1
  fi
fi

echo "Generating top-up manifest (failed retries + $EXTRA_N new strict)..."
"$ROOT/.venv/bin/python" perturbations_diverse.py --topup --extra-n "$EXTRA_N" --out-dir "$ROOT/generated/gcd"

COMPLETE=$(find "$ROOT/../../flow/logs/nangate45/gcd" -path '*/ppa_traj_lhs_*/6_report.json' 2>/dev/null | wc -l)
{
  echo "=== LHS top-up start $(date -Iseconds) jobs=$JOBS manifest=$MANIFEST ==="
  echo "complete_at_start=$COMPLETE"
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
