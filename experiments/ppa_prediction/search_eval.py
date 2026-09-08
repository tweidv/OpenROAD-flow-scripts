#!/usr/bin/env python3
"""Offline search-ordering evaluation on held-out GCD trajectories.

Hypothesis: can structural checkpoint predictions order a fixed candidate set
so near-optimal designs are found faster than random search?

This is NOT counterfactual action-value prediction. We replay completed
trajectories; the optimiser decides on predictions, metrics use true finals.
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

from build_dataset import build_dataset, load_trajectories
from designs import DESIGNS
from features import STAGES
from frontier_eval import combined_v, train_stage_models
from ppa_value import collect_completed_runs, targets_from_batch
from splits import split_trajectories
from train import feature_columns

FLOW = Path(__file__).resolve().parents[2] / "flow"
EXP = Path(__file__).resolve().parent

STAGE_LIST = list(STAGES)  # floorplan, placement, cts, routing

# Relative compute cost per checkpoint (GCD ~2 min/run profile).
DEFAULT_STAGE_COSTS: dict[str, float] = {
    "floorplan": 2.0,
    "placement": 4.0,
    "cts": 2.0,
    "routing": 3.0,
}


@dataclass
class CheckpointAccounting:
    """Running tally of checkpoint observations and cumulative compute cost."""

    stage_costs: dict[str, float]
    tally: dict[str, int] = field(default_factory=lambda: {s: 0 for s in STAGE_LIST})
    cumulative_cost: float = 0.0
    cost_curve: list[dict[str, Any]] = field(default_factory=list)

    @property
    def full_run_cost(self) -> float:
        return sum(self.stage_costs[s] for s in STAGE_LIST)

    def observe(self, stage: str) -> None:
        self.tally[stage] += 1
        self.cumulative_cost += self.stage_costs[stage]

    def snapshot(self, *, n_complete: int, best_found: float) -> None:
        self.cost_curve.append(
            {
                "cumulative_cost": self.cumulative_cost,
                "n_complete": n_complete,
                "best_found": best_found,
                "checkpoint_tally": dict(self.tally),
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "checkpoint_tally": dict(self.tally),
            "total_checkpoints": sum(self.tally.values()),
            "cumulative_cost": self.cumulative_cost,
            "stage_costs": dict(self.stage_costs),
            "full_run_cost": self.full_run_cost,
            "cost_curve": self.cost_curve,
        }


def parse_stage_costs(text: str) -> dict[str, float]:
    costs = dict(DEFAULT_STAGE_COSTS)
    for part in text.split(","):
        name, _, val = part.partition("=")
        name = name.strip()
        if not name:
            continue
        if name not in STAGE_LIST:
            raise ValueError(f"unknown stage {name!r}; choose from {STAGE_LIST}")
        costs[name] = float(val.strip())
    return costs


def cost_to_threshold(cost_curve: list[dict[str, Any]], threshold: float) -> float | None:
    for point in cost_curve:
        if point["best_found"] >= threshold:
            return float(point["cumulative_cost"])
    return None


@dataclass
class SearchState:
    trajectory_id: str
    stage_depth: int  # 0=floorplan .. 3=routing observed
    complete: bool = False
    pred_v: float = 0.0
    pred_v_p: float = 0.0
    pred_v_t: float = 0.0
    pred_v_a: float = 0.0


def load_test_truth(df: pd.DataFrame, test_traj: list[str]) -> dict[str, float]:
    truth = (
        df[df["trajectory_id"].isin(test_traj)]
        .groupby("trajectory_id", as_index=False)
        .first()
    )
    return {r.trajectory_id: float(r.final_V) for r in truth.itertuples()}


def build_prediction_cache(
    df: pd.DataFrame, feature_cols: list[str]
) -> dict[tuple[str, str], np.ndarray]:
    numeric = df[feature_cols].apply(pd.to_numeric, errors="coerce").astype(float)
    cache: dict[tuple[str, str], np.ndarray] = {}
    for idx, row in df.iterrows():
        key = (str(row["trajectory_id"]), str(row["stage"]))
        cache[key] = numeric.loc[idx].to_numpy(dtype=float).reshape(1, -1)
    return cache


def predict_v(
    tid: str,
    stage: str,
    models: dict[str, Any],
    feature_cache: dict[tuple[str, str], np.ndarray],
) -> tuple[float, float, float, float]:
    X = feature_cache[(tid, stage)]
    m = models[stage]
    v_p = float(m.v_p.predict(X)[0])
    v_t = float(m.v_t.predict(X)[0])
    v_a = float(m.v_a.predict(X)[0])
    return v_p, v_t, v_a, combined_v(v_p, v_t, v_a)


def update_predictions(
    states: dict[str, SearchState],
    models: dict[str, Any],
    feature_cache: dict[tuple[str, str], np.ndarray],
) -> None:
    for tid, st in states.items():
        if st.complete:
            continue
        stage = STAGE_LIST[st.stage_depth]
        v_p, v_t, v_a, v = predict_v(tid, stage, models, feature_cache)
        st.pred_v_p, st.pred_v_t, st.pred_v_a, st.pred_v = v_p, v_t, v_a, v


def simulate_model_guided(
    test_traj: list[str],
    models: dict[str, Any],
    feature_cache: dict[tuple[str, str], np.ndarray],
    truth: dict[str, float],
    *,
    stage_costs: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Checkpoint-switching search using predictions only for decisions."""
    costs = stage_costs or DEFAULT_STAGE_COSTS
    accounting = CheckpointAccounting(stage_costs=costs)
    states = {tid: SearchState(tid, stage_depth=0) for tid in test_traj}

    # Floorplan features readable for all candidates; predictions are free.
    # Cost accrues only when a flow stage is actually run (reveal_checkpoint).
    accounting.snapshot(n_complete=0, best_found=0.0)

    update_predictions(states, models, feature_cache)

    best_found = 0.0
    n_complete = 0
    curve: list[dict[str, Any]] = []
    steps: list[dict[str, Any]] = []
    step_idx = 0

    while n_complete < len(test_traj):
        active = [tid for tid, st in states.items() if not st.complete]
        best_tid = max(active, key=lambda t: states[t].pred_v)

        st = states[best_tid]
        step_idx += 1

        if st.stage_depth < len(STAGE_LIST) - 1:
            st.stage_depth += 1
            revealed = STAGE_LIST[st.stage_depth]
            accounting.observe(revealed)
            update_predictions(states, models, feature_cache)
            accounting.snapshot(n_complete=n_complete, best_found=best_found)
            steps.append(
                {
                    "step": step_idx,
                    "action": "reveal_checkpoint",
                    "trajectory_id": best_tid,
                    "stage_revealed": revealed,
                    "stage_depth": st.stage_depth,
                    "pred_V": st.pred_v,
                    "pred_V_P": st.pred_v_p,
                    "pred_V_T": st.pred_v_t,
                    "pred_V_A": st.pred_v_a,
                    "n_complete": n_complete,
                    "best_found_so_far": best_found,
                    "cumulative_cost": accounting.cumulative_cost,
                    "checkpoint_tally": dict(accounting.tally),
                }
            )
        else:
            st.complete = True
            n_complete += 1
            actual = truth[best_tid]
            best_found = max(best_found, actual)
            accounting.snapshot(n_complete=n_complete, best_found=best_found)
            steps.append(
                {
                    "step": step_idx,
                    "action": "complete_evaluation",
                    "trajectory_id": best_tid,
                    "stage_depth": st.stage_depth,
                    "pred_V": st.pred_v,
                    "actual_V": actual,
                    "n_complete": n_complete,
                    "best_found_so_far": best_found,
                    "cumulative_cost": accounting.cumulative_cost,
                    "checkpoint_tally": dict(accounting.tally),
                }
            )
            curve.append(
                {
                    "n_evaluated": n_complete,
                    "best_found": best_found,
                    "trajectory_id": best_tid,
                    "actual_V": actual,
                    "pred_V": st.pred_v,
                    "cumulative_cost": accounting.cumulative_cost,
                }
            )

    return {
        "strategy": "model_guided",
        "curve": curve,
        "steps": steps,
        "final_best": best_found,
        "checkpoint_accounting": accounting.to_dict(),
    }


def simulate_random_order(
    order: list[str],
    truth: dict[str, float],
    *,
    stage_costs: dict[str, float] | None = None,
) -> dict[str, Any]:
    costs = stage_costs or DEFAULT_STAGE_COSTS
    accounting = CheckpointAccounting(stage_costs=costs)
    best_found = 0.0
    curve: list[dict[str, Any]] = []
    for i, tid in enumerate(order, start=1):
        for stage in STAGE_LIST:
            accounting.observe(stage)
        actual = truth[tid]
        best_found = max(best_found, actual)
        accounting.snapshot(n_complete=i, best_found=best_found)
        curve.append(
            {
                "n_evaluated": i,
                "best_found": best_found,
                "trajectory_id": tid,
                "actual_V": actual,
                "cumulative_cost": accounting.cumulative_cost,
            }
        )
    return {
        "curve": curve,
        "final_best": best_found,
        "checkpoint_accounting": accounting.to_dict(),
    }


def summarize_cost_strategy(
    accountings: list[dict[str, Any]],
    optimum: float,
    *,
    name: str,
) -> dict[str, Any]:
    thresholds = {0.90: "cost_to_90pct", 0.95: "cost_to_95pct", 0.99: "cost_to_99pct"}
    out: dict[str, Any] = {
        "strategy": name,
        "n_runs": len(accountings),
        "true_optimum": optimum,
    }
    if len(accountings) == 1:
        out["checkpoint_accounting"] = accountings[0]
    else:
        tallies = [a["checkpoint_tally"] for a in accountings]
        out["checkpoint_tally_mean"] = {
            stage: float(np.mean([t[stage] for t in tallies])) for stage in STAGE_LIST
        }
        out["cumulative_cost_mean"] = float(np.mean([a["cumulative_cost"] for a in accountings]))
    for ratio, key in thresholds.items():
        vals = [
            cost_to_threshold(a["cost_curve"], ratio * optimum) for a in accountings
        ]
        vals_ok = [v for v in vals if v is not None]
        out[key] = {
            "mean": float(np.mean(vals_ok)) if vals_ok else None,
            "p50": float(np.median(vals_ok)) if vals_ok else None,
            "values": vals,
        }
    return out


def plot_best_vs_cost(
    random_runs: list[dict[str, Any]],
    model_accounting: dict[str, Any],
    optimum: float,
    out_path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    for run in random_runs[:50]:
        xs = [p["cumulative_cost"] for p in run["cost_curve"]]
        ys = [p["best_found"] for p in run["cost_curve"]]
        ax.plot(xs, ys, color="#94a3b8", alpha=0.15, linewidth=1)
    model_curve = model_accounting["cost_curve"]
    ax.plot(
        [p["cumulative_cost"] for p in model_curve],
        [p["best_found"] for p in model_curve],
        color="#2563eb",
        linewidth=2.5,
        label="model-guided",
    )
    ax.axhline(optimum, color="#16a34a", linestyle="--", linewidth=1.2, label=f"optimum ({optimum:.3f})")
    ax.set_xlabel("Cumulative checkpoint cost")
    ax.set_ylabel("Best actual PPA value found so far")
    ax.set_title("Search progress vs compute cost")
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def print_checkpoint_tally(label: str, accounting: dict[str, Any]) -> None:
    tally = accounting["checkpoint_tally"]
    costs = accounting["stage_costs"]
    print(f"\n{label} checkpoint tally:")
    print(f"  {'stage':<12} {'count':>8} {'unit_cost':>10} {'subtotal':>10}")
    for stage in STAGE_LIST:
        subtotal = tally[stage] * costs[stage]
        print(f"  {stage:<12} {tally[stage]:>8} {costs[stage]:>10.1f} {subtotal:>10.1f}")
    print(
        f"  {'TOTAL':<12} {accounting['total_checkpoints']:>8} "
        f"{'':>10} {accounting['cumulative_cost']:>10.1f}"
    )
    print(f"  (full run = {accounting['full_run_cost']:.1f} cost units)")


def curve_to_arrays(curve: list[dict[str, Any]], n_max: int) -> np.ndarray:
    """best_found[n] after n evaluations (1-indexed); pad with last value."""
    arr = np.zeros(n_max)
    by_n = {p["n_evaluated"]: p["best_found"] for p in curve}
    last = 0.0
    for i in range(1, n_max + 1):
        last = by_n.get(i, last)
        arr[i - 1] = last
    return arr


def evals_to_threshold(curve: list[dict[str, Any]], threshold: float) -> int | None:
    for p in curve:
        if p["best_found"] >= threshold:
            return p["n_evaluated"]
    return None


def auc_normalized(curve: list[dict[str, Any]], optimum: float, n: int) -> float:
    """Mean best-found / optimum over evaluation counts (1..n)."""
    if optimum <= 0:
        return float("nan")
    arr = curve_to_arrays(curve, n) / optimum
    return float(np.mean(arr))


def summarize_strategy(
    curves: list[list[dict[str, Any]]],
    optimum: float,
    n: int,
    *,
    name: str,
) -> dict[str, Any]:
    thresholds = {0.90: "evals_to_90pct", 0.95: "evals_to_95pct", 0.99: "evals_to_99pct"}
    arrays = np.array([curve_to_arrays(c, n) for c in curves])
    final_bests = arrays[:, -1]

    out: dict[str, Any] = {
        "strategy": name,
        "n_runs": len(curves),
        "true_optimum": optimum,
        "final_best_mean": float(np.mean(final_bests)),
        "final_best_std": float(np.std(final_bests)) if len(curves) > 1 else 0.0,
        "final_optimality_gap_mean": float(np.mean(optimum - final_bests)),
        "curve_mean": arrays.mean(axis=0).tolist(),
        "curve_p10": np.percentile(arrays, 10, axis=0).tolist(),
        "curve_p25": np.percentile(arrays, 25, axis=0).tolist(),
        "curve_p50": np.percentile(arrays, 50, axis=0).tolist(),
        "curve_p75": np.percentile(arrays, 75, axis=0).tolist(),
        "curve_p90": np.percentile(arrays, 90, axis=0).tolist(),
        "auc_mean_ratio": float(np.mean([auc_normalized(c, optimum, n) for c in curves])),
    }
    for ratio, key in thresholds.items():
        vals = [evals_to_threshold(c, ratio * optimum) for c in curves]
        vals_ok = [v for v in vals if v is not None]
        out[key] = {
            "mean": float(np.mean(vals_ok)) if vals_ok else None,
            "p50": float(np.median(vals_ok)) if vals_ok else None,
            "values": vals,
        }
    return out


def plot_best_vs_evals(
    random_summary: dict[str, Any],
    model_summary: dict[str, Any],
    model_curve: list[dict[str, Any]],
    optimum: float,
    out_path: Path,
) -> None:
    n = len(random_summary["curve_mean"])
    xs = np.arange(1, n + 1)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.fill_between(
        xs,
        random_summary["curve_p10"],
        random_summary["curve_p90"],
        alpha=0.2,
        color="#94a3b8",
        label="random p10–p90",
    )
    ax.fill_between(
        xs,
        random_summary["curve_p25"],
        random_summary["curve_p75"],
        alpha=0.3,
        color="#64748b",
        label="random p25–p75",
    )
    ax.plot(xs, random_summary["curve_mean"], color="#475569", linewidth=2, label="random mean")
    model_y = curve_to_arrays(model_curve, n)
    ax.plot(xs, model_y, color="#2563eb", linewidth=2.5, marker="o", markersize=4, label="model-guided")
    ax.axhline(optimum, color="#16a34a", linestyle="--", linewidth=1.2, label=f"optimum ({optimum:.3f})")

    ax.set_xlabel("Candidates fully evaluated")
    ax.set_ylabel("Best actual PPA value found so far")
    ax.set_title("GCD held-out search: model-guided vs random ordering")
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)
    ax.set_xlim(1, n)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_evals_to_95_hist(
    random_curves: list[list[dict[str, Any]]],
    model_curve: list[dict[str, Any]],
    optimum: float,
    out_path: Path,
) -> None:
    threshold = 0.95 * optimum
    random_evals = [evals_to_threshold(c, threshold) for c in random_curves]
    random_evals = [v for v in random_evals if v is not None]
    model_eval = evals_to_threshold(model_curve, threshold)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(random_evals, bins=range(1, len(model_curve) + 2), color="#94a3b8", edgecolor="white", alpha=0.85)
    if model_eval is not None:
        ax.axvline(model_eval, color="#2563eb", linewidth=2.5, label=f"model-guided ({model_eval})")
    ax.set_xlabel("Evaluations to reach 95% of optimum")
    ax.set_ylabel("Random permutation count")
    ax.set_title("Random search distribution vs model-guided")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_pred_vs_actual(model_curve: list[dict[str, Any]], out_path: Path) -> None:
    pred = [p["pred_V"] for p in model_curve if "pred_V" in p]
    act = [p["actual_V"] for p in model_curve if "actual_V" in p]
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.scatter(act, pred, alpha=0.8)
    ax.plot([0, 1], [0, 1], "--", color="gray")
    ax.set_xlabel("Actual final V (at completion)")
    ax.set_ylabel("Predicted V (at completion)")
    ax.set_title("Model-guided: predicted vs actual at full evaluation")
    ax.set_xlim(0, 1.05)
    ax.set_ylim(0, 1.05)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline search-ordering evaluation")
    parser.add_argument("--design", choices=sorted(DESIGNS), default="gcd")
    parser.add_argument("--n-random", type=int, default=1000, help="Random permutation runs")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Use only the first N trajectories from the manifest",
    )
    parser.add_argument(
        "--train-size",
        type=int,
        default=20,
        help="Number of trajectories for training (rest are test candidates)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Output directory (default: output/{design}/search_eval/split_{train}_{test})",
    )
    parser.add_argument(
        "--stage-costs",
        default="",
        help="Comma-separated stage costs, e.g. floorplan=2,placement=4,cts=2,routing=3",
    )
    args = parser.parse_args()

    stage_costs = parse_stage_costs(args.stage_costs) if args.stage_costs else DEFAULT_STAGE_COSTS

    spec = DESIGNS[args.design]
    trajectories = load_trajectories(args.design)
    if args.limit:
        trajectories = trajectories[: args.limit]
    tids = [t.trajectory_id for t in trajectories]
    n_manifest = len(tids)
    n_test_planned = n_manifest - args.train_size
    out_dir = args.out_dir or (
        EXP / "output" / spec.key / "search_eval" / f"split_{args.train_size}_{n_test_planned}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    runs = collect_completed_runs(FLOW, tids, platform=spec.platform, log_name=spec.log_name)
    targets = targets_from_batch(runs)
    df = build_dataset(trajectories, spec, targets)

    feature_cols = feature_columns(df, include_norm_pta=False, exclude_timing_proxies=False)
    feature_cache = build_prediction_cache(df, feature_cols)
    completed = set(df["trajectory_id"].unique())
    train_list, test_list_full = split_trajectories(tids, train_size=args.train_size)
    train_set = set(train_list) & completed
    test_list = sorted(set(test_list_full) & completed)
    split_mode = "manifest"

    min_train = max(2, args.train_size // 2)
    if len(train_set) < min_train:
        # Planned train IDs may not be finished yet (e.g. mega-sweep still running).
        completed_sorted = sorted(completed)
        train_list, test_list = split_trajectories(
            completed_sorted, train_size=args.train_size
        )
        train_set = set(train_list)
        split_mode = "completed_only"

    n_test = len(test_list)

    if len(train_set) < min_train:
        raise SystemExit(
            f"Only {len(train_set)}/{args.train_size} training trajectories complete; "
            f"need more data ({len(completed)} total complete)"
        )
    if len(test_list) < 8:
        raise SystemExit(f"Only {len(test_list)} test trajectories complete; need at least 8")

    models = {
        stage: train_stage_models(df, feature_cols, train_set, stage) for stage in STAGE_LIST
    }
    truth = load_test_truth(df, test_list)
    optimum = max(truth.values())

    rng = np.random.default_rng(args.seed)
    random_runs = []
    random_curves = []
    for _ in range(args.n_random):
        order = test_list.copy()
        rng.shuffle(order)
        run = simulate_random_order(order, truth, stage_costs=stage_costs)
        random_runs.append(run)
        random_curves.append(run["curve"])

    model_run = simulate_model_guided(
        test_list, models, feature_cache, truth, stage_costs=stage_costs
    )
    model_curve = model_run["curve"]
    model_accounting = model_run["checkpoint_accounting"]

    random_summary = summarize_strategy(random_curves, optimum, n_test, name="random")
    model_summary = summarize_strategy([model_curve], optimum, n_test, name="model_guided")
    random_cost_summary = summarize_cost_strategy(
        [r["checkpoint_accounting"] for r in random_runs], optimum, name="random"
    )
    model_cost_summary = summarize_cost_strategy(
        [model_accounting], optimum, name="model_guided"
    )

    report = {
        "disclaimer": (
            "Offline replay on completed trajectories. The optimiser uses predictions only; "
            "true final PPA is used for metrics. This is not counterfactual action-value prediction."
        ),
        "hypothesis": (
            "Can intermediate structural checkpoint predictions order a fixed candidate set "
            "so near-optimal designs are discovered faster than random search?"
        ),
        "design": args.design,
        "manifest_limit": args.limit or n_manifest,
        "train_size": args.train_size,
        "split_mode": split_mode,
        "n_train": len(train_set),
        "n_train_planned": len(train_list),
        "n_test_candidates": n_test,
        "n_test_planned": len(test_list_full),
        "n_completed_total": len(completed),
        "test_trajectories": test_list,
        "true_optimum": optimum,
        "optimum_trajectory": max(truth, key=truth.get),
        "n_random_permutations": args.n_random,
        "stage_costs": stage_costs,
        "random": random_summary,
        "random_cost": random_cost_summary,
        "model_guided": {
            **model_summary,
            "steps": model_run["steps"],
            "completion_order": model_curve,
            "checkpoint_accounting": model_accounting,
        },
        "model_guided_cost": model_cost_summary,
    }
    (out_dir / "search_eval.json").write_text(json.dumps(report, indent=2))

    plot_best_vs_evals(
        random_summary,
        model_summary,
        model_curve,
        optimum,
        out_dir / "best_vs_evaluations.png",
    )
    plot_evals_to_95_hist(random_curves, model_curve, optimum, out_dir / "evals_to_95pct.png")
    plot_pred_vs_actual(model_curve, out_dir / "pred_vs_actual_at_completion.png")
    plot_best_vs_cost(
        [r["checkpoint_accounting"] for r in random_runs],
        model_accounting,
        optimum,
        out_dir / "best_vs_cost.png",
    )

    print("\n=== Offline search-ordering evaluation (GCD held-out) ===")
    print(report["disclaimer"])
    print(f"\nStage costs: {stage_costs}")
    print(f"Optimum: {report['optimum_trajectory']}  V={optimum:.4f}")
    print(f"\n{'Strategy':<14} {'final best':>10} {'gap':>8} {'→90%':>6} {'→95%':>6} {'→99%':>6} {'AUC':>6}")
    for key, label in [("random", "random (mean)"), ("model_guided", "model-guided")]:
        s = report[key]
        e90 = s["evals_to_90pct"]["mean"]
        e95 = s["evals_to_95pct"]["mean"]
        e99 = s["evals_to_99pct"]["mean"]
        print(
            f"{label:<14} {s['final_best_mean']:>10.4f} {s['final_optimality_gap_mean']:>8.4f} "
            f"{e90:>6.1f} {e95:>6.1f} {e99:>6.1f} {s['auc_mean_ratio']:>6.3f}"
        )

    print(f"\n{'Strategy':<14} {'cost→90%':>10} {'cost→95%':>10} {'cost→99%':>10}")
    for key, label in [("random_cost", "random (mean)"), ("model_guided_cost", "model-guided")]:
        s = report[key]
        c90 = s["cost_to_90pct"]["mean"]
        c95 = s["cost_to_95pct"]["mean"]
        c99 = s["cost_to_99pct"]["mean"]
        print(
            f"{label:<14} "
            f"{c90 if c90 is not None else float('nan'):>10.1f} "
            f"{c95 if c95 is not None else float('nan'):>10.1f} "
            f"{c99 if c99 is not None else float('nan'):>10.1f}"
        )

    print_checkpoint_tally("Model-guided", model_accounting)
    print_checkpoint_tally(
        "Random (mean per run)",
        {
            "checkpoint_tally": random_cost_summary["checkpoint_tally_mean"],
            "stage_costs": stage_costs,
            "total_checkpoints": int(
                sum(random_cost_summary["checkpoint_tally_mean"].values())
            ),
            "cumulative_cost": random_cost_summary["cumulative_cost_mean"],
            "full_run_cost": sum(stage_costs[s] for s in STAGE_LIST),
        },
    )

    print("\nModel-guided completion order:")
    for p in model_curve:
        print(f"  #{p['n_evaluated']:2d}  {p['trajectory_id']:<18}  actual={p['actual_V']:.3f}  pred={p['pred_V']:.3f}")

    print(f"\nWrote {out_dir}/search_eval.json")
    print(f"Wrote {out_dir}/best_vs_evaluations.png")
    print(f"Wrote {out_dir}/best_vs_cost.png")
    print(f"Wrote {out_dir}/evals_to_95pct.png")


if __name__ == "__main__":
    main()
