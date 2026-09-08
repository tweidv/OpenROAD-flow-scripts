# Prediction baseline grid — power, area, WNS, TNS

**All CLK (LHS sweep):** 132 completes, 20 train / 112 test
**Fixed CLK ≈ 0.25 ns (±5%):** 7 completes (same split pool)

**Targets:** power (`internal__total` checkpoint / `power__total` finish),
area (`instance__area`), WNS (`timing__setup__ws`), TNS (`timing__setup__tns`).

**Methods:**
- `read_forward` — linear fit using **same metric** at source only
- `linear_compact` — linear on source `[power, area, wns, tns]` (or params if pre-floorplan)
- `xgb_compact` — XGBoost on same features (often worse for read-forward metrics)

GCD baseline CLK in `designs.py`: **0.25 ns**. LHS sweep varies CLK intentionally;
dashboard/tapeout use fixed CLK — see fixed-CLK section below.

**Floorplan cost:** ~2/11 of relative full-flow cost in search models (cheap vs placement=4, routing=3).

## Full LHS sweep (CLK varies)

### Next step

#### read_forward

| source → target | power | area | wns | tns |
|-----------------|------:|-----:|----:|----:|
| params → floorplan | — | — | — | — |
| floorplan → placement | 0.993 | 0.896 | 0.993 | 0.999 |
| placement → cts | 0.998 | 0.987 | 0.997 | 0.999 |
| cts → routing | 0.998 | 0.970 | 0.996 | 0.998 |
| routing → final | 0.999 | 1.000 | 0.998 | 0.998 |

#### linear_compact

| source → target | power | area | wns | tns |
|-----------------|------:|-----:|----:|----:|
| params → floorplan | -2.804 | -1.701 | -1.111 | -3.361 |
| floorplan → placement | 0.958 | 0.708 | 0.991 | 0.999 |
| placement → cts | 0.996 | 0.973 | 0.996 | 0.999 |
| cts → routing | 0.997 | 0.969 | 0.996 | 0.999 |
| routing → final | 0.998 | 1.000 | 0.998 | 0.997 |

#### xgb_compact

| source → target | power | area | wns | tns |
|-----------------|------:|-----:|----:|----:|
| params → floorplan | 0.200 | 0.084 | 0.127 | 0.194 |
| floorplan → placement | 0.825 | 0.805 | 0.957 | 0.908 |
| placement → cts | 0.772 | 0.751 | 0.910 | 0.826 |
| cts → routing | 0.792 | 0.779 | 0.916 | 0.854 |
| routing → final | 0.823 | 0.800 | 0.908 | 0.832 |

### At finish

#### read_forward

| source → target | power | area | wns | tns |
|-----------------|------:|-----:|----:|----:|
| params → final | — | — | — | — |
| floorplan → final | 0.993 | 0.848 | 0.987 | 0.996 |
| placement → final | 0.993 | 0.940 | 0.995 | 0.999 |
| cts → final | 0.996 | 0.970 | 0.998 | 1.000 |
| routing → final | 0.999 | 1.000 | 0.998 | 0.998 |

#### linear_compact

| source → target | power | area | wns | tns |
|-----------------|------:|-----:|----:|----:|
| params → final | -2.978 | -1.124 | -1.429 | -3.275 |
| floorplan → final | 0.986 | 0.870 | 0.983 | 0.998 |
| placement → final | 0.993 | 0.940 | 0.994 | 0.999 |
| cts → final | 0.997 | 0.969 | 0.996 | 0.999 |
| routing → final | 0.998 | 1.000 | 0.998 | 0.997 |

#### xgb_compact

| source → target | power | area | wns | tns |
|-----------------|------:|-----:|----:|----:|
| params → final | 0.204 | 0.091 | 0.131 | 0.200 |
| floorplan → final | 0.876 | 0.801 | 0.941 | 0.903 |
| placement → final | 0.806 | 0.743 | 0.905 | 0.818 |
| cts → final | 0.820 | 0.779 | 0.911 | 0.839 |
| routing → final | 0.823 | 0.800 | 0.908 | 0.832 |

### Best method per cell

| source | horizon | metric | best | R² |
|--------|---------|--------|------|---:|
| cts → routing | next | area | **read_forward** | 0.970 |
| cts → routing | next | power | **read_forward** | 0.998 |
| cts → routing | next | tns | **linear_compact** | 0.999 |
| cts → routing | next | wns | **read_forward** | 0.996 |
| floorplan → placement | next | area | **read_forward** | 0.896 |
| floorplan → placement | next | power | **read_forward** | 0.993 |
| floorplan → placement | next | tns | **linear_compact** | 0.999 |
| floorplan → placement | next | wns | **read_forward** | 0.993 |
| params → floorplan | next | area | **xgb_compact** | 0.084 |
| params → floorplan | next | power | **xgb_compact** | 0.200 |
| params → floorplan | next | tns | **xgb_compact** | 0.194 |
| params → floorplan | next | wns | **xgb_compact** | 0.127 |
| placement → cts | next | area | **read_forward** | 0.987 |
| placement → cts | next | power | **read_forward** | 0.998 |
| placement → cts | next | tns | **linear_compact** | 0.999 |
| placement → cts | next | wns | **read_forward** | 0.997 |
| routing → final | next | area | **read_forward** | 1.000 |
| routing → final | next | power | **read_forward** | 0.999 |
| routing → final | next | tns | **read_forward** | 0.998 |
| routing → final | next | wns | **linear_compact** | 0.998 |
| cts → final | final | area | **read_forward** | 0.970 |
| cts → final | final | power | **linear_compact** | 0.997 |
| cts → final | final | tns | **read_forward** | 1.000 |
| cts → final | final | wns | **read_forward** | 0.998 |
| floorplan → final | final | area | **linear_compact** | 0.870 |
| floorplan → final | final | power | **read_forward** | 0.993 |
| floorplan → final | final | tns | **linear_compact** | 0.998 |
| floorplan → final | final | wns | **read_forward** | 0.987 |
| params → final | final | area | **xgb_compact** | 0.091 |
| params → final | final | power | **xgb_compact** | 0.204 |
| params → final | final | tns | **xgb_compact** | 0.200 |
| params → final | final | wns | **xgb_compact** | 0.131 |
| placement → final | final | area | **linear_compact** | 0.940 |
| placement → final | final | power | **read_forward** | 0.993 |
| placement → final | final | tns | **linear_compact** | 0.999 |
| placement → final | final | wns | **read_forward** | 0.995 |
| routing → final | final | area | **read_forward** | 1.000 |
| routing → final | final | power | **read_forward** | 0.999 |
| routing → final | final | tns | **read_forward** | 0.998 |
| routing → final | final | wns | **linear_compact** | 0.998 |

## How OpenROAD computes these (same call every stage)

ORFS `report_metrics` → OpenROAD STA/power/area hooks (`tools/OpenROAD/src/Metrics.tcl`):

| Metric | OR function | Meaning |
|--------|-------------|---------|
| **power** | `design_power` → `power__internal__total` | Switching + internal from current netlist/parasitics |
| **area** | `report_design_area_metrics` | Sum of instance areas |
| **WNS** | `worst_slack -max` → `timing__setup__ws` | Worst setup slack (negative = violated) |
| **TNS** | `total_negative_slack -max` → `timing__setup__tns` | Sum of negative slacks |

Each stage re-runs STA on the **current netlist** with the **same SDC clock period**.
Late-stage WNS/TNS ≈ finish because little changes after GRT.

CSV: `prediction_baseline_grid.csv` · plots: `plots/prediction_baseline_*.png`
