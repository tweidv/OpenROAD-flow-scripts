#!/usr/bin/env python3
"""Greedy forward feature selection for GCD PPA prediction (offline, no new runs)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from designs import DESIGNS
from feature_analysis import (
    EXP,
    MODEL_PARAMS,
    STAGE_FEATURES,
    TARGETS,
    load_final_pta,
    make_model,
    train_eval,
)
from features import STAGES
from splits import DEFAULT_RANDOM_STATE, DEFAULT_TRAIN_SIZE, split_train_validation, split_trajectories
from wide_metrics import build_all_stages

OUT_ROOT = EXP / "output" / "gcd" / "feature_selection"
FULL_SHAP = EXP / "output" / "gcd" / "feature_analysis" / "full" / "shap"
FULL_INDIV = EXP / "output" / "gcd" / "feature_analysis" / "full" / "individual"
TARGETS_JSON = EXP / "output" / "gcd" / "targets.json"
DATASET_CSV = EXP / "output" / "gcd" / "dataset.csv"

IMPROVEMENT_THRESHOLDS = (0.95, 0.99)


def baseline_r2(y_train: pd.Series, y_val: pd.Series) -> float:
    """Mean predictor baseline."""
    pred = np.full(len(y_val), float(y_train.mean()))
    return float(r2_score(y_val, pred))


def eval_metrics(y_true: pd.Series, pred: np.ndarray) -> dict[str, float]:
    return {
        "r2": float(r2_score(y_true, pred)),
        "mae": float(mean_absolute_error(y_true, pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, pred))),
    }


def drop_constant_features(
    df: pd.DataFrame, feature_cols: list[str], trajectory_ids: list[str]
) -> list[str]:
    sub = df[df["trajectory_id"].isin(trajectory_ids)]
    keep = []
    for col in feature_cols:
        nuniq = sub[col].nunique(dropna=True)
        if nuniq >= 2:
            keep.append(col)
    return keep


def load_stage_data(
    design: str, limit: int, train_traj: list[str]
) -> dict[str, tuple[pd.DataFrame, list[str]]]:
    wide_data = build_all_stages(design, limit)
    spec = DESIGNS[design]
    pta = load_final_pta(
        sorted({tid for s in STAGES for tid in wide_data[s][0]["trajectory_id"]}),
        spec,
    )
    result: dict[str, tuple[pd.DataFrame, list[str]]] = {}
    for stage in STAGES:
        wide, feats, _ = wide_data[stage]
        df = wide.merge(pta, on="trajectory_id")
        feats = drop_constant_features(df, feats, train_traj)
        result[stage] = (df, feats)
    return result


def load_handpicked_stage_data(
    design: str, limit: int, pta: pd.DataFrame
) -> dict[str, pd.DataFrame]:
    df = pd.read_csv(DATASET_CSV)
    traj_order = sorted(df["trajectory_id"].unique())[:limit]
    df = df[df["trajectory_id"].isin(traj_order)].merge(pta, on="trajectory_id")
    return {stage: df[df["stage"] == stage].copy() for stage in STAGES}


def mean_predictor_metrics(
    y_inner_train: pd.Series,
    y_inner_val: pd.Series,
) -> dict[str, float]:
    pred = np.full(len(y_inner_val), float(y_inner_train.mean()))
    return eval_metrics(y_inner_val, pred)


def candidate_score_multi_seed(
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str,
    train_traj: list[str],
    inner_seeds: list[int],
    val_size: int,
) -> tuple[float, float, float, float]:
    """Return mean val R², std, mean MAE, mean RMSE averaged over inner seeds."""
    r2s, maes, rmses = [], [], []
    for seed in inner_seeds:
        inner_train, inner_val = split_train_validation(
            train_traj, val_size=val_size, random_state=seed
        )
        tr = df[df["trajectory_id"].isin(inner_train)]
        va = df[df["trajectory_id"].isin(inner_val)]
        X_tr = tr[feature_cols].astype(float)
        y_tr = tr[target_col]
        X_va = va[feature_cols].astype(float)
        y_va = va[target_col]
        model = make_model()
        model.fit(X_tr, y_tr)
        pred = model.predict(X_va)
        m = eval_metrics(y_va, pred)
        r2s.append(m["r2"])
        maes.append(m["mae"])
        rmses.append(m["rmse"])
    return float(np.mean(r2s)), float(np.std(r2s)), float(np.mean(maes)), float(np.mean(rmses))


def baseline_multi_seed(
    df: pd.DataFrame,
    target_col: str,
    train_traj: list[str],
    inner_seeds: list[int],
    val_size: int,
) -> tuple[float, float]:
    r2s = []
    for seed in inner_seeds:
        inner_train, inner_val = split_train_validation(
            train_traj, val_size=val_size, random_state=seed
        )
        tr = df[df["trajectory_id"].isin(inner_train)]
        va = df[df["trajectory_id"].isin(inner_val)]
        r2s.append(mean_predictor_metrics(tr[target_col], va[target_col])["r2"])
    return float(np.mean(r2s)), float(np.std(r2s))


def forward_select(
    df: pd.DataFrame,
    feature_cols: list[str],
    target_key: str,
    stage: str,
    train_traj: list[str],
    inner_seeds: list[int],
    val_size: int,
    out_dir: Path,
) -> pd.DataFrame:
    target_col = TARGETS[target_key]
    selected: list[str] = []
    remaining = list(feature_cols)
    baseline_mean, baseline_std = baseline_multi_seed(
        df, target_col, train_traj, inner_seeds, val_size
    )

    rows: list[dict[str, Any]] = [
        {
            "stage": stage,
            "target": target_key,
            "iteration": 0,
            "feature_added": "",
            "validation_R2": baseline_mean,
            "validation_R2_std": baseline_std,
            "validation_MAE": np.nan,
            "validation_RMSE": np.nan,
            "selected_features": "[]",
            "number_of_features": 0,
            "baseline_R2": baseline_mean,
        }
    ]

    best_val_r2 = baseline_mean
    for iteration in range(1, len(feature_cols) + 1):
        best_feat = None
        best_r2 = -np.inf
        best_std = 0.0
        best_mae = np.nan
        best_rmse = np.nan

        for feat in remaining:
            trial_feats = selected + [feat]
            r2, std, mae, rmse = candidate_score_multi_seed(
                df, trial_feats, target_col, train_traj, inner_seeds, val_size
            )
            if r2 > best_r2 + 1e-12:
                best_r2, best_std, best_mae, best_rmse, best_feat = r2, std, mae, rmse, feat
            elif abs(r2 - best_r2) <= 1e-12 and best_feat is not None:
                if mae < best_mae:
                    best_mae, best_rmse, best_feat = mae, rmse, feat
            elif abs(r2 - best_r2) <= 1e-12 and best_feat is None:
                best_r2, best_std, best_mae, best_rmse, best_feat = r2, std, mae, rmse, feat

        assert best_feat is not None
        selected.append(best_feat)
        remaining.remove(best_feat)
        best_val_r2 = max(best_val_r2, best_r2)

        rows.append(
            {
                "stage": stage,
                "target": target_key,
                "iteration": iteration,
                "feature_added": best_feat,
                "validation_R2": best_r2,
                "validation_R2_std": best_std,
                "validation_MAE": best_mae,
                "validation_RMSE": best_rmse,
                "selected_features": json.dumps(selected),
                "number_of_features": len(selected),
                "baseline_R2": baseline_mean,
            }
        )
        print(
            f"  iter {iteration:3d}: +{best_feat[:60]}... "
            f"val R²={best_r2:.4f}±{best_std:.4f} ({len(selected)} feats)",
            flush=True,
        )

    out = pd.DataFrame(rows)
    out.to_csv(out_dir / f"ffs_{stage}_{target_key}.csv", index=False)
    return out


def pick_threshold_set(
    ffs_df: pd.DataFrame, fraction: float
) -> tuple[int, list[str]]:
    """Smallest k reaching fraction of max improvement over baseline."""
    baseline = float(ffs_df.loc[ffs_df.iteration == 0, "validation_R2"].iloc[0])
    scored = ffs_df[ffs_df.iteration > 0].copy()
    if scored.empty:
        return 0, []

    max_r2 = float(scored["validation_R2"].max())
    max_improvement = max_r2 - baseline
    if max_improvement <= 1e-12:
        best_row = scored.loc[scored["validation_R2"].idxmax()]
        k = int(best_row["number_of_features"])
        return k, json.loads(best_row["selected_features"])

    target_improvement = fraction * max_improvement
    for _, row in scored.sort_values("number_of_features").iterrows():
        improvement = float(row["validation_R2"]) - baseline
        if improvement >= target_improvement - 1e-12:
            return int(row["number_of_features"]), json.loads(row["selected_features"])
    last = scored.sort_values("number_of_features").iloc[-1]
    return int(last["number_of_features"]), json.loads(last["selected_features"])


def final_test_eval(
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str,
    train_traj: list[str],
    test_traj: list[str],
) -> dict[str, float]:
    tr = df[df["trajectory_id"].isin(train_traj)]
    te = df[df["trajectory_id"].isin(test_traj)]
    if not feature_cols:
        pred = np.full(len(te), float(tr[target_col].mean()))
        y_te = te[target_col]
        return {
            **eval_metrics(y_te, pred),
            "n_features": 0,
        }
    _, metrics, _ = train_eval(
        tr[feature_cols].astype(float),
        tr[target_col],
        te[feature_cols].astype(float),
        te[target_col],
    )
    metrics["n_features"] = len(feature_cols)
    return metrics


def compute_v_components(
    p: np.ndarray, fmax: np.ndarray, area: np.ndarray, targets: dict[str, float]
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    p_tgt, t_tgt, a_tgt = targets["P_target"], targets["T_target"], targets["A_target"]
    v_p = np.clip(p_tgt / np.maximum(p, 1e-30), 0, 1)
    v_t = np.clip(fmax / t_tgt, 0, 1)
    v_a = np.clip(a_tgt / np.maximum(area, 1e-30), 0, 1)
    v = (v_p * v_t * v_a) ** (1.0 / 3.0)
    return v_p, v_t, v_a, v


def plot_ffs_curve(ffs_df: pd.DataFrame, stage: str, target: str, out_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.errorbar(
        ffs_df["number_of_features"],
        ffs_df["validation_R2"],
        yerr=ffs_df["validation_R2_std"].fillna(0),
        marker="o",
        capsize=3,
        color="#2563eb",
    )
    baseline = float(ffs_df.loc[ffs_df.iteration == 0, "validation_R2"].iloc[0])
    ax.axhline(baseline, color="#94a3b8", linestyle="--", label=f"baseline R²={baseline:.3f}")
    for frac, color in zip(IMPROVEMENT_THRESHOLDS, ("#16a34a", "#ca8a04")):
        k, _ = pick_threshold_set(ffs_df, frac)
        if k > 0:
            r2 = float(ffs_df.loc[ffs_df.number_of_features == k, "validation_R2"].iloc[0])
            ax.axvline(k, color=color, linestyle=":", alpha=0.8, label=f"{int(frac*100)}% imp @ k={k}")
            ax.scatter([k], [r2], color=color, s=80, zorder=5)
    ax.set_xlabel("Number of selected features")
    ax.set_ylabel("Validation R² (mean ± std over inner seeds)")
    ax.set_title(f"FFS: {stage} → {target}")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out_dir / f"ffs_curve_{stage}_{target}.png", dpi=150)
    plt.close(fig)


def load_shap_rankings(stage: str, target: str) -> pd.DataFrame:
    path = FULL_SHAP / f"shap_{stage}_{target}.csv"
    if not path.exists():
        return pd.DataFrame()
    sh = pd.read_csv(path)
    sh["shap_rank"] = sh["mean_abs_shap"].rank(ascending=False, method="first").astype(int)
    return sh[["feature", "mean_abs_shap", "shap_rank"]]


def load_ablation_rankings(stage: str, target: str) -> pd.DataFrame:
    path = FULL_INDIV / f"feature_ablation_{stage}.csv"
    if not path.exists():
        return pd.DataFrame()
    ab = pd.read_csv(path)
    ab = ab[ab.target == target].copy()
    ab["ablation_rank"] = ab["delta_r2"].rank(ascending=False, method="first").astype(int)
    return ab[["dropped_feature", "delta_r2", "ablation_rank"]].rename(
        columns={"dropped_feature": "feature"}
    )


def build_comparison_table(
    ffs_df: pd.DataFrame,
    stage: str,
    target: str,
    selected_99: list[str],
) -> pd.DataFrame:
    sh = load_shap_rankings(stage, target)
    ab = load_ablation_rankings(stage, target)
    feat_to_iter: dict[str, int] = {}
    for _, row in ffs_df[ffs_df.iteration > 0].iterrows():
        feat_to_iter[str(row["feature_added"])] = int(row["iteration"])

    all_feats = sorted(set(sh.get("feature", pd.Series(dtype=str)).tolist()) | set(feat_to_iter))
    rows = []
    for i, feat in enumerate(all_feats, 1):
        sh_row = sh[sh.feature == feat] if len(sh) else pd.DataFrame()
        ab_row = ab[ab.feature == feat] if len(ab) else pd.DataFrame()
        rows.append(
            {
                "stage": stage,
                "target": target,
                "rank": i,
                "feature": feat,
                "ffs_iteration": feat_to_iter.get(feat),
                "mean_abs_shap": float(sh_row["mean_abs_shap"].iloc[0]) if len(sh_row) else np.nan,
                "shap_rank": int(sh_row["shap_rank"].iloc[0]) if len(sh_row) else np.nan,
                "ablation_delta_r2": float(ab_row["delta_r2"].iloc[0]) if len(ab_row) else np.nan,
                "ablation_rank": int(ab_row["ablation_rank"].iloc[0]) if len(ab_row) else np.nan,
                "selected_by_ffs_99": feat in selected_99,
            }
        )
    comp = pd.DataFrame(rows)
    comp = comp.sort_values(
        ["ffs_iteration", "shap_rank"],
        ascending=[True, True],
        na_position="last",
    )
    comp["rank"] = range(1, len(comp) + 1)
    return comp


def count_expected_fits(stage_features: dict[str, list[str]], n_seeds: int) -> dict[str, int]:
    per_combo = {}
    total = 0
    for stage in STAGES:
        n = len(stage_features[stage])
        # iter 0 baseline + sum_{k=1..n} (n-k+1) candidates
        fits = 1 + sum(n - k + 1 for k in range(1, n + 1))
        per_combo[stage] = fits * len(TARGETS) * n_seeds
        total += per_combo[stage]
    return {"per_stage_targets": per_combo, "total_val_fits": total}


def print_preflight(
    stage_data: dict[str, tuple[pd.DataFrame, list[str]]],
    train_traj: list[str],
    test_traj: list[str],
    inner_seeds: list[int],
    val_size: int,
) -> None:
    print("\n=== Forward Feature Selection — Preflight ===")
    print(f"Trajectories: {len(train_traj) + len(test_traj)} total")
    print(f"Train: {len(train_traj)}  |  Test: {len(test_traj)} (untouched during FFS)")
    print(f"Inner split: {len(train_traj) - val_size} train / {val_size} validation per seed")
    print(f"Inner seeds: {inner_seeds}")
    print("\nInner validation trajectory IDs per seed:")
    for seed in inner_seeds:
        _, inner_val = split_train_validation(train_traj, val_size=val_size, random_state=seed)
        print(f"  seed {seed}: {inner_val}")

    print("\nCandidate features per stage (after dropping train-constant):")
    for stage in STAGES:
        _, feats = stage_data[stage]
        print(f"\n  {stage}: {len(feats)} features")
        for f in feats:
            print(f"    - {f}")

    counts = count_expected_fits({s: stage_data[s][1] for s in STAGES}, len(inner_seeds))
    print(f"\nExpected validation model fits: {counts['total_val_fits']}")
    print(f"  per stage (×3 targets × {len(inner_seeds)} seeds): {counts['per_stage_targets']}")
    print(f"\nSHAP/ablation comparison inputs: {FULL_SHAP} (exists={FULL_SHAP.exists()})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Forward feature selection for GCD PPA")
    parser.add_argument("--design", default="gcd")
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--train-size", type=int, default=DEFAULT_TRAIN_SIZE)
    parser.add_argument("--val-size", type=int, default=5)
    parser.add_argument(
        "--inner-seeds",
        default="42,43,44",
        help="Comma-separated seeds for inner train/val splits",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print preflight only")
    args = parser.parse_args()

    inner_seeds = [int(s.strip()) for s in args.inner_seeds.split(",") if s.strip()]
    out_dir = EXP / "output" / args.design / "feature_selection"
    plots_dir = out_dir / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    spec = DESIGNS[args.design]
    pta = load_final_pta(
        sorted(
            pd.read_csv(DATASET_CSV)["trajectory_id"].unique().tolist()
        )[: args.limit],
        spec,
    )
    all_traj = sorted(pta["trajectory_id"].unique())[: args.limit]
    train_traj, test_traj = split_trajectories(all_traj, train_size=args.train_size)

    print("Building wide feature tables from existing JSON logs...")
    stage_data = load_stage_data(args.design, args.limit, train_traj)
    handpicked = load_handpicked_stage_data(args.design, args.limit, pta)

    print_preflight(stage_data, train_traj, test_traj, inner_seeds, args.val_size)
    if args.dry_run:
        return

    meta = {
        "design": args.design,
        "limit": args.limit,
        "train_trajectory_ids": train_traj,
        "test_trajectory_ids": test_traj,
        "train_size": args.train_size,
        "val_size": args.val_size,
        "inner_seeds": inner_seeds,
        "inner_splits": {
            str(seed): {
                "inner_train": split_train_validation(
                    train_traj, val_size=args.val_size, random_state=seed
                )[0],
                "inner_val": split_train_validation(
                    train_traj, val_size=args.val_size, random_state=seed
                )[1],
            }
            for seed in inner_seeds
        },
        "model_params": MODEL_PARAMS,
        "stage_features": {s: stage_data[s][1] for s in STAGES},
        "expected_val_fits": count_expected_fits(
            {s: stage_data[s][1] for s in STAGES}, len(inner_seeds)
        ),
    }
    (out_dir / "run_metadata.json").write_text(json.dumps(meta, indent=2, default=str))

    # --- FFS ---
    ffs_results: dict[tuple[str, str], pd.DataFrame] = {}
    for stage in STAGES:
        df, feats = stage_data[stage]
        for target_key in TARGETS:
            print(f"\n[FFS] {stage} → {target_key} ({len(feats)} candidates)", flush=True)
            ffs_df = forward_select(
                df,
                feats,
                target_key,
                stage,
                train_traj,
                inner_seeds,
                args.val_size,
                out_dir,
            )
            ffs_results[(stage, target_key)] = ffs_df
            plot_ffs_curve(ffs_df, stage, target_key, plots_dir)

    # --- Selected feature sets ---
    selected_rows = []
    saturation_rows = []
    for stage in STAGES:
        for target_key in TARGETS:
            ffs_df = ffs_results[(stage, target_key)]
            baseline = float(ffs_df.loc[ffs_df.iteration == 0, "validation_R2"].iloc[0])
            max_r2 = float(ffs_df["validation_R2"].max())
            max_improvement = max_r2 - baseline
            for frac in IMPROVEMENT_THRESHOLDS:
                k, feats = pick_threshold_set(ffs_df, frac)
                selected_rows.append(
                    {
                        "stage": stage,
                        "target": target_key,
                        "selection_rule": f"{int(frac * 100)}pct_improvement",
                        "n_features": k,
                        "selected_features": json.dumps(feats),
                    }
                )
                saturation_rows.append(
                    {
                        "stage": stage,
                        "target": target_key,
                        "threshold": f"{int(frac * 100)}pct",
                        "n_features_required": k,
                        "validation_R2_at_k": float(
                            ffs_df.loc[ffs_df.number_of_features == k, "validation_R2"].iloc[0]
                        )
                        if k > 0
                        else baseline,
                        "baseline_validation_R2": baseline,
                        "max_validation_R2": max_r2,
                        "max_improvement": max_improvement,
                    }
                )
            k_max = int(ffs_df.loc[ffs_df.validation_R2.idxmax(), "number_of_features"])
            feats_max = json.loads(
                ffs_df.loc[ffs_df.validation_R2.idxmax(), "selected_features"]
            )
            selected_rows.append(
                {
                    "stage": stage,
                    "target": target_key,
                    "selection_rule": "max_validation_r2",
                    "n_features": k_max,
                    "selected_features": json.dumps(feats_max),
                }
            )
    pd.DataFrame(selected_rows).to_csv(out_dir / "selected_features.csv", index=False)
    pd.DataFrame(saturation_rows).to_csv(out_dir / "saturation_thresholds.csv", index=False)

    # --- Final test evaluation ---
    test_rows = []
    for stage in STAGES:
        df, all_feats = stage_data[stage]
        hp_df = handpicked[stage]
        hp_feats = STAGE_FEATURES[stage]
        for target_key, target_col in TARGETS.items():
            k99, feats99 = pick_threshold_set(ffs_results[(stage, target_key)], 0.99)
            k95, feats95 = pick_threshold_set(ffs_results[(stage, target_key)], 0.95)

            for label, feats in [
                ("ffs_99pct", feats99),
                ("ffs_95pct", feats95),
                ("full", all_feats),
                ("handpicked", hp_feats),
            ]:
                if label == "handpicked":
                    m = final_test_eval(hp_df, feats, target_col, train_traj, test_traj)
                else:
                    m = final_test_eval(df, feats, target_col, train_traj, test_traj)
                test_rows.append(
                    {
                        "stage": stage,
                        "target": target_key,
                        "feature_set": label,
                        "n_features": m["n_features"],
                        "test_R2": m["r2"],
                        "test_MAE": m["mae"],
                        "test_RMSE": m["rmse"],
                    }
                )
    pd.DataFrame(test_rows).to_csv(out_dir / "final_test_results.csv", index=False)

    # --- SHAP / ablation comparison ---
    comp_frames = []
    for stage in STAGES:
        for target_key in TARGETS:
            _, feats99 = pick_threshold_set(ffs_results[(stage, target_key)], 0.99)
            comp = build_comparison_table(
                ffs_results[(stage, target_key)], stage, target_key, feats99
            )
            comp.to_csv(out_dir / f"comparison_{stage}_{target_key}.csv", index=False)
            comp_frames.append(comp)

    # --- Shared stage feature sets ---
    targets_json = json.loads(TARGETS_JSON.read_text())
    shared_rows = []
    for stage in STAGES:
        df, _ = stage_data[stage]
        hp_df = handpicked[stage]
        per_target = {}
        for target_key in TARGETS:
            _, feats = pick_threshold_set(ffs_results[(stage, target_key)], 0.99)
            per_target[target_key] = feats

        union = sorted(set(per_target["power"]) | set(per_target["fmax"]) | set(per_target["area"]))

        for set_name, feats in [
            ("union_99pct", union),
            ("power_only_99pct", per_target["power"]),
            ("fmax_only_99pct", per_target["fmax"]),
            ("area_only_99pct", per_target["area"]),
        ]:
            row: dict[str, Any] = {
                "stage": stage,
                "feature_set": set_name,
                "n_features": len(feats),
                "features": json.dumps(feats),
            }
            preds: dict[str, np.ndarray] = {}
            for target_key, target_col in TARGETS.items():
                m = final_test_eval(df, feats, target_col, train_traj, test_traj)
                row[f"test_R2_{target_key}"] = m["r2"]
                row[f"test_MAE_{target_key}"] = m["mae"]
                row[f"test_RMSE_{target_key}"] = m["rmse"]
                tr = df[df.trajectory_id.isin(train_traj)]
                te = df[df.trajectory_id.isin(test_traj)]
                if feats:
                    model = make_model()
                    model.fit(tr[feats].astype(float), tr[target_col])
                    preds[target_key] = model.predict(te[feats].astype(float))
                else:
                    preds[target_key] = np.full(len(te), float(tr[target_col].mean()))

            te = df[df.trajectory_id.isin(test_traj)]
            act_p = te["final_power"].values
            act_f = te["final_fmax"].values
            act_a = te["final_area"].values
            v_p, v_t, v_a, v = compute_v_components(
                preds["power"], preds["fmax"], preds["area"], targets_json
            )
            act_vp, act_vt, act_va, act_v = compute_v_components(
                act_p, act_f, act_a, targets_json
            )
            row["test_R2_combined_V"] = float(r2_score(act_v, v))
            row["test_MAE_combined_V"] = float(mean_absolute_error(act_v, v))
            shared_rows.append(row)

    pd.DataFrame(shared_rows).to_csv(out_dir / "shared_stage_features.csv", index=False)

    # --- Summary markdown ---
    write_summary(out_dir, meta, ffs_results, test_rows, shared_rows, saturation_rows)
    print(f"\nDone. Outputs in {out_dir}")


def write_summary(
    out_dir: Path,
    meta: dict,
    ffs_results: dict,
    test_rows: list,
    shared_rows: list,
    saturation_rows: list,
) -> None:
    test_df = pd.DataFrame(test_rows)
    sat_df = pd.DataFrame(saturation_rows)
    shared_df = pd.DataFrame(shared_rows)

    lines = [
        "# GCD Forward Feature Selection — Summary",
        "",
        f"**Design:** {meta['design']}  |  **Trajectories:** {meta['limit']}",
        f"**Split:** {meta['train_size']} train / {len(meta['test_trajectory_ids'])} test",
        f"**Inner validation:** {meta['train_size'] - meta['val_size']} / {meta['val_size']} "
        f"from train pool, seeds {meta['inner_seeds']}",
        "",
        "## Method",
        "",
        "- Greedy forward selection per stage × target on **validation R²** (mean ± std over inner seeds).",
        "- Test set **never used** during selection.",
        "- Final models retrained on all 20 train trajectories, evaluated once on 980 test.",
        "- Feature pool: 233 wide ORFS metrics (train-constant features removed).",
        "",
        "## Saturation: features required for 95% / 99% of achievable improvement",
        "",
        "| Stage | Target | 95% imp (k) | 99% imp (k) | Max val R² | Baseline val R² |",
        "|-------|--------|------------:|------------:|-----------:|----------------:|",
    ]
    for stage in STAGES:
        for target in TARGETS:
            s95 = sat_df[(sat_df.stage == stage) & (sat_df.target == target) & (sat_df.threshold == "95pct")]
            s99 = sat_df[(sat_df.stage == stage) & (sat_df.target == target) & (sat_df.threshold == "99pct")]
            if len(s95) and len(s99):
                lines.append(
                    f"| {stage} | {target} | {int(s95.n_features_required.iloc[0])} | "
                    f"{int(s99.n_features_required.iloc[0])} | "
                    f"{s95.max_validation_R2.iloc[0]:.3f} | {s95.baseline_validation_R2.iloc[0]:.3f} |"
                )

    lines += [
        "",
        "## Final test R²: FFS vs full vs hand-picked",
        "",
        "| Stage | Target | FFS 99% | FFS 95% | Full | Hand-picked |",
        "|-------|--------|--------:|--------:|-----:|------------:|",
    ]
    for stage in STAGES:
        for target in TARGETS:
            def r2(label):
                sub = test_df[
                    (test_df.stage == stage) & (test_df.target == target) & (test_df.feature_set == label)
                ]
                return f"{sub.test_R2.iloc[0]:.3f}" if len(sub) else "—"

            lines.append(
                f"| {stage} | {target} | {r2('ffs_99pct')} | {r2('ffs_95pct')} | "
                f"{r2('full')} | {r2('handpicked')} |"
            )

    lines += [
        "",
        "## Shared feature sets (union of 99% FFS selections)",
        "",
        "| Stage | Set | n | R² power | R² fmax | R² area | R² combined V |",
        "|-------|-----|--:|---------:|--------:|--------:|--------------:|",
    ]
    for stage in STAGES:
        for set_name in ["union_99pct", "power_only_99pct", "fmax_only_99pct", "area_only_99pct"]:
            sub = shared_df[(shared_df.stage == stage) & (shared_df.feature_set == set_name)]
            if len(sub):
                r = sub.iloc[0]
                lines.append(
                    f"| {stage} | {set_name} | {int(r.n_features)} | "
                    f"{r.test_R2_power:.3f} | {r.test_R2_fmax:.3f} | {r.test_R2_area:.3f} | "
                    f"{r.test_R2_combined_V:.3f} |"
                )

    lines += [
        "",
        "## Interpretation checklist",
        "",
        "- **Features needed:** see saturation table above.",
        "- **Consistent selections:** compare `selected_features.csv` across targets.",
        "- **Redundancy:** see `comparison_<stage>_<target>.csv` for SHAP high / FFS late cases.",
        "- **Shared vs target-specific:** union row vs per-target rows in shared table.",
        "- **Compact vs full loss:** FFS 99% column vs Full column in test table.",
        "",
        "## Outputs",
        "",
        "- `ffs_<stage>_<target>.csv` — every FFS iteration",
        "- `selected_features.csv` — chosen sets by rule",
        "- `final_test_results.csv` — held-out test metrics",
        "- `shared_stage_features.csv` — cross-target union analysis",
        "- `comparison_<stage>_<target>.csv` — FFS vs SHAP vs ablation",
        "- `plots/ffs_curve_*.png` — validation R² vs # features",
    ]
    (out_dir / "feature_selection_summary.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
