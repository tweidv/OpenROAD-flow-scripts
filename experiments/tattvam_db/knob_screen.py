#!/usr/bin/env python3
"""Screen ORFS knobs using the local Tattvam SQLite mirror.

Standalone from PPA prediction / surrogate training. Two gates only:

  1. Stage reach — does this knob affect the checkpoint stage we care about?
  2. Label sensitivity — when the knob varies, does the metric move (Spearman ρ)?

Data source: experiments/tattvam_db/data/tattvam.sqlite (dashboard API sync).

Usage:
    python3 experiments/tattvam_db/knob_screen.py
    python3 experiments/tattvam_db/knob_screen.py --design gcd --stage floorplan
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from knob_stage_map import (
    DEFAULT_METRICS,
    KNOB_FIRST_STAGE,
    NON_NUMERIC_KNOBS,
    STAGE_ORDER,
    VERDICT_CODE,
    VERDICT_FROM_RANK,
    VERDICT_RANK,
    knob_reaches_stage,
    metrics_for_stage,
)

HERE = Path(__file__).resolve().parent
DEFAULT_DB = HERE / "data" / "tattvam.sqlite"
DEFAULT_OUT = HERE / "output"


def parse_numeric_series(values: pd.Series) -> pd.Series:
    """Best-effort float parse; non-numeric → NaN."""
    return pd.to_numeric(values, errors="coerce")


def load_designs(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT DISTINCT design FROM runs ORDER BY design"
    ).fetchall()
    return [r[0] for r in rows]


def load_params(conn: sqlite3.Connection, design: str | None) -> pd.DataFrame:
    sql = """
        SELECT r.design, cp.run_id, cp.candidate_id, cp.param, cp.value
        FROM candidate_params cp
        JOIN runs r ON r.run_id = cp.run_id
    """
    args: tuple = ()
    if design:
        sql += " WHERE r.design = ?"
        args = (design,)
    df = pd.read_sql_query(sql, conn, params=args)
    df["value_num"] = parse_numeric_series(df["value"])
    return df


def load_metrics(
    conn: sqlite3.Connection,
    design: str | None,
    stages: list[str],
    metrics: list[str],
) -> pd.DataFrame:
    stage_placeholders = ",".join("?" for _ in stages)
    metric_placeholders = ",".join("?" for _ in metrics)
    sql = f"""
        SELECT r.design, m.run_id, m.candidate_id, m.stage, m.metric, m.value_num
        FROM metrics m
        JOIN runs r ON r.run_id = m.run_id
        WHERE m.stage IN ({stage_placeholders})
          AND m.metric IN ({metric_placeholders})
          AND m.value_num IS NOT NULL
    """
    args: tuple = (*stages, *metrics)
    if design:
        sql += " AND r.design = ?"
        args = (*args, design)
    return pd.read_sql_query(sql, conn, params=args)


def sensitivity_row(
    design: str,
    stage: str,
    metric: str,
    param: str,
    pairs: pd.DataFrame,
) -> dict:
    gate1 = knob_reaches_stage(param, stage)
    numeric_ok = param not in NON_NUMERIC_KNOBS

    sub = pairs.dropna(subset=["param_val", "metric_val"])
    n = len(sub)
    param_nuniq = int(sub["param_val"].nunique()) if n else 0
    metric_nuniq = int(sub["metric_val"].nunique()) if n else 0

    metric_cv = np.nan
    if n >= 2:
        mu = sub["metric_val"].mean()
        if mu != 0:
            metric_cv = 100.0 * float(sub["metric_val"].std(ddof=1) / abs(mu))

    rho = np.nan
    pearson_r = np.nan
    if numeric_ok and n >= 10 and param_nuniq >= 3 and metric_nuniq >= 2:
        rho, _ = spearmanr(sub["param_val"], sub["metric_val"])
        pearson_r = float(np.corrcoef(sub["param_val"], sub["metric_val"])[0, 1])

    # Gate 2 verdict (informational labels only).
    if not gate1:
        gate2 = "wrong_stage"
    elif not numeric_ok:
        gate2 = "non_numeric"
    elif param_nuniq < 3:
        gate2 = "param_flat"
    elif metric_nuniq < 2:
        gate2 = "label_flat"
    elif np.isnan(rho) or abs(rho) < 0.08:
        gate2 = "insensitive"
    elif abs(rho) < 0.15:
        gate2 = "weak"
    elif abs(rho) < 0.30:
        gate2 = "moderate"
    else:
        gate2 = "strong"

    return {
        "design": design,
        "stage": stage,
        "metric": metric,
        "param": param,
        "knob_first_stage": KNOB_FIRST_STAGE.get(param, ""),
        "gate1_reaches_stage": int(gate1),
        "gate2_verdict": gate2,
        "n": n,
        "param_nunique": param_nuniq,
        "metric_nunique": metric_nuniq,
        "metric_cv_pct": metric_cv,
        "spearman_rho": rho,
        "pearson_r": pearson_r,
    }


def screen_design(
    params: pd.DataFrame,
    metrics: pd.DataFrame,
    design: str,
    stages: list[str],
) -> pd.DataFrame:
    rows: list[dict] = []
    psub = params[params["design"] == design]
    msub = metrics[metrics["design"] == design]

    all_params = sorted(psub["param"].unique())

    for stage in stages:
        stage_metrics = [m for m in metrics_for_stage(stage) if m in msub["metric"].unique()]
        if not stage_metrics:
            continue
        for metric in stage_metrics:
            mmetric = msub[(msub["stage"] == stage) & (msub["metric"] == metric)]
            if mmetric.empty:
                continue
            base = mmetric[["run_id", "candidate_id", "value_num"]].rename(
                columns={"value_num": "metric_val"}
            )
            for param in all_params:
                pparam = psub[psub["param"] == param][
                    ["run_id", "candidate_id", "value_num"]
                ].rename(columns={"value_num": "param_val"})
                pairs = base.merge(pparam, on=["run_id", "candidate_id"], how="inner")
                rows.append(
                    sensitivity_row(design, stage, metric, param, pairs)
                )
    return pd.DataFrame(rows)


def summarize_keepers(df: pd.DataFrame, stage: str, metric: str) -> pd.DataFrame:
    sub = df[(df["stage"] == stage) & (df["metric"] == metric)].copy()
    sub = sub[sub["gate1_reaches_stage"] == 1]
    sub = sub[sub["gate2_verdict"].isin(["weak", "moderate", "strong"])]
    sub = sub.sort_values("spearman_rho", key=lambda s: s.abs(), ascending=False)
    return sub


def aggregate_param_design_stage(df: pd.DataFrame) -> pd.DataFrame:
    """Best verdict across all metrics for each param × design × stage."""
    rows: list[dict] = []
    grouped = df.groupby(["param", "design", "stage"], sort=True)
    for (param, design, stage), g in grouped:
        best_rank = -1
        best_verdict = "insensitive"
        best_rho = np.nan
        best_pearson = np.nan
        best_metric = ""
        for _, r in g.iterrows():
            v = r["gate2_verdict"]
            rank = VERDICT_RANK.get(v, -1)
            if rank > best_rank:
                best_rank = rank
                best_verdict = v
                best_rho = r["spearman_rho"]
                best_pearson = r["pearson_r"]
                best_metric = r["metric"]
            elif rank == best_rank:
                if pd.notna(r["spearman_rho"]) and (
                    pd.isna(best_rho) or abs(r["spearman_rho"]) > abs(best_rho)
                ):
                    best_rho = r["spearman_rho"]
                    best_pearson = r["pearson_r"]
                    best_metric = r["metric"]
        rows.append(
            {
                "param": param,
                "design": design,
                "stage": stage,
                "knob_first_stage": KNOB_FIRST_STAGE.get(param, ""),
                "verdict": best_verdict,
                "verdict_rank": best_rank,
                "verdict_code": VERDICT_CODE.get(best_verdict, "?"),
                "best_spearman_rho": best_rho,
                "best_pearson_r": best_pearson,
                "best_metric": best_metric,
                "matters": best_verdict in ("weak", "moderate", "strong"),
            }
        )
    return pd.DataFrame(rows)


def build_summary_pivot(agg: pd.DataFrame, designs: list[str]) -> pd.DataFrame:
    """Wide grid: rows=param, cols=design@stage, values=verdict_code."""
    cols: list[str] = []
    for design in designs:
        for stage in STAGE_ORDER:
            cols.append(f"{design}@{stage}")
    params = sorted(agg["param"].unique())
    rows: list[dict] = []
    for param in params:
        row: dict = {"param": param, "knob_first_stage": KNOB_FIRST_STAGE.get(param, "")}
        sub = agg[agg["param"] == param]
        for design in designs:
            for stage in STAGE_ORDER:
                col = f"{design}@{stage}"
                hit = sub[(sub["design"] == design) & (sub["stage"] == stage)]
                if hit.empty:
                    row[col] = "—"
                else:
                    row[col] = hit.iloc[0]["verdict_code"]
        # Any design weak+ at any stage?
        matters_any = sub[sub["matters"]]
        row["stages_with_signal"] = ",".join(
            sorted({f"{r.design}@{r.stage}" for r in matters_any.itertuples()})
        )
        row["n_design_stage_hits"] = int(matters_any[["design", "stage"]].drop_duplicates().shape[0])
        rows.append(row)
    return pd.DataFrame(rows)


def knobs_matter_by_stage(agg: pd.DataFrame, designs: list[str]) -> dict[str, list[str]]:
    """Knobs with weak+ on at least one design at this stage."""
    out: dict[str, list[str]] = {}
    for stage in STAGE_ORDER:
        sub = agg[(agg["stage"] == stage) & agg["matters"]]
        params = sorted(sub["param"].unique())
        out[stage] = params
    return out


def stage_exclude_and_rank(agg: pd.DataFrame, designs: list[str]) -> pd.DataFrame:
    """Per stage: exclude counts + weak+ knobs ranked by max |Pearson| across designs."""
    all_params = sorted(agg["param"].unique())
    n_total = len(all_params)
    rows: list[dict] = []

    for stage in STAGE_ORDER:
        stage_agg = agg[agg["stage"] == stage]
        keep_params = sorted(stage_agg[stage_agg["matters"]]["param"].unique())
        n_keep = len(keep_params)
        n_exclude = n_total - n_keep

        ranked: list[tuple[str, float, str, str, str]] = []
        for param in keep_params:
            hits = stage_agg[(stage_agg["param"] == param) & stage_agg["matters"]]
            best_idx = hits["best_pearson_r"].abs().idxmax()
            best_row = hits.loc[best_idx]
            ranked.append(
                (
                    param,
                    float(best_row["best_pearson_r"]),
                    best_row["design"],
                    best_row["best_metric"],
                    best_row["verdict"],
                )
            )
        ranked.sort(key=lambda x: abs(x[1]), reverse=True)

        for rank, (param, pearson, design, metric, verdict) in enumerate(ranked, 1):
            rows.append(
                {
                    "stage": stage,
                    "n_total_knobs": n_total,
                    "n_keep_weak_plus": n_keep,
                    "n_exclude": n_exclude,
                    "rank": rank,
                    "param": param,
                    "max_pearson_r": pearson,
                    "abs_max_pearson_r": abs(pearson),
                    "best_design": design,
                    "best_metric": metric,
                    "best_verdict": verdict,
                }
            )
        if not ranked:
            rows.append(
                {
                    "stage": stage,
                    "n_total_knobs": n_total,
                    "n_keep_weak_plus": 0,
                    "n_exclude": n_exclude,
                    "rank": np.nan,
                    "param": "",
                    "max_pearson_r": np.nan,
                    "abs_max_pearson_r": np.nan,
                    "best_design": "",
                    "best_metric": "",
                    "best_verdict": "",
                }
            )
    return pd.DataFrame(rows)


def write_stage_ranking(agg: pd.DataFrame, designs: list[str], out_dir: Path) -> None:
    ranking = stage_exclude_and_rank(agg, designs)
    ranking.to_csv(out_dir / "knob_stage_ranking.csv", index=False)

    all_params = sorted(agg["param"].unique())
    n_total = len(all_params)
    lines = [
        "# Per-stage exclude counts & weak+ ranking (max |Pearson|)",
        "",
        f"Total knobs in DB: **{n_total}**",
        "",
        "A knob is **kept** if it is weak/moderate/strong (|Spearman ρ| ≥ 0.08) on "
        "≥1 design at that stage (best across metrics). Ranking uses **max |Pearson r|** "
        "across gcd/aes/jpeg at that stage.",
        "",
    ]

    for stage in STAGE_ORDER:
        block = ranking[ranking["stage"] == stage]
        if block.empty:
            continue
        n_keep = int(block.iloc[0]["n_keep_weak_plus"])
        n_exclude = int(block.iloc[0]["n_exclude"])
        lines += [
            f"## {stage}",
            "",
            f"- **Keep (weak+):** {n_keep} knobs",
            f"- **Exclude:** {n_exclude} knobs ({100 * n_exclude / n_total:.0f}% of {n_total})",
            "",
        ]
        ranked = block[block["param"] != ""].sort_values("abs_max_pearson_r", ascending=False)
        if ranked.empty:
            lines.append("_No weak+ knobs at this stage._")
        else:
            lines += [
                "| rank | knob | max Pearson r | design | metric | verdict |",
                "|-----:|------|--------------:|--------|--------|---------|",
            ]
            for _, r in ranked.iterrows():
                lines.append(
                    f"| {int(r['rank'])} | {r['param']} | {r['max_pearson_r']:+.3f} | "
                    f"{r['best_design']} | {r['best_metric']} | {r['best_verdict']} |"
                )
        lines.append("")

        # List excluded knobs
        keep_set = set(ranked["param"].tolist())
        excluded = [p for p in all_params if p not in keep_set]
        if excluded:
            lines.append(f"**Excluded @ {stage}** ({len(excluded)}): " + ", ".join(f"`{p}`" for p in excluded))
            lines.append("")

    path = out_dir / "knob_stage_ranking.md"
    path.write_text("\n".join(lines))
    print(f"Wrote {out_dir / 'knob_stage_ranking.csv'}")
    print(f"Wrote {path}")


def write_grid_outputs(
    df: pd.DataFrame,
    agg: pd.DataFrame,
    pivot: pd.DataFrame,
    out_dir: Path,
    designs: list[str],
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    agg.to_csv(out_dir / "knob_grid_agg.csv", index=False)
    pivot.to_csv(out_dir / "knob_grid_summary.csv", index=False)
    write_stage_ranking(agg, designs, out_dir)

    # Long detail already in knob_screen_all.csv
    matter = knobs_matter_by_stage(agg, designs)

    lines = [
        "# Knob grid — all designs × all stages",
        "",
        "Source: Tattvam SQLite. Cell = **best verdict** across all metrics at that "
        "design+stage (highest of wns/tns/power/util/fmax/area/…).",
        "",
        "See also: `knob_stage_ranking.md` — exclude counts + weak+ knobs by max |Pearson|.",
        "",
        "## Codes",
        "",
        "| Code | Verdict |",
        "|------|---------|",
        "| S | strong (\\|ρ\\| ≥ 0.30) |",
        "| M | moderate (0.15–0.30) |",
        "| W | weak (0.08–0.15) |",
        "| I | insensitive (\\|ρ\\| < 0.08) |",
        "| WS | wrong_stage (Gate 1) |",
        "| PF | param_flat (< 3 unique values) |",
        "| LF | label_flat |",
        "| NN | non_numeric |",
        "| — | no data |",
        "",
        "Full numeric detail: `knob_grid_agg.csv`, `knob_screen_all.csv`.",
        "",
    ]

    for stage in STAGE_ORDER:
        lines += [f"## {stage}", ""]
        stage_params = sorted(agg[agg["stage"] == stage]["param"].unique())
        header = "| knob | " + " | ".join(designs) + " | any weak+ |"
        sep = "|------|" + "|".join(["------"] * len(designs)) + "|---------|"
        lines += [header, sep]
        for param in stage_params:
            cells = []
            any_hit = False
            for design in designs:
                hit = agg[
                    (agg["param"] == param)
                    & (agg["design"] == design)
                    & (agg["stage"] == stage)
                ]
                if hit.empty:
                    cells.append("—")
                else:
                    code = hit.iloc[0]["verdict_code"]
                    cells.append(code)
                    if hit.iloc[0]["matters"]:
                        any_hit = True
            flag = "yes" if any_hit else ""
            lines.append(f"| {param} | " + " | ".join(cells) + f" | {flag} |")
        lines.append("")
        if matter[stage]:
            lines.append(
                f"**Knobs with signal (weak+) on ≥1 design @ {stage}:** "
                + ", ".join(f"`{p}`" for p in matter[stage])
            )
        else:
            lines.append(f"_No knobs with weak+ signal @ {stage}_")
        lines.append("")

    grid_path = out_dir / "knob_grid_report.md"
    grid_path.write_text("\n".join(lines))
    print(f"Wrote {out_dir / 'knob_grid_agg.csv'}")
    print(f"Wrote {out_dir / 'knob_grid_summary.csv'}")
    print(f"Wrote {grid_path}")


def write_report(df: pd.DataFrame, out_dir: Path, designs: list[str]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "knob_screen_all.csv"
    df.to_csv(csv_path, index=False)

    lines = [
        "# Knob screening (Tattvam DB)",
        "",
        "Source: `experiments/tattvam_db/data/tattvam.sqlite`",
        "",
        "Two gates only — **not** tied to surrogate / prediction models.",
        "",
        "## Gate 1 — stage reach",
        "",
        "Knob must first take effect at or before the metric stage "
        "(see `knob_stage_map.py`). Otherwise verdict = `wrong_stage`.",
        "",
        "## Gate 2 — label sensitivity",
        "",
        "Spearman ρ between numeric knob value and metric, per design × stage × metric.",
        "",
        "| Verdict | Meaning |",
        "|---------|---------|",
        "| `wrong_stage` | Gate 1 fail — knob not applied yet at this stage |",
        "| `non_numeric` | Path / Tcl / text knob — skipped |",
        "| `param_flat` | Knob took < 3 distinct values in data |",
        "| `label_flat` | Metric constant in joined rows |",
        "| `insensitive` | \\|ρ\\| < 0.08 |",
        "| `weak` | 0.08 ≤ \\|ρ\\| < 0.15 |",
        "| `moderate` | 0.15 ≤ \\|ρ\\| < 0.30 |",
        "| `strong` | \\|ρ\\| ≥ 0.30 |",
        "",
    ]

    for design in designs:
        ddf = df[df["design"] == design]
        lines += [f"## {design}", ""]
        for stage in STAGE_ORDER:
            sdf = ddf[ddf["stage"] == stage]
            if sdf.empty:
                continue
            lines.append(f"### {stage}")
            lines.append("")
            for metric in sorted(sdf["metric"].unique()):
                keep = summarize_keepers(ddf, stage, metric)
                lines.append(f"**{metric}** — knobs passing Gate 1 with weak+ sensitivity:")
                lines.append("")
                if keep.empty:
                    lines.append("_none_")
                else:
                    lines.append("| param | ρ | verdict | n | param uniq | metric CV% |")
                    lines.append("|-------|---|---------|---|------------|------------|")
                    for _, r in keep.head(12).iterrows():
                        rho = r["spearman_rho"]
                        rho_s = f"{rho:+.3f}" if pd.notna(rho) else "n/a"
                        cv = r["metric_cv_pct"]
                        cv_s = f"{cv:.1f}" if pd.notna(cv) else "n/a"
                        lines.append(
                            f"| {r['param']} | {rho_s} | {r['gate2_verdict']} | "
                            f"{int(r['n'])} | {int(r['param_nunique'])} | {cv_s} |"
                        )
                lines.append("")

        # Quick shortlist: floorplan WNS + power
        lines.append("### Shortlist hints (floorplan)")
        lines.append("")
        for metric in ["wns_ns", "power_total_w", "utilization_pct"]:
            keep = summarize_keepers(ddf, "floorplan", metric)
            if keep.empty:
                lines.append(f"- **{metric}**: no sensitive knobs found")
            else:
                names = ", ".join(keep.head(6)["param"].tolist())
                lines.append(f"- **{metric}**: {names}")
        lines.append("")

    md_path = out_dir / "knob_screen_report.md"
    md_path.write_text("\n".join(lines))
    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Screen knobs from Tattvam SQLite")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--design", action="append", help="Limit to design(s), e.g. gcd")
    parser.add_argument(
        "--stage",
        action="append",
        choices=STAGE_ORDER,
        help="Limit to stage(s); default all",
    )
    args = parser.parse_args()

    if not args.db.exists():
        raise SystemExit(f"database not found: {args.db}")

    stages = args.stage or list(STAGE_ORDER)
    all_metrics: list[str] = []
    for st in stages:
        for m in metrics_for_stage(st):
            if m not in all_metrics:
                all_metrics.append(m)

    conn = sqlite3.connect(args.db)
    designs = args.design or load_designs(conn)
    print(f"Designs: {designs}")
    print(f"Stages: {stages}")

    params = load_params(conn, None)
    metrics = load_metrics(conn, None, stages, all_metrics)
    conn.close()

    print(f"Param rows: {len(params):,}; metric rows: {len(metrics):,}")

    frames = [screen_design(params, metrics, d, stages) for d in designs]
    df = pd.concat(frames, ignore_index=True)

    write_report(df, args.out, designs)

    agg = aggregate_param_design_stage(df)
    pivot = build_summary_pivot(agg, designs)
    write_grid_outputs(df, agg, pivot, args.out, designs)

    # Console: knobs that matter per stage (any design)
    print("\n=== Knobs with weak+ signal @ stage (any of gcd/aes/jpeg) ===")
    matter = knobs_matter_by_stage(agg, designs)
    for stage in STAGE_ORDER:
        knobs = matter[stage]
        print(f"  {stage}: {len(knobs)} knobs")
        if knobs:
            print(f"    {', '.join(knobs)}")


if __name__ == "__main__":
    main()
