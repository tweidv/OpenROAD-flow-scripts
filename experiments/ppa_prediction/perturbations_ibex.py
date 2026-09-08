"""Ibex trajectory configs for PPA prediction."""

from __future__ import annotations

from designs import IBEX_BASE, DesignSpec, generated_dir
from perturbations import TrajectoryConfig, _cfg, write_manifest


def generate_ibex_trajectories() -> list[TrajectoryConfig]:
    """~18 trajectories: enough for learning-curve signal without a 70-run sweep."""
    trajectories: list[TrajectoryConfig] = [
        _cfg("ibex_default", "default", base=IBEX_BASE),
        # pilot (already run)
        _cfg(
            "ibex_sweep_001",
            "pilot",
            base=IBEX_BASE,
            CORE_UTILIZATION=45,
            CLK_PERIOD=2.5,
        ),
        # hand-crafted diversity
        _cfg(
            "ibex_small_01",
            "small",
            base=IBEX_BASE,
            CORE_UTILIZATION=45,
            PLACE_DENSITY_LB_ADDON=0.15,
        ),
        _cfg(
            "ibex_small_02",
            "small",
            base=IBEX_BASE,
            CORE_UTILIZATION=55,
            PLACE_DENSITY_LB_ADDON=0.25,
        ),
        _cfg(
            "ibex_small_03",
            "small",
            base=IBEX_BASE,
            CLK_PERIOD=2.5,
            CTS_CLUSTER_SIZE=40,
        ),
        _cfg(
            "ibex_medium_01",
            "medium",
            base=IBEX_BASE,
            CORE_UTILIZATION=42,
            CLK_PERIOD=2.8,
        ),
        _cfg(
            "ibex_medium_02",
            "medium",
            base=IBEX_BASE,
            CORE_UTILIZATION=58,
            CLK_PERIOD=2.0,
        ),
        _cfg(
            "ibex_large_01",
            "large",
            base=IBEX_BASE,
            CORE_UTILIZATION=38,
            CLK_PERIOD=3.5,
        ),
        _cfg(
            "ibex_bad_01",
            "bad",
            base=IBEX_BASE,
            CORE_UTILIZATION=65,
            CLK_PERIOD=1.8,
        ),
    ]

    # compact util × clk grid (9 points)
    idx = 2
    for util in (45, 50, 55):
        for clk in (2.0, 2.2, 2.5):
            tid = f"ibex_sweep_{idx:03d}"
            if tid == "ibex_sweep_001":
                idx += 1
                tid = f"ibex_sweep_{idx:03d}"
            trajectories.append(
                _cfg(
                    tid,
                    "sweep",
                    base=IBEX_BASE,
                    CORE_UTILIZATION=util,
                    CLK_PERIOD=clk,
                )
            )
            idx += 1

    seen: set[str] = set()
    unique: list[TrajectoryConfig] = []
    for traj in trajectories:
        if traj.trajectory_id in seen:
            continue
        seen.add(traj.trajectory_id)
        unique.append(traj)
    return unique


def write_ibex_manifest(spec: DesignSpec, trajectories: list[TrajectoryConfig]):
    return write_manifest(generated_dir(spec), trajectories)
