#!/bin/sh
set -eu
export LC_ALL=C

task_source_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
task_build_dir=$(mktemp -d /tmp/top-ada-lifetime.XXXXXX)
trap 'rm -rf -- "$task_build_dir"' EXIT
trap 'exit 1' HUP INT TERM
cd "$task_build_dir"

compile_probe() (
    task_compile_probe=$1
    shift
    # GNAT_FLAGS is intentionally split into additional compiler/tool arguments.
    "${GNATMAKE:-gnatmake}" -q -gnat2022 -gnata -gnatwa -gnatwe \
        -I"$task_source_dir" "$task_source_dir/$task_compile_probe.adb" \
        "$@" ${GNAT_FLAGS:-}
)

for task_probe in carrier_probes companion_lifetime escape_dynamic; do
    compile_probe "$task_probe" -o "$task_build_dir/$task_probe"
    "$task_build_dir/$task_probe"
done

expect_compile_refusal() {
    task_probe=$1
    for task_mode in legal illegal; do
        mkdir "$task_build_dir/$task_probe-$task_mode"
    done
    task_legal_log="$task_build_dir/$task_probe-legal.log"
    task_illegal_log="$task_build_dir/$task_probe-illegal.log"
    # Each mode compiles the same source in its own fresh object directory.
    # Preprocessing changes only the forbidden scope/type relationship.
    if ! (cd "$task_build_dir/$task_probe-legal" &&
        compile_probe "$task_probe" -c -gnateDIllegal=False) \
        >"$task_legal_log" 2>&1; then
        echo "ERROR: $task_probe legal control did not compile" >&2
        cat "$task_legal_log" >&2
        exit 1
    fi
    if (cd "$task_build_dir/$task_probe-illegal" &&
        compile_probe "$task_probe" -c -gnateDIllegal=True) \
        >"$task_illegal_log" 2>&1; then
        echo "ERROR: $task_probe forbidden variant unexpectedly compiled" >&2
        cat "$task_illegal_log" >&2
        exit 1
    fi
    echo "$task_probe: legal control compiled; forbidden variant rejected"
}

expect_compile_refusal escape_static
expect_compile_refusal limited_copy
