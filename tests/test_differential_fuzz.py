"""A short run of the differential fuzzer under the ordinary suite.

Two short programs, one of the heavy mix, each run on two copies of the
working tree's kit in fresh interpreters: the transcripts must agree, so
the programs are deterministic and the harness normalizes what varies
between runs and between kit locations. Both seeds print an address and
a warning from inside the kit, so a normalizer that stopped working would
fail here. Comparing two versions of the kit is
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
            base = differential_fuzz.Kit(
                    differential_fuzz.WORKING_TREE,
                    root / "base",
                    )
            new = differential_fuzz.Kit(
                    differential_fuzz.WORKING_TREE,
                    root / "new",
                    )

            for seed, heavy in ((26, False), (10, True)):   # both show an address and a kit path
                outcome = differential_fuzz.Run_Seed(
                        seed,
                        60,
                        heavy,
                        base,
                        new,
                        root,
                        timeout=30,
                        )

                self.assertEqual(outcome.base, outcome.new)
                self.assertTrue(                                   # what the normalizer must hide
                        any("0x?" in line for line in outcome.new)
                        and any("@ TopKit/" in line for line in outcome.new),
                        (seed, heavy),
                        )
                self.assertIn("=== exit ===", outcome.new)       # the program ran to its end
                self.assertEqual(outcome.new[-1], "exit status 0")


if __name__ == "__main__":
    unittest.main()
