#!/usr/bin/env bash
# Run GCD trajectory batch detached from the terminal (survives SSH/Cursor disconnect).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
LOG="${BATCH_LOG:-/data/tmp/gcd_batch_1000.log}"
PIDFILE="${BATCH_PIDFILE:-/data/tmp/gcd_batch.pid}"
LIMIT="${BATCH_LIMIT:-1000}"
JOBS="${BATCH_JOBS:-8}"

cd "$ROOT"

if [[ -f "$PIDFILE" ]]; then
  old_pid="$(cat "$PIDFILE")"
  if kill -0 "$old_pid" 2>/dev/null; then
    echo "Batch already running (pid $old_pid). Log: $LOG"
    exit 1
  fi
fi

{
  echo "=== GCD batch start $(date -Iseconds) limit=$LIMIT jobs=$JOBS ==="
  complete="$(ls "$ROOT/../../flow/logs/nangate45/gcd/ppa_"*/6_report.json 2>/dev/null | wc -l)"
  echo "complete_at_start=$complete"
} >> "$LOG"

nohup setsid "$ROOT/.venv/bin/python" run_trajectories.py \
  --design gcd \
  --jobs "$JOBS" \
  --skip-existing \
  --limit "$LIMIT" \
  >> "$LOG" 2>&1 &

echo $! > "$PIDFILE"
echo "Started pid $(cat "$PIDFILE") — log: $LOG"
echo "Monitor: tail -f $LOG"
echo "Count:   ls flow/logs/nangate45/gcd/ppa_*/6_report.json | wc -l"
