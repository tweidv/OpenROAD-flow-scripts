#!/usr/bin/env python3
"""Train XGBoost models on PPA prediction dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

from splits import split_trajectories

from build_dataset import build_dataset, load_trajectories
from designs import DESIGNS, DesignSpec
from features import STAGES
from ppa_value import collect_completed_runs, targets_from_batch

ROOT = Path(__file__).resolve().parents[2]
FLOW = ROOT / "flow"
EXP = Path(__file__).resolve().parent

STAGE_ORDER = {s: i for i, s in enumerate(STAGES)}
NORM_COLS = {"norm_p", "norm_t", "norm_a"}
META_COLS = {"trajectory_id", "tier", "final_V", "V_P", "V_T", "V_A", "feasible", "stage"}
TIMING_PROXY_COLS = {"inv_fmax"}


def feature_columns(
    df: pd.DataFrame,
    *,
    include_norm_pta: bool,
    exclude_timing_proxies: bool = False,
) -> list[str]:
    cols = [c for c in df.columns if c not in META_COLS]
    if not include_norm_pta:
        cols = [c for c in cols if c not in NORM_COLS]
    if exclude_timing_proxies:
        cols = [c for c in cols if c not in TIMING_PROXY_COLS]
    return cols


def train_eval(
    df: pd.DataFrame,
    feature_cols: list[str],
    *,
    out_dir: Path,
    label: str,
    stage_filter: str | None = None,
    scale_features: bool = False,
) -> dict[str, float]:
    data = df if stage_filter is None else df[df["stage"] == stage_filter].copy()
    if data.empty:
        return {}

    X = data[feature_cols].copy()
    y = data["final_V"]
    traj_ids = data["trajectory_id"]

    unique_traj = traj_ids.unique()
    if len(unique_traj) < 4:
        return {"error": "too_few_trajectories", "n_traj": len(unique_traj)}

    train_traj, test_traj = split_trajectories(unique_traj)
    train_mask = traj_ids.isin(train_traj)
    test_mask = traj_ids.isin(test_traj)

    X_train, X_test = X[train_mask].copy(), X[test_mask].copy()
    y_train, y_test = y[train_mask], y[test_mask]

    if scale_features:
        scaler = StandardScaler()
        X_train = pd.DataFrame(scaler.fit_transform(X_train), columns=feature_cols, index=X_train.index)
        X_test = pd.DataFrame(scaler.transform(X_test), columns=feature_cols, index=X_test.index)

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

    metrics = {
        "mae": float(mean_absolute_error(y_test, pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_test, pred))),
        "r2": float(r2_score(y_test, pred)),
        "baseline_mae": float(mean_absolute_error(y_test, mean_pred)),
        "n_train_traj": int(len(train_traj)),
        "n_test_traj": int(len(test_traj)),
        "n_train_rows": int(len(y_train)),
        "n_test_rows": int(len(y_test)),
        "y_test_min": float(y_test.min()),
        "y_test_max": float(y_test.max()),
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "_scaled" if scale_features else ""
    scatter = out_dir / f"scatter_{label}{suffix}.png"
    plt.figure(figsize=(5, 5))
    plt.scatter(y_test, pred, alpha=0.8)
    lims = [max(0, y_test.min() - 0.05), min(1, y_test.max() + 0.05)]
    plt.plot(lims, lims, "--", color="gray")
    plt.xlabel("Actual final V")
    plt.ylabel("Predicted final V")
    plt.title(f"{label}{suffix}: MAE={metrics['mae']:.3f}, R2={metrics['r2']:.3f}")
    plt.xlim(lims)
    plt.ylim(lims)
    plt.tight_layout()
    plt.savefig(scatter, dpi=150)
    plt.close()

    return metrics


def run_experiment(
    df: pd.DataFrame,
    *,
    name: str,
    include_norm_pta: bool,
    exclude_timing_proxies: bool = False,
    scale_features: bool = False,
    out_dir: Path,
) -> dict[str, dict[str, float]]:
    feature_cols = feature_columns(
        df,
        include_norm_pta=include_norm_pta,
        exclude_timing_proxies=exclude_timing_proxies,
    )
    result: dict[str, dict[str, float]] = {
        "feature_cols": feature_cols,
        "models": {},
    }
    for stage in [None, *STAGES]:
        label = "combined" if stage is None else stage
        result["models"][label] = train_eval(
            df,
            feature_cols,
            out_dir=out_dir / name,
            label=label,
            stage_filter=stage,
            scale_features=scale_features,
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--design", choices=sorted(DESIGNS), default="gcd")
    args = parser.parse_args()

    spec = DESIGNS[args.design]
    out = EXP / "output" / spec.key
    trajectories = load_trajectories(args.design)
    tids = [t.trajectory_id for t in trajectories]
    runs = collect_completed_runs(
        FLOW, tids, platform=spec.platform, log_name=spec.log_name
    )
    targets = targets_from_batch(runs)

    df = build_dataset(trajectories, spec, targets)
    df["stage_id"] = df["stage"].map(STAGE_ORDER)
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "dataset.csv", index=False)
    (out / "targets.json").write_text(json.dumps(targets, indent=2))

    experiments = {
        "structural_only": {
            "include_norm_pta": False,
            "exclude_timing_proxies": False,
            "scale_features": False,
        },
        "norm_pta": {
            "include_norm_pta": True,
            "exclude_timing_proxies": False,
            "scale_features": False,
        },
    }

    summary = {
        "design": args.design,
        "n_trajectories": len(runs),
        "n_rows": len(df),
        "targets": targets,
        "experiments": {},
    }
    for name, cfg in experiments.items():
        summary["experiments"][name] = run_experiment(df, name=name, out_dir=out, **cfg)

    (out / "metrics.json").write_text(json.dumps(summary, indent=2))

    print(f"=== {args.design}: {len(runs)} trajectories, {len(df)} rows ===")
    for name in experiments:
        print(f"\n--- {name} ---")
        print(json.dumps(summary["experiments"][name]["models"], indent=2))


if __name__ == "__main__":
    main()
