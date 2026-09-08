#!/usr/bin/env bash
# Build dataset + search eval for 100/900 and 20/980 splits (detached from terminal).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
LOG="${EVAL_LOG:-/data/tmp/gcd_eval_runs.log}"
PIDFILE="${EVAL_PIDFILE:-/data/tmp/gcd_eval.pid}"
LIMIT="${EVAL_LIMIT:-1000}"
PY="$ROOT/.venv/bin/python"

if [[ -f "$PIDFILE" ]]; then
  old_pid="$(cat "$PIDFILE")"
  if kill -0 "$old_pid" 2>/dev/null; then
    echo "Eval pipeline already running (pid $old_pid). Log: $LOG"
    exit 1
  fi
fi

{
  echo "=== eval pipeline start $(date -Iseconds) limit=$LIMIT ==="
  cd "$ROOT"

  echo "--- build_dataset --limit $LIMIT ---"
  "$PY" build_dataset.py --design gcd --limit "$LIMIT"

  echo "--- search_eval train=100 test=900 ---"
  MPLBACKEND=Agg "$PY" search_eval.py --design gcd --limit "$LIMIT" --train-size 100 --n-random 1000

  echo "--- search_eval train=20 test=980 ---"
  MPLBACKEND=Agg "$PY" search_eval.py --design gcd --limit "$LIMIT" --train-size 20 --n-random 1000

  echo "=== eval pipeline end $(date -Iseconds) exit=0 ==="
} >> "$LOG" 2>&1 &

echo $! > "$PIDFILE"
echo "Started eval pipeline pid $(cat "$PIDFILE") — log: $LOG"
