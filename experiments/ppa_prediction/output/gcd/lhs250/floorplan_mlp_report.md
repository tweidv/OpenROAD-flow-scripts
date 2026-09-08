# Floorplan MLP mock — params → floorplan PPA

**Dataset:** `/data/projects/openroad-exploration/experiments/ppa_prediction/output/gcd/lhs250/floorplan_param_explore.csv`
**Subset:** fclk (250 trajectories)
**Split:** 80 train / 170 test (trajectory-level)
**Features:** 14 physical knobs (no RTL graph, no CLK in fclk subset)

**Models per metric:** mean baseline, linear, separate MLP `(64, 32)` + StandardScaler

| target | model | R² | MAE | NMAE % | rank ρ | baseline MAE |
|--------|-------|---:|----:|-------:|-------:|-------------:|
| power | mean | -0.004 | 1.621e-05 | 70.9 | nan | 1.621e-05 |
| power | linear | 0.537 | 1.18e-05 | 51.6 | 0.879 | 1.621e-05 |
| power | mlp | 0.398 | 1.219e-05 | 53.3 | 0.718 | 1.621e-05 |
| | *(test σ=2.286e-05)* | | | | | |
| area | mean | -0.001 | 4.346 | 67.1 | nan | 4.346 |
| area | linear | 0.498 | 3.287 | 50.7 | 0.774 | 4.346 |
| area | mlp | 0.380 | 3.322 | 51.3 | 0.671 | 4.346 |
| | *(test σ=6.482)* | | | | | |
| wns | mean | -0.003 | 1.089e-05 | 51.1 | nan | 1.089e-05 |
| wns | linear | 0.204 | 1.288e-05 | 60.5 | 0.486 | 1.089e-05 |
| wns | mlp | 0.216 | 1.08e-05 | 50.7 | 0.368 | 1.089e-05 |
| | *(test σ=2.13e-05)* | | | | | |
| tns | mean | -0.021 | 0.03219 | 87.7 | nan | 0.03219 |
| tns | linear | 0.642 | 0.01648 | 44.9 | 0.902 | 0.03219 |
| tns | mlp | 0.533 | 0.01837 | 50.0 | 0.822 | 0.03219 |
| | *(test σ=0.03671)* | | | | | |

**Notes:**
- GCD floorplan targets have low variance (~1% on power/area/WNS for fixed-CLK batch).
- Negative R² means worse than predicting the train mean.
- NMAE = MAE / σ(test); rank ρ = Spearman ordinal correlation (FastPASE-style).
