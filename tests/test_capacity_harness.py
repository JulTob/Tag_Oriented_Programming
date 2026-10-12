"""Capacity observations require the harness's validation assertions."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CapacityHarnessTests(unittest.TestCase):
    def run_probe(self, flags=(), optimize="0"):
        environment = os.environ.copy()
        environment["PYTHONOPTIMIZE"] = optimize
        environment["PYTHONPATH"] = str(ROOT)
        return subprocess.run(
                [sys.executable, *flags, "-m", "benchmarks.capacity", "form", "4"],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                timeout=30,
                )

    def test_normal_interpreter_runs_the_verified_probe(self):
        result = self.run_probe()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("FORM PASS depth=4", result.stdout)
        self.assertEqual(result.stderr, "")

    def test_optimized_interpreters_refuse_without_reporting_pass(self):
        for flags, optimize in (
                (("-O",), "0"),
                (("-OO",), "0"),
                ((), "1"),
                ((), "2"),
                ):
            with self.subTest(flags=flags, optimize=optimize):
                result = self.run_probe(flags, optimize)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("PASS", result.stdout)
                self.assertIn("assertions", result.stderr)
                self.assertIn("-O/-OO", result.stderr)
                self.assertIn("PYTHONOPTIMIZE", result.stderr)


if __name__ == "__main__":
    unittest.main()
