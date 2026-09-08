# Knob grid — all designs × all stages

Source: Tattvam SQLite. Cell = **best verdict** across all metrics at that design+stage (highest of wns/tns/power/util/fmax/area/…).

See also: `knob_stage_ranking.md` — exclude counts + weak+ knobs by max |Pearson|.

## Codes

| Code | Verdict |
|------|---------|
| S | strong (\|ρ\| ≥ 0.30) |
| M | moderate (0.15–0.30) |
| W | weak (0.08–0.15) |
| I | insensitive (\|ρ\| < 0.08) |
| WS | wrong_stage (Gate 1) |
| PF | param_flat (< 3 unique values) |
| LF | label_flat |
| NN | non_numeric |
| — | no data |

Full numeric detail: `knob_grid_agg.csv`, `knob_screen_all.csv`.

## synth

| knob | aes | gcd | jpeg | any weak+ |
|------|------|------|------|---------|
| ABC_AREA | PF | PF | PF |  |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | WS | WS | WS |  |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | WS | WS | WS |  |
| CLUSTER_FLOPS | WS | WS | WS |  |
| CORE_ASPECT_RATIO | WS | WS | WS |  |
| CORE_MARGIN | WS | WS | WS |  |
| CORE_UTILIZATION | WS | WS | WS |  |
| CORNERS | — | NN | — |  |
| CTS_CLUSTER_DIAMETER | WS | WS | WS |  |
| CTS_CLUSTER_SIZE | WS | WS | WS |  |
| DETAILED_ROUTE_END_ITERATION | WS | WS | WS |  |
| DONT_BUFFER_PORTS | WS | WS | WS |  |
| ENABLE_DPO | WS | WS | WS |  |
| FASTROUTE_TCL | WS | WS | WS |  |
| GLOBAL_ROUTE_ARGS | WS | WS | WS |  |
| GPL_ROUTABILITY_DRIVEN | WS | WS | WS |  |
| GPL_TIMING_DRIVEN | WS | WS | WS |  |
| HOLD_SLACK_MARGIN | WS | WS | WS |  |
| IO_PLACER_H | WS | WS | WS |  |
| IO_PLACER_V | WS | WS | WS |  |
| MATCH_CELL_FOOTPRINT | WS | WS | WS |  |
| MAX_REPAIR_TIMING_ITER | — | WS | — |  |
| MAX_ROUTING_LAYER | WS | WS | WS |  |
| MIN_ROUTING_LAYER | WS | WS | WS |  |
| OPENROAD_HIERARCHICAL | PF | PF | PF |  |
| PLACE_DENSITY | WS | WS | WS |  |
| PLACE_DENSITY_LB_ADDON | WS | WS | WS |  |
| PLACE_PINS_ARGS | WS | WS | WS |  |
| REMOVE_ABC_BUFFERS | WS | WS | WS |  |
| ROUTING_LAYER_ADJUSTMENT | WS | WS | WS |  |
| SETUP_SLACK_MARGIN | WS | WS | WS |  |
| SKIP_GATE_CLONING | — | WS | — |  |
| SKIP_PIN_SWAP | — | WS | — |  |
| SKIP_VT_SWAP | — | WS | — |  |
| SWAP_ARITH_OPERATORS | PF | PF | — |  |
| SYNTH_HIERARCHICAL | PF | PF | PF |  |
| TNS_END_PERCENT | WS | WS | WS |  |

_No knobs with weak+ signal @ synth_

## floorplan

| knob | aes | gcd | jpeg | any weak+ |
|------|------|------|------|---------|
| ABC_AREA | PF | PF | PF |  |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | M | W | I | yes |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | M | W | W | yes |
| CLUSTER_FLOPS | WS | WS | WS |  |
| CORE_ASPECT_RATIO | M | M | M | yes |
| CORE_MARGIN | S | M | M | yes |
| CORE_UTILIZATION | S | S | S | yes |
| CORNERS | — | NN | — |  |
| CTS_CLUSTER_DIAMETER | WS | WS | WS |  |
| CTS_CLUSTER_SIZE | WS | WS | WS |  |
| DETAILED_ROUTE_END_ITERATION | WS | WS | WS |  |
| DONT_BUFFER_PORTS | PF | PF | PF |  |
| ENABLE_DPO | WS | WS | WS |  |
| FASTROUTE_TCL | NN | NN | NN |  |
| GLOBAL_ROUTE_ARGS | WS | WS | WS |  |
| GPL_ROUTABILITY_DRIVEN | WS | WS | WS |  |
| GPL_TIMING_DRIVEN | WS | WS | WS |  |
| HOLD_SLACK_MARGIN | M | I | M | yes |
| IO_PLACER_H | PF | PF | PF |  |
| IO_PLACER_V | PF | PF | PF |  |
| MATCH_CELL_FOOTPRINT | WS | WS | WS |  |
| MAX_REPAIR_TIMING_ITER | — | WS | — |  |
| MAX_ROUTING_LAYER | WS | WS | WS |  |
| MIN_ROUTING_LAYER | WS | WS | WS |  |
| OPENROAD_HIERARCHICAL | PF | PF | PF |  |
| PLACE_DENSITY | S | I | M | yes |
| PLACE_DENSITY_LB_ADDON | M | S | I | yes |
| PLACE_PINS_ARGS | WS | WS | WS |  |
| REMOVE_ABC_BUFFERS | PF | PF | PF |  |
| ROUTING_LAYER_ADJUSTMENT | W | W | M | yes |
| SETUP_SLACK_MARGIN | M | W | M | yes |
| SKIP_GATE_CLONING | — | WS | — |  |
| SKIP_PIN_SWAP | — | WS | — |  |
| SKIP_VT_SWAP | — | WS | — |  |
| SWAP_ARITH_OPERATORS | PF | PF | — |  |
| SYNTH_HIERARCHICAL | PF | PF | PF |  |
| TNS_END_PERCENT | S | M | M | yes |

**Knobs with signal (weak+) on ≥1 design @ floorplan:** `CELL_PAD_IN_SITES_DETAIL_PLACEMENT`, `CELL_PAD_IN_SITES_GLOBAL_PLACEMENT`, `CORE_ASPECT_RATIO`, `CORE_MARGIN`, `CORE_UTILIZATION`, `HOLD_SLACK_MARGIN`, `PLACE_DENSITY`, `PLACE_DENSITY_LB_ADDON`, `ROUTING_LAYER_ADJUSTMENT`, `SETUP_SLACK_MARGIN`, `TNS_END_PERCENT`

## place

| knob | aes | gcd | jpeg | any weak+ |
|------|------|------|------|---------|
| ABC_AREA | PF | PF | PF |  |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | S | W | M | yes |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | M | I | M | yes |
| CLUSTER_FLOPS | WS | WS | WS |  |
| CORE_ASPECT_RATIO | W | I | M | yes |
| CORE_MARGIN | S | I | M | yes |
| CORE_UTILIZATION | S | S | S | yes |
| CORNERS | — | NN | — |  |
| CTS_CLUSTER_DIAMETER | WS | WS | WS |  |
| CTS_CLUSTER_SIZE | WS | WS | WS |  |
| DETAILED_ROUTE_END_ITERATION | WS | WS | WS |  |
| DONT_BUFFER_PORTS | PF | PF | PF |  |
| ENABLE_DPO | PF | PF | PF |  |
| FASTROUTE_TCL | NN | NN | NN |  |
| GLOBAL_ROUTE_ARGS | WS | WS | WS |  |
| GPL_ROUTABILITY_DRIVEN | PF | PF | PF |  |
| GPL_TIMING_DRIVEN | PF | PF | PF |  |
| HOLD_SLACK_MARGIN | S | M | W | yes |
| IO_PLACER_H | PF | PF | PF |  |
| IO_PLACER_V | PF | PF | PF |  |
| MATCH_CELL_FOOTPRINT | WS | WS | WS |  |
| MAX_REPAIR_TIMING_ITER | — | I | — |  |
| MAX_ROUTING_LAYER | WS | WS | WS |  |
| MIN_ROUTING_LAYER | WS | WS | WS |  |
| OPENROAD_HIERARCHICAL | PF | PF | PF |  |
| PLACE_DENSITY | S | W | M | yes |
| PLACE_DENSITY_LB_ADDON | S | S | I | yes |
| PLACE_PINS_ARGS | NN | NN | NN |  |
| REMOVE_ABC_BUFFERS | PF | PF | PF |  |
| ROUTING_LAYER_ADJUSTMENT | M | I | M | yes |
| SETUP_SLACK_MARGIN | S | I | W | yes |
| SKIP_GATE_CLONING | — | PF | — |  |
| SKIP_PIN_SWAP | — | PF | — |  |
| SKIP_VT_SWAP | — | PF | — |  |
| SWAP_ARITH_OPERATORS | PF | PF | — |  |
| SYNTH_HIERARCHICAL | PF | PF | PF |  |
| TNS_END_PERCENT | M | S | M | yes |

**Knobs with signal (weak+) on ≥1 design @ place:** `CELL_PAD_IN_SITES_DETAIL_PLACEMENT`, `CELL_PAD_IN_SITES_GLOBAL_PLACEMENT`, `CORE_ASPECT_RATIO`, `CORE_MARGIN`, `CORE_UTILIZATION`, `HOLD_SLACK_MARGIN`, `PLACE_DENSITY`, `PLACE_DENSITY_LB_ADDON`, `ROUTING_LAYER_ADJUSTMENT`, `SETUP_SLACK_MARGIN`, `TNS_END_PERCENT`

## cts

| knob | aes | gcd | jpeg | any weak+ |
|------|------|------|------|---------|
| ABC_AREA | PF | PF | PF |  |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | M | W | M | yes |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | M | M | M | yes |
| CLUSTER_FLOPS | WS | WS | WS |  |
| CORE_ASPECT_RATIO | M | M | M | yes |
| CORE_MARGIN | S | W | M | yes |
| CORE_UTILIZATION | S | S | S | yes |
| CORNERS | — | NN | — |  |
| CTS_CLUSTER_DIAMETER | M | I | M | yes |
| CTS_CLUSTER_SIZE | M | W | M | yes |
| DETAILED_ROUTE_END_ITERATION | WS | WS | WS |  |
| DONT_BUFFER_PORTS | PF | PF | PF |  |
| ENABLE_DPO | PF | PF | PF |  |
| FASTROUTE_TCL | NN | NN | NN |  |
| GLOBAL_ROUTE_ARGS | WS | WS | WS |  |
| GPL_ROUTABILITY_DRIVEN | PF | PF | PF |  |
| GPL_TIMING_DRIVEN | PF | PF | PF |  |
| HOLD_SLACK_MARGIN | M | M | W | yes |
| IO_PLACER_H | PF | PF | PF |  |
| IO_PLACER_V | PF | PF | PF |  |
| MATCH_CELL_FOOTPRINT | WS | WS | WS |  |
| MAX_REPAIR_TIMING_ITER | — | I | — |  |
| MAX_ROUTING_LAYER | WS | WS | WS |  |
| MIN_ROUTING_LAYER | WS | WS | WS |  |
| OPENROAD_HIERARCHICAL | PF | PF | PF |  |
| PLACE_DENSITY | S | W | M | yes |
| PLACE_DENSITY_LB_ADDON | S | S | W | yes |
| PLACE_PINS_ARGS | NN | NN | NN |  |
| REMOVE_ABC_BUFFERS | PF | PF | PF |  |
| ROUTING_LAYER_ADJUSTMENT | M | W | M | yes |
| SETUP_SLACK_MARGIN | M | W | M | yes |
| SKIP_GATE_CLONING | — | PF | — |  |
| SKIP_PIN_SWAP | — | PF | — |  |
| SKIP_VT_SWAP | — | PF | — |  |
| SWAP_ARITH_OPERATORS | PF | PF | — |  |
| SYNTH_HIERARCHICAL | PF | PF | PF |  |
| TNS_END_PERCENT | S | M | M | yes |

**Knobs with signal (weak+) on ≥1 design @ cts:** `CELL_PAD_IN_SITES_DETAIL_PLACEMENT`, `CELL_PAD_IN_SITES_GLOBAL_PLACEMENT`, `CORE_ASPECT_RATIO`, `CORE_MARGIN`, `CORE_UTILIZATION`, `CTS_CLUSTER_DIAMETER`, `CTS_CLUSTER_SIZE`, `HOLD_SLACK_MARGIN`, `PLACE_DENSITY`, `PLACE_DENSITY_LB_ADDON`, `ROUTING_LAYER_ADJUSTMENT`, `SETUP_SLACK_MARGIN`, `TNS_END_PERCENT`

## route

| knob | aes | gcd | jpeg | any weak+ |
|------|------|------|------|---------|
| ABC_AREA | PF | PF | PF |  |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | M | S | S | yes |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | M | M | M | yes |
| CLUSTER_FLOPS | PF | PF | PF |  |
| CORE_ASPECT_RATIO | S | M | S | yes |
| CORE_MARGIN | S | S | S | yes |
| CORE_UTILIZATION | S | S | S | yes |
| CORNERS | — | NN | — |  |
| CTS_CLUSTER_DIAMETER | S | W | M | yes |
| CTS_CLUSTER_SIZE | S | M | W | yes |
| DETAILED_ROUTE_END_ITERATION | S | W | S | yes |
| DONT_BUFFER_PORTS | PF | PF | PF |  |
| ENABLE_DPO | PF | PF | PF |  |
| FASTROUTE_TCL | NN | NN | NN |  |
| GLOBAL_ROUTE_ARGS | NN | NN | NN |  |
| GPL_ROUTABILITY_DRIVEN | PF | PF | PF |  |
| GPL_TIMING_DRIVEN | PF | PF | PF |  |
| HOLD_SLACK_MARGIN | M | S | S | yes |
| IO_PLACER_H | PF | PF | PF |  |
| IO_PLACER_V | PF | PF | PF |  |
| MATCH_CELL_FOOTPRINT | PF | PF | PF |  |
| MAX_REPAIR_TIMING_ITER | — | W | — | yes |
| MAX_ROUTING_LAYER | PF | PF | PF |  |
| MIN_ROUTING_LAYER | PF | PF | PF |  |
| OPENROAD_HIERARCHICAL | PF | PF | PF |  |
| PLACE_DENSITY | S | M | S | yes |
| PLACE_DENSITY_LB_ADDON | S | S | W | yes |
| PLACE_PINS_ARGS | NN | NN | NN |  |
| REMOVE_ABC_BUFFERS | PF | PF | PF |  |
| ROUTING_LAYER_ADJUSTMENT | W | W | S | yes |
| SETUP_SLACK_MARGIN | M | M | M | yes |
| SKIP_GATE_CLONING | — | PF | — |  |
| SKIP_PIN_SWAP | — | PF | — |  |
| SKIP_VT_SWAP | — | PF | — |  |
| SWAP_ARITH_OPERATORS | PF | PF | — |  |
| SYNTH_HIERARCHICAL | PF | PF | PF |  |
| TNS_END_PERCENT | S | S | S | yes |

**Knobs with signal (weak+) on ≥1 design @ route:** `CELL_PAD_IN_SITES_DETAIL_PLACEMENT`, `CELL_PAD_IN_SITES_GLOBAL_PLACEMENT`, `CORE_ASPECT_RATIO`, `CORE_MARGIN`, `CORE_UTILIZATION`, `CTS_CLUSTER_DIAMETER`, `CTS_CLUSTER_SIZE`, `DETAILED_ROUTE_END_ITERATION`, `HOLD_SLACK_MARGIN`, `MAX_REPAIR_TIMING_ITER`, `PLACE_DENSITY`, `PLACE_DENSITY_LB_ADDON`, `ROUTING_LAYER_ADJUSTMENT`, `SETUP_SLACK_MARGIN`, `TNS_END_PERCENT`

## finish

| knob | aes | gcd | jpeg | any weak+ |
|------|------|------|------|---------|
| ABC_AREA | PF | PF | PF |  |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | M | S | S | yes |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | M | S | M | yes |
| CLUSTER_FLOPS | PF | PF | PF |  |
| CORE_ASPECT_RATIO | S | S | S | yes |
| CORE_MARGIN | S | S | S | yes |
| CORE_UTILIZATION | S | S | S | yes |
| CORNERS | — | NN | — |  |
| CTS_CLUSTER_DIAMETER | S | M | S | yes |
| CTS_CLUSTER_SIZE | S | M | M | yes |
| DETAILED_ROUTE_END_ITERATION | S | W | S | yes |
| DONT_BUFFER_PORTS | PF | PF | PF |  |
| ENABLE_DPO | PF | PF | PF |  |
| FASTROUTE_TCL | NN | NN | NN |  |
| GLOBAL_ROUTE_ARGS | NN | NN | NN |  |
| GPL_ROUTABILITY_DRIVEN | PF | PF | PF |  |
| GPL_TIMING_DRIVEN | PF | PF | PF |  |
| HOLD_SLACK_MARGIN | S | S | M | yes |
| IO_PLACER_H | PF | PF | PF |  |
| IO_PLACER_V | PF | PF | PF |  |
| MATCH_CELL_FOOTPRINT | PF | PF | PF |  |
| MAX_REPAIR_TIMING_ITER | — | M | — | yes |
| MAX_ROUTING_LAYER | PF | PF | PF |  |
| MIN_ROUTING_LAYER | PF | PF | PF |  |
| OPENROAD_HIERARCHICAL | PF | PF | PF |  |
| PLACE_DENSITY | S | M | S | yes |
| PLACE_DENSITY_LB_ADDON | S | W | W | yes |
| PLACE_PINS_ARGS | NN | NN | NN |  |
| REMOVE_ABC_BUFFERS | PF | PF | PF |  |
| ROUTING_LAYER_ADJUSTMENT | S | S | S | yes |
| SETUP_SLACK_MARGIN | S | S | M | yes |
| SKIP_GATE_CLONING | — | PF | — |  |
| SKIP_PIN_SWAP | — | PF | — |  |
| SKIP_VT_SWAP | — | PF | — |  |
| SWAP_ARITH_OPERATORS | PF | PF | — |  |
| SYNTH_HIERARCHICAL | PF | PF | PF |  |
| TNS_END_PERCENT | S | S | M | yes |

**Knobs with signal (weak+) on ≥1 design @ finish:** `CELL_PAD_IN_SITES_DETAIL_PLACEMENT`, `CELL_PAD_IN_SITES_GLOBAL_PLACEMENT`, `CORE_ASPECT_RATIO`, `CORE_MARGIN`, `CORE_UTILIZATION`, `CTS_CLUSTER_DIAMETER`, `CTS_CLUSTER_SIZE`, `DETAILED_ROUTE_END_ITERATION`, `HOLD_SLACK_MARGIN`, `MAX_REPAIR_TIMING_ITER`, `PLACE_DENSITY`, `PLACE_DENSITY_LB_ADDON`, `ROUTING_LAYER_ADJUSTMENT`, `SETUP_SLACK_MARGIN`, `TNS_END_PERCENT`
