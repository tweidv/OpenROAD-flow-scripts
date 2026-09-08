# Knob screening (Tattvam DB)

Source: `experiments/tattvam_db/data/tattvam.sqlite`

Two gates only — **not** tied to surrogate / prediction models.

## Gate 1 — stage reach

Knob must first take effect at or before the metric stage (see `knob_stage_map.py`). Otherwise verdict = `wrong_stage`.

## Gate 2 — label sensitivity

Spearman ρ between numeric knob value and metric, per design × stage × metric.

| Verdict | Meaning |
|---------|---------|
| `wrong_stage` | Gate 1 fail — knob not applied yet at this stage |
| `non_numeric` | Path / Tcl / text knob — skipped |
| `param_flat` | Knob took < 3 distinct values in data |
| `label_flat` | Metric constant in joined rows |
| `insensitive` | \|ρ\| < 0.08 |
| `weak` | 0.08 ≤ \|ρ\| < 0.15 |
| `moderate` | 0.15 ≤ \|ρ\| < 0.30 |
| `strong` | \|ρ\| ≥ 0.30 |

## aes

### synth

**cell_count** — knobs passing Gate 1 with weak+ sensitivity:

_none_

**chip_area_um2** — knobs passing Gate 1 with weak+ sensitivity:

_none_

**comb_area_um2** — knobs passing Gate 1 with weak+ sensitivity:

_none_

**logic_depth** — knobs passing Gate 1 with weak+ sensitivity:

_none_

**seq_area_pct** — knobs passing Gate 1 with weak+ sensitivity:

_none_

**seq_area_um2** — knobs passing Gate 1 with weak+ sensitivity:

_none_

### floorplan

**core_area_um2** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_UTILIZATION | -0.996 | strong | 1540 | 61 | 33.2 |
| PLACE_DENSITY | -0.331 | strong | 1324 | 328 | 34.8 |
| HOLD_SLACK_MARGIN | +0.273 | moderate | 1169 | 267 | 35.5 |
| SETUP_SLACK_MARGIN | +0.260 | moderate | 1170 | 302 | 35.5 |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | +0.249 | moderate | 1411 | 5 | 34.0 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | +0.240 | moderate | 1490 | 5 | 33.5 |
| TNS_END_PERCENT | +0.136 | weak | 1540 | 101 | 33.2 |
| CORE_ASPECT_RATIO | +0.126 | weak | 1540 | 211 | 33.2 |
| PLACE_DENSITY_LB_ADDON | +0.114 | weak | 1540 | 181 | 33.2 |

**fmax_mhz** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| TNS_END_PERCENT | -0.407 | strong | 1540 | 101 | 21.6 |
| CORE_MARGIN | +0.392 | strong | 1540 | 21 | 21.6 |
| CORE_ASPECT_RATIO | -0.225 | moderate | 1540 | 211 | 21.6 |
| PLACE_DENSITY_LB_ADDON | +0.215 | moderate | 1540 | 181 | 21.6 |
| CORE_UTILIZATION | +0.186 | moderate | 1540 | 61 | 21.6 |
| PLACE_DENSITY | +0.143 | weak | 1324 | 328 | 16.9 |
| HOLD_SLACK_MARGIN | -0.114 | weak | 1169 | 267 | 16.9 |

**power_total_w** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| ROUTING_LAYER_ADJUSTMENT | +0.125 | weak | 1411 | 183 | 38.8 |
| PLACE_DENSITY | -0.123 | weak | 1324 | 328 | 39.2 |
| CORE_UTILIZATION | -0.110 | weak | 1540 | 61 | 38.3 |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | +0.103 | weak | 1411 | 5 | 38.8 |
| PLACE_DENSITY_LB_ADDON | +0.100 | weak | 1540 | 181 | 38.3 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | +0.091 | weak | 1490 | 5 | 38.5 |

**tns_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| PLACE_DENSITY_LB_ADDON | -0.168 | moderate | 1540 | 181 | 223.1 |
| HOLD_SLACK_MARGIN | -0.125 | weak | 1169 | 267 | 246.0 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.081 | weak | 1490 | 5 | 229.3 |

**utilization_pct** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_UTILIZATION | +0.998 | strong | 1540 | 61 | 21.8 |
| PLACE_DENSITY | +0.340 | strong | 1324 | 328 | 21.2 |
| HOLD_SLACK_MARGIN | -0.288 | moderate | 1169 | 267 | 21.3 |
| SETUP_SLACK_MARGIN | -0.273 | moderate | 1170 | 302 | 21.3 |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | -0.255 | moderate | 1411 | 5 | 21.9 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.246 | moderate | 1490 | 5 | 21.5 |
| TNS_END_PERCENT | -0.160 | moderate | 1540 | 101 | 21.8 |
| CORE_ASPECT_RATIO | -0.146 | weak | 1540 | 211 | 21.8 |
| PLACE_DENSITY_LB_ADDON | -0.099 | weak | 1540 | 181 | 21.8 |
| ROUTING_LAYER_ADJUSTMENT | -0.080 | weak | 1411 | 183 | 21.7 |

**wns_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| PLACE_DENSITY_LB_ADDON | -0.176 | moderate | 1540 | 181 | 188.1 |
| HOLD_SLACK_MARGIN | -0.129 | weak | 1169 | 267 | 197.7 |
| ROUTING_LAYER_ADJUSTMENT | -0.095 | weak | 1411 | 183 | 184.9 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.094 | weak | 1490 | 5 | 191.5 |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | -0.089 | weak | 1411 | 5 | 184.9 |
| CORE_UTILIZATION | +0.089 | weak | 1540 | 61 | 188.1 |

### place

**core_area_um2** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_UTILIZATION | -0.996 | strong | 1540 | 61 | 33.2 |
| PLACE_DENSITY | -0.331 | strong | 1324 | 328 | 34.8 |
| HOLD_SLACK_MARGIN | +0.273 | moderate | 1169 | 267 | 35.5 |
| SETUP_SLACK_MARGIN | +0.260 | moderate | 1170 | 302 | 35.5 |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | +0.249 | moderate | 1411 | 5 | 34.0 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | +0.240 | moderate | 1490 | 5 | 33.5 |
| TNS_END_PERCENT | +0.136 | weak | 1540 | 101 | 33.2 |
| CORE_ASPECT_RATIO | +0.126 | weak | 1540 | 211 | 33.2 |
| PLACE_DENSITY_LB_ADDON | +0.114 | weak | 1540 | 181 | 33.2 |

**fmax_mhz** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_UTILIZATION | +0.476 | strong | 1166 | 57 | 11.1 |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | -0.312 | strong | 1043 | 5 | 10.3 |
| SETUP_SLACK_MARGIN | -0.277 | moderate | 824 | 161 | 11.1 |
| HOLD_SLACK_MARGIN | -0.274 | moderate | 824 | 158 | 11.1 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.253 | moderate | 1121 | 5 | 11.1 |
| PLACE_DENSITY | +0.250 | moderate | 958 | 171 | 10.6 |
| CORE_ASPECT_RATIO | -0.145 | weak | 1166 | 143 | 11.1 |
| PLACE_DENSITY_LB_ADDON | +0.142 | weak | 1166 | 104 | 11.1 |
| CORE_MARGIN | +0.113 | weak | 1166 | 21 | 11.1 |
| TNS_END_PERCENT | -0.101 | weak | 1166 | 87 | 11.1 |

**tns_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_MARGIN | -0.357 | strong | 1166 | 21 | 344.2 |
| SETUP_SLACK_MARGIN | -0.311 | strong | 824 | 161 | 284.4 |
| HOLD_SLACK_MARGIN | -0.310 | strong | 824 | 158 | 284.4 |
| PLACE_DENSITY_LB_ADDON | -0.307 | strong | 1166 | 104 | 344.2 |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | -0.298 | moderate | 1043 | 5 | 324.0 |
| TNS_END_PERCENT | +0.283 | moderate | 1166 | 87 | 344.2 |
| CORE_UTILIZATION | +0.258 | moderate | 1166 | 57 | 344.2 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.248 | moderate | 1121 | 5 | 337.0 |
| ROUTING_LAYER_ADJUSTMENT | -0.155 | moderate | 1039 | 98 | 323.3 |
| PLACE_DENSITY | +0.151 | moderate | 958 | 171 | 309.2 |
| CORE_ASPECT_RATIO | +0.134 | weak | 1166 | 143 | 344.2 |

**wns_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_MARGIN | -0.357 | strong | 1166 | 21 | 244.6 |
| PLACE_DENSITY_LB_ADDON | -0.310 | strong | 1166 | 104 | 244.6 |
| SETUP_SLACK_MARGIN | -0.297 | moderate | 824 | 161 | 199.5 |
| HOLD_SLACK_MARGIN | -0.296 | moderate | 824 | 158 | 199.5 |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | -0.288 | moderate | 1043 | 5 | 229.1 |
| TNS_END_PERCENT | +0.287 | moderate | 1166 | 87 | 244.6 |
| CORE_UTILIZATION | +0.252 | moderate | 1166 | 57 | 244.6 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.237 | moderate | 1121 | 5 | 239.1 |
| ROUTING_LAYER_ADJUSTMENT | -0.153 | moderate | 1039 | 98 | 229.2 |
| PLACE_DENSITY | +0.150 | weak | 958 | 171 | 218.3 |
| CORE_ASPECT_RATIO | +0.142 | weak | 1166 | 143 | 244.6 |

### cts

**clock_insertion_delay_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_UTILIZATION | -0.224 | moderate | 1161 | 57 | 14.7 |
| CORE_MARGIN | -0.084 | weak | 1161 | 21 | 14.7 |

**clock_skew_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_MARGIN | -0.087 | weak | 1161 | 21 | 508.3 |

**core_area_um2** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_UTILIZATION | -0.996 | strong | 1540 | 61 | 33.2 |
| PLACE_DENSITY | -0.331 | strong | 1324 | 328 | 34.8 |
| HOLD_SLACK_MARGIN | +0.273 | moderate | 1169 | 267 | 35.5 |
| SETUP_SLACK_MARGIN | +0.260 | moderate | 1170 | 302 | 35.5 |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | +0.249 | moderate | 1411 | 5 | 34.0 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | +0.240 | moderate | 1490 | 5 | 33.5 |
| CTS_CLUSTER_DIAMETER | -0.140 | weak | 1540 | 423 | 33.2 |
| TNS_END_PERCENT | +0.136 | weak | 1540 | 101 | 33.2 |
| CORE_ASPECT_RATIO | +0.126 | weak | 1540 | 211 | 33.2 |
| PLACE_DENSITY_LB_ADDON | +0.114 | weak | 1540 | 181 | 33.2 |
| CTS_CLUSTER_SIZE | -0.090 | weak | 1540 | 41 | 33.2 |

**fmax_mhz** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_MARGIN | +0.394 | strong | 1161 | 21 | 5.3 |
| CORE_UTILIZATION | +0.336 | strong | 1161 | 57 | 5.3 |
| TNS_END_PERCENT | -0.323 | strong | 1161 | 87 | 5.3 |
| PLACE_DENSITY_LB_ADDON | +0.319 | strong | 1161 | 104 | 5.3 |
| CTS_CLUSTER_DIAMETER | +0.249 | moderate | 1161 | 210 | 5.3 |
| CTS_CLUSTER_SIZE | +0.218 | moderate | 1161 | 41 | 5.3 |
| PLACE_DENSITY | +0.209 | moderate | 953 | 170 | 3.6 |
| ROUTING_LAYER_ADJUSTMENT | +0.207 | moderate | 1034 | 98 | 4.1 |
| CORE_ASPECT_RATIO | -0.171 | moderate | 1161 | 143 | 5.3 |
| SETUP_SLACK_MARGIN | +0.158 | moderate | 822 | 159 | 3.0 |
| HOLD_SLACK_MARGIN | +0.120 | weak | 822 | 156 | 3.0 |

**hold_violation_count** — knobs passing Gate 1 with weak+ sensitivity:

_none_

**tns_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| PLACE_DENSITY | +0.176 | moderate | 953 | 170 | 918.8 |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | -0.160 | moderate | 1038 | 5 | 959.4 |
| CORE_UTILIZATION | +0.133 | weak | 1161 | 57 | 1015.2 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.128 | weak | 1116 | 5 | 995.1 |
| PLACE_DENSITY_LB_ADDON | -0.110 | weak | 1161 | 104 | 1015.2 |
| CTS_CLUSTER_DIAMETER | +0.095 | weak | 1161 | 210 | 1015.2 |

**wns_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| PLACE_DENSITY | +0.176 | moderate | 953 | 170 | 693.9 |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | -0.159 | moderate | 1038 | 5 | 724.8 |
| CORE_UTILIZATION | +0.133 | weak | 1161 | 57 | 767.2 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.128 | weak | 1116 | 5 | 752.0 |
| PLACE_DENSITY_LB_ADDON | -0.110 | weak | 1161 | 104 | 767.2 |
| CTS_CLUSTER_DIAMETER | +0.095 | weak | 1161 | 210 | 767.2 |

### route

**core_area_um2** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_UTILIZATION | -0.996 | strong | 1540 | 61 | 33.2 |
| PLACE_DENSITY | -0.331 | strong | 1324 | 328 | 34.8 |
| HOLD_SLACK_MARGIN | +0.273 | moderate | 1169 | 267 | 35.5 |
| SETUP_SLACK_MARGIN | +0.260 | moderate | 1170 | 302 | 35.5 |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | +0.249 | moderate | 1411 | 5 | 34.0 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | +0.240 | moderate | 1490 | 5 | 33.5 |
| DETAILED_ROUTE_END_ITERATION | -0.167 | moderate | 1414 | 176 | 33.8 |
| CTS_CLUSTER_DIAMETER | -0.140 | weak | 1540 | 423 | 33.2 |
| TNS_END_PERCENT | +0.136 | weak | 1540 | 101 | 33.2 |
| CORE_ASPECT_RATIO | +0.126 | weak | 1540 | 211 | 33.2 |
| PLACE_DENSITY_LB_ADDON | +0.114 | weak | 1540 | 181 | 33.2 |
| CTS_CLUSTER_SIZE | -0.090 | weak | 1540 | 41 | 33.2 |

**fmax_mhz** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_MARGIN | +0.541 | strong | 939 | 17 | 6.8 |
| TNS_END_PERCENT | -0.495 | strong | 939 | 72 | 6.8 |
| CTS_CLUSTER_DIAMETER | +0.473 | strong | 939 | 140 | 6.8 |
| CTS_CLUSTER_SIZE | +0.444 | strong | 939 | 40 | 6.8 |
| CORE_ASPECT_RATIO | -0.415 | strong | 939 | 62 | 6.8 |
| PLACE_DENSITY_LB_ADDON | +0.404 | strong | 939 | 68 | 6.8 |
| CORE_UTILIZATION | +0.219 | moderate | 939 | 52 | 6.8 |
| PLACE_DENSITY | +0.189 | moderate | 778 | 114 | 4.2 |
| SETUP_SLACK_MARGIN | +0.095 | weak | 662 | 47 | 3.6 |
| ROUTING_LAYER_ADJUSTMENT | +0.084 | weak | 822 | 35 | 4.7 |

**tns_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| PLACE_DENSITY_LB_ADDON | -0.236 | moderate | 939 | 68 | 1455.7 |
| CTS_CLUSTER_DIAMETER | +0.187 | moderate | 939 | 140 | 1455.7 |
| PLACE_DENSITY | +0.133 | weak | 778 | 114 | 1331.2 |
| CORE_MARGIN | -0.108 | weak | 939 | 17 | 1455.7 |
| CORE_UTILIZATION | +0.095 | weak | 939 | 52 | 1455.7 |
| CORE_ASPECT_RATIO | +0.082 | weak | 939 | 62 | 1455.7 |

**utilization_pct** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_UTILIZATION | +0.991 | strong | 31 | 9 | 18.3 |
| CTS_CLUSTER_DIAMETER | +0.478 | strong | 31 | 13 | 18.3 |
| PLACE_DENSITY_LB_ADDON | -0.464 | strong | 31 | 9 | 18.3 |
| CTS_CLUSTER_SIZE | +0.452 | strong | 31 | 9 | 18.3 |
| PLACE_DENSITY | -0.367 | strong | 10 | 6 | 22.8 |
| DETAILED_ROUTE_END_ITERATION | +0.315 | strong | 25 | 12 | 15.7 |
| CORE_ASPECT_RATIO | -0.312 | strong | 31 | 4 | 18.3 |
| CORE_MARGIN | -0.302 | strong | 31 | 4 | 18.3 |
| TNS_END_PERCENT | +0.084 | weak | 31 | 8 | 18.3 |

**wns_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| PLACE_DENSITY_LB_ADDON | -0.236 | moderate | 939 | 68 | 788.5 |
| CTS_CLUSTER_DIAMETER | +0.183 | moderate | 939 | 140 | 788.5 |
| PLACE_DENSITY | +0.132 | weak | 778 | 114 | 726.5 |
| CORE_MARGIN | -0.107 | weak | 939 | 17 | 788.5 |
| CORE_UTILIZATION | +0.091 | weak | 939 | 52 | 788.5 |
| HOLD_SLACK_MARGIN | -0.083 | weak | 662 | 46 | 681.1 |
| CORE_ASPECT_RATIO | +0.082 | weak | 939 | 62 | 788.5 |

### finish

**drc_violations** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_UTILIZATION | +0.796 | strong | 114 | 24 | 101.4 |
| CORE_MARGIN | +0.492 | strong | 114 | 6 | 101.4 |
| TNS_END_PERCENT | -0.423 | strong | 114 | 30 | 101.4 |
| CORE_ASPECT_RATIO | -0.404 | strong | 114 | 10 | 101.4 |
| HOLD_SLACK_MARGIN | -0.303 | strong | 48 | 4 | 52.4 |
| SETUP_SLACK_MARGIN | -0.303 | strong | 48 | 4 | 52.4 |
| PLACE_DENSITY_LB_ADDON | +0.295 | moderate | 114 | 19 | 101.4 |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | -0.247 | moderate | 83 | 3 | 83.9 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.227 | moderate | 99 | 4 | 92.0 |
| ROUTING_LAYER_ADJUSTMENT | +0.162 | moderate | 86 | 6 | 84.4 |

**fmax_mhz** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| PLACE_DENSITY | +0.693 | strong | 10 | 6 | 5.7 |
| CORE_MARGIN | +0.525 | strong | 31 | 4 | 9.7 |
| PLACE_DENSITY_LB_ADDON | +0.415 | strong | 31 | 9 | 9.7 |
| ROUTING_LAYER_ADJUSTMENT | +0.336 | strong | 20 | 4 | 8.4 |
| CTS_CLUSTER_DIAMETER | +0.316 | strong | 31 | 13 | 9.7 |
| CTS_CLUSTER_SIZE | +0.270 | moderate | 31 | 9 | 9.7 |
| CORE_ASPECT_RATIO | +0.103 | weak | 31 | 4 | 9.7 |

**power_total_w** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_UTILIZATION | -0.679 | strong | 31 | 9 | 49.1 |
| PLACE_DENSITY | +0.595 | strong | 10 | 6 | 32.8 |
| DETAILED_ROUTE_END_ITERATION | -0.345 | strong | 25 | 12 | 51.0 |
| CTS_CLUSTER_SIZE | -0.340 | strong | 31 | 9 | 49.1 |
| TNS_END_PERCENT | +0.331 | strong | 31 | 8 | 49.1 |
| CORE_MARGIN | -0.297 | moderate | 31 | 4 | 49.1 |
| PLACE_DENSITY_LB_ADDON | +0.238 | moderate | 31 | 9 | 49.1 |
| CTS_CLUSTER_DIAMETER | -0.209 | moderate | 31 | 13 | 49.1 |

**tns_ns** — knobs passing Gate 1 with weak+ sensitivity:

_none_

**utilization_pct** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_UTILIZATION | +0.991 | strong | 31 | 9 | 18.3 |
| CTS_CLUSTER_DIAMETER | +0.478 | strong | 31 | 13 | 18.3 |
| PLACE_DENSITY_LB_ADDON | -0.464 | strong | 31 | 9 | 18.3 |
| CTS_CLUSTER_SIZE | +0.452 | strong | 31 | 9 | 18.3 |
| PLACE_DENSITY | -0.367 | strong | 10 | 6 | 22.8 |
| DETAILED_ROUTE_END_ITERATION | +0.315 | strong | 25 | 12 | 15.7 |
| CORE_ASPECT_RATIO | -0.312 | strong | 31 | 4 | 18.3 |
| CORE_MARGIN | -0.302 | strong | 31 | 4 | 18.3 |
| TNS_END_PERCENT | +0.084 | weak | 31 | 8 | 18.3 |

**wns_ns** — knobs passing Gate 1 with weak+ sensitivity:

_none_

### Shortlist hints (floorplan)

- **wns_ns**: PLACE_DENSITY_LB_ADDON, HOLD_SLACK_MARGIN, ROUTING_LAYER_ADJUSTMENT, CELL_PAD_IN_SITES_GLOBAL_PLACEMENT, CELL_PAD_IN_SITES_DETAIL_PLACEMENT, CORE_UTILIZATION
- **power_total_w**: ROUTING_LAYER_ADJUSTMENT, PLACE_DENSITY, CORE_UTILIZATION, CELL_PAD_IN_SITES_DETAIL_PLACEMENT, PLACE_DENSITY_LB_ADDON, CELL_PAD_IN_SITES_GLOBAL_PLACEMENT
- **utilization_pct**: CORE_UTILIZATION, PLACE_DENSITY, HOLD_SLACK_MARGIN, SETUP_SLACK_MARGIN, CELL_PAD_IN_SITES_DETAIL_PLACEMENT, CELL_PAD_IN_SITES_GLOBAL_PLACEMENT

## gcd

### synth

**cell_count** — knobs passing Gate 1 with weak+ sensitivity:

_none_

**chip_area_um2** — knobs passing Gate 1 with weak+ sensitivity:

_none_

**comb_area_um2** — knobs passing Gate 1 with weak+ sensitivity:

_none_

**logic_depth** — knobs passing Gate 1 with weak+ sensitivity:

_none_

**seq_area_pct** — knobs passing Gate 1 with weak+ sensitivity:

_none_

**seq_area_um2** — knobs passing Gate 1 with weak+ sensitivity:

_none_

### floorplan

**core_area_um2** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_UTILIZATION | -0.961 | strong | 4935 | 63 | 40.8 |
| PLACE_DENSITY_LB_ADDON | +0.377 | strong | 4505 | 645 | 42.4 |

**fmax_mhz** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| TNS_END_PERCENT | +0.127 | weak | 4932 | 101 | 52.9 |
| CORE_ASPECT_RATIO | +0.097 | weak | 4574 | 763 | 54.9 |

**power_total_w** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_MARGIN | +0.187 | moderate | 4566 | 22 | 60.4 |
| CORE_ASPECT_RATIO | +0.159 | moderate | 4574 | 763 | 60.4 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.120 | weak | 4502 | 5 | 60.1 |
| SETUP_SLACK_MARGIN | +0.102 | weak | 4562 | 1896 | 60.4 |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | -0.092 | weak | 4502 | 5 | 60.1 |
| ROUTING_LAYER_ADJUSTMENT | +0.084 | weak | 4565 | 1052 | 60.4 |

**tns_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| TNS_END_PERCENT | +0.179 | moderate | 4932 | 101 | 124.7 |

**utilization_pct** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_UTILIZATION | +0.989 | strong | 4932 | 63 | 33.3 |
| PLACE_DENSITY_LB_ADDON | -0.395 | strong | 4502 | 645 | 33.9 |

**wns_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| TNS_END_PERCENT | +0.164 | moderate | 4932 | 101 | 119.5 |

### place

**core_area_um2** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_UTILIZATION | -0.961 | strong | 4932 | 63 | 40.8 |
| PLACE_DENSITY_LB_ADDON | +0.378 | strong | 4502 | 645 | 42.4 |

**fmax_mhz** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| TNS_END_PERCENT | +0.356 | strong | 1700 | 101 | 47.2 |
| CORE_UTILIZATION | +0.269 | moderate | 1700 | 58 | 47.2 |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | -0.150 | weak | 1284 | 5 | 55.1 |
| HOLD_SLACK_MARGIN | -0.110 | weak | 1342 | 624 | 53.8 |

**tns_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| TNS_END_PERCENT | +0.411 | strong | 1700 | 101 | 140.5 |
| CORE_UTILIZATION | +0.264 | moderate | 1700 | 58 | 140.5 |
| HOLD_SLACK_MARGIN | -0.157 | moderate | 1342 | 624 | 119.1 |
| PLACE_DENSITY | +0.090 | weak | 1345 | 556 | 119.3 |

**wns_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| TNS_END_PERCENT | +0.406 | strong | 1700 | 101 | 128.7 |
| CORE_UTILIZATION | +0.261 | moderate | 1700 | 58 | 128.7 |
| HOLD_SLACK_MARGIN | -0.147 | weak | 1342 | 624 | 110.5 |
| PLACE_DENSITY | +0.083 | weak | 1345 | 556 | 110.6 |

### cts

**clock_insertion_delay_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_ASPECT_RATIO | -0.166 | moderate | 987 | 389 | 57.1 |
| CTS_CLUSTER_SIZE | -0.145 | weak | 926 | 41 | 56.7 |
| PLACE_DENSITY_LB_ADDON | -0.142 | weak | 926 | 359 | 56.7 |
| TNS_END_PERCENT | -0.142 | weak | 1334 | 101 | 58.0 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | +0.137 | weak | 926 | 5 | 56.7 |
| CORE_UTILIZATION | -0.104 | weak | 1334 | 47 | 58.0 |
| HOLD_SLACK_MARGIN | +0.092 | weak | 976 | 478 | 57.1 |
| CORE_MARGIN | -0.085 | weak | 980 | 21 | 57.1 |

**clock_skew_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| TNS_END_PERCENT | -0.134 | weak | 1334 | 101 | 953.9 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | +0.118 | weak | 926 | 5 | 694.5 |
| HOLD_SLACK_MARGIN | +0.089 | weak | 976 | 478 | 726.0 |

**core_area_um2** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_UTILIZATION | -0.961 | strong | 4932 | 63 | 40.8 |
| PLACE_DENSITY_LB_ADDON | +0.378 | strong | 4502 | 645 | 42.4 |

**fmax_mhz** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_UTILIZATION | +0.195 | moderate | 1334 | 47 | 39.3 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.178 | moderate | 926 | 5 | 48.3 |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | -0.126 | weak | 926 | 5 | 48.3 |
| TNS_END_PERCENT | +0.117 | weak | 1334 | 101 | 39.3 |
| CORE_MARGIN | +0.098 | weak | 980 | 21 | 46.6 |
| CORE_ASPECT_RATIO | +0.094 | weak | 987 | 389 | 46.4 |

**hold_violation_count** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.099 | weak | 926 | 5 | 672.0 |
| SETUP_SLACK_MARGIN | +0.099 | weak | 976 | 512 | 690.3 |
| CORE_ASPECT_RATIO | +0.093 | weak | 987 | 389 | 694.2 |
| PLACE_DENSITY_LB_ADDON | -0.089 | weak | 926 | 359 | 672.0 |
| ROUTING_LAYER_ADJUSTMENT | +0.084 | weak | 979 | 280 | 691.4 |

**tns_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_UTILIZATION | +0.333 | strong | 1334 | 47 | 159.7 |
| TNS_END_PERCENT | +0.287 | moderate | 1334 | 101 | 159.7 |
| HOLD_SLACK_MARGIN | -0.195 | moderate | 976 | 478 | 130.5 |
| CTS_CLUSTER_SIZE | +0.138 | weak | 926 | 41 | 125.1 |
| PLACE_DENSITY | +0.127 | weak | 980 | 473 | 130.9 |
| SETUP_SLACK_MARGIN | -0.112 | weak | 976 | 512 | 130.5 |
| CORE_MARGIN | -0.107 | weak | 980 | 21 | 130.9 |

**wns_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_UTILIZATION | +0.316 | strong | 1334 | 47 | 143.6 |
| TNS_END_PERCENT | +0.227 | moderate | 1334 | 101 | 143.6 |
| HOLD_SLACK_MARGIN | -0.181 | moderate | 976 | 478 | 121.4 |
| CTS_CLUSTER_SIZE | +0.133 | weak | 926 | 41 | 116.3 |
| PLACE_DENSITY | +0.124 | weak | 980 | 473 | 121.7 |
| SETUP_SLACK_MARGIN | -0.121 | weak | 976 | 512 | 121.4 |
| CORE_MARGIN | -0.099 | weak | 980 | 21 | 121.8 |

### route

**core_area_um2** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_UTILIZATION | -0.961 | strong | 4932 | 63 | 40.8 |
| PLACE_DENSITY_LB_ADDON | +0.378 | strong | 4502 | 645 | 42.4 |

**fmax_mhz** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_UTILIZATION | +0.223 | moderate | 856 | 42 | 38.0 |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | -0.219 | moderate | 495 | 5 | 51.8 |
| TNS_END_PERCENT | +0.200 | moderate | 856 | 98 | 38.0 |
| HOLD_SLACK_MARGIN | -0.181 | moderate | 540 | 281 | 49.2 |
| CORE_ASPECT_RATIO | +0.157 | moderate | 550 | 228 | 48.6 |
| CTS_CLUSTER_SIZE | +0.135 | weak | 495 | 41 | 51.8 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.113 | weak | 495 | 5 | 51.8 |
| PLACE_DENSITY | +0.091 | weak | 543 | 310 | 49.0 |
| CTS_CLUSTER_DIAMETER | -0.090 | weak | 495 | 324 | 51.8 |

**tns_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_UTILIZATION | +0.351 | strong | 856 | 42 | 157.2 |
| HOLD_SLACK_MARGIN | -0.341 | strong | 540 | 281 | 120.7 |
| TNS_END_PERCENT | +0.303 | strong | 856 | 98 | 157.2 |
| PLACE_DENSITY | +0.200 | moderate | 543 | 310 | 121.1 |
| CTS_CLUSTER_SIZE | +0.200 | moderate | 495 | 41 | 111.9 |
| CORE_MARGIN | -0.192 | moderate | 542 | 21 | 121.1 |
| SETUP_SLACK_MARGIN | -0.189 | moderate | 540 | 286 | 120.7 |
| ROUTING_LAYER_ADJUSTMENT | -0.083 | weak | 542 | 167 | 121.1 |

**utilization_pct** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_UTILIZATION | +0.790 | strong | 267 | 34 | 25.0 |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | -0.533 | strong | 193 | 5 | 24.8 |
| TNS_END_PERCENT | +0.445 | strong | 267 | 80 | 25.0 |
| CORE_MARGIN | -0.304 | strong | 229 | 21 | 24.7 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.296 | moderate | 193 | 5 | 24.8 |
| CTS_CLUSTER_SIZE | -0.232 | moderate | 193 | 40 | 24.8 |
| CORE_ASPECT_RATIO | -0.215 | moderate | 230 | 92 | 24.8 |
| MAX_REPAIR_TIMING_ITER | -0.145 | weak | 28 | 24 | 28.2 |
| SETUP_SLACK_MARGIN | -0.142 | weak | 227 | 108 | 24.8 |
| PLACE_DENSITY_LB_ADDON | -0.127 | weak | 193 | 109 | 24.8 |
| DETAILED_ROUTE_END_ITERATION | +0.120 | weak | 193 | 91 | 24.8 |
| ROUTING_LAYER_ADJUSTMENT | -0.102 | weak | 229 | 68 | 24.8 |

**wns_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_UTILIZATION | +0.359 | strong | 856 | 42 | 139.9 |
| HOLD_SLACK_MARGIN | -0.318 | strong | 540 | 281 | 112.2 |
| TNS_END_PERCENT | +0.309 | strong | 856 | 98 | 139.9 |
| CORE_MARGIN | -0.208 | moderate | 542 | 21 | 112.6 |
| SETUP_SLACK_MARGIN | -0.194 | moderate | 540 | 286 | 112.2 |
| PLACE_DENSITY | +0.186 | moderate | 543 | 310 | 112.6 |
| CTS_CLUSTER_SIZE | +0.167 | moderate | 495 | 41 | 103.8 |
| ROUTING_LAYER_ADJUSTMENT | -0.086 | weak | 542 | 167 | 112.6 |

### finish

**drc_violations** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| MAX_REPAIR_TIMING_ITER | -0.191 | moderate | 39 | 26 | 246.2 |
| CTS_CLUSTER_SIZE | +0.128 | weak | 239 | 41 | 428.4 |
| SETUP_SLACK_MARGIN | -0.082 | weak | 284 | 134 | 468.5 |

**fmax_mhz** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.334 | strong | 196 | 5 | 54.2 |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | -0.314 | strong | 196 | 5 | 54.2 |
| HOLD_SLACK_MARGIN | -0.313 | strong | 230 | 110 | 49.2 |
| CTS_CLUSTER_SIZE | +0.252 | moderate | 196 | 40 | 54.2 |
| TNS_END_PERCENT | +0.238 | moderate | 270 | 81 | 46.0 |
| CORE_UTILIZATION | +0.202 | moderate | 270 | 34 | 46.0 |
| CTS_CLUSTER_DIAMETER | -0.183 | moderate | 196 | 128 | 54.2 |
| CORE_ASPECT_RATIO | +0.126 | weak | 233 | 95 | 48.8 |
| PLACE_DENSITY | +0.107 | weak | 231 | 123 | 49.1 |
| PLACE_DENSITY_LB_ADDON | -0.103 | weak | 196 | 112 | 54.2 |
| DETAILED_ROUTE_END_ITERATION | +0.101 | weak | 196 | 93 | 54.2 |
| ROUTING_LAYER_ADJUSTMENT | -0.087 | weak | 232 | 70 | 49.0 |

**power_total_w** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_MARGIN | +0.558 | strong | 232 | 21 | 81.1 |
| CORE_UTILIZATION | -0.531 | strong | 270 | 34 | 82.6 |
| SETUP_SLACK_MARGIN | +0.370 | strong | 230 | 111 | 80.6 |
| CORE_ASPECT_RATIO | +0.355 | strong | 233 | 95 | 81.2 |
| TNS_END_PERCENT | -0.327 | strong | 270 | 81 | 82.6 |
| ROUTING_LAYER_ADJUSTMENT | +0.314 | strong | 232 | 70 | 81.1 |
| HOLD_SLACK_MARGIN | +0.291 | moderate | 230 | 110 | 80.6 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.233 | moderate | 196 | 5 | 72.8 |
| CTS_CLUSTER_SIZE | +0.193 | moderate | 196 | 40 | 72.8 |
| PLACE_DENSITY | -0.122 | weak | 231 | 123 | 80.2 |
| CTS_CLUSTER_DIAMETER | -0.115 | weak | 196 | 128 | 72.8 |
| DETAILED_ROUTE_END_ITERATION | +0.097 | weak | 196 | 93 | 72.8 |

**tns_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| HOLD_SLACK_MARGIN | -0.557 | strong | 230 | 110 | 121.7 |
| CORE_UTILIZATION | +0.431 | strong | 270 | 34 | 132.3 |
| TNS_END_PERCENT | +0.415 | strong | 270 | 81 | 132.3 |
| SETUP_SLACK_MARGIN | -0.309 | strong | 230 | 111 | 121.7 |
| CTS_CLUSTER_SIZE | +0.274 | moderate | 196 | 40 | 105.5 |
| PLACE_DENSITY | +0.271 | moderate | 231 | 123 | 122.0 |
| CORE_MARGIN | -0.267 | moderate | 232 | 21 | 122.5 |
| ROUTING_LAYER_ADJUSTMENT | -0.237 | moderate | 232 | 70 | 122.5 |
| CTS_CLUSTER_DIAMETER | -0.115 | weak | 196 | 128 | 105.5 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.101 | weak | 196 | 5 | 105.5 |

**utilization_pct** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_UTILIZATION | +0.795 | strong | 270 | 34 | 25.1 |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | -0.521 | strong | 196 | 5 | 24.9 |
| TNS_END_PERCENT | +0.445 | strong | 270 | 81 | 25.1 |
| CORE_MARGIN | -0.314 | strong | 232 | 21 | 24.8 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.282 | moderate | 196 | 5 | 24.9 |
| CTS_CLUSTER_SIZE | -0.228 | moderate | 196 | 40 | 24.9 |
| CORE_ASPECT_RATIO | -0.221 | moderate | 233 | 95 | 24.8 |
| SETUP_SLACK_MARGIN | -0.151 | moderate | 230 | 111 | 24.9 |
| DETAILED_ROUTE_END_ITERATION | +0.134 | weak | 196 | 93 | 24.9 |
| PLACE_DENSITY_LB_ADDON | -0.129 | weak | 196 | 112 | 24.9 |
| ROUTING_LAYER_ADJUSTMENT | -0.092 | weak | 232 | 70 | 24.8 |
| MAX_REPAIR_TIMING_ITER | -0.084 | weak | 31 | 25 | 27.7 |

**wns_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| HOLD_SLACK_MARGIN | -0.537 | strong | 230 | 110 | 113.8 |
| CORE_UTILIZATION | +0.451 | strong | 270 | 34 | 122.7 |
| TNS_END_PERCENT | +0.418 | strong | 270 | 81 | 122.7 |
| SETUP_SLACK_MARGIN | -0.314 | strong | 230 | 111 | 113.8 |
| CORE_MARGIN | -0.286 | moderate | 232 | 21 | 114.7 |
| ROUTING_LAYER_ADJUSTMENT | -0.254 | moderate | 232 | 70 | 114.7 |
| CTS_CLUSTER_SIZE | +0.248 | moderate | 196 | 40 | 97.9 |
| PLACE_DENSITY | +0.244 | moderate | 231 | 123 | 114.0 |
| CTS_CLUSTER_DIAMETER | -0.112 | weak | 196 | 128 | 97.9 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.094 | weak | 196 | 5 | 97.9 |

### Shortlist hints (floorplan)

- **wns_ns**: TNS_END_PERCENT
- **power_total_w**: CORE_MARGIN, CORE_ASPECT_RATIO, CELL_PAD_IN_SITES_GLOBAL_PLACEMENT, SETUP_SLACK_MARGIN, CELL_PAD_IN_SITES_DETAIL_PLACEMENT, ROUTING_LAYER_ADJUSTMENT
- **utilization_pct**: CORE_UTILIZATION, PLACE_DENSITY_LB_ADDON

## jpeg

### synth

**cell_count** — knobs passing Gate 1 with weak+ sensitivity:

_none_

**chip_area_um2** — knobs passing Gate 1 with weak+ sensitivity:

_none_

**comb_area_um2** — knobs passing Gate 1 with weak+ sensitivity:

_none_

**seq_area_pct** — knobs passing Gate 1 with weak+ sensitivity:

_none_

**seq_area_um2** — knobs passing Gate 1 with weak+ sensitivity:

_none_

### floorplan

**core_area_um2** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_UTILIZATION | -0.892 | strong | 377 | 50 | 37.2 |
| ROUTING_LAYER_ADJUSTMENT | +0.213 | moderate | 375 | 70 | 37.4 |
| CORE_ASPECT_RATIO | +0.206 | moderate | 377 | 73 | 37.2 |
| CORE_MARGIN | +0.199 | moderate | 377 | 20 | 37.2 |
| PLACE_DENSITY | -0.166 | moderate | 375 | 106 | 37.4 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | +0.098 | weak | 375 | 5 | 37.4 |
| HOLD_SLACK_MARGIN | +0.093 | weak | 375 | 103 | 37.4 |
| SETUP_SLACK_MARGIN | +0.088 | weak | 375 | 102 | 37.4 |

**fmax_mhz** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| TNS_END_PERCENT | +0.250 | moderate | 377 | 88 | 87.3 |
| HOLD_SLACK_MARGIN | +0.224 | moderate | 375 | 103 | 86.9 |
| SETUP_SLACK_MARGIN | +0.222 | moderate | 375 | 102 | 86.9 |
| PLACE_DENSITY | -0.199 | moderate | 375 | 106 | 86.9 |
| CORE_MARGIN | +0.188 | moderate | 377 | 20 | 87.3 |
| ROUTING_LAYER_ADJUSTMENT | +0.165 | moderate | 375 | 70 | 86.9 |
| CORE_ASPECT_RATIO | +0.100 | weak | 377 | 73 | 87.3 |

**power_total_w** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| ROUTING_LAYER_ADJUSTMENT | -0.271 | moderate | 375 | 70 | 11.2 |
| CORE_MARGIN | -0.173 | moderate | 377 | 20 | 11.2 |
| PLACE_DENSITY | +0.158 | moderate | 375 | 106 | 11.2 |
| SETUP_SLACK_MARGIN | -0.091 | weak | 375 | 102 | 11.2 |

**tns_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| TNS_END_PERCENT | +0.195 | moderate | 377 | 88 | 99.7 |
| HOLD_SLACK_MARGIN | +0.181 | moderate | 375 | 103 | 100.1 |
| SETUP_SLACK_MARGIN | +0.170 | moderate | 375 | 102 | 100.1 |
| CORE_MARGIN | +0.157 | moderate | 377 | 20 | 99.7 |
| PLACE_DENSITY | -0.149 | weak | 375 | 106 | 100.1 |
| ROUTING_LAYER_ADJUSTMENT | +0.103 | weak | 375 | 70 | 100.1 |

**utilization_pct** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_UTILIZATION | +0.985 | strong | 377 | 50 | 20.7 |
| CORE_ASPECT_RATIO | -0.218 | moderate | 377 | 73 | 20.7 |
| CORE_MARGIN | -0.216 | moderate | 377 | 20 | 20.7 |
| ROUTING_LAYER_ADJUSTMENT | -0.191 | moderate | 375 | 70 | 20.6 |
| PLACE_DENSITY | +0.189 | moderate | 375 | 106 | 20.6 |
| SETUP_SLACK_MARGIN | -0.115 | weak | 375 | 102 | 20.6 |
| HOLD_SLACK_MARGIN | -0.101 | weak | 375 | 103 | 20.6 |

**wns_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| TNS_END_PERCENT | +0.251 | moderate | 377 | 88 | 101.6 |
| HOLD_SLACK_MARGIN | +0.226 | moderate | 375 | 103 | 102.2 |
| SETUP_SLACK_MARGIN | +0.224 | moderate | 375 | 102 | 102.2 |
| PLACE_DENSITY | -0.196 | moderate | 375 | 106 | 102.2 |
| CORE_MARGIN | +0.190 | moderate | 377 | 20 | 101.6 |
| ROUTING_LAYER_ADJUSTMENT | +0.165 | moderate | 375 | 70 | 102.2 |
| CORE_ASPECT_RATIO | +0.104 | weak | 377 | 73 | 101.6 |

### place

**core_area_um2** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_UTILIZATION | -0.892 | strong | 377 | 50 | 37.2 |
| ROUTING_LAYER_ADJUSTMENT | +0.213 | moderate | 375 | 70 | 37.4 |
| CORE_ASPECT_RATIO | +0.206 | moderate | 377 | 73 | 37.2 |
| CORE_MARGIN | +0.199 | moderate | 377 | 20 | 37.2 |
| PLACE_DENSITY | -0.166 | moderate | 375 | 106 | 37.4 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | +0.098 | weak | 375 | 5 | 37.4 |
| HOLD_SLACK_MARGIN | +0.093 | weak | 375 | 103 | 37.4 |
| SETUP_SLACK_MARGIN | +0.088 | weak | 375 | 102 | 37.4 |

**fmax_mhz** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| TNS_END_PERCENT | +0.241 | moderate | 269 | 65 | 20.1 |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | -0.228 | moderate | 267 | 5 | 20.2 |
| PLACE_DENSITY | -0.210 | moderate | 267 | 59 | 20.2 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.148 | weak | 267 | 5 | 20.2 |
| SETUP_SLACK_MARGIN | +0.139 | weak | 267 | 88 | 20.2 |
| CORE_UTILIZATION | +0.105 | weak | 269 | 46 | 20.1 |

**tns_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | -0.203 | moderate | 267 | 5 | 130.2 |
| TNS_END_PERCENT | +0.198 | moderate | 269 | 65 | 130.8 |
| PLACE_DENSITY | -0.176 | moderate | 267 | 59 | 130.2 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.174 | moderate | 267 | 5 | 130.2 |
| CORE_UTILIZATION | +0.160 | moderate | 269 | 46 | 130.8 |
| SETUP_SLACK_MARGIN | +0.144 | weak | 267 | 88 | 130.2 |
| CORE_ASPECT_RATIO | -0.102 | weak | 269 | 58 | 130.8 |

**wns_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| TNS_END_PERCENT | +0.241 | moderate | 269 | 65 | 91.7 |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | -0.228 | moderate | 267 | 5 | 91.7 |
| PLACE_DENSITY | -0.210 | moderate | 267 | 59 | 91.7 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.147 | weak | 267 | 5 | 91.7 |
| SETUP_SLACK_MARGIN | +0.140 | weak | 267 | 88 | 91.7 |
| CORE_UTILIZATION | +0.104 | weak | 269 | 46 | 91.7 |

### cts

**clock_insertion_delay_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_UTILIZATION | -0.340 | strong | 247 | 45 | 13.8 |
| CORE_MARGIN | +0.161 | moderate | 247 | 19 | 13.8 |
| ROUTING_LAYER_ADJUSTMENT | +0.117 | weak | 245 | 52 | 13.8 |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | +0.115 | weak | 245 | 4 | 13.8 |
| HOLD_SLACK_MARGIN | +0.102 | weak | 245 | 85 | 13.8 |
| CTS_CLUSTER_SIZE | -0.086 | weak | 245 | 36 | 13.8 |

**clock_skew_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CTS_CLUSTER_DIAMETER | +0.116 | weak | 245 | 83 | 3157.0 |
| CORE_ASPECT_RATIO | -0.100 | weak | 247 | 55 | 2849.9 |

**core_area_um2** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_UTILIZATION | -0.892 | strong | 377 | 50 | 37.2 |
| ROUTING_LAYER_ADJUSTMENT | +0.213 | moderate | 375 | 70 | 37.4 |
| CORE_ASPECT_RATIO | +0.206 | moderate | 377 | 73 | 37.2 |
| CORE_MARGIN | +0.199 | moderate | 377 | 20 | 37.2 |
| PLACE_DENSITY | -0.166 | moderate | 375 | 106 | 37.4 |
| CTS_CLUSTER_DIAMETER | -0.123 | weak | 375 | 128 | 37.4 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | +0.098 | weak | 375 | 5 | 37.4 |
| HOLD_SLACK_MARGIN | +0.093 | weak | 375 | 103 | 37.4 |
| SETUP_SLACK_MARGIN | +0.088 | weak | 375 | 102 | 37.4 |

**fmax_mhz** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| TNS_END_PERCENT | +0.287 | moderate | 247 | 59 | 6.0 |
| CTS_CLUSTER_DIAMETER | +0.243 | moderate | 245 | 83 | 6.0 |
| SETUP_SLACK_MARGIN | +0.229 | moderate | 245 | 88 | 6.0 |
| ROUTING_LAYER_ADJUSTMENT | +0.187 | moderate | 245 | 52 | 6.0 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.184 | moderate | 245 | 5 | 6.0 |
| PLACE_DENSITY | -0.178 | moderate | 245 | 55 | 6.0 |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | -0.156 | moderate | 245 | 4 | 6.0 |
| CTS_CLUSTER_SIZE | +0.152 | moderate | 245 | 36 | 6.0 |
| HOLD_SLACK_MARGIN | +0.147 | weak | 245 | 85 | 6.0 |
| CORE_UTILIZATION | +0.139 | weak | 247 | 45 | 6.0 |
| PLACE_DENSITY_LB_ADDON | -0.114 | weak | 247 | 47 | 6.0 |

**hold_violation_count** — knobs passing Gate 1 with weak+ sensitivity:

_none_

**tns_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| TNS_END_PERCENT | +0.265 | moderate | 247 | 59 | 169.2 |
| CTS_CLUSTER_DIAMETER | +0.213 | moderate | 245 | 83 | 169.6 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.185 | moderate | 245 | 5 | 169.6 |
| SETUP_SLACK_MARGIN | +0.178 | moderate | 245 | 88 | 169.6 |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | -0.164 | moderate | 245 | 4 | 169.6 |
| CTS_CLUSTER_SIZE | +0.154 | moderate | 245 | 36 | 169.6 |
| PLACE_DENSITY | -0.150 | moderate | 245 | 55 | 169.6 |
| CORE_UTILIZATION | +0.145 | weak | 247 | 45 | 169.2 |
| ROUTING_LAYER_ADJUSTMENT | +0.138 | weak | 245 | 52 | 169.6 |
| PLACE_DENSITY_LB_ADDON | -0.097 | weak | 247 | 47 | 169.2 |
| HOLD_SLACK_MARGIN | +0.094 | weak | 245 | 85 | 169.6 |

**wns_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| TNS_END_PERCENT | +0.274 | moderate | 247 | 59 | 99.6 |
| CTS_CLUSTER_DIAMETER | +0.230 | moderate | 245 | 83 | 100.3 |
| SETUP_SLACK_MARGIN | +0.212 | moderate | 245 | 88 | 100.3 |
| ROUTING_LAYER_ADJUSTMENT | +0.184 | moderate | 245 | 52 | 100.3 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.181 | moderate | 245 | 5 | 100.3 |
| PLACE_DENSITY | -0.160 | moderate | 245 | 55 | 100.3 |
| CTS_CLUSTER_SIZE | +0.151 | moderate | 245 | 36 | 100.3 |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | -0.151 | moderate | 245 | 4 | 100.3 |
| CORE_UTILIZATION | +0.135 | weak | 247 | 45 | 99.6 |
| HOLD_SLACK_MARGIN | +0.129 | weak | 245 | 85 | 100.3 |
| PLACE_DENSITY_LB_ADDON | -0.106 | weak | 247 | 47 | 99.6 |

### route

**core_area_um2** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_UTILIZATION | -0.892 | strong | 377 | 50 | 37.2 |
| ROUTING_LAYER_ADJUSTMENT | +0.213 | moderate | 375 | 70 | 37.4 |
| CORE_ASPECT_RATIO | +0.206 | moderate | 377 | 73 | 37.2 |
| CORE_MARGIN | +0.199 | moderate | 377 | 20 | 37.2 |
| PLACE_DENSITY | -0.166 | moderate | 375 | 106 | 37.4 |
| CTS_CLUSTER_DIAMETER | -0.123 | weak | 375 | 128 | 37.4 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | +0.098 | weak | 375 | 5 | 37.4 |
| HOLD_SLACK_MARGIN | +0.093 | weak | 375 | 103 | 37.4 |
| SETUP_SLACK_MARGIN | +0.088 | weak | 375 | 102 | 37.4 |
| DETAILED_ROUTE_END_ITERATION | +0.086 | weak | 375 | 106 | 37.4 |

**fmax_mhz** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| PLACE_DENSITY | -0.333 | strong | 141 | 39 | 6.6 |
| TNS_END_PERCENT | +0.328 | strong | 143 | 48 | 6.5 |
| HOLD_SLACK_MARGIN | +0.316 | strong | 141 | 55 | 6.6 |
| DETAILED_ROUTE_END_ITERATION | -0.305 | strong | 141 | 49 | 6.6 |
| ROUTING_LAYER_ADJUSTMENT | +0.259 | moderate | 141 | 25 | 6.6 |
| CTS_CLUSTER_DIAMETER | +0.246 | moderate | 141 | 64 | 6.6 |
| SETUP_SLACK_MARGIN | +0.244 | moderate | 141 | 53 | 6.6 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.204 | moderate | 141 | 3 | 6.6 |
| CORE_MARGIN | +0.190 | moderate | 143 | 17 | 6.5 |
| CORE_ASPECT_RATIO | +0.156 | moderate | 143 | 34 | 6.5 |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | -0.155 | moderate | 141 | 4 | 6.6 |
| CTS_CLUSTER_SIZE | +0.101 | weak | 141 | 30 | 6.6 |

**tns_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| TNS_END_PERCENT | +0.294 | moderate | 143 | 48 | 109.9 |
| PLACE_DENSITY | -0.265 | moderate | 141 | 39 | 111.0 |
| HOLD_SLACK_MARGIN | +0.257 | moderate | 141 | 55 | 111.0 |
| DETAILED_ROUTE_END_ITERATION | -0.243 | moderate | 141 | 49 | 111.0 |
| CTS_CLUSTER_DIAMETER | +0.230 | moderate | 141 | 64 | 111.0 |
| ROUTING_LAYER_ADJUSTMENT | +0.227 | moderate | 141 | 25 | 111.0 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.220 | moderate | 141 | 3 | 111.0 |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | -0.196 | moderate | 141 | 4 | 111.0 |
| SETUP_SLACK_MARGIN | +0.187 | moderate | 141 | 53 | 111.0 |
| CORE_UTILIZATION | +0.146 | weak | 143 | 38 | 109.9 |
| CORE_MARGIN | +0.141 | weak | 143 | 17 | 109.9 |
| CTS_CLUSTER_SIZE | +0.135 | weak | 141 | 30 | 111.0 |

**utilization_pct** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_UTILIZATION | +0.984 | strong | 52 | 21 | 24.7 |
| PLACE_DENSITY | +0.529 | strong | 50 | 26 | 25.1 |
| CORE_ASPECT_RATIO | -0.528 | strong | 52 | 17 | 24.7 |
| ROUTING_LAYER_ADJUSTMENT | -0.394 | strong | 50 | 12 | 25.1 |
| CORE_MARGIN | -0.347 | strong | 52 | 9 | 24.7 |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | -0.335 | strong | 50 | 3 | 25.1 |
| SETUP_SLACK_MARGIN | -0.287 | moderate | 50 | 23 | 25.1 |
| HOLD_SLACK_MARGIN | -0.184 | moderate | 50 | 24 | 25.1 |
| DETAILED_ROUTE_END_ITERATION | +0.136 | weak | 50 | 25 | 25.1 |
| TNS_END_PERCENT | +0.122 | weak | 52 | 26 | 24.7 |
| CTS_CLUSTER_SIZE | -0.109 | weak | 50 | 20 | 25.1 |

**wns_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| PLACE_DENSITY | -0.329 | strong | 141 | 39 | 77.6 |
| TNS_END_PERCENT | +0.326 | strong | 143 | 48 | 76.9 |
| HOLD_SLACK_MARGIN | +0.316 | strong | 141 | 55 | 77.6 |
| DETAILED_ROUTE_END_ITERATION | -0.305 | strong | 141 | 49 | 77.6 |
| ROUTING_LAYER_ADJUSTMENT | +0.258 | moderate | 141 | 25 | 77.6 |
| SETUP_SLACK_MARGIN | +0.245 | moderate | 141 | 53 | 77.6 |
| CTS_CLUSTER_DIAMETER | +0.245 | moderate | 141 | 64 | 77.6 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.204 | moderate | 141 | 3 | 77.6 |
| CORE_MARGIN | +0.189 | moderate | 143 | 17 | 76.9 |
| CORE_ASPECT_RATIO | +0.157 | moderate | 143 | 34 | 76.9 |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | -0.155 | moderate | 141 | 4 | 77.6 |
| CTS_CLUSTER_SIZE | +0.103 | weak | 141 | 30 | 77.6 |

### finish

**drc_violations** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| DETAILED_ROUTE_END_ITERATION | +0.343 | strong | 69 | 27 | 667.8 |
| CORE_UTILIZATION | +0.339 | strong | 71 | 27 | 677.5 |
| CORE_ASPECT_RATIO | -0.322 | strong | 71 | 22 | 677.5 |
| CORE_MARGIN | -0.252 | moderate | 71 | 9 | 677.5 |
| ROUTING_LAYER_ADJUSTMENT | -0.229 | moderate | 69 | 15 | 667.8 |
| PLACE_DENSITY | +0.176 | moderate | 69 | 34 | 667.8 |
| CTS_CLUSTER_DIAMETER | -0.165 | moderate | 69 | 37 | 667.8 |
| TNS_END_PERCENT | -0.164 | moderate | 71 | 29 | 677.5 |
| HOLD_SLACK_MARGIN | -0.133 | weak | 69 | 33 | 667.8 |
| CTS_CLUSTER_SIZE | -0.128 | weak | 69 | 23 | 667.8 |
| SETUP_SLACK_MARGIN | -0.111 | weak | 69 | 31 | 667.8 |

**fmax_mhz** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| PLACE_DENSITY | -0.264 | moderate | 50 | 26 | 6.8 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.251 | moderate | 50 | 3 | 6.8 |
| CORE_ASPECT_RATIO | +0.224 | moderate | 52 | 17 | 6.7 |
| ROUTING_LAYER_ADJUSTMENT | +0.201 | moderate | 50 | 12 | 6.8 |
| DETAILED_ROUTE_END_ITERATION | -0.173 | moderate | 50 | 25 | 6.8 |
| HOLD_SLACK_MARGIN | +0.153 | moderate | 50 | 24 | 6.8 |
| CORE_MARGIN | +0.138 | weak | 52 | 9 | 6.7 |
| TNS_END_PERCENT | +0.110 | weak | 52 | 26 | 6.7 |
| PLACE_DENSITY_LB_ADDON | +0.089 | weak | 52 | 17 | 6.7 |

**power_total_w** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CTS_CLUSTER_DIAMETER | -0.329 | strong | 50 | 31 | 13.5 |
| ROUTING_LAYER_ADJUSTMENT | -0.318 | strong | 50 | 12 | 13.5 |
| PLACE_DENSITY | +0.189 | moderate | 50 | 26 | 13.5 |
| CTS_CLUSTER_SIZE | -0.168 | moderate | 50 | 20 | 13.5 |
| HOLD_SLACK_MARGIN | -0.151 | moderate | 50 | 24 | 13.5 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | +0.123 | weak | 50 | 3 | 13.5 |
| PLACE_DENSITY_LB_ADDON | +0.120 | weak | 52 | 17 | 13.4 |
| CORE_ASPECT_RATIO | -0.105 | weak | 52 | 17 | 13.4 |
| CORE_MARGIN | -0.103 | weak | 52 | 9 | 13.4 |

**tns_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| PLACE_DENSITY | -0.209 | moderate | 50 | 26 | 122.3 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.204 | moderate | 50 | 3 | 122.3 |
| CORE_ASPECT_RATIO | +0.145 | weak | 52 | 17 | 121.0 |
| DETAILED_ROUTE_END_ITERATION | -0.127 | weak | 50 | 25 | 122.3 |
| ROUTING_LAYER_ADJUSTMENT | +0.126 | weak | 50 | 12 | 122.3 |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | -0.115 | weak | 50 | 3 | 122.3 |
| CORE_MARGIN | +0.112 | weak | 52 | 9 | 121.0 |
| HOLD_SLACK_MARGIN | +0.102 | weak | 50 | 24 | 122.3 |

**utilization_pct** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| CORE_UTILIZATION | +0.984 | strong | 52 | 21 | 24.7 |
| PLACE_DENSITY | +0.529 | strong | 50 | 26 | 25.1 |
| CORE_ASPECT_RATIO | -0.528 | strong | 52 | 17 | 24.7 |
| ROUTING_LAYER_ADJUSTMENT | -0.394 | strong | 50 | 12 | 25.1 |
| CORE_MARGIN | -0.347 | strong | 52 | 9 | 24.7 |
| CELL_PAD_IN_SITES_DETAIL_PLACEMENT | -0.335 | strong | 50 | 3 | 25.1 |
| SETUP_SLACK_MARGIN | -0.287 | moderate | 50 | 23 | 25.1 |
| HOLD_SLACK_MARGIN | -0.184 | moderate | 50 | 24 | 25.1 |
| DETAILED_ROUTE_END_ITERATION | +0.136 | weak | 50 | 25 | 25.1 |
| TNS_END_PERCENT | +0.122 | weak | 52 | 26 | 24.7 |
| CTS_CLUSTER_SIZE | -0.109 | weak | 50 | 20 | 25.1 |

**wns_ns** — knobs passing Gate 1 with weak+ sensitivity:

| param | ρ | verdict | n | param uniq | metric CV% |
|-------|---|---------|---|------------|------------|
| PLACE_DENSITY | -0.263 | moderate | 50 | 26 | 86.8 |
| CELL_PAD_IN_SITES_GLOBAL_PLACEMENT | -0.251 | moderate | 50 | 3 | 86.8 |
| CORE_ASPECT_RATIO | +0.219 | moderate | 52 | 17 | 85.4 |
| ROUTING_LAYER_ADJUSTMENT | +0.200 | moderate | 50 | 12 | 86.8 |
| DETAILED_ROUTE_END_ITERATION | -0.175 | moderate | 50 | 25 | 86.8 |
| HOLD_SLACK_MARGIN | +0.147 | weak | 50 | 24 | 86.8 |
| CORE_MARGIN | +0.137 | weak | 52 | 9 | 85.4 |
| TNS_END_PERCENT | +0.112 | weak | 52 | 26 | 85.4 |
| PLACE_DENSITY_LB_ADDON | +0.089 | weak | 52 | 17 | 85.4 |

### Shortlist hints (floorplan)

- **wns_ns**: TNS_END_PERCENT, HOLD_SLACK_MARGIN, SETUP_SLACK_MARGIN, PLACE_DENSITY, CORE_MARGIN, ROUTING_LAYER_ADJUSTMENT
- **power_total_w**: ROUTING_LAYER_ADJUSTMENT, CORE_MARGIN, PLACE_DENSITY, SETUP_SLACK_MARGIN
- **utilization_pct**: CORE_UTILIZATION, CORE_ASPECT_RATIO, CORE_MARGIN, ROUTING_LAYER_ADJUSTMENT, PLACE_DENSITY, SETUP_SLACK_MARGIN
