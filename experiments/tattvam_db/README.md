# Tattvam local mirror

Pulls the silicompiler API behind [tattvam-ui.ngrok.dev](https://tattvam-ui.ngrok.dev/) (`tattvam-server.ngrok.dev`) into SQLite on this machine.

Stored: run configs, every candidate's full knob dict, param diffs, stage Tcl, executed/proposed tool calls + stdout, per-stage metrics, exploration outcomes. Dropped: LLM reasoning, expected-outcome prose, eval writeups.

## Sync

```bash
python3 experiments/tattvam_db/sync.py
```

Finished runs are cached under `cache/`. The live run is always re-fetched. Use `--force` to refresh everything, `--no-eval` to skip the bulky eval sidecar, `--only RUN_ID ...` to pull one run.

## Query

```bash
sqlite3 experiments/tattvam_db/data/tattvam.sqlite
```

Useful starting points: `v_candidate_wide`, `candidate_params`, `param_changes`, `tool_calls`, `metrics`.

## Knob screening (Gate 1 + 2)

Standalone from PPA prediction — screens which knobs matter using only this DB:

```bash
python3 experiments/tattvam_db/knob_screen.py
python3 experiments/tattvam_db/knob_screen.py --design gcd --stage floorplan
```

Outputs: `output/knob_screen_report.md`, `output/knob_screen_all.csv` (per metric detail).

**Full design × stage grid** (best verdict per knob, all metrics aggregated):

```bash
python3 experiments/tattvam_db/knob_screen.py   # also writes knob_grid_*.csv/md
```

- `output/knob_grid_report.md` — tables: knob × (gcd, aes, jpeg) for each stage
- `output/knob_grid_summary.csv` — wide pivot (columns `gcd@floorplan`, …)
- `output/knob_grid_agg.csv` — one row per knob × design × stage with best ρ


- **Gate 1:** stage reach (`knob_stage_map.py`) — is the knob applied by this checkpoint?
- **Gate 2:** Spearman ρ vs floorplan/place/… metrics — does the label move when the knob moves?

