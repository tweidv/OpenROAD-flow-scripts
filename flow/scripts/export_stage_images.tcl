source $::env(SCRIPTS_DIR)/util.tcl

set stages {
  {"1_synth" "Synthesis"}
  {"2_floorplan" "Floorplan"}
  {"3_place" "Placement"}
  {"4_cts" "Clock tree synthesis"}
  {"5_route" "Routing"}
  {"6_final" "Final"}
}

set out_dir $::env(REPORTS_DIR)
file mkdir $out_dir

foreach stage $stages {
  lassign $stage tag label
  set db_path $::env(RESULTS_DIR)/${tag}.odb
  if {![file exists $db_path]} {
    puts "Skip missing $db_path"
    continue
  }
  puts "Rendering $label from $db_path"
  read_db $db_path
  gui::fit
  set height [[[ord::get_db_block] getBBox] getDY]
  set height [ord::dbu_to_microns $height]
  set resolution [expr $height / 1200]
  set png_path $out_dir/progression_${tag}.png
  save_image -resolution $resolution $png_path
  puts "Wrote $png_path"
}
