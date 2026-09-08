"""Design-specific settings for PPA prediction experiments."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FLOW = ROOT / "flow"


@dataclass(frozen=True)
class DesignSpec:
    key: str
    platform: str
    log_name: str
    base_config: Path
    sdc_design: str
    clk_port_name: str
    clk_latency: float
    config_exports: dict[str, float | int]
    base_params: dict[str, float | int]


GCD_BASE = {
    "CORE_UTILIZATION": 55,
    "PLACE_DENSITY_LB_ADDON": 0.20,
    "CORE_ASPECT_RATIO": 1.0,
    "CORE_MARGIN": 1.0,
    "CTS_CLUSTER_SIZE": 50,
    "CTS_CLUSTER_DIAMETER": 50,
    "TNS_END_PERCENT": 100,
    "CLK_PERIOD": 0.25,
    "CELL_PAD_IN_SITES_GLOBAL_PLACEMENT": 0,
    "CELL_PAD_IN_SITES_DETAIL_PLACEMENT": 0,
    "SETUP_SLACK_MARGIN": 0.0,
    "ENABLE_PLACE_REPAIR_TIMING": 0,
    "ROUTING_LAYER_ADJUSTMENT": 0.5,
}

IBEX_BASE = {
    "CORE_UTILIZATION": 50,
    "PLACE_DENSITY_LB_ADDON": 0.20,
    "CORE_ASPECT_RATIO": 1.0,
    "CTS_CLUSTER_SIZE": 50,
    "TNS_END_PERCENT": 100,
    "CLK_PERIOD": 2.2,
    "CELL_PAD_IN_SITES_GLOBAL_PLACEMENT": 0,
    "CELL_PAD_IN_SITES_DETAIL_PLACEMENT": 0,
}

DESIGNS: dict[str, DesignSpec] = {
    "gcd": DesignSpec(
        key="gcd",
        platform="nangate45",
        log_name="gcd",
        base_config=FLOW / "designs/nangate45/gcd/config.mk",
        sdc_design="gcd",
        clk_port_name="clk",
        clk_latency=0.070,
        config_exports={
            "CORE_UTILIZATION": 55,
            "PLACE_DENSITY_LB_ADDON": 0.20,
            "TNS_END_PERCENT": 100,
        },
        base_params=GCD_BASE,
    ),
    "ibex": DesignSpec(
        key="ibex",
        platform="nangate45",
        log_name="ibex",
        base_config=FLOW / "designs/nangate45/ibex/config.mk",
        sdc_design="ibex_core",
        clk_port_name="clk_i",
        clk_latency=0.285,
        config_exports={
            "CORE_UTILIZATION": 50,
            "PLACE_DENSITY_LB_ADDON": 0.20,
            "TNS_END_PERCENT": 100,
        },
        base_params=IBEX_BASE,
    ),
}


def log_dir(spec: DesignSpec, trajectory_id: str) -> Path:
    return FLOW / "logs" / spec.platform / spec.log_name / f"ppa_{trajectory_id}"


def generated_dir(spec: DesignSpec) -> Path:
    return Path(__file__).resolve().parent / "generated" / spec.key
