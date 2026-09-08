# Checkpoint Metrics vs Final PPA — Interpretation Report

**Date:** 2026-09-07  
**Design:** GCD (nangate45), 1000 perturbed trajectories  
**Context:** Forward feature selection (FFS) + scatter analysis of OpenROAD checkpoint metrics vs finish P/T/A

Related reports:
- `ffs_results_report.md` — full FFS test results
- `feature_selection_summary.md` — auto-generated tables
- `../feature_analysis/gcd_feature_analysis_report.md` — SHAP/ablation on full vs hand-picked features

---

## 1. Executive summary

OpenROAD already computes almost everything we need at each checkpoint. The strongest predictors of final PPA are **the same quantities OpenROAD reports mid-flow**, not obscure derived features:

| Final target | Natural OR checkpoint proxy | Typical Pearson r |
|--------------|----------------------------|-------------------|
| **Power** | `power__internal__total` | **0.998–1.000** |
| **Area** | `design__instance__area` | **0.96–1.000** |
| **Fmax** | `timing__setup__ws` (slack) | **−0.80 to −0.85** |

Forward feature selection rediscovered this: **1 feature for power, 2 for fmax** at every stage. The ML is mostly **reading OpenROAD’s own estimates forward** and ranking trajectories — not learning new physics.

**Implication:** Use a **3-feature checkpoint vector** (`internal_power`, `instance_area`, `setup_ws`) for search ordering. Don’t expect magic from 200 JSON metrics.

---

## 2. What we ran

1. **Forward feature selection** — greedy selection on validation R² (15/5 inner split, 3 seeds), test on 980 held-out trajectories. See `ffs_results_report.md`.

2. **Scatter plots** — all 1000 trajectories, colored by checkpoint stage:
   - `plots/internal_power_vs_final_{power,fmax,area}.png`
   - `plots/setup_ws_vs_final_{power,fmax,area}.png`
   - `plots/instance_area_vs_final_{power,fmax,area}.png`

---

## 3. Expected vs observed relationships

### 3.1 Internal power → final power

**Expected:** Tight positive linear relationship. Checkpoint internal power uses the same leakage/switching estimation methodology as finish power on the same netlist scale. Should look like `y ≈ x` with small noise from clock-gating, routing buffers, and CTS changes.

**Observed:** r = **0.998–1.000** at all stages. Scatter collapses to a near-diagonal line. FFS needs only this one feature (test R² ≈ 0.95).

**Interpretation:** Predicting final power from checkpoint power is almost tautological. High model R² here is **unsurprising and not evidence of deep learning** — it confirms OR’s power model is consistent across stages.

---

### 3.2 Internal power → final fmax

**Expected:** Moderate positive correlation, wide cloud. Internal power scales with instance count and activity; larger/heavier configs tend toward different timing, but **clock period (CLK_PERIOD sweep)** is the dominant fmax knob. Same power level can correspond to different fmax depending on whether the design met timing.

**Observed:** r ≈ **0.64–0.65** at all stages. Clear upward trend but substantial spread.

**Interpretation:** Power is a **proxy for design scale**, not a timing metric. Useful for coarse ranking; insufficient alone for fmax (FFS adds `setup_ws` as second feature).

---

### 3.3 Internal power → final area

**Expected:** Strong positive correlation. More cells → more area and more internal power. Not as tight as area→area because power also depends on switching activity and clock.

**Observed:** r ≈ **0.85–0.87**.

**Interpretation:** Power works for area ranking but **`design__instance__area` is the direct read** (r up to 1.0). Prefer instance area over power when area is the target.

---

### 3.4 Setup WS → final fmax

**Expected:** Negative correlation. Setup worst slack (WS) measures how far the most critical path is from meeting the clock:
- **WS > 0:** timing met at that checkpoint; room to increase fmax
- **WS < 0:** violations; fmax above current clock is not achievable without change
- Higher (less negative) slack → higher achievable fmax

Relationship is ** monotonic but not linear** when many points are negative and configs differ in CLK_PERIOD.

**Observed:** r ≈ **−0.80 to −0.85** (negative as expected). Floorplan cloud is widest because many trajectories haven’t been optimized yet.

**Interpretation:** This is the **legitimate timing signal** — what OpenROAD’s STA reports. FFS picks this (with power) for fmax at most stages. Hand-picked `inv_fmax` is the same information inverted.

---

### 3.5 Setup WS → final power

**Expected:** Negative correlation in a utilisation/clock sweep. Aggressive configs (high util, tight clock) → more instances, higher power, **worse slack**. Not causal — both driven by shared parameters (CORE_UTILIZATION, CLK_PERIOD).

**Observed:** r ≈ **−0.94 to −0.96**.

**Interpretation:** Slack is acting as a **confound proxy for aggressiveness** of the sweep point. Don’t interpret “more slack causes less power” — they co-vary with configuration.

---

### 3.6 Setup WS → final area

**Expected:** Negative correlation for the same reason — denser/larger designs (more area) often have worse slack when pushed.

**Observed:** r ≈ **−0.93 to −0.95**.

**Interpretation:** Slack is a weak area predictor compared to **`instance__area` directly** (r ≈ −0.84 for displacement vs area at CTS; r ≈ 1.0 for instance area at routing). For area targets, use structural metrics, not timing.

---

### 3.7 Instance area → final area (the “obvious” proxy)

**Expected:** Near-identity at late stages; strong at floorplan once floorplan area is fixed.

**Observed:**

| Stage | r vs final_area |
|-------|----------------|
| floorplan | 0.961 |
| placement | 0.987 |
| cts | 0.990 |
| routing | **1.000** |

**Interpretation:** Same story as power — **`design__instance__area` at routing is essentially final area**. Hand-picked HPWL/utilization are good indirect proxies; FFS sometimes picked timing features for area due to small validation set overfitting.

---

## 4. Negative setup slack — should we worry?

### Counts (setup WS < 0)

| Stage | Violations | % |
|-------|----------:|--:|
| floorplan | 574 | 57% |
| placement | 631 | 63% |
| cts | 631 | 63% |
| routing | 672 | 67% |
| **finish** | 612 | **61%** |

### Verdict: **not a data quality problem**

The batch is a **utilisation × clock grid sweep**. Most points intentionally push timing hard. Our feasibility definition is **flow completes + DRC clean** (WNS/slack not required), so 61% negative slack at finish is consistent.

### Modeling implications

1. **Early slack is a noisy fmax predictor** — many floorplan-violating runs partially recover; many don’t.
2. **Scatter plots show two regimes** — positive slack (timing met) vs negative (violated); fmax is capped differently in each.
3. **Ranking still works** — relative ordering within the sweep matters for search, even if absolute fmax prediction is hard.
4. **Don’t filter out WS < 0** unless you redefine the problem to “predict only timing-clean designs.”

---

## 5. FFS results (condensed)

Full detail in `ffs_results_report.md`.

### Compact 99% feature sets (test R²)

| Stage | Power (1f) | Fmax (2f) | Area (1f) |
|-------|----------:|----------:|----------:|
| floorplan | 0.950 | 0.923 | 0.966 |
| placement | 0.950 | 0.917 | 0.959 |
| cts | 0.949 | **0.800** ⚠ | 0.900 |
| routing | 0.950 | 0.925 | 0.950 |

**Compact beats full** for power/fmax everywhere. **Hand-picked wins** placement area (0.977), routing area (0.983), CTS fmax (0.933).

### Recommended checkpoint features

```
All stages:  power__internal__total
             design__instance__area
             timing__setup__ws
```

Optional stage-specific additions:
- **Placement/routing area:** HPWL / wirelength (hand-picked)
- **CTS fmax:** total negative slack, clock skew (hand-picked — FFS failed here)

---

## 6. What this means for the project

### 6.1 What we learned

| Claim | Supported? |
|-------|------------|
| “We need 200 ORFS metrics to predict PPA” | **No** — 1–3 suffice |
| “ML discovers hidden PPA drivers” | **Mostly no** — it selects OR’s own reports |
| “Checkpoint prediction can guide search” | **Yes** — ranking 980 trajectories works (see search eval) |
| “Early-stage fmax prediction is easy” | **No** — 60% negative slack, moderate r |
| “Power/area prediction from checkpoint is easy” | **Yes** — nearly the same metric |

### 6.2 What OpenROAD is “already predicting”

At each checkpoint OR runs (approximately):
- **Power analysis** → `power__internal__total`, etc.
- **Area accounting** → `design__instance__area`, utilization
- **Static timing** → `timing__setup__ws`, TNS, fmax

Our XGBoost models **combine and extrapolate these forward** to finish. The value add is:
1. **Trajectory ranking** for search (which config to run next)
2. **Multivariate correction** when single metrics disagree (fmax especially)
3. **Stage selection** — knowing floorplan reads are enough for power, need slack for timing

### 6.3 What to do next

1. **Search eval with compact 3-feature set** — expect similar ordering to full model for P/T; verify area ranking at placement/routing with instance_area + HPWL.

2. **Don’t over-interpret R²** — 0.95 power R² is partly identity mapping, not generalization to new designs.

3. **Document slack regime** — predictions are within a timing-stressed sweep, not spec-closure guarantees.

4. **Prefer interpretable features** in production:
   - `power__internal__total`
   - `design__instance__area`
   - `timing__setup__ws`
   - (+ HPWL for routing/placement area)

5. **Keep hand-picked for CTS fmax and late area** until a compact FFS set beats them on test.

---

## 7. Plot gallery

All in `plots/`:

| Plot | What to look for |
|------|------------------|
| `internal_power_vs_final_power.png` | Near-diagonal line; r≈1 |
| `internal_power_vs_final_fmax.png` | Upward cloud; r≈0.65 |
| `internal_power_vs_final_area.png` | Upward trend; r≈0.86 |
| `setup_ws_vs_final_fmax.png` | Negative slope; two regimes around WS=0 |
| `setup_ws_vs_final_power.png` | Negative; confounded by sweep |
| `setup_ws_vs_final_area.png` | Negative; use instance_area instead |
| `instance_area_vs_final_area.png` | Near-diagonal at routing; r→1 |
| `instance_area_vs_final_power.png` | Strong positive; scale proxy |
| `instance_area_vs_final_fmax.png` | Moderate positive; scale proxy |
| `ffs_curve_<stage>_<target>.png` | Validation R² saturates at k≤4 |

---

## 8. One-paragraph takeaway

**You should not be surprised.** Checkpoint internal power ≈ final power and checkpoint instance area ≈ final area because OpenROAD measures the same physical design at every stage. Setup slack is the native timing quality report — essential for fmax ranking, negative for ~60% of runs because the sweep explores aggressive configs. Machine learning’s job here is not to outsmart the P&R engine but to **cheaply rank which trajectory deserves the next expensive stage run** using 2–3 numbers OR already prints. The FFS experiment confirms that; the scatter plots show why.
