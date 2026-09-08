#!/usr/bin/env bash
# Smoke-test v2 density-safe manifest (20 trajectories).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
LOG="${BATCH_LOG:-/data/tmp/gcd_fclk2_test20.log}"
PIDFILE="${BATCH_PIDFILE:-/data/tmp/gcd_fclk2_test20.pid}"
MANIFEST="${BATCH_MANIFEST:-trajectories_fixedclk250_v2.json}"
LIMIT="${BATCH_LIMIT:-20}"
JOBS="${BATCH_JOBS:-4}"

cd "$ROOT"

if [[ -f "$PIDFILE" ]]; then
  old_pid="$(cat "$PIDFILE")"
  if kill -0 "$old_pid" 2>/dev/null; then
    echo "v2 test batch already running (pid $old_pid). Log: $LOG"
    exit 1
  fi
fi

{
  echo "=== GCD fclk2 v2 smoke test $(date -Iseconds) limit=$LIMIT manifest=$MANIFEST ==="
} >> "$LOG"

nohup setsid "$ROOT/.venv/bin/python" run_trajectories.py \
  --design gcd \
  --manifest "$MANIFEST" \
  --limit "$LIMIT" \
  --jobs "$JOBS" \
  >> "$LOG" 2>&1 &
batch_pid=$!
echo "$batch_pid" > "$PIDFILE"
echo "Started v2 smoke test pid $batch_pid — log: $LOG"
echo "Monitor: tail -f $LOG"
echo "Full completes: find flow/logs/nangate45/gcd -path '*/ppa_traj_fclk2_*/6_report.json' | wc -l"
echo "GPL density errors: grep -c 'FLW-0024' $LOG"
