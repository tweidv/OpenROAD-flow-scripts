#!/usr/bin/env python3
"""Train separate models for V_P, V_T, V_A (power, timing, area components)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from splits import split_trajectories
from xgboost import XGBRegressor

from build_dataset import build_dataset, load_trajectories
from designs import DESIGNS
from features import STAGES
from ppa_value import collect_completed_runs, targets_from_batch
from train import feature_columns

FLOW = Path(__file__).resolve().parents[2] / "flow"
EXP = Path(__file__).resolve().parent

TARGETS = ("V_P", "V_T", "V_A")
TARGET_LABELS = {
    "V_P": "Power (V_P)",
    "V_T": "Timing (V_T)",
    "V_A": "Area (V_A)",
}


def train_one_target(
    df: pd.DataFrame,
    feature_cols: list[str],
    y_col: str,
    *,
    stage_filter: str,
) -> dict[str, float]:
    data = df[df["stage"] == stage_filter].copy()
    X = data[feature_cols]
    y = data[y_col]
    traj_ids = data["trajectory_id"]

    train_traj, test_traj = split_trajectories(traj_ids.unique())
    train_mask = traj_ids.isin(train_traj)
    test_mask = traj_ids.isin(test_traj)

    X_train, X_test = X[train_mask], X[test_mask]
    y_train, y_test = y[train_mask], y[test_mask]

    mean_pred = np.full_like(y_test, y_train.mean())
    model = XGBRegressor(
        n_estimators=80,
        max_depth=4,
        learning_rate=0.1,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=42,
        objective="reg:squarederror",
    )
    model.fit(X_train, y_train)
    pred = model.predict(X_test)

    return {
        "mae": float(mean_absolute_error(y_test, pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_test, pred))),
        "r2": float(r2_score(y_test, pred)),
        "baseline_mae": float(mean_absolute_error(y_test, mean_pred)),
        "n_train_traj": int(len(train_traj)),
        "n_test_traj": int(len(test_traj)),
        "n_test_rows": int(len(y_test)),
    }


def run_experiment(
    df: pd.DataFrame,
    *,
    name: str,
    include_norm_pta: bool,
    exclude_timing_proxies: bool = False,
) -> dict:
    feature_cols = feature_columns(
        df,
        include_norm_pta=include_norm_pta,
        exclude_timing_proxies=exclude_timing_proxies,
    )
    result: dict = {"feature_cols": feature_cols, "targets": {}}
    for y_col in TARGETS:
        result["targets"][y_col] = {}
        for stage in STAGES:
            result["targets"][y_col][stage] = train_one_target(
                df, feature_cols, y_col, stage_filter=stage
            )
    return result


def plot_scatter_grid(df: pd.DataFrame, out_dir: Path, experiment: dict, exp_name: str, design: str) -> None:
    """3×4 grid: rows=V_P/V_T/V_A, cols=floorplan/placement/cts/routing."""
    feature_cols = experiment["feature_cols"]
    fig, axes = plt.subplots(3, 4, figsize=(14, 10), sharex="col", sharey="row")

    for row, y_col in enumerate(TARGETS):
        for col, stage in enumerate(STAGES):
            ax = axes[row, col]
            data = df[df["stage"] == stage]
            traj_ids = data["trajectory_id"]
            train_traj, test_traj = split_trajectories(traj_ids.unique())
            test = data[traj_ids.isin(test_traj)]
            train = data[traj_ids.isin(train_traj)]

            model = XGBRegressor(
                n_estimators=80, max_depth=4, learning_rate=0.1,
                subsample=0.9, colsample_bytree=0.9, random_state=42,
            )
            model.fit(train[feature_cols], train[y_col])
            pred = model.predict(test[feature_cols])
            r2 = r2_score(test[y_col], pred)

            ax.scatter(test[y_col], pred, alpha=0.7, s=25)
            ax.plot([0, 1], [0, 1], "--", color="gray", linewidth=0.8)
            ax.set_xlim(0, 1.05)
            ax.set_ylim(0, 1.05)
            if row == 0:
                ax.set_title(stage)
            if col == 0:
                ax.set_ylabel(TARGET_LABELS[y_col])
            ax.text(0.05, 0.92, f"R²={r2:.2f}", transform=ax.transAxes, fontsize=8)

    fig.suptitle(f"{design} {exp_name}: predict final V_P/V_T/V_A from checkpoint features", fontsize=12)
    fig.tight_layout()
    fig.savefig(out_dir / f"scatter_pta_{exp_name}.png", dpi=150)
    plt.close(fig)


def print_summary(summary: dict) -> None:
    for exp_name, exp in summary["experiments"].items():
        print(f"\n=== {exp_name} (per-stage only) ===")
        header = f"{'Stage':12s}  {'V_P R²':>8s}  {'V_T R²':>8s}  {'V_A R²':>8s}"
        print(header)
        for stage in STAGES:
            cols = [exp["targets"][t][stage]["r2"] for t in TARGETS]
            print(f"{stage:12s}  {cols[0]:8.3f}  {cols[1]:8.3f}  {cols[2]:8.3f}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--design", choices=sorted(DESIGNS), default="gcd")
    args = parser.parse_args()

    spec = DESIGNS[args.design]
    out_dir = EXP / "output" / spec.key / "pta_separate"
    trajectories = load_trajectories(args.design)
    tids = [t.trajectory_id for t in trajectories]
    runs = collect_completed_runs(
        FLOW, tids, platform=spec.platform, log_name=spec.log_name
    )
    targets = targets_from_batch(runs)
    df = build_dataset(trajectories, spec, targets)
    df["stage_id"] = df["stage"].map({s: i for i, s in enumerate(STAGES)})

    experiments = {
        "structural_only": {"include_norm_pta": False, "exclude_timing_proxies": False},
        "norm_pta": {"include_norm_pta": True, "exclude_timing_proxies": False},
    }

    summary = {"design": args.design, "n_trajectories": len(runs), "batch_targets": targets, "experiments": {}}
    out_dir.mkdir(parents=True, exist_ok=True)

    for name, cfg in experiments.items():
        summary["experiments"][name] = run_experiment(df, name=name, **cfg)
        plot_scatter_grid(df, out_dir, summary["experiments"][name], name, args.design)

    (out_dir / "metrics_pta_separate.json").write_text(json.dumps(summary, indent=2))
    print_summary(summary)
    print(f"\nWrote {out_dir}/metrics_pta_separate.json")
    print(f"Wrote {out_dir}/scatter_pta_*.png")


if __name__ == "__main__":
    main()
