"""Performance budgets: TOP against the same behaviour in plain Python.

Opt-in, because timing depends on the machine:

    TOPKIT_PERF=1 PYTHONPATH=. python3 -m unittest tests.test_performance -v

Every budget is a ratio to the plain-OOP equivalent, measured in the same
process a moment before, so a fast or a slow machine moves both sides.
Each side is timed by Race in benchmarks/scenarios.py: the fastest of
REPEAT runs, the sides taking turns. The budgets are generous, at least
twice what the kit cost when they were set (CPython 3.14, Apple M5), so
they catch a real regression, such as a Record that stops being a plain
attribute or a tagging that starts copying the world, and not a busy
machine. A budget that fails is
measured once more before it is reported.

The scenarios and the timing come from `benchmarks/scenarios.py`;
`benchmarks/compare.py` times the same scenarios and prints the whole
comparison.
"""

from __future__ import annotations

import os
import unittest

from benchmarks.scenarios import CHECK
from benchmarks.scenarios import Call_Attack
from benchmarks.scenarios import Creature
from benchmarks.scenarios import Cycle_Asleep
from benchmarks.scenarios import Flip_Asleep
from benchmarks.scenarios import New_Party
from benchmarks.scenarios import Observe
from benchmarks.scenarios import Oop_Ari
from benchmarks.scenarios import Oop_Bruk
from benchmarks.scenarios import Oop_Build
from benchmarks.scenarios import Oop_Champion_Bruk
from benchmarks.scenarios import Oop_Guild
from benchmarks.scenarios import Oop_Herd
from benchmarks.scenarios import Oop_Is_Sound
from benchmarks.scenarios import Oop_Is_Undead
from benchmarks.scenarios import Oop_Is_Wizard
from benchmarks.scenarios import Oop_Leave_Registry
from benchmarks.scenarios import Oop_Person
from benchmarks.scenarios import Oop_Recruit_Registry
from benchmarks.scenarios import Oop_Walk_Registry
from benchmarks.scenarios import Oop_Ward
from benchmarks.scenarios import POPULATION
from benchmarks.scenarios import Person
from benchmarks.scenarios import Plain_Herd
from benchmarks.scenarios import Race
from benchmarks.scenarios import Read_Level
from benchmarks.scenarios import Read_Spell_Slots
from benchmarks.scenarios import Side
from benchmarks.scenarios import Top_Ari
from benchmarks.scenarios import Top_Bruk
from benchmarks.scenarios import Top_Build
from benchmarks.scenarios import Top_Champion_Bruk
from benchmarks.scenarios import Top_Guild
from benchmarks.scenarios import Top_Herd
from benchmarks.scenarios import Top_Is_Sound
from benchmarks.scenarios import Top_Is_Undead
from benchmarks.scenarios import Top_Is_Wizard
from benchmarks.scenarios import Top_Leave
from benchmarks.scenarios import Top_Recruits
from benchmarks.scenarios import Top_Walk_Recruits
from benchmarks.scenarios import Top_Ward
from benchmarks.scenarios import Write_Spell_Slots


@unittest.skipUnless(
        os.environ.get("TOPKIT_PERF") == "1",
        "performance budgets are opt-in: set TOPKIT_PERF=1",
        )
class PerformanceBudgetTests(unittest.TestCase):

    def assertWithinBudget(
            self,
            what: str,
            oop: Side,
            top: Side,
            number: int,
            budget: float,
            same: bool = True,
            ) -> None:
        """TOP may cost at most ``budget`` times the OOP equivalent. When
        the two sides are the same behaviour (``same``), they must first
        give the same observable result, so the ratio is fair."""

        if same:
            self.assertEqual(
                    Observe(oop, CHECK),
                    Observe(top, CHECK),
                    f"{what}: the two versions disagree",
                    )

        attempts: list[tuple[float, float, float]] = []

        for _attempt in range(2):
            oop_seconds, top_seconds = Race(
                    [
                        oop,
                        top,
                        ],
                    number,
                    )
            ratio = top_seconds / oop_seconds
            attempts.append(
                    (
                        ratio,
                        oop_seconds / number,
                        top_seconds / number,
                        )
                    )

            if ratio <= budget:
                return

        ratio, oop_per_step, top_per_step = min(attempts)

        self.fail(
                f"{what}: TOP costs {ratio:.1f}x the OOP equivalent"
                f" ({top_per_step * 1e9:,.0f} ns against"
                f" {oop_per_step * 1e9:,.0f} ns); the budget is {budget}x"
                )

    # Reads, writes, calls: the hot path.

    def test_a_record_read_is_near_an_attribute_read(self) -> None:
        self.assertWithinBudget(
                "Record read vs attribute read",
                Side(Oop_Ari, Read_Spell_Slots),
                Side(Top_Ari, Read_Spell_Slots),
                300_000,
                6,
                )

    def test_a_record_read_costs_what_any_agent_attribute_costs(self) -> None:
        self.assertWithinBudget(
                "Record read vs a host attribute read on the same Agent",
                Side(Top_Ari, Read_Level),
                Side(Top_Ari, Read_Spell_Slots),
                300_000,
                2.5,
                same=False,
                )

    def test_a_record_write_is_an_attribute_write(self) -> None:
        self.assertWithinBudget(
                "Record write vs attribute write",
                Side(Oop_Ari, Write_Spell_Slots),
                Side(Top_Ari, Write_Spell_Slots),
                300_000,
                6,
                )

    def test_an_action_call(self) -> None:
        self.assertWithinBudget(
                "Action call vs method call",
                Side(Oop_Bruk, Call_Attack),
                Side(Top_Bruk, Call_Attack),
                300_000,
                20,
                )

    def test_an_underlay_chain(self) -> None:
        self.assertWithinBudget(
                "3-layer @Underlay chain vs 3-layer super() chain",
                Side(Oop_Champion_Bruk, Call_Attack),
                Side(Top_Champion_Bruk, Call_Attack),
                100_000,
                18,
                )

    # Asking what an Agent is.

    def test_membership(self) -> None:
        self.assertWithinBudget(
                "agent in Tag vs isinstance",
                Side(Oop_Ari, Oop_Is_Wizard),
                Side(Top_Ari, Top_Is_Wizard),
                300_000,
                30,
                )

    def test_a_keyword(self) -> None:
        self.assertWithinBudget(
                "\"Undead\" in agent vs a keyword set",
                Side(Oop_Ari, Oop_Is_Undead),
                Side(Top_Ari, Top_Is_Undead),
                300_000,
                80,
                )

    def test_a_promise_read_as_bool(self) -> None:
        self.assertWithinBudget(
                "bool(agent), 1 @Post, vs an invariant property",
                Side(Oop_Ward, Oop_Is_Sound),
                Side(Top_Ward, Top_Is_Sound),
                100_000,
                100,
                )

    # Populations.

    def test_walking_the_field(self) -> None:
        self.assertWithinBudget(
                "for a in Tag vs a WeakSet registry, 1,000 members",
                Side(Oop_Recruit_Registry, Oop_Walk_Registry),
                Side(Top_Recruits, Top_Walk_Recruits),
                20,
                25,
                )

    def test_leaving_a_role(self) -> None:
        self.assertWithinBudget(
                "del Tag[agent] vs attribute reset and WeakSet discard",
                Side(Oop_Guild, Oop_Leave_Registry),
                Side(Top_Guild, Top_Leave),
                POPULATION,
                15,
                )

    # Tagging, measured in plain constructions of the same character.
    # 2,000 constructions set off a garbage collection (CPython 3.14), which
    # the OOP side pays inside its timing; 1,000 set off none.

    def test_tagging_a_one_tag_form(self) -> None:
        self.assertWithinBudget(
                "host + a Form of 1 Tag vs constructing the OOP class",
                Side(New_Party, Oop_Build(Oop_Person, 1)),
                Side(New_Party, Top_Build(Person, 1)),
                2_000,
                100,
                )

    def test_applying_and_ripping_a_tag(self) -> None:
        self.assertWithinBudget(
                "Asleep(h) then del Asleep[h] vs constructing the OOP class",
                Side(New_Party, Oop_Build(Oop_Person, 1)),
                Side(Plain_Herd, Cycle_Asleep),
                POPULATION,
                150,
                same=False,
                )

    # The Guide's way for a passing state.

    def test_a_passing_state_as_a_record(self) -> None:
        self.assertWithinBudget(
                "a Record flipped vs an attribute flipped, 1,000 per turn",
                Side(Oop_Herd, Flip_Asleep),
                Side(Top_Herd(Creature), Flip_Asleep),
                20,
                6,
                )


if __name__ == "__main__":
    unittest.main()
