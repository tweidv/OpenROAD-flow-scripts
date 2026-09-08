# LHS-250 quick eval (20 train / rest test)

**Completed trajectories:** see run metadata  
**Split:** 20 train, rest test (seed 42, trajectory-level — no leakage across stages)

## Where do these R² values come from?

Each number is **test-set R²** from scikit-learn: how well XGBoost predicts a **finish metric** on trajectories it was **not trained on**.

| Piece | What it is |
|-------|------------|
| **Target (y)** | Ground truth from `6_report.json`: `final_power`, `final_fmax`, or `final_area` at end of flow |
| **Features (X)** | OpenROAD checkpoint metrics at one stage (floorplan / placement / CTS / routing) |
| **Model** | XGBoost regressor (`n_estimators=80`, `max_depth=4`, same as main experiments) |
| **Train** | 20 trajectories (all 4 stages from those runs) |
| **Test** | Remaining completed trajectories (~62 when n=82) |
| **R²** | `1 − MSE(model)/MSE(mean predictor)` on **test only** — 1.0 = perfect rank/scale, 0 = no better than guessing the mean |

**Compact 3 features** (per stage): checkpoint `power__internal__total`, `design__instance__area`, `timing__setup__ws` — what OR already printed mid-flow.

**Compact + fmax** adds checkpoint `timing__fmax` (OR’s STA estimate at that stage).

**Hand-picked** uses the curated stage features from `feature_analysis.py` (utilization, HPWL, inv_fmax, TNS, etc.).

Important: high R² for **power/area** often means “OR’s checkpoint read-forward works,” not magic ML. **Fmax** without checkpoint fmax is the honest timing challenge. With checkpoint fmax at late stages, R² jumps because it’s nearly the same number as finish.

## Clock still dominates?

| Param vs final | Pearson r |
|----------------|----------:|
| CLK vs fmax | -0.488 |
| CLK vs power | -0.445 |
| CLK vs area | -0.494 |

## Test R² — compact 3 (power, area, setup_ws)

| Stage | Power | Fmax | Area |
|-------|------:|-----:|-----:|
| floorplan | 0.948 | 0.623 | 0.850 |
| placement | 0.924 | 0.489 | 0.793 |
| cts | 0.931 | 0.477 | 0.910 |
| routing | 0.931 | 0.580 | 0.930 |

## Test R² — compact + checkpoint fmax

| Stage | Power | Fmax | Area |
|-------|------:|-----:|-----:|
| floorplan | 0.951 | 0.671 | 0.840 |
| placement | 0.920 | 0.913 | 0.895 |
| cts | 0.936 | 0.923 | 0.915 |
| routing | 0.934 | 0.949 | 0.929 |

## Test R² — hand-picked stage features

| Stage | Power | Fmax | Area |
|-------|------:|-----:|-----:|
| floorplan | 0.689 | 0.502 | 0.691 |
| placement | 0.802 | 0.743 | 0.860 |
| cts | 0.940 | 0.948 | 0.924 |
| routing | 0.937 | 0.930 | 0.912 |

## vs old util×clk grid (1000 runs, 20 train)

Old grid: power R²≈0.95, fmax R²≈0.92, area R²≈0.97 with compact features.

See `quick_eval_results.csv` for full table.
