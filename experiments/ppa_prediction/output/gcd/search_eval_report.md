# GCD Search-Ordering Evaluation Report

**Date:** 2026-09-07 (updated)  
**Design:** GCD (nangate45)  
**Dataset:** 1000 completed perturbed trajectories  

---

## Question

Can intermediate structural checkpoint predictions order a fixed candidate set so near-optimal designs are discovered **faster than random search** — including when checkpoint reveals have **compute cost**?

This is an **offline replay**: all trajectories were already run in batch. The optimiser uses model predictions to decide order; metrics use true final PPA. It is **not** a counterfactual action-value test.

---

## PPA label

\[
V = (V_P \cdot V_T \cdot V_A)^{1/3}
\]

Targets \(P^*, T^*, A^*\) are best-of-batch across 1000 trajectories. Feasibility = flow completes + DRC clean (WNS not used).

**Test-set optimum:** `traj_sweep_104`, **V = 0.963**

---

## Method

### Data

- 1000 trajectories (23 hand-crafted + utilisation × clock grid sweep)
- 4 checkpoints per trajectory → 4000 feature rows
- XGBoost per stage predicts \(V_P, V_T, V_A\); combined to predicted \(V\)

### Splits (seed 42)

| Split | Train | Test |
|-------|------:|-----:|
| A | 100 | 900 |
| B | 20 | 980 |

Both splits use the fixed manifest split on the first 1000 trajectory IDs (all complete).

### Search strategies

**Model-guided (deterministic):** at each step, reveal the next checkpoint on the highest predicted-\(V\) active candidate; when routing is observed, fully evaluate that trajectory. Predictions are **free**.

**Random (1000 shuffled permutations, seed 42):** each run shuffles the test candidate list, then fully evaluates trajectories in that order until all are seen. Reported random metrics are the **mean/p50 over 1000 permutations**.

### Compute cost model

| What | Cost |
|------|------|
| Model prediction (XGBoost on existing features) | **Free** |
| Reading initial floorplan features for all candidates | **Free** |
| **Running** placement / CTS / routing on a design | **Paid** |

Stage run costs (relative units, ~GCD 2 min/run profile):

| Stage | Cost | Notes |
|-------|-----:|-------|
| Floorplan | 2 | Not re-run during search (free read) |
| Placement | 4 | Charged on each reveal |
| CTS | 2 | Charged on each reveal |
| Routing | 3 | Charged on each reveal |
| **Full run from scratch** | **11** | What random pays per evaluation |

---

## Results: evaluation count

| Split | Strategy | →90% | →95% | →99% | AUC | Finds optimum |
|-------|----------|-----:|-----:|-----:|----:|---------------|
| **100/900** | Random (mean) | 3.1 | 5.5 | 26.0 | 0.999 | ✓ |
| | Model-guided | **1** | **1** | **11** | 1.000 | eval **#12** |
| **20/980** | Random (mean) | 3.1 | 5.2 | 26.1 | 0.999 | ✓ |
| | Model-guided | **1** | **1** | **11** | 1.000 | eval **#12** |

Train size (20 vs 100) does **not** change search behaviour on this dataset.

### Model-guided completion order (first 12 — identical across splits)

| Eval | Trajectory | Actual V |
|-----:|------------|--------:|
| 1 | `traj_bad_03` | 0.951 |
| 2–11 | sweep cluster | 0.900–0.957 |
| **12** | **`traj_sweep_104`** | **0.963** |

---

## Results: compute cost

Cost to reach threshold (random = mean over **1000 shuffled** permutations):

| Split | Threshold | Model-guided | Random mean | Random p50 |
|-------|-----------|-------------:|------------:|-----------:|
| 100/900 | 90% | ~9 | ~49 | ~33 |
| | **95%** | **9** | **60** | **44** |
| | 99% | ~99 | ~286 | ~253 |
| 20/980 | **95%** | **9** | **57** | **44** |

**Model →95% cost = 9** = one trajectory run through placement (4) + CTS (2) + routing (3) before the first result above threshold.

**Random →95% cost ≈ 57–60** ≈ 5 full runs × 11, consistent with ~5 evaluations to 95%.

Under the run-cost model, model-guided is **~6× cheaper** than random to reach 95% of optimum.

---

## Checkpoint tally: stages actually run

Model-guided must eventually run placement, CTS, and routing on every test candidate to finish the search. Floorplan is never re-run (free initial read).

### 100 train / 900 test

| Stage | Runs | Cost units |
|-------|-----:|-----------:|
| Floorplan | 0 | 0 |
| Placement | 900 | 3600 |
| CTS | 900 | 1800 |
| Routing | 900 | 2700 |
| **Total** | **2700** | **8100** |

### 20 train / 980 test

| Stage | Runs | Cost units |
|-------|-----:|-----------:|
| Floorplan | 0 | 0 |
| Placement | 980 | 3920 |
| CTS | 980 | 1960 |
| Routing | 980 | 2940 |
| **Total** | **2940** | **8820** |

Random (to 95% only, ~5 full evals): **20 stage-runs** (5× each stage) = **55 cost units** — but only explores 5 designs fully; model-guided explores all candidates incrementally.

---

## Interpretation

### What works

- Checkpoint predictions carry enough signal to rank candidates: first full evaluation (`traj_bad_03`, V=0.951) is near-optimal
- True optimum found by eval #12 in both splits (~5× fewer evals than random for 95%)
- With run-cost accounting, model-guided reaches 95% for **9 cost units vs ~57 random** (~6× cheaper)
- Results robust to train size (20 vs 100)

### Caveats

1. **Offline replay** — all outcomes known in advance; no early abandonment of bad runs
2. **Free floorplan read** — all candidates start with floorplan features at zero cost; a stricter model would charge floorplan when first exploring a new candidate
3. **Lucky first pick** — `traj_bad_03` (hand-crafted, V=0.951) in test set inflates "1 eval to 95%"
4. **Duplicate sweep configs** — many grid points share identical parameters; model assigns identical scores
5. **Narrow V spread** — most trajectories cluster V ≈ 0.85–0.96
6. **Random is shuffled** — 1000 permutations with seed 42; p50 cost-to-95% (44) is lower than mean (57) due to lucky orderings

---

## Artifacts

```
output/gcd/
├── dataset.csv
├── targets.json
├── search_eval_report.md          ← this file
├── checkpoint_tally_summary.md    ← tally only (instant recompute)
├── search_eval/
│   ├── split_100_900/
│   └── split_20_980/
│       ├── search_eval.json
│       ├── best_vs_evaluations.png
│       └── evals_to_95pct.png
```

**Reproduce eval:**
```bash
cd experiments/ppa_prediction
.venv/bin/python build_dataset.py --design gcd --limit 1000
MPLBACKEND=Agg .venv/bin/python search_eval.py --design gcd --limit 1000 --train-size 100 --n-random 1000
MPLBACKEND=Agg .venv/bin/python search_eval.py --design gcd --limit 1000 --train-size 20 --n-random 1000
```

**Recompute checkpoint tally (instant, no re-simulation):**
```bash
.venv/bin/python tally_checkpoints.py \
  output/gcd/search_eval/split_100_900/search_eval.json \
  output/gcd/search_eval/split_20_980/search_eval.json \
  -o output/gcd/checkpoint_tally_summary.md
```

---

## Bottom line

On 1000 GCD trajectories, structural checkpoint models **accelerate search** on both evaluation-count and compute-cost metrics. Model-guided reaches 95% of the test optimum for **1 evaluation / 9 cost units** vs random **~5 evaluations / ~57 cost units** (1000 shuffled baselines). The true optimum is found by eval #12 regardless of train size. Read headline "1 eval" with skepticism due to test-set luck; the **~6× cost advantage** to 95% is the stronger claim under the run-cost model.
