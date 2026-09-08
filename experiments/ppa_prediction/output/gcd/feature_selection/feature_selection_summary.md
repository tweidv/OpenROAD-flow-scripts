# GCD Forward Feature Selection — Summary

**Design:** gcd  |  **Trajectories:** 1000
**Split:** 20 train / 980 test
**Inner validation:** 15 / 5 from train pool, seeds [42, 43, 44]

## Method

- Greedy forward selection per stage × target on **validation R²** (mean ± std over inner seeds).
- Test set **never used** during selection.
- Final models retrained on all 20 train trajectories, evaluated once on 980 test.
- Feature pool: 233 wide ORFS metrics (train-constant features removed).

## Saturation: features required for 95% / 99% of achievable improvement

| Stage | Target | 95% imp (k) | 99% imp (k) | Max val R² | Baseline val R² |
|-------|--------|------------:|------------:|-----------:|----------------:|
| floorplan | power | 1 | 1 | 0.986 | -0.077 |
| floorplan | fmax | 1 | 2 | 0.975 | -0.168 |
| floorplan | area | 1 | 1 | 0.991 | -0.071 |
| placement | power | 1 | 1 | 0.986 | -0.077 |
| placement | fmax | 2 | 2 | 0.986 | -0.168 |
| placement | area | 1 | 1 | 0.998 | -0.071 |
| cts | power | 1 | 1 | 0.986 | -0.077 |
| cts | fmax | 2 | 2 | 0.988 | -0.168 |
| cts | area | 1 | 1 | 1.000 | -0.071 |
| routing | power | 1 | 1 | 0.986 | -0.077 |
| routing | fmax | 2 | 2 | 0.981 | -0.168 |
| routing | area | 1 | 1 | 1.000 | -0.071 |

## Final test R²: FFS vs full vs hand-picked

| Stage | Target | FFS 99% | FFS 95% | Full | Hand-picked |
|-------|--------|--------:|--------:|-----:|------------:|
| floorplan | power | 0.950 | 0.950 | 0.942 | 0.863 |
| floorplan | fmax | 0.923 | 0.886 | 0.868 | 0.589 |
| floorplan | area | 0.966 | 0.966 | 0.969 | 0.887 |
| placement | power | 0.950 | 0.950 | 0.932 | 0.902 |
| placement | fmax | 0.917 | 0.917 | 0.910 | 0.894 |
| placement | area | 0.959 | 0.959 | 0.964 | 0.977 |
| cts | power | 0.949 | 0.949 | 0.912 | 0.908 |
| cts | fmax | 0.800 | 0.800 | 0.893 | 0.933 |
| cts | area | 0.900 | 0.900 | 0.945 | 0.940 |
| routing | power | 0.950 | 0.950 | 0.916 | 0.942 |
| routing | fmax | 0.925 | 0.925 | 0.876 | 0.910 |
| routing | area | 0.950 | 0.950 | 0.970 | 0.983 |

## Shared feature sets (union of 99% FFS selections)

| Stage | Set | n | R² power | R² fmax | R² area | R² combined V |
|-------|-----|--:|---------:|--------:|--------:|--------------:|
| floorplan | union_99pct | 3 | 0.953 | 0.896 | 0.974 | 0.957 |
| floorplan | power_only_99pct | 1 | 0.950 | 0.886 | 0.968 | 0.955 |
| floorplan | fmax_only_99pct | 2 | 0.954 | 0.923 | 0.979 | 0.955 |
| floorplan | area_only_99pct | 1 | 0.946 | 0.741 | 0.966 | 0.949 |
| placement | union_99pct | 3 | 0.953 | 0.901 | 0.975 | 0.958 |
| placement | power_only_99pct | 1 | 0.950 | 0.886 | 0.968 | 0.955 |
| placement | fmax_only_99pct | 2 | 0.954 | 0.917 | 0.981 | 0.956 |
| placement | area_only_99pct | 1 | 0.943 | 0.812 | 0.959 | 0.945 |
| cts | union_99pct | 3 | 0.916 | 0.873 | 0.938 | 0.930 |
| cts | power_only_99pct | 1 | 0.949 | 0.886 | 0.969 | 0.955 |
| cts | fmax_only_99pct | 2 | 0.910 | 0.800 | 0.958 | 0.940 |
| cts | area_only_99pct | 1 | 0.831 | 0.657 | 0.900 | 0.888 |
| routing | union_99pct | 3 | 0.954 | 0.923 | 0.989 | 0.961 |
| routing | power_only_99pct | 1 | 0.950 | 0.889 | 0.977 | 0.957 |
| routing | fmax_only_99pct | 2 | 0.956 | 0.925 | 0.984 | 0.957 |
| routing | area_only_99pct | 1 | 0.824 | 0.747 | 0.950 | 0.908 |

## Interpretation checklist

- **Features needed:** see saturation table above.
- **Consistent selections:** compare `selected_features.csv` across targets.
- **Redundancy:** see `comparison_<stage>_<target>.csv` for SHAP high / FFS late cases.
- **Shared vs target-specific:** union row vs per-target rows in shared table.
- **Compact vs full loss:** FFS 99% column vs Full column in test table.

## Outputs

- `ffs_<stage>_<target>.csv` — every FFS iteration
- `selected_features.csv` — chosen sets by rule
- `final_test_results.csv` — held-out test metrics
- `shared_stage_features.csv` — cross-target union analysis
- `comparison_<stage>_<target>.csv` — FFS vs SHAP vs ablation
- `plots/ffs_curve_*.png` — validation R² vs # features