"""Final repaired PPA-value computation."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open() as f:
        return json.load(f)


def repair_failed(finish: dict[str, Any], route: dict[str, Any]) -> bool:
    if not finish:
        return True
    if finish.get("finish__flow__errors__count", 0) not in (0, 0.0, None):
        return True
    drc = route.get("detailedroute__route__drc_errors", finish.get("detailedroute__route__drc_errors"))
    if drc is None:
        return False
    return float(drc) > 0


def compute_ppa_value(
    finish: dict[str, Any],
    *,
    p_target: float,
    t_target: float,
    a_target: float,
    route: dict[str, Any] | None = None,
) -> tuple[float, dict[str, float]]:
    """Return (V, components dict). V=0 if repair/feasibility failed."""
    route = route or {}
    if repair_failed(finish, route):
        return 0.0, {"V_P": 0.0, "V_T": 0.0, "V_A": 0.0, "feasible": 0.0}

    p = float(finish.get("finish__power__total", 0.0))
    a = float(finish.get("finish__design__instance__area__stdcell", finish.get("finish__design__instance__area", 0.0)))
    t = float(finish.get("finish__timing__fmax", finish.get("finish__timing__setup__ws", 0.0)))

    if p <= 0 or a <= 0 or t <= 0:
        return 0.0, {"V_P": 0.0, "V_T": 0.0, "V_A": 0.0, "feasible": 0.0}

    v_p = min(1.0, p_target / p)
    v_t = min(1.0, t / t_target)
    v_a = min(1.0, a_target / a)
    v = (v_p * v_t * v_a) ** (1.0 / 3.0)
    return v, {"V_P": v_p, "V_T": v_t, "V_A": v_a, "feasible": 1.0}


def _finish_pta(finish: dict[str, Any]) -> tuple[float, float, float] | None:
    if not finish:
        return None
    p = finish.get("finish__power__total")
    t = finish.get("finish__timing__fmax")
    a = finish.get("finish__design__instance__area__stdcell", finish.get("finish__design__instance__area"))
    if p in (None, "N/A") or t in (None, "N/A") or a in (None, "N/A"):
        return None
    p, t, a = float(p), float(t), float(a)
    if p <= 0 or t <= 0 or a <= 0:
        return None
    return p, t, a


def targets_from_baseline(finish: dict[str, Any]) -> dict[str, float]:
    """Use a single baseline finish metrics JSON as PPA targets (legacy)."""
    pta = _finish_pta(finish)
    if pta is None:
        raise ValueError("baseline finish metrics missing P/T/A")
    p, t, a = pta
    return {"P_target": p, "T_target": t, "A_target": a}


def targets_from_batch(
    runs: list[tuple[str, dict[str, Any], dict[str, Any]]],
) -> dict[str, Any]:
    """Set targets to the best P/T/A observed across feasible completed runs.

    - P_target: minimum power (lower is better)
    - T_target: maximum fmax (higher is better)
    - A_target: minimum stdcell area (lower is better)
    """
    best_p: tuple[float, str] | None = None
    best_t: tuple[float, str] | None = None
    best_a: tuple[float, str] | None = None

    for tid, finish, route in runs:
        if repair_failed(finish, route):
            continue
        pta = _finish_pta(finish)
        if pta is None:
            continue
        p, t, a = pta
        if best_p is None or p < best_p[0]:
            best_p = (p, tid)
        if best_t is None or t > best_t[0]:
            best_t = (t, tid)
        if best_a is None or a < best_a[0]:
            best_a = (a, tid)

    if best_p is None or best_t is None or best_a is None:
        raise ValueError("no feasible completed runs available to derive batch targets")

    return {
        "source": "best_of_batch",
        "P_target": best_p[0],
        "T_target": best_t[0],
        "A_target": best_a[0],
        "best_P_trajectory": best_p[1],
        "best_T_trajectory": best_t[1],
        "best_A_trajectory": best_a[1],
        "n_feasible_runs": sum(1 for _, f, r in runs if not repair_failed(f, r) and _finish_pta(f)),
    }


def collect_completed_runs(
    flow: Path,
    trajectory_ids: list[str],
    *,
    platform: str = "nangate45",
    log_name: str = "gcd",
) -> list[tuple[str, dict[str, Any], dict[str, Any]]]:
    runs: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    for tid in trajectory_ids:
        log_dir = flow / "logs" / platform / log_name / f"ppa_{tid}"
        finish = load_json(log_dir / "6_report.json")
        if not finish:
            continue
        route = load_json(log_dir / "5_2_route.json")
        runs.append((tid, finish, route))
    return runs


def finish_paths(log_dir: Path) -> tuple[Path, Path]:
    return log_dir / "6_report.json", log_dir / "5_2_route.json"
