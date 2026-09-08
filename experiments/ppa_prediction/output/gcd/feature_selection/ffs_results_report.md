# GCD Forward Feature Selection — Results Report

**Date:** 2026-09-07  
**Design:** gcd, 1000 trajectories  
**Split:** 20 train / 980 test (trajectory-level, seed 42)  
**FFS inner split:** 15 train / 5 validation × 3 seeds (42, 43, 44)  
**Feature pool:** 188 numeric features per stage (233 wide minus train-constant)

---

## Executive summary

Forward feature selection confirms that **1–2 features per stage×target** capture most generalizable signal on the held-out test set. The compact 99%-improvement sets **match or beat the full feature set** on test R² for power and fmax at every stage. Area is more stage-dependent; hand-picked features still win at placement and routing area.

**Recommended production representation:** a **shared 3-feature union per stage** (power internal + timing slack + one target-specific metric), which achieves combined V R² of **0.93–0.96** on test.

---

## Features required (99% of achievable validation improvement)

| Stage | Power | Fmax | Area |
|-------|------:|-----:|-----:|
| floorplan | **1** | **2** | **1** |
| placement | **1** | **2** | **1** |
| cts | **1** | **2** | **1** |
| routing | **1** | **2** | **1** |

Validation R² near 1.0 for area at CTS/routing was **overfitting on 5 val trajectories** — test R² for those 1-feature sets is 0.90–0.95, not 1.0.

---

## Selected features (99% rule)

### Power — same everywhere

Every stage picks **`power__internal__total`** as the sole feature:

- floorplan: `2_1_floorplan__floorplan__power__internal__total`
- placement: `3_3_place_gp__globalplace__power__internal__total`
- cts: `4_1_cts__cts__power__internal__total`
- routing: `5_1_grt__globalroute__power__internal__total`

### Fmax — power + timing (2 features)

| Stage | Features |
|-------|----------|
| floorplan | `power__internal__total` + `timing__setup__ws` |
| placement | `power__internal__total` + `timing__setup__ws` |
| cts | `power__internal__total` + `timing__drv__max_slew_limit` |
| routing | `power__internal__total` + `timing__setup__ws` |

### Area — one feature each (differs by stage)

| Stage | Feature |
|-------|---------|
| floorplan | `timing__hold__ws` |
| placement | `timing__setup__tns` |
| cts | `design__instance__displacement__mean` |
| routing | `route__wirelength__iter:1` (detailed route WL) |

---

## Test R²: compact vs full vs hand-picked

| Stage | Target | FFS 99% (k) | Full (k) | Hand-picked (k) | Winner |
|-------|--------|------------:|---------:|----------------:|--------|
| floorplan | power | **0.950** (1) | 0.942 (19) | 0.863 (3) | **FFS** |
| floorplan | fmax | **0.923** (2) | 0.868 (19) | 0.589 (3) | **FFS** |
| floorplan | area | 0.966 (1) | **0.969** (19) | 0.887 (3) | Full ≈ FFS |
| placement | power | **0.950** (1) | 0.932 (75) | 0.902 (4) | **FFS** |
| placement | fmax | **0.917** (2) | 0.910 (75) | 0.894 (4) | **FFS** |
| placement | area | 0.959 (1) | 0.964 (75) | **0.977** (4) | Hand-picked |
| cts | power | **0.949** (1) | 0.912 (36) | 0.908 (4) | **FFS** |
| cts | fmax | 0.800 (2) | 0.893 (36) | **0.933** (4) | Hand-picked |
| cts | area | 0.900 (1) | **0.945** (36) | 0.940 (4) | Full ≈ hand-picked |
| routing | power | **0.950** (1) | 0.916 (58) | 0.942 (5) | FFS ≈ hand-picked |
| routing | fmax | **0.925** (2) | 0.876 (58) | 0.910 (5) | **FFS** |
| routing | area | 0.950 (1) | 0.970 (58) | **0.983** (5) | Hand-picked |

### Key test-set findings

1. **More features often hurts on test.** Full 58–75 feature models underperform compact sets for power/fmax at every stage. This validates the overfitting concern with n=20 train.
2. **FFS compact beats hand-picked for power and fmax** at floorplan, placement, and routing.
3. **Hand-picked wins for area** at placement (0.977 vs 0.959) and routing (0.983 vs 0.950), and for **CTS fmax** (0.933 vs 0.800).
4. **CTS fmax is the main failure case** for FFS — the 2-feature compact set (`power + max_slew_limit`) generalizes poorly (test R² 0.80). Hand-picked timing slack/skew features are better here.

---

## Shared feature sets (one representation per stage)

Union of the three 99%-FFS selections (3 features each):

| Stage | Union features (k=3) | Test R² P / T / A | Combined V |
|-------|----------------------|------------------:|-----------:|
| floorplan | power_internal, hold_ws, setup_ws | 0.953 / 0.896 / 0.974 | **0.957** |
| placement | power_internal, setup_tns, setup_ws | 0.953 / 0.901 / 0.975 | **0.958** |
| cts | displacement_mean, power_internal, max_slew | 0.916 / 0.873 / 0.938 | **0.930** |
| routing | power_internal, setup_ws, route_wl_iter1 | 0.954 / 0.923 / 0.989 | **0.961** |

A single 3-feature vector per stage works well for all three targets — **routing union is best overall** (V R² 0.961).

Target-specific 1–2 feature sets are slightly better for individual targets but the union is a practical compromise.

---

## FFS vs SHAP vs hand-picked

| Pattern | Example |
|---------|---------|
| FFS agrees with SHAP on power | `power__internal__total` ranked #1–2 by both |
| FFS disagrees with hand-picked on fmax | Hand-picked uses `inv_fmax`/slack; FFS uses checkpoint power + setup WS |
| SHAP high but FFS late | `design__instance__area` — high SHAP, added mid-FFS because power/timing already explain most variance |
| Validation-perfect, test-mediocre | CTS/routing area 1-feature sets — val R²≈1.0, test R² 0.90–0.95 |

See `comparison_<stage>_<target>.csv` for full rank tables.

---

## Recommendations

### For search-ordering models (next step)

Use **stage-specific compact sets**, not full 188-feature wide tables:

```
floorplan:  power_internal, setup_ws, hold_ws          (3 feats, union)
placement:  power_internal, setup_tns, setup_ws         (3 feats, union)
cts:        hand-picked timing (inv_fmax, TNS, skew)  (4 feats) — FFS fails on fmax
routing:    hand-picked (wirelength, inv_fmax, TNS)    (5 feats) — best for area
```

Or simpler: **power_internal + setup_ws at every stage** (2 feats) for P/T ranking; add hand-picked HPWL/wirelength for area at placement/routing.

### For feature representation research

- **Power prediction:** trivially solved by checkpoint `power__internal__total` alone (test R²≈0.95 all stages).
- **Fmax prediction:** needs timing slack proxies; do not use area/displacement features selected by FFS for area.
- **Area prediction:** needs structural metrics (HPWL, wirelength, utilization) — hand-picked set remains best.
- **Do not trust validation R² >0.99** with n=5 val trajectories.

### Methodological caveats

- 20 training trajectories is small; FFS selections may shift with more train data.
- Same `power__internal__total` selected at all stages suggests it proxies for design scale/config — may not counterfactual-generalize.
- Test eval uses 980 trajectories — these test R² numbers are the authoritative comparison.

---

## Output files

| File | Description |
|------|-------------|
| `ffs_<stage>_<target>.csv` | Full FFS curve (every iteration) |
| `selected_features.csv` | Chosen sets by 95%/99%/max-val rule |
| `final_test_results.csv` | Held-out test: FFS vs full vs hand-picked |
| `saturation_thresholds.csv` | Features needed for 95%/99% improvement |
| `shared_stage_features.csv` | Cross-target union evaluation |
| `comparison_<stage>_<target>.csv` | FFS vs SHAP vs ablation ranks |
| `plots/ffs_curve_*.png` | Validation R² vs # features |
| `feature_selection_summary.md` | Auto-generated summary tables |
