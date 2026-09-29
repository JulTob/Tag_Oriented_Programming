"""A short run of the differential fuzzer under the ordinary suite.

Two short programs, one of the heavy mix, each run twice on the working
tree's kit in fresh interpreters: the transcripts must agree, so the
programs are deterministic and the harness normalizes what varies from
run to run. Comparing two versions of the kit is
`PYTHONPATH=. python3 tests/differential_fuzz.py --base origin/main`.
"""

from __future__ import annotations

import pathlib
import tempfile
import unittest

from tests import differential_fuzz


class DifferentialFuzzTests(unittest.TestCase):

    def test_the_working_tree_agrees_with_itself(self) -> None:
        with tempfile.TemporaryDirectory(prefix="topkit-fuzz-") as scratch:
            root = pathlib.Path(scratch).resolve()
            kit = differential_fuzz.Kit(
                    differential_fuzz.WORKING_TREE,
                    root / "kit",
                    )

            for seed, heavy in ((0, False), (1, True)):
                outcome = differential_fuzz.Run_Seed(
                        seed,
                        60,
                        heavy,
                        kit,
                        kit,
                        root,
                        timeout=30,
                        )

                self.assertEqual(outcome.base, outcome.new)
                self.assertIn("=== exit ===", outcome.new)       # the program ran to its end
                self.assertEqual(outcome.new[-1], "exit status 0")


if __name__ == "__main__":
    unittest.main()
