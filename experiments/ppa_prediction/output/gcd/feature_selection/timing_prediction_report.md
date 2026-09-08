# Timing (Fmax) Prediction — What’s Hard and What Works

**Date:** 2026-09-07  
**Design:** GCD, 1000 trajectories

Related plots: `plots/timing_predictors_by_stage.png`, `plots/checkpoint_fmax_vs_final_fmax_by_stage.png`, `plots/fmax_single_metric_r2_by_stage.png`

---

## Short answer

**Yes — timing is the hard part.** Power and area are almost “read forward” from OpenROAD (`internal_power` r²≈1, `instance_area` r²≈1 at routing). **Fmax is harder because:**

1. At **floorplan**, timing is immature — checkpoint fmax only explains **~66%** of final fmax variance; slack and clock period matter more than at later stages.
2. At **placement → routing**, checkpoint `timing__fmax` becomes a **direct OR read-forward** (r² 0.89–0.98) — same STA engine, less flow left to change timing.
3. **~60% of runs have negative setup slack** at every stage — many configs are timing-violated; predicting *final* fmax requires knowing which ones recover after CTS/opt.

Power/area: OR gives you the answer early. **Timing: OR gives you a provisional answer that may or may not survive the rest of the flow.**

---

## Best single-metric predictors of final_fmax (Pearson r²)

| Stage | internal_power | instance_area | **setup WS** | **checkpoint fmax** |
|-------|---------------:|--------------:|-------------:|--------------------:|
| floorplan | 0.41 | 0.62 | **0.72** | 0.66 |
| placement | 0.42 | 0.73 | 0.68 | **0.89** |
| cts | 0.42 | 0.69 | 0.66 | **0.93** |
| routing | 0.43 | 0.73 | 0.64 | **0.98** |

See bar chart: `plots/fmax_single_metric_r2_by_stage.png`

### By stage — what to use

| Stage | Best OR timing metrics | r vs final_fmax | Notes |
|-------|------------------------|----------------:|-------|
| **Floorplan** | `timing__setup__ws` | −0.85 | Best *intrinsic* timing signal early; also `timing__fmax` (r=+0.81), `param:CLK_PERIOD` (r=−0.86) |
| **Placement** | `timing__fmax` (detailedplace) | +0.94 | Checkpoint fmax ≈ final; slack/TNS add little alone |
| **CTS** | `timing__fmax` | +0.97 | Same; `setup_violation_count`, `setup__tns` secondary |
| **Routing** | `timing__fmax` (globalroute) | +0.99 | Nearly identity — little changes after GRT for timing |

Hand-picked features (test-set validated):
- **CTS fmax:** `inv_fmax`, `total_negative_slack`, `clock_skew` beat FFS compact set (test R² 0.93 vs 0.80)
- **Placement/routing:** `inv_fmax` ≈ 1/checkpoint_fmax; TNS captures violation severity

---

## What the graphs show

### `checkpoint_fmax_vs_final_fmax_by_stage.png`

- **Floorplan:** wide scatter — early STA is noisy; many points off the diagonal.
- **Placement/CTS:** tightening cloud.
- **Routing:** nearly on **y = x** line (r=0.99) — checkpoint fmax *is* final fmax for ranking purposes.

**Expected relationship:** Should approach diagonal as flow completes. Early stages: expect horizontal/vertical smear from configs that recover or degrade.

### `timing_predictors_by_stage.png`

Each row = one stage; columns = top 3 timing metrics vs final fmax (GHz).

- **Floorplan:** setup WS vs fmax — negative slope, two regimes at WS=0.
- **Placement+:** checkpoint fmax — tight positive linear band.
- **TNS:** negative correlation (more violation → lower fmax); useful with slack for violated designs.

### `setup_ws_vs_final_fmax.png` (from earlier)

Slack works at all stages (r≈−0.8) but is **not sufficient alone** when combined with power in FFS — multicollinearity with scale proxies. Still the right *timing quality* indicator when checkpoint fmax isn’t trusted (early floorplan).

---

## Why FFS picked power + setup_ws (not checkpoint fmax)

On the **20-trajectory train / 5-val split**, greedy FFS often picks:
1. `power__internal__total` (design scale)
2. `timing__setup__ws` (timing quality)

Even though **checkpoint fmax** has higher raw correlation at placement+, FFS avoids it because:
- **Collinear with final fmax** — redundant with target once XGBoost already has power
- **Collinear with CLK_PERIOD** sweep parameter
- Small validation set favors complementary features over duplicate timing readouts

For **search ranking at routing**, you may as well use **checkpoint fmax directly** (or `inv_fmax`) — it’s the OR timing report.

---

## Expected vs observed (timing only)

| Relationship | Expected | Observed |
|--------------|----------|----------|
| Checkpoint fmax → final fmax | Diagonal at late stages; noisy early | ✓ r² 0.66 → 0.98 |
| Setup WS → final fmax | Negative; violated configs cluster low | ✓ r≈−0.8 |
| Setup TNS → final fmax | Negative; violation severity | ✓ r≈−0.6 to −0.7 |
| CLK_PERIOD → final fmax | Negative (longer period → lower fmax) | ✓ r≈−0.86 at floorplan |
| Internal power → final fmax | Weak scale proxy only | ✓ r≈0.65 |
| Instance area → final fmax | Weak scale proxy | ✓ r≈0.75–0.85 |

---

## Practical recommendations

### For search ordering

| Stage | Minimal timing feature(s) |
|-------|---------------------------|
| Floorplan | `setup__ws` + `CLK_PERIOD` (or `checkpoint fmax` if available) |
| Placement | `checkpoint fmax` @ detailedplace, or `inv_fmax` |
| CTS | `inv_fmax` + `total_negative_slack` + `clock_skew` (hand-picked wins on test) |
| Routing | `checkpoint fmax` @ globalroute |

### What “hard” means for the project

- **Not hard:** “What’s the fmax if I finish this trajectory?” at routing (read OR’s number).
- **Hard:** “What’s the fmax at floorplan before placement/CTS?” (r²~0.66, 60% violated).
- **Hard:** “Which violated floorplan will recover?” (needs multivariate / ML beyond one metric).
- **Hard:** Generalizing to **new designs** — high r² here is partly same-metric read-forward within one sweep.

### Compact 3-vector still works

For a single representation at every stage:
```
power__internal__total   → power ranking
design__instance__area   → area ranking  
timing__fmax or setup__ws → timing ranking (use fmax after placement)
```

---

## Plot index

| File | Content |
|------|---------|
| `timing_predictors_by_stage.png` | Top 3 timing metrics × 4 stages vs final fmax |
| `checkpoint_fmax_vs_final_fmax_by_stage.png` | OR read-forward gets tighter through flow |
| `fmax_single_metric_r2_by_stage.png` | Bar chart: power/area/slack/fmax r² by stage |
| `setup_ws_vs_final_fmax.png` | Slack vs fmax (all stages overlaid) |
| `internal_power_vs_final_fmax.png` | Scale proxy only (r≈0.65) |

See also: `checkpoint_vs_final_report.md`, `ffs_results_report.md`
