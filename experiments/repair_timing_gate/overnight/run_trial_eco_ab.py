#!/usr/bin/env python3
"""Pack002 only: champion vs each trial-ECO speedup, one flag at a time."""

from __future__ import annotations

from pathlib import Path

from run_mix_ext import JOBS, fmt_row, log, logs_dir, parse_log, replay

HERE = Path(__file__).resolve().parent
OUT = HERE / "trial_eco_ab_summary.txt"
CHAMP_STEM = "repair_simple_vs_nop"
JOB_ID = "ibex_pack002"
VARIANTS = [
    ("keep", {"keep_winner": True}),
    ("inv", {"inverse_undo": True}),
    ("one", {"one_sta": True}),
    ("skip", {"skip_restore_sta": True}),
]


def extra(p: dict) -> str:
    bits = []
    if p.get("sta") is not None:
        bits.append(
            f"eval={p['eval']} sta={p['sta']} commit={p['committed']} "
            f"ovr={p['override']}"
        )
    if p.get("swap") is not None:
        bits.append(f"swap={p['swap']} clone={p.get('clone')}")
    flags = [
        name
        for name in (
            "keep_winner",
            "inverse_undo",
            "one_sta",
            "skip_restore_sta",
        )
        if p.get(name)
    ]
    if flags:
        bits.append(" ".join(flags))
    return ("  " + " ".join(bits)) if bits else ""


def main() -> None:
    job = next(j for j in JOBS if j["id"] == JOB_ID)
    rows: list[str] = []
    champ = parse_log(logs_dir(job) / f"{CHAMP_STEM}.log")
    line = fmt_row(job["id"], "champ", champ) + extra(champ)
    rows.append(line)
    print(line, flush=True)

    for kind, flags in VARIANTS:
        parsed = parse_log(
            replay(
                job,
                f"repair_trial_{kind}",
                guided=True,
                vs_nop=True,
                clip_after=False,
                **flags,
            )
        )
        line = fmt_row(job["id"], kind, parsed) + extra(parsed)
        rows.append(line)
        print(line, flush=True)

    OUT.write_text("\n".join(rows) + "\n")
    log(f"wrote {OUT}")


if __name__ == "__main__":
    main()
