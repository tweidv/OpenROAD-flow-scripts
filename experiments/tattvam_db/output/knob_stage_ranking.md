# Per-stage exclude counts & weak+ ranking (max |Pearson|)

Total knobs in DB: **37**

A knob is **kept** if it is weak/moderate/strong (|Spearman ρ| ≥ 0.08) on ≥1 design at that stage (best across metrics). Ranking uses **max |Pearson r|** across gcd/aes/jpeg at that stage.

## synth

- **Keep (weak+):** 0 knobs
- **Exclude:** 37 knobs (100% of 37)

_No weak+ knobs at this stage._

**Excluded @ synth** (37): `ABC_AREA`, `CELL_PAD_IN_SITES_DETAIL_PLACEMENT`, `CELL_PAD_IN_SITES_GLOBAL_PLACEMENT`, `CLUSTER_FLOPS`, `CORE_ASPECT_RATIO`, `CORE_MARGIN`, `CORE_UTILIZATION`, `CORNERS`, `CTS_CLUSTER_DIAMETER`, `CTS_CLUSTER_SIZE`, `DETAILED_ROUTE_END_ITERATION`, `DONT_BUFFER_PORTS`, `ENABLE_DPO`, `FASTROUTE_TCL`, `GLOBAL_ROUTE_ARGS`, `GPL_ROUTABILITY_DRIVEN`, `GPL_TIMING_DRIVEN`, `HOLD_SLACK_MARGIN`, `IO_PLACER_H`, `IO_PLACER_V`, `MATCH_CELL_FOOTPRINT`, `MAX_REPAIR_TIMING_ITER`, `MAX_ROUTING_LAYER`, `MIN_ROUTING_LAYER`, `OPENROAD_HIERARCHICAL`, `PLACE_DENSITY`, `PLACE_DENSITY_LB_ADDON`, `PLACE_PINS_ARGS`, `REMOVE_ABC_BUFFERS`, `ROUTING_LAYER_ADJUSTMENT`, `SETUP_SLACK_MARGIN`, `SKIP_GATE_CLONING`, `SKIP_PIN_SWAP`, `SKIP_VT_SWAP`, `SWAP_ARITH_OPERATORS`, `SYNTH_HIERARCHICAL`, `TNS_END_PERCENT`

## floorplan

- **Keep (weak+):** 11 knobs
- **Exclude:** 26 knobs (70% of 37)

| rank | knob | max Pearson r | design | metric | verdict |
|-----:|------|--------------:|--------|--------|---------|
| 1 | CORE_UTILIZATION | +0.999 | aes | utilization_pct | strong |
| 2 | PLACE_DENSITY_LB_ADDON | -0.414 | gcd | utilization_pct | strong |
| 3 | CORE_MARGIN | +0.338 | aes | fmax_mhz | strong |
| 4 | HOLD_SLACK_MARGIN | -0.328 | aes | utilization_pct | moderate |
| 5 | PLACE_DENSITY | +0.327 | aes | utilization_pct | strong |
| 6 | TNS_END_PERCENT | -0.316 | aes | fmax_mhz | strong |
| 7 | CORE_ASPECT_RATIO | -0.309 | jpeg | utilization_pct | moderate |
| 8 | SETUP_SLACK_MARGIN | -0.303 | aes | utilization_pct | moderate |
| 9 | CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.265 | aes | utilization_pct | moderate |
| 10 | CELL_PAD_IN_SITES_DETAIL_PLACEMENT | -0.242 | aes | utilization_pct | moderate |
| 11 | ROUTING_LAYER_ADJUSTMENT | -0.189 | jpeg | power_total_w | moderate |

**Excluded @ floorplan** (26): `ABC_AREA`, `CLUSTER_FLOPS`, `CORNERS`, `CTS_CLUSTER_DIAMETER`, `CTS_CLUSTER_SIZE`, `DETAILED_ROUTE_END_ITERATION`, `DONT_BUFFER_PORTS`, `ENABLE_DPO`, `FASTROUTE_TCL`, `GLOBAL_ROUTE_ARGS`, `GPL_ROUTABILITY_DRIVEN`, `GPL_TIMING_DRIVEN`, `IO_PLACER_H`, `IO_PLACER_V`, `MATCH_CELL_FOOTPRINT`, `MAX_REPAIR_TIMING_ITER`, `MAX_ROUTING_LAYER`, `MIN_ROUTING_LAYER`, `OPENROAD_HIERARCHICAL`, `PLACE_PINS_ARGS`, `REMOVE_ABC_BUFFERS`, `SKIP_GATE_CLONING`, `SKIP_PIN_SWAP`, `SKIP_VT_SWAP`, `SWAP_ARITH_OPERATORS`, `SYNTH_HIERARCHICAL`

## place

- **Keep (weak+):** 11 knobs
- **Exclude:** 26 knobs (70% of 37)

| rank | knob | max Pearson r | design | metric | verdict |
|-----:|------|--------------:|--------|--------|---------|
| 1 | CORE_UTILIZATION | -0.928 | aes | core_area_um2 | strong |
| 2 | CELL_PAD_IN_SITES_DETAIL_PLACEMENT | -0.397 | aes | fmax_mhz | strong |
| 3 | SETUP_SLACK_MARGIN | -0.365 | aes | tns_ns | strong |
| 4 | PLACE_DENSITY_LB_ADDON | +0.361 | gcd | core_area_um2 | strong |
| 5 | HOLD_SLACK_MARGIN | -0.350 | aes | tns_ns | strong |
| 6 | CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.304 | aes | fmax_mhz | moderate |
| 7 | CORE_ASPECT_RATIO | +0.299 | jpeg | core_area_um2 | moderate |
| 8 | PLACE_DENSITY | -0.273 | aes | core_area_um2 | strong |
| 9 | TNS_END_PERCENT | +0.269 | gcd | tns_ns | strong |
| 10 | CORE_MARGIN | +0.259 | jpeg | core_area_um2 | moderate |
| 11 | ROUTING_LAYER_ADJUSTMENT | +0.205 | jpeg | core_area_um2 | moderate |

**Excluded @ place** (26): `ABC_AREA`, `CLUSTER_FLOPS`, `CORNERS`, `CTS_CLUSTER_DIAMETER`, `CTS_CLUSTER_SIZE`, `DETAILED_ROUTE_END_ITERATION`, `DONT_BUFFER_PORTS`, `ENABLE_DPO`, `FASTROUTE_TCL`, `GLOBAL_ROUTE_ARGS`, `GPL_ROUTABILITY_DRIVEN`, `GPL_TIMING_DRIVEN`, `IO_PLACER_H`, `IO_PLACER_V`, `MATCH_CELL_FOOTPRINT`, `MAX_REPAIR_TIMING_ITER`, `MAX_ROUTING_LAYER`, `MIN_ROUTING_LAYER`, `OPENROAD_HIERARCHICAL`, `PLACE_PINS_ARGS`, `REMOVE_ABC_BUFFERS`, `SKIP_GATE_CLONING`, `SKIP_PIN_SWAP`, `SKIP_VT_SWAP`, `SWAP_ARITH_OPERATORS`, `SYNTH_HIERARCHICAL`

## cts

- **Keep (weak+):** 13 knobs
- **Exclude:** 24 knobs (65% of 37)

| rank | knob | max Pearson r | design | metric | verdict |
|-----:|------|--------------:|--------|--------|---------|
| 1 | CORE_UTILIZATION | -0.928 | aes | core_area_um2 | strong |
| 2 | CORE_MARGIN | +0.459 | aes | fmax_mhz | strong |
| 3 | PLACE_DENSITY_LB_ADDON | +0.402 | aes | fmax_mhz | strong |
| 4 | TNS_END_PERCENT | -0.401 | aes | fmax_mhz | strong |
| 5 | HOLD_SLACK_MARGIN | +0.336 | aes | core_area_um2 | moderate |
| 6 | SETUP_SLACK_MARGIN | +0.309 | aes | core_area_um2 | moderate |
| 7 | CORE_ASPECT_RATIO | +0.299 | jpeg | core_area_um2 | moderate |
| 8 | CTS_CLUSTER_DIAMETER | +0.293 | aes | fmax_mhz | moderate |
| 9 | CTS_CLUSTER_SIZE | +0.286 | aes | fmax_mhz | moderate |
| 10 | PLACE_DENSITY | -0.273 | aes | core_area_um2 | strong |
| 11 | CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | +0.266 | aes | core_area_um2 | moderate |
| 12 | CELL_PAD_IN_SITES_DETAIL_PLACEMENT | +0.249 | aes | core_area_um2 | moderate |
| 13 | ROUTING_LAYER_ADJUSTMENT | +0.205 | jpeg | core_area_um2 | moderate |

**Excluded @ cts** (24): `ABC_AREA`, `CLUSTER_FLOPS`, `CORNERS`, `DETAILED_ROUTE_END_ITERATION`, `DONT_BUFFER_PORTS`, `ENABLE_DPO`, `FASTROUTE_TCL`, `GLOBAL_ROUTE_ARGS`, `GPL_ROUTABILITY_DRIVEN`, `GPL_TIMING_DRIVEN`, `IO_PLACER_H`, `IO_PLACER_V`, `MATCH_CELL_FOOTPRINT`, `MAX_REPAIR_TIMING_ITER`, `MAX_ROUTING_LAYER`, `MIN_ROUTING_LAYER`, `OPENROAD_HIERARCHICAL`, `PLACE_PINS_ARGS`, `REMOVE_ABC_BUFFERS`, `SKIP_GATE_CLONING`, `SKIP_PIN_SWAP`, `SKIP_VT_SWAP`, `SWAP_ARITH_OPERATORS`, `SYNTH_HIERARCHICAL`

## route

- **Keep (weak+):** 15 knobs
- **Exclude:** 22 knobs (59% of 37)

| rank | knob | max Pearson r | design | metric | verdict |
|-----:|------|--------------:|--------|--------|---------|
| 1 | CORE_UTILIZATION | +0.993 | jpeg | utilization_pct | strong |
| 2 | CORE_ASPECT_RATIO | -0.675 | jpeg | utilization_pct | strong |
| 3 | CORE_MARGIN | +0.578 | aes | fmax_mhz | strong |
| 4 | CELL_PAD_IN_SITES_DETAIL_PLACEMENT | -0.534 | gcd | utilization_pct | strong |
| 5 | TNS_END_PERCENT | -0.523 | aes | fmax_mhz | strong |
| 6 | CTS_CLUSTER_SIZE | +0.518 | aes | utilization_pct | strong |
| 7 | CTS_CLUSTER_DIAMETER | +0.515 | aes | utilization_pct | strong |
| 8 | PLACE_DENSITY_LB_ADDON | -0.455 | aes | utilization_pct | strong |
| 9 | PLACE_DENSITY | +0.447 | jpeg | utilization_pct | strong |
| 10 | HOLD_SLACK_MARGIN | +0.336 | aes | core_area_um2 | moderate |
| 11 | ROUTING_LAYER_ADJUSTMENT | -0.330 | jpeg | utilization_pct | strong |
| 12 | CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.311 | gcd | utilization_pct | moderate |
| 13 | SETUP_SLACK_MARGIN | +0.309 | aes | core_area_um2 | moderate |
| 14 | DETAILED_ROUTE_END_ITERATION | +0.308 | aes | utilization_pct | strong |
| 15 | MAX_REPAIR_TIMING_ITER | -0.163 | gcd | utilization_pct | weak |

**Excluded @ route** (22): `ABC_AREA`, `CLUSTER_FLOPS`, `CORNERS`, `DONT_BUFFER_PORTS`, `ENABLE_DPO`, `FASTROUTE_TCL`, `GLOBAL_ROUTE_ARGS`, `GPL_ROUTABILITY_DRIVEN`, `GPL_TIMING_DRIVEN`, `IO_PLACER_H`, `IO_PLACER_V`, `MATCH_CELL_FOOTPRINT`, `MAX_ROUTING_LAYER`, `MIN_ROUTING_LAYER`, `OPENROAD_HIERARCHICAL`, `PLACE_PINS_ARGS`, `REMOVE_ABC_BUFFERS`, `SKIP_GATE_CLONING`, `SKIP_PIN_SWAP`, `SKIP_VT_SWAP`, `SWAP_ARITH_OPERATORS`, `SYNTH_HIERARCHICAL`

## finish

- **Keep (weak+):** 15 knobs
- **Exclude:** 22 knobs (59% of 37)

| rank | knob | max Pearson r | design | metric | verdict |
|-----:|------|--------------:|--------|--------|---------|
| 1 | CORE_UTILIZATION | +0.993 | jpeg | utilization_pct | strong |
| 2 | CORE_ASPECT_RATIO | -0.675 | jpeg | utilization_pct | strong |
| 3 | PLACE_DENSITY | +0.637 | aes | fmax_mhz | strong |
| 4 | CORE_MARGIN | +0.590 | aes | fmax_mhz | strong |
| 5 | CELL_PAD_IN_SITES_DETAIL_PLACEMENT | -0.525 | gcd | utilization_pct | strong |
| 6 | CTS_CLUSTER_SIZE | +0.518 | aes | utilization_pct | strong |
| 7 | CTS_CLUSTER_DIAMETER | +0.515 | aes | utilization_pct | strong |
| 8 | PLACE_DENSITY_LB_ADDON | -0.455 | aes | utilization_pct | strong |
| 9 | HOLD_SLACK_MARGIN | -0.417 | gcd | tns_ns | strong |
| 10 | SETUP_SLACK_MARGIN | -0.402 | aes | drc_violations | strong |
| 11 | TNS_END_PERCENT | +0.390 | gcd | utilization_pct | strong |
| 12 | DETAILED_ROUTE_END_ITERATION | -0.331 | aes | power_total_w | strong |
| 13 | ROUTING_LAYER_ADJUSTMENT | -0.330 | jpeg | utilization_pct | strong |
| 14 | CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.264 | jpeg | wns_ns | moderate |
| 15 | MAX_REPAIR_TIMING_ITER | -0.032 | gcd | drc_violations | moderate |

**Excluded @ finish** (22): `ABC_AREA`, `CLUSTER_FLOPS`, `CORNERS`, `DONT_BUFFER_PORTS`, `ENABLE_DPO`, `FASTROUTE_TCL`, `GLOBAL_ROUTE_ARGS`, `GPL_ROUTABILITY_DRIVEN`, `GPL_TIMING_DRIVEN`, `IO_PLACER_H`, `IO_PLACER_V`, `MATCH_CELL_FOOTPRINT`, `MAX_ROUTING_LAYER`, `MIN_ROUTING_LAYER`, `OPENROAD_HIERARCHICAL`, `PLACE_PINS_ARGS`, `REMOVE_ABC_BUFFERS`, `SKIP_GATE_CLONING`, `SKIP_PIN_SWAP`, `SKIP_VT_SWAP`, `SWAP_ARITH_OPERATORS`, `SYNTH_HIERARCHICAL`
