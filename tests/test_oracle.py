"""A short run of the oracle under the ordinary suite.

The full run is `PYTHONPATH=. python3 tests/oracle_topkit.py --seeds 50
--steps 1200 --population 18`; this keeps the suite fast and still walks
a few thousand transitions on every run.
"""

from __future__ import annotations

import unittest
import warnings

from tests import oracle_topkit


class OracleTests(unittest.TestCase):

    def test_the_kit_agrees_with_the_model(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            transitions = sum(
                    oracle_topkit.Run_Seed(seed, steps=250, population=7)
                    for seed in range(1701, 1705)
                    )

        self.assertEqual(transitions, 1000)

    def test_fields_never_keep_an_agent_alive(self) -> None:
        oracle_topkit.Weak_Field_Probe(200)


if __name__ == "__main__":
    unittest.main()
