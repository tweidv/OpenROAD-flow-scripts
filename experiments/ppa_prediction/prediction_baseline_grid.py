#!/usr/bin/env python3
"""Best-predictor grid: power, area, WNS, TNS — next step and final.

Compares read-forward (same OR metric), linear compact, and XGB compact.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from xgboost import XGBRegressor

from designs import DESIGNS, log_dir
from ppa_value import load_json
from run_trajectories import load_trajectories_from_manifest
from splits import split_trajectories

EXP = Path(__file__).resolve().parent
OUT = EXP / "output" / "gcd" / "lhs250"

STAGES = ("floorplan", "placement", "cts", "routing")
SOURCES = ("params", *STAGES)
METRICS = ("power", "area", "wns", "tns")

NEXT_TARGET = {
    "params": "floorplan",
    "floorplan": "placement",
    "placement": "cts",
    "cts": "routing",
    "routing": "final",
}

STAGE_JSON = {
    "floorplan": "2_1_floorplan.json",
    "placement": "3_5_place_dp.json",
    "cts": "4_1_cts.json",
    "routing": "5_1_grt.json",
}

STAGE_SUFFIX = {
    "floorplan": {
        "power": "floorplan__power__internal__total",
        "area": "floorplan__design__instance__area",
        "wns": "floorplan__timing__setup__ws",
        "tns": "floorplan__timing__setup__tns",
    },
    "placement": {
        "power": "detailedplace__power__internal__total",
        "area": "detailedplace__design__instance__area",
        "wns": "detailedplace__timing__setup__ws",
        "tns": "detailedplace__timing__setup__tns",
    },
    "cts": {
        "power": "cts__power__internal__total",
        "area": "cts__design__instance__area",
        "wns": "cts__timing__setup__ws",
        "tns": "cts__timing__setup__tns",
    },
    "routing": {
        "power": "globalroute__power__internal__total",
        "area": "globalroute__design__instance__area",
        "wns": "globalroute__timing__setup__ws",
        "tns": "globalroute__timing__setup__tns",
    },
}

FINAL_SUFFIX = {
    "power": "finish__power__total",
    "area": "finish__design__instance__area__stdcell",
    "wns": "finish__timing__setup__ws",
    "tns": "finish__timing__setup__tns",
}

MANIFEST_PATHS = [
    EXP / "generated" / "gcd" / "trajectories_lhs250.json",
    EXP / "generated" / "gcd" / "trajectories_lhs_topup.json",
]

XGB_PARAMS = {
    "n_estimators": 80,
    "max_depth": 4,
    "learning_rate": 0.1,
    "subsample": 0.9,
    "colsample_bytree": 0.9,
    "random_state": 42,
    "n_jobs": 1,
}

GCD_BASE_CLK = 0.25


def load_manifest() -> dict[str, dict]:
    manifest: dict[str, dict] = {}
    for path in MANIFEST_PATHS:
        if not path.exists():
            continue
        for t in load_trajectories_from_manifest(path):
            manifest[t.trajectory_id] = t.params
    return manifest


def completed_ids(spec, manifest: dict[str, dict]) -> list[str]:
    return sorted(
        tid for tid in manifest if (log_dir(spec, tid) / "6_report.json").exists()
    )


def _fval(data: dict, key: str, alt: str | None = None) -> float:
    val = data.get(key)
    if val in (None, "N/A", "ERR") and alt:
        val = data.get(alt)
    if val in (None, "N/A", "ERR"):
        return np.nan
    return float(val)


def load_row(spec, tid: str, params: dict) -> dict:
    row: dict = {"trajectory_id": tid, "param_CLK_PERIOD": params.get("CLK_PERIOD")}
    for k, v in sorted(params.items()):
        row[f"param_{k}"] = v

    finish = load_json(log_dir(spec, tid) / "6_report.json")
    for m, sk in FINAL_SUFFIX.items():
        alt = "finish__design__instance__area" if m == "area" else None
        row[f"final__{m}"] = _fval(finish, sk, alt)

    for stage in STAGES:
        data = load_json(log_dir(spec, tid) / STAGE_JSON[stage])
        for m, sk in STAGE_SUFFIX[stage].items():
            row[f"{stage}__{m}"] = _fval(data, sk)
    return row


def target_col(target: str, metric: str) -> str:
    prefix = "final" if target == "final" else target
    return f"{prefix}__{metric}"


def eval_r2(model, X_tr, y_tr, X_te, y_te) -> float:
    model.fit(X_tr, y_tr)
    return float(r2_score(y_te, model.predict(X_te)))


def run_grid(
    df: pd.DataFrame,
    param_cols: list[str],
    train_traj: list[str],
    test_traj: list[str],
) -> pd.DataFrame:
    rows = []
    methods = ("read_forward", "linear_compact", "xgb_compact")

    for source in SOURCES:
        for horizon, target in (("next", NEXT_TARGET[source]), ("final", "final")):
            for metric in METRICS:
                ycol = target_col(target, metric)
                rf_col = None if source == "params" else f"{source}__{metric}"

                if source == "params":
                    x_linear = param_cols
                else:
                    x_linear = [f"{source}__{m}" for m in METRICS]

                sub = df.dropna(subset=[ycol])
                if source != "params":
                    sub = sub.dropna(subset=x_linear)
                else:
                    sub = sub.dropna(subset=param_cols)

                tr = sub[sub.trajectory_id.isin(train_traj)]
                te = sub[sub.trajectory_id.isin(test_traj)]
                if len(tr) < 5 or len(te) < 2:
                    continue

                y_tr, y_te = tr[ycol].astype(float), te[ycol].astype(float)

                scores: dict[str, float] = {}
                if rf_col and rf_col in sub.columns:
                    rf_sub = sub.dropna(subset=[rf_col, ycol])
                    tr_rf = rf_sub[rf_sub.trajectory_id.isin(train_traj)]
                    te_rf = rf_sub[rf_sub.trajectory_id.isin(test_traj)]
                    if len(tr_rf) >= 5 and len(te_rf) >= 2:
                        scores["read_forward"] = eval_r2(
                            LinearRegression(),
                            tr_rf[[rf_col]],
                            tr_rf[ycol].astype(float),
                            te_rf[[rf_col]],
                            te_rf[ycol].astype(float),
                        )

                if source == "params" or all(c in sub.columns for c in x_linear):
                    tr_x = tr[x_linear].astype(float)
                    te_x = te[x_linear].astype(float)
                    scores["linear_compact"] = eval_r2(
                        LinearRegression(), tr_x, y_tr, te_x, y_te
                    )
                    scores["xgb_compact"] = eval_r2(
                        XGBRegressor(**XGB_PARAMS), tr_x, y_tr, te_x, y_te
                    )

                for method in methods:
                    if method not in scores:
                        continue
                    rows.append(
                        {
                            "source": source,
                            "horizon": horizon,
                            "target": target,
                            "metric": metric,
                            "method": method,
                            "test_R2": scores[method],
                            "n_train": len(tr),
                            "n_test": len(te),
                        }
                    )
    return pd.DataFrame(rows)


def best_method_table(res: pd.DataFrame, horizon: str) -> pd.DataFrame:
    """Per source×metric, which method wins."""
    sub = res[res.horizon == horizon].copy()
    if sub.empty:
        return sub
    idx = sub.groupby(["source", "metric"])["test_R2"].idxmax()
    best = sub.loc[idx].copy()
    best = best.sort_values(["source", "metric"])
    return best


def write_report(
    res: pd.DataFrame,
    res_fixed: pd.DataFrame | None,
    out_path: Path,
    *,
    n_all: int,
    n_fixed: int,
    n_train: int,
    n_test: int,
) -> str:
    lines = [
        "# Prediction baseline grid — power, area, WNS, TNS",
        "",
        f"**All CLK (LHS sweep):** {n_all} completes, {n_train} train / {n_test} test",
    ]
    if n_fixed:
        lines.append(
            f"**Fixed CLK ≈ {GCD_BASE_CLK} ns (±5%):** {n_fixed} completes (same split pool)"
        )
    lines.extend(
        [
            "",
            "**Targets:** power (`internal__total` checkpoint / `power__total` finish),",
            "area (`instance__area`), WNS (`timing__setup__ws`), TNS (`timing__setup__tns`).",
            "",
            "**Methods:**",
            "- `read_forward` — linear fit using **same metric** at source only",
            "- `linear_compact` — linear on source `[power, area, wns, tns]` (or params if pre-floorplan)",
            "- `xgb_compact` — XGBoost on same features (often worse for read-forward metrics)",
            "",
            f"GCD baseline CLK in `designs.py`: **{GCD_BASE_CLK} ns**. LHS sweep varies CLK intentionally;",
            "dashboard/tapeout use fixed CLK — see fixed-CLK section below.",
            "",
            "**Floorplan cost:** ~2/11 of relative full-flow cost in search models (cheap vs placement=4, routing=3).",
            "",
        ]
    )

    def section(res_df: pd.DataFrame, title: str) -> None:
        if res_df.empty:
            lines.append(f"## {title}\n\n_(no data)_\n")
            return
        lines.extend([f"## {title}", ""])
        for horizon, label in (("next", "Next step"), ("final", "At finish")):
            lines.extend([f"### {label}", ""])
            for method in ("read_forward", "linear_compact", "xgb_compact"):
                sub = res_df[(res_df.horizon == horizon) & (res_df.method == method)]
                if sub.empty:
                    continue
                lines.append(f"#### {method}")
                lines.append("")
                lines.append("| source → target | power | area | wns | tns |")
                lines.append("|-----------------|------:|-----:|----:|----:|")
                for source in SOURCES:
                    target = NEXT_TARGET[source] if horizon == "next" else "final"
                    cells = []
                    for metric in METRICS:
                        row = sub[
                            (sub.source == source)
                            & (sub.metric == metric)
                        ]
                        cells.append(
                            f"{row['test_R2'].iloc[0]:.3f}" if not row.empty else "—"
                        )
                    lines.append(
                        f"| {source} → {target} | " + " | ".join(cells) + " |"
                    )
                lines.append("")

        lines.extend(["### Best method per cell", ""])
        lines.append("| source | horizon | metric | best | R² |")
        lines.append("|--------|---------|--------|------|---:|")
        for horizon in ("next", "final"):
            best = best_method_table(res_df, horizon)
            for _, r in best.iterrows():
                tgt = NEXT_TARGET[r.source] if horizon == "next" else "final"
                lines.append(
                    f"| {r.source} → {tgt} | {horizon} | {r.metric} | **{r.method}** | {r.test_R2:.3f} |"
                )
        lines.append("")

    section(res, "Full LHS sweep (CLK varies)")
    if res_fixed is not None and not res_fixed.empty:
        section(res_fixed, f"Fixed CLK subset (|CLK − {GCD_BASE_CLK}| ≤ 5%)")

    lines.extend(
        [
            "## How OpenROAD computes these (same call every stage)",
            "",
            "ORFS `report_metrics` → OpenROAD STA/power/area hooks (`tools/OpenROAD/src/Metrics.tcl`):",
            "",
            "| Metric | OR function | Meaning |",
            "|--------|-------------|---------|",
            "| **power** | `design_power` → `power__internal__total` | Switching + internal from current netlist/parasitics |",
            "| **area** | `report_design_area_metrics` | Sum of instance areas |",
            "| **WNS** | `worst_slack -max` → `timing__setup__ws` | Worst setup slack (negative = violated) |",
            "| **TNS** | `total_negative_slack -max` → `timing__setup__tns` | Sum of negative slacks |",
            "",
            "Each stage re-runs STA on the **current netlist** with the **same SDC clock period**.",
            "Late-stage WNS/TNS ≈ finish because little changes after GRT.",
            "",
            "CSV: `prediction_baseline_grid.csv` · plots: `plots/prediction_baseline_*.png`",
        ]
    )
    text = "\n".join(lines) + "\n"
    out_path.write_text(text)
    return text


def save_plots(res: pd.DataFrame, tag: str, out_dir: Path) -> None:
    plot_dir = out_dir / "plots"
    plot_dir.mkdir(parents=True, exist_ok=True)
    for horizon in ("next", "final"):
        for method in ("read_forward", "linear_compact"):
            sub = res[(res.horizon == horizon) & (res.method == method)]
            if sub.empty:
                continue
            table = sub.pivot_table(
                index="source", columns="metric", values="test_R2", aggfunc="first"
            )
            table = table.reindex(index=SOURCES, columns=METRICS)
            fig, ax = plt.subplots(figsize=(5, 4))
            data = table.to_numpy(dtype=float)
            im = ax.imshow(data, vmin=0, vmax=1, cmap="viridis", aspect="auto")
            ax.set_xticks(range(len(METRICS)))
            ax.set_xticklabels(METRICS)
            ax.set_yticks(range(len(SOURCES)))
            ax.set_yticklabels(SOURCES)
            tgt = "next step" if horizon == "next" else "finish"
            ax.set_title(f"{tag} {method} → {tgt}")
            for i in range(data.shape[0]):
                for j in range(data.shape[1]):
                    v = data[i, j]
                    if np.isfinite(v):
                        ax.text(j, i, f"{v:.2f}", ha="center", va="center", color="white", fontsize=8)
            fig.colorbar(im, ax=ax, fraction=0.046)
            fig.tight_layout()
            fig.savefig(plot_dir / f"prediction_baseline_{tag}_{horizon}_{method}.png", dpi=150)
            plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train-size", type=int, default=20)
    parser.add_argument("--clk-tol", type=float, default=0.05, help="Fixed CLK band as fraction")
    args = parser.parse_args()

    spec = DESIGNS["gcd"]
    manifest = load_manifest()
    tids = completed_ids(spec, manifest)
    if len(tids) <= args.train_size:
        raise SystemExit(f"Need >{args.train_size} completes, got {len(tids)}")

    rows = [load_row(spec, tid, manifest[tid]) for tid in tids]
    df = pd.DataFrame(rows)
    param_cols = [c for c in df.columns if c.startswith("param_")]

    train_traj, test_traj = split_trajectories(tids, train_size=args.train_size)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "prediction_baseline_dataset.csv", index=False)

    res = run_grid(df, param_cols, train_traj, test_traj)
    res["clk_filter"] = "all"
    res.to_csv(OUT / "prediction_baseline_grid.csv", index=False)

    tol = GCD_BASE_CLK * args.clk_tol
    fixed = df[df.param_CLK_PERIOD.between(GCD_BASE_CLK - tol, GCD_BASE_CLK + tol)]
    fixed_tids = sorted(fixed.trajectory_id.unique())
    res_fixed = pd.DataFrame()
    if len(fixed_tids) > args.train_size + 2:
        tr_f, te_f = split_trajectories(fixed_tids, train_size=min(args.train_size, len(fixed_tids) - 2))
        res_fixed = run_grid(fixed, param_cols, tr_f, te_f)
        res_fixed["clk_filter"] = "fixed"
        res_fixed.to_csv(OUT / "prediction_baseline_grid_fixed_clk.csv", index=False)

    save_plots(res, "all", OUT)
    if not res_fixed.empty:
        save_plots(res_fixed, "fixed_clk", OUT)

    report = write_report(
        res,
        res_fixed if not res_fixed.empty else None,
        OUT / "prediction_baseline_report.md",
        n_all=len(tids),
        n_fixed=len(fixed_tids),
        n_train=len(train_traj),
        n_test=len(test_traj),
    )
    print(report)


if __name__ == "__main__":
    main()
