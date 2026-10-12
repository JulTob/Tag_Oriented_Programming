#!/bin/sh
set -eu

task_source_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
task_build_dir=$(mktemp -d /tmp/top-ada-lifetime.XXXXXX)
trap 'rm -rf -- "$task_build_dir"' EXIT
trap 'exit 1' HUP INT TERM
cd "$task_build_dir"

# GNAT_FLAGS is intentionally split into additional compiler/tool arguments.
"${GNATMAKE:-gnatmake}" -q -gnat2022 -gnata -gnatwa -gnatwe \
    -I"$task_source_dir" "$task_source_dir/carrier_probes.adb" \
    -o "$task_build_dir/carrier_probes" ${GNAT_FLAGS:-}
"$task_build_dir/carrier_probes"
