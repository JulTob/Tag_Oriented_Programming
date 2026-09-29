"""Performance budgets: TOP against the same behaviour in plain Python.

Opt-in, because timing depends on the machine:

    TOPKIT_PERF=1 PYTHONPATH=. python3 -m unittest tests.test_performance -v

Every budget is a ratio to the plain-OOP equivalent, measured in the same
process a moment before, so a fast or a slow machine moves both sides.
Each side is the fastest of seven runs, the sides taking turns. The
budgets are generous, at least twice what the kit cost when they were
set (CPython 3.14, Apple M5), so they catch a real regression, such as a
Record that stops being a plain attribute or a tagging that starts
copying the world, and not a busy machine. A budget that fails is
measured once more before it is reported.

`benchmarks/compare.py` prints the whole comparison.
"""

from __future__ import annotations

from typing import Any
from typing import Callable
from typing import NamedTuple
import gc
import os
import time
import unittest
import weakref

from TopKit import Flag
from TopKit import Post
from TopKit import Record
from TopKit import Tag
from TopKit import Underlay


REPEAT = 7
POPULATION = 1_000


# ==================================================================
# The same behaviour, both ways
# ==================================================================


class Character:
    def __init__(
            character,
            name: str,
            level: int = 3,
            ) -> None:
        character.name = name
        character.level = level


class Oop_Adept(Character):

    def __init__(
            adept,
            name: str,
            level: int = 3,
            ) -> None:
        super().__init__(
                name,
                level,
                )
        adept.spell_slots = 2
        adept.hit_points = 6 * adept.level

    def Attack(
            adept,
            ) -> str:
        return "Attack!"


class Oop_Duelist(Oop_Adept):

    def Attack(
            duelist,
            ) -> str:
        return "With a flourish, " + super().Attack()


class Oop_Champion(Oop_Duelist):

    def Attack(
            champion,
            ) -> str:
        return super().Attack() + " For the crowd!"


class Oop_Warded(Oop_Adept):

    @property
    def is_sound(
            warded,
            ) -> bool:
        return warded.spell_slots >= 0


class Adept(Tag):

    @Record
    def spell_slots(agent) -> int:
        return 2

    @Record
    def hit_points(agent, stored) -> int:
        return (stored or 0) + 6 * agent.level

    def Attack(agent) -> str:
        return "Attack!"


class Duelist(Adept):

    @Underlay
    def Attack(agent, underlay) -> str:
        return "With a flourish, " + underlay()


class Champion(Duelist):

    @Underlay
    def Attack(agent, underlay) -> str:
        return underlay() + " For the crowd!"


class Warded(Adept):

    @Post
    def Has_Slots(agent) -> bool:
        return agent.spell_slots >= 0


@Flag
class Spectral(Tag):
    pass


class Asleep(Tag):
    pass


class Drilled(Tag):
    pass


# ==================================================================
# Timing
# ==================================================================


class Side(NamedTuple):
    """``prepare()`` builds what a run needs, untimed; ``run(fixture,
    number)`` performs ``number`` operations, timed."""

    prepare: Callable[[], Any]
    run: Callable[[Any, int], Any]


def Race(
        oop: Side,
        top: Side,
        number: int,
        ) -> tuple[float, float]:
    """Seconds per operation for each side, the fastest of REPEAT runs."""

    fastest = [
            float("inf"),
            float("inf"),
            ]

    for _ in range(REPEAT):
        for index, side in enumerate((oop, top)):
            fixture = side.prepare()
            gc.collect()
            start = time.perf_counter()
            side.run(
                    fixture,
                    number,
                    )
            elapsed = time.perf_counter() - start
            del fixture
            fastest[index] = min(
                    fastest[index],
                    elapsed,
                    )

    return (
            fastest[0] / number,
            fastest[1] / number,
            )


def Oop_Bruk() -> Oop_Champion:
    return Oop_Champion("Bruk")


def Top_Bruk() -> Character:
    return Champion(Character("Bruk"))


def Oop_Ward() -> Oop_Warded:
    return Oop_Warded("Ward")


def Top_Ward() -> Character:
    return Warded(Character("Ward"))


def Oop_Ari() -> Oop_Adept:
    ari = Oop_Adept("Ari")
    ari.keywords = {"Spectral"}

    return ari


def Top_Ari() -> Character:
    ari = Character("Ari")
    Adept(ari)
    Spectral(ari)

    return ari


def Read_Record(
        character: Any,
        number: int,
        ) -> Any:
    for _ in range(number):
        value = character.spell_slots

    return value


def Read_Host_Attribute(
        character: Any,
        number: int,
        ) -> Any:
    for _ in range(number):
        value = character.level

    return value


def Write_Record(
        character: Any,
        number: int,
        ) -> Any:
    for _ in range(number):
        character.spell_slots = 3

    return character.spell_slots


def Call_Attack(
        character: Any,
        number: int,
        ) -> Any:
    for _ in range(number):
        value = character.Attack()

    return value


def Is_Adept(
        character: Any,
        number: int,
        ) -> Any:
    for _ in range(number):
        value = isinstance(character, Oop_Adept)

    return value


def In_Adept(
        agent: Any,
        number: int,
        ) -> Any:
    for _ in range(number):
        value = agent in Adept

    return value


def Has_Keyword_Set(
        character: Any,
        number: int,
        ) -> Any:
    for _ in range(number):
        value = "Spectral" in character.keywords

    return value


def Has_Keyword_Flag(
        agent: Any,
        number: int,
        ) -> Any:
    for _ in range(number):
        value = "Spectral" in agent

    return value


def Is_Sound_Property(
        character: Any,
        number: int,
        ) -> Any:
    for _ in range(number):
        value = character.is_sound

    return value


def Is_Sound_Bool(
        agent: Any,
        number: int,
        ) -> Any:
    for _ in range(number):
        value = bool(agent)

    return value


def New_Party() -> list[object]:
    return []


def Construct_Adept(
        party: list[object],
        number: int,
        ) -> Any:
    for _ in range(number):
        party.append(Oop_Adept("Ari"))

    return party[-1].hit_points


def Tag_Adept(
        party: list[object],
        number: int,
        ) -> Any:
    for _ in range(number):
        character = Character("Ari")
        Adept(character)
        party.append(character)

    return party[-1].hit_points


def Oop_Roster() -> tuple[weakref.WeakSet, list[Character]]:
    roster = [
            Character(f"Recruit {index}")
            for index in range(POPULATION)
            ]

    for recruit in roster:
        recruit.drilled = True

    return (
            weakref.WeakSet(roster),
            roster,
            )


def Top_Roster() -> list[Character]:
    roster = [
            Character(f"Recruit {index}")
            for index in range(POPULATION)
            ]

    for recruit in roster:
        Drilled(recruit)

    return roster


def Walk_Registry(
        fixture: tuple[weakref.WeakSet, list[Character]],
        number: int,
        ) -> Any:
    registry, _keep = fixture

    for _ in range(number):
        total = 0

        for recruit in registry:
            total += recruit.level

    return total


def Walk_Field(
        _keep: list[Character],
        number: int,
        ) -> Any:
    for _ in range(number):
        total = 0

        for recruit in Drilled:
            total += recruit.level

    return total


def Leave_Registry(
        fixture: tuple[weakref.WeakSet, list[Character]],
        number: int,
        ) -> Any:
    registry, roster = fixture

    for recruit in roster[:number]:
        recruit.drilled = False
        registry.discard(recruit)

    return recruit.drilled


def Leave_Field(
        roster: list[Character],
        number: int,
        ) -> Any:
    for recruit in roster[:number]:
        del Drilled[recruit]

    return recruit in Drilled


class Oop_Creature(Character):

    def __init__(
            creature,
            name: str,
            level: int = 3,
            ) -> None:
        super().__init__(
                name,
                level,
                )
        creature.asleep = False


def Oop_Herd() -> list[Oop_Creature]:
    return [
            Oop_Creature(f"Creature {index}")
            for index in range(POPULATION)
            ]


class Creature(Tag):

    @Record
    def asleep(agent) -> bool:
        return False


def Top_Herd() -> list[Character]:
    herd = [
            Character(f"Creature {index}")
            for index in range(POPULATION)
            ]

    for creature in herd:
        Creature(creature)

    return herd


def Flip_Asleep(
        herd: list[Any],
        turns: int,
        ) -> Any:
    sleeping = 0

    for _ in range(turns):
        for creature in herd:
            if creature.asleep:
                creature.asleep = False
            else:
                creature.asleep = True
                sleeping += 1

    return sleeping


def Cycle_Asleep(
        herd: list[Any],
        number: int,
        ) -> Any:
    for creature in herd[:number]:
        Asleep(creature)
        del Asleep[creature]

    return creature in Asleep


def Plain_Herd() -> list[Character]:
    return [
            Character(f"Creature {index}")
            for index in range(POPULATION)
            ]


# ==================================================================
# Budgets
# ==================================================================


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
                    oop.run(oop.prepare(), 10),
                    top.run(top.prepare(), 10),
                    f"{what}: the two versions disagree",
                    )

        attempts: list[tuple[float, float, float]] = []

        for _attempt in range(2):
            oop_seconds, top_seconds = Race(
                    oop,
                    top,
                    number,
                    )
            ratio = top_seconds / oop_seconds
            attempts.append(
                    (
                        ratio,
                        oop_seconds,
                        top_seconds,
                        )
                    )

            if ratio <= budget:
                return

        ratio, oop_seconds, top_seconds = min(attempts)

        self.fail(
                f"{what}: TOP costs {ratio:.1f}x the OOP equivalent"
                f" ({top_seconds * 1e9:,.0f} ns against"
                f" {oop_seconds * 1e9:,.0f} ns); the budget is {budget}x"
                )

    # Reads, writes, calls: the hot path.

    def test_a_record_read_is_near_an_attribute_read(self) -> None:
        self.assertWithinBudget(
                "Record read vs attribute read",
                Side(Oop_Ari, Read_Record),
                Side(Top_Ari, Read_Record),
                300_000,
                6,
                )

    def test_a_record_read_costs_what_any_agent_attribute_costs(self) -> None:
        self.assertWithinBudget(
                "Record read vs a host attribute read on the same Agent",
                Side(Top_Ari, Read_Host_Attribute),
                Side(Top_Ari, Read_Record),
                300_000,
                2.5,
                same=False,
                )

    def test_a_record_write_is_an_attribute_write(self) -> None:
        self.assertWithinBudget(
                "Record write vs attribute write",
                Side(Oop_Ari, Write_Record),
                Side(Top_Ari, Write_Record),
                300_000,
                6,
                )

    def test_an_action_call(self) -> None:
        self.assertWithinBudget(
                "Action call vs method call",
                Side(Oop_Ari, Call_Attack),
                Side(Top_Ari, Call_Attack),
                300_000,
                20,
                )

    def test_an_underlay_chain(self) -> None:
        self.assertWithinBudget(
                "3-layer @Underlay chain vs 3-layer super() chain",
                Side(Oop_Bruk, Call_Attack),
                Side(Top_Bruk, Call_Attack),
                100_000,
                18,
                )

    # Asking what an Agent is.

    def test_membership(self) -> None:
        self.assertWithinBudget(
                "agent in Tag vs isinstance",
                Side(Oop_Ari, Is_Adept),
                Side(Top_Ari, In_Adept),
                300_000,
                30,
                )

    def test_a_keyword(self) -> None:
        self.assertWithinBudget(
                "\"Spectral\" in agent vs a keyword set",
                Side(Oop_Ari, Has_Keyword_Set),
                Side(Top_Ari, Has_Keyword_Flag),
                300_000,
                80,
                )

    def test_a_promise_read_as_bool(self) -> None:
        self.assertWithinBudget(
                "bool(agent), 1 @Post, vs an invariant property",
                Side(Oop_Ward, Is_Sound_Property),
                Side(Top_Ward, Is_Sound_Bool),
                100_000,
                100,
                )

    # Populations.

    def test_walking_the_field(self) -> None:
        self.assertWithinBudget(
                "for a in Tag vs a WeakSet registry, 1,000 members",
                Side(Oop_Roster, Walk_Registry),
                Side(Top_Roster, Walk_Field),
                20,
                25,
                )

    def test_leaving_a_role(self) -> None:
        self.assertWithinBudget(
                "del Tag[agent] vs attribute reset and WeakSet discard",
                Side(Oop_Roster, Leave_Registry),
                Side(Top_Roster, Leave_Field),
                POPULATION,
                15,
                )

    # Tagging, measured in plain constructions of the same character.

    def test_tagging_a_one_tag_form(self) -> None:
        self.assertWithinBudget(
                "host + a Form of 1 Tag vs constructing the OOP class",
                Side(New_Party, Construct_Adept),
                Side(New_Party, Tag_Adept),
                2_000,
                250,
                )

    def test_applying_and_ripping_a_tag(self) -> None:
        self.assertWithinBudget(
                "Asleep(h) then del Asleep[h] vs constructing the OOP class",
                Side(New_Party, Construct_Adept),
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
                Side(Top_Herd, Flip_Asleep),
                20,
                6,
                )


if __name__ == "__main__":
    unittest.main()
