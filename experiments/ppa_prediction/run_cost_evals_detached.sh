#!/usr/bin/env bash
# Cost-aware search eval for 100/900 and 20/980 splits (detached).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
LOG="${EVAL_LOG:-/data/tmp/gcd_eval_cost_runs.log}"
PIDFILE="${EVAL_PIDFILE:-/data/tmp/gcd_eval_cost.pid}"
LIMIT="${EVAL_LIMIT:-1000}"
PY="$ROOT/.venv/bin/python"
SUMMARY="$ROOT/output/gcd/checkpoint_tally_summary.md"

if [[ -f "$PIDFILE" ]]; then
  old_pid="$(cat "$PIDFILE")"
  if kill -0 "$old_pid" 2>/dev/null; then
    echo "Cost eval pipeline already running (pid $old_pid). Log: $LOG"
    exit 1
  fi
fi

{
  echo "=== cost-aware eval pipeline start $(date -Iseconds) limit=$LIMIT ==="
  cd "$ROOT"

  for TRAIN in 100 20; do
    TEST=$((LIMIT - TRAIN))
    OUT="output/gcd/search_eval/split_${TRAIN}_${TEST}_cost"
    echo "--- search_eval train=$TRAIN test=$TEST (with checkpoint costs) ---"
    MPLBACKEND=Agg "$PY" search_eval.py \
      --design gcd --limit "$LIMIT" --train-size "$TRAIN" --n-random 1000 \
      --out-dir "$OUT"
  done

  echo "--- writing checkpoint tally summary ---"
  "$PY" - <<'PY'
import json
from pathlib import Path

root = Path(".")
lines = [
    "# Checkpoint tally summary (cost-aware search eval)",
    "",
    "Default stage costs: floorplan=2, placement=4, cts=2, routing=3 (11 per full run).",
    "",
]
for train in (100, 20):
    test = 1000 - train
    p = root / f"output/gcd/search_eval/split_{train}_{test}_cost/search_eval.json"
    if not p.exists():
        lines.append(f"## {train}/{test} — NOT RUN")
        continue
    r = json.loads(p.read_text())
    mg = r["model_guided"]["checkpoint_accounting"]
    rc = r["random_cost"]
    lines += [
        f"## {train} train / {test} test",
        "",
        f"Optimum: `{r['optimum_trajectory']}` V={r['true_optimum']:.4f}",
        "",
        "### Model-guided checkpoint tally",
        "",
        "| Stage | Count | Unit cost | Subtotal |",
        "|-------|------:|----------:|---------:|",
    ]
    for stage in ("floorplan", "placement", "cts", "routing"):
        c = mg["checkpoint_tally"][stage]
        u = mg["stage_costs"][stage]
        lines.append(f"| {stage} | {c} | {u:.1f} | {c * u:.1f} |")
    lines += [
        f"| **TOTAL** | **{mg['total_checkpoints']}** | | **{mg['cumulative_cost']:.1f}** |",
        "",
        "### Cost to reach thresholds",
        "",
        "| Strategy | Cost →90% | Cost →95% | Cost →99% |",
        "|----------|----------:|----------:|----------:|",
    ]
    for key, label in [("random_cost", "Random"), ("model_guided_cost", "Model-guided")]:
        s = r[key]
        c90 = s["cost_to_90pct"]["mean"]
        c95 = s["cost_to_95pct"]["mean"]
        c99 = s["cost_to_99pct"]["mean"]
        lines.append(
            f"| {label} | {c90:.1f} | {c95:.1f} | {c99:.1f} |"
        )
    rt = rc["checkpoint_tally_mean"]
    lines += [
        "",
        "### Random (mean) checkpoint tally per full search",
        "",
        "| Stage | Mean count |",
        "|-------|----------:|",
    ]
    for stage in ("floorplan", "placement", "cts", "routing"):
        lines.append(f"| {stage} | {rt[stage]:.0f} |")
    lines.append("")
    lines.append(f"Mean total cost (all {test} full evals): {rc['cumulative_cost_mean']:.1f}")
    lines.append("")

Path("output/gcd/checkpoint_tally_summary.md").write_text("\n".join(lines))
print("Wrote output/gcd/checkpoint_tally_summary.md")
PY

  echo "=== cost-aware eval pipeline end $(date -Iseconds) exit=0 ==="
} >> "$LOG" 2>&1 &

echo $! > "$PIDFILE"
echo "Started cost eval pipeline pid $(cat "$PIDFILE") — log: $LOG"
