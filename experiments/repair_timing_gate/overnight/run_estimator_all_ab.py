#!/usr/bin/env python3
"""All designs: reuse greedy logs, run Liberty DelayEstimator (faster champion)."""

from __future__ import annotations

from pathlib import Path

from run_mix_ext import JOBS, fmt_row, log, logs_dir, parse_log, replay

HERE = Path(__file__).resolve().parent
OUT = HERE / "estimator_all_ab_summary.txt"
GREEDY_STEM = "repair_legacy_v4"
EST_STEM = "repair_est_all"


def extra(p: dict) -> str:
    bits = []
    if p.get("sta") is not None:
        bits.append(
            f"eval={p['eval']} sta={p['sta']} commit={p['committed']} "
            f"ovr={p['override']}"
        )
    if p.get("estimator") is not None:
        bits.append(f"est={p['estimator']} lv={p.get('est_levels')}")
    if p.get("delay_contest") is not None:
        bits.append(f"contest={p['delay_contest']} direct={p['delay_direct']}")
    if p.get("swap") is not None:
        bits.append(f"swap={p['swap']} clone={p.get('clone')}")
    return ("  " + " ".join(bits)) if bits else ""


def dwns(est: dict, greedy: dict) -> str:
    if est.get("wns") is None or greedy.get("wns") is None:
        return ""
    delta_ps = (est["wns"] - greedy["wns"]) * 1000.0
    return f"  dWNS={delta_ps:+.1f}ps vs greedy"


def main() -> None:
    rows: list[str] = []
    for job in JOBS:
        greedy_path = logs_dir(job) / f"{GREEDY_STEM}.log"
        gp = parse_log(greedy_path)
        line = fmt_row(job["id"], "greedy", gp) + extra(gp)
        rows.append(line)
        print(line, flush=True)

        ep = parse_log(
            replay(
                job,
                EST_STEM,
                guided=True,
                vs_nop=True,
                clip_after=False,
                faster_champion=True,
            )
        )
        line = fmt_row(job["id"], "est", ep) + extra(ep) + dwns(ep, gp)
        rows.append(line)
        print(line, flush=True)

    OUT.write_text("\n".join(rows) + "\n")
    log(f"wrote {OUT}")


if __name__ == "__main__":
    main()
