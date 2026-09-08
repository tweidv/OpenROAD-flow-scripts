# OpenROAD / ORFS Full Metrics Inventory (GCD, 1000 trajectories)

**Generated offline** from existing `flow/logs/` JSON metrics + `trajectories.json` parameters.  
**No new OpenROAD runs.**

## Scope

This inventory covers **everything ORFS currently writes as structured JSON metrics** per flow stage, plus **all 8 swept trajectory parameters** and `clock_period.txt`.

It does **not** include:
- Unstructured text inside `.rpt` report files (timing path dumps, DRC details, etc.)
- Binary/WEBP artifacts, ODB contents, netlists
- Metrics from designs/stages that never ran `report_metrics` in this flow

For GCD with the standard ORFS metric JSON export, the complete universe is **476 rows** — not millions, but much larger than the 13 hand-picked features.

## Totals

| Source | Metrics |
|--------|--------:|
| Configuration params (`trajectories.json`) | 8 |
| `1_synth.json` | 19 |
| Floorplan JSONs (2_1 … 2_4) | 53 |
| Placement JSONs (3_1 … 3_5) | 151 |
| `4_1_cts.json` | 55 |
| Global route + route JSONs (5_1 … 5_3) | 116 |
| Finish JSONs (6_1, 6_report) | 73 |
| `clock_period.txt` | 1 |
| **Total unique (file, key) pairs** | **476** |

**Currently used in `features.py`:** ~13 engineered features (57 JSON keys partially overlap via suffix matching).

## By metric category (prefix)

| Category | Count |
|----------|------:|
| routing | 112 |
| placement | 95 |
| finish | 70 |
| cts | 55 |
| placeopt (resizer) | 43 |
| floorplan | 38 |
| flow | 23 |
| synthesis | 19 |
| configuration | 8 |
| other | 13 |

## Configuration parameters (all trajectories)

| Parameter | Unique values | Range |
|-----------|--------------:|-------|
| CORE_UTILIZATION | 32 | 35–90 |
| CLK_PERIOD | 51 | 0.10–0.62 ns |
| CORE_ASPECT_RATIO | 11 | 0.5–2.0 |
| PLACE_DENSITY_LB_ADDON | 14 | 0.05–0.40 |
| CTS_CLUSTER_SIZE | 8 | 30–200 |
| TNS_END_PERCENT | 5 | 10–100 |
| CELL_PAD_* | 1 | 0 |

## Files

- **`openroad_metrics_inventory_full.csv`** — full list (476 rows): every metric key, source file, stage, category, missing fraction, n_unique, min/max/mean, `currently_extracted` flag
- **`openroad_metrics_by_file.csv`** — counts per JSON file
- **`openroad_metrics_by_category.csv`** — counts per category prefix

## Reproduce

```bash
cd experiments/ppa_prediction
.venv/bin/python inventory_openroad_metrics.py --limit 1000
```

## Next steps (if you want even more)

1. **Parse `.rpt` section headers** from `flow/reports/` (~dozens of report types × many scalar extractions)
2. **Flatten all JSON keys across all intermediate stages** into a wide dataset (476 columns × 1000 trajectories)
3. **Re-run SHAP/ablation** on the full 476-feature set (or per-stage subsets) — expensive but offline
