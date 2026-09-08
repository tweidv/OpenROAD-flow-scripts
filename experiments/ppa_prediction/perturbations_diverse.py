"""Latin-hypercube sweep across many ORFS knobs (decoupled from util×clk grid)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from perturbations import BASE, TrajectoryConfig


def resolve_design(design: str) -> tuple[dict[str, Any], float, str]:
    """Return (base_params, fixed_clk_period, density_design_key)."""
    if design == "ibex":
        from designs import IBEX_BASE

        base = dict(BASE)
        base.update(IBEX_BASE)
        return base, float(IBEX_BASE["CLK_PERIOD"]), "ibex"
    return dict(BASE), FIXED_CLK_PERIOD, "gcd"

MANIFEST_NAME = "trajectories_lhs250.json"
FIXEDCLK_MANIFEST_NAME = "trajectories_fixedclk250.json"
DEFAULT_N = 250
DEFAULT_SEED = 43
FIXED_CLK_PERIOD = 0.25  # GCD dashboard / designs.py baseline (4 GHz)

# ORFS: place_density = lb + (1-lb)*addon + 0.01  (util.tcl)
# lb comes from gpl::get_global_placement_uniform_density AFTER floorplan — often
# 0.72–0.85 on GCD, much higher than CORE_UTILIZATION/100. Keep target well below 1.0.
MAX_PLACE_DENSITY = 0.99
SAFE_MAX_PLACE_DENSITY = 0.88  # runtime lb on GCD can exceed 0.95

# Empirical GCD calibration from fclk batch logs (gpl::get_global_placement_uniform_density).
GCD_RUNTIME_LB_BASE = 0.70
GCD_RUNTIME_LB_PER_UTIL = 0.004  # per util point above 40

# (name, kind, lo, hi) — kind: float | int | bool
LHS_DIMENSIONS: list[tuple[str, str, float, float]] = [
    ("CORE_UTILIZATION", "int", 40, 65),
    ("CORE_ASPECT_RATIO", "float", 0.80, 1.25),
    ("CORE_MARGIN", "float", 1.0, 2.5),
    ("PLACE_DENSITY_LB_ADDON", "float", 0.05, 0.28),
    ("CELL_PAD_IN_SITES_GLOBAL_PLACEMENT", "int", 0, 2),
    ("CELL_PAD_IN_SITES_DETAIL_PLACEMENT", "int", 0, 2),
    ("CTS_CLUSTER_SIZE", "int", 25, 100),
    ("CTS_CLUSTER_DIAMETER", "int", 80, 250),
    ("TNS_END_PERCENT", "int", 20, 100),
    ("SETUP_SLACK_MARGIN", "float", -0.03, 0.02),
    ("ENABLE_PLACE_REPAIR_TIMING", "bool", 0, 1),
    ("ROUTING_LAYER_ADJUSTMENT", "float", 0.15, 0.45),
    ("GPL_RANDOM_SEED", "int", 1, 99999),
    ("GRT_SEED", "int", 1, 99999),
]

CLK_BANDS: list[tuple[str, float, float, float]] = [
    ("easy", 0.45, 0.62, 0.30),
    ("medium", 0.28, 0.45, 0.40),
    ("hard", 0.18, 0.28, 0.30),
]


def _lhs_unit(n_samples: int, n_dims: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    cuts = np.linspace(0.0, 1.0, n_samples + 1)
    u = np.empty((n_samples, n_dims))
    for j in range(n_dims):
        u[:, j] = rng.uniform(cuts[:-1], cuts[1:])
        rng.shuffle(u[:, j])
    return u


def _quantize(name: str, kind: str, lo: float, hi: float, u: float) -> Any:
    x = lo + u * (hi - lo)
    if kind == "int":
        return int(round(x))
    if kind == "bool":
        return 1 if u >= 0.5 else 0
    if name == "CLK_PERIOD":
        return round(x, 3)
    if name in ("CORE_ASPECT_RATIO", "PLACE_DENSITY_LB_ADDON", "ROUTING_LAYER_ADJUSTMENT"):
        return round(x, 2)
    if name == "SETUP_SLACK_MARGIN":
        return round(x, 4)
    if name == "CORE_MARGIN":
        return round(x, 1)
    return float(x)


def _assign_clk_bands(n: int, seed: int) -> list[tuple[str, float]]:
    rng = np.random.default_rng(seed + 1)
    counts = [max(1, int(round(n * frac))) for _, _, _, frac in CLK_BANDS]
    delta = n - sum(counts)
    counts[1] += delta  # adjust medium band
    bands: list[tuple[str, float]] = []
    for (label, lo, hi, _), count in zip(CLK_BANDS, counts):
        u = _lhs_unit(count, 1, seed + hash(label) % 10_000)[:, 0]
        for ui in u:
            bands.append((label, lo + float(ui) * (hi - lo)))
    rng.shuffle(bands)
    return bands[:n]


def _params_key(params: dict[str, Any]) -> tuple[tuple[str, Any], ...]:
    return tuple(sorted(params.items()))


def estimate_place_density_lb(
    core_utilization: int,
    *,
    cell_pad_gp: int = 0,
    aspect_ratio: float = 1.0,
    core_margin: float = 2.0,
    design: str = "gcd",
) -> float:
    """Conservative offline estimate of GPL uniform-density lower bound.

    OR computes the real lb after floorplan via gpl::get_global_placement_uniform_density.
    On GCD this is typically 0.72–0.80 when CORE_MARGIN >= 1.5, but climbs to 0.96+
    with tight margins (~1.1) — the main cause of FLW-0024 in fclk/fclk2 batches.
    """
    pad = 0.02 * cell_pad_gp
    aspect = 0.04 * abs(aspect_ratio - 1.0)
    if design in ("gcd", "ibex"):
        util = max(40, int(core_utilization))
        # Empirical from GCD fclk2 skip_io logs; ibex uses same conservative guardrails until calibrated.
        margin_penalty = max(0.0, 0.75 - 0.45 * float(core_margin))
        lb = GCD_RUNTIME_LB_BASE + GCD_RUNTIME_LB_PER_UTIL * (util - 40) + pad + aspect + margin_penalty
        return min(0.98, lb)
    util = core_utilization / 100.0
    return min(0.90, util + 0.06 + pad + aspect)


def max_place_density_addon(
    place_density_lb: float, *, max_density: float = SAFE_MAX_PLACE_DENSITY
) -> float:
    """Largest PLACE_DENSITY_LB_ADDON s.t. lb + (1-lb)*addon + 0.01 <= max_density."""
    headroom = max_density - 0.01 - place_density_lb
    if headroom <= 0:
        return 0.0
    denom = 1.0 - place_density_lb
    if denom <= 1e-6:
        return 0.0
    return max(0.0, headroom / denom)


def enforce_place_density(
    params: dict[str, Any], *, design: str = "gcd", max_density: float = SAFE_MAX_PLACE_DENSITY
) -> float:
    """Clip PLACE_DENSITY_LB_ADDON to a feasible value; return implied density."""
    lb = estimate_place_density_lb(
        int(params["CORE_UTILIZATION"]),
        cell_pad_gp=int(params.get("CELL_PAD_IN_SITES_GLOBAL_PLACEMENT", 0)),
        aspect_ratio=float(params.get("CORE_ASPECT_RATIO", 1.0)),
        core_margin=float(params.get("CORE_MARGIN", 2.0)),
        design=design,
    )
    cap = max_place_density_addon(lb, max_density=max_density)
    requested = float(params["PLACE_DENSITY_LB_ADDON"])
    params["PLACE_DENSITY_LB_ADDON"] = round(min(requested, cap), 2)
    return lb + (1.0 - lb) * params["PLACE_DENSITY_LB_ADDON"] + 0.01


STRICT_DIM_OVERRIDES: dict[str, tuple[str, float, float]] = {
    "CORE_UTILIZATION": ("int", 40, 55),
    "CORE_MARGIN": ("float", 1.5, 2.5),
    "PLACE_DENSITY_LB_ADDON": ("float", 0.05, 0.15),
    "CORE_ASPECT_RATIO": ("float", 0.85, 1.15),
}


def _lhs_dimensions(*, strict: bool) -> list[tuple[str, str, float, float]]:
    if not strict:
        return LHS_DIMENSIONS
    out: list[tuple[str, str, float, float]] = []
    for name, kind, lo, hi in LHS_DIMENSIONS:
        if name in STRICT_DIM_OVERRIDES:
            o_kind, lo, hi = STRICT_DIM_OVERRIDES[name]
            kind = o_kind
        out.append((name, kind, lo, hi))
    return out


def generate_lhs_trajectories(
    n: int = DEFAULT_N,
    seed: int = DEFAULT_SEED,
    *,
    strict: bool = False,
    fixed_clk: bool = True,
    id_offset: int = 0,
    tier_prefix: str = "lhs",
    id_prefix: str = "traj_lhs",
    design: str = "gcd",
) -> tuple[list[TrajectoryConfig], dict[str, Any]]:
    base_params, default_clk, density_design = resolve_design(design)
    lhs_dims = _lhs_dimensions(strict=strict)
    density_margin = 0.10 if strict else 0.06
    max_density = SAFE_MAX_PLACE_DENSITY if strict else MAX_PLACE_DENSITY

    n_dims = len(lhs_dims)
    unit = _lhs_unit(n, n_dims, seed)
    clk_assignments = None if fixed_clk else _assign_clk_bands(n, seed)

    trajectories: list[TrajectoryConfig] = []
    seen: set[tuple[tuple[str, Any], ...]] = set()
    clipped = 0

    for i in range(n):
        params = dict(base_params)
        if fixed_clk:
            params["CLK_PERIOD"] = default_clk
            tier = tier_prefix
        else:
            clk_label, clk_raw = clk_assignments[i]  # type: ignore[index]
            params["CLK_PERIOD"] = round(clk_raw, 3)
            tier = f"{tier_prefix}_{clk_label}"

        for j, (name, kind, lo, hi) in enumerate(lhs_dims):
            params[name] = _quantize(name, kind, lo, hi, float(unit[i, j]))

        lb = estimate_place_density_lb(
            int(params["CORE_UTILIZATION"]),
            cell_pad_gp=int(params["CELL_PAD_IN_SITES_GLOBAL_PLACEMENT"]),
            aspect_ratio=float(params["CORE_ASPECT_RATIO"]),
            core_margin=float(params["CORE_MARGIN"]),
            design=density_design,
        )
        cap = max(0.0, (max_density - 0.01 - lb) / max(1e-6, 1.0 - lb))
        before = float(params["PLACE_DENSITY_LB_ADDON"])
        params["PLACE_DENSITY_LB_ADDON"] = round(min(before, cap), 2)
        if params["PLACE_DENSITY_LB_ADDON"] < before - 1e-9:
            clipped += 1
        if lb + 0.01 > max_density + 1e-6:
            # Tight floorplan — nudge margin up so GPL lb is feasible
            params["CORE_MARGIN"] = round(min(2.5, float(params["CORE_MARGIN"]) + 0.4), 1)
            lb = estimate_place_density_lb(
                int(params["CORE_UTILIZATION"]),
                cell_pad_gp=int(params["CELL_PAD_IN_SITES_GLOBAL_PLACEMENT"]),
                aspect_ratio=float(params["CORE_ASPECT_RATIO"]),
                core_margin=float(params["CORE_MARGIN"]),
                design=density_design,
            )
            cap = max(0.0, (max_density - 0.01 - lb) / max(1e-6, 1.0 - lb))
            params["PLACE_DENSITY_LB_ADDON"] = round(min(before, cap), 2)

        pk = _params_key(params)
        if pk in seen:
            # rare collision — nudge GPL seed
            params["GPL_RANDOM_SEED"] = int(params["GPL_RANDOM_SEED"]) + i + 1
            pk = _params_key(params)
        seen.add(pk)

        trajectories.append(
            TrajectoryConfig(
                trajectory_id=f"{id_prefix}_{id_offset + i + 1:03d}",
                tier=tier,
                params=params,
            )
        )

    return trajectories, {
        "addon_clipped": clipped,
        "fixed_clk": fixed_clk,
        "clk_period": default_clk if fixed_clk else "varied",
        "design": design,
    }


def generate_topup_trajectories(
    failed_ids: list[str],
    extra_n: int = 100,
    seed: int = 44,
) -> tuple[list[TrajectoryConfig], dict[str, Any]]:
    """Fresh strict LHS params for failed IDs plus extra new trajectories."""
    n = len(failed_ids) + extra_n
    batch, stats = generate_lhs_trajectories(
        n, seed, strict=True, id_offset=0, tier_prefix="lhs_topup"
    )
    out: list[TrajectoryConfig] = []
    for i, tid in enumerate(failed_ids):
        t = batch[i]
        out.append(TrajectoryConfig(trajectory_id=tid, tier=t.tier, params=t.params))
    for j in range(extra_n):
        t = batch[len(failed_ids) + j]
        out.append(
            TrajectoryConfig(
                trajectory_id=f"traj_lhs_{251 + j:03d}",
                tier=t.tier,
                params=t.params,
            )
        )
    stats["n_failed_retry"] = len(failed_ids)
    stats["n_extra"] = extra_n
    return out, stats


def validate_manifest(
    trajectories: list[TrajectoryConfig], *, design: str = "gcd"
) -> dict[str, Any]:
    clipped = 0
    max_density = 0.0
    for t in trajectories:
        p = dict(t.params)
        before = float(p["PLACE_DENSITY_LB_ADDON"])
        d = enforce_place_density(p, design=design)
        max_density = max(max_density, d)
        if p["PLACE_DENSITY_LB_ADDON"] < before - 1e-9:
            clipped += 1
    infeasible = sum(
        1
        for t in trajectories
        if enforce_place_density(dict(t.params), design=design) > MAX_PLACE_DENSITY + 1e-6
    )
    return {
        "addon_clipped_during_generation": clipped,
        "infeasible_after_enforce": infeasible,
        "max_implied_place_density": round(max_density, 4),
    }


def write_manifest(out_dir: Path, trajectories: list[TrajectoryConfig], name: str = MANIFEST_NAME) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / name
    path.write_text(json.dumps([t.to_dict() for t in trajectories], indent=2))
    return path


def manifest_summary(trajectories: list[TrajectoryConfig], *, fixed_clk: bool = True) -> dict[str, Any]:
    tiers = {}
    for t in trajectories:
        tiers[t.tier] = tiers.get(t.tier, 0) + 1
    clk_vals = sorted({t.params.get("CLK_PERIOD") for t in trajectories})
    return {
        "n": len(trajectories),
        "tiers": tiers,
        "n_swept_params": len(LHS_DIMENSIONS),
        "fixed_clk": fixed_clk,
        "clk_periods": clk_vals,
        "param_names": (["CLK_PERIOD (fixed)"] if fixed_clk else ["CLK_PERIOD"])
        + [d[0] for d in LHS_DIMENSIONS],
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate LHS diverse trajectory manifest")
    parser.add_argument("-n", type=int, default=DEFAULT_N)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--design",
        choices=("gcd", "ibex"),
        default="gcd",
        help="Target design (sets default out-dir and fixed CLK)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Output directory (default: generated/<design>)",
    )
    parser.add_argument("--strict", action="store_true")
    parser.add_argument(
        "--vary-clk",
        action="store_true",
        help="Old behaviour: stratified CLK bands (default: fixed 0.25 ns)",
    )
    parser.add_argument(
        "--manifest-name",
        type=str,
        default=None,
        help="Output manifest filename (default: fixedclk or lhs250)",
    )
    parser.add_argument(
        "--id-prefix",
        type=str,
        default=None,
        help="Trajectory id prefix (default: traj_fclk or traj_lhs)",
    )
    parser.add_argument(
        "--topup",
        action="store_true",
        help="Regenerate failed lhs250 IDs + 100 new strict trajectories",
    )
    parser.add_argument("--extra-n", type=int, default=100)
    args = parser.parse_args()
    out_dir = args.out_dir or (Path(__file__).resolve().parent / "generated" / args.design)
    _, default_clk, _ = resolve_design(args.design)

    if args.topup:
        from designs import DESIGNS, log_dir

        spec = DESIGNS["gcd"]
        base_manifest = out_dir / MANIFEST_NAME
        manifest = json.loads(base_manifest.read_text())
        failed = sorted(
            t["trajectory_id"]
            for t in manifest
            if not (log_dir(spec, t["trajectory_id"]) / "6_report.json").exists()
        )
        trajs, gen_stats = generate_topup_trajectories(failed, extra_n=args.extra_n, seed=44)
        path = write_manifest(out_dir, trajs, name="trajectories_lhs_topup.json")
        summary = manifest_summary(trajs)
        summary["generation"] = gen_stats
        summary["feasibility"] = validate_manifest(trajs, design=args.design)
        print(json.dumps(summary, indent=2))
        print(f"Wrote {path} ({len(failed)} retries + {args.extra_n} new)")
        raise SystemExit(0)

    fixed_clk = not args.vary_clk
    id_prefix = args.id_prefix or ("traj_fclk" if fixed_clk else "traj_lhs")
    manifest_name = args.manifest_name or (
        FIXEDCLK_MANIFEST_NAME if fixed_clk else MANIFEST_NAME
    )
    tier_prefix = "fixedclk" if fixed_clk else "lhs"

    trajs, gen_stats = generate_lhs_trajectories(
        n=args.n,
        seed=args.seed,
        strict=args.strict,
        fixed_clk=fixed_clk,
        tier_prefix=tier_prefix,
        id_prefix=id_prefix,
        design=args.design,
    )
    path = write_manifest(out_dir, trajs, name=manifest_name)
    summary = manifest_summary(trajs, fixed_clk=fixed_clk)
    summary["design"] = args.design
    summary["generation"] = gen_stats
    summary["feasibility"] = validate_manifest(trajs, design=args.design)
    print(json.dumps(summary, indent=2))
    print(f"Wrote {path}")
