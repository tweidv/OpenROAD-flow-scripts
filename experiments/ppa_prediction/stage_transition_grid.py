#!/usr/bin/env python3
"""R² grid: predict P/T/A at each target stage from each source stage (or params)."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from designs import DESIGNS, log_dir
from features import STAGES, extract_trajectory_features
from ppa_value import load_json
from run_trajectories import load_trajectories_from_manifest
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from splits import split_trajectories
from xgboost import XGBRegressor

EXP = Path(__file__).resolve().parent
OUT = EXP / "output" / "gcd" / "lhs250"

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

MODEL_PARAMS = {
    "n_estimators": 80,
    "max_depth": 4,
    "learning_rate": 0.1,
    "subsample": 0.9,
    "colsample_bytree": 0.9,
    "random_state": 42,
    "objective": "reg:squarederror",
    "n_jobs": 1,
}


def make_model() -> XGBRegressor:
    return XGBRegressor(**MODEL_PARAMS)


def train_eval(X_train, y_train, X_test, y_test):
    model = make_model()
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    metrics = {
        "mae": float(mean_absolute_error(y_test, pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_test, pred))),
        "r2": float(r2_score(y_test, pred)),
        "n_train": len(y_train),
        "n_test": len(y_test),
    }
    return model, metrics, pred


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

EXP = Path(__file__).resolve().parent
OUT = EXP / "output" / "gcd" / "lhs250"

SOURCES = ("params", *STAGES)
TARGET_STAGES = (*STAGES, "final")
METRICS = ("power", "fmax", "area")
CHECKPOINT_METRICS = ("power", "fmax", "area", "setup_ws")

STAGE_JSON = {
    "floorplan": "2_1_floorplan.json",
    "placement": "3_5_place_dp.json",
    "cts": "4_1_cts.json",
    "routing": "5_1_grt.json",
}

STAGE_ORDER = {s: i for i, s in enumerate(SOURCES)}
TARGET_ORDER = {s: i for i, s in enumerate(TARGET_STAGES)}

MANIFEST_PATHS = [
    EXP / "generated" / "gcd" / "trajectories_lhs250.json",
    EXP / "generated" / "gcd" / "trajectories_lhs_topup.json",
]


def load_lhs_manifest() -> dict[str, dict]:
    manifest: dict[str, dict] = {}
    for path in MANIFEST_PATHS:
        if not path.exists():
            continue
        for t in load_trajectories_from_manifest(path):
            manifest[t.trajectory_id] = t.params
    return manifest


def completed_lhs_ids(spec) -> list[str]:
    manifest = load_lhs_manifest()
    done = []
    for tid in manifest:
        if (log_dir(spec, tid) / "6_report.json").exists():
            done.append(tid)
    return sorted(done)


def load_wide_row_fixed(spec, tid: str, stage: str) -> dict[str, float]:
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
    data = load_json(log_dir(spec, tid) / STAGE_JSON[stage])
    row: dict[str, float] = {}
    for k, sk in suffix_map.items():
        val = data.get(sk)
        row[k] = float(val) if val not in (None, "N/A", "ERR") else np.nan
    return row


def param_columns(manifest: dict[str, dict]) -> list[str]:
    keys: set[str] = set()
    for params in manifest.values():
        keys.update(params.keys())
    return sorted(keys)


def build_trajectory_table(spec, tids: list[str], manifest: dict[str, dict]) -> pd.DataFrame:
    param_cols = param_columns(manifest)
    rows = []
    pta = load_final_pta(tids, spec)
    pta_idx = pta.set_index("trajectory_id")

    for tid in tids:
        if tid not in pta_idx.index:
            continue
        log = log_dir(spec, tid)
        params = manifest[tid]
        row: dict = {"trajectory_id": tid}
        for k in param_cols:
            row[f"param_{k}"] = params.get(k)

        fin = pta_idx.loc[tid]
        row["final_power"] = fin["final_power"]
        row["final_fmax"] = fin["final_fmax"]
        row["final_area"] = fin["final_area"]

        for stage in STAGES:
            ckpt = load_wide_row_fixed(spec, tid, stage)
            for m in CHECKPOINT_METRICS:
                row[f"{stage}__{m}"] = ckpt.get(m, np.nan)

            hand = {}
            for r in extract_trajectory_features(log, params, None):
                if r["stage"] == stage:
                    hand = {f: r.get(f, np.nan) for f in STAGE_FEATURES[stage]}
                    break
            for feat in STAGE_FEATURES[stage]:
                row[f"{stage}__hp__{feat}"] = hand.get(feat, np.nan)

        rows.append(row)

    return pd.DataFrame(rows)


def feature_columns(featureset: str, source: str) -> list[str]:
    if source == "params":
        raise ValueError("params columns resolved from dataframe")
    if featureset == "compact+fmax":
        return [f"{source}__{m}" for m in CHECKPOINT_METRICS]
    if featureset == "handpicked":
        return [f"{source}__hp__{f}" for f in STAGE_FEATURES[source]]
    raise ValueError(featureset)


def target_column(target: str, metric: str) -> str:
    if target == "final":
        return f"final_{metric}"
    return f"{target}__{metric}"


def transition_kind(source: str, target: str) -> str:
    si = STAGE_ORDER[source]
    ti = TARGET_ORDER[target]
    if si == ti:
        return "same"
    if si < ti:
        return "forward"
    return "backward"


def eval_grid(
    df: pd.DataFrame,
    param_cols: list[str],
    train_traj: list[str],
    test_traj: list[str],
) -> pd.DataFrame:
    results = []
    for featureset in ("compact+fmax", "handpicked"):
        for source in SOURCES:
            if source == "params":
                x_cols = param_cols
            else:
                x_cols = feature_columns(featureset, source)

            for target in TARGET_STAGES:
                for metric in METRICS:
                    y_col = target_column(target, metric)
                    sub = df.dropna(subset=[*x_cols, y_col])
                    tr = sub[sub["trajectory_id"].isin(train_traj)]
                    te = sub[sub["trajectory_id"].isin(test_traj)]
                    if len(tr) < 5 or len(te) < 2:
                        continue
                    _, m, _ = train_eval(
                        tr[x_cols].astype(float),
                        tr[y_col].astype(float),
                        te[x_cols].astype(float),
                        te[y_col].astype(float),
                    )
                    results.append(
                        {
                            "featureset": featureset,
                            "source": source,
                            "target": target,
                            "metric": metric,
                            "transition": transition_kind(source, target),
                            "test_R2": m["r2"],
                            "test_MAE": m["mae"],
                            "n_train": m["n_train"],
                            "n_test": m["n_test"],
                        }
                    )
    return pd.DataFrame(results)


def pivot_r2(res: pd.DataFrame, featureset: str, metric: str) -> pd.DataFrame:
    sub = res[(res.featureset == featureset) & (res.metric == metric)]
    table = sub.pivot(index="source", columns="target", values="test_R2")
    table = table.reindex(index=SOURCES, columns=TARGET_STAGES)
    return table


def save_heatmaps(res: pd.DataFrame, out_dir: Path) -> None:
    plot_dir = out_dir / "plots"
    plot_dir.mkdir(parents=True, exist_ok=True)
    for featureset in ("compact+fmax", "handpicked"):
        for metric in METRICS:
            table = pivot_r2(res, featureset, metric)
            if table.empty:
                continue
            fig, ax = plt.subplots(figsize=(6.5, 4.5))
            data = table.to_numpy(dtype=float)
            im = ax.imshow(data, vmin=0, vmax=1, cmap="viridis", aspect="auto")
            ax.set_xticks(range(len(TARGET_STAGES)))
            ax.set_xticklabels(TARGET_STAGES, rotation=30, ha="right")
            ax.set_yticks(range(len(SOURCES)))
            ax.set_yticklabels(SOURCES)
            ax.set_xlabel("Target stage")
            ax.set_ylabel("Source features")
            ax.set_title(f"{featureset} — test R² for {metric}")
            for i in range(data.shape[0]):
                for j in range(data.shape[1]):
                    val = data[i, j]
                    if np.isfinite(val):
                        ax.text(j, i, f"{val:.2f}", ha="center", va="center", color="white", fontsize=8)
            fig.colorbar(im, ax=ax, fraction=0.046)
            tag = featureset.replace("+", "_")
            fig.tight_layout()
            fig.savefig(plot_dir / f"transition_r2_{tag}_{metric}.png", dpi=150)
            plt.close(fig)


def write_report(
    res: pd.DataFrame,
    out_path: Path,
    *,
    n_complete: int,
    n_train: int,
    n_test: int,
) -> str:
    lines = [
        "# Stage transition prediction grid (LHS sweep)",
        "",
        f"**Completed trajectories:** {n_complete}",
        f"**Split:** {n_train} train / {n_test} test (seed 42, trajectory-level)",
        "",
        "Each cell: test-set R² predicting **target** power/fmax/area at column stage from **source**",
        "features at row stage. `params` = pre-floorplan ORFS knobs only (no OR metrics yet).",
        "",
        "Feature sets:",
        "- **compact+fmax** — checkpoint power, area, setup slack, fmax",
        "- **handpicked** — curated stage features from `feature_analysis.py` (includes `inv_fmax` at placement+)",
        "",
        "**Forward** = source earlier in flow than target. **Next step** = forward with distance 1.",
        "",
    ]

    next_pairs = [
        ("params", "floorplan"),
        ("floorplan", "placement"),
        ("placement", "cts"),
        ("cts", "routing"),
        ("routing", "final"),
    ]

    for featureset in ("compact+fmax", "handpicked"):
        lines.extend([f"## {featureset}", ""])
        for metric in METRICS:
            table = pivot_r2(res, featureset, metric)
            lines.append(f"### {metric}")
            lines.append("")
            header = "| source \\\\ target | " + " | ".join(TARGET_STAGES) + " |"
            sep = "|---|" + "|".join(["---:"] * len(TARGET_STAGES)) + "|"
            lines.extend([header, sep])
            for source in SOURCES:
                cells = []
                for target in TARGET_STAGES:
                    val = table.loc[source, target] if source in table.index and target in table.columns else np.nan
                    cells.append(f"{val:.3f}" if np.isfinite(val) else "—")
                lines.append(f"| {source} | " + " | ".join(cells) + " |")
            lines.append("")

        lines.extend(["### Next-step highlights", ""])
        lines.append("| Step | Power | Fmax | Area |")
        lines.append("|------|------:|-----:|-----:|")
        for src, tgt in next_pairs:
            cells = []
            for metric in METRICS:
                row = res[
                    (res.featureset == featureset)
                    & (res.source == src)
                    & (res.target == tgt)
                    & (res.metric == metric)
                ]
                cells.append(f"{row['test_R2'].iloc[0]:.3f}" if not row.empty else "—")
            lines.append(f"| {src} → {tgt} | " + " | ".join(cells) + " |")
        lines.extend(["", "### Predict final from each source", ""])
        lines.append("| Source | Power | Fmax | Area |")
        lines.append("|--------|------:|-----:|-----:|")
        for src in SOURCES:
            cells = []
            for metric in METRICS:
                row = res[
                    (res.featureset == featureset)
                    & (res.source == src)
                    & (res.target == "final")
                    & (res.metric == metric)
                ]
                cells.append(f"{row['test_R2'].iloc[0]:.3f}" if not row.empty else "—")
            lines.append(f"| {src} | " + " | ".join(cells) + " |")
        lines.append("")

    lines.extend(
        [
            "## Plots",
            "",
            "Heatmaps: `plots/transition_r2_compact_fmax_{power,fmax,area}.png` and `handpicked_*`.",
            "",
            "Full table: `stage_transition_grid.csv`.",
        ]
    )
    text = "\n".join(lines) + "\n"
    out_path.write_text(text)
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train-size", type=int, default=20)
    args = parser.parse_args()

    spec = DESIGNS["gcd"]
    manifest = load_lhs_manifest()
    tids = completed_lhs_ids(spec)
    if len(tids) <= args.train_size:
        raise SystemExit(f"Need >{args.train_size} completes, got {len(tids)}")

    df = build_trajectory_table(spec, tids, manifest)
    param_cols = [c for c in df.columns if c.startswith("param_")]
    train_traj, test_traj = split_trajectories(tids, train_size=args.train_size)

    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "stage_transition_dataset.csv", index=False)
    print(f"Built dataset: {len(df)} trajectories", flush=True)

    res = eval_grid(df, param_cols, train_traj, test_traj)
    print(f"Evaluated {len(res)} cells", flush=True)
    res.to_csv(OUT / "stage_transition_grid.csv", index=False)
    save_heatmaps(res, OUT)
    report = write_report(
        res,
        OUT / "stage_transition_report.md",
        n_complete=len(tids),
        n_train=len(train_traj),
        n_test=len(test_traj),
    )
    print(report)


if __name__ == "__main__":
    main()
