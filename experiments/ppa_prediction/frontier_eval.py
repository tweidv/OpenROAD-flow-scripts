#!/usr/bin/env python3
"""Offline frontier-search sanity check on held-out GCD trajectories.

This is NOT a counterfactual or action-value test. We replay completed
trajectories and ask whether structural-only checkpoint predictions would
keep the actually-best branch alive under a simple top-k + margin prune.

Models are trained only on the train split; all frontier candidates come
from the held-out test split.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score
from splits import split_trajectories
from xgboost import XGBRegressor

from build_dataset import build_dataset, load_trajectories
from designs import DESIGNS
from features import STAGES
from ppa_value import collect_completed_runs, targets_from_batch
from train import feature_columns

FLOW = Path(__file__).resolve().parents[2] / "flow"
EXP = Path(__file__).resolve().parent

COMPONENTS = ("V_P", "V_T", "V_A")
EVAL_STAGES = ("placement", "cts", "routing")


def combined_v(v_p: float, v_t: float, v_a: float) -> float:
    v_p = float(np.clip(v_p, 0.0, 1.0))
    v_t = float(np.clip(v_t, 0.0, 1.0))
    v_a = float(np.clip(v_a, 0.0, 1.0))
    return float((v_p * v_t * v_a) ** (1.0 / 3.0))


def make_models() -> XGBRegressor:
    return XGBRegressor(
        n_estimators=80,
        max_depth=4,
        learning_rate=0.1,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=42,
        objective="reg:squarederror",
    )


@dataclass
class StageModels:
    v_p: XGBRegressor
    v_t: XGBRegressor
    v_a: XGBRegressor


@dataclass
class CandidateState:
    trajectory_id: str
    pred_v_p: float
    pred_v_t: float
    pred_v_a: float
    pred_v: float
    actual_v_p: float
    actual_v_t: float
    actual_v_a: float
    actual_v: float
    pred_rank: int = 0
    alive: bool = True


def train_stage_models(
    df: pd.DataFrame,
    feature_cols: list[str],
    train_traj: set[str],
    stage: str,
) -> StageModels:
    data = df[(df["stage"] == stage) & (df["trajectory_id"].isin(train_traj))]
    X = data[feature_cols].apply(pd.to_numeric, errors="coerce").astype(float)
    return StageModels(
        v_p=make_models().fit(X, data["V_P"]),
        v_t=make_models().fit(X, data["V_T"]),
        v_a=make_models().fit(X, data["V_A"]),
    )


def predict_candidate(
    row: pd.Series,
    models: StageModels,
    feature_cols: list[str],
    actual: pd.Series,
) -> CandidateState:
    X = row[feature_cols].apply(pd.to_numeric, errors="coerce").astype(float).to_frame().T
    v_p = float(models.v_p.predict(X)[0])
    v_t = float(models.v_t.predict(X)[0])
    v_a = float(models.v_a.predict(X)[0])
    return CandidateState(
        trajectory_id=str(row["trajectory_id"]),
        pred_v_p=v_p,
        pred_v_t=v_t,
        pred_v_a=v_a,
        pred_v=combined_v(v_p, v_t, v_a),
        actual_v_p=float(actual["V_P"]),
        actual_v_t=float(actual["V_T"]),
        actual_v_a=float(actual["V_A"]),
        actual_v= float(actual["final_V"]),
    )


def actual_ground_truth(df: pd.DataFrame, test_traj: list[str]) -> pd.DataFrame:
    """One row per test trajectory with final labels."""
    return (
        df[df["trajectory_id"].isin(test_traj)]
        .groupby("trajectory_id", as_index=False)
        .first()[["trajectory_id", "final_V", "V_P", "V_T", "V_A"]]
    )


def run_frontier(
    df: pd.DataFrame,
    *,
    train_traj: set[str],
    test_traj: list[str],
    feature_cols: list[str],
    stages: tuple[str, ...],
    top_k: int,
    margin: float,
) -> dict[str, Any]:
    truth = actual_ground_truth(df, test_traj)
    best_actual_tid = truth.loc[truth["final_V"].idxmax(), "trajectory_id"]
    best_actual_v = float(truth["final_V"].max())

    alive = set(test_traj)
    stage_reports: list[dict[str, Any]] = []

    for stage in stages:
        models = train_stage_models(df, feature_cols, train_traj, stage)
        candidates: list[CandidateState] = []
        for tid in sorted(alive):
            row = df[(df["trajectory_id"] == tid) & (df["stage"] == stage)].iloc[0]
            act = truth[truth["trajectory_id"] == tid].iloc[0]
            candidates.append(predict_candidate(row, models, feature_cols, act))

        candidates.sort(key=lambda c: c.pred_v, reverse=True)
        for i, c in enumerate(candidates, start=1):
            c.pred_rank = i

        n_before = len(candidates)
        best_pred = candidates[0].pred_v if candidates else 0.0
        cutoff = best_pred - margin

        # Margin prune, then keep top-k among survivors.
        survivors = [c for c in candidates if c.pred_v >= cutoff]
        survivors = survivors[:top_k]
        survivor_ids = {c.trajectory_id for c in survivors}
        eliminated = [c for c in candidates if c.trajectory_id not in survivor_ids]

        best_in_stage = next((c for c in candidates if c.trajectory_id == best_actual_tid), None)
        if best_in_stage is not None:
            best_rank = best_in_stage.pred_rank
            best_survives = best_actual_tid in survivor_ids
        else:
            best_rank = None
            best_survives = False

        pred_vs_actual = [
            {
                "trajectory_id": c.trajectory_id,
                "pred_V_P": c.pred_v_p,
                "pred_V_T": c.pred_v_t,
                "pred_V_A": c.pred_v_a,
                "pred_V": c.pred_v,
                "actual_V_P": c.actual_v_p,
                "actual_V_T": c.actual_v_t,
                "actual_V_A": c.actual_v_a,
                "actual_V": c.actual_v,
                "pred_rank": c.pred_rank,
                "survived": c.trajectory_id in survivor_ids,
            }
            for c in candidates
        ]

        pred_v = np.array([c.pred_v for c in candidates])
        act_v = np.array([c.actual_v for c in candidates])
        stage_reports.append(
            {
                "stage": stage,
                "n_candidates_before": n_before,
                "n_eliminated": len(eliminated),
                "n_survivors": len(survivors),
                "eliminated_ids": [c.trajectory_id for c in eliminated],
                "survivor_ids": sorted(survivor_ids),
                "best_actual_trajectory": best_actual_tid,
                "best_actual_V": best_actual_v,
                "best_actual_pred_rank": best_rank,
                "best_actual_survives": best_survives,
                "best_predicted_V": best_pred,
                "margin_cutoff": cutoff,
                "prediction_quality": {
                    "V_mae": float(mean_absolute_error(act_v, pred_v)),
                    "V_r2": float(r2_score(act_v, pred_v)) if len(candidates) > 1 else float("nan"),
                    "V_P_mae": float(mean_absolute_error([c.actual_v_p for c in candidates], [c.pred_v_p for c in candidates])),
                    "V_T_mae": float(mean_absolute_error([c.actual_v_t for c in candidates], [c.pred_v_t for c in candidates])),
                    "V_A_mae": float(mean_absolute_error([c.actual_v_a for c in candidates], [c.pred_v_a for c in candidates])),
                },
                "candidates": pred_vs_actual,
            }
        )

        alive = survivor_ids

    final_survives = best_actual_tid in alive
    return {
        "best_actual_trajectory": best_actual_tid,
        "best_actual_V": best_actual_v,
        "best_survives_to_end": final_survives,
        "final_survivors": sorted(alive),
        "top_k": top_k,
        "margin": margin,
        "stages": stage_reports,
    }


def plot_survival(stage_reports: list[dict], out_path: Path, title: str) -> None:
    stages = [s["stage"] for s in stage_reports]
    ranks = [s["best_actual_pred_rank"] if s["best_actual_pred_rank"] is not None else np.nan for s in stage_reports]
    n_alive = [s["n_survivors"] for s in stage_reports]

    fig, ax1 = plt.subplots(figsize=(7, 4))
    ax1.plot(stages, ranks, marker="o", color="#2563eb", linewidth=2, label="rank of actual-best")
    ax1.axhline(1, color="gray", linestyle="--", alpha=0.5)
    ax1.set_ylabel("Predicted rank of actual-best")
    ax1.set_xlabel("Checkpoint stage")
    ax1.set_title(title)
    ax1.invert_yaxis()
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    ax2.bar(stages, n_alive, alpha=0.2, color="#16a34a", label="survivors")
    ax2.set_ylabel("Live candidates")

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_pred_vs_actual(stage_reports: list[dict], out_path: Path, title: str) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    pairs = [("V_P", "pred_V_P", "actual_V_P"), ("V_T", "pred_V_T", "actual_V_T"), ("V_A", "pred_V_A", "actual_V_A")]

    # Use last stage (most candidates still had full eval at prior stages; use routing if present)
    last = stage_reports[-1]
    data = last["candidates"]

    for ax, (label, pk, ak) in zip(axes, pairs):
        pred = [d[pk] for d in data]
        act = [d[ak] for d in data]
        ax.scatter(act, pred, alpha=0.75)
        ax.plot([0, 1], [0, 1], "--", color="gray")
        ax.set_xlabel(f"Actual {label}")
        ax.set_ylabel(f"Predicted {label}")
        ax.set_title(f"{label} @ {last['stage']}")
        ax.set_xlim(0, 1.05)
        ax.set_ylim(0, 1.05)

    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def print_summary(report: dict[str, Any]) -> None:
    print("\n=== Offline frontier search (structural-only, held-out test candidates) ===")
    print("NOTE: replay sanity check — not a counterfactual action-value test.\n")
    print(f"Best actual test trajectory: {report['best_actual_trajectory']}  V={report['best_actual_V']:.3f}")
    print(f"Survives to end (top_k={report['top_k']}, margin={report['margin']}): {report['best_survives_to_end']}")
    print(f"Final survivors ({len(report['final_survivors'])}): {', '.join(report['final_survivors'])}")
    print()
    print(f"{'Stage':<12} {'Rank':>5} {'Surv?':>6} {'Elim':>5} {'Live':>5} {'V MAE':>8} {'V R²':>8}")
    for s in report["stages"]:
        pq = s["prediction_quality"]
        rank = s["best_actual_pred_rank"]
        rank_s = str(rank) if rank is not None else "elim"
        print(
            f"{s['stage']:<12} {rank_s:>5} "
            f"{str(s['best_actual_survives']):>6} {s['n_eliminated']:>5} {s['n_survivors']:>5} "
            f"{pq['V_mae']:>8.4f} {pq['V_r2']:>8.3f}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline frontier-search evaluation")
    parser.add_argument("--design", choices=sorted(DESIGNS), default="gcd")
    parser.add_argument(
        "--stages",
        nargs="+",
        default=["placement", "cts", "routing"],
        choices=EVAL_STAGES,
        help="Checkpoint stages in prune order",
    )
    parser.add_argument("--top-k", type=int, default=5, help="Max live candidates after each stage")
    parser.add_argument(
        "--margin",
        type=float,
        default=0.05,
        help="Eliminate when predicted V is more than this below the stage best",
    )
    parser.add_argument(
        "--sweep-top-k",
        action="store_true",
        help="Also run survival sweep over top_k values",
    )
    args = parser.parse_args()

    spec = DESIGNS[args.design]
    out_dir = EXP / "output" / spec.key / "frontier_eval"
    out_dir.mkdir(parents=True, exist_ok=True)

    trajectories = load_trajectories(args.design)
    tids = [t.trajectory_id for t in trajectories]
    runs = collect_completed_runs(FLOW, tids, platform=spec.platform, log_name=spec.log_name)
    targets = targets_from_batch(runs)
    df = build_dataset(trajectories, spec, targets)

    feature_cols = feature_columns(df, include_norm_pta=False, exclude_timing_proxies=False)
    train_list, test_list = split_trajectories(sorted(df["trajectory_id"].unique()))
    train_set = set(train_list)

    stages = tuple(s for s in EVAL_STAGES if s in args.stages)
    stage_tag = "_".join(stages) if stages != EVAL_STAGES else "full"

    report = run_frontier(
        df,
        train_traj=train_set,
        test_traj=test_list,
        feature_cols=feature_cols,
        stages=stages,
        top_k=args.top_k,
        margin=args.margin,
    )
    report["design"] = args.design
    report["disclaimer"] = (
        "Offline replay on completed trajectories. Predictions rank held-out branches; "
        "this does not measure counterfactual outcomes of killing runs mid-flow."
    )
    report["n_train_trajectories"] = len(train_set)
    report["n_test_candidates"] = len(test_list)
    report["train_trajectories"] = sorted(train_set)
    report["test_trajectories"] = test_list
    report["targets"] = targets

    if args.sweep_top_k:
        sweep = []
        for k in range(1, len(test_list) + 1):
            r = run_frontier(
                df,
                train_traj=train_set,
                test_traj=test_list,
                feature_cols=feature_cols,
                stages=stages,
                top_k=k,
                margin=args.margin,
            )
            sweep.append(
                {
                    "top_k": k,
                    "best_survives_to_end": r["best_survives_to_end"],
                    "final_survivors": r["final_survivors"],
                }
            )
        report["top_k_sweep"] = sweep
        surviving = sum(1 for s in sweep if s["best_survives_to_end"])
        report["top_k_sweep_survival_rate"] = surviving / len(sweep)

    (out_dir / f"frontier_eval_{stage_tag}.json").write_text(json.dumps(report, indent=2))
    plot_survival(
        report["stages"],
        out_dir / f"frontier_best_rank_{stage_tag}.png",
        f"{args.design} frontier ({stage_tag}): rank of actual-best (top_k={args.top_k})",
    )
    plot_pred_vs_actual(
        report["stages"],
        out_dir / f"frontier_pred_vs_actual_{stage_tag}.png",
        f"{args.design} predicted vs actual components ({stage_tag})",
    )

    print_summary(report)
    if args.sweep_top_k:
        print(f"\nTop-k sweep survival rate: {report['top_k_sweep_survival_rate']:.1%}")
        for s in report["top_k_sweep"]:
            mark = "✓" if s["best_survives_to_end"] else "✗"
            print(f"  top_k={s['top_k']:2d}  survives={mark}")

    print(f"\nWrote {out_dir}/frontier_eval_{stage_tag}.json")
    print(f"Wrote {out_dir}/frontier_best_rank_{stage_tag}.png")
    print(f"Wrote {out_dir}/frontier_pred_vs_actual_{stage_tag}.png")


if __name__ == "__main__":
    main()
