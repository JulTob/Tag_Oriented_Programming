#!/bin/sh
set -eu
export LC_ALL=C

task_source_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
task_build_dir=$(mktemp -d /tmp/top-ada-targets.XXXXXX)
trap 'rm -rf -- "$task_build_dir"' EXIT
trap 'exit 1' HUP INT TERM

compile_probe() (
    task_probe=$1
    shift
    # GNAT_FLAGS is intentionally split into additional compiler/tool arguments.
    "${GNATMAKE:-gnatmake}" -q -gnat2022 -gnata -gnatwa -gnatwe \
        -I"$task_source_dir" "$task_source_dir/$task_probe.adb" \
        "$@" ${GNAT_FLAGS:-}
)

mkdir "$task_build_dir/tests"
(cd "$task_build_dir/tests" &&
    compile_probe target_tests -o "$task_build_dir/target_tests")
"$task_build_dir/target_tests"

expect_compile_refusal() {
    task_probe=$1
    task_case=$2
    shift 2
    for task_mode in legal illegal; do
        mkdir "$task_build_dir/$task_case-$task_mode"
    done
    if ! (cd "$task_build_dir/$task_case-legal" &&
        compile_probe "$task_probe" -c -gnateDIllegal=False "$@") \
        >"$task_build_dir/$task_case-legal.log" 2>&1; then
        echo "ERROR: $task_case legal control did not compile" >&2
        cat "$task_build_dir/$task_case-legal.log" >&2
        exit 1
    fi
    if (cd "$task_build_dir/$task_case-illegal" &&
        compile_probe "$task_probe" -c -gnateDIllegal=True "$@") \
        >"$task_build_dir/$task_case-illegal.log" 2>&1; then
        echo "ERROR: $task_case forbidden variant unexpectedly compiled" >&2
        cat "$task_build_dir/$task_case-illegal.log" >&2
        exit 1
    fi
    echo "$task_case: legal control compiled; forbidden variant rejected"
}

expect_compile_refusal limited_target_copy limited_target_assignment
expect_compile_refusal private_target_support private_target_token \
    -gnateDTokenAccess=True
expect_compile_refusal private_target_support private_handle_finalizer \
    -gnateDTokenAccess=False
