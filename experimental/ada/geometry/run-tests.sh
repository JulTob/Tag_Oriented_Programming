#!/bin/sh
set -eu

task_source_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
task_build_dir=$(mktemp -d /tmp/top-ada-geometry.XXXXXX)
trap 'rm -rf -- "$task_build_dir"' EXIT
trap 'exit 1' HUP INT TERM
cd "$task_build_dir"

# GNAT_FLAGS is intentionally split into additional compiler/tool arguments.
# Assertions and Ada 2022 are always requested by the runner.
"${GNATMAKE:-gnatmake}" -q -gnat2022 -gnata -I"$task_source_dir" \
    "$task_source_dir/geometry_tests.adb" -o "$task_build_dir/geometry_tests" \
    ${GNAT_FLAGS:-}
"$task_build_dir/geometry_tests"
