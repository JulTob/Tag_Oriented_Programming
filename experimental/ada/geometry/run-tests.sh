#!/bin/sh
set -eu

task_source_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
task_build_dir=$(mktemp -d /tmp/top-ada-geometry.XXXXXX)
trap 'rm -rf -- "$task_build_dir"' EXIT
trap 'exit 1' HUP INT TERM
mkdir "$task_build_dir/disabled" "$task_build_dir/enabled"

# GNAT_FLAGS is intentionally split into additional compiler/tool arguments.
# Build the actual fixture without assertion enabling in an independent build
# directory. It must fail at its sentinel, before reporting oracle evidence.
cd "$task_build_dir/disabled"
"${GNATMAKE:-gnatmake}" -q -gnat2022 -I"$task_source_dir" \
    "$task_source_dir/geometry_tests.adb" -o "$task_build_dir/disabled/geometry_tests" \
    ${GNAT_FLAGS:-}
if "$task_build_dir/disabled/geometry_tests" > "$task_build_dir/disabled/output" 2>&1; then
    cat "$task_build_dir/disabled/output" >&2
    echo "Geometry assertion control unexpectedly accepted disabled assertions" >&2
    exit 1
fi
# Match our own sentinel payload, not compiler diagnostics or GNAT's exception
# formatting. An unrelated runtime failure does not satisfy this control.
if ! grep -F -q 'Geometry tests require enabled assertions' "$task_build_dir/disabled/output"; then
    cat "$task_build_dir/disabled/output" >&2
    echo "Geometry assertion control failed outside its sentinel" >&2
    exit 1
fi

# Ada 2022 and assertions are requested for the real evidence run.
cd "$task_build_dir/enabled"
"${GNATMAKE:-gnatmake}" -q -gnat2022 -gnata -I"$task_source_dir" \
    "$task_source_dir/geometry_tests.adb" -o "$task_build_dir/enabled/geometry_tests" \
    ${GNAT_FLAGS:-}
"$task_build_dir/enabled/geometry_tests"
