#!/usr/bin/env python3
"""Inventory ALL ORFS/OpenROAD metrics and trajectory parameters from existing logs."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from designs import DESIGNS, log_dir
from features import CHECKPOINT_FILES, AUX_FILES, STAGES

EXP = Path(__file__).resolve().parent
FLOW = EXP.parents[1] / "flow"

# Currently hand-picked in features.py
CURRENTLY_EXTRACTED = {
    "core_area",
    "utilization",
    "aspect_ratio",
    "hpwl",
    "placement_density",
    "estimated_congestion",
    "inv_fmax",
    "total_negative_slack",
    "clock_skew",
    "buffer_inverter_count",
    "routed_wirelength",
    "congestion",
    "drc_violation_count",
    "norm_p",
    "norm_t",
    "norm_a",
}

STAGE_FILE_MAP = {
    "1_synth.json": ("synth", 1),
    "2_1_floorplan.json": ("floorplan", 2),
    "2_2_floorplan_macro.json": ("floorplan_macro", 2),
    "2_3_floorplan_tapcell.json": ("floorplan_tapcell", 2),
    "2_4_floorplan_pdn.json": ("floorplan_pdn", 2),
    "3_1_place_gp_skip_io.json": ("place_gp_skip_io", 3),
    "3_2_place_iop.json": ("place_iop", 3),
    "3_3_place_gp.json": ("place_gp", 3),
    "3_4_place_resized.json": ("place_resized", 3),
    "3_5_place_dp.json": ("place_dp", 3),
    "4_1_cts.json": ("cts", 4),
    "5_1_grt.json": ("grt", 5),
    "5_2_route.json": ("route", 6),
    "5_3_fillcell.json": ("fillcell", 6),
    "6_1_fill.json": ("fill", 6),
    "6_report.json": ("finish", 7),
}

# Map to canonical checkpoint stage for PPA experiment alignment
CHECKPOINT_STAGE = {
    "2_1_floorplan.json": "floorplan",
    "3_5_place_dp.json": "placement",
    "4_1_cts.json": "cts",
    "5_2_route.json": "routing",
    "5_1_grt.json": "routing_aux",
    "3_3_place_gp.json": "placement_aux",
}


def metric_category(key: str) -> str:
    if key.startswith("param:"):
        return "configuration"
    top = key.split("__", 1)[0]
    mapping = {
        "floorplan": "floorplan",
        "detailedplace": "placement",
        "globalplace": "placement",
        "cts": "cts",
        "globalroute": "routing",
        "detailedroute": "routing",
        "finish": "finish",
        "synth": "synthesis",
        "timing": "timing",
        "power": "power",
        "design": "design",
        "flow": "flow",
        "clock": "clock",
        "rsz": "resizer",
        "dpl": "detailed_place",
        "grt": "global_route",
        "drt": "detailed_route",
        "pdn": "pdn",
        "tap": "tapcell",
        "macro": "macro",
        "place": "placement",
        "route": "routing",
        "fillcell": "fillcell",
    }
    return mapping.get(top, top)


def is_numeric(val) -> bool:
    if val in (None, "N/A", "ERR", ""):
        return False
    try:
        float(val)
        return True
    except (TypeError, ValueError):
        return False


def load_trajectory_params(design: str, limit: int) -> tuple[list[str], dict[str, dict]]:
    manifest = json.loads((EXP / "generated" / design / "trajectories.json").read_text())
    manifest = manifest[:limit]
    tids = [t["trajectory_id"] for t in manifest]
    params = {t["trajectory_id"]: t["params"] for t in manifest}
    param_keys = sorted({k for p in params.values() for k in p})
    return tids, params, param_keys


def scan_metrics(
    spec,
    trajectory_ids: list[str],
) -> pd.DataFrame:
    # metric_key -> stats accumulators
    records: dict[tuple[str, str], dict] = {}

    def acc(source_file: str, key: str, val, tid: str) -> None:
        k = (source_file, key)
        if k not in records:
            flow_stage, flow_num = STAGE_FILE_MAP.get(source_file, ("unknown", -1))
            records[k] = {
                "metric_key": key,
                "source_file": source_file,
                "flow_stage": flow_stage,
                "flow_stage_number": flow_num,
                "checkpoint_stage": CHECKPOINT_STAGE.get(source_file, ""),
                "metric_category": metric_category(key),
                "values": [],
                "trajectories_present": set(),
                "trajectories_missing": 0,
            }
        rec = records[k]
        if val is None or val in ("N/A", "ERR"):
            return
        rec["trajectories_present"].add(tid)
        if is_numeric(val):
            rec["values"].append(float(val))
        else:
            rec["values"].append(str(val))

    n_traj = len(trajectory_ids)
    for i, tid in enumerate(trajectory_ids):
        if i and i % 200 == 0:
            print(f"  scanned {i}/{n_traj} trajectories...", flush=True)
        log = log_dir(spec, tid)
        if not log.exists():
            continue
        for jf in sorted(log.glob("*.json")):
            source = jf.name
            if source not in STAGE_FILE_MAP:
                continue
            data = json.loads(jf.read_text()) if jf.exists() else {}
            for key, val in data.items():
                acc(source, key, val, tid)

        # clock period sidecar
        cp = FLOW / "results" / spec.platform / spec.log_name / f"ppa_{tid}" / "clock_period.txt"
        if cp.exists():
            acc("clock_period.txt", "clock_period", cp.read_text().strip(), tid)

    rows = []
    for (source_file, key), rec in sorted(records.items()):
        vals = rec["values"]
        present = len(rec["trajectories_present"])
        numeric = [v for v in vals if isinstance(v, float)]
        rows.append(
            {
                "metric_key": key,
                "source_file": source_file,
                "flow_stage": rec["flow_stage"],
                "flow_stage_number": rec["flow_stage_number"],
                "checkpoint_stage": rec["checkpoint_stage"],
                "metric_category": rec["metric_category"],
                "missing_fraction": 1.0 - present / n_traj,
                "n_trajectories_present": present,
                "n_unique": len(set(vals)),
                "n_numeric": len(numeric),
                "dtype": "float" if numeric and len(numeric) == len(vals) else "mixed",
                "min": min(numeric) if numeric else np.nan,
                "max": max(numeric) if numeric else np.nan,
                "mean": float(np.mean(numeric)) if numeric else np.nan,
                "currently_extracted": key in CURRENTLY_EXTRACTED
                or any(key.endswith(suffix) for suffix in (
                    "__design__core__area",
                    "__design__instance__utilization",
                    "__route__wirelength__estimated",
                    "__route__wirelength",
                    "__timing__setup__tns",
                    "__clock__skew__setup",
                    "__route__drc_errors",
                    "__gpl__routability__congestion",
                    "__timing__fmax",
                    "__power__total",
                    "__design__instance__area__stdcell",
                )),
            }
        )
    return pd.DataFrame(rows)


def scan_params(param_keys: list[str], params: dict[str, dict], n_traj: int) -> pd.DataFrame:
    rows = []
    for pk in param_keys:
        vals = [p.get(pk) for p in params.values()]
        numeric = [float(v) for v in vals if v is not None]
        rows.append(
            {
                "metric_key": f"param:{pk}",
                "source_file": "trajectories.json",
                "flow_stage": "configuration",
                "flow_stage_number": 0,
                "checkpoint_stage": "all",
                "metric_category": "configuration",
                "missing_fraction": 0.0,
                "n_trajectories_present": n_traj,
                "n_unique": len(set(vals)),
                "n_numeric": len(numeric),
                "dtype": "float" if len(numeric) == len(vals) else "mixed",
                "min": min(numeric) if numeric else np.nan,
                "max": max(numeric) if numeric else np.nan,
                "mean": float(np.mean(numeric)) if numeric else np.nan,
                "currently_extracted": pk in {"CORE_UTILIZATION", "CORE_ASPECT_RATIO", "CLK_PERIOD"},
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--design", default="gcd")
    parser.add_argument("--limit", type=int, default=1000)
    args = parser.parse_args()

    spec = DESIGNS[args.design]
    out_dir = EXP / "output" / args.design / "feature_analysis"
    out_dir.mkdir(parents=True, exist_ok=True)

    tids, params, param_keys = load_trajectory_params(args.design, args.limit)
    print(f"Scanning {len(tids)} trajectories, {len(STAGE_FILE_MAP)} JSON stage files each...")

    metrics_df = scan_metrics(spec, tids)
    params_df = scan_params(param_keys, params, len(tids))
    full = pd.concat([params_df, metrics_df], ignore_index=True)
    full = full.sort_values(
        ["flow_stage_number", "source_file", "metric_category", "metric_key"]
    ).reset_index(drop=True)

    out_csv = out_dir / "openroad_metrics_inventory_full.csv"
    full.to_csv(out_csv, index=False)

    # Summary by source file
    by_file = (
        full.groupby("source_file", as_index=False)
        .agg(n_metrics=("metric_key", "count"), n_extracted=("currently_extracted", "sum"))
        .sort_values("source_file")
    )
    by_file.to_csv(out_dir / "openroad_metrics_by_file.csv", index=False)

    by_cat = (
        full.groupby("metric_category", as_index=False)
        .agg(n_metrics=("metric_key", "count"))
        .sort_values("n_metrics", ascending=False)
    )
    by_cat.to_csv(out_dir / "openroad_metrics_by_category.csv", index=False)

    print(f"\nTotal inventory rows: {len(full)}")
    print(f"  configuration params: {len(params_df)}")
    print(f"  ORFS JSON metrics: {len(metrics_df)}")
    print(f"  currently extracted (approx): {int(full['currently_extracted'].sum())}")
    print(f"\nMetrics per source file:")
    for _, r in by_file.iterrows():
        print(f"  {r['source_file']}: {r['n_metrics']} metrics ({r['n_extracted']} extracted)")
    print(f"\nWrote {out_csv}")


if __name__ == "__main__":
    main()
