# PPA Prediction Experiment — GCD Report

**Project:** OpenROAD-flow-scripts GCD (nangate45)  
**Goal:** Test whether final repaired PPA-value \(V\) can be predicted from intermediate OpenROAD checkpoint features, to support early skip/continue decisions during RTL-to-GDS runs.

---

## What we built

An end-to-end pipeline under `experiments/ppa_prediction/`:

| Component | Purpose |
|-----------|---------|
| `perturbations.py` | 74 hand-crafted + grid-swept flow configs (util, clock, density, aspect, CTS) |
| `run_trajectories.py` | Batch ORFS runs (`--jobs 8`, `--skip-existing`) |
| `features.py` | Checkpoint features at floorplan, placement, CTS, routing |
| `ppa_value.py` | Final label \(V\) and batch-derived targets |
| `build_dataset.py` / `train.py` | Dataset CSV + XGBoost train/eval (trajectory-level train/test split) |

Each completed trajectory yields **4 training rows** (one per checkpoint), all labelled with the same final \(V\).

---

## PPA label and targets

**Final repaired PPA-value** (feasibility failures → \(V=0\)):

\[
V = (V_P \cdot V_T \cdot V_A)^{1/3}
\]

- \(V_P = \min(1,\, P_\text{target}/P)\) — power (lower is better)
- \(V_T = \min(1,\, T/T_\text{target}\) — fmax (higher is better)
- \(V_A = \min(1,\, A_\text{target}/A)\) — stdcell area (lower is better)

**Targets** are the best feasible P/T/A observed across the batch (not a single baseline run). On GCD this gives \(V \in [0.43,\, 0.96]\) with meaningful spread.

**No lookahead:** features use only metrics available at the checkpoint. Normalised P/T/A (`norm_p`, `norm_t`, `norm_a`) are current-stage power/fmax/area against fixed targets — valid for skip/continue decisions.

---

## Data generated

| | Count |
|--|-------|
| Trajectories configured | 74 |
| Completed to GDS/signoff | 74 |
| Training rows | **296** (74 × 4 checkpoints) |
| Train / test split | 55 / 19 trajectories |

Runs executed in parallel (~8 jobs on 16 cores). Full batch wall time ~1.5 h for the expanded sweep.

---

## Features and models

**Structural features:** core area, utilisation, HPWL, congestion, `inv_fmax`, TNS, skew, buffer count, routed wirelength, DRC count, stage id.

**Normalised P/T/A features:** checkpoint power, fmax, area expressed against batch targets (same direction as \(V_P, V_T, V_A\)).

**Model:** XGBoost regression; 75/25 trajectory holdout (checkpoints from the same run never leak across train/test).

---

## Results (norm P/T/A model, test set)

| Checkpoint | Test MAE | Test R² |
|------------|----------|---------|
| Floorplan | 0.025 | 0.70 |
| Placement | 0.011 | 0.97 |
| CTS | 0.007 | 0.99 |
| Routing | 0.007 | 0.98 |
| **Combined** | **0.009** | **0.98** |

All beat the mean-predictor baseline (MAE ≈ 0.089). Structural features alone (no norm P/T/A): combined R² ≈ 0.74.

Outputs: `output/metrics.json`, `output/dataset.csv`, scatter plots per stage.

---

## What GCD proved

1. **The prediction problem is learnable** with ~55–75 trajectories and no lookahead — at least on this design, late-checkpoint features predict final \(V\) reliably on held-out runs.

2. **Early decision is feasible in principle.** By placement, predicted \(V\) is already close to final \(V\) (R² ≈ 0.97). A skip/continue policy based on predicted \(V\) at an intermediate checkpoint is technically sound.

3. **Intermediate normalised PPA is the strongest signal.** Late-stage power, fmax, and area at a checkpoint track final PPA because they change little after placement on GCD. This is expected behaviour, not leakage.

4. **Most flow perturbations barely move \(V\) on GCD.** Clock period explains ~97% of label variance (corr ≈ 0.98). Utilisation, aspect ratio, density, and CTS settings cause only small residual spread within a fixed clock.

---

## Caveats and limits

- **GCD is tiny** (~250 cells). Results do not automatically transfer to ibex/jpeg-scale designs.
- **High late-stage R² reflects design simplicity**, not magic: routing PPA ≈ final PPA.
- **Floorplan remains hard** (R² ≈ 0.7 with norm features; ≈ 0.14 without) — early abort decisions would be noisier.
- **Batch targets** for normalisation should become fixed design specs in production, not recomputed from the full sweep.
- **35 distinct \(V\) values** across 74 runs — label diversity is moderate, not exhaustive.

---

## Conclusion

On GCD we showed that **non-lookahead checkpoint features can predict final repaired PPA-value well enough to support early run termination**, especially from placement onward. The experiment does **not** yet answer how many trajectories larger designs need, nor whether structural features alone (without intermediate PPA readouts) suffice. Next step: repeat on **ibex** with fixed spec targets and a skip/continue policy simulation.
