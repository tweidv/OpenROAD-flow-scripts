# PPA prediction experiment (GCD)

Tests whether final repaired PPA-value \(V\) can be predicted from intermediate OpenROAD checkpoint features.

## Setup

```bash
cd /home/tom/projects/openroad-exploration
source env.sh && source dev_env.sh
pip install -r experiments/ppa_prediction/requirements.txt
```

## Run everything

```bash
bash experiments/ppa_prediction/run_all.sh
```

Or step-by-step:

```bash
cd experiments/ppa_prediction
python3 run_trajectories.py --jobs 8          # parallel (recommended on 16-core VM)
python3 run_trajectories.py --skip-existing # resume incomplete runs
python3 build_dataset.py
python3 train.py
```

Dry-run configs only:

```bash
python3 run_trajectories.py --dry-run
python3 run_trajectories.py --only traj_default traj_bad_01
```

## Outputs

- `generated/trajectories.json` — perturbation manifest
- `generated/run_results.json` — per-run exit codes
- `output/dataset.csv` — training rows (4 checkpoints × N trajectories)
- `output/metrics.json` — MAE / RMSE / R² per model
- `output/scatter_*.png` — predicted vs actual
- `output/learning_curve.png` — error vs trajectory count

## PPA-value definition

Targets `(P_target, T_target, A_target)` come from the **best feasible run in the batch**:

- `P_target` = lowest `finish__power__total`
- `T_target` = highest `finish__timing__fmax`
- `A_target` = lowest `finish__design__instance__area__stdcell`

At least one completed run should score `V = 1.0`; others spread below based on how far they are from these bests.

\[
V = (V_P V_T V_A)^{1/3},\quad V_P=\min(1,P_{target}/P),\quad V_T=\min(1,T/T_{target}),\quad V_A=\min(1,A_{target}/A)
\]

If the flow fails repair/feasibility (errors, DRC > 0, missing finish), `V = 0`.

## Notes / assumptions

- ORFS does not define this PPA scalar internally; targets are baseline-derived.
- Congestion uses `globalplace__gpl__routability__congestion` at placement and routing checkpoints.
- Timing features use `inv_fmax = 1/fmax` (clock period); WNS is not used.
- Train/test split is by **trajectory id**, not by checkpoint row.
