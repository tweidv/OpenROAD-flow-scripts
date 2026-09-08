#!/usr/bin/env python3
"""Plot R² learning curves vs number of training trajectories."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import r2_score
from splits import DEFAULT_RANDOM_STATE, split_trajectories
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


def _fit_predict_r2(
    df: pd.DataFrame,
    feature_cols: list[str],
    train_traj: np.ndarray,
    test_traj: np.ndarray,
    y_col: str,
    stage_filter: str,
) -> float:
    train = df[(df["stage"] == stage_filter) & (df["trajectory_id"].isin(train_traj))]
    test = df[(df["stage"] == stage_filter) & (df["trajectory_id"].isin(test_traj))]
    if len(train) < 3 or len(test) < 1:
        return float("nan")

    model = XGBRegressor(
        n_estimators=80,
        max_depth=4,
        learning_rate=0.1,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=42,
        objective="reg:squarederror",
    )
    model.fit(train[feature_cols], train[y_col])
    pred = model.predict(test[feature_cols])
    return float(r2_score(test[y_col], pred))


def learning_curve_points(
    df: pd.DataFrame,
    *,
    y_col: str,
    include_norm_pta: bool,
    exclude_timing_proxies: bool = False,
    stage_filter: str,
    test_size: float = 0.25,
    min_train: int = 4,
    n_points: int = 10,
) -> list[dict[str, float]]:
    feature_cols = feature_columns(
        df,
        include_norm_pta=include_norm_pta,
        exclude_timing_proxies=exclude_timing_proxies,
    )
    all_traj = np.array(sorted(df["trajectory_id"].unique()))
    if len(all_traj) < min_train + 2:
        return []

    train_pool, test_traj = split_trajectories(all_traj)
    train_pool = np.array(train_pool)
    test_traj = np.array(test_traj)

    max_n = len(train_pool)
    counts = sorted({min_train, *np.linspace(min_train, max_n, n_points, dtype=int)})
    counts = [c for c in counts if c <= max_n]

    points = []
    for n in counts:
        subset = train_pool[:n]
        r2 = _fit_predict_r2(df, feature_cols, subset, test_traj, y_col, stage_filter)
        points.append({"n_train_trajectories": int(n), "r2": r2})
    return points


def plot_pta_learning_grid(
    df: pd.DataFrame,
    out_dir: Path,
    *,
    design: str,
    exp_name: str,
    include_norm_pta: bool,
    exclude_timing_proxies: bool = False,
    n_test: int,
) -> dict:
    """3×4 grid: rows V_P/V_T/V_A, cols floorplan/placement/cts/routing."""
    results: dict = {}
    fig, axes = plt.subplots(3, 4, figsize=(14, 10), sharex=True, sharey=True)

    for row, y_col in enumerate(TARGETS):
        results[y_col] = {}
        for col, stage in enumerate(STAGES):
            ax = axes[row, col]
            pts = learning_curve_points(
                df,
                y_col=y_col,
                include_norm_pta=include_norm_pta,
                exclude_timing_proxies=exclude_timing_proxies,
                stage_filter=stage,
                min_train=max(3, min(4, len(df["trajectory_id"].unique()) // 4)),
            )
            results[y_col][stage] = pts
            if pts:
                xs = [p["n_train_trajectories"] for p in pts]
                ys = [p["r2"] for p in pts]
                ax.plot(xs, ys, marker="o", color="#2563eb", linewidth=2, markersize=4)
            ax.axhline(0, color="gray", linestyle="--", linewidth=0.6, alpha=0.6)
            ax.axhline(0.7, color="gray", linestyle=":", linewidth=0.5, alpha=0.4)
            ax.set_ylim(-0.5, 1.05)
            ax.grid(True, alpha=0.3)
            if row == 0:
                ax.set_title(stage)
            if col == 0:
                ax.set_ylabel(TARGET_LABELS[y_col])
            if row == 2:
                ax.set_xlabel("Training trajectories")

    fig.suptitle(
        f"{design} {exp_name}: per-stage test R² vs training trajectories "
        f"(fixed {n_test}-trajectory test set)",
        fontsize=11,
    )
    fig.tight_layout()
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"learning_curve_r2_pta_{exp_name}.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return results


def print_milestones(curves: dict, exp_name: str) -> None:
    print(f"\n=== {exp_name} milestones (R² ≥ 0.7) ===")
    for y_col in TARGETS:
        for stage in STAGES:
            pts = curves.get(y_col, {}).get(stage, [])
            hit = next((p for p in pts if p["r2"] >= 0.7), None)
            if hit:
                print(f"  {y_col:3s} @ {stage:10s}: n={hit['n_train_trajectories']:2d}  R²={hit['r2']:.3f}")
            else:
                last = pts[-1]["r2"] if pts else float("nan")
                print(f"  {y_col:3s} @ {stage:10s}: never (max R²={last:.3f})")


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
    if len(runs) < 8:
        raise SystemExit(f"Need at least 8 completed runs; have {len(runs)}")

    targets = targets_from_batch(runs)
    df = build_dataset(trajectories, spec, targets)
    df["stage_id"] = df["stage"].map({s: i for i, s in enumerate(STAGES)})
    train_list, test_list = split_trajectories(sorted(df["trajectory_id"].unique()))
    n_test = max(1, int(round(len(test_list))))

    pta_curves: dict = {}
    for exp_name, include_norm, exclude_timing in [
        ("structural_only", False, False),
        ("norm_pta", True, False),
    ]:
        pta_curves[exp_name] = plot_pta_learning_grid(
            df,
            out_dir,
            design=args.design,
            exp_name=exp_name,
            include_norm_pta=include_norm,
            exclude_timing_proxies=exclude_timing,
            n_test=n_test,
        )
        print_milestones(pta_curves[exp_name], exp_name)

    (out_dir / "learning_curve_r2_pta.json").write_text(json.dumps(pta_curves, indent=2))

    print(f"\nWrote {out_dir}/learning_curve_r2_pta_structural_only.png")
    print(f"Wrote {out_dir}/learning_curve_r2_pta_norm_pta.png")
    print(f"Wrote {out_dir}/learning_curve_r2_pta.json")


if __name__ == "__main__":
    main()
