#!/usr/bin/env python3
"""Build wide per-stage feature matrices from existing ORFS JSON logs."""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from designs import DESIGNS, log_dir
from inventory_openroad_metrics import STAGE_FILE_MAP, scan_params
from ppa_value import load_json

EXP = Path(__file__).resolve().parent
FLOW = EXP.parents[1] / "flow"

# Canonical checkpoint → JSON log files (no future-stage leakage).
STAGE_SOURCE_FILES: dict[str, list[str]] = {
    "floorplan": [
        "2_1_floorplan.json",
        "2_2_floorplan_macro.json",
        "2_3_floorplan_tapcell.json",
        "2_4_floorplan_pdn.json",
    ],
    "placement": [
        "3_3_place_gp.json",
        "3_4_place_resized.json",
        "3_5_place_dp.json",
    ],
    "cts": ["4_1_cts.json"],
    "routing": [
        "5_1_grt.json",
        "5_2_route.json",
        "5_3_fillcell.json",
    ],
}

PARAM_PREFIX = "param:"


def _feat_name(source_file: str, metric_key: str) -> str:
    stem = source_file.replace(".json", "")
    return f"{stem}__{metric_key}"


def _is_numeric(val) -> bool:
    if val in (None, "N/A", "ERR", ""):
        return False
    try:
        float(val)
        return True
    except (TypeError, ValueError):
        return False


def load_trajectory_params(design: str, limit: int) -> tuple[list[str], pd.DataFrame]:
    manifest = json.loads((EXP / "generated" / design / "trajectories.json").read_text())
    manifest = manifest[:limit]
    rows = []
    for t in manifest:
        row = {"trajectory_id": t["trajectory_id"]}
        for k, v in t["params"].items():
            row[f"{PARAM_PREFIX}{k}"] = v
        rows.append(row)
    params_df = pd.DataFrame(rows)
    return [t["trajectory_id"] for t in manifest], params_df


def load_inventory(design: str) -> pd.DataFrame:
    path = EXP / "output" / design / "feature_analysis" / "openroad_metrics_inventory_full.csv"
    if not path.exists():
        raise FileNotFoundError(f"Run inventory_openroad_metrics.py first: {path}")
    return pd.read_csv(path)


def feature_groups_from_inventory(
    inventory: pd.DataFrame, feature_cols: list[str]
) -> dict[str, list[str]]:
    """Map wide column names to ablation groups."""
    groups: dict[str, list[str]] = {"configuration": []}
    for col in feature_cols:
        if col.startswith(PARAM_PREFIX):
            groups["configuration"].append(col)
            continue
        # col like 2_1_floorplan__floorplan__design__core__area
        if "__" not in col:
            groups.setdefault("other", []).append(col)
            continue
        metric_key = col.split("__", 1)[1]
        cat = metric_key.split("__", 1)[0]
        groups.setdefault(cat, []).append(col)
    return {k: v for k, v in groups.items() if v}


def build_wide_stage_table(
    design: str,
    stage: str,
    trajectory_ids: list[str],
    params_df: pd.DataFrame,
    inventory: pd.DataFrame,
    *,
    min_unique: int = 2,
    max_missing: float = 0.05,
) -> tuple[pd.DataFrame, list[str], dict[str, list[str]]]:
    spec = DESIGNS[design]
    source_files = STAGE_SOURCE_FILES[stage]

    # Eligible metrics from inventory for these files.
    inv_sub = inventory[inventory["source_file"].isin(source_files)].copy()

    rows: list[dict] = []
    for tid in trajectory_ids:
        log = log_dir(spec, tid)
        row: dict = {"trajectory_id": tid, "stage": stage}
        for sf in source_files:
            data = load_json(log / sf)
            for key, val in data.items():
                if _is_numeric(val):
                    row[_feat_name(sf, key)] = float(val)
        rows.append(row)

    wide = pd.DataFrame(rows)
    wide = wide.merge(params_df, on="trajectory_id", how="left")

    meta = set(wide.columns) - {"trajectory_id", "stage"}
    feature_cols = sorted(meta)

    # Drop constant / mostly-missing columns.
    keep = []
    for col in feature_cols:
        miss = wide[col].isna().mean()
        nuniq = wide[col].nunique(dropna=True)
        if miss <= max_missing and nuniq >= min_unique:
            keep.append(col)

    wide = wide[["trajectory_id", "stage", *keep]].copy()
    wide[keep] = wide[keep].astype(float)
    groups = feature_groups_from_inventory(inventory, keep)
    return wide, keep, groups


def build_all_stages(
    design: str = "gcd",
    limit: int = 1000,
    out_dir: Path | None = None,
) -> dict[str, tuple[pd.DataFrame, list[str], dict[str, list[str]]]]:
    out_dir = out_dir or EXP / "output" / design / "feature_analysis" / "wide"
    out_dir.mkdir(parents=True, exist_ok=True)

    tids, params_df = load_trajectory_params(design, limit)
    inventory = load_inventory(design)
    result: dict[str, tuple[pd.DataFrame, list[str], dict[str, list[str]]]] = {}

    for stage in STAGE_SOURCE_FILES:
        wide, cols, groups = build_wide_stage_table(
            design, stage, tids, params_df, inventory
        )
        wide.to_csv(out_dir / f"wide_{stage}.csv", index=False)
        meta = {
            "stage": stage,
            "n_features": len(cols),
            "feature_groups": {k: len(v) for k, v in groups.items()},
            "source_files": STAGE_SOURCE_FILES[stage],
        }
        (out_dir / f"wide_{stage}_meta.json").write_text(json.dumps(meta, indent=2))
        result[stage] = (wide, cols, groups)
        print(f"{stage}: {len(cols)} features → {out_dir / f'wide_{stage}.csv'}")
    return result


if __name__ == "__main__":
    build_all_stages()
