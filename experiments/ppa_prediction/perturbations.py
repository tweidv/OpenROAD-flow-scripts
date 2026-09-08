"""Generate perturbed GCD flow configurations for trajectory diversity."""

from __future__ import annotations

import copy
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

BASE = {
    "CORE_UTILIZATION": 55,
    "PLACE_DENSITY_LB_ADDON": 0.20,
    "CORE_ASPECT_RATIO": 1.0,
    "CTS_CLUSTER_SIZE": 50,
    "TNS_END_PERCENT": 100,
    "CLK_PERIOD": 0.25,
    "CELL_PAD_IN_SITES_GLOBAL_PLACEMENT": 0,
    "CELL_PAD_IN_SITES_DETAIL_PLACEMENT": 0,
}


@dataclass
class TrajectoryConfig:
    trajectory_id: str
    tier: str
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _cfg(
    tid: str,
    tier: str,
    *,
    base: dict[str, Any] | None = None,
    **overrides: Any,
) -> TrajectoryConfig:
    params = copy.deepcopy(base if base is not None else BASE)
    params.update(overrides)
    return TrajectoryConfig(trajectory_id=tid, tier=tier, params=params)


def generate_sweep_trajectories(start_idx: int = 1) -> list[TrajectoryConfig]:
    """Systematic grid sweep for additional trajectory diversity."""
    trajectories: list[TrajectoryConfig] = []
    idx = start_idx

    utilizations = [42, 48, 52, 58, 64, 70]
    clk_periods = [0.18, 0.22, 0.28, 0.32, 0.38, 0.45, 0.52]
    for util in utilizations:
        for clk in clk_periods:
            trajectories.append(
                _cfg(
                    f"traj_sweep_{idx:03d}",
                    "sweep",
                    CORE_UTILIZATION=util,
                    CLK_PERIOD=clk,
                )
            )
            idx += 1

    aspect_util = [
        (0.75, 50),
        (0.75, 60),
        (0.85, 55),
        (1.15, 50),
        (1.15, 60),
        (1.30, 55),
        (1.30, 65),
    ]
    for aspect, util in aspect_util:
        trajectories.append(
            _cfg(
                f"traj_sweep_{idx:03d}",
                "sweep",
                CORE_ASPECT_RATIO=aspect,
                CORE_UTILIZATION=util,
            )
        )
        idx += 1

    density_cts = [
        (0.08, 30),
        (0.12, 40),
        (0.18, 50),
        (0.24, 60),
        (0.28, 80),
        (0.32, 100),
    ]
    for addon, cts in density_cts:
        trajectories.append(
            _cfg(
                f"traj_sweep_{idx:03d}",
                "sweep",
                PLACE_DENSITY_LB_ADDON=addon,
                CTS_CLUSTER_SIZE=cts,
            )
        )
        idx += 1

    return trajectories


def _sweep_id(idx: int) -> str:
    return f"traj_sweep_{idx:04d}" if idx >= 1000 else f"traj_sweep_{idx:03d}"


def generate_mega_sweep(start_idx: int = 56) -> list[TrajectoryConfig]:
    """Large util×clk grid (~2000 configs) for overnight data collection."""
    trajectories: list[TrajectoryConfig] = []
    idx = start_idx

    # Primary grid: 41 utils × 49 clk periods ≈ 2000 util/clk combos.
    utilizations = list(range(35, 76))
    clk_periods = [round(0.14 + i * 0.01, 2) for i in range(49)]  # 0.14 .. 0.62
    for util in utilizations:
        for clk in clk_periods:
            trajectories.append(
                _cfg(
                    _sweep_id(idx),
                    "mega_sweep",
                    CORE_UTILIZATION=util,
                    CLK_PERIOD=clk,
                )
            )
            idx += 1

    # Secondary diversity: aspect ratio × util (default clk).
    for aspect_i in range(5, 16):  # 0.50 .. 1.50 step 0.10
        aspect = round(aspect_i / 10.0, 2)
        for util in range(38, 74, 2):
            trajectories.append(
                _cfg(
                    _sweep_id(idx),
                    "mega_sweep",
                    CORE_ASPECT_RATIO=aspect,
                    CORE_UTILIZATION=util,
                )
            )
            idx += 1

    # Density addon × util.
    for addon_i in range(4, 40, 2):  # 0.04 .. 0.38 step 0.02
        addon = round(addon_i / 100.0, 2)
        for util in range(40, 72, 2):
            trajectories.append(
                _cfg(
                    _sweep_id(idx),
                    "mega_sweep",
                    PLACE_DENSITY_LB_ADDON=addon,
                    CORE_UTILIZATION=util,
                )
            )
            idx += 1

    # CTS cluster × TNS repair budget.
    for cts in range(20, 125, 5):
        for tns in (10, 25, 40, 55, 70, 85, 100):
            trajectories.append(
                _cfg(
                    _sweep_id(idx),
                    "mega_sweep",
                    CTS_CLUSTER_SIZE=cts,
                    TNS_END_PERCENT=tns,
                )
            )
            idx += 1

    return trajectories


def _params_key(params: dict[str, Any]) -> tuple[tuple[str, Any], ...]:
    return tuple(sorted(params.items()))


def generate_trajectories() -> list[TrajectoryConfig]:
    """Hand-crafted sweep plus systematic grid."""
    trajectories: list[TrajectoryConfig] = []

    trajectories.append(_cfg("traj_default", "default"))

    small_variants = [
        {"CORE_UTILIZATION": 50, "PLACE_DENSITY_LB_ADDON": 0.15},
        {"CORE_UTILIZATION": 60, "PLACE_DENSITY_LB_ADDON": 0.25},
        {"CLK_PERIOD": 0.30, "CTS_CLUSTER_SIZE": 40},
        {"CORE_ASPECT_RATIO": 1.2, "TNS_END_PERCENT": 80},
        {"CORE_ASPECT_RATIO": 0.9, "CORE_UTILIZATION": 52},
    ]
    for i, overrides in enumerate(small_variants, start=1):
        trajectories.append(_cfg(f"traj_small_{i:02d}", "small", **overrides))

    medium_variants = [
        {"CORE_UTILIZATION": 45, "PLACE_DENSITY_LB_ADDON": 0.10, "CLK_PERIOD": 0.35},
        {"CORE_UTILIZATION": 65, "PLACE_DENSITY_LB_ADDON": 0.30, "CTS_CLUSTER_SIZE": 80},
        {"CLK_PERIOD": 0.20, "TNS_END_PERCENT": 50},
        {"CORE_ASPECT_RATIO": 0.6, "CORE_UTILIZATION": 58},
        {"CORE_ASPECT_RATIO": 1.35, "CORE_UTILIZATION": 56},
    ]
    for i, overrides in enumerate(medium_variants, start=1):
        trajectories.append(_cfg(f"traj_medium_{i:02d}", "medium", **overrides))

    large_variants = [
        {"CORE_UTILIZATION": 40, "CLK_PERIOD": 0.45, "PLACE_DENSITY_LB_ADDON": 0.05},
        {"CORE_UTILIZATION": 72, "PLACE_DENSITY_LB_ADDON": 0.35, "CTS_CLUSTER_SIZE": 120},
        {"CLK_PERIOD": 0.15, "TNS_END_PERCENT": 30},
        {"CORE_ASPECT_RATIO": 0.5, "CORE_UTILIZATION": 62},
    ]
    for i, overrides in enumerate(large_variants, start=1):
        trajectories.append(_cfg(f"traj_large_{i:02d}", "large", **overrides))

    bad_variants = [
        {"CORE_UTILIZATION": 85, "PLACE_DENSITY_LB_ADDON": 0.40, "CLK_PERIOD": 0.12},
        {"CORE_UTILIZATION": 90, "CLK_PERIOD": 0.10, "CTS_CLUSTER_SIZE": 200},
        {"CORE_UTILIZATION": 35, "CLK_PERIOD": 0.60, "TNS_END_PERCENT": 10},
        {"CORE_UTILIZATION": 78, "CORE_ASPECT_RATIO": 2.0, "CLK_PERIOD": 0.12},
    ]
    for i, overrides in enumerate(bad_variants, start=1):
        trajectories.append(_cfg(f"traj_bad_{i:02d}", "bad", **overrides))

    trajectories.extend(generate_sweep_trajectories())
    trajectories.extend(generate_mega_sweep(start_idx=56))

    seen_ids: set[str] = set()
    seen_params: set[tuple[tuple[str, Any], ...]] = set()
    unique: list[TrajectoryConfig] = []
    for traj in trajectories:
        if traj.trajectory_id in seen_ids:
            continue
        pk = _params_key(traj.params)
        if pk in seen_params:
            continue
        seen_ids.add(traj.trajectory_id)
        seen_params.add(pk)
        unique.append(traj)
    return unique


def write_manifest(out_dir: Path, trajectories: list[TrajectoryConfig]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = [t.to_dict() for t in trajectories]
    path = out_dir / "trajectories.json"
    path.write_text(json.dumps(manifest, indent=2))
    return path
