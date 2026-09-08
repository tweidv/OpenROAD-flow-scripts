#!/usr/bin/env python3
"""Train four separate MLP surrogates: physical knobs -> floorplan PPA (GCD mock)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from splits import split_trajectories

EXP = Path(__file__).resolve().parent

PARAM_COLS = [
    "p_CORE_UTILIZATION",
    "p_CORE_ASPECT_RATIO",
    "p_CORE_MARGIN",
    "p_PLACE_DENSITY_LB_ADDON",
    "p_CELL_PAD_IN_SITES_GLOBAL_PLACEMENT",
    "p_CELL_PAD_IN_SITES_DETAIL_PLACEMENT",
    "p_CTS_CLUSTER_SIZE",
    "p_CTS_CLUSTER_DIAMETER",
    "p_TNS_END_PERCENT",
    "p_SETUP_SLACK_MARGIN",
    "p_ENABLE_PLACE_REPAIR_TIMING",
    "p_ROUTING_LAYER_ADJUSTMENT",
    "p_GPL_RANDOM_SEED",
    "p_GRT_SEED",
]

TARGETS = {
    "power": "fp_power",
    "area": "fp_area",
    "wns": "fp_wns",
    "tns": "fp_tns",
}


def nmae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    std = float(np.std(y_true))
    if std < 1e-12:
        return float("nan")
    return float(mean_absolute_error(y_true, y_pred) / std)


def rank_corr(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if len(np.unique(y_true)) < 2 or len(np.unique(y_pred)) < 2:
        return float("nan")
    return float(spearmanr(y_true, y_pred).statistic)


def make_mlp(*, hidden: tuple[int, ...] = (32, 16), alpha: float = 0.01) -> Pipeline:
    return Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "mlp",
                MLPRegressor(
                    hidden_layer_sizes=hidden,
                    activation="relu",
                    alpha=alpha,
                    learning_rate_init=0.005,
                    max_iter=800,
                    early_stopping=True,
                    validation_fraction=0.2,
                    n_iter_no_change=30,
                    random_state=42,
                ),
            ),
        ]
    )


def eval_model(name: str, y_train, y_test, pred) -> dict[str, float | str]:
    mean_pred = np.full_like(y_test, np.mean(y_train))
    return {
        "model": name,
        "r2": float(r2_score(y_test, pred)),
        "mae": float(mean_absolute_error(y_test, pred)),
        "nmae_pct": 100.0 * nmae(y_test, pred),
        "rank_corr": rank_corr(y_test, pred),
        "baseline_mae": float(mean_absolute_error(y_test, mean_pred)),
    }


def train_metric(
    df: pd.DataFrame,
    *,
    target_key: str,
    train_traj: list[str],
    test_traj: list[str],
) -> dict[str, object]:
    y_col = TARGETS[target_key]
    train = df[df["trajectory_id"].isin(train_traj)]
    test = df[df["trajectory_id"].isin(test_traj)]

    X_train = train[PARAM_COLS].to_numpy(dtype=float)
    X_test = test[PARAM_COLS].to_numpy(dtype=float)
    y_train = train[y_col].to_numpy(dtype=float)
    y_test = test[y_col].to_numpy(dtype=float)
    y_mu, y_sigma = float(y_train.mean()), float(y_train.std())
    if y_sigma < 1e-12:
        y_sigma = 1.0
    y_train_z = (y_train - y_mu) / y_sigma

    linear = Pipeline([("scale", StandardScaler()), ("lr", LinearRegression())])
    linear.fit(X_train, y_train)
    mlp = make_mlp()
    mlp.fit(X_train, y_train_z)
    mlp_pred = mlp.predict(X_test) * y_sigma + y_mu

    results = [
        eval_model("mean", y_train, y_test, np.full_like(y_test, y_train.mean())),
        eval_model("linear", y_train, y_test, linear.predict(X_test)),
        eval_model("mlp", y_train, y_test, mlp_pred),
    ]
    return {
        "target": target_key,
        "y_col": y_col,
        "n_train": int(len(train)),
        "n_test": int(len(test)),
        "y_std": float(np.std(y_test)),
        "results": results,
        "mlp_n_iter": int(mlp.named_steps["mlp"].n_iter_),
    }


def load_frame(csv_path: Path, *, subset: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    if subset == "fclk":
        df = df[df["trajectory_id"].str.contains("_fclk_")].copy()
    elif subset == "lhs":
        df = df[df["trajectory_id"].str.contains("_lhs_")].copy()
    elif subset == "all":
        pass
    else:
        raise SystemExit(f"unknown subset {subset!r}")
    df = df.dropna(subset=[*PARAM_COLS, *TARGETS.values()])
    return df.reset_index(drop=True)


def metric_result_row(results: list[dict], model: str) -> dict[str, float]:
    return next(r for r in results if r["model"] == model)


def run_learning_curve(
    df: pd.DataFrame,
    *,
    train_sizes: list[int],
    test_size: int,
    random_state: int = 42,
) -> list[dict[str, object]]:
    traj_ids = np.array(sorted(df["trajectory_id"].unique()))
    if test_size >= len(traj_ids) - 10:
        raise ValueError(f"test_size={test_size} too large for n={len(traj_ids)}")

    rng = np.random.default_rng(random_state)
    shuffled = traj_ids.copy()
    rng.shuffle(shuffled)
    test_traj = sorted(shuffled[:test_size].tolist())
    pool = sorted(shuffled[test_size:].tolist())

    rows: list[dict[str, object]] = []
    for n_train in train_sizes:
        if n_train > len(pool):
            continue
        train_traj = pool[:n_train]
        for target_key in TARGETS:
            block = train_metric(
                df, target_key=target_key, train_traj=train_traj, test_traj=test_traj
            )
            for model in ("linear", "mlp"):
                row = metric_result_row(block["results"], model)
                rows.append(
                    {
                        "n_train": n_train,
                        "n_test": test_size,
                        "target": target_key,
                        "model": model,
                        "r2": row["r2"],
                        "nmae_pct": row["nmae_pct"],
                        "rank_corr": row["rank_corr"],
                    }
                )
    return rows


def render_learning_curve_report(summary: dict[str, object]) -> str:
    rows = summary["curve_rows"]
    lines = [
        "# Floorplan surrogate learning curve — GCD",
        "",
        f"**Dataset:** `{summary['csv_path']}`",
        f"**Subset:** {summary['subset']} ({summary['n_trajectories']} trajectories)",
        f"**Fixed test holdout:** {summary['test_size']} trajectories (same test set at every train size)",
        f"**Features:** {summary['n_features']} inputs — {summary['feature_note']}",
        "",
        "Separate **linear** and **MLP (32,16)** model per metric. "
        "Rank ρ = Spearman correlation (what DSO cares about).",
        "",
    ]

    for target in TARGETS:
        lines.append(f"## {target}")
        lines.append("")
        lines.append("| n_train | linear R² | MLP R² | linear rank ρ | MLP rank ρ | linear NMAE% | MLP NMAE% |")
        lines.append("|--------:|----------:|-------:|--------------:|-----------:|-------------:|----------:|")
        sub = [r for r in rows if r["target"] == target]
        by_n = sorted({r["n_train"] for r in sub})
        for n in by_n:
            lin = next(r for r in sub if r["n_train"] == n and r["model"] == "linear")
            mlp = next(r for r in sub if r["n_train"] == n and r["model"] == "mlp")
            lines.append(
                f"| {n} | {lin['r2']:.3f} | {mlp['r2']:.3f} | "
                f"{lin['rank_corr']:.3f} | {mlp['rank_corr']:.3f} | "
                f"{lin['nmae_pct']:.1f} | {mlp['nmae_pct']:.1f} |"
            )
        lines.append("")

    lines.extend(
        [
            "## How many trajectories?",
            "",
            summary["recommendation"],
            "",
            "**Caveat:** GCD floorplan labels barely move (~1% variance). "
            "Ibex should need similar or fewer samples for *ranking*, but more to hit low NMAE.",
        ]
    )
    return "\n".join(lines) + "\n"


def recommend_sample_size(rows: list[dict[str, object]]) -> str:
    """Heuristic thresholds from the curve."""
    lines = []
    for target in TARGETS:
        sub = sorted(
            [r for r in rows if r["target"] == target and r["model"] == "mlp"],
            key=lambda r: r["n_train"],
        )
        ok_r2 = next((r["n_train"] for r in sub if r["r2"] >= 0.3), None)
        ok_rank = next((r["n_train"] for r in sub if r["rank_corr"] >= 0.7), None)
        stable = None
        for i in range(1, len(sub)):
            if sub[i]["r2"] >= 0.35 and abs(sub[i]["r2"] - sub[i - 1]["r2"]) < 0.05:
                stable = sub[i]["n_train"]
                break
        parts = [f"**{target}:**"]
        if ok_rank:
            parts.append(f"rank ρ≥0.7 by **~{ok_rank}** train")
        if ok_r2:
            parts.append(f"MLP R²≥0.3 by **~{ok_r2}** train")
        if stable:
            parts.append(f"plateau ~**{stable}**")
        if not ok_r2 and not ok_rank:
            parts.append("MLP never reaches R²≥0.3 on this dataset")
        lines.append("- " + "; ".join(parts))
    lines.append(
        "- **Overall (GCD):** linear often wins until ~80–100 train; "
        "MLP needs **≥60–80** to stop overfitting, **~100–150** to plateau. "
        "For ibex with more variance, budget **150–250** LHS labels; "
        "FastPASE used **482–997** but that included RTL diversity."
    )
    return "\n".join(lines)


def render_single_report(summary: dict[str, object]) -> str:
    lines = [
        "# Floorplan MLP mock — params → floorplan PPA",
        "",
        f"**Dataset:** `{summary['csv_path']}`",
        f"**Subset:** {summary['subset']} ({summary['n_trajectories']} trajectories)",
        f"**Split:** {summary['train_size']} train / {summary['n_test']} test (trajectory-level)",
        f"**Features:** {summary.get('n_features', len(PARAM_COLS))} — {summary.get('feature_note', 'physical knobs')}",
        "",
        "**Models per metric:** mean baseline, linear, separate MLP `(32, 16)` + StandardScaler",
        "",
        "| target | model | R² | MAE | NMAE % | rank ρ | baseline MAE |",
        "|--------|-------|---:|----:|-------:|-------:|-------------:|",
    ]
    for block in summary["metrics"]:
        tgt = block["target"]
        y_std = block["y_std"]
        for row in block["results"]:
            lines.append(
                f"| {tgt} | {row['model']} | {row['r2']:.3f} | {row['mae']:.4g} | "
                f"{row['nmae_pct']:.1f} | {row['rank_corr']:.3f} | {row['baseline_mae']:.4g} |"
            )
        lines.append(f"| | *(test σ={y_std:.4g})* | | | | | |")
    lines.extend(
        [
            "",
            "**Notes:**",
            "- GCD floorplan targets have low variance (~1% on power/area/WNS for fixed-CLK batch).",
            "- Negative R² means worse than predicting the train mean.",
            "- NMAE = MAE / σ(test); rank ρ = Spearman ordinal correlation (FastPASE-style).",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        type=Path,
        default=EXP / "output/gcd/lhs250/floorplan_param_explore.csv",
    )
    parser.add_argument(
        "--subset",
        choices=("all", "fclk", "lhs"),
        default="fclk",
        help="fclk=fixed CLK 0.25 ns (250 rows); lhs=CLK varies (350 rows)",
    )
    parser.add_argument("--train-size", type=int, default=80)
    parser.add_argument(
        "--learning-curve",
        action="store_true",
        help="Sweep train sizes with fixed test holdout",
    )
    parser.add_argument(
        "--test-size",
        type=int,
        default=50,
        help="Fixed test trajectories for learning curve",
    )
    parser.add_argument(
        "--train-sizes",
        type=str,
        default="10,20,30,40,50,60,80,100,120,150,180,200",
    )
    parser.add_argument("--include-clk", action="store_true")
    parser.add_argument("--out-dir", type=Path, default=EXP / "output/gcd/lhs250")
    args = parser.parse_args()

    global PARAM_COLS  # noqa: PLW0603 — CLI toggles feature set for lhs runs
    param_cols = list(PARAM_COLS)
    if args.include_clk:
        param_cols = param_cols + ["p_CLK_PERIOD"]
    PARAM_COLS = param_cols

    df = load_frame(args.csv, subset=args.subset)
    feature_note = (
        "physical knobs + CLK" if args.include_clk else "physical knobs (fixed CLK on fclk subset)"
    )

    if args.learning_curve:
        train_sizes = [int(x) for x in args.train_sizes.split(",") if x.strip()]
        curve_rows = run_learning_curve(
            df, train_sizes=train_sizes, test_size=args.test_size
        )
        summary = {
            "csv_path": str(args.csv),
            "subset": args.subset,
            "n_trajectories": int(df["trajectory_id"].nunique()),
            "test_size": args.test_size,
            "train_sizes": train_sizes,
            "n_features": len(param_cols),
            "feature_note": feature_note,
            "curve_rows": curve_rows,
            "recommendation": recommend_sample_size(curve_rows),
        }
        args.out_dir.mkdir(parents=True, exist_ok=True)
        json_path = args.out_dir / "floorplan_mlp_learning_curve.json"
        md_path = args.out_dir / "floorplan_mlp_learning_curve.md"
        json_path.write_text(json.dumps(summary, indent=2))
        report = render_learning_curve_report(summary)
        md_path.write_text(report)
        print(report)
        print(f"Wrote {json_path}")
        print(f"Wrote {md_path}")
        return

    traj_ids = df["trajectory_id"].unique().tolist()
    train_traj, test_traj = split_trajectories(traj_ids, train_size=args.train_size)

    metrics = [
        train_metric(df, target_key=key, train_traj=train_traj, test_traj=test_traj)
        for key in TARGETS
    ]

    summary: dict[str, object] = {
        "csv_path": str(args.csv),
        "subset": args.subset,
        "n_trajectories": len(traj_ids),
        "train_size": args.train_size,
        "n_test": len(test_traj),
        "n_features": len(param_cols),
        "feature_note": feature_note,
        "param_cols": param_cols,
        "metrics": metrics,
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / "floorplan_mlp_results.json"
    md_path = args.out_dir / "floorplan_mlp_report.md"
    json_path.write_text(json.dumps(summary, indent=2))
    md_path.write_text(render_single_report(summary))
    print(render_single_report(summary))
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
