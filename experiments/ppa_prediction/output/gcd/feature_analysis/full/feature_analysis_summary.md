# Full ORFS Metrics — Feature Analysis

**Mode:** all JSON metrics from existing logs (no new OpenROAD runs)
**Trajectories:** 1000  |  **Split:** 20 train / 980 test

## Features per stage

- **floorplan:** 27 features
- **placement:** 95 features
- **cts:** 44 features
- **routing:** 67 features

## Full-model test R²

| Stage | Power | Fmax | Area |
|-------|------:|-----:|-----:|
| floorplan | 0.942 | 0.871 | 0.969 |
| placement | 0.932 | 0.903 | 0.965 |
| cts | 0.911 | 0.888 | 0.946 |
| routing | 0.915 | 0.875 | 0.967 |

## FLOORPLAN

### Top 15 SHAP → power

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
- `2_1_floorplan__floorplan__design__sites:FreePDK45_38x28_10R_NP_162NW_34O` |SHAP|=0
- `2_1_floorplan__floorplan__flow__warnings__count` |SHAP|=0
- `2_1_floorplan__floorplan__flow__warnings__type_count` |SHAP|=0
- `2_1_floorplan__floorplan__power__leakage__total` |SHAP|=0
- `2_1_floorplan__floorplan__power__switching__total` |SHAP|=0

### Top 15 SHAP → fmax

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
- `2_1_floorplan__floorplan__design__rows` |SHAP|=0
- `2_1_floorplan__floorplan__design__rows:FreePDK45_38x28_10R_NP_162NW_34O` |SHAP|=0
- `2_1_floorplan__floorplan__design__sites` |SHAP|=0
- `2_1_floorplan__floorplan__design__sites:FreePDK45_38x28_10R_NP_162NW_34O` |SHAP|=0
- `2_1_floorplan__floorplan__flow__warnings__count` |SHAP|=0

### Top 15 SHAP → area

- `2_1_floorplan__floorplan__design__instance__area` |SHAP|=89.7
- `2_1_floorplan__floorplan__power__internal__total` |SHAP|=19.44
- `2_1_floorplan__floorplan__design__instance__area__stdcell` |SHAP|=13.89
- `param:CORE_UTILIZATION` |SHAP|=2.246
- `2_1_floorplan__floorplan__power__total` |SHAP|=0.4583
- `2_1_floorplan__floorplan__power__switching__total` |SHAP|=0.2059
- `param:CTS_CLUSTER_SIZE` |SHAP|=0.01133
- `2_1_floorplan__floorplan__design__core__area` |SHAP|=0
- `2_1_floorplan__floorplan__design__die__area` |SHAP|=0
- `2_1_floorplan__floorplan__design__instance__utilization` |SHAP|=0
- `2_1_floorplan__floorplan__design__instance__utilization__stdcell` |SHAP|=0
- `2_1_floorplan__floorplan__design__rows` |SHAP|=0
- `2_1_floorplan__floorplan__design__rows:FreePDK45_38x28_10R_NP_162NW_34O` |SHAP|=0
- `2_1_floorplan__floorplan__design__sites` |SHAP|=0
- `2_1_floorplan__floorplan__design__sites:FreePDK45_38x28_10R_NP_162NW_34O` |SHAP|=0

### Top 10 ablation → power

- `2_1_floorplan__floorplan__design__instance__area` ΔR²=0.0012
- `2_1_floorplan__floorplan__design__instance__area__stdcell` ΔR²=0.0012
- `2_1_floorplan__floorplan__design__instance__utilization` ΔR²=0.0003
- `2_1_floorplan__floorplan__design__instance__utilization__stdcell` ΔR²=0.0003
- `2_1_floorplan__floorplan__design__rows` ΔR²=0.0003
- `2_1_floorplan__floorplan__design__rows:FreePDK45_38x28_10R_NP_162NW_34O` ΔR²=0.0003
- `2_1_floorplan__floorplan__design__sites` ΔR²=0.0003
- `2_1_floorplan__floorplan__design__sites:FreePDK45_38x28_10R_NP_162NW_34O` ΔR²=0.0003
- `2_1_floorplan__floorplan__flow__warnings__count` ΔR²=0.0003
- `2_1_floorplan__floorplan__flow__warnings__type_count` ΔR²=0.0003

### Top 10 ablation → fmax

- `2_1_floorplan__floorplan__design__instance__utilization` ΔR²=0.0033
- `2_1_floorplan__floorplan__design__instance__utilization__stdcell` ΔR²=0.0033
- `2_1_floorplan__floorplan__design__rows` ΔR²=0.0033
- `2_1_floorplan__floorplan__design__rows:FreePDK45_38x28_10R_NP_162NW_34O` ΔR²=0.0033
- `2_1_floorplan__floorplan__design__sites` ΔR²=0.0033
- `2_1_floorplan__floorplan__design__sites:FreePDK45_38x28_10R_NP_162NW_34O` ΔR²=0.0033
- `2_1_floorplan__floorplan__flow__warnings__count` ΔR²=0.0033
- `2_1_floorplan__floorplan__flow__warnings__type_count` ΔR²=0.0033
- `2_1_floorplan__floorplan__power__leakage__total` ΔR²=0.0033
- `2_1_floorplan__floorplan__power__switching__total` ΔR²=0.0033

### Top 10 ablation → area

- `param:CORE_UTILIZATION` ΔR²=0.0025
- `2_1_floorplan__floorplan__design__core__area` ΔR²=0.0003
- `2_1_floorplan__floorplan__design__die__area` ΔR²=0.0003
- `2_1_floorplan__floorplan__design__instance__utilization` ΔR²=0.0003
- `2_1_floorplan__floorplan__design__instance__utilization__stdcell` ΔR²=0.0003
- `2_1_floorplan__floorplan__design__rows` ΔR²=0.0003
- `2_1_floorplan__floorplan__design__rows:FreePDK45_38x28_10R_NP_162NW_34O` ΔR²=0.0003
- `2_1_floorplan__floorplan__design__sites` ΔR²=0.0003
- `2_1_floorplan__floorplan__design__sites:FreePDK45_38x28_10R_NP_162NW_34O` ΔR²=0.0003
- `2_1_floorplan__floorplan__flow__warnings__count` ΔR²=0.0003

### Group ablations (mean ΔR²)

- `-floorplan`: 0.0117
- `-configuration`: -0.0006


## PLACEMENT

### Top 15 SHAP → power

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
- `3_3_place_gp__globalplace__design__instance__utilization__stdcell` |SHAP|=0
- `3_3_place_gp__globalplace__design__nets` |SHAP|=0
- `3_3_place_gp__globalplace__design__rows` |SHAP|=0
- `3_3_place_gp__globalplace__design__rows:FreePDK45_38x28_10R_NP_162NW_34O` |SHAP|=0
- `3_3_place_gp__globalplace__design__sites` |SHAP|=0

### Top 15 SHAP → fmax

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
- `3_3_place_gp__globalplace__power__internal__total` |SHAP|=3.767e+05
- `3_5_place_dp__detailedplace__dpl__hpwl__delta` |SHAP|=3.487e+05
- `3_3_place_gp__globalplace__power__switching__total` |SHAP|=2.826e+05
- `3_5_place_dp__detailedplace__timing__hold__ws` |SHAP|=2.81e+05
- `3_3_place_gp__globalplace__timing__hold__ws` |SHAP|=2.168e+05

### Top 15 SHAP → area

- `3_3_place_gp__globalplace__design__instance__area` |SHAP|=93.37
- `3_3_place_gp__globalplace__design__instance__area__stdcell` |SHAP|=15.01
- `3_3_place_gp__globalplace__design__instance__count` |SHAP|=11.57
- `3_5_place_dp__detailedplace__timing__fmax` |SHAP|=2.526
- `3_3_place_gp__globalplace__gpl__routability__iteration` |SHAP|=1.792
- `3_5_place_dp__detailedplace__timing__fmax__clock:core_clock` |SHAP|=0.6392
- `3_5_place_dp__detailedplace__design__instance__displacement__total` |SHAP|=0.4923
- `3_3_place_gp__globalplace__gpl__area__original` |SHAP|=0.4503
- `3_3_place_gp__globalplace__gpl__convergence__iteration` |SHAP|=0.325
- `3_4_place_resized__placeopt__timing__drv__max_slew_limit` |SHAP|=0.2561
- `param:CORE_UTILIZATION` |SHAP|=0.1751
- `3_3_place_gp__globalplace__gpl__routability__congestion` |SHAP|=0.1481
- `3_5_place_dp__detailedplace__design__instance__displacement__mean` |SHAP|=0.106
- `3_5_place_dp__detailedplace__design__instance__displacement__max` |SHAP|=0.04909
- `3_3_place_gp__globalplace__route__wirelength__estimated` |SHAP|=0.04469

### Top 10 ablation → power

- `3_3_place_gp__globalplace__design__core__area` ΔR²=0.0003
- `3_3_place_gp__globalplace__design__die__area` ΔR²=0.0003
- `3_3_place_gp__globalplace__design__instance__count` ΔR²=0.0003
- `3_3_place_gp__globalplace__design__instance__count__stdcell` ΔR²=0.0003
- `3_3_place_gp__globalplace__design__instance__utilization` ΔR²=0.0003
- `3_3_place_gp__globalplace__design__instance__utilization__stdcell` ΔR²=0.0003
- `3_3_place_gp__globalplace__design__nets` ΔR²=0.0003
- `3_3_place_gp__globalplace__design__rows` ΔR²=0.0003
- `3_3_place_gp__globalplace__design__rows:FreePDK45_38x28_10R_NP_162NW_34O` ΔR²=0.0003
- `3_3_place_gp__globalplace__design__sites` ΔR²=0.0003

### Top 10 ablation → fmax

- `3_5_place_dp__detailedplace__timing__drv__max_cap_limit` ΔR²=0.0045
- `3_3_place_gp__globalplace__design__instance__area` ΔR²=0.0021
- `3_3_place_gp__globalplace__design__instance__area__stdcell` ΔR²=0.0021
- `3_3_place_gp__globalplace__gpl__area__original` ΔR²=0.0020
- `3_3_place_gp__globalplace__design__instance__count` ΔR²=0.0020
- `3_3_place_gp__globalplace__design__instance__count__stdcell` ΔR²=0.0020
- `3_3_place_gp__globalplace__design__core__area` ΔR²=0.0019
- `3_3_place_gp__globalplace__design__die__area` ΔR²=0.0019
- `3_3_place_gp__globalplace__design__instance__utilization` ΔR²=0.0019
- `3_3_place_gp__globalplace__design__instance__utilization__stdcell` ΔR²=0.0019

### Top 10 ablation → area

- `3_5_place_dp__detailedplace__design__instance__displacement__total` ΔR²=0.0004
- `3_3_place_gp__globalplace__gpl__convergence__iteration` ΔR²=0.0003
- `3_3_place_gp__globalplace__gpl__routability__iteration` ΔR²=0.0003
- `3_3_place_gp__globalplace__gpl__area__original` ΔR²=0.0002
- `3_5_place_dp__detailedplace__timing__fmax` ΔR²=0.0002
- `3_5_place_dp__detailedplace__timing__fmax__clock:core_clock` ΔR²=0.0002
- `3_5_place_dp__detailedplace__design__instance__displacement__mean` ΔR²=0.0002
- `3_3_place_gp__globalplace__gpl__area__timing_delta` ΔR²=0.0001
- `3_3_place_gp__globalplace__gpl__area__timing_delta__percent` ΔR²=0.0001
- `3_3_place_gp__globalplace__design__instance__area` ΔR²=0.0001

### Group ablations (mean ΔR²)

- `-detailedplace`: 0.0024
- `-configuration`: -0.0018
- `-globalplace`: -0.0021
- `-placeopt`: -0.0032


## CTS

### Top 15 SHAP → power

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
- `4_1_cts__cts__design__die__area` |SHAP|=0
- `4_1_cts__cts__design__instance__count__setup_buffer` |SHAP|=0
- `4_1_cts__cts__design__instance__count__stdcell` |SHAP|=0
- `4_1_cts__cts__design__instance__displacement__max` |SHAP|=0
- `4_1_cts__cts__design__instance__utilization` |SHAP|=0

### Top 15 SHAP → fmax

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
- `4_1_cts__cts__clock__skew__setup` |SHAP|=5.021e+05
- `4_1_cts__cts__timing__fmax__clock:core_clock` |SHAP|=4.412e+05
- `4_1_cts__cts__negotiation__converge__phase_1__iteration` |SHAP|=2.65e+05
- `param:CORE_UTILIZATION` |SHAP|=2.415e+05
- `4_1_cts__cts__design__instance__count` |SHAP|=2.108e+05

### Top 15 SHAP → area

- `4_1_cts__cts__design__instance__area` |SHAP|=96.72
- `4_1_cts__cts__design__instance__area__stdcell` |SHAP|=13.93
- `4_1_cts__cts__clock__skew__hold` |SHAP|=9.824
- `4_1_cts__cts__design__instance__displacement__mean` |SHAP|=2.948
- `4_1_cts__cts__clock__skew__setup` |SHAP|=1.054
- `4_1_cts__cts__timing__drv__max_cap_limit` |SHAP|=0.8087
- `4_1_cts__cts__timing__hold__ws` |SHAP|=0.375
- `4_1_cts__cts__timing__drv__max_slew_limit` |SHAP|=0.3721
- `4_1_cts__cts__design__instance__displacement__total` |SHAP|=0.2034
- `4_1_cts__cts__design__instance__count` |SHAP|=0.1223
- `4_1_cts__cts__design__instance__count__stdcell` |SHAP|=0.0308
- `4_1_cts__cts__design__instance__count__setup_buffer` |SHAP|=0.01917
- `4_1_cts__cts__dpl__hpwl__delta` |SHAP|=0.005953
- `4_1_cts__cts__timing__fmax` |SHAP|=0.002859
- `4_1_cts__cts__design__core__area` |SHAP|=0

### Top 10 ablation → power

- `4_1_cts__cts__design__instance__count` ΔR²=0.0015
- `4_1_cts__cts__design__instance__count__stdcell` ΔR²=0.0015
- `4_1_cts__cts__design__instance__displacement__max` ΔR²=0.0015
- `4_1_cts__cts__design__instance__displacement__mean` ΔR²=0.0015
- `4_1_cts__cts__design__instance__displacement__total` ΔR²=0.0015
- `4_1_cts__cts__design__instance__utilization` ΔR²=0.0015
- `4_1_cts__cts__design__instance__utilization__stdcell` ΔR²=0.0015
- `4_1_cts__cts__design__rows` ΔR²=0.0015
- `4_1_cts__cts__design__rows:FreePDK45_38x28_10R_NP_162NW_34O` ΔR²=0.0015
- `4_1_cts__cts__design__sites` ΔR²=0.0015

### Top 10 ablation → fmax

- `4_1_cts__cts__timing__hold__ws` ΔR²=0.0055
- `4_1_cts__cts__design__instance__count` ΔR²=-0.0001
- `4_1_cts__cts__design__core__area` ΔR²=-0.0001
- `4_1_cts__cts__design__die__area` ΔR²=-0.0001
- `4_1_cts__cts__timing__drv__max_slew_limit` ΔR²=-0.0001
- `4_1_cts__cts__clock__skew__hold` ΔR²=-0.0004
- `4_1_cts__cts__clock__skew__setup` ΔR²=-0.0004
- `4_1_cts__cts__design__instance__area` ΔR²=-0.0007
- `4_1_cts__cts__design__instance__area__stdcell` ΔR²=-0.0007
- `4_1_cts__cts__timing__drv__max_cap_limit` ΔR²=-0.0013

### Top 10 ablation → area

- `4_1_cts__cts__design__instance__area` ΔR²=-0.0035
- `4_1_cts__cts__design__instance__area__stdcell` ΔR²=-0.0035
- `4_1_cts__cts__design__instance__count__stdcell` ΔR²=-0.0039
- `4_1_cts__cts__design__instance__displacement__mean` ΔR²=-0.0039
- `4_1_cts__cts__design__instance__displacement__total` ΔR²=-0.0039
- `4_1_cts__cts__design__instance__count` ΔR²=-0.0039
- `4_1_cts__cts__design__core__area` ΔR²=-0.0039
- `4_1_cts__cts__design__die__area` ΔR²=-0.0039
- `4_1_cts__cts__design__instance__displacement__max` ΔR²=-0.0039
- `4_1_cts__cts__design__instance__utilization` ΔR²=-0.0039

### Group ablations (mean ΔR²)

- `-configuration`: -0.0006
- `-cts`: -0.0007


## ROUTING

### Top 15 SHAP → power

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
- `5_1_grt__globalroute__design__instance__count__setup_buffer` |SHAP|=0
- `5_1_grt__globalroute__design__instance__displacement__max` |SHAP|=0
- `5_1_grt__globalroute__design__instance__displacement__mean` |SHAP|=0
- `5_1_grt__globalroute__design__instance__displacement__total` |SHAP|=0
- `5_1_grt__globalroute__design__instance__utilization` |SHAP|=0

### Top 15 SHAP → fmax

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
- `5_1_grt__globalroute__design__instance__displacement__mean` |SHAP|=9.051e+05
- `5_1_grt__globalroute__design__instance__count__stdcell` |SHAP|=5.891e+05
- `5_1_grt__globalroute__timing__fmax__clock:core_clock` |SHAP|=4.937e+05
- `5_1_grt__globalroute__timing__drv__max_cap_limit` |SHAP|=2.889e+05
- `5_1_grt__globalroute__clock__skew__setup` |SHAP|=2.58e+05

### Top 15 SHAP → area

- `5_1_grt__globalroute__design__instance__area` |SHAP|=91.01
- `5_1_grt__globalroute__design__instance__area__stdcell` |SHAP|=20.1
- `5_1_grt__globalroute__clock__skew__hold` |SHAP|=1.655
- `5_2_route__detailedroute__route__vias` |SHAP|=0.8013
- `5_2_route__detailedroute__route__drc_errors__iter:1` |SHAP|=0.7104
- `5_1_grt__globalroute__design__instance__count` |SHAP|=0.4749
- `5_1_grt__globalroute__clock__skew__setup` |SHAP|=0.3304
- `5_1_grt__globalroute__design__instance__displacement__max` |SHAP|=0.2928
- `5_1_grt__globalroute__design__instance__displacement__mean` |SHAP|=0.2815
- `5_1_grt__globalroute__timing__drv__max_slew_limit` |SHAP|=0.1102
- `5_2_route__detailedroute__route__vias__singlecut` |SHAP|=0.08346
- `5_1_grt__globalroute__global_route__wirelength` |SHAP|=0.05557
- `5_1_grt__globalroute__design__instance__displacement__total` |SHAP|=0.02098
- `5_1_grt__globalroute__design__instance__count__setup_buffer` |SHAP|=0.01551
- `5_1_grt__globalroute__timing__drv__max_cap_limit` |SHAP|=0.01512

### Top 10 ablation → power

- `5_1_grt__globalroute__clock__skew__hold` ΔR²=0.0000
- `5_1_grt__globalroute__clock__skew__setup` ΔR²=0.0000
- `5_1_grt__globalroute__design__core__area` ΔR²=0.0000
- `5_1_grt__globalroute__design__die__area` ΔR²=0.0000
- `5_1_grt__globalroute__design__instance__count__setup_buffer` ΔR²=0.0000
- `5_1_grt__globalroute__design__instance__count__stdcell` ΔR²=0.0000
- `5_1_grt__globalroute__design__instance__displacement__max` ΔR²=0.0000
- `5_1_grt__globalroute__design__instance__displacement__mean` ΔR²=0.0000
- `5_1_grt__globalroute__design__instance__displacement__total` ΔR²=0.0000
- `5_1_grt__globalroute__design__instance__utilization` ΔR²=0.0000

### Top 10 ablation → fmax

- `5_1_grt__globalroute__timing__drv__max_slew_limit` ΔR²=0.0100
- `5_1_grt__globalroute__dpl__hpwl__delta` ΔR²=0.0089
- `5_1_grt__globalroute__global_route__fastroute__monotonic_s` ΔR²=0.0038
- `param:CORE_UTILIZATION` ΔR²=0.0025
- `5_1_grt__globalroute__global_route__vias` ΔR²=0.0021
- `5_1_grt__globalroute__global_route__fastroute__overflow_iterations_s` ΔR²=0.0017
- `5_1_grt__globalroute__timing__drv__setup_violation_count` ΔR²=0.0015
- `5_2_route__detailedroute__route__vias` ΔR²=0.0015
- `5_2_route__detailedroute__route__vias__singlecut` ΔR²=0.0015
- `5_1_grt__globalroute__global_route__fastroute__route_l_s` ΔR²=0.0012

### Top 10 ablation → area

- `5_1_grt__globalroute__design__instance__count__setup_buffer` ΔR²=0.0002
- `5_1_grt__globalroute__design__instance__count__stdcell` ΔR²=0.0002
- `5_1_grt__globalroute__design__instance__displacement__mean` ΔR²=0.0002
- `5_1_grt__globalroute__design__instance__displacement__total` ΔR²=0.0002
- `5_1_grt__globalroute__design__instance__utilization` ΔR²=0.0002
- `5_1_grt__globalroute__design__instance__utilization__stdcell` ΔR²=0.0002
- `5_1_grt__globalroute__design__nets` ΔR²=0.0002
- `5_1_grt__globalroute__design__rows` ΔR²=0.0002
- `5_1_grt__globalroute__design__rows:FreePDK45_38x28_10R_NP_162NW_34O` ΔR²=0.0002
- `5_1_grt__globalroute__design__sites` ΔR²=0.0002

### Group ablations (mean ΔR²)

- `-globalroute`: 0.0149
- `-detailedroute`: 0.0028
- `-configuration`: 0.0002
