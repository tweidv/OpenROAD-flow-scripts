# GCD Feature Analysis Summary

Design: gcd  |  Trajectories: 1000  |  Split: 20 train / 980 test

Primary targets: `final_power`, `final_fmax`, `final_area` (from finish metrics).
Inputs: structural checkpoint features only (no norm_p/t/a).

Model: XGBoost {'n_estimators': 80, 'max_depth': 4, 'learning_rate': 0.1, 'subsample': 0.9, 'colsample_bytree': 0.9, 'random_state': 42, 'objective': 'reg:squarederror'}

## Feature inventory

See `feature_inventory.csv` (16 feature×stage rows).

### Features per stage

**floorplan:** core_area, utilization, aspect_ratio
  - groups: floorplan(3)

**placement:** hpwl, placement_density, estimated_congestion, inv_fmax
  - groups: placement(2), congestion(1), timing(1)

**cts:** inv_fmax, total_negative_slack, clock_skew, buffer_inverter_count
  - groups: timing(2), cts(2)

**routing:** routed_wirelength, inv_fmax, total_negative_slack, congestion, drc_violation_count
  - groups: routing(2), timing(2), congestion(1)

## Full-model test R² (by stage × target)

| Stage | Power | Fmax | Area |
|-------|------:|-----:|-----:|
| floorplan | 0.863 | 0.589 | 0.887 |
| placement | 0.902 | 0.894 | 0.977 |
| cts | 0.908 | 0.933 | 0.940 |
| routing | 0.942 | 0.910 | 0.983 |

## FLOORPLAN

### Power

Top 10 SHAP:

- `utilization` |SHAP|=0.002243
- `core_area` |SHAP|=0
- `aspect_ratio` |SHAP|=0

Top 10 ablation (ΔR² when removed):

- `utilization` ΔR²=0.9525
- `core_area` ΔR²=-0.0005
- `aspect_ratio` ΔR²=-0.0011

### Fmax

Top 10 SHAP:

- `utilization` |SHAP|=7.043e+07
- `core_area` |SHAP|=0
- `aspect_ratio` |SHAP|=0

Top 10 ablation (ΔR² when removed):

- `utilization` ΔR²=0.6029
- `core_area` ΔR²=-0.0022
- `aspect_ratio` ΔR²=-0.0061

### Area

Top 10 SHAP:

- `utilization` |SHAP|=112.2
- `core_area` |SHAP|=0
- `aspect_ratio` |SHAP|=0

Top 10 ablation (ΔR² when removed):

- `utilization` ΔR²=1.0142
- `core_area` ΔR²=-0.0016
- `aspect_ratio` ΔR²=-0.0020

Largest group ablations (mean ΔR² across targets):


SHAP vs ablation Spearman ρ by target:
- power: ρ=1.000
- fmax: ρ=1.000
- area: ρ=1.000


## PLACEMENT

### Power

Top 10 SHAP:

- `placement_density` |SHAP|=0.00115
- `inv_fmax` |SHAP|=0.0009021
- `hpwl` |SHAP|=0.0004405
- `estimated_congestion` |SHAP|=1.395e-05

Top 10 ablation (ΔR² when removed):

- `placement_density` ΔR²=0.0985
- `inv_fmax` ΔR²=-0.0088
- `estimated_congestion` ΔR²=-0.0103
- `hpwl` ΔR²=-0.0166

### Fmax

Top 10 SHAP:

- `hpwl` |SHAP|=4.248e+07
- `placement_density` |SHAP|=3.159e+07
- `estimated_congestion` |SHAP|=4.808e+06
- `inv_fmax` |SHAP|=4.661e+06

Top 10 ablation (ΔR² when removed):

- `placement_density` ΔR²=-0.0129
- `inv_fmax` ΔR²=-0.0140
- `hpwl` ΔR²=-0.0173
- `estimated_congestion` ΔR²=-0.0272

### Area

Top 10 SHAP:

- `hpwl` |SHAP|=55.89
- `placement_density` |SHAP|=53.29
- `inv_fmax` |SHAP|=12.43
- `estimated_congestion` |SHAP|=1.858

Top 10 ablation (ΔR² when removed):

- `placement_density` ΔR²=0.0084
- `hpwl` ΔR²=0.0007
- `inv_fmax` ΔR²=-0.0024
- `estimated_congestion` ΔR²=-0.0033

Largest group ablations (mean ΔR² across targets):

- `-placement`: ΔR²=0.2705
- `-timing`: ΔR²=-0.0084
- `-congestion`: ΔR²=-0.0136

SHAP vs ablation Spearman ρ by target:
- power: ρ=0.800
- fmax: ρ=0.000
- area: ρ=0.800


## CTS

### Power

Top 10 SHAP:

- `total_negative_slack` |SHAP|=0.001392
- `buffer_inverter_count` |SHAP|=0.0005652
- `inv_fmax` |SHAP|=0.0005081
- `clock_skew` |SHAP|=0

Top 10 ablation (ΔR² when removed):

- `total_negative_slack` ΔR²=0.2563
- `buffer_inverter_count` ΔR²=-0.0036
- `clock_skew` ΔR²=-0.0127
- `inv_fmax` ΔR²=-0.0175

### Fmax

Top 10 SHAP:

- `inv_fmax` |SHAP|=3.811e+07
- `total_negative_slack` |SHAP|=3.014e+07
- `clock_skew` |SHAP|=6.948e+06
- `buffer_inverter_count` |SHAP|=2.665e+06

Top 10 ablation (ΔR² when removed):

- `inv_fmax` ΔR²=0.1859
- `total_negative_slack` ΔR²=-0.0026
- `clock_skew` ΔR²=-0.0059
- `buffer_inverter_count` ΔR²=-0.0139

### Area

Top 10 SHAP:

- `inv_fmax` |SHAP|=62.94
- `total_negative_slack` |SHAP|=45.71
- `clock_skew` |SHAP|=5.756
- `buffer_inverter_count` |SHAP|=2.246

Top 10 ablation (ΔR² when removed):

- `total_negative_slack` ΔR²=0.0272
- `buffer_inverter_count` ΔR²=0.0055
- `clock_skew` ΔR²=-0.0104
- `inv_fmax` ΔR²=-0.0123

Largest group ablations (mean ΔR² across targets):

- `-timing`: ΔR²=0.2862
- `-cts`: ΔR²=0.0339

SHAP vs ablation Spearman ρ by target:
- power: ρ=0.800
- fmax: ρ=1.000
- area: ρ=-0.400


## ROUTING

### Power

Top 10 SHAP:

- `total_negative_slack` |SHAP|=0.001388
- `routed_wirelength` |SHAP|=0.0007674
- `inv_fmax` |SHAP|=0.0002528
- `congestion` |SHAP|=2.317e-05
- `drc_violation_count` |SHAP|=0

Top 10 ablation (ΔR² when removed):

- `total_negative_slack` ΔR²=0.0991
- `routed_wirelength` ΔR²=0.0568
- `inv_fmax` ΔR²=-0.0059
- `congestion` ΔR²=-0.0084
- `drc_violation_count` ΔR²=-0.0084

### Fmax

Top 10 SHAP:

- `routed_wirelength` |SHAP|=5.738e+07
- `inv_fmax` |SHAP|=1.994e+07
- `total_negative_slack` |SHAP|=6.356e+06
- `congestion` |SHAP|=5.259e+06
- `drc_violation_count` |SHAP|=0

Top 10 ablation (ΔR² when removed):

- `inv_fmax` ΔR²=0.0157
- `congestion` ΔR²=0.0015
- `total_negative_slack` ΔR²=-0.0225
- `drc_violation_count` ΔR²=-0.0228
- `routed_wirelength` ΔR²=-0.0619

### Area

Top 10 SHAP:

- `routed_wirelength` |SHAP|=67.92
- `total_negative_slack` |SHAP|=46.07
- `inv_fmax` |SHAP|=3.841
- `congestion` |SHAP|=0.9178
- `drc_violation_count` |SHAP|=0

Top 10 ablation (ΔR² when removed):

- `routed_wirelength` ΔR²=0.0513
- `total_negative_slack` ΔR²=0.0219
- `drc_violation_count` ΔR²=-0.0038
- `congestion` ΔR²=-0.0060
- `inv_fmax` ΔR²=-0.0064

Largest group ablations (mean ΔR² across targets):

- `-timing`: ΔR²=0.1096
- `-routing`: ΔR²=-0.0015
- `-congestion`: ΔR²=-0.0043

SHAP vs ablation Spearman ρ by target:
- power: ρ=1.000
- fmax: ρ=-0.100
- area: ρ=0.600
