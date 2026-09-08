#!/usr/bin/env python3
"""SHAP + ablation on FULL ORFS JSON metrics (offline, no new runs)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from feature_analysis import (
    EXP,
    STAGES,
    TARGETS,
    compare_shap_ablation,
    load_final_pta,
    run_group_ablation_generic,
    run_individual_ablation_generic,
    run_shap_for_stage_target_generic,
    write_summary_full,
)
from designs import DESIGNS
from splits import DEFAULT_TRAIN_SIZE, split_trajectories
from wide_metrics import build_all_stages, load_trajectory_params

MODEL_COUNTS = {}


def count_models(stage_features: dict[str, list[str]], stage_groups: dict[str, dict]) -> dict:
    shap = len(STAGES) * len(TARGETS)
    group = sum((len(stage_groups[s]) + 1) * len(TARGETS) for s in STAGES)
    indiv = sum(len(stage_features[s]) * len(TARGETS) for s in STAGES)
    return {"shap": shap, "group_ablation": group, "individual_ablation": indiv, "total_fits": shap + group + indiv}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--design", default="gcd")
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--train-size", type=int, default=DEFAULT_TRAIN_SIZE)
    parser.add_argument("--skip-individual", action="store_true", help="Skip LOO (faster)")
    args = parser.parse_args()

    out_root = EXP / "output" / args.design / "feature_analysis" / "full"
    shap_dir = out_root / "shap"
    ablation_dir = out_root / "ablation"
    indiv_dir = out_root / "individual"
    for d in (out_root, shap_dir, ablation_dir, indiv_dir):
        d.mkdir(parents=True, exist_ok=True)

    print("Building wide feature tables from existing JSON logs (no new OR runs)...")
    wide_data = build_all_stages(args.design, args.limit)

    spec = DESIGNS[args.design]
    tids, _ = load_trajectory_params(args.design, args.limit)
    pta = load_final_pta(tids, spec)
    train_traj, test_traj = split_trajectories(
        sorted(pta["trajectory_id"].unique()), train_size=args.train_size
    )

    stage_features = {s: wide_data[s][1] for s in STAGES}
    stage_groups = {s: wide_data[s][2] for s in STAGES}
    counts = count_models(stage_features, stage_groups)

    print("\n=== Full metrics analysis scope ===")
    for s in STAGES:
        print(f"  {s}: {len(stage_features[s])} features, {len(stage_groups[s])} groups")
    print(json.dumps(counts, indent=2))

    meta = {
        "mode": "full_orfs_metrics",
        "design": args.design,
        "limit": args.limit,
        "train_size": args.train_size,
        "n_train": len(train_traj),
        "n_test": len(test_traj),
        "stage_features": {s: len(stage_features[s]) for s in STAGES},
        "model_counts": counts,
    }
    (out_root / "run_metadata.json").write_text(json.dumps(meta, indent=2))

    shap_frames = []
    group_frames = {}
    indiv_frames = {}

    for stage in STAGES:
        wide, feats, groups = wide_data[stage]
        df = wide.merge(pta, on="trajectory_id")
        print(f"\n[{stage}] {len(feats)} features, SHAP...", flush=True)
        for target_key in TARGETS:
            print(f"  → {target_key}", flush=True)
            shap_frames.append(
                run_shap_for_stage_target_generic(
                    df, feats, stage, target_key, train_traj, test_traj, shap_dir
                )
            )

        print(f"[{stage}] group ablation...", flush=True)
        gdf = run_group_ablation_generic(df, feats, groups, stage, train_traj, test_traj)
        gdf.to_csv(ablation_dir / f"ablation_{stage}.csv", index=False)
        group_frames[stage] = gdf

        if not args.skip_individual:
            print(f"[{stage}] individual ablation ({len(feats)} features)...", flush=True)
            idf = run_individual_ablation_generic(df, feats, stage, train_traj, test_traj)
            idf.to_csv(indiv_dir / f"feature_ablation_{stage}.csv", index=False)
            indiv_frames[stage] = idf

    compare = compare_shap_ablation(shap_frames, indiv_frames) if indiv_frames else pd.DataFrame()
    if len(compare):
        compare.to_csv(out_root / "shap_vs_ablation.csv", index=False)

    shap_all = pd.concat(shap_frames, ignore_index=True)
    shap_all.groupby(["stage", "feature"], as_index=False).agg(
        mean_abs_shap=("mean_abs_shap", "mean")
    ).sort_values(["stage", "mean_abs_shap"], ascending=[True, False]).to_csv(
        shap_dir / "shap_combined_summary.csv", index=False
    )

    write_summary_full(
        out_root / "feature_analysis_summary.md",
        meta,
        shap_frames,
        group_frames,
        indiv_frames,
        compare,
        stage_features,
    )
    print(f"\nDone. Outputs in {out_root}")


if __name__ == "__main__":
    main()
