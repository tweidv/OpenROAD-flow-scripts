#!/usr/bin/env python3
"""Run perturbed trajectories through ORFS."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from designs import DESIGNS, DesignSpec, generated_dir, log_dir
from perturbations import BASE, generate_trajectories, write_manifest

ROOT = Path(__file__).resolve().parents[2]
FLOW = ROOT / "flow"

# ORFS make targets for partial flows (see flow/Makefile do-step rules).
FLOW_TARGETS: dict[str, str] = {
    "finish": "finish",
    "floorplan": "2_1_floorplan",
}

FLOW_TARGET_ARTIFACTS: dict[str, str] = {
    "finish": "6_report.json",
    "floorplan": "2_1_floorplan.json",
}


def render_config_mk(
    traj: dict,
    sdc_path: Path,
    out_path: Path,
    spec: DesignSpec,
) -> None:
    p = traj["params"]
    lines = [
        f"include {spec.base_config.resolve()}",
        f"export SDC_FILE = {sdc_path.resolve()}",
    ]
    for key, val in p.items():
        if key == "CLK_PERIOD":
            continue
        default = spec.config_exports.get(key, spec.base_params.get(key, BASE.get(key)))
        if default is None or val != default:
            op = "?=" if key == "CORE_UTILIZATION" else "="
            lines.append(f"export {key} {op} {val}")
    lines.append("")
    out_path.write_text("\n".join(lines))


def render_sdc(params: dict, out_path: Path, spec: DesignSpec) -> None:
    period = params["CLK_PERIOD"]
    text = f"""current_design {spec.sdc_design}

set clk_name core_clock
set clk_port_name {spec.clk_port_name}
set clk_period {period}
set clk_io_pct 0.2

set clk_port [get_ports $clk_port_name]

create_clock -name $clk_name -period $clk_period $clk_port
set clk_io_name vclk_$clk_name
create_clock -name $clk_io_name -period $clk_period
set_clock_latency {spec.clk_latency} [get_clocks $clk_name]
set_clock_latency {spec.clk_latency} [get_clocks $clk_io_name]

set non_clock_inputs [all_inputs -no_clocks]

set_input_delay [expr $clk_period * $clk_io_pct] -clock $clk_io_name $non_clock_inputs
set_output_delay [expr $clk_period * $clk_io_pct] -clock $clk_io_name [all_outputs]
"""
    out_path.write_text(text)


def run_one(
    traj: dict,
    spec: DesignSpec,
    *,
    dry_run: bool = False,
    num_cores: int | None = None,
    make_target: str = "finish",
) -> int:
    tid = traj["trajectory_id"]
    variant = f"ppa_{tid}"
    gen = generated_dir(spec)
    cfg_dir = gen / "configs"
    sdc_dir = gen / "sdc"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    sdc_dir.mkdir(parents=True, exist_ok=True)

    sdc_path = sdc_dir / f"{tid}.sdc"
    cfg_path = cfg_dir / f"{tid}.mk"
    render_sdc(traj["params"], sdc_path, spec)
    render_config_mk(traj, sdc_path.resolve(), cfg_path, spec)

    cmd = [
        "make",
        f"DESIGN_CONFIG={cfg_path}",
        f"FLOW_VARIANT={variant}",
        make_target,
    ]
    print(
        f"[RUN] {spec.key}/{tid} ({traj['tier']}) -> "
        f"FLOW_VARIANT={variant} target={make_target}"
    )
    if dry_run:
        print("  ", " ".join(cmd))
        return 0

    env = os.environ.copy()
    env.setdefault("TMPDIR", "/data/tmp")
    if num_cores is not None:
        env["NUM_CORES"] = str(num_cores)
    proc = subprocess.run(cmd, cwd=FLOW, env=env)
    return proc.returncode


def _run_one_worker(
    args: tuple[dict, DesignSpec, bool, int | None, str],
) -> dict[str, object]:
    traj, spec, dry_run, num_cores, make_target = args
    rc = run_one(traj, spec, dry_run=dry_run, num_cores=num_cores, make_target=make_target)
    return {"trajectory_id": traj["trajectory_id"], "returncode": rc}


def load_trajectories_from_manifest(manifest_path: Path) -> list:
    from perturbations import TrajectoryConfig

    if not manifest_path.exists():
        raise SystemExit(f"Manifest not found: {manifest_path}")
    raw = json.loads(manifest_path.read_text())
    return [TrajectoryConfig(**item) for item in raw]


def load_trajectories(design: str, manifest: str | None = None):
    if manifest:
        path = generated_dir(DESIGNS[design]) / manifest
        return load_trajectories_from_manifest(path)
    if design == "gcd":
        return generate_trajectories()
    if design == "ibex":
        from perturbations_ibex import generate_ibex_trajectories

        return generate_ibex_trajectories()
    raise SystemExit(f"Unknown design {design!r}; choose from {sorted(DESIGNS)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--design",
        choices=sorted(DESIGNS),
        default="gcd",
        help="Target design (default: gcd)",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--only", nargs="*", help="Run specific trajectory ids")
    parser.add_argument(
        "--jobs",
        type=int,
        default=1,
        help="Run this many trajectories in parallel (default: 1)",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip trajectories that already have the target artifact JSON",
    )
    parser.add_argument(
        "--target",
        choices=sorted(FLOW_TARGETS),
        default="finish",
        help="ORFS make target (default: finish; use floorplan for 2_1_floorplan.json only)",
    )
    parser.add_argument(
        "--manifest",
        default="",
        help="Manifest filename under generated/<design>/ (default: built-in generator)",
    )
    args = parser.parse_args()

    make_target = FLOW_TARGETS[args.target]
    artifact_name = FLOW_TARGET_ARTIFACTS[args.target]

    spec = DESIGNS[args.design]
    gen = generated_dir(spec)
    manifest = args.manifest or None
    trajectories = load_trajectories(args.design, manifest=manifest)
    if not manifest:
        write_manifest(gen, trajectories)

    selected = trajectories
    if args.only:
        only = set(args.only)
        selected = [t for t in trajectories if t.trajectory_id in only]
    if args.limit:
        selected = selected[: args.limit]
    if args.skip_existing:
        kept = []
        for traj in selected:
            done = log_dir(spec, traj.trajectory_id) / artifact_name
            if done.exists():
                print(f"[SKIP] {traj.trajectory_id} (already has {artifact_name})")
                continue
            kept.append(traj)
        selected = kept

    cpu_count = os.cpu_count() or 1
    jobs = max(1, min(args.jobs, len(selected) or 1))
    num_cores = max(1, cpu_count // jobs)

    results: list[dict[str, object]] = []
    if jobs == 1:
        for traj in selected:
            rc = run_one(
                traj.to_dict(),
                spec,
                dry_run=args.dry_run,
                num_cores=num_cores,
                make_target=make_target,
            )
            results.append({"trajectory_id": traj.trajectory_id, "returncode": rc})
    else:
        print(f"[PARALLEL] jobs={jobs}, NUM_CORES per run={num_cores}")
        worker_args = [
            (traj.to_dict(), spec, args.dry_run, num_cores, make_target)
            for traj in selected
        ]
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            futures = [pool.submit(_run_one_worker, arg) for arg in worker_args]
            for fut in as_completed(futures):
                results.append(fut.result())

    results.sort(key=lambda r: str(r["trajectory_id"]))

    out = gen / "run_results.json"
    out.write_text(json.dumps(results, indent=2))
    failed = [r for r in results if r["returncode"] != 0]
    if failed:
        print(f"{len(failed)} trajectory run(s) failed")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
