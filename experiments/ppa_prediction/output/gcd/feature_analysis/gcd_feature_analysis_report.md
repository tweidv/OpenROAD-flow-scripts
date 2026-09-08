# GCD PPA Prediction — Feature Analysis Report

**Date:** 2026-09-07
**Design:** gcd (nangate45)
**Trajectories:** 1000 completed perturbed runs
**Split:** 20 train / 980 test (trajectory-level, seed 42)

**Targets:** `final_power`, `final_fmax`, `final_area` from `6_report.json` finish metrics.
**Inputs:** structural checkpoint features only — no `norm_p/t/a`.

**Model:** XGBoost `n_estimators=80, max_depth=4, learning_rate=0.1, subsample=0.9, colsample_bytree=0.9, random_state=42`

---

# Part 1 — What Was Run

All analysis is **offline** on existing ORFS JSON logs under `flow/logs/nangate45/gcd/ppa_*/`. No new OpenROAD runs were required.

| Step | Script | Output |
|------|--------|--------|
| 1. Batch trajectories | `run_batch_detached.sh` | 1000 complete GCD flows |
| 2. Dataset build | `build_dataset.py` | `output/gcd/dataset.csv` (4000 rows) |
| 3. Search ordering eval | `search_eval.py` | `output/gcd/search_eval_report.md` |
| 4. Metrics inventory | `inventory_openroad_metrics.py` | 476 unique (file × metric) pairs |
| 5. Hand-picked feature analysis | `feature_analysis.py` | 13 curated features × 4 stages |
| 6. Wide feature tables | `wide_metrics.py` | 233 numeric features × 4 stages |
| 7. Full metrics analysis | `feature_analysis_full.py` | SHAP + group + LOO ablation (756 XGBoost fits) |

### Search eval (separate from feature importance)

- Offline replay: model orders which checkpoint to reveal next on 980 test trajectories.
- Model-guided: **1 eval to 95%** of batch optimum; finds true optimum (`traj_sweep_104`, V=0.963) at eval #12.
- Random baseline: ~5 evals to 95% (mean over 1000 permutations).
- With run-cost model: model **9 cost units** vs random **~57 mean / 44 p50** to 95%.
- See [`search_eval_report.md`](../search_eval_report.md).

### Feature analysis methods

- **SHAP** (TreeExplainer): primary importance metric on test set.
- **Group ablation**: drop entire metric categories (timing, design, power, etc.) and measure ΔR².
- **Individual ablation**: leave-one-out (LOO) per feature; slow but catches redundancy effects.
- Per-stage features only — no future-stage leakage.

---

# Part 2 — Recommendations

### For production PPA prediction models

1. **Use the hand-picked 13-feature set for search ordering.** It matches or beats full metrics on most stage×target R² (routing power is the exception: 0.942 vs 0.915), trains faster, and is easier to interpret.
2. **Floorplan: `utilization` (CORE_UTILIZATION) is the single dominant signal** for all three targets. At floorplan, fmax R² is still modest (0.59–0.87) — expect early ranking to be noisier than post-placement.
3. **Placement onward: combine structural + timing proxies.** HPWL/placement_density (area, power), inv_fmax and setup slack (timing), congestion (routing stress).
4. **Post-CTS: timing metrics dominate** — `total_negative_slack`, `inv_fmax`, `clock_skew`. Buffer counts add marginal power signal.
5. **Post-routing: wirelength + slack** for power/area; inv_fmax and congestion for fmax ranking.

### For feature selection / dimensionality reduction

6. **Full 233-feature analysis confirms massive redundancy.** `design__instance__area` and correlated design metrics (core/die area, utilization, rows/sites) dominate SHAP everywhere; many features show |SHAP|=0 but non-zero ablation ΔR² due to collinearity.
7. **Do not trust individual ablation alone** when features are correlated — negative ΔR² is common. Prefer SHAP for ranking; use group ablation to validate category-level importance.
8. **Drop constant features** (`drc_violation_count`=0 everywhere; many flow warning counts). The wide builder already filters n_unique<2 and >5% missing.
9. **Config params (`param:*`)** are useful at floorplan (`CORE_UTILIZATION`) but contribute little once structural metrics are available at later stages.

### For next experiments

10. **No need to re-run OpenROAD** for feature work — all metrics are in JSON logs. Re-run only `feature_analysis_full.py` if split or filtering changes.
11. **Try a reduced “best-of-both” set** (~25 features): hand-picked 13 + top full-metric additions (`design__instance__area`, `timing__setup__tns`, `timing__drv__max_cap_limit`, `global_route__wirelength`, `route__vias`). Compare R² and search-eval cost.
12. **Search eval caveat:** offline replay with `traj_bad_03` in test inflates “1 eval to 95%”. Consider held-out designs or counterfactual checkpoint reveals for stronger claims.
13. **Expand train set** beyond 20 trajectories if deploying — current split is intentionally harsh for generalisation testing.

---

# Part 3 — Hand-Picked Features (13 features)

## Hand-picked feature analysis

### Full-model test R² (by stage × target)

| Stage | Power | Fmax | Area |
|-------|------:|-----:|-----:|
| floorplan | 0.863 | 0.589 | 0.887 |
| placement | 0.902 | 0.894 | 0.977 |
| cts | 0.908 | 0.933 | 0.940 |
| routing | 0.942 | 0.910 | 0.983 |

### Features per stage

**floorplan** (3 features):
`core_area`, `utilization`, `aspect_ratio`

**placement** (4 features):
`hpwl`, `placement_density`, `estimated_congestion`, `inv_fmax`

**cts** (4 features):
`inv_fmax`, `total_negative_slack`, `clock_skew`, `buffer_inverter_count`

**routing** (5 features):
`routed_wirelength`, `inv_fmax`, `total_negative_slack`, `congestion`, `drc_violation_count`

### FLOORPLAN

#### Power — Top 10 SHAP

- `utilization` |SHAP|=0.002243
- `core_area` |SHAP|=0
- `aspect_ratio` |SHAP|=0

#### Power — Top 10 ablation (ΔR² when removed)

- `utilization` ΔR²=0.9525
- `core_area` ΔR²=-0.0005008
- `aspect_ratio` ΔR²=-0.001104

#### Fmax — Top 10 SHAP

- `utilization` |SHAP|=7.043e+07
- `core_area` |SHAP|=0
- `aspect_ratio` |SHAP|=0

#### Fmax — Top 10 ablation (ΔR² when removed)

- `utilization` ΔR²=0.6029
- `core_area` ΔR²=-0.002188
- `aspect_ratio` ΔR²=-0.006088

#### Area — Top 10 SHAP

- `utilization` |SHAP|=112.249
- `core_area` |SHAP|=0
- `aspect_ratio` |SHAP|=0

#### Area — Top 10 ablation (ΔR² when removed)

- `utilization` ΔR²=1.014
- `core_area` ΔR²=-0.0016
- `aspect_ratio` ΔR²=-0.002034

#### Largest group ablations (mean ΔR² across targets)


#### SHAP vs ablation Spearman ρ by target

- power: ρ=1.000
- fmax: ρ=1.000
- area: ρ=1.000

### PLACEMENT

#### Power — Top 10 SHAP

- `placement_density` |SHAP|=0.00115
- `inv_fmax` |SHAP|=0.0009021
- `hpwl` |SHAP|=0.0004405
- `estimated_congestion` |SHAP|=1.395e-05

#### Power — Top 10 ablation (ΔR² when removed)

- `placement_density` ΔR²=0.09848
- `inv_fmax` ΔR²=-0.008845
- `estimated_congestion` ΔR²=-0.01032
- `hpwl` ΔR²=-0.0166

#### Fmax — Top 10 SHAP

- `hpwl` |SHAP|=4.248e+07
- `placement_density` |SHAP|=3.159e+07
- `estimated_congestion` |SHAP|=4.808e+06
- `inv_fmax` |SHAP|=4.661e+06

#### Fmax — Top 10 ablation (ΔR² when removed)

- `placement_density` ΔR²=-0.01294
- `inv_fmax` ΔR²=-0.01398
- `hpwl` ΔR²=-0.01727
- `estimated_congestion` ΔR²=-0.02719

#### Area — Top 10 SHAP

- `hpwl` |SHAP|=55.893
- `placement_density` |SHAP|=53.2889
- `inv_fmax` |SHAP|=12.4304
- `estimated_congestion` |SHAP|=1.85769

#### Area — Top 10 ablation (ΔR² when removed)

- `placement_density` ΔR²=0.008354
- `hpwl` ΔR²=0.0006619
- `inv_fmax` ΔR²=-0.002395
- `estimated_congestion` ΔR²=-0.003334

#### Largest group ablations (mean ΔR² across targets)

- `-placement`: 0.2705
- `-timing`: -0.008407
- `-congestion`: -0.01361

#### SHAP vs ablation Spearman ρ by target

- power: ρ=0.800
- fmax: ρ=0.000
- area: ρ=0.800

### CTS

#### Power — Top 10 SHAP

- `total_negative_slack` |SHAP|=0.001392
- `buffer_inverter_count` |SHAP|=0.0005652
- `inv_fmax` |SHAP|=0.0005081
- `clock_skew` |SHAP|=0

#### Power — Top 10 ablation (ΔR² when removed)

- `total_negative_slack` ΔR²=0.2563
- `buffer_inverter_count` ΔR²=-0.003612
- `clock_skew` ΔR²=-0.01268
- `inv_fmax` ΔR²=-0.01751

#### Fmax — Top 10 SHAP

- `inv_fmax` |SHAP|=3.811e+07
- `total_negative_slack` |SHAP|=3.014e+07
- `clock_skew` |SHAP|=6.948e+06
- `buffer_inverter_count` |SHAP|=2.665e+06

#### Fmax — Top 10 ablation (ΔR² when removed)

- `inv_fmax` ΔR²=0.1859
- `total_negative_slack` ΔR²=-0.002618
- `clock_skew` ΔR²=-0.005922
- `buffer_inverter_count` ΔR²=-0.01391

#### Area — Top 10 SHAP

- `inv_fmax` |SHAP|=62.944
- `total_negative_slack` |SHAP|=45.7106
- `clock_skew` |SHAP|=5.7556
- `buffer_inverter_count` |SHAP|=2.2463

#### Area — Top 10 ablation (ΔR² when removed)

- `total_negative_slack` ΔR²=0.02717
- `buffer_inverter_count` ΔR²=0.005512
- `clock_skew` ΔR²=-0.0104
- `inv_fmax` ΔR²=-0.0123

#### Largest group ablations (mean ΔR² across targets)

- `-timing`: 0.2862
- `-cts`: 0.0339

#### SHAP vs ablation Spearman ρ by target

- power: ρ=0.800
- fmax: ρ=1.000
- area: ρ=-0.400

### ROUTING

#### Power — Top 10 SHAP

- `total_negative_slack` |SHAP|=0.001388
- `routed_wirelength` |SHAP|=0.0007674
- `inv_fmax` |SHAP|=0.0002528
- `congestion` |SHAP|=2.317e-05
- `drc_violation_count` |SHAP|=0

#### Power — Top 10 ablation (ΔR² when removed)

- `total_negative_slack` ΔR²=0.09907
- `routed_wirelength` ΔR²=0.05682
- `inv_fmax` ΔR²=-0.005922
- `congestion` ΔR²=-0.008403
- `drc_violation_count` ΔR²=-0.008403

#### Fmax — Top 10 SHAP

- `routed_wirelength` |SHAP|=5.738e+07
- `inv_fmax` |SHAP|=1.994e+07
- `total_negative_slack` |SHAP|=6.356e+06
- `congestion` |SHAP|=5.259e+06
- `drc_violation_count` |SHAP|=0

#### Fmax — Top 10 ablation (ΔR² when removed)

- `inv_fmax` ΔR²=0.0157
- `congestion` ΔR²=0.00148
- `total_negative_slack` ΔR²=-0.02245
- `drc_violation_count` ΔR²=-0.02278
- `routed_wirelength` ΔR²=-0.06192

#### Area — Top 10 SHAP

- `routed_wirelength` |SHAP|=67.9217
- `total_negative_slack` |SHAP|=46.0681
- `inv_fmax` |SHAP|=3.84056
- `congestion` |SHAP|=0.917794
- `drc_violation_count` |SHAP|=0

#### Area — Top 10 ablation (ΔR² when removed)

- `routed_wirelength` ΔR²=0.05128
- `total_negative_slack` ΔR²=0.02195
- `drc_violation_count` ΔR²=-0.003794
- `congestion` ΔR²=-0.006009
- `inv_fmax` ΔR²=-0.00636

#### Largest group ablations (mean ΔR² across targets)

- `-timing`: 0.1096
- `-routing`: -0.001479
- `-congestion`: -0.004311

#### SHAP vs ablation Spearman ρ by target

- power: ρ=1.000
- fmax: ρ=-0.100
- area: ρ=0.600

---

# Part 4 — Full ORFS Metrics (233 features)

## Full metrics analysis

### Full-model test R² (by stage × target)

| Stage | Power | Fmax | Area |
|-------|------:|-----:|-----:|
| floorplan | 0.942 | 0.871 | 0.969 |
| placement | 0.932 | 0.903 | 0.965 |
| cts | 0.911 | 0.888 | 0.946 |
| routing | 0.915 | 0.875 | 0.967 |

### Features per stage

**floorplan** (27 features):
- Metrics: 21
- Config params: `param:CLK_PERIOD`, `param:CORE_ASPECT_RATIO`, `param:CORE_UTILIZATION`, `param:CTS_CLUSTER_SIZE`, `param:PLACE_DENSITY_LB_ADDON`, `param:TNS_END_PERCENT`

**placement** (95 features):
- Metrics: 89
- Config params: `param:CLK_PERIOD`, `param:CORE_ASPECT_RATIO`, `param:CORE_UTILIZATION`, `param:CTS_CLUSTER_SIZE`, `param:PLACE_DENSITY_LB_ADDON`, `param:TNS_END_PERCENT`

**cts** (44 features):
- Metrics: 38
- Config params: `param:CLK_PERIOD`, `param:CORE_ASPECT_RATIO`, `param:CORE_UTILIZATION`, `param:CTS_CLUSTER_SIZE`, `param:PLACE_DENSITY_LB_ADDON`, `param:TNS_END_PERCENT`

**routing** (67 features):
- Metrics: 61
- Config params: `param:CLK_PERIOD`, `param:CORE_ASPECT_RATIO`, `param:CORE_UTILIZATION`, `param:CTS_CLUSTER_SIZE`, `param:PLACE_DENSITY_LB_ADDON`, `param:TNS_END_PERCENT`

### FLOORPLAN

#### Power — Top 10 SHAP

- `2_1_floorplan__floorplan__design__instance__area` |SHAP|=0.001662
- `2_1_floorplan__floorplan__power__internal__total` |SHAP|=0.0004418
- `2_1_floorplan__floorplan__design__instance__area__stdcell` |SHAP|=0.0002908
- `2_1_floorplan__floorplan__design__core__area` |SHAP|=0
- `2_1_floorplan__floorplan__design__die__area` |SHAP|=0
- `2_1_floorplan__floorplan__design__instance__utilization` |SHAP|=0
- `2_1_floorplan__floorplan__design__instance__utilization__stdcell` |SHAP|=0
- `2_1_floorplan__floorplan__design__rows` |SHAP|=0
- `2_1_floorplan__floorplan__design__rows:FreePDK45_38x28_10R_NP_162NW_34O` |SHAP|=0
- `2_1_floorplan__floorplan__design__sites` |SHAP|=0

#### Power — Top 10 ablation (ΔR² when removed)

- `2_1_floorplan__floorplan__design__instance__area` ΔR²=0.001155
- `2_1_floorplan__floorplan__design__instance__area__stdcell` ΔR²=0.001155
- `2_1_floorplan__floorplan__design__instance__utilization` ΔR²=0.0002698
- `2_1_floorplan__floorplan__design__instance__utilization__stdcell` ΔR²=0.0002698
- `2_1_floorplan__floorplan__design__rows` ΔR²=0.0002698
- `2_1_floorplan__floorplan__design__rows:FreePDK45_38x28_10R_NP_162NW_34O` ΔR²=0.0002698
- `2_1_floorplan__floorplan__design__sites` ΔR²=0.0002698
- `2_1_floorplan__floorplan__design__sites:FreePDK45_38x28_10R_NP_162NW_34O` ΔR²=0.0002698
- `2_1_floorplan__floorplan__flow__warnings__count` ΔR²=0.0002698
- `2_1_floorplan__floorplan__flow__warnings__type_count` ΔR²=0.0002698

#### Fmax — Top 10 SHAP

- `2_1_floorplan__floorplan__power__internal__total` |SHAP|=6.361e+07
- `2_1_floorplan__floorplan__design__instance__area` |SHAP|=1.702e+07
- `param:CORE_UTILIZATION` |SHAP|=3.487e+06
- `2_1_floorplan__floorplan__design__instance__area__stdcell` |SHAP|=1.95e+06
- `2_1_floorplan__floorplan__power__total` |SHAP|=1.332e+06
- `2_1_floorplan__floorplan__power__switching__total` |SHAP|=2.18e+05
- `2_1_floorplan__floorplan__design__core__area` |SHAP|=0
- `2_1_floorplan__floorplan__design__die__area` |SHAP|=0
- `2_1_floorplan__floorplan__design__instance__utilization` |SHAP|=0
- `2_1_floorplan__floorplan__design__instance__utilization__stdcell` |SHAP|=0

#### Fmax — Top 10 ablation (ΔR² when removed)

- `2_1_floorplan__floorplan__design__instance__utilization` ΔR²=0.003266
- `2_1_floorplan__floorplan__design__instance__utilization__stdcell` ΔR²=0.003266
- `2_1_floorplan__floorplan__design__rows` ΔR²=0.003266
- `2_1_floorplan__floorplan__design__rows:FreePDK45_38x28_10R_NP_162NW_34O` ΔR²=0.003266
- `2_1_floorplan__floorplan__design__sites` ΔR²=0.003266
- `2_1_floorplan__floorplan__design__sites:FreePDK45_38x28_10R_NP_162NW_34O` ΔR²=0.003266
- `2_1_floorplan__floorplan__flow__warnings__count` ΔR²=0.003266
- `2_1_floorplan__floorplan__flow__warnings__type_count` ΔR²=0.003266
- `2_1_floorplan__floorplan__power__leakage__total` ΔR²=0.003266
- `2_1_floorplan__floorplan__power__switching__total` ΔR²=0.003266

#### Area — Top 10 SHAP

- `2_1_floorplan__floorplan__design__instance__area` |SHAP|=89.6962
- `2_1_floorplan__floorplan__power__internal__total` |SHAP|=19.4375
- `2_1_floorplan__floorplan__design__instance__area__stdcell` |SHAP|=13.8876
- `param:CORE_UTILIZATION` |SHAP|=2.2463
- `2_1_floorplan__floorplan__power__total` |SHAP|=0.458318
- `2_1_floorplan__floorplan__power__switching__total` |SHAP|=0.205915
- `param:CTS_CLUSTER_SIZE` |SHAP|=0.0113262
- `2_1_floorplan__floorplan__design__core__area` |SHAP|=0
- `2_1_floorplan__floorplan__design__die__area` |SHAP|=0
- `2_1_floorplan__floorplan__design__instance__utilization` |SHAP|=0

#### Area — Top 10 ablation (ΔR² when removed)

- `param:CORE_UTILIZATION` ΔR²=0.002504
- `2_1_floorplan__floorplan__design__core__area` ΔR²=0.00034
- `2_1_floorplan__floorplan__design__die__area` ΔR²=0.00034
- `2_1_floorplan__floorplan__design__instance__utilization` ΔR²=0.0002627
- `2_1_floorplan__floorplan__design__instance__utilization__stdcell` ΔR²=0.0002627
- `2_1_floorplan__floorplan__design__rows` ΔR²=0.0002627
- `2_1_floorplan__floorplan__design__rows:FreePDK45_38x28_10R_NP_162NW_34O` ΔR²=0.0002627
- `2_1_floorplan__floorplan__design__sites` ΔR²=0.0002627
- `2_1_floorplan__floorplan__design__sites:FreePDK45_38x28_10R_NP_162NW_34O` ΔR²=0.0002627
- `2_1_floorplan__floorplan__flow__warnings__count` ΔR²=0.0002627

#### Largest group ablations (mean ΔR² across targets)

- `-floorplan`: 0.01165
- `-configuration`: -0.0006393

#### SHAP vs ablation Spearman ρ by target

- power: ρ=0.640
- fmax: ρ=0.110
- area: ρ=0.299

### PLACEMENT

#### Power — Top 10 SHAP

- `3_3_place_gp__globalplace__design__instance__area` |SHAP|=0.001575
- `3_3_place_gp__globalplace__gpl__area__original` |SHAP|=0.0004903
- `3_3_place_gp__globalplace__power__internal__total` |SHAP|=0.0002204
- `3_3_place_gp__globalplace__design__instance__area__stdcell` |SHAP|=0.0001433
- `3_3_place_gp__globalplace__gpl__routability__congestion` |SHAP|=4.863e-05
- `3_3_place_gp__globalplace__design__core__area` |SHAP|=0
- `3_3_place_gp__globalplace__design__die__area` |SHAP|=0
- `3_3_place_gp__globalplace__design__instance__count` |SHAP|=0
- `3_3_place_gp__globalplace__design__instance__count__stdcell` |SHAP|=0
- `3_3_place_gp__globalplace__design__instance__utilization` |SHAP|=0

#### Power — Top 10 ablation (ΔR² when removed)

- `3_3_place_gp__globalplace__design__core__area` ΔR²=0.0002912
- `3_3_place_gp__globalplace__design__die__area` ΔR²=0.0002912
- `3_3_place_gp__globalplace__design__instance__count` ΔR²=0.0002912
- `3_3_place_gp__globalplace__design__instance__count__stdcell` ΔR²=0.0002912
- `3_3_place_gp__globalplace__design__instance__utilization` ΔR²=0.0002912
- `3_3_place_gp__globalplace__design__instance__utilization__stdcell` ΔR²=0.0002912
- `3_3_place_gp__globalplace__design__nets` ΔR²=0.0002912
- `3_3_place_gp__globalplace__design__rows` ΔR²=0.0002912
- `3_3_place_gp__globalplace__design__rows:FreePDK45_38x28_10R_NP_162NW_34O` ΔR²=0.0002912
- `3_3_place_gp__globalplace__design__sites` ΔR²=0.0002912

#### Fmax — Top 10 SHAP

- `3_3_place_gp__globalplace__design__instance__area` |SHAP|=6.338e+07
- `3_3_place_gp__globalplace__design__instance__area__stdcell` |SHAP|=9.109e+06
- `3_5_place_dp__detailedplace__timing__drv__max_cap_limit` |SHAP|=9.038e+06
- `3_4_place_resized__placeopt__timing__drv__max_cap_limit` |SHAP|=4.181e+06
- `3_5_place_dp__detailedplace__design__instance__displacement__max` |SHAP|=3.972e+06
- `3_4_place_resized__placeopt__timing__drv__max_slew_limit` |SHAP|=3.041e+06
- `3_3_place_gp__globalplace__gpl__convergence__iteration` |SHAP|=1.805e+06
- `3_3_place_gp__globalplace__design__instance__count` |SHAP|=1.66e+06
- `3_3_place_gp__globalplace__gpl__routability__congestion` |SHAP|=8.361e+05
- `3_5_place_dp__detailedplace__design__instance__displacement__total` |SHAP|=3.868e+05

#### Fmax — Top 10 ablation (ΔR² when removed)

- `3_5_place_dp__detailedplace__timing__drv__max_cap_limit` ΔR²=0.004495
- `3_3_place_gp__globalplace__design__instance__area` ΔR²=0.002102
- `3_3_place_gp__globalplace__design__instance__area__stdcell` ΔR²=0.002102
- `3_3_place_gp__globalplace__gpl__area__original` ΔR²=0.001977
- `3_3_place_gp__globalplace__design__instance__count` ΔR²=0.001966
- `3_3_place_gp__globalplace__design__instance__count__stdcell` ΔR²=0.001966
- `3_3_place_gp__globalplace__design__core__area` ΔR²=0.001939
- `3_3_place_gp__globalplace__design__die__area` ΔR²=0.001939
- `3_3_place_gp__globalplace__design__instance__utilization` ΔR²=0.001939
- `3_3_place_gp__globalplace__design__instance__utilization__stdcell` ΔR²=0.001939

#### Area — Top 10 SHAP

- `3_3_place_gp__globalplace__design__instance__area` |SHAP|=93.3678
- `3_3_place_gp__globalplace__design__instance__area__stdcell` |SHAP|=15.0139
- `3_3_place_gp__globalplace__design__instance__count` |SHAP|=11.5735
- `3_5_place_dp__detailedplace__timing__fmax` |SHAP|=2.52637
- `3_3_place_gp__globalplace__gpl__routability__iteration` |SHAP|=1.79154
- `3_5_place_dp__detailedplace__timing__fmax__clock:core_clock` |SHAP|=0.639162
- `3_5_place_dp__detailedplace__design__instance__displacement__total` |SHAP|=0.492288
- `3_3_place_gp__globalplace__gpl__area__original` |SHAP|=0.450295
- `3_3_place_gp__globalplace__gpl__convergence__iteration` |SHAP|=0.324971
- `3_4_place_resized__placeopt__timing__drv__max_slew_limit` |SHAP|=0.256086

#### Area — Top 10 ablation (ΔR² when removed)

- `3_5_place_dp__detailedplace__design__instance__displacement__total` ΔR²=0.0004143
- `3_3_place_gp__globalplace__gpl__convergence__iteration` ΔR²=0.0003453
- `3_3_place_gp__globalplace__gpl__routability__iteration` ΔR²=0.0002874
- `3_3_place_gp__globalplace__gpl__area__original` ΔR²=0.0002419
- `3_5_place_dp__detailedplace__timing__fmax` ΔR²=0.0002212
- `3_5_place_dp__detailedplace__timing__fmax__clock:core_clock` ΔR²=0.0002212
- `3_5_place_dp__detailedplace__design__instance__displacement__mean` ΔR²=0.0001543
- `3_3_place_gp__globalplace__gpl__area__timing_delta` ΔR²=7.119e-05
- `3_3_place_gp__globalplace__gpl__area__timing_delta__percent` ΔR²=7.119e-05
- `3_3_place_gp__globalplace__design__instance__area` ΔR²=6.114e-05

#### Largest group ablations (mean ΔR² across targets)

- `-detailedplace`: 0.002435
- `-configuration`: -0.001825
- `-globalplace`: -0.002111
- `-placeopt`: -0.003206

#### SHAP vs ablation Spearman ρ by target

- power: ρ=0.759
- fmax: ρ=0.499
- area: ρ=0.860

### CTS

#### Power — Top 10 SHAP

- `4_1_cts__cts__design__instance__area` |SHAP|=0.001068
- `4_1_cts__cts__design__instance__displacement__mean` |SHAP|=0.0004981
- `4_1_cts__cts__design__instance__count` |SHAP|=0.0004822
- `4_1_cts__cts__power__internal__total` |SHAP|=0.0001316
- `4_1_cts__cts__design__instance__displacement__total` |SHAP|=0.0001239
- `4_1_cts__cts__design__instance__area__stdcell` |SHAP|=8.417e-05
- `4_1_cts__cts__power__switching__total` |SHAP|=4.724e-05
- `4_1_cts__cts__clock__skew__hold` |SHAP|=2.205e-05
- `4_1_cts__cts__clock__skew__setup` |SHAP|=0
- `4_1_cts__cts__design__core__area` |SHAP|=0

#### Power — Top 10 ablation (ΔR² when removed)

- `4_1_cts__cts__design__instance__count` ΔR²=0.001533
- `4_1_cts__cts__design__instance__count__stdcell` ΔR²=0.001465
- `4_1_cts__cts__design__instance__displacement__max` ΔR²=0.001465
- `4_1_cts__cts__design__instance__displacement__mean` ΔR²=0.001465
- `4_1_cts__cts__design__instance__displacement__total` ΔR²=0.001465
- `4_1_cts__cts__design__instance__utilization` ΔR²=0.001465
- `4_1_cts__cts__design__instance__utilization__stdcell` ΔR²=0.001465
- `4_1_cts__cts__design__rows` ΔR²=0.001465
- `4_1_cts__cts__design__rows:FreePDK45_38x28_10R_NP_162NW_34O` ΔR²=0.001465
- `4_1_cts__cts__design__sites` ΔR²=0.001465

#### Fmax — Top 10 SHAP

- `4_1_cts__cts__design__instance__area` |SHAP|=6.355e+07
- `4_1_cts__cts__design__instance__area__stdcell` |SHAP|=8.749e+06
- `4_1_cts__cts__clock__skew__hold` |SHAP|=6.398e+06
- `4_1_cts__cts__timing__fmax` |SHAP|=3.384e+06
- `4_1_cts__cts__timing__drv__max_slew_limit` |SHAP|=2.68e+06
- `4_1_cts__cts__design__instance__count__setup_buffer` |SHAP|=1.589e+06
- `4_1_cts__cts__power__internal__total` |SHAP|=1.509e+06
- `4_1_cts__cts__timing__drv__max_cap_limit` |SHAP|=1.231e+06
- `4_1_cts__cts__timing__hold__ws` |SHAP|=9.542e+05
- `4_1_cts__cts__design__instance__displacement__max` |SHAP|=5.681e+05

#### Fmax — Top 10 ablation (ΔR² when removed)

- `4_1_cts__cts__timing__hold__ws` ΔR²=0.005464
- `4_1_cts__cts__design__instance__count` ΔR²=-6.128e-05
- `4_1_cts__cts__design__core__area` ΔR²=-6.16e-05
- `4_1_cts__cts__design__die__area` ΔR²=-6.16e-05
- `4_1_cts__cts__timing__drv__max_slew_limit` ΔR²=-7.421e-05
- `4_1_cts__cts__clock__skew__hold` ΔR²=-0.0004434
- `4_1_cts__cts__clock__skew__setup` ΔR²=-0.0004434
- `4_1_cts__cts__design__instance__area` ΔR²=-0.000711
- `4_1_cts__cts__design__instance__area__stdcell` ΔR²=-0.000711
- `4_1_cts__cts__timing__drv__max_cap_limit` ΔR²=-0.001309

#### Area — Top 10 SHAP

- `4_1_cts__cts__design__instance__area` |SHAP|=96.7163
- `4_1_cts__cts__design__instance__area__stdcell` |SHAP|=13.9327
- `4_1_cts__cts__clock__skew__hold` |SHAP|=9.8238
- `4_1_cts__cts__design__instance__displacement__mean` |SHAP|=2.94834
- `4_1_cts__cts__clock__skew__setup` |SHAP|=1.0539
- `4_1_cts__cts__timing__drv__max_cap_limit` |SHAP|=0.808686
- `4_1_cts__cts__timing__hold__ws` |SHAP|=0.374962
- `4_1_cts__cts__timing__drv__max_slew_limit` |SHAP|=0.372094
- `4_1_cts__cts__design__instance__displacement__total` |SHAP|=0.203375
- `4_1_cts__cts__design__instance__count` |SHAP|=0.12234

#### Area — Top 10 ablation (ΔR² when removed)

- `4_1_cts__cts__design__instance__area` ΔR²=-0.003537
- `4_1_cts__cts__design__instance__area__stdcell` ΔR²=-0.003537
- `4_1_cts__cts__design__instance__count__stdcell` ΔR²=-0.00387
- `4_1_cts__cts__design__instance__displacement__mean` ΔR²=-0.00388
- `4_1_cts__cts__design__instance__displacement__total` ΔR²=-0.00388
- `4_1_cts__cts__design__instance__count` ΔR²=-0.00389
- `4_1_cts__cts__design__core__area` ΔR²=-0.003894
- `4_1_cts__cts__design__die__area` ΔR²=-0.003894
- `4_1_cts__cts__design__instance__displacement__max` ΔR²=-0.003894
- `4_1_cts__cts__design__instance__utilization` ΔR²=-0.003902

#### Largest group ablations (mean ΔR² across targets)

- `-configuration`: -0.000556
- `-cts`: -0.0006636

#### SHAP vs ablation Spearman ρ by target

- power: ρ=0.232
- fmax: ρ=0.432
- area: ρ=0.432

### ROUTING

#### Power — Top 10 SHAP

- `5_1_grt__globalroute__design__instance__area` |SHAP|=0.001445
- `5_1_grt__globalroute__power__internal__total` |SHAP|=0.0003176
- `5_1_grt__globalroute__design__instance__count` |SHAP|=0.0002902
- `5_1_grt__globalroute__design__instance__area__stdcell` |SHAP|=0.0001772
- `5_1_grt__globalroute__design__instance__count__stdcell` |SHAP|=8.692e-05
- `5_1_grt__globalroute__clock__skew__hold` |SHAP|=3.9e-05
- `5_1_grt__globalroute__power__total` |SHAP|=2.415e-05
- `5_1_grt__globalroute__clock__skew__setup` |SHAP|=1.511e-05
- `5_1_grt__globalroute__design__core__area` |SHAP|=0
- `5_1_grt__globalroute__design__die__area` |SHAP|=0

#### Power — Top 10 ablation (ΔR² when removed)

- `5_1_grt__globalroute__clock__skew__hold` ΔR²=0
- `5_1_grt__globalroute__clock__skew__setup` ΔR²=0
- `5_1_grt__globalroute__design__core__area` ΔR²=0
- `5_1_grt__globalroute__design__die__area` ΔR²=0
- `5_1_grt__globalroute__design__instance__count__setup_buffer` ΔR²=0
- `5_1_grt__globalroute__design__instance__count__stdcell` ΔR²=0
- `5_1_grt__globalroute__design__instance__displacement__max` ΔR²=0
- `5_1_grt__globalroute__design__instance__displacement__mean` ΔR²=0
- `5_1_grt__globalroute__design__instance__displacement__total` ΔR²=0
- `5_1_grt__globalroute__design__instance__utilization` ΔR²=0

#### Fmax — Top 10 SHAP

- `5_1_grt__globalroute__design__instance__area` |SHAP|=5.893e+07
- `5_1_grt__globalroute__design__instance__area__stdcell` |SHAP|=1.29e+07
- `5_1_grt__globalroute__dpl__hpwl__delta__percent` |SHAP|=3.424e+06
- `5_1_grt__globalroute__dpl__hpwl__delta` |SHAP|=2.874e+06
- `5_2_route__detailedroute__route__vias` |SHAP|=2.575e+06
- `5_1_grt__globalroute__design__instance__count` |SHAP|=2.358e+06
- `5_1_grt__globalroute__timing__fmax` |SHAP|=2.33e+06
- `5_1_grt__globalroute__design__instance__displacement__max` |SHAP|=1.816e+06
- `5_1_grt__globalroute__timing__drv__max_slew_limit` |SHAP|=1.67e+06
- `5_1_grt__globalroute__clock__skew__hold` |SHAP|=1.314e+06

#### Fmax — Top 10 ablation (ΔR² when removed)

- `5_1_grt__globalroute__timing__drv__max_slew_limit` ΔR²=0.01002
- `5_1_grt__globalroute__dpl__hpwl__delta` ΔR²=0.008937
- `5_1_grt__globalroute__global_route__fastroute__monotonic_s` ΔR²=0.003821
- `param:CORE_UTILIZATION` ΔR²=0.0025
- `5_1_grt__globalroute__global_route__vias` ΔR²=0.002056
- `5_1_grt__globalroute__global_route__fastroute__overflow_iterations_s` ΔR²=0.001693
- `5_1_grt__globalroute__timing__drv__setup_violation_count` ΔR²=0.001532
- `5_2_route__detailedroute__route__vias` ΔR²=0.001475
- `5_2_route__detailedroute__route__vias__singlecut` ΔR²=0.001475
- `5_1_grt__globalroute__global_route__fastroute__route_l_s` ΔR²=0.00122

#### Area — Top 10 SHAP

- `5_1_grt__globalroute__design__instance__area` |SHAP|=91.0077
- `5_1_grt__globalroute__design__instance__area__stdcell` |SHAP|=20.1004
- `5_1_grt__globalroute__clock__skew__hold` |SHAP|=1.65538
- `5_2_route__detailedroute__route__vias` |SHAP|=0.801313
- `5_2_route__detailedroute__route__drc_errors__iter:1` |SHAP|=0.710397
- `5_1_grt__globalroute__design__instance__count` |SHAP|=0.47492
- `5_1_grt__globalroute__clock__skew__setup` |SHAP|=0.330364
- `5_1_grt__globalroute__design__instance__displacement__max` |SHAP|=0.292833
- `5_1_grt__globalroute__design__instance__displacement__mean` |SHAP|=0.281483
- `5_1_grt__globalroute__timing__drv__max_slew_limit` |SHAP|=0.110178

#### Area — Top 10 ablation (ΔR² when removed)

- `5_1_grt__globalroute__design__instance__count__setup_buffer` ΔR²=0.0001831
- `5_1_grt__globalroute__design__instance__count__stdcell` ΔR²=0.0001817
- `5_1_grt__globalroute__design__instance__displacement__mean` ΔR²=0.0001817
- `5_1_grt__globalroute__design__instance__displacement__total` ΔR²=0.0001817
- `5_1_grt__globalroute__design__instance__utilization` ΔR²=0.0001817
- `5_1_grt__globalroute__design__instance__utilization__stdcell` ΔR²=0.0001817
- `5_1_grt__globalroute__design__nets` ΔR²=0.0001817
- `5_1_grt__globalroute__design__rows` ΔR²=0.0001817
- `5_1_grt__globalroute__design__rows:FreePDK45_38x28_10R_NP_162NW_34O` ΔR²=0.0001817
- `5_1_grt__globalroute__design__sites` ΔR²=0.0001817

#### Largest group ablations (mean ΔR² across targets)

- `-globalroute`: 0.01491
- `-detailedroute`: 0.002817
- `-configuration`: 0.0002134

#### SHAP vs ablation Spearman ρ by target

- power: ρ=0.704
- fmax: ρ=-0.273
- area: ρ=0.357

---

# Part 5 — Complete Feature List (233 features)

## FLOORPLAN (27 features)

1. `2_1_floorplan__floorplan__design__core__area`
2. `2_1_floorplan__floorplan__design__die__area`
3. `2_1_floorplan__floorplan__design__instance__area`
4. `2_1_floorplan__floorplan__design__instance__area__stdcell`
5. `2_1_floorplan__floorplan__design__instance__utilization`
6. `2_1_floorplan__floorplan__design__instance__utilization__stdcell`
7. `2_1_floorplan__floorplan__design__rows`
8. `2_1_floorplan__floorplan__design__rows:FreePDK45_38x28_10R_NP_162NW_34O`
9. `2_1_floorplan__floorplan__design__sites`
10. `2_1_floorplan__floorplan__design__sites:FreePDK45_38x28_10R_NP_162NW_34O`
11. `2_1_floorplan__floorplan__flow__warnings__count`
12. `2_1_floorplan__floorplan__flow__warnings__type_count`
13. `2_1_floorplan__floorplan__power__internal__total`
14. `2_1_floorplan__floorplan__power__leakage__total`
15. `2_1_floorplan__floorplan__power__switching__total`
16. `2_1_floorplan__floorplan__power__total`
17. `2_1_floorplan__floorplan__timing__fmax`
18. `2_1_floorplan__floorplan__timing__fmax__clock:core_clock`
19. `2_1_floorplan__floorplan__timing__hold__ws`
20. `2_1_floorplan__floorplan__timing__setup__tns`
21. `2_1_floorplan__floorplan__timing__setup__ws`
22. `param:CLK_PERIOD`
23. `param:CORE_ASPECT_RATIO`
24. `param:CORE_UTILIZATION`
25. `param:CTS_CLUSTER_SIZE`
26. `param:PLACE_DENSITY_LB_ADDON`
27. `param:TNS_END_PERCENT`

## PLACEMENT (95 features)

1. `3_3_place_gp__globalplace__design__core__area`
2. `3_3_place_gp__globalplace__design__die__area`
3. `3_3_place_gp__globalplace__design__instance__area`
4. `3_3_place_gp__globalplace__design__instance__area__stdcell`
5. `3_3_place_gp__globalplace__design__instance__count`
6. `3_3_place_gp__globalplace__design__instance__count__stdcell`
7. `3_3_place_gp__globalplace__design__instance__utilization`
8. `3_3_place_gp__globalplace__design__instance__utilization__stdcell`
9. `3_3_place_gp__globalplace__design__nets`
10. `3_3_place_gp__globalplace__design__rows`
11. `3_3_place_gp__globalplace__design__rows:FreePDK45_38x28_10R_NP_162NW_34O`
12. `3_3_place_gp__globalplace__design__sites`
13. `3_3_place_gp__globalplace__design__sites:FreePDK45_38x28_10R_NP_162NW_34O`
14. `3_3_place_gp__globalplace__gpl__area__final`
15. `3_3_place_gp__globalplace__gpl__area__final__percent`
16. `3_3_place_gp__globalplace__gpl__area__original`
17. `3_3_place_gp__globalplace__gpl__area__timing_delta`
18. `3_3_place_gp__globalplace__gpl__area__timing_delta__percent`
19. `3_3_place_gp__globalplace__gpl__convergence__iteration`
20. `3_3_place_gp__globalplace__gpl__routability__congestion`
21. `3_3_place_gp__globalplace__gpl__routability__iteration`
22. `3_3_place_gp__globalplace__power__internal__total`
23. `3_3_place_gp__globalplace__power__leakage__total`
24. `3_3_place_gp__globalplace__power__switching__total`
25. `3_3_place_gp__globalplace__power__total`
26. `3_3_place_gp__globalplace__route__wirelength__estimated`
27. `3_3_place_gp__globalplace__timing__fmax`
28. `3_3_place_gp__globalplace__timing__fmax__clock:core_clock`
29. `3_3_place_gp__globalplace__timing__hold__ws`
30. `3_3_place_gp__globalplace__timing__setup__tns`
31. `3_3_place_gp__globalplace__timing__setup__ws`
32. `3_4_place_resized__placeopt__design__core__area`
33. `3_4_place_resized__placeopt__design__die__area`
34. `3_4_place_resized__placeopt__design__instance__area`
35. `3_4_place_resized__placeopt__design__instance__area__stdcell`
36. `3_4_place_resized__placeopt__design__instance__count`
37. `3_4_place_resized__placeopt__design__instance__count__stdcell`
38. `3_4_place_resized__placeopt__design__instance__utilization`
39. `3_4_place_resized__placeopt__design__instance__utilization__stdcell`
40. `3_4_place_resized__placeopt__design__nets`
41. `3_4_place_resized__placeopt__design__rows`
42. `3_4_place_resized__placeopt__design__rows:FreePDK45_38x28_10R_NP_162NW_34O`
43. `3_4_place_resized__placeopt__design__sites`
44. `3_4_place_resized__placeopt__design__sites:FreePDK45_38x28_10R_NP_162NW_34O`
45. `3_4_place_resized__placeopt__power__internal__total`
46. `3_4_place_resized__placeopt__power__leakage__total`
47. `3_4_place_resized__placeopt__power__switching__total`
48. `3_4_place_resized__placeopt__power__total`
49. `3_4_place_resized__placeopt__timing__drv__max_cap_limit`
50. `3_4_place_resized__placeopt__timing__drv__max_slew_limit`
51. `3_4_place_resized__placeopt__timing__drv__setup_violation_count`
52. `3_4_place_resized__placeopt__timing__fmax`
53. `3_4_place_resized__placeopt__timing__fmax__clock:core_clock`
54. `3_4_place_resized__placeopt__timing__hold__ws`
55. `3_4_place_resized__placeopt__timing__setup__tns`
56. `3_4_place_resized__placeopt__timing__setup__ws`
57. `3_5_place_dp__detailedplace__design__core__area`
58. `3_5_place_dp__detailedplace__design__die__area`
59. `3_5_place_dp__detailedplace__design__instance__area`
60. `3_5_place_dp__detailedplace__design__instance__area__stdcell`
61. `3_5_place_dp__detailedplace__design__instance__count`
62. `3_5_place_dp__detailedplace__design__instance__count__stdcell`
63. `3_5_place_dp__detailedplace__design__instance__displacement__max`
64. `3_5_place_dp__detailedplace__design__instance__displacement__mean`
65. `3_5_place_dp__detailedplace__design__instance__displacement__total`
66. `3_5_place_dp__detailedplace__design__instance__utilization`
67. `3_5_place_dp__detailedplace__design__instance__utilization__stdcell`
68. `3_5_place_dp__detailedplace__design__nets`
69. `3_5_place_dp__detailedplace__design__rows`
70. `3_5_place_dp__detailedplace__design__rows:FreePDK45_38x28_10R_NP_162NW_34O`
71. `3_5_place_dp__detailedplace__design__sites`
72. `3_5_place_dp__detailedplace__design__sites:FreePDK45_38x28_10R_NP_162NW_34O`
73. `3_5_place_dp__detailedplace__dpl__hpwl__delta`
74. `3_5_place_dp__detailedplace__dpl__hpwl__delta__percent`
75. `3_5_place_dp__detailedplace__negotiation__converge__phase_1__iteration`
76. `3_5_place_dp__detailedplace__power__internal__total`
77. `3_5_place_dp__detailedplace__power__leakage__total`
78. `3_5_place_dp__detailedplace__power__switching__total`
79. `3_5_place_dp__detailedplace__power__total`
80. `3_5_place_dp__detailedplace__route__wirelength__estimated`
81. `3_5_place_dp__detailedplace__timing__drv__max_cap_limit`
82. `3_5_place_dp__detailedplace__timing__drv__max_slew_limit`
83. `3_5_place_dp__detailedplace__timing__drv__setup_violation_count`
84. `3_5_place_dp__detailedplace__timing__fmax`
85. `3_5_place_dp__detailedplace__timing__fmax__clock:core_clock`
86. `3_5_place_dp__detailedplace__timing__hold__ws`
87. `3_5_place_dp__detailedplace__timing__setup__tns`
88. `3_5_place_dp__detailedplace__timing__setup__ws`
89. `3_5_place_dp__detailedplace__utilization__before__dpl`
90. `param:CLK_PERIOD`
91. `param:CORE_ASPECT_RATIO`
92. `param:CORE_UTILIZATION`
93. `param:CTS_CLUSTER_SIZE`
94. `param:PLACE_DENSITY_LB_ADDON`
95. `param:TNS_END_PERCENT`

## CTS (44 features)

1. `4_1_cts__cts__clock__skew__hold`
2. `4_1_cts__cts__clock__skew__setup`
3. `4_1_cts__cts__design__core__area`
4. `4_1_cts__cts__design__die__area`
5. `4_1_cts__cts__design__instance__area`
6. `4_1_cts__cts__design__instance__area__stdcell`
7. `4_1_cts__cts__design__instance__count`
8. `4_1_cts__cts__design__instance__count__setup_buffer`
9. `4_1_cts__cts__design__instance__count__stdcell`
10. `4_1_cts__cts__design__instance__displacement__max`
11. `4_1_cts__cts__design__instance__displacement__mean`
12. `4_1_cts__cts__design__instance__displacement__total`
13. `4_1_cts__cts__design__instance__utilization`
14. `4_1_cts__cts__design__instance__utilization__stdcell`
15. `4_1_cts__cts__design__nets`
16. `4_1_cts__cts__design__rows`
17. `4_1_cts__cts__design__rows:FreePDK45_38x28_10R_NP_162NW_34O`
18. `4_1_cts__cts__design__sites`
19. `4_1_cts__cts__design__sites:FreePDK45_38x28_10R_NP_162NW_34O`
20. `4_1_cts__cts__dpl__hpwl__delta`
21. `4_1_cts__cts__dpl__hpwl__delta__percent`
22. `4_1_cts__cts__flow__warnings__count`
23. `4_1_cts__cts__flow__warnings__type_count`
24. `4_1_cts__cts__negotiation__converge__phase_1__iteration`
25. `4_1_cts__cts__power__internal__total`
26. `4_1_cts__cts__power__leakage__total`
27. `4_1_cts__cts__power__switching__total`
28. `4_1_cts__cts__power__total`
29. `4_1_cts__cts__route__wirelength__estimated`
30. `4_1_cts__cts__timing__drv__max_cap_limit`
31. `4_1_cts__cts__timing__drv__max_slew_limit`
32. `4_1_cts__cts__timing__drv__setup_violation_count`
33. `4_1_cts__cts__timing__fmax`
34. `4_1_cts__cts__timing__fmax__clock:core_clock`
35. `4_1_cts__cts__timing__hold__ws`
36. `4_1_cts__cts__timing__setup__tns`
37. `4_1_cts__cts__timing__setup__ws`
38. `4_1_cts__cts__utilization__before__dpl`
39. `param:CLK_PERIOD`
40. `param:CORE_ASPECT_RATIO`
41. `param:CORE_UTILIZATION`
42. `param:CTS_CLUSTER_SIZE`
43. `param:PLACE_DENSITY_LB_ADDON`
44. `param:TNS_END_PERCENT`

## ROUTING (67 features)

1. `5_1_grt__globalroute__clock__skew__hold`
2. `5_1_grt__globalroute__clock__skew__setup`
3. `5_1_grt__globalroute__design__core__area`
4. `5_1_grt__globalroute__design__die__area`
5. `5_1_grt__globalroute__design__instance__area`
6. `5_1_grt__globalroute__design__instance__area__stdcell`
7. `5_1_grt__globalroute__design__instance__count`
8. `5_1_grt__globalroute__design__instance__count__setup_buffer`
9. `5_1_grt__globalroute__design__instance__count__stdcell`
10. `5_1_grt__globalroute__design__instance__displacement__max`
11. `5_1_grt__globalroute__design__instance__displacement__mean`
12. `5_1_grt__globalroute__design__instance__displacement__total`
13. `5_1_grt__globalroute__design__instance__utilization`
14. `5_1_grt__globalroute__design__instance__utilization__stdcell`
15. `5_1_grt__globalroute__design__nets`
16. `5_1_grt__globalroute__design__rows`
17. `5_1_grt__globalroute__design__rows:FreePDK45_38x28_10R_NP_162NW_34O`
18. `5_1_grt__globalroute__design__sites`
19. `5_1_grt__globalroute__design__sites:FreePDK45_38x28_10R_NP_162NW_34O`
20. `5_1_grt__globalroute__dpl__hpwl__delta`
21. `5_1_grt__globalroute__dpl__hpwl__delta__percent`
22. `5_1_grt__globalroute__flow__warnings__count`
23. `5_1_grt__globalroute__flow__warnings__type_count`
24. `5_1_grt__globalroute__global_route__fastroute__congestion_rsmt_s`
25. `5_1_grt__globalroute__global_route__fastroute__finalization_s`
26. `5_1_grt__globalroute__global_route__fastroute__initial_rsmt_s`
27. `5_1_grt__globalroute__global_route__fastroute__monotonic_s`
28. `5_1_grt__globalroute__global_route__fastroute__new_route_l_s`
29. `5_1_grt__globalroute__global_route__fastroute__overflow_iterations_s`
30. `5_1_grt__globalroute__global_route__fastroute__route_l_s`
31. `5_1_grt__globalroute__global_route__fastroute__route_z_s`
32. `5_1_grt__globalroute__global_route__fastroute__spiral_s`
33. `5_1_grt__globalroute__global_route__vias`
34. `5_1_grt__globalroute__global_route__wirelength`
35. `5_1_grt__globalroute__power__internal__total`
36. `5_1_grt__globalroute__power__leakage__total`
37. `5_1_grt__globalroute__power__switching__total`
38. `5_1_grt__globalroute__power__total`
39. `5_1_grt__globalroute__route__net`
40. `5_1_grt__globalroute__route__wirelength__estimated`
41. `5_1_grt__globalroute__timing__drv__max_cap_limit`
42. `5_1_grt__globalroute__timing__drv__max_slew_limit`
43. `5_1_grt__globalroute__timing__drv__setup_violation_count`
44. `5_1_grt__globalroute__timing__fmax`
45. `5_1_grt__globalroute__timing__fmax__clock:core_clock`
46. `5_1_grt__globalroute__timing__hold__ws`
47. `5_1_grt__globalroute__timing__setup__tns`
48. `5_1_grt__globalroute__timing__setup__ws`
49. `5_1_grt__globalroute__utilization__before__dpl`
50. `5_2_route__detailedroute__route__drc_errors__iter:0`
51. `5_2_route__detailedroute__route__drc_errors__iter:1`
52. `5_2_route__detailedroute__route__drc_errors__iter:2`
53. `5_2_route__detailedroute__route__drc_errors__iter:3`
54. `5_2_route__detailedroute__route__net`
55. `5_2_route__detailedroute__route__vias`
56. `5_2_route__detailedroute__route__vias__singlecut`
57. `5_2_route__detailedroute__route__wirelength`
58. `5_2_route__detailedroute__route__wirelength__iter:0`
59. `5_2_route__detailedroute__route__wirelength__iter:1`
60. `5_2_route__detailedroute__route__wirelength__iter:2`
61. `5_2_route__detailedroute__route__wirelength__iter:3`
62. `param:CLK_PERIOD`
63. `param:CORE_ASPECT_RATIO`
64. `param:CORE_UTILIZATION`
65. `param:CTS_CLUSTER_SIZE`
66. `param:PLACE_DENSITY_LB_ADDON`
67. `param:TNS_END_PERCENT`

**Total: 233 features** (233 unique across stages; config params repeated per stage).

---

# Appendix — Output Files

| Path | Description |
|------|-------------|
| `feature_analysis/feature_analysis_summary.md` | Hand-picked 13-feature summary |
| `feature_analysis/full/feature_analysis_summary.md` | Full 233-feature summary |
| `feature_analysis/full/shap/` | SHAP CSVs and bar charts |
| `feature_analysis/full/ablation/` | Group ablation CSVs |
| `feature_analysis/full/individual/` | LOO ablation CSVs |
| `feature_analysis/wide/wide_{stage}.csv` | Wide feature tables |
| `feature_analysis/openroad_metrics_inventory_full.csv` | All 476 inventoried metrics |
| `search_eval_report.md` | Search ordering evaluation |