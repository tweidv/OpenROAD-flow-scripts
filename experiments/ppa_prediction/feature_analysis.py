#!/usr/bin/env python3
"""Offline feature importance analysis: SHAP + ablation per flow stage."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from scipy.stats import spearmanr
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

from designs import DESIGNS, log_dir
from features import STAGES
from ppa_value import load_json
from splits import DEFAULT_TRAIN_SIZE, split_trajectories

EXP = Path(__file__).resolve().parent
FLOW = EXP.parents[1] / "flow"

META_COLS = {
    "trajectory_id",
    "tier",
    "stage",
    "final_V",
    "V_P",
    "V_T",
    "V_A",
    "feasible",
    "norm_p",
    "norm_t",
    "norm_a",
    "final_power",
    "final_fmax",
    "final_area",
}

# Existing extracted features only — no norm_p/t/a, no future-stage leakage.
STAGE_FEATURES: dict[str, list[str]] = {
    "floorplan": ["core_area", "utilization", "aspect_ratio"],
    "placement": ["hpwl", "placement_density", "estimated_congestion", "inv_fmax"],
    "cts": ["inv_fmax", "total_negative_slack", "clock_skew", "buffer_inverter_count"],
    "routing": [
        "routed_wirelength",
        "inv_fmax",
        "total_negative_slack",
        "congestion",
        "drc_violation_count",
    ],
}

FEATURE_META: dict[str, dict[str, str]] = {
    "core_area": {
        "group": "floorplan",
        "description": "floorplan__design__core__area",
    },
    "utilization": {
        "group": "floorplan",
        "description": "floorplan__design__instance__utilization",
    },
    "aspect_ratio": {
        "group": "floorplan",
        "description": "CORE_ASPECT_RATIO param (+ die/core area proxy)",
    },
    "hpwl": {
        "group": "placement",
        "description": "detailedplace__route__wirelength__estimated",
    },
    "placement_density": {
        "group": "placement",
        "description": "detailedplace__design__instance__utilization",
    },
    "estimated_congestion": {
        "group": "congestion",
        "description": "globalplace__gpl__routability__congestion (GP aux)",
    },
    "inv_fmax": {
        "group": "timing",
        "description": "1/fmax at stage checkpoint (seconds)",
    },
    "total_negative_slack": {
        "group": "timing",
        "description": "setup TNS at stage checkpoint",
    },
    "clock_skew": {"group": "cts", "description": "cts__clock__skew__setup"},
    "buffer_inverter_count": {
        "group": "cts",
        "description": "setup + hold buffer/inverter count after CTS",
    },
    "routed_wirelength": {
        "group": "routing",
        "description": "detailedroute__route__wirelength",
    },
    "congestion": {
        "group": "congestion",
        "description": "GPL routability congestion (GP aux at route)",
    },
    "drc_violation_count": {
        "group": "routing",
        "description": "detailedroute__route__drc_errors",
    },
}

TARGETS = {
    "power": "final_power",
    "fmax": "final_fmax",
    "area": "final_area",
}

MODEL_PARAMS = {
    "n_estimators": 80,
    "max_depth": 4,
    "learning_rate": 0.1,
    "subsample": 0.9,
    "colsample_bytree": 0.9,
    "random_state": 42,
    "objective": "reg:squarederror",
}


def make_model() -> XGBRegressor:
    return XGBRegressor(**MODEL_PARAMS)


def load_final_pta(trajectory_ids: list[str], spec) -> pd.DataFrame:
    rows = []
    for tid in trajectory_ids:
        finish = load_json(log_dir(spec, tid) / "6_report.json")
        p = finish.get("finish__power__total")
        fmax = finish.get("finish__timing__fmax")
        area = finish.get(
            "finish__design__instance__area__stdcell",
            finish.get("finish__design__instance__area"),
        )
        if p in (None, "N/A") or fmax in (None, "N/A") or area in (None, "N/A"):
            continue
        rows.append(
            {
                "trajectory_id": tid,
                "final_power": float(p),
                "final_fmax": float(fmax),
                "final_area": float(area),
            }
        )
    return pd.DataFrame(rows)


def load_dataset(
    design: str = "gcd",
    limit: int = 1000,
    train_size: int = DEFAULT_TRAIN_SIZE,
) -> tuple[pd.DataFrame, dict[str, Any], list[str], list[str]]:
    spec = DESIGNS[design]
    df = pd.read_csv(EXP / "output" / spec.key / "dataset.csv")
    traj_order = sorted(df["trajectory_id"].unique())[:limit]
    df = df[df["trajectory_id"].isin(traj_order)].copy()

    pta = load_final_pta(traj_order, spec)
    df = df.merge(pta, on="trajectory_id", how="inner")

    train_traj, test_traj = split_trajectories(sorted(df["trajectory_id"].unique()), train_size=train_size)
    meta = {
        "design": design,
        "limit": limit,
        "train_size": train_size,
        "n_train": len(train_traj),
        "n_test": len(test_traj),
        "model_params": MODEL_PARAMS,
    }
    return df, meta, train_traj, test_traj


def stage_frame(df: pd.DataFrame, stage: str) -> pd.DataFrame:
    feats = STAGE_FEATURES[stage]
    sub = df[df["stage"] == stage].copy()
    return sub.dropna(subset=feats)


def build_inventory(df: pd.DataFrame, out_path: Path) -> pd.DataFrame:
    rows = []
    for feat, meta in FEATURE_META.items():
        stages_avail = [s for s in STAGES if feat in STAGE_FEATURES[s]]
        for stage in stages_avail:
            col = df.loc[df["stage"] == stage, feat]
            rows.append(
                {
                    "feature": feat,
                    "stage_available": stage,
                    "feature_group": meta["group"],
                    "dtype": "float",
                    "missing_fraction": float(col.isna().mean()),
                    "n_unique": int(col.nunique(dropna=True)),
                    "description": meta["description"],
                }
            )
    inv = pd.DataFrame(rows).sort_values(["feature", "stage_available"])
    inv.to_csv(out_path, index=False)
    return inv


def train_eval(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> tuple[XGBRegressor, dict[str, float], np.ndarray]:
    model = make_model()
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    metrics = {
        "mae": float(mean_absolute_error(y_test, pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_test, pred))),
        "r2": float(r2_score(y_test, pred)),
        "n_train": int(len(y_train)),
        "n_test": int(len(y_test)),
    }
    return model, metrics, pred


def groups_for_stage(stage: str) -> dict[str, list[str]]:
    feats = STAGE_FEATURES[stage]
    groups: dict[str, list[str]] = {}
    for f in feats:
        g = FEATURE_META[f]["group"]
        groups.setdefault(g, []).append(f)
    return groups


def run_shap_for_stage_target_generic(
    df: pd.DataFrame,
    feature_cols: list[str],
    stage: str,
    target_key: str,
    train_traj: list[str],
    test_traj: list[str],
    out_dir: Path,
) -> pd.DataFrame:
    target_col = TARGETS[target_key]
    train = df[df["trajectory_id"].isin(train_traj)]
    test = df[df["trajectory_id"].isin(test_traj)]

    X_train = train[feature_cols].astype(float)
    y_train = train[target_col]
    X_test = test[feature_cols].astype(float)
    y_test = test[target_col]

    model, metrics, _ = train_eval(X_train, y_train, X_test, y_test)

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)

    mean_abs = np.abs(shap_values).mean(axis=0)
    mean_signed = shap_values.mean(axis=0)
    out = pd.DataFrame(
        {
            "feature": feature_cols,
            "mean_abs_shap": mean_abs,
            "mean_shap": mean_signed,
        }
    )
    out["rank"] = out["mean_abs_shap"].rank(ascending=False, method="first").astype(int)
    out = out.sort_values("rank")
    out["target"] = target_key
    out["stage"] = stage
    for k, v in metrics.items():
        out[k] = v

    csv_path = out_dir / f"shap_{stage}_{target_key}.csv"
    out[["feature", "mean_abs_shap", "mean_shap", "rank"]].to_csv(csv_path, index=False)

    plot_dir = out_dir / "plots"
    plot_dir.mkdir(parents=True, exist_ok=True)
    top_n = min(20, len(out))
    top = out.head(top_n)
    fig, ax = plt.subplots(figsize=(10, max(4, top_n * 0.35)))
    ax.barh(top["feature"][::-1], top["mean_abs_shap"][::-1], color="#2563eb")
    ax.set_xlabel("Mean |SHAP|")
    ax.set_title(f"{stage} → final_{target_key}  (test R²={metrics['r2']:.3f}, {len(feature_cols)} feats)")
    fig.tight_layout()
    fig.savefig(plot_dir / f"shap_{stage}_{target_key}.png", dpi=150)
    plt.close(fig)
    return out


def run_shap_for_stage_target(
    df: pd.DataFrame,
    stage: str,
    target_key: str,
    train_traj: list[str],
    test_traj: list[str],
    out_dir: Path,
) -> pd.DataFrame:
    target_col = TARGETS[target_key]
    feats = STAGE_FEATURES[stage]
    data = stage_frame(df, stage)
    train = data[data["trajectory_id"].isin(train_traj)]
    test = data[data["trajectory_id"].isin(test_traj)]

    X_train = train[feats].astype(float)
    y_train = train[target_col]
    X_test = test[feats].astype(float)
    y_test = test[target_col]

    model, metrics, _ = train_eval(X_train, y_train, X_test, y_test)

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)

    mean_abs = np.abs(shap_values).mean(axis=0)
    mean_signed = shap_values.mean(axis=0)
    out = pd.DataFrame(
        {
            "feature": feats,
            "mean_abs_shap": mean_abs,
            "mean_shap": mean_signed,
        }
    )
    out["rank"] = out["mean_abs_shap"].rank(ascending=False, method="first").astype(int)
    out = out.sort_values("rank")
    out["target"] = target_key
    out["stage"] = stage
    for k, v in metrics.items():
        out[k] = v

    csv_path = out_dir / f"shap_{stage}_{target_key}.csv"
    out[["feature", "mean_abs_shap", "mean_shap", "rank"]].to_csv(csv_path, index=False)

    plot_dir = out_dir / "plots"
    plot_dir.mkdir(parents=True, exist_ok=True)
    top_n = min(20, len(out))
    top = out.head(top_n)
    fig, ax = plt.subplots(figsize=(8, max(4, top_n * 0.3)))
    ax.barh(top["feature"][::-1], top["mean_abs_shap"][::-1], color="#2563eb")
    ax.set_xlabel("Mean |SHAP|")
    ax.set_title(f"{stage} → final_{target_key}  (test R²={metrics['r2']:.3f})")
    fig.tight_layout()
    fig.savefig(plot_dir / f"shap_{stage}_{target_key}.png", dpi=150)
    plt.close(fig)

    return out


def run_group_ablation_generic(
    df: pd.DataFrame,
    feature_cols: list[str],
    groups: dict[str, list[str]],
    stage: str,
    train_traj: list[str],
    test_traj: list[str],
) -> pd.DataFrame:
    train = df[df["trajectory_id"].isin(train_traj)]
    test = df[df["trajectory_id"].isin(test_traj)]
    rows = []
    for target_key, target_col in TARGETS.items():
        y_train = train[target_col]
        y_test = test[target_col]
        X_train_full = train[feature_cols].astype(float)
        X_test_full = test[feature_cols].astype(float)
        _, full_metrics, _ = train_eval(X_train_full, y_train, X_test_full, y_test)
        rows.append(
            {
                "stage": stage,
                "target": target_key,
                "ablation": "all",
                "removed_group": "",
                "n_features": len(feature_cols),
                **full_metrics,
                "delta_r2": 0.0,
            }
        )
        for group_name, group_feats in sorted(groups.items()):
            keep = [f for f in feature_cols if f not in group_feats]
            if not keep or len(keep) == len(feature_cols):
                continue
            _, metrics, _ = train_eval(
                train[keep].astype(float), y_train, test[keep].astype(float), y_test
            )
            rows.append(
                {
                    "stage": stage,
                    "target": target_key,
                    "ablation": f"-{group_name}",
                    "removed_group": group_name,
                    "n_features": len(keep),
                    **metrics,
                    "delta_r2": full_metrics["r2"] - metrics["r2"],
                }
            )
    return pd.DataFrame(rows)


def run_individual_ablation_generic(
    df: pd.DataFrame,
    feature_cols: list[str],
    stage: str,
    train_traj: list[str],
    test_traj: list[str],
) -> pd.DataFrame:
    train = df[df["trajectory_id"].isin(train_traj)]
    test = df[df["trajectory_id"].isin(test_traj)]
    rows = []
    for target_key, target_col in TARGETS.items():
        y_train = train[target_col]
        y_test = test[target_col]
        X_train_full = train[feature_cols].astype(float)
        X_test_full = test[feature_cols].astype(float)
        _, full_metrics, _ = train_eval(X_train_full, y_train, X_test_full, y_test)
        for drop in feature_cols:
            keep = [f for f in feature_cols if f != drop]
            _, metrics, _ = train_eval(
                train[keep].astype(float), y_train, test[keep].astype(float), y_test
            )
            rows.append(
                {
                    "stage": stage,
                    "target": target_key,
                    "dropped_feature": drop,
                    **metrics,
                    "delta_r2": full_metrics["r2"] - metrics["r2"],
                    "full_r2": full_metrics["r2"],
                }
            )
    out = pd.DataFrame(rows)
    out["ablation_rank"] = (
        out.groupby(["stage", "target"])["delta_r2"]
        .rank(ascending=False, method="first")
        .astype(int)
    )
    return out.sort_values(["stage", "target", "ablation_rank"])


def run_group_ablation(
    df: pd.DataFrame,
    stage: str,
    train_traj: list[str],
    test_traj: list[str],
) -> pd.DataFrame:
    feats = STAGE_FEATURES[stage]
    groups = groups_for_stage(stage)
    data = stage_frame(df, stage)
    train = data[data["trajectory_id"].isin(train_traj)]
    test = data[data["trajectory_id"].isin(test_traj)]

    rows = []
    for target_key, target_col in TARGETS.items():
        y_train = train[target_col]
        y_test = test[target_col]
        X_train_full = train[feats].astype(float)
        X_test_full = test[feats].astype(float)
        _, full_metrics, _ = train_eval(X_train_full, y_train, X_test_full, y_test)
        rows.append(
            {
                "stage": stage,
                "target": target_key,
                "ablation": "all",
                "removed_group": "",
                "features_used": ",".join(feats),
                "n_features": len(feats),
                **full_metrics,
                "delta_r2": 0.0,
            }
        )
        for group_name, group_feats in sorted(groups.items()):
            keep = [f for f in feats if f not in group_feats]
            if not keep:
                continue
            X_train = train[keep].astype(float)
            X_test = test[keep].astype(float)
            _, metrics, _ = train_eval(X_train, y_train, X_test, y_test)
            rows.append(
                {
                    "stage": stage,
                    "target": target_key,
                    "ablation": f"-{group_name}",
                    "removed_group": group_name,
                    "features_used": ",".join(keep),
                    "n_features": len(keep),
                    **metrics,
                    "delta_r2": full_metrics["r2"] - metrics["r2"],
                }
            )
    return pd.DataFrame(rows)


def run_individual_ablation(
    df: pd.DataFrame,
    stage: str,
    train_traj: list[str],
    test_traj: list[str],
) -> pd.DataFrame:
    feats = STAGE_FEATURES[stage]
    data = stage_frame(df, stage)
    train = data[data["trajectory_id"].isin(train_traj)]
    test = data[data["trajectory_id"].isin(test_traj)]

    rows = []
    for target_key, target_col in TARGETS.items():
        y_train = train[target_col]
        y_test = test[target_col]
        X_train_full = train[feats].astype(float)
        X_test_full = test[feats].astype(float)
        _, full_metrics, _ = train_eval(X_train_full, y_train, X_test_full, y_test)

        for drop in feats:
            keep = [f for f in feats if f != drop]
            X_train = train[keep].astype(float)
            X_test = test[keep].astype(float)
            _, metrics, _ = train_eval(X_train, y_train, X_test, y_test)
            rows.append(
                {
                    "stage": stage,
                    "target": target_key,
                    "dropped_feature": drop,
                    "feature_group": FEATURE_META[drop]["group"],
                    **metrics,
                    "delta_r2": full_metrics["r2"] - metrics["r2"],
                    "full_r2": full_metrics["r2"],
                }
            )
    out = pd.DataFrame(rows)
    out["ablation_rank"] = (
        out.groupby(["stage", "target"])["delta_r2"]
        .rank(ascending=False, method="first")
        .astype(int)
    )
    return out.sort_values(["stage", "target", "ablation_rank"])


def compare_shap_ablation(
    shap_frames: list[pd.DataFrame],
    indiv_frames: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    shap_all = pd.concat(shap_frames, ignore_index=True)
    rows = []
    for stage in STAGES:
        for target_key in TARGETS:
            sh = shap_all[(shap_all["stage"] == stage) & (shap_all["target"] == target_key)].copy()
            ab = indiv_frames[stage]
            ab = ab[ab["target"] == target_key].copy()
            merged = sh.merge(
                ab[["dropped_feature", "delta_r2", "ablation_rank"]],
                left_on="feature",
                right_on="dropped_feature",
                how="inner",
            )
            rho = float("nan")
            if len(merged) >= 2:
                rho = float(spearmanr(merged["rank"], merged["ablation_rank"]).statistic)
            for _, r in merged.iterrows():
                rows.append(
                    {
                        "stage": stage,
                        "target": target_key,
                        "feature": r["feature"],
                        "shap_rank": int(r["rank"]),
                        "mean_abs_shap": float(r["mean_abs_shap"]),
                        "ablation_delta_r2": float(r["delta_r2"]),
                        "ablation_rank": int(r["ablation_rank"]),
                    }
                )
            rows.append(
                {
                    "stage": stage,
                    "target": target_key,
                    "feature": "__spearman_rho__",
                    "shap_rank": np.nan,
                    "mean_abs_shap": np.nan,
                    "ablation_delta_r2": rho,
                    "ablation_rank": np.nan,
                }
            )
    return pd.DataFrame(rows)


def write_summary(
    out_path: Path,
    meta: dict[str, Any],
    inventory: pd.DataFrame,
    shap_frames: list[pd.DataFrame],
    group_frames: dict[str, pd.DataFrame],
    indiv_frames: dict[str, pd.DataFrame],
    compare: pd.DataFrame,
) -> None:
    lines = [
        "# GCD Feature Analysis Summary",
        "",
        f"Design: {meta['design']}  |  Trajectories: {meta['limit']}  |  "
        f"Split: {meta['train_size']} train / {meta['n_test']} test",
        "",
        "Primary targets: `final_power`, `final_fmax`, `final_area` (from finish metrics).",
        "Inputs: structural checkpoint features only (no norm_p/t/a).",
        "",
        f"Model: XGBoost {meta['model_params']}",
        "",
        "## Feature inventory",
        "",
        f"See `feature_inventory.csv` ({len(inventory)} feature×stage rows).",
        "",
        "### Features per stage",
        "",
    ]
    for stage in STAGES:
        lines.append(f"**{stage}:** {', '.join(STAGE_FEATURES[stage])}")
        groups = groups_for_stage(stage)
        lines.append(f"  - groups: {', '.join(f'{k}({len(v)})' for k, v in groups.items())}")
        lines.append("")

    lines += ["## Full-model test R² (by stage × target)", ""]
    lines.append("| Stage | Power | Fmax | Area |")
    lines.append("|-------|------:|-----:|-----:|")
    shap_all = pd.concat(shap_frames, ignore_index=True)
    for stage in STAGES:
        r2s = []
        for tk in TARGETS:
            sub = shap_all[(shap_all.stage == stage) & (shap_all.target == tk)]
            r2s.append(f"{sub['r2'].iloc[0]:.3f}" if len(sub) else "—")
        lines.append(f"| {stage} | " + " | ".join(r2s) + " |")

    for stage in STAGES:
        lines += [f"", f"## {stage.upper()}", ""]
        for tk, label in [("power", "Power"), ("fmax", "Fmax"), ("area", "Area")]:
            sh = shap_all[(shap_all.stage == stage) & (shap_all.target == tk)].head(10)
            ab = indiv_frames[stage][indiv_frames[stage].target == tk].head(10)
            lines += [f"### {label}", "", "Top 10 SHAP:", ""]
            for _, r in sh.iterrows():
                lines.append(f"- `{r['feature']}` |SHAP|={r['mean_abs_shap']:.4g}")
            lines += ["", "Top 10 ablation (ΔR² when removed):", ""]
            for _, r in ab.iterrows():
                lines.append(f"- `{r['dropped_feature']}` ΔR²={r['delta_r2']:.4f}")
            lines.append("")

        gb = group_frames[stage]
        lines += ["Largest group ablations (mean ΔR² across targets):", ""]
        gmean = gb[gb.ablation != "all"].groupby("removed_group")["delta_r2"].mean().sort_values(ascending=False)
        for g, v in gmean.items():
            lines.append(f"- `-{g}`: ΔR²={v:.4f}")
        lines.append("")

        rho_row = compare[
            (compare.stage == stage) & (compare.feature == "__spearman_rho__")
        ]
        if len(rho_row):
            lines.append("SHAP vs ablation Spearman ρ by target:")
            for _, r in rho_row.iterrows():
                lines.append(f"- {r['target']}: ρ={r['ablation_delta_r2']:.3f}")
            lines.append("")

    out_path.write_text("\n".join(lines))


def write_summary_full(
    out_path: Path,
    meta: dict,
    shap_frames: list[pd.DataFrame],
    group_frames: dict[str, pd.DataFrame],
    indiv_frames: dict[str, pd.DataFrame],
    compare: pd.DataFrame,
    stage_features: dict[str, list[str]],
) -> None:
    shap_all = pd.concat(shap_frames, ignore_index=True)
    lines = [
        "# Full ORFS Metrics — Feature Analysis",
        "",
        f"**Mode:** all JSON metrics from existing logs (no new OpenROAD runs)",
        f"**Trajectories:** {meta['limit']}  |  **Split:** {meta['train_size']} train / {meta['n_test']} test",
        "",
        "## Features per stage",
        "",
    ]
    for s in STAGES:
        lines.append(f"- **{s}:** {len(stage_features[s])} features")
    lines += ["", "## Full-model test R²", "", "| Stage | Power | Fmax | Area |", "|-------|------:|-----:|-----:|"]
    for stage in STAGES:
        r2s = []
        for tk in TARGETS:
            sub = shap_all[(shap_all.stage == stage) & (shap_all.target == tk)]
            r2s.append(f"{sub['r2'].iloc[0]:.3f}" if len(sub) else "—")
        lines.append(f"| {stage} | " + " | ".join(r2s) + " |")

    for stage in STAGES:
        lines += [f"", f"## {stage.upper()}", ""]
        for tk in TARGETS:
            sh = shap_all[(shap_all.stage == stage) & (shap_all.target == tk)].head(15)
            lines += [f"### Top 15 SHAP → {tk}", ""]
            for _, r in sh.iterrows():
                fname = r["feature"]
                if len(fname) > 80:
                    fname = "…" + fname[-77:]
                lines.append(f"- `{fname}` |SHAP|={r['mean_abs_shap']:.4g}")
            lines.append("")
        if stage in indiv_frames:
            for tk in TARGETS:
                ab = indiv_frames[stage][indiv_frames[stage].target == tk].head(10)
                lines += [f"### Top 10 ablation → {tk}", ""]
                for _, r in ab.iterrows():
                    fname = r["dropped_feature"]
                    if len(fname) > 80:
                        fname = "…" + fname[-77:]
                    lines.append(f"- `{fname}` ΔR²={r['delta_r2']:.4f}")
                lines.append("")
        gb = group_frames[stage]
        gmean = gb[gb.ablation != "all"].groupby("removed_group")["delta_r2"].mean().sort_values(ascending=False)
        lines += ["### Group ablations (mean ΔR²)", ""]
        for g, v in gmean.head(10).items():
            lines.append(f"- `-{g}`: {v:.4f}")
        lines.append("")

    out_path.write_text("\n".join(lines))


def count_planned_models() -> dict[str, int]:
    shap = len(STAGES) * len(TARGETS)
    group = sum((len(groups_for_stage(s)) + 1) * len(TARGETS) for s in STAGES)
    indiv = sum(len(STAGE_FEATURES[s]) * len(TARGETS) for s in STAGES)
    return {"shap": shap, "group_ablation": group, "individual_ablation": indiv, "total_fits": shap + group + indiv}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--design", default="gcd")
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--train-size", type=int, default=DEFAULT_TRAIN_SIZE)
    args = parser.parse_args()

    out_root = EXP / "output" / args.design / "feature_analysis"
    shap_dir = out_root / "shap"
    ablation_dir = out_root / "ablation"
    indiv_dir = out_root / "individual"
    for d in (out_root, shap_dir, ablation_dir, indiv_dir):
        d.mkdir(parents=True, exist_ok=True)

    counts = count_planned_models()
    print("=== Feature analysis scope ===")
    print(json.dumps({"stage_features": STAGE_FEATURES, "model_counts": counts}, indent=2))

    df, meta, train_traj, test_traj = load_dataset(args.design, args.limit, args.train_size)
    meta["model_counts"] = counts
    (out_root / "run_metadata.json").write_text(json.dumps(meta, indent=2, default=str))

    inventory = build_inventory(df, out_root / "feature_inventory.csv")
    print(f"\nWrote {out_root / 'feature_inventory.csv'} ({len(inventory)} rows)")

    shap_frames: list[pd.DataFrame] = []
    for stage in STAGES:
        print(f"\n[{stage}] features: {STAGE_FEATURES[stage]}")
        for target_key in TARGETS:
            print(f"  SHAP → {target_key}...", flush=True)
            shap_frames.append(
                run_shap_for_stage_target(df, stage, target_key, train_traj, test_traj, shap_dir)
            )

    group_frames: dict[str, pd.DataFrame] = {}
    for stage in STAGES:
        print(f"\n[{stage}] group ablation...", flush=True)
        gdf = run_group_ablation(df, stage, train_traj, test_traj)
        gdf.to_csv(ablation_dir / f"ablation_{stage}.csv", index=False)
        group_frames[stage] = gdf

    indiv_frames: dict[str, pd.DataFrame] = {}
    for stage in STAGES:
        print(f"\n[{stage}] individual ablation...", flush=True)
        idf = run_individual_ablation(df, stage, train_traj, test_traj)
        idf.to_csv(indiv_dir / f"feature_ablation_{stage}.csv", index=False)
        indiv_frames[stage] = idf

    compare = compare_shap_ablation(shap_frames, indiv_frames)
    compare.to_csv(out_root / "shap_vs_ablation.csv", index=False)

    # Combined SHAP summary across targets
    shap_all = pd.concat(shap_frames, ignore_index=True)
    combined = (
        shap_all.groupby(["stage", "feature"], as_index=False)
        .agg(mean_abs_shap=("mean_abs_shap", "mean"), mean_shap=("mean_shap", "mean"))
        .sort_values(["stage", "mean_abs_shap"], ascending=[True, False])
    )
    combined.to_csv(shap_dir / "shap_combined_summary.csv", index=False)

    write_summary(
        out_root / "feature_analysis_summary.md",
        meta,
        inventory,
        shap_frames,
        group_frames,
        indiv_frames,
        compare,
    )
    print(f"\nDone. Outputs in {out_root}")


if __name__ == "__main__":
    main()
