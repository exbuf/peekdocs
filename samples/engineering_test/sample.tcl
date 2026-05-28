# sample.tcl -- Tcl script for FPGA synthesis tool automation
# PEEKDOCS_TEST_MARKER

proc create_project {name device} {
    puts "Creating project: $name for device $device"
    set project_dir "./build/$name"
    file mkdir $project_dir

    set settings [dict create \
        device $device \
        top_module "top" \
        constraint_file "constraints.xdc" \
        optimization "area" \
    ]
    return $settings
}

proc add_source_files {project_dir pattern} {
    set files [glob -nocomplain $pattern]
    if {[llength $files] == 0} {
        puts "WARNING: No files matched pattern $pattern"
        return 0
    }
    foreach f $files {
        puts "  Adding: $f"
        file copy -force $f $project_dir
    }
    return [llength $files]
}

proc run_synthesis {settings} {
    set device [dict get $settings device]
    set top [dict get $settings top_module]
    puts "Synthesizing $top for $device..."
    puts "Optimization: [dict get $settings optimization]"
    # In practice this would invoke the vendor tool chain
    return 0
}

# Main flow
set cfg [create_project "sensor_hub" "XC7A35T"]
add_source_files "./build/sensor_hub" "rtl/*.v"
run_synthesis $cfg
