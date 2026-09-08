#!/usr/bin/env python3
"""Mirror the Tattvam silicompiler API into a local SQLite database.

Keeps configs, parameter diffs, stage metrics, exploration outcomes, and
tool calls (Tcl + transcript scripts). Drops LLM prose by default.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
DEFAULT_BASE = "https://tattvam-server.ngrok.dev"
SCHEMA_PATH = HERE / "schema.sql"
NUMERIC_TYPES = (int, float)


def to_sql(value: Any) -> Any:
    """SQLite-safe scalar. Nested objects become JSON."""
    if value is None or isinstance(value, (int, float, str)):
        return value
    if isinstance(value, bool):
        return int(value)
    return json.dumps(value, default=str)


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.executescript(SCHEMA_PATH.read_text())
    return conn


def set_meta(conn: sqlite3.Connection, key: str, value: Any) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO sync_meta(key, value) VALUES (?, ?)",
        (key, json.dumps(value) if not isinstance(value, str) else value),
    )


class Api:
    def __init__(self, base: str, timeout: float, cache_dir: Path, force: bool):
        self.base = base.rstrip("/")
        self.timeout = timeout
        self.cache_dir = cache_dir
        self.force = force
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def cache_path(self, name: str) -> Path:
        safe = name.replace("/", "_").replace("?", "_").replace("&", "_")
        return self.cache_dir / f"{safe}.json"

    def get(
        self,
        path: str,
        *,
        cache_name: str | None = None,
        use_cache: bool = False,
    ) -> tuple[Any | None, int, int, str | None]:
        """Return (payload, http_status, bytes, error)."""
        cache_file = self.cache_path(cache_name) if cache_name else None
        if use_cache and not self.force and cache_file and cache_file.exists():
            raw = cache_file.read_bytes()
            try:
                return json.loads(raw), 200, len(raw), None
            except json.JSONDecodeError:
                pass

        url = self.base + path
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "tattvam-db-sync/1.0",
                "ngrok-skip-browser-warning": "true",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read()
                status = getattr(resp, "status", 200)
        except urllib.error.HTTPError as exc:
            raw = exc.read() or b""
            return _maybe_json(raw), exc.code, len(raw), f"HTTP {exc.code}"
        except Exception as exc:  # noqa: BLE001 — want the sync to continue
            return None, 0, 0, str(exc)

        payload = _maybe_json(raw)
        if cache_file is not None and status == 200 and payload is not None:
            cache_file.write_bytes(raw)
        return payload, status, len(raw), None


def _maybe_json(raw: bytes) -> Any | None:
    if not raw:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def log_fetch(
    conn: sqlite3.Connection,
    path: str,
    run_id: str | None,
    status: int,
    n_bytes: int,
    cached: bool,
    error: str | None,
) -> None:
    conn.execute(
        """
        INSERT INTO fetch_log(path, run_id, fetched_at, http_status, bytes, cached, error)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (path, run_id, utcnow(), status, n_bytes, int(cached), error),
    )


def flatten_metrics(obj: Any, prefix: str = "") -> list[tuple[str, float | None, str | None]]:
    rows: list[tuple[str, float | None, str | None]] = []
    if obj is None:
        return rows
    if isinstance(obj, dict):
        for key, val in obj.items():
            name = f"{prefix}.{key}" if prefix else str(key)
            rows.extend(flatten_metrics(val, name))
        return rows
    if isinstance(obj, bool):
        rows.append((prefix, float(obj), str(obj)))
        return rows
    if isinstance(obj, NUMERIC_TYPES) and not isinstance(obj, bool):
        rows.append((prefix, float(obj), None))
        return rows
    if isinstance(obj, list):
        if all(isinstance(x, NUMERIC_TYPES) for x in obj):
            rows.append((prefix, None, json.dumps(obj)))
            if obj:
                rows.append((f"{prefix}._len", float(len(obj)), None))
                rows.append((f"{prefix}._last", float(obj[-1]), None))
                rows.append((f"{prefix}._min", float(min(obj)), None))
                rows.append((f"{prefix}._max", float(max(obj)), None))
        else:
            rows.append((prefix, None, json.dumps(obj)[:4000]))
        return rows
    rows.append((prefix, None, str(obj)[:4000]))
    return rows


def upsert_run(conn: sqlite3.Connection, listing: dict, detail: dict | None) -> None:
    src = {**listing, **(detail or {})}
    target = src.get("target") or {}
    conn.execute(
        """
        INSERT OR REPLACE INTO runs(
            run_id, design, origin, intent, area_um2_max, period_ns_max, power_w_max,
            scope, corners, config_mode, agent_mode, tcl_live, seeding, model, server,
            started_at, running, paused, controllable, listing_origin, synced_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            src["run_id"],
            src.get("design"),
            src.get("origin"),
            to_sql(src.get("intent")),
            target.get("area_um2_max") if isinstance(target, dict) else None,
            target.get("period_ns_max") if isinstance(target, dict) else None,
            target.get("power_w_max") if isinstance(target, dict) else None,
            to_sql(src.get("scope")),
            to_sql(src.get("corners")),
            to_sql(src.get("config_mode")),
            to_sql(src.get("agent_mode")),
            int(bool(src.get("tcl_live"))) if src.get("tcl_live") is not None else None,
            src.get("seeding"),
            src.get("model"),
            src.get("server"),
            src.get("started_at"),
            int(bool(src.get("running"))) if src.get("running") is not None else None,
            int(bool(src.get("paused"))) if src.get("paused") is not None else None,
            int(bool(src.get("controllable"))) if src.get("controllable") is not None else None,
            listing.get("origin"),
            utcnow(),
        ),
    )


def replace_children(conn: sqlite3.Connection, table: str, run_id: str) -> None:
    conn.execute(f"DELETE FROM {table} WHERE run_id = ?", (run_id,))


def ingest_pdk(conn: sqlite3.Connection, run_id: str, pdk: dict) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO pdk_info(
            run_id, design, top_module, platform, pdk_name, process_node,
            stdcell_library, metal_stack, nominal_voltage_v, clock_period_ns,
            clock_name, corners_json, sdc_path, notes_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            pdk.get("design"),
            pdk.get("top_module"),
            pdk.get("platform"),
            pdk.get("pdk_name"),
            pdk.get("process_node"),
            pdk.get("stdcell_library"),
            pdk.get("metal_stack"),
            pdk.get("nominal_voltage_v"),
            pdk.get("clock_period_ns"),
            pdk.get("clock_name"),
            json.dumps(pdk.get("corners") or []),
            ((pdk.get("constraint") or {}).get("path")),
            json.dumps(pdk.get("notes") or []),
        ),
    )


def ingest_candidates(conn: sqlite3.Connection, run_id: str, cands: list[dict]) -> None:
    replace_children(conn, "tool_calls", run_id)
    replace_children(conn, "param_changes", run_id)
    replace_children(conn, "candidate_params", run_id)
    replace_children(conn, "stages", run_id)
    replace_children(conn, "candidates", run_id)

    cand_rows = []
    param_rows = []
    change_rows = []
    stage_rows = []
    tool_rows = []

    for cand in cands:
        cid = cand.get("id")
        if not cid:
            continue
        stages = cand.get("stages") or []
        changed = cand.get("changed_params") or []
        all_params = cand.get("all_params") or {}
        cand_rows.append(
            (
                run_id,
                cid,
                cand.get("iteration"),
                cand.get("timestamp"),
                cand.get("area_um2"),
                cand.get("elapsed_seconds"),
                int(bool(cand.get("routed"))),
                cand.get("outcome_state"),
                len(stages),
                len(changed),
                len(all_params),
            )
        )
        for param, value in all_params.items():
            param_rows.append((run_id, cid, param, None if value is None else str(value)))
        for ch in changed:
            if not isinstance(ch, dict):
                continue
            change_rows.append(
                (
                    run_id,
                    cid,
                    None,
                    ch.get("param"),
                    None if ch.get("previous") is None else str(ch.get("previous")),
                    None if ch.get("current") is None else str(ch.get("current")),
                )
            )
        for idx, stage in enumerate(stages):
            if not isinstance(stage, dict):
                continue
            transcript = stage.get("tcl_transcript") or []
            intents = stage.get("specialist_intents") or []
            review = stage.get("master_review") or {}
            stage_name = stage.get("stage")
            label = stage.get("label")
            stage_rows.append(
                (
                    run_id,
                    cid,
                    idx,
                    stage_name,
                    label,
                    to_sql(stage.get("knobs")),
                    to_sql(stage.get("tcl")),
                    len(transcript) if isinstance(transcript, list) else 0,
                    len(intents) if isinstance(intents, list) else 0,
                    to_sql(review.get("concern")) if isinstance(review, dict) else None,
                    to_sql(review.get("intent")) if isinstance(review, dict) else None,
                )
            )
            for ch in stage.get("changed_params") or []:
                if not isinstance(ch, dict):
                    continue
                change_rows.append(
                    (
                        run_id,
                        cid,
                        stage_name,
                        ch.get("param"),
                        None if ch.get("previous") is None else str(ch.get("previous")),
                        None if ch.get("current") is None else str(ch.get("current")),
                    )
                )
            if stage.get("tcl"):
                tool_rows.append(
                    (
                        run_id,
                        cid,
                        stage_name,
                        label,
                        None,
                        "stage_tcl",
                        None,
                        None,
                        to_sql(stage.get("tcl")),
                        None,
                        None,
                        None,
                        None,
                    )
                )
            if isinstance(intents, list):
                for intent in intents:
                    if not isinstance(intent, dict):
                        continue
                    tool_rows.append(
                        (
                            run_id,
                            cid,
                            stage_name,
                            label,
                            None,
                            "proposed",
                            to_sql(intent.get("concern")),
                            int(bool(intent.get("chosen"))),
                            to_sql(intent.get("intent")) if intent.get("intent") else None,
                            None,
                            None,
                            None,
                            None,
                        )
                    )
            if isinstance(review, dict) and review.get("intent"):
                tool_rows.append(
                    (
                        run_id,
                        cid,
                        stage_name,
                        label,
                        None,
                        "chosen",
                        to_sql(review.get("concern")),
                        1,
                        to_sql(review.get("intent")),
                        None,
                        None,
                        None,
                        None,
                    )
                )
            if isinstance(transcript, list):
                for turn in transcript:
                    if not isinstance(turn, dict):
                        continue
                    if turn.get("script") or turn.get("error") or turn.get("rejected") or turn.get("rewind_to"):
                        tool_rows.append(
                            (
                                run_id,
                                cid,
                                stage_name,
                                label,
                                turn.get("turn"),
                                "rewind" if turn.get("rewind_to") else "executed",
                                None,
                                None,
                                to_sql(turn.get("script")),
                                to_sql(turn.get("stdout")),
                                to_sql(turn.get("error") or turn.get("reason")),
                                int(bool(turn.get("rejected"))) if "rejected" in turn else None,
                                turn.get("rewind_to"),
                            )
                        )

    conn.executemany(
        """
        INSERT INTO candidates(
            run_id, candidate_id, iteration, timestamp, area_um2, elapsed_seconds,
            routed, outcome_state, n_stages, n_changed_params, n_all_params
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        cand_rows,
    )
    conn.executemany(
        "INSERT INTO candidate_params(run_id, candidate_id, param, value) VALUES (?, ?, ?, ?)",
        param_rows,
    )
    conn.executemany(
        """
        INSERT INTO param_changes(run_id, candidate_id, stage, param, previous, current)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        change_rows,
    )
    conn.executemany(
        """
        INSERT INTO stages(
            run_id, candidate_id, stage_index, stage, label, knobs, tcl,
            n_transcript_turns, n_specialist_intents, master_concern, master_intent
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        stage_rows,
    )
    conn.executemany(
        """
        INSERT INTO tool_calls(
            run_id, candidate_id, stage, label, turn, kind, concern, chosen,
            command, stdout, error, rejected, rewind_to
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        tool_rows,
    )


def ingest_status(conn: sqlite3.Connection, run_id: str, status: dict) -> None:
    replace_children(conn, "metrics", run_id)
    replace_children(conn, "exploration_points", run_id)
    exploration = status.get("exploration") or {}
    points = exploration.get("points") or []
    cms = status.get("candidate_metrics") or {}

    conn.execute(
        """
        INSERT OR REPLACE INTO run_status(
            run_id, design_name, design_goal, overall_status, mode, operating_mode,
            current_stage, started_at, elapsed_active_seconds, last_updated,
            tapeout_progress_pct, n_candidate_metrics, n_exploration_points,
            exploration_complete, selected_point_id, target_cuboid_json,
            remaining_milestones_json, stop_notice
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            status.get("design_name"),
            status.get("design_goal"),
            status.get("overall_status"),
            status.get("mode"),
            status.get("operating_mode"),
            status.get("current_stage"),
            status.get("started_at"),
            status.get("elapsed_active_seconds"),
            status.get("last_updated"),
            status.get("tapeout_progress_pct"),
            len(cms),
            len(points),
            int(bool(exploration.get("complete"))),
            exploration.get("selected_point_id"),
            json.dumps(exploration.get("target_cuboid")) if exploration.get("target_cuboid") else None,
            json.dumps(status.get("remaining_milestones")) if status.get("remaining_milestones") else None,
            json.dumps(status.get("stop_notice")) if status.get("stop_notice") else None,
        ),
    )

    point_rows = []
    for point in points:
        if not isinstance(point, dict) or not point.get("id"):
            continue
        point_rows.append(
            (
                run_id,
                point.get("id"),
                point.get("fmax_mhz"),
                point.get("power_total_w"),
                point.get("area_um2"),
                point.get("effective_period_ns"),
                point.get("achievable_period_ns"),
                point.get("closure_likelihood_pct"),
                int(bool(point.get("is_recommended"))),
                int(bool(point.get("excluded"))),
                int(bool(point.get("routed"))),
                int(bool(point.get("closed"))),
                int(bool(point.get("failed"))),
                int(bool(point.get("tapeout_failed"))),
                point.get("state"),
            )
        )
    conn.executemany(
        """
        INSERT INTO exploration_points(
            run_id, candidate_id, fmax_mhz, power_total_w, area_um2,
            effective_period_ns, achievable_period_ns, closure_likelihood_pct,
            is_recommended, excluded, routed, closed, failed, tapeout_failed, state
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        point_rows,
    )

    metric_rows = []
    for cid, stages in cms.items():
        if not isinstance(stages, dict):
            continue
        for stage, payload in stages.items():
            for metric, num, text in flatten_metrics(payload):
                metric_rows.append((run_id, cid, stage, metric, num, text))
    conn.executemany(
        """
        INSERT OR REPLACE INTO metrics(run_id, candidate_id, stage, metric, value_num, value_text)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        metric_rows,
    )


def ingest_eval(conn: sqlite3.Connection, run_id: str, ev: dict) -> None:
    replace_children(conn, "eval_checks", run_id)
    replace_children(conn, "eval_candidates", run_id)
    traj = ev.get("trajectory") or {}
    assessment = ev.get("assessment") or {}
    conn.execute(
        """
        INSERT OR REPLACE INTO eval_runs(
            run_id, generated_at, present, n_candidates, totals_json, run_stats_json,
            trust_gate_json, assessment_verdict, assessment_score, trajectory_objective,
            n_routed_clean, first_clean, best_die
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            ev.get("generated_at"),
            int(bool(ev.get("present", True))),
            len(ev.get("candidates") or []),
            json.dumps(ev.get("totals")) if ev.get("totals") is not None else None,
            json.dumps(ev.get("run_stats")) if ev.get("run_stats") is not None else None,
            json.dumps(ev.get("trust_gate")) if ev.get("trust_gate") is not None else None,
            to_sql(assessment.get("verdict")),
            assessment.get("score") if isinstance(assessment.get("score"), NUMERIC_TYPES) else None,
            to_sql(
                (traj.get("objective") or {}).get("label")
                if isinstance(traj.get("objective"), dict)
                else traj.get("objective")
            ),
            traj.get("n_routed_clean") if isinstance(traj.get("n_routed_clean"), NUMERIC_TYPES) else None,
            to_sql(traj.get("first_clean")),
            traj.get("best_die") if isinstance(traj.get("best_die"), NUMERIC_TYPES) else None,
        ),
    )
    check_rows = []
    for check in ev.get("checks") or []:
        if not isinstance(check, dict):
            continue
        check_rows.append(
            (
                run_id,
                check.get("name"),
                check.get("group"),
                check.get("step"),
                check.get("score"),
                check.get("n_pass"),
                check.get("n_fail"),
                check.get("n_na"),
                int(bool(check.get("disabled"))),
                to_sql(check.get("question")),
            )
        )
    conn.executemany(
        """
        INSERT INTO eval_checks(
            run_id, name, grp, step, score, n_pass, n_fail, n_na, disabled, question
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        check_rows,
    )
    cand_rows = []
    for cand in ev.get("candidates") or []:
        if not isinstance(cand, dict) or not cand.get("id"):
            continue
        knobs = cand.get("knobs_touched") or []
        names = []
        for knob in knobs:
            if isinstance(knob, dict):
                names.append(knob.get("knob") or knob.get("name") or "")
            else:
                names.append(str(knob))
        cand_rows.append(
            (
                run_id,
                cand.get("id"),
                cand.get("status"),
                cand.get("die_area_um2"),
                cand.get("final_util_pct"),
                cand.get("util_kind"),
                cand.get("n_findings"),
                ",".join(n for n in names if n),
            )
        )
    conn.executemany(
        """
        INSERT INTO eval_candidates(
            run_id, candidate_id, status, die_area_um2, final_util_pct, util_kind,
            n_findings, knobs_touched
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        cand_rows,
    )


def qpath(path: str, **params: Any) -> str:
    qs = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    return f"{path}?{qs}" if qs else path


def fetch_and_log(
    api: Api,
    conn: sqlite3.Connection,
    path: str,
    *,
    run_id: str | None = None,
    cache_name: str | None = None,
    use_cache: bool = False,
) -> Any | None:
    payload, status, n_bytes, error = api.get(path, cache_name=cache_name, use_cache=use_cache)
    cached = bool(use_cache and error is None and status == 200)
    log_fetch(conn, path, run_id, status, n_bytes, cached, error)
    if error:
        print(f"  ! {path} {error} ({n_bytes} B)", file=sys.stderr)
        return None
    print(f"  {path} {status} {n_bytes:,} B", flush=True)
    return payload


def sync_run(
    api: Api,
    conn: sqlite3.Connection,
    listing: dict,
    *,
    with_eval: bool,
    skip_eval_raw: bool,
) -> None:
    run_id = listing["run_id"]
    design = listing.get("design")
    running = bool(listing.get("running"))
    use_cache = not running

    print(f"\n== {run_id} ({design}) running={running} ==", flush=True)

    detail = fetch_and_log(
        api,
        conn,
        f"/api/flow/run/{run_id}",
        run_id=run_id,
        cache_name=f"run_{run_id}",
        use_cache=use_cache,
    )
    if not isinstance(detail, dict):
        detail = None
    upsert_run(conn, listing, detail)

    pdk = fetch_and_log(
        api,
        conn,
        qpath("/api/flow/pdk-info", design=design, run_id=run_id),
        run_id=run_id,
        cache_name=f"pdk_{run_id}",
        use_cache=use_cache,
    )
    if isinstance(pdk, dict):
        ingest_pdk(conn, run_id, pdk)

    cands = fetch_and_log(
        api,
        conn,
        qpath("/api/flow/reasoning/candidates", design=design, run_id=run_id),
        run_id=run_id,
        cache_name=f"candidates_{run_id}",
        use_cache=use_cache,
    )
    if isinstance(cands, list):
        ingest_candidates(conn, run_id, cands)
        print(f"    candidates={len(cands)}")
    elif isinstance(cands, dict) and isinstance(cands.get("candidates"), list):
        ingest_candidates(conn, run_id, cands["candidates"])
        print(f"    candidates={len(cands['candidates'])}")

    status = fetch_and_log(
        api,
        conn,
        qpath("/api/flow/status", design=design, run_id=run_id),
        run_id=run_id,
        cache_name=f"status_{run_id}",
        use_cache=use_cache,
    )
    if isinstance(status, dict):
        ingest_status(conn, run_id, status)
        print(
            f"    metrics={len(status.get('candidate_metrics') or {})} "
            f"points={len((status.get('exploration') or {}).get('points') or [])}"
        )

    if with_eval:
        ev = fetch_and_log(
            api,
            conn,
            qpath("/api/flow/eval", run_id=run_id),
            run_id=run_id,
            cache_name=None if skip_eval_raw else f"eval_{run_id}",
            use_cache=use_cache and not skip_eval_raw,
        )
        if isinstance(ev, dict) and (ev.get("present") or ev.get("candidates") or ev.get("checks")):
            ingest_eval(conn, run_id, ev)
            print(f"    eval candidates={len(ev.get('candidates') or [])}")

    conn.commit()


def summarize(conn: sqlite3.Connection) -> None:
    print("\n==== local database ====")
    for table in [
        "runs",
        "candidates",
        "candidate_params",
        "param_changes",
        "stages",
        "tool_calls",
        "metrics",
        "exploration_points",
        "eval_runs",
        "eval_checks",
    ]:
        n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table:22} {n:,}")

    print("\nruns:")
    rows = conn.execute(
        """
        SELECT r.run_id, r.design, r.config_mode, r.agent_mode, r.tcl_live, r.model,
               r.running, COUNT(c.candidate_id) AS n_cands
        FROM runs r
        LEFT JOIN candidates c ON c.run_id = r.run_id
        GROUP BY r.run_id
        ORDER BY r.started_at IS NULL, r.started_at
        """
    ).fetchall()
    for row in rows:
        print(
            f"  {row['run_id']:34} {row['design']:5} "
            f"mode={row['config_mode']}/{row['agent_mode']} tcl={row['tcl_live']} "
            f"cands={row['n_cands']:4} running={row['running']} {row['model'] or ''}"
        )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base", default=DEFAULT_BASE, help="silicompiler API base URL")
    p.add_argument("--db", default=str(HERE / "data" / "tattvam.sqlite"))
    p.add_argument("--cache", default=str(HERE / "cache"))
    p.add_argument("--timeout", type=float, default=180)
    p.add_argument("--force", action="store_true", help="ignore cache even for finished runs")
    p.add_argument("--no-eval", action="store_true", help="skip /api/flow/eval (huge, mostly prose)")
    p.add_argument("--keep-eval-raw", action="store_true", help="also cache full eval JSON")
    p.add_argument("--only", nargs="*", help="restrict to these run_ids")
    p.add_argument("--sleep", type=float, default=0.2, help="pause between runs")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    db_path = Path(args.db)
    cache_dir = Path(args.cache)
    conn = connect(db_path)
    api = Api(args.base, args.timeout, cache_dir, args.force)

    listing = fetch_and_log(
        api,
        conn,
        "/api/flow/runs",
        cache_name="runs",
        use_cache=False,
    )
    if not isinstance(listing, dict):
        print("failed to list runs", file=sys.stderr)
        return 1

    runs = (listing.get("latest") or []) + (listing.get("older") or [])
    if args.only:
        want = set(args.only)
        runs = [r for r in runs if r.get("run_id") in want]

    print(f"syncing {len(runs)} runs from {api.base}")
    set_meta(conn, "base", api.base)
    set_meta(conn, "last_sync", utcnow())
    conn.commit()

    for listing_row in runs:
        try:
            sync_run(
                api,
                conn,
                listing_row,
                with_eval=not args.no_eval,
                skip_eval_raw=not args.keep_eval_raw,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"  failed {listing_row.get('run_id')}: {exc}", file=sys.stderr)
            conn.rollback()
        time.sleep(args.sleep)

    summarize(conn)
    conn.close()
    print(f"\nSQLite: {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
