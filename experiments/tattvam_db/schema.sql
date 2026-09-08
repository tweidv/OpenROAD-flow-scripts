-- Tattvam / silicompiler local mirror.
-- Prose (reasoning, expected, eval writeups) is intentionally omitted.

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS sync_meta (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS fetch_log (
    path TEXT NOT NULL,
    run_id TEXT,
    fetched_at TEXT NOT NULL,
    http_status INTEGER,
    bytes INTEGER,
    cached INTEGER NOT NULL DEFAULT 0,
    error TEXT,
    PRIMARY KEY (path, fetched_at)
);

CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    design TEXT NOT NULL,
    origin TEXT,
    intent TEXT,
    area_um2_max REAL,
    period_ns_max REAL,
    power_w_max REAL,
    scope TEXT,
    corners TEXT,
    config_mode TEXT,
    agent_mode TEXT,
    tcl_live INTEGER,
    seeding TEXT,
    model TEXT,
    server TEXT,
    started_at TEXT,
    running INTEGER,
    paused INTEGER,
    controllable INTEGER,
    listing_origin TEXT,
    synced_at TEXT
);

CREATE TABLE IF NOT EXISTS pdk_info (
    run_id TEXT PRIMARY KEY,
    design TEXT,
    top_module TEXT,
    platform TEXT,
    pdk_name TEXT,
    process_node TEXT,
    stdcell_library TEXT,
    metal_stack TEXT,
    nominal_voltage_v REAL,
    clock_period_ns REAL,
    clock_name TEXT,
    corners_json TEXT,
    sdc_path TEXT,
    notes_json TEXT,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS candidates (
    run_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    iteration INTEGER,
    timestamp TEXT,
    area_um2 REAL,
    elapsed_seconds REAL,
    routed INTEGER,
    outcome_state TEXT,
    n_stages INTEGER,
    n_changed_params INTEGER,
    n_all_params INTEGER,
    PRIMARY KEY (run_id, candidate_id),
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS candidate_params (
    run_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    param TEXT NOT NULL,
    value TEXT,
    PRIMARY KEY (run_id, candidate_id, param),
    FOREIGN KEY (run_id, candidate_id) REFERENCES candidates(run_id, candidate_id)
);

CREATE TABLE IF NOT EXISTS param_changes (
    run_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    stage TEXT,
    param TEXT NOT NULL,
    previous TEXT,
    current TEXT,
    FOREIGN KEY (run_id, candidate_id) REFERENCES candidates(run_id, candidate_id)
);

CREATE INDEX IF NOT EXISTS idx_param_changes_param
    ON param_changes(param, run_id);

CREATE TABLE IF NOT EXISTS stages (
    run_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    stage_index INTEGER NOT NULL,
    stage TEXT,
    label TEXT,
    knobs TEXT,
    tcl TEXT,
    n_transcript_turns INTEGER,
    n_specialist_intents INTEGER,
    master_concern TEXT,
    master_intent TEXT,
    PRIMARY KEY (run_id, candidate_id, stage_index),
    FOREIGN KEY (run_id, candidate_id) REFERENCES candidates(run_id, candidate_id)
);

CREATE TABLE IF NOT EXISTS tool_calls (
    run_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    stage TEXT,
    label TEXT,
    turn INTEGER,
    kind TEXT NOT NULL,
    concern TEXT,
    chosen INTEGER,
    command TEXT,
    stdout TEXT,
    error TEXT,
    rejected INTEGER,
    rewind_to TEXT,
    FOREIGN KEY (run_id, candidate_id) REFERENCES candidates(run_id, candidate_id)
);

CREATE INDEX IF NOT EXISTS idx_tool_calls_command
    ON tool_calls(kind, run_id);

CREATE TABLE IF NOT EXISTS exploration_points (
    run_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    fmax_mhz REAL,
    power_total_w REAL,
    area_um2 REAL,
    effective_period_ns REAL,
    achievable_period_ns REAL,
    closure_likelihood_pct REAL,
    is_recommended INTEGER,
    excluded INTEGER,
    routed INTEGER,
    closed INTEGER,
    failed INTEGER,
    tapeout_failed INTEGER,
    state TEXT,
    PRIMARY KEY (run_id, candidate_id),
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS metrics (
    run_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    stage TEXT NOT NULL,
    metric TEXT NOT NULL,
    value_num REAL,
    value_text TEXT,
    PRIMARY KEY (run_id, candidate_id, stage, metric),
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE INDEX IF NOT EXISTS idx_metrics_name
    ON metrics(metric, stage);

CREATE TABLE IF NOT EXISTS run_status (
    run_id TEXT PRIMARY KEY,
    design_name TEXT,
    design_goal TEXT,
    overall_status TEXT,
    mode TEXT,
    operating_mode TEXT,
    current_stage TEXT,
    started_at TEXT,
    elapsed_active_seconds REAL,
    last_updated TEXT,
    tapeout_progress_pct REAL,
    n_candidate_metrics INTEGER,
    n_exploration_points INTEGER,
    exploration_complete INTEGER,
    selected_point_id TEXT,
    target_cuboid_json TEXT,
    remaining_milestones_json TEXT,
    stop_notice TEXT,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS eval_runs (
    run_id TEXT PRIMARY KEY,
    generated_at TEXT,
    present INTEGER,
    n_candidates INTEGER,
    totals_json TEXT,
    run_stats_json TEXT,
    trust_gate_json TEXT,
    assessment_verdict TEXT,
    assessment_score REAL,
    trajectory_objective TEXT,
    n_routed_clean INTEGER,
    first_clean TEXT,
    best_die REAL,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS eval_checks (
    run_id TEXT NOT NULL,
    name TEXT NOT NULL,
    grp TEXT,
    step TEXT,
    score REAL,
    n_pass INTEGER,
    n_fail INTEGER,
    n_na INTEGER,
    disabled INTEGER,
    question TEXT,
    PRIMARY KEY (run_id, name),
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS eval_candidates (
    run_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    status TEXT,
    die_area_um2 REAL,
    final_util_pct REAL,
    util_kind TEXT,
    n_findings INTEGER,
    knobs_touched TEXT,
    PRIMARY KEY (run_id, candidate_id),
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE VIEW IF NOT EXISTS v_candidate_wide AS
SELECT
    c.run_id,
    c.candidate_id,
    r.design,
    r.config_mode,
    r.agent_mode,
    r.tcl_live,
    r.seeding,
    r.model,
    c.iteration,
    c.routed AS cand_routed,
    c.outcome_state,
    c.area_um2 AS cand_area_um2,
    c.elapsed_seconds,
    e.state AS explore_state,
    e.closed,
    e.failed,
    e.tapeout_failed,
    e.routed AS explore_routed,
    e.area_um2 AS explore_area_um2,
    e.fmax_mhz,
    e.achievable_period_ns,
    e.effective_period_ns,
    e.power_total_w
FROM candidates c
JOIN runs r ON r.run_id = c.run_id
LEFT JOIN exploration_points e
    ON e.run_id = c.run_id AND e.candidate_id = c.candidate_id;
