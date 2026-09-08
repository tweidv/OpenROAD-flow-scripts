#!/usr/bin/env bash
set -euo pipefail

stages=(
  "1_synth|Synthesis"
  "2_floorplan|Floorplan"
  "3_place|Placement"
  "4_cts|Clock tree synthesis"
  "5_route|Routing"
  "6_final|Final"
)

mkdir -p "$REPORTS_DIR" "$LOG_DIR"

for entry in "${stages[@]}"; do
  IFS='|' read -r tag label <<< "$entry"
  db="$RESULTS_DIR/${tag}.odb"
  png="$REPORTS_DIR/progression_${tag}.png"
  if [[ ! -f "$db" ]]; then
    echo "Skip missing $db"
    continue
  fi
  echo "Rendering $label -> $png"
  export STAGE_DB="$db" STAGE_PNG="$png"
  "$PYTHON_EXE" "$SCRIPTS_DIR/run_command.py" --log "$(realpath "$LOG_DIR/progression_${tag}.log")" --tee -- \
    $OPENROAD_CMD -no_splash "$SCRIPTS_DIR/export_one_stage_image.tcl"
done

echo "Done."
