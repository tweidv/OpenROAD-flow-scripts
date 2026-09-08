# Floorplan MLP mock — params → floorplan PPA

**Dataset:** `/data/projects/openroad-exploration/experiments/ppa_prediction/output/gcd/lhs250/floorplan_param_explore.csv`
**Subset:** all (600 trajectories)
**Split:** 20 train / 580 test (trajectory-level)
**Features:** 14 physical knobs (no RTL graph, no CLK in fclk subset)

**Models per metric:** mean baseline, linear, separate MLP `(64, 32)` + StandardScaler

| target | model | R² | MAE | NMAE % | rank ρ | baseline MAE |
|--------|-------|---:|----:|-------:|-------:|-------------:|
| power | mean | -0.015 | 0.0005164 | 87.6 | nan | 0.0005164 |
| power | linear | -1.275 | 0.0007215 | 122.3 | 0.005 | 0.0005164 |
| power | mlp | -26089.947 | 0.0769 | 13039.1 | 0.016 | 0.0005164 |
| | *(test σ=0.0005898)* | | | | | |
| area | mean | -0.029 | 20.23 | 83.4 | nan | 20.23 |
| area | linear | -1.910 | 33.97 | 140.0 | -0.081 | 20.23 |
| area | mlp | -47.181 | 142.3 | 586.4 | -0.065 | 20.23 |
| | *(test σ=24.27)* | | | | | |
| wns | mean | -0.028 | 0.09845 | 84.2 | nan | 0.09845 |
| wns | linear | -1.612 | 0.1522 | 130.0 | -0.011 | 0.09845 |
| wns | mlp | -0.675 | 0.1179 | 100.8 | -0.059 | 0.09845 |
| | *(test σ=0.117)* | | | | | |
| tns | mean | -0.006 | 2.776 | 92.0 | nan | 2.776 |
| tns | linear | -1.209 | 3.661 | 121.3 | -0.005 | 2.776 |
| tns | mlp | -0.290 | 2.905 | 96.2 | -0.112 | 2.776 |
| | *(test σ=3.019)* | | | | | |

**Notes:**
- GCD floorplan targets have low variance (~1% on power/area/WNS for fixed-CLK batch).
- Negative R² means worse than predicting the train mean.
- NMAE = MAE / σ(test); rank ρ = Spearman ordinal correlation (FastPASE-style).
