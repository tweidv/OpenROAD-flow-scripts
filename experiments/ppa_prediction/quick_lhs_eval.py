#!/usr/bin/env python3
"""Quick 20-train eval on completed LHS trajectories."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score

from designs import DESIGNS, log_dir
from feature_analysis import (
    STAGE_FEATURES,
    TARGETS,
    load_final_pta,
    make_model,
    train_eval,
)
from features import STAGES
from ppa_value import load_json
from run_trajectories import load_trajectories_from_manifest
from splits import split_trajectories

EXP = Path(__file__).resolve().parent
OUT = EXP / "output" / "gcd" / "lhs250"

# Compact OR checkpoint proxies (same as FFS recommendation).
STAGE_CHECKPOINT_COLS: dict[str, dict[str, str]] = {
    "floorplan": {
        "power": "2_1_floorplan__floorplan__power__internal__total",
        "area": "2_1_floorplan__floorplan__design__instance__area",
        "setup_ws": "2_1_floorplan__floorplan__timing__setup__ws",
        "fmax": "2_1_floorplan__floorplan__timing__fmax",
    },
    "placement": {
        "power": "3_3_place_gp__globalplace__power__internal__total",
        "area": "3_5_place_dp__detailedplace__design__instance__area",
        "setup_ws": "3_5_place_dp__detailedplace__timing__setup__ws",
        "fmax": "3_5_place_dp__detailedplace__timing__fmax",
    },
    "cts": {
        "power": "4_1_cts__cts__power__internal__total",
        "area": "4_1_cts__cts__design__instance__area",
        "setup_ws": "4_1_cts__cts__timing__setup__ws",
        "fmax": "4_1_cts__cts__timing__fmax",
    },
    "routing": {
        "power": "5_1_grt__globalroute__power__internal__total",
        "area": "5_1_grt__globalroute__design__instance__area",
        "setup_ws": "5_1_grt__globalroute__timing__setup__ws",
        "fmax": "5_1_grt__globalroute__timing__fmax",
    },
}

STAGE_JSON = {
    "floorplan": "2_1_floorplan.json",
    "placement": "3_5_place_dp.json",
    "cts": "4_1_cts.json",
    "routing": "5_1_grt.json",
}


def completed_lhs_ids(spec) -> list[str]:
    manifest = load_trajectories_from_manifest(EXP / "generated" / "gcd" / "trajectories_lhs250.json")
    done = []
    for t in manifest:
        if (log_dir(spec, t.trajectory_id) / "6_report.json").exists():
            done.append(t.trajectory_id)
    return sorted(done)


def load_wide_row(spec, tid: str, stage: str) -> dict[str, float]:
    data = load_json(log_dir(spec, tid) / STAGE_JSON[stage])
    row: dict[str, float] = {}
    for key, col in STAGE_CHECKPOINT_COLS[stage].items():
        val = data.get(col.split("__", 1)[-1] if "__" in col else col)
        # col is full wide name; json keys are suffix after first __
        # Actually json keys are like floorplan__power__internal__total
        suffix = col.split("__", 1)[1] if "__" in col else col
        # find matching key in data
        matched = None
        for k, v in data.items():
            if k == suffix or k.endswith(suffix.split("__", 1)[-1]):
                matched = v
                break
        if matched is None:
            # direct: strip file prefix from col
            for k, v in data.items():
                if col.endswith(k) or k in col:
                    matched = v
                    break
        if matched in (None, "N/A", "ERR"):
            row[key] = np.nan
        else:
            row[key] = float(matched)
    return row


def load_wide_row_fixed(spec, tid: str, stage: str) -> dict[str, float]:
    data = load_json(log_dir(spec, tid) / STAGE_JSON[stage])
    row: dict[str, float] = {}
    prefix = STAGE_CHECKPOINT_COLS[stage]
    # map logical names to json metric suffixes per stage file
    suffix_map = {
        "floorplan": {
            "power": "floorplan__power__internal__total",
            "area": "floorplan__design__instance__area",
            "setup_ws": "floorplan__timing__setup__ws",
            "fmax": "floorplan__timing__fmax",
        },
        "placement": {
            "power": "detailedplace__power__internal__total",
            "area": "detailedplace__design__instance__area",
            "setup_ws": "detailedplace__timing__setup__ws",
            "fmax": "detailedplace__timing__fmax",
        },
        "cts": {
            "power": "cts__power__internal__total",
            "area": "cts__design__instance__area",
            "setup_ws": "cts__timing__setup__ws",
            "fmax": "cts__timing__fmax",
        },
        "routing": {
            "power": "globalroute__power__internal__total",
            "area": "globalroute__design__instance__area",
            "setup_ws": "globalroute__timing__setup__ws",
            "fmax": "globalroute__timing__fmax",
        },
    }[stage]
    for k, sk in suffix_map.items():
        val = data.get(sk)
        row[k] = float(val) if val not in (None, "N/A", "ERR") else np.nan
    return row


def load_handpicked_row(spec, tid: str, stage: str, log, params: dict) -> dict[str, float]:
    from features import extract_trajectory_features

    rows = list(extract_trajectory_features(log, params, None))
    for r in rows:
        if r["stage"] == stage:
            feats = STAGE_FEATURES[stage]
            return {f: r.get(f, np.nan) for f in feats}
    return {}


def main() -> None:
    spec = DESIGNS["gcd"]
    tids = completed_lhs_ids(spec)
    manifest = {
        t.trajectory_id: t.params
        for t in load_trajectories_from_manifest(
            EXP / "generated" / "gcd" / "trajectories_lhs250.json"
        )
    }

    pta = load_final_pta(tids, spec)
    train_traj, test_traj = split_trajectories(tids, train_size=20)

    rows_compact = []
    rows_hand = []
    for tid in tids:
        log = log_dir(spec, tid)
        params = manifest[tid]
        base = {"trajectory_id": tid, "CLK_PERIOD": params.get("CLK_PERIOD")}
        base.update(pta[pta.trajectory_id == tid].iloc[0].to_dict())
        for stage in STAGES:
            r = {**base, "stage": stage, **load_wide_row_fixed(spec, tid, stage)}
            rows_compact.append(r)
            hr = load_handpicked_row(spec, tid, stage, log, params)
            rows_hand.append({**base, "stage": stage, **hr})

    df_c = pd.DataFrame(rows_compact)
    df_h = pd.DataFrame(rows_hand)

    OUT.mkdir(parents=True, exist_ok=True)

    results = []
    for featset, df, feats in [
        ("compact3", df_c, ["power", "area", "setup_ws"]),
        ("compact+fmax", df_c, ["power", "area", "setup_ws", "fmax"]),
        ("handpicked", df_h, None),
    ]:
        for stage in STAGES:
            sub = df[df["stage"] == stage].dropna(subset=["final_power", "final_fmax", "final_area"])
            feature_cols = feats or STAGE_FEATURES[stage]
            sub = sub.dropna(subset=feature_cols)
            tr = sub[sub["trajectory_id"].isin(train_traj)]
            te = sub[sub["trajectory_id"].isin(test_traj)]
            for target_key, target_col in TARGETS.items():
                _, m, _ = train_eval(
                    tr[feature_cols].astype(float),
                    tr[target_col].astype(float),
                    te[feature_cols].astype(float),
                    te[target_col].astype(float),
                )
                results.append(
                    {
                        "featureset": featset,
                        "stage": stage,
                        "target": target_key,
                        "test_R2": m["r2"],
                        "test_MAE": m["mae"],
                        "n_train": m["n_train"],
                        "n_test": m["n_test"],
                    }
                )

    res = pd.DataFrame(results)
    res.to_csv(OUT / "quick_eval_results.csv", index=False)

    # structural check
    fin = pta.copy()
    fin["CLK_PERIOD"] = [manifest[t]["CLK_PERIOD"] for t in fin.trajectory_id]
    corr = {
        "CLK_vs_fmax": fin["CLK_PERIOD"].corr(fin["final_fmax"]),
        "CLK_vs_power": fin["CLK_PERIOD"].corr(fin["final_power"]),
        "CLK_vs_area": fin["CLK_PERIOD"].corr(fin["final_area"]),
    }

    lines = [
        "# LHS-250 quick eval (20 train / rest test)",
        "",
        f"**Completed trajectories:** {len(tids)} / 250",
        f"**Split:** {len(train_traj)} train, {len(test_traj)} test (seed 42)",
        "",
        "## Clock still dominates?",
        "",
        "| Param vs final | Pearson r |",
        "|----------------|----------:|",
    ]
    for k, v in corr.items():
        lines.append(f"| {k.replace('_', ' ')} | {v:+.3f} |")

    lines.extend(["", "## Test R² — compact 3 (power, area, setup_ws)", ""])
    lines.append("| Stage | Power | Fmax | Area |")
    lines.append("|-------|------:|-----:|-----:|")
    for stage in STAGES:
        row = res[(res.featureset == "compact3") & (res.stage == stage)]
        p = row[row.target == "power"]["test_R2"].iloc[0]
        f = row[row.target == "fmax"]["test_R2"].iloc[0]
        a = row[row.target == "area"]["test_R2"].iloc[0]
        lines.append(f"| {stage} | {p:.3f} | {f:.3f} | {a:.3f} |")

    lines.extend(["", "## Test R² — compact + checkpoint fmax", ""])
    lines.append("| Stage | Power | Fmax | Area |")
    lines.append("|-------|------:|-----:|-----:|")
    for stage in STAGES:
        row = res[(res.featureset == "compact+fmax") & (res.stage == stage)]
        p = row[row.target == "power"]["test_R2"].iloc[0]
        f = row[row.target == "fmax"]["test_R2"].iloc[0]
        a = row[row.target == "area"]["test_R2"].iloc[0]
        lines.append(f"| {stage} | {p:.3f} | {f:.3f} | {a:.3f} |")

    lines.extend(["", "## Test R² — hand-picked stage features", ""])
    lines.append("| Stage | Power | Fmax | Area |")
    lines.append("|-------|------:|-----:|-----:|")
    for stage in STAGES:
        row = res[(res.featureset == "handpicked") & (res.stage == stage)]
        if row.empty:
            continue
        p = row[row.target == "power"]["test_R2"].iloc[0]
        f = row[row.target == "fmax"]["test_R2"].iloc[0]
        a = row[row.target == "area"]["test_R2"].iloc[0]
        lines.append(f"| {stage} | {p:.3f} | {f:.3f} | {a:.3f} |")

    lines.extend(
        [
            "",
            "## vs old util×clk grid (1000 runs, 20 train)",
            "",
            "Old grid: power R²≈0.95, fmax R²≈0.92, area R²≈0.97 with compact features.",
            "",
            "See `quick_eval_results.csv` for full table.",
        ]
    )

    report = "\n".join(lines) + "\n"
    (OUT / "quick_eval_report.md").write_text(report)
    print(report)


if __name__ == "__main__":
    main()
