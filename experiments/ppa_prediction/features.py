"""Extract checkpoint features from ORFS stage metrics JSON logs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

STAGES = ("floorplan", "placement", "cts", "routing")

CHECKPOINT_FILES = {
    "floorplan": "2_1_floorplan.json",
    "placement": "3_5_place_dp.json",
    "cts": "4_1_cts.json",
    "routing": "5_2_route.json",
}

AUX_FILES = {
    "placement_gp": "3_3_place_gp.json",
    "routing_grt": "5_1_grt.json",
}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open() as f:
        return json.load(f)


def _get(metrics: dict[str, Any], key: str, default: float = 0.0) -> float:
    val = metrics.get(key, default)
    if val in (None, "N/A", "ERR"):
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _inv_fmax(metrics: dict[str, Any], prefix: str) -> float:
    """Clock period (1/fmax) in seconds; higher means worse timing."""
    fmax = _get(metrics, f"{prefix}__timing__fmax")
    if fmax <= 0:
        return 0.0
    return 1.0 / fmax


def _congestion_proxy(gp: dict[str, Any]) -> float:
    """GPL routability congestion estimate in [0, 1] (higher = more congested)."""
    return _get(gp, "globalplace__gpl__routability__congestion")

STAGE_PREFIX = {
    "floorplan": "floorplan",
    "placement": "detailedplace",
    "cts": "cts",
    "routing": "globalroute",
}


def _norm_pta(metrics: dict[str, Any], prefix: str, targets: dict[str, float]) -> dict[str, float]:
    """Normalise checkpoint P/T/A against batch targets (same direction as V components)."""
    p = _get(metrics, f"{prefix}__power__total")
    t = _get(metrics, f"{prefix}__timing__fmax")
    a = _get(metrics, f"{prefix}__design__instance__area__stdcell")
    p_tgt = float(targets["P_target"])
    t_tgt = float(targets["T_target"])
    a_tgt = float(targets["A_target"])
    return {
        "norm_p": p_tgt / p if p > 0 else 0.0,
        "norm_t": t / t_tgt if t_tgt > 0 else 0.0,
        "norm_a": a_tgt / a if a > 0 else 0.0,
    }


def extract_floorplan_features(
    m: dict[str, Any], params: dict[str, Any], targets: dict[str, float] | None = None
) -> dict[str, float]:
    core = _get(m, "floorplan__design__core__area")
    util = _get(m, "floorplan__design__instance__utilization")
    die = _get(m, "floorplan__design__die__area", core)
    aspect = float(params.get("CORE_ASPECT_RATIO", 1.0))
    if core > 0 and die > 0:
        # Approximate physical aspect when only areas are logged.
        aspect = max(aspect, die / core)
    feats = {
        "core_area": core,
        "utilization": util,
        "aspect_ratio": aspect,
    }
    if targets:
        feats.update(_norm_pta(m, "floorplan", targets))
    return feats


def extract_placement_features(
    m: dict[str, Any], gp: dict[str, Any], targets: dict[str, float] | None = None
) -> dict[str, float]:
    feats = {
        "hpwl": _get(m, "detailedplace__route__wirelength__estimated"),
        "placement_density": _get(m, "detailedplace__design__instance__utilization"),
        "estimated_congestion": _congestion_proxy(gp),
        "inv_fmax": _inv_fmax(m, "detailedplace"),
    }
    if targets:
        feats.update(_norm_pta(m, "detailedplace", targets))
    return feats


def extract_cts_features(m: dict[str, Any], targets: dict[str, float] | None = None) -> dict[str, float]:
    setup_buf = _get(m, "cts__design__instance__count__setup_buffer")
    hold_buf = _get(m, "cts__design__instance__count__hold_buffer")
    feats = {
        "inv_fmax": _inv_fmax(m, "cts"),
        "total_negative_slack": _get(m, "cts__timing__setup__tns"),
        "clock_skew": _get(m, "cts__clock__skew__setup"),
        "buffer_inverter_count": setup_buf + hold_buf,
    }
    if targets:
        feats.update(_norm_pta(m, "cts", targets))
    return feats


def extract_routing_features(
    route: dict[str, Any],
    grt: dict[str, Any],
    gp: dict[str, Any],
    targets: dict[str, float] | None = None,
) -> dict[str, float]:
    feats = {
        "routed_wirelength": _get(route, "detailedroute__route__wirelength"),
        "inv_fmax": _inv_fmax(grt, "globalroute"),
        "total_negative_slack": _get(grt, "globalroute__timing__setup__tns"),
        "congestion": _congestion_proxy(gp),
        "drc_violation_count": _get(route, "detailedroute__route__drc_errors"),
    }
    if targets:
        feats.update(_norm_pta(grt, "globalroute", targets))
    return feats


def extract_trajectory_features(
    log_dir: Path, params: dict[str, Any], targets: dict[str, float] | None = None
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    gp = load_json(log_dir / AUX_FILES["placement_gp"])
    grt = load_json(log_dir / AUX_FILES["routing_grt"])

    extractors = {
        "floorplan": lambda m: extract_floorplan_features(m, params, targets),
        "placement": lambda m: extract_placement_features(m, gp, targets),
        "cts": lambda m: extract_cts_features(m, targets),
        "routing": lambda m: extract_routing_features(m, grt, gp, targets),
    }

    for stage in STAGES:
        metrics = load_json(log_dir / CHECKPOINT_FILES[stage])
        if not metrics:
            continue
        feats = extractors[stage](metrics)
        feats["stage"] = stage
        rows.append(feats)
    return rows
