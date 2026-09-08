#!/usr/bin/env python3
"""Tally checkpoint costs from existing search_eval.json (no re-simulation)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

STAGES = ("floorplan", "placement", "cts", "routing")
DEFAULT_STAGE_COSTS = {
    "floorplan": 2.0,
    "placement": 4.0,
    "cts": 2.0,
    "routing": 3.0,
}


def tally_model_guided(
    report: dict,
    stage_costs: dict[str, float],
    *,
    charge_initial_floorplan: bool = False,
) -> dict:
    """Count only stages actually run during search (reveal actions).

    Model predictions are free. Initial floorplan features for all candidates
    are free by default (reading existing checkpoint metadata, not re-running).
    """
    n_test = report["n_test_candidates"]
    tally = {s: 0 for s in STAGES}

    if charge_initial_floorplan:
        tally["floorplan"] = n_test

    for step in report["model_guided"]["steps"]:
        if step["action"] == "reveal_checkpoint":
            tally[step["stage_revealed"]] += 1

    cumulative = sum(tally[s] * stage_costs[s] for s in STAGES)
    return {
        "checkpoint_tally": tally,
        "total_checkpoints": sum(tally.values()),
        "cumulative_cost": cumulative,
        "stage_costs": stage_costs,
        "full_run_cost": sum(stage_costs[s] for s in STAGES),
        "charge_initial_floorplan": charge_initial_floorplan,
    }


def tally_random(
    n_test: int,
    n_evals: int,
    stage_costs: dict[str, float],
) -> dict:
    """Random evaluates n_evals full trajectories (each uses all 4 stages)."""
    tally = {s: n_evals for s in STAGES}
    cumulative = n_evals * sum(stage_costs[s] for s in STAGES)
    return {
        "checkpoint_tally": tally,
        "total_checkpoints": sum(tally.values()),
        "cumulative_cost": cumulative,
        "stage_costs": stage_costs,
        "full_run_cost": sum(stage_costs[s] for s in STAGES),
        "n_evals": n_evals,
    }


def cost_at_threshold(cost_curve: list[dict], threshold: float) -> float | None:
    for point in cost_curve:
        if point["best_found"] >= threshold:
            return point["cumulative_cost"]
    return None


def build_cost_curve_from_steps(
    steps: list[dict],
    n_test: int,
    optimum: float,
    stage_costs: dict[str, float],
    *,
    charge_initial_floorplan: bool = False,
) -> list[dict]:
    cost = 0.0
    if charge_initial_floorplan:
        cost = n_test * stage_costs["floorplan"]
    best = 0.0
    n_complete = 0
    curve = [{"cumulative_cost": cost, "best_found": 0.0, "n_complete": 0}]

    for step in steps:
        if step["action"] == "reveal_checkpoint":
            stage = step["stage_revealed"]
            cost += stage_costs[stage]
            curve.append(
                {"cumulative_cost": cost, "best_found": best, "n_complete": n_complete}
            )
        else:
            n_complete += 1
            best = max(best, step["actual_V"])
            curve.append(
                {"cumulative_cost": cost, "best_found": best, "n_complete": n_complete}
            )
    return curve


def cost_at_threshold_random(
    n_test: int,
    evals_to: int,
    stage_costs: dict[str, float],
) -> float:
    return evals_to * sum(stage_costs[s] for s in STAGES)


def process_report(path: Path, stage_costs: dict[str, float]) -> dict:
    report = json.loads(path.read_text())
    optimum = report["true_optimum"]
    mg = tally_model_guided(report, stage_costs)
    cost_curve = build_cost_curve_from_steps(
        report["model_guided"]["steps"],
        report["n_test_candidates"],
        optimum,
        stage_costs,
    )

    mg_costs = {
        f"cost_to_{int(r*100)}pct": cost_at_threshold(cost_curve, r * optimum)
        for r in (0.90, 0.95, 0.99)
    }

    rand = report["random"]
    full_run = sum(stage_costs[s] for s in STAGES)
    rand_costs = {}
    rand_cost_samples: dict[str, list[float]] = {}
    for ratio, eval_key, cost_key in [
        (0.90, "evals_to_90pct", "cost_to_90pct"),
        (0.95, "evals_to_95pct", "cost_to_95pct"),
        (0.99, "evals_to_99pct", "cost_to_99pct"),
    ]:
        eval_vals = [v for v in rand[eval_key]["values"] if v is not None]
        cost_vals = [v * full_run for v in eval_vals]
        rand_cost_samples[cost_key] = cost_vals
        rand_costs[cost_key] = {
            "mean": float(np.mean(cost_vals)) if cost_vals else None,
            "p50": float(np.median(cost_vals)) if cost_vals else None,
        }

    rand_at_95 = int(rand["evals_to_95pct"]["mean"])
    rand_tally = tally_random(report["n_test_candidates"], rand_at_95, stage_costs)

    return {
        "path": str(path),
        "train_size": report.get("train_size"),
        "n_test": report["n_test_candidates"],
        "optimum": optimum,
        "model_guided": mg,
        "model_guided_costs": mg_costs,
        "random_at_95pct": rand_tally,
        "random_costs": rand_costs,
        "n_random_permutations": report.get("n_random_permutations"),
    }


def print_tally(label: str, accounting: dict) -> None:
    tally = accounting["checkpoint_tally"]
    costs = accounting["stage_costs"]
    print(f"\n{label}:")
    print(f"  {'stage':<12} {'runs':>8} {'unit':>6} {'subtotal':>10}")
    for stage in STAGES:
        if tally[stage] == 0 and label.startswith("Model") and stage == "floorplan":
            continue
        print(f"  {stage:<12} {tally[stage]:>8} {costs[stage]:>6.1f} {tally[stage]*costs[stage]:>10.1f}")
    print(f"  {'TOTAL':<12} {accounting['total_checkpoints']:>8} {'':>6} {accounting['cumulative_cost']:>10.1f}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("reports", nargs="+", type=Path)
    parser.add_argument("-o", "--output", type=Path, default=None)
    args = parser.parse_args()

    results = [process_report(p, DEFAULT_STAGE_COSTS) for p in args.reports]
    lines = [
        "# Checkpoint tally (from existing search_eval steps)",
        "",
        "Costs apply only to **running** a flow stage. Model predictions are free.",
        "Initial floorplan features for all candidates are free (metadata peek, not re-run).",
        "",
        f"Stage run costs: {DEFAULT_STAGE_COSTS} (11 per full run from scratch)",
        "",
    ]

    for r in results:
        train = r["train_size"]
        test = r["n_test"]
        print(f"\n=== {train}/{test} split ===")
        print_tally("Model-guided (full search)", r["model_guided"])
        print_tally(f"Random (to 95%, ~{r['random_at_95pct']['n_evals']} evals)", r["random_at_95pct"])
        rc95 = r["random_costs"]["cost_to_95pct"]
        print(
            f"  Cost →95%: model={r['model_guided_costs']['cost_to_95pct']:.1f}  "
            f"random mean={rc95['mean']:.1f} p50={rc95['p50']:.1f} "
            f"({r['n_random_permutations']} shuffled permutations)"
        )

        lines += [
            f"## {train} train / {test} test",
            "",
            "### Model-guided (complete search)",
            "",
            "| Stage | Count | Subtotal |",
            "|-------|------:|---------:|",
        ]
        mg = r["model_guided"]
        for stage in STAGES:
            c = mg["checkpoint_tally"][stage]
            lines.append(f"| {stage} | {c} | {c * mg['stage_costs'][stage]:.1f} |")
        lines.append(f"| **TOTAL** | **{mg['total_checkpoints']}** | **{mg['cumulative_cost']:.1f}** |")
        lines += [
            "",
            f"Cost to 95%: model **{r['model_guided_costs']['cost_to_95pct']:.1f}** vs "
            f"random mean **{r['random_costs']['cost_to_95pct']['mean']:.1f}** "
            f"(p50 **{r['random_costs']['cost_to_95pct']['p50']:.1f}**, "
            f"{r['n_random_permutations']} shuffled orders)",
            "",
        ]

    if args.output:
        args.output.write_text("\n".join(lines) + "\n")
        print(f"\nWrote {args.output}")


if __name__ == "__main__":
    main()
