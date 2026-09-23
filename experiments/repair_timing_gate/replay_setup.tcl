# Replay repair_timing -setup on a pre-repair CTS snapshot.
# Same parasitics / dont_use / padding as cts.tcl after the snapshot.
utl::set_metrics_stage "cts__{}"
source $::env(SCRIPTS_DIR)/load.tcl
erase_non_stage_variables cts

set odb_name 4_1_pre_repair_setup_hold.odb
set sdc_name 4_1_pre_repair_setup_hold.sdc
if { [env_var_exists_and_non_empty REPAIR_REPLAY_ODB] } {
  set odb_name $::env(REPAIR_REPLAY_ODB)
}
if { [env_var_exists_and_non_empty REPAIR_REPLAY_SDC] } {
  set sdc_name $::env(REPAIR_REPLAY_SDC)
}

load_design $odb_name $sdc_name

if { [env_var_exists_and_non_empty DONT_USE_CELLS] } {
  set_dont_use $::env(DONT_USE_CELLS)
}

set_placement_padding -global \
  -left $::env(CELL_PAD_IN_SITES_DETAIL_PLACEMENT) \
  -right $::env(CELL_PAD_IN_SITES_DETAIL_PLACEMENT)

# Placement parasitics for the CTS snapshot; global_routing for a GRT odb.
set parasitics_mode placement
if { [env_var_exists_and_non_empty REPAIR_PARASITICS] } {
  set parasitics_mode $::env(REPAIR_PARASITICS)
}
if { $parasitics_mode eq "global_routing" } {
  set_propagated_clock [all_clocks]
}
log_cmd estimate_parasitics -$parasitics_mode

puts "=== BEFORE repair_timing ==="
report_wns
report_tns
report_design_area

# Setup-only: isolate the search. Hold is a different engine (0 inserts on this
# ibex seed). Extra argv from the helper env knobs (SKIP_LAST_GASP, sequence).
set extra {}
if { [env_var_exists_and_non_empty REPAIR_TIMING_EXTRA_ARGS] } {
  set extra $::env(REPAIR_TIMING_EXTRA_ARGS)
}
repair_timing_helper -setup {*}$extra

puts "=== AFTER repair_timing ==="
report_wns
report_tns
report_design_area
report_power

if { [env_var_exists_and_non_empty REPAIR_REPLAY_OUT_ODB] } {
  log_cmd write_db $::env(REPAIR_REPLAY_OUT_ODB)
}
