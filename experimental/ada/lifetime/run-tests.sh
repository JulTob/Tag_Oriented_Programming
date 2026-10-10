#!/bin/sh
set -eu
export LC_ALL=C

task_source_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
task_build_dir=$(mktemp -d /tmp/top-ada-lifetime.XXXXXX)
trap 'rm -rf -- "$task_build_dir"' EXIT
trap 'exit 1' HUP INT TERM
cd "$task_build_dir"

compile_probe() {
    # GNAT_FLAGS is intentionally split into additional compiler/tool arguments.
    "${GNATMAKE:-gnatmake}" -q -gnat2022 -gnata -gnatwa -gnatwe \
        -I"$task_source_dir" "$task_source_dir/$1.adb" \
        -o "$task_build_dir/$1" ${GNAT_FLAGS:-}
}

for task_probe in carrier_probes companion_lifetime escape_dynamic; do
    compile_probe "$task_probe"
    "$task_build_dir/$task_probe"
done

expect_compile_refusal() {
    task_log="$task_build_dir/$1.log"
    if compile_probe "$1" >"$task_log" 2>&1; then
        echo "ERROR: $1 unexpectedly compiled" >&2
        exit 1
    fi
    if ! grep -F "$1.adb:" "$task_log" | grep -F "error: $2" >/dev/null; then
        echo "ERROR: $1 failed without its expected compiler diagnostic" >&2
        cat "$task_log" >&2
        exit 1
    fi
    echo "$1: expected compiler rejection ($2)"
}

expect_compile_refusal escape_static \
    "prefix of attribute has deeper level than allocator type"
expect_compile_refusal limited_copy \
    "left hand of assignment must not be limited type"
