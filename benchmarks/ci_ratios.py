"""Report two noisy Tagging ratios for CI without making them a merge gate.

Run with ``PYTHONPATH=. python -m benchmarks.ci_ratios``. Both scenarios
use the same Sides and operation counts as the opt-in performance budgets.
The ratios are observations, not stable pass/fail limits on shared runners.
"""

from __future__ import annotations

import platform

from benchmarks.scenarios import Cycle_Asleep
from benchmarks.scenarios import New_Party
from benchmarks.scenarios import Oop_Build
from benchmarks.scenarios import Oop_Person
from benchmarks.scenarios import POPULATION
from benchmarks.scenarios import Person
from benchmarks.scenarios import Plain_Herd
from benchmarks.scenarios import Race
from benchmarks.scenarios import Side
from benchmarks.scenarios import Top_Build


def main() -> None:
    print(f"Python {platform.python_version()} on {platform.platform()}", flush=True)

    for label, oop, top, count in (
            (
                "first Tagging",
                Side(New_Party, Oop_Build(Oop_Person, 1)),
                Side(New_Party, Top_Build(Person, 1)),
                2_000,
                ),
            (
                "apply and Rip",
                Side(New_Party, Oop_Build(Oop_Person, 1)),
                Side(Plain_Herd, Cycle_Asleep),
                POPULATION,
                ),
            ):
        oop_seconds, top_seconds = Race([oop, top], count)
        print(
                f"{label}: {top_seconds / oop_seconds:.1f}x OOP"
                f" (TOP {top_seconds / count * 1e6:.1f} us/step;"
                f" OOP {oop_seconds / count * 1e6:.1f} us/step)",
                flush=True,
                )


if __name__ == "__main__":
    main()
