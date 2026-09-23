#!/usr/bin/env python3
"""Greedy vs clip-first vs greedy-then-clip A/B on gcd, aes, ibex, jpeg."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FLOW = ROOT / "flow"
HERE = Path(__file__).resolve().parent
REPLAY = ROOT / "experiments" / "repair_timing_gate" / "replay_setup.tcl"
BUILD_OR = ROOT / "tools" / "OpenROAD" / "build" / "bin" / "openroad"
INSTALL_OR = ROOT / "tools" / "install" / "OpenROAD" / "bin" / "openroad"
SUMMARY = Path(os.environ.get("MIX_SUMMARY", str(HERE / "mix_ext_summary_v7.txt")))
SWITCH_STEM = os.environ.get("MIX_SWITCH_STEM", "repair_switch_v7")
GREEDY_STEM = os.environ.get("MIX_GREEDY_STEM", "repair_legacy_v4")

JOBS = [
    {
        "id": "gcd",
        "design": "gcd",
        "config": FLOW / "designs/nangate45/gcd/config.mk",
        "variant": "rt_mix_gate",
        "place_src": FLOW / "results/nangate45/gcd/base",
        "tight_sdc": None,
    },
    {
        "id": "aes_p065",
        "design": "aes",
        "config": FLOW / "designs/nangate45/aes/config.mk",
        "variant": "rt_aes_gate",
        "place_src": None,
        "tight_sdc": "4_1_pre_repair_setup_hold_p065.sdc",
    },
    {
        "id": "ibex_pack002",
        "design": "ibex",
        "config": ROOT
        / "experiments/ppa_prediction/generated/ibex/configs/traj_ibex_pack_002.mk",
        "variant": "rt_ovn_pack002",
        "place_src": None,
        "tight_sdc": None,
    },
    {
        "id": "ibex_pack010",
        "design": "ibex",
        "config": ROOT
        / "experiments/ppa_prediction/generated/ibex/configs/traj_ibex_pack_010.mk",
        "variant": "rt_ovn_pack010",
        "place_src": None,
        "tight_sdc": None,
    },
    {
        "id": "ibex_pack012",
        "design": "ibex",
        "config": ROOT
        / "experiments/ppa_prediction/generated/ibex/configs/traj_ibex_pack_012.mk",
        "variant": "rt_ovn_pack012",
        "place_src": None,
        "tight_sdc": None,
    },
    {
        "id": "ibex_pack013",
        "design": "ibex",
        "config": ROOT
        / "experiments/ppa_prediction/generated/ibex/configs/traj_ibex_pack_013.mk",
        "variant": "rt_ovn_pack013",
        "place_src": None,
        "tight_sdc": None,
    },
    {
        "id": "jpeg",
        "design": "jpeg",
        "config": FLOW / "designs/nangate45/jpeg/config.mk",
        "variant": "rt_mix_gate",
        "place_src": None,
        "tight_sdc": None,
    },
]


def log(msg: str) -> None:
    print(f"{time.strftime('%H:%M:%S')} {msg}", flush=True)


def results_dir(job: dict) -> Path:
    return FLOW / "results" / "nangate45" / job["design"] / job["variant"]


def logs_dir(job: dict) -> Path:
    return FLOW / "logs" / "nangate45" / job["design"] / job["variant"]


def snapshot_odb(job: dict) -> Path:
    return results_dir(job) / "4_1_pre_repair_setup_hold.odb"


def run_make(args: list[str], env: dict[str, str], log_path: Path) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["make", "-C", str(FLOW), *args]
    env = dict(env)
    env["MAKEFLAGS"] = ""
    with log_path.open("w") as fh:
        proc = subprocess.run(
            cmd, cwd=FLOW, env=env, stdout=fh, stderr=subprocess.STDOUT, text=True
        )
    return proc.returncode


def ensure_gcd_place(job: dict) -> None:
    src = job["place_src"]
    dest = results_dir(job)
    dest.mkdir(parents=True, exist_ok=True)
    logs_dir(job).mkdir(parents=True, exist_ok=True)
    for name in ("3_place.odb", "3_place.sdc"):
        s, d = src / name, dest / name
        if s.is_file() and not d.is_file():
            shutil.copy2(s, d)


def build_snapshot(job: dict) -> None:
    if snapshot_odb(job).is_file():
        log(f"snapshot exists {job['id']}")
        return
    log(f"snapshot CTS {job['id']}")
    env = os.environ.copy()
    or_exe = str(INSTALL_OR if INSTALL_OR.is_file() else BUILD_OR)
    extra = [
        f"DESIGN_CONFIG={job['config']}",
        f"FLOW_VARIANT={job['variant']}",
        f"OPENROAD_EXE={or_exe}",
        "NUM_CORES=8",
        "SKIP_CTS_REPAIR_TIMING=1",
        "CTS_SNAPSHOTS=1",
    ]
    make_log = HERE / f"snap_{job['id']}.make.log"
    if job["place_src"] is not None:
        ensure_gcd_place(job)
        rc = run_make([*extra, "do-4_1_cts"], env, make_log)
        if rc != 0 or not snapshot_odb(job).is_file():
            log(f"do-4_1_cts failed {job['id']} rc={rc}, trying make cts")
            rc = run_make([*extra, "cts"], env, make_log)
    else:
        rc = run_make([*extra, "cts"], env, make_log)
    if rc != 0 or not snapshot_odb(job).is_file():
        raise SystemExit(f"snapshot failed {job['id']} rc={rc} log={make_log}")
    log(f"snapshot ok {job['id']}")


def replay(job: dict, stem: str, guided: bool = False, clip_after: bool = False, knot: bool = False, simple: bool = False, vs_nop: bool = False, tns_end: int | None = None, tourney_min_fanout: int | None = None, faster_champion: bool = False, greedy_abort: bool = False, cheap_sta: bool = False, keep_winner: bool = False, inverse_undo: bool = False, one_sta: bool = False, skip_restore_sta: bool = False) -> Path:
    env = os.environ.copy()
    env.pop("RSZ_GUIDED_PICK", None)
    env.pop("RSZ_GUIDED_CLIP", None)
    env.pop("RSZ_GUIDED_KNOT", None)
    env.pop("RSZ_SIMPLE_TOURNEY", None)
    env.pop("RSZ_SIMPLE_VS_NOP", None)
    env.pop("RSZ_TOURNEY_MIN_FANOUT", None)
    env.pop("RSZ_FASTER_CHAMPION", None)
    env.pop("RSZ_GREEDY_ABORT", None)
    env.pop("RSZ_CHEAP_STA", None)
    env.pop("RSZ_KEEP_WINNER", None)
    env.pop("RSZ_INVERSE_UNDO", None)
    env.pop("RSZ_ONE_STA", None)
    env.pop("RSZ_SKIP_RESTORE_STA", None)
    env["RSZ_GUIDED_PICK"] = "1" if guided else "0"
    if guided:
        env["RSZ_GUIDED_CLIP"] = "after" if clip_after else "first"
    extra = [
        f"DESIGN_CONFIG={job['config']}",
        f"FLOW_VARIANT={job['variant']}",
        f"OPENROAD_EXE={BUILD_OR}",
        "NUM_CORES=4",
        f"RUN_SCRIPT={REPLAY}",
        f"RUN_LOG_NAME_STEM={stem}",
        "REPAIR_TIMING_EXTRA_ARGS=-phases LEGACY",
        f"RSZ_GUIDED_PICK={env['RSZ_GUIDED_PICK']}",
        "run",
    ]
    if guided:
        extra.insert(-1, f"RSZ_GUIDED_CLIP={env['RSZ_GUIDED_CLIP']}")
        far_rel = os.environ.get("RSZ_GUIDED_FAR_REL")
        if far_rel:
            env["RSZ_GUIDED_FAR_REL"] = far_rel
            extra.insert(-1, f"RSZ_GUIDED_FAR_REL={far_rel}")
    if knot:
        env["RSZ_GUIDED_KNOT"] = "1"
        extra.insert(-1, "RSZ_GUIDED_KNOT=1")
    if simple:
        env["RSZ_SIMPLE_TOURNEY"] = "1"
        extra.insert(-1, "RSZ_SIMPLE_TOURNEY=1")
    if vs_nop:
        env["RSZ_SIMPLE_VS_NOP"] = "1"
        extra.insert(-1, "RSZ_SIMPLE_VS_NOP=1")
    if tns_end is not None:
        env["TNS_END_PERCENT"] = str(tns_end)
        extra.insert(-1, f"TNS_END_PERCENT={tns_end}")
    if tourney_min_fanout is not None:
        env["RSZ_TOURNEY_MIN_FANOUT"] = str(tourney_min_fanout)
        extra.insert(-1, f"RSZ_TOURNEY_MIN_FANOUT={tourney_min_fanout}")
    if faster_champion:
        env["RSZ_FASTER_CHAMPION"] = "1"
        extra.insert(-1, "RSZ_FASTER_CHAMPION=1")
    if greedy_abort:
        env["RSZ_GREEDY_ABORT"] = "1"
        extra.insert(-1, "RSZ_GREEDY_ABORT=1")
    if cheap_sta:
        env["RSZ_CHEAP_STA"] = "1"
        extra.insert(-1, "RSZ_CHEAP_STA=1")
    if keep_winner:
        env["RSZ_KEEP_WINNER"] = "1"
        extra.insert(-1, "RSZ_KEEP_WINNER=1")
    if inverse_undo:
        env["RSZ_INVERSE_UNDO"] = "1"
        extra.insert(-1, "RSZ_INVERSE_UNDO=1")
    if one_sta:
        env["RSZ_ONE_STA"] = "1"
        extra.insert(-1, "RSZ_ONE_STA=1")
    if skip_restore_sta:
        env["RSZ_SKIP_RESTORE_STA"] = "1"
        extra.insert(-1, "RSZ_SKIP_RESTORE_STA=1")
    if job["tight_sdc"]:
        extra.insert(-1, f"REPAIR_REPLAY_SDC={job['tight_sdc']}")
        env["REPAIR_REPLAY_SDC"] = job["tight_sdc"]
    make_log = HERE / f"{job['id']}_{stem}.make.log"
    log(f"replay {job['id']} {stem} guided={guided} clip_after={clip_after} knot={knot} simple={simple} vs_nop={vs_nop} tns_end={tns_end if tns_end is not None else '-'} far_rel={env.get('RSZ_GUIDED_FAR_REL', '-')} fo_min={tourney_min_fanout if tourney_min_fanout is not None else '-'} faster={faster_champion} greedy_abort={greedy_abort} cheap_sta={cheap_sta} keep={keep_winner} inv={inverse_undo} one={one_sta} skip={skip_restore_sta}")
    started = time.time()
    rc = run_make(extra, env, make_log)
    elapsed = time.time() - started
    log_path = logs_dir(job) / f"{stem}.log"
    if rc != 0:
        log(f"FAIL {job['id']} {stem} rc={rc} {elapsed:.0f}s")
    else:
        log(f"done {job['id']} {stem} {elapsed:.0f}s")
    return log_path


def parse_log(path: Path) -> dict:
    row = {"log": str(path), "exists": path.is_file()}
    if not path.is_file():
        return row
    text = path.read_text(errors="replace")
    modes = re.findall(
        r"Guided-pick: (pile, using greedy|tail, tournament on all pins|"
        r"tail, clipping worst pin|"
        r"no slack tail, using greedy|slack tail present, tournament)",
        text,
    )
    def mode_name(label: str) -> str:
        if "pile" in label or "no slack tail" in label:
            return "pile"
        if "tournament" in label or "clipping" in label or "tail" in label:
            return "tail"
        return label

    row["tail_modes"] = modes
    if modes:
        row["tail_mode"] = mode_name(modes[-1])
        row["tail_mode0"] = mode_name(modes[0])
        row["mode_hops"] = max(0, len(modes) - 1)
    else:
        row["tail_mode"] = ""
        row["tail_mode0"] = ""
        row["mode_hops"] = 0
    row["stalled"] = "WNS stalled for 80" in text
    row["hard_stop"] = "stopping setup repair" in text
    row["guided"] = "Guided-pick enabled" in text
    m = re.search(r"=== BEFORE repair_timing ===\s*\nwns max ([-\d.]+)\s*\ntns max ([-\d.]+)", text)
    if m:
        row["wns0"] = float(m.group(1))
        row["tns0"] = float(m.group(2))
    m = re.search(r"=== AFTER repair_timing ===\s*\nwns max ([-\d.]+)\s*\ntns max ([-\d.]+)", text)
    if m:
        row["wns"] = float(m.group(1))
        row["tns"] = float(m.group(2))
    m = re.search(r"Runtime: ([\d.]+)s", text)
    if m:
        row["runtime"] = float(m.group(1))
    m = re.search(
        r"^\s*final\s+\|\s+\d+\s+\|\s+(\d+)\s+\|\s+(\d+)\s+\|\s+(\d+)\s+\|\s+(\d+)\s+\|\s+([+\-0-9.%]+)\s+\|\s+([+\-0-9.]+)",
        text,
        re.M,
    )
    if m:
        row["up"] = int(m.group(1))
        row["buf"] = int(m.group(2))
        row["clone"] = int(m.group(3))
        row["swap"] = int(m.group(4))
        row["area"] = m.group(5)
        row["wns_tbl"] = float(m.group(6))
    m = re.search(
        r"Guided-pick: evaluated (\d+) pins, STA (\d+), committed (\d+), overrode first-success (\d+)",
        text,
    )
    if m:
        row["eval"] = int(m.group(1))
        row["sta"] = int(m.group(2))
        row["committed"] = int(m.group(3))
        row["override"] = int(m.group(4))
    m = re.search(
        r"Delay contest: (\d+) pins \(fanout>=(\d+)\), size-up-only (\d+)",
        text,
    )
    if m:
        row["delay_contest"] = int(m.group(1))
        row["delay_fo"] = int(m.group(2))
        row["delay_direct"] = int(m.group(3))
    m = re.search(
        r"Faster champion: estimator delay contest on (\d+) pins \(delay_levels=(\d+)\)",
        text,
    )
    if m:
        row["estimator"] = int(m.group(1))
        row["est_levels"] = int(m.group(2))
    row["cheap_sta"] = "Cheap STA" in text
    row["greedy_abort"] = "same abort as greedy" in text or "Greedy abort" in text
    row["keep_winner"] = "Keep winner" in text
    row["inverse_undo"] = "Inverse undo" in text
    row["one_sta"] = "One STA" in text
    row["skip_restore_sta"] = "Skip restore STA" in text
    return row


def fmt_row(job_id: str, kind: str, p: dict) -> str:
    if not p.get("exists"):
        return f"{job_id:16} {kind:6} MISSING"
    wns = p.get("wns", p.get("wns_tbl"))
    tns = p.get("tns")
    return (
        f"{job_id:16} {kind:6} WNS {wns!s:>7} TNS {tns!s:>8} "
        f"area {p.get('area','?'):>6} up={p.get('up','?'):>4} buf={p.get('buf','?'):>4} "
        f"t={p.get('runtime','?'):>7}s mode0={p.get('tail_mode0','?'):5} "
        f"mode={p.get('tail_mode','?'):5} hops={p.get('mode_hops', 0)} "
        f"stall={p.get('stalled')} hard={p.get('hard_stop')}"
    )


def maybe_tighten_jpeg(job: dict) -> None:
    """Squeeze jpeg only if the default 1.0 ns clock is easy (|WNS| < 40 ps)."""
    js = logs_dir(job) / "4_1_cts.json"
    wns = None
    if js.is_file():
        import json

        data = json.loads(js.read_text())
        wns = data.get("cts__timing__setup__ws")
    log(f"jpeg snapshot WNS={wns}")
    if wns is None or abs(float(wns)) >= 0.04:
        return
    sdc = results_dir(job) / "4_1_pre_repair_setup_hold.sdc"
    if not sdc.is_file():
        return
    text = sdc.read_text()
    m = re.search(r"-period\s+([0-9.]+)", text)
    if not m:
        return
    period = float(m.group(1))
    tight = results_dir(job) / "4_1_pre_repair_setup_hold_p080.sdc"
    tight.write_text(
        text.replace(f"-period {m.group(1)}", f"-period {period * 0.80:.4f}")
    )
    job["tight_sdc"] = tight.name
    log(f"jpeg easy ({wns}); companion SDC {period:.4f} -> {period * 0.80:.4f}")


def main() -> int:
    if not BUILD_OR.is_file():
        raise SystemExit(f"missing {BUILD_OR}")
    wanted = None
    if len(sys.argv) > 1:
        wanted = set(sys.argv[1].split(","))
    jobs = [j for j in JOBS if wanted is None or j["id"] in wanted]
    for job in jobs:
        if not snapshot_odb(job).is_file():
            build_snapshot(job)
        else:
            log(f"snapshot exists {job['id']}")

    jpeg = next((j for j in jobs if j["id"] == "jpeg"), None)
    if jpeg is not None:
        maybe_tighten_jpeg(jpeg)

    lines = []
    for job in jobs:
        greedy_path = logs_dir(job) / f"{GREEDY_STEM}.log"
        if greedy_path.is_file() and "=== AFTER repair_timing ===" in greedy_path.read_text(
            errors="replace"
        ):
            log(f"reuse {job['id']} {GREEDY_STEM}")
            g = greedy_path
        else:
            g = replay(job, GREEDY_STEM, guided=False)
        switch_path = logs_dir(job) / f"{SWITCH_STEM}.log"
        if switch_path.is_file() and "=== AFTER repair_timing ===" in switch_path.read_text(
            errors="replace"
        ):
            log(f"reuse {job['id']} {SWITCH_STEM}")
            m = switch_path
        else:
            m = replay(job, SWITCH_STEM, guided=True, clip_after=False)
        gp, mp = parse_log(g), parse_log(m)
        lines.append(fmt_row(job["id"], "greedy", gp))
        lines.append(fmt_row(job["id"], "switch", mp))
        if gp.get("wns") is not None and mp.get("wns") is not None:
            lines[-1] += f"  dWNS={(mp['wns'] - gp['wns']) * 1000:+.1f}ps vs greedy"

    text = "\n".join(lines) + "\n"
    SUMMARY.write_text(text)
    print(
        f"\n=== mix {SWITCH_STEM} far u>{os.environ.get('RSZ_GUIDED_FAR_REL', '0.10')} ==="
    )
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
