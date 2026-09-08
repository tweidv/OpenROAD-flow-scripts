#!/usr/bin/env python3
"""Build dataset CSV from completed trajectory logs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from designs import DESIGNS, DesignSpec, log_dir
from features import extract_trajectory_features
from ppa_value import collect_completed_runs, compute_ppa_value, load_json, targets_from_batch

ROOT = Path(__file__).resolve().parents[2]
FLOW = ROOT / "flow"
EXP = Path(__file__).resolve().parent


def load_trajectories(design: str):
    if design == "gcd":
        from perturbations import generate_trajectories

        return generate_trajectories()
    if design == "ibex":
        from perturbations_ibex import generate_ibex_trajectories

        return generate_ibex_trajectories()
    raise SystemExit(f"Unknown design {design!r}")


def build_dataset(
    trajectories,
    spec: DesignSpec,
    targets: dict[str, float],
) -> pd.DataFrame:
    rows = []
    for traj in trajectories:
        tid = traj.trajectory_id
        log = log_dir(spec, tid)
        finish = load_json(log / "6_report.json")
        if not finish:
            continue
        route = load_json(log / "5_2_route.json")
        v, comps = compute_ppa_value(
            finish,
            p_target=targets["P_target"],
            t_target=targets["T_target"],
            a_target=targets["A_target"],
            route=route,
        )
        for feat_row in extract_trajectory_features(log, traj.params, targets):
            rows.append(
                {
                    "trajectory_id": tid,
                    "tier": traj.tier,
                    "final_V": v,
                    **comps,
                    **feat_row,
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--design", choices=sorted(DESIGNS), default="gcd")
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Use only the first N trajectories from the manifest",
    )
    args = parser.parse_args()

    spec = DESIGNS[args.design]
    trajectories = load_trajectories(args.design)
    if args.limit:
        trajectories = trajectories[: args.limit]
    tids = [t.trajectory_id for t in trajectories]
    runs = collect_completed_runs(
        FLOW, tids, platform=spec.platform, log_name=spec.log_name
    )
    if not runs:
        raise SystemExit(f"No completed runs for design {args.design}")

    targets = targets_from_batch(runs)
    df = build_dataset(trajectories, spec, targets)
    out = EXP / "output" / spec.key
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "dataset.csv", index=False)
    (out / "targets.json").write_text(json.dumps(targets, indent=2))
    print(json.dumps(targets, indent=2))
    print(f"Wrote {len(df)} rows ({len(runs)} trajectories) to {out / 'dataset.csv'}")


if __name__ == "__main__":
    main()
