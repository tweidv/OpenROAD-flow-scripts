read_db $::env(STAGE_DB)
set height [[[ord::get_db_block] getBBox] getDY]
set height [ord::dbu_to_microns $height]
set resolution [expr $height / 1200]
save_image -resolution $resolution $::env(STAGE_PNG)
puts "Wrote $::env(STAGE_PNG)"
