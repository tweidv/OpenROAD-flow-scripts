# Stage transition prediction grid (LHS sweep)

**Completed trajectories:** 127
**Split:** 20 train / 107 test (seed 42, trajectory-level)

Each cell: test-set R² predicting **target** power/fmax/area at column stage from **source**
features at row stage. `params` = pre-floorplan ORFS knobs only (no OR metrics yet).

Feature sets:
- **compact+fmax** — checkpoint power, area, setup slack, fmax
- **handpicked** — curated stage features from `feature_analysis.py` (includes `inv_fmax` at placement+)

**Forward** = source earlier in flow than target. **Next step** = forward with distance 1.

## compact+fmax

### power

| source \\ target | floorplan | placement | cts | routing | final |
|---|---:|---:|---:|---:|---:|
| params | 0.093 | 0.150 | 0.153 | 0.169 | 0.257 |
| floorplan | 0.398 | 0.586 | 0.614 | 0.651 | 0.776 |
| placement | 0.348 | 0.541 | 0.571 | 0.612 | 0.729 |
| cts | 0.302 | 0.502 | 0.537 | 0.578 | 0.690 |
| routing | 0.349 | 0.543 | 0.575 | 0.614 | 0.729 |

### fmax

| source \\ target | floorplan | placement | cts | routing | final |
|---|---:|---:|---:|---:|---:|
| params | 0.212 | 0.178 | 0.267 | 0.271 | 0.273 |
| floorplan | 0.764 | 0.816 | 0.804 | 0.821 | 0.737 |
| placement | 0.602 | 0.828 | 0.898 | 0.896 | 0.892 |
| cts | 0.516 | 0.786 | 0.909 | 0.898 | 0.906 |
| routing | 0.591 | 0.792 | 0.901 | 0.920 | 0.906 |

### area

| source \\ target | floorplan | placement | cts | routing | final |
|---|---:|---:|---:|---:|---:|
| params | 0.169 | 0.088 | 0.167 | 0.232 | 0.232 |
| floorplan | 0.759 | 0.727 | 0.794 | 0.871 | 0.871 |
| placement | 0.618 | 0.655 | 0.700 | 0.834 | 0.834 |
| cts | 0.531 | 0.563 | 0.630 | 0.789 | 0.789 |
| routing | 0.614 | 0.630 | 0.688 | 0.825 | 0.825 |

### Next-step highlights

| Step | Power | Fmax | Area |
|------|------:|-----:|-----:|
| params → floorplan | 0.093 | 0.212 | 0.169 |
| floorplan → placement | 0.586 | 0.816 | 0.727 |
| placement → cts | 0.571 | 0.898 | 0.700 |
| cts → routing | 0.578 | 0.898 | 0.789 |
| routing → final | 0.729 | 0.906 | 0.825 |

### Predict final from each source

| Source | Power | Fmax | Area |
|--------|------:|-----:|-----:|
| params | 0.257 | 0.273 | 0.232 |
| floorplan | 0.776 | 0.737 | 0.871 |
| placement | 0.729 | 0.892 | 0.834 |
| cts | 0.690 | 0.906 | 0.789 |
| routing | 0.729 | 0.906 | 0.825 |

## handpicked

### power

| source \\ target | floorplan | placement | cts | routing | final |
|---|---:|---:|---:|---:|---:|
| params | 0.093 | 0.150 | 0.153 | 0.169 | 0.257 |
| floorplan | 0.283 | 0.371 | 0.384 | 0.402 | 0.476 |
| placement | 0.467 | 0.673 | 0.690 | 0.730 | 0.801 |
| cts | 0.470 | 0.669 | 0.702 | 0.713 | 0.752 |
| routing | 0.444 | 0.627 | 0.670 | 0.670 | 0.689 |

### fmax

| source \\ target | floorplan | placement | cts | routing | final |
|---|---:|---:|---:|---:|---:|
| params | 0.212 | 0.178 | 0.267 | 0.271 | 0.273 |
| floorplan | 0.644 | 0.338 | 0.177 | 0.134 | 0.110 |
| placement | 0.879 | 0.843 | 0.703 | 0.708 | 0.642 |
| cts | 0.665 | 0.893 | 0.862 | 0.872 | 0.812 |
| routing | 0.625 | 0.807 | 0.748 | 0.772 | 0.694 |

### area

| source \\ target | floorplan | placement | cts | routing | final |
|---|---:|---:|---:|---:|---:|
| params | 0.169 | 0.088 | 0.167 | 0.232 | 0.232 |
| floorplan | 0.656 | 0.579 | 0.557 | 0.523 | 0.523 |
| placement | 0.873 | 0.956 | 0.942 | 0.681 | 0.681 |
| cts | 0.615 | 0.754 | 0.809 | 0.798 | 0.798 |
| routing | 0.591 | 0.698 | 0.769 | 0.691 | 0.691 |

### Next-step highlights

| Step | Power | Fmax | Area |
|------|------:|-----:|-----:|
| params → floorplan | 0.093 | 0.212 | 0.169 |
| floorplan → placement | 0.371 | 0.338 | 0.579 |
| placement → cts | 0.690 | 0.703 | 0.942 |
| cts → routing | 0.713 | 0.872 | 0.798 |
| routing → final | 0.689 | 0.694 | 0.691 |

### Predict final from each source

| Source | Power | Fmax | Area |
|--------|------:|-----:|-----:|
| params | 0.257 | 0.273 | 0.232 |
| floorplan | 0.476 | 0.110 | 0.523 |
| placement | 0.801 | 0.642 | 0.681 |
| cts | 0.752 | 0.812 | 0.798 |
| routing | 0.689 | 0.694 | 0.691 |

## Plots

Heatmaps: `plots/transition_r2_compact_fmax_{power,fmax,area}.png` and `handpicked_*`.

Full table: `stage_transition_grid.csv`.
