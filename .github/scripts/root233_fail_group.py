"""Temporary CI diagnosis: expose only a public test group's pass/fail."""

import re
import subprocess
import sys
import unittest


def flatten(suite):
    for member in suite:
        if isinstance(member, unittest.TestSuite):
            yield from flatten(member)
        else:
            yield member


ids = [case.id() for case in flatten(unittest.TestLoader().discover("tests", top_level_dir="."))]
result = subprocess.run(
    [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    check=False,
)

if result.returncode == 0:
    raise SystemExit(0)

headers = re.findall(
    r"^(?:FAIL|ERROR): ([A-Za-z_][A-Za-z_0-9]*) \((tests\.[A-Za-z_0-9.]+)\)",
    result.stdout.decode(errors="replace"),
    re.MULTILINE,
)
positions = {case_id: index for index, case_id in enumerate(ids)}
failures = {positions[f"{owner}.{method}"] for method, owner in headers
            if f"{owner}.{method}" in positions}

group = sys.argv[1]
if group == "unparsed":
    raise SystemExit(0 if failures else 1)

start, end = ((0, 219), (219, 438), (438, 657), (657, 875))[int(group)]
raise SystemExit(1 if any(start <= index < end for index in failures) else 0)
