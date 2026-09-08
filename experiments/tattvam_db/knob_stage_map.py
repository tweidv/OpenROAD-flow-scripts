"""Which ORFS knobs can affect metrics reported at each flow stage.

Gate 1 of knob screening: a knob is *reachable* at stage S if the flow has
already applied it by the time stage S reports metrics.

Stage order matches Tattvam metric keys: synth → floorplan → place → cts → route → finish.
"""

from __future__ import annotations

STAGE_ORDER: list[str] = [
    "synth",
    "floorplan",
    "place",
    "cts",
    "route",
    "finish",
]

# Earliest stage where changing the knob affects downstream state.
KNOB_FIRST_STAGE: dict[str, str] = {
    # Synthesis (netlist before floorplan)
    "ABC_AREA": "synth",
    "SWAP_ARITH_OPERATORS": "synth",
    "SYNTH_HIERARCHICAL": "synth",
    "OPENROAD_HIERARCHICAL": "synth",
    # Floorplan init + floorplan timing repair
    "CORE_UTILIZATION": "floorplan",
    "CORE_ASPECT_RATIO": "floorplan",
    "CORE_MARGIN": "floorplan",
    "PLACE_DENSITY_LB_ADDON": "floorplan",
    "PLACE_DENSITY": "floorplan",
    "SETUP_SLACK_MARGIN": "floorplan",
    "HOLD_SLACK_MARGIN": "floorplan",
    "TNS_END_PERCENT": "floorplan",
    "ROUTING_LAYER_ADJUSTMENT": "floorplan",
    "CELL_PAD_IN_SITES_GLOBAL_PLACEMENT": "floorplan",
    "CELL_PAD_IN_SITES_DETAIL_PLACEMENT": "floorplan",
    "IO_PLACER_H": "floorplan",
    "IO_PLACER_V": "floorplan",
    "REMOVE_ABC_BUFFERS": "floorplan",
    "DONT_BUFFER_PORTS": "floorplan",
    "FASTROUTE_TCL": "floorplan",
    # Global / detailed placement
    "GPL_ROUTABILITY_DRIVEN": "place",
    "GPL_TIMING_DRIVEN": "place",
    "PLACE_PINS_ARGS": "place",
    "ENABLE_DPO": "place",
    # CTS
    "CTS_CLUSTER_SIZE": "cts",
    "CTS_CLUSTER_DIAMETER": "cts",
    # Routing
    "GLOBAL_ROUTE_ARGS": "route",
    "MIN_ROUTING_LAYER": "route",
    "MAX_ROUTING_LAYER": "route",
    "DETAILED_ROUTE_END_ITERATION": "route",
    "CLUSTER_FLOPS": "route",
    "MATCH_CELL_FOOTPRINT": "route",
    # Timing repair toggles (placement/resizing paths)
    "SKIP_VT_SWAP": "place",
    "SKIP_PIN_SWAP": "place",
    "SKIP_GATE_CLONING": "place",
    "MAX_REPAIR_TIMING_ITER": "place",
    # Corners / MMMC (STA at all post-synth stages)
    "CORNERS": "synth",
}

# PPA-ish metrics to screen (must exist in metrics table).
SCREEN_METRICS: dict[str, list[str]] = {
    "timing": ["wns_ns", "tns_ns", "fmax_mhz", "worst_slack_ns"],
    "power": ["power_total_w"],
    "area": ["utilization_pct", "core_area_um2", "die_area_um2", "design_area_um2"],
    "signoff": ["drc_violations", "drc_status"],
    "cts": ["clock_skew_ns", "clock_insertion_delay_ns", "hold_violation_count"],
}

DEFAULT_METRICS: list[str] = [
    "wns_ns",
    "tns_ns",
    "fmax_mhz",
    "power_total_w",
    "utilization_pct",
    "core_area_um2",
]

SYNTH_METRICS: list[str] = [
    "cell_count",
    "chip_area_um2",
    "comb_area_um2",
    "seq_area_um2",
    "seq_area_pct",
    "logic_depth",
]

# Best verdict rank when aggregating across metrics (higher = stronger signal).
VERDICT_RANK: dict[str, int] = {
    "wrong_stage": 0,
    "non_numeric": 1,
    "label_flat": 2,
    "param_flat": 3,
    "insensitive": 4,
    "weak": 5,
    "moderate": 6,
    "strong": 7,
}

VERDICT_FROM_RANK: dict[int, str] = {v: k for k, v in VERDICT_RANK.items()}

# Compact codes for grid display.
VERDICT_CODE: dict[str, str] = {
    "strong": "S",
    "moderate": "M",
    "weak": "W",
    "insensitive": "I",
    "wrong_stage": "WS",
    "param_flat": "PF",
    "label_flat": "LF",
    "non_numeric": "NN",
}

# Knobs that are paths / Tcl / free text — skip Gate 2 correlation.
NON_NUMERIC_KNOBS: frozenset[str] = frozenset(
    {
        "FASTROUTE_TCL",
        "GLOBAL_ROUTE_ARGS",
        "PLACE_PINS_ARGS",
        "CORNERS",
    }
)


def stage_index(stage: str) -> int:
    try:
        return STAGE_ORDER.index(stage)
    except ValueError as exc:
        raise ValueError(f"unknown stage {stage!r}; expected one of {STAGE_ORDER}") from exc


def knob_reaches_stage(knob: str, stage: str) -> bool:
    """True if changing *knob* can influence metrics reported at *stage*."""
    first = KNOB_FIRST_STAGE.get(knob)
    if first is None:
        return False
    return stage_index(first) <= stage_index(stage)


def knobs_for_stage(stage: str) -> list[str]:
    return sorted(k for k in KNOB_FIRST_STAGE if knob_reaches_stage(k, stage))


def metrics_for_stage(stage: str) -> list[str]:
    """Metrics that exist and make sense at this stage."""
    if stage == "synth":
        return list(SYNTH_METRICS)
    base = list(DEFAULT_METRICS)
    if stage == "cts":
        base.extend(SCREEN_METRICS["cts"])
    if stage == "finish":
        base.extend(SCREEN_METRICS["signoff"])
    # De-dupe while preserving order.
    seen: set[str] = set()
    out: list[str] = []
    for m in base:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out
