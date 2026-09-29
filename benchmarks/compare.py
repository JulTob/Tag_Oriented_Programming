"""TOP against plain OOP: the same behaviour, written twice, timed.

Run:  PYTHONPATH=. python3 benchmarks/compare.py

Every scenario is one piece of domain behaviour written the idiomatic
Python way (classes, attributes, methods, a registry) and the idiomatic
TOP way (a host, Tags, Records, Actions, Fields). The scenarios live in
benchmarks/scenarios.py, which the budgets in tests/test_performance.py
import too, so a row here and a budget there time the same code. Before
anything is timed, both ways run once and must give the same observable
result, so the table compares like with like. Each side is then timed as
the fastest of seven runs (time.perf_counter), the sides taking turns so
that both meet the same machine. The loop that drives an operation is the
same on both sides and is counted; the garbage collector stays on, as in
a program.

Section h is the suspected misuse: a passing state (Asleep, Poisoned,
Stunned) kept as a Tag, applied and Ripped every turn, against the same
state kept as a Record, which is what the Guide says to do.

Section i is memory: the bytes that stay alive per character, traced in a
pass of its own (tracemalloc slows every allocation, so it never runs
while anything is timed). Time saved by spending memory, or the reverse,
shows up as a row that moved in one table and not the other.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import Callable
import gc
import platform
import tracemalloc

from benchmarks.scenarios import Archmage
from benchmarks.scenarios import CHECK
from benchmarks.scenarios import Call_Attack
from benchmarks.scenarios import Caster
from benchmarks.scenarios import Creature
from benchmarks.scenarios import Flag_Stunned
from benchmarks.scenarios import Flip_Asleep
from benchmarks.scenarios import Flip_Poison
from benchmarks.scenarios import Flip_Stunned
from benchmarks.scenarios import Mortal
from benchmarks.scenarios import New_Party
from benchmarks.scenarios import Nothing
from benchmarks.scenarios import Observe
from benchmarks.scenarios import Oop_Archmage
from benchmarks.scenarios import Oop_Ari
from benchmarks.scenarios import Oop_Bruk
from benchmarks.scenarios import Oop_Build
from benchmarks.scenarios import Oop_Caster
from benchmarks.scenarios import Oop_Champion_Bruk
from benchmarks.scenarios import Oop_Enrol
from benchmarks.scenarios import Oop_Guild
from benchmarks.scenarios import Oop_Has_Wizard_Role
from benchmarks.scenarios import Oop_Herd
from benchmarks.scenarios import Oop_Is_Flying
from benchmarks.scenarios import Oop_Is_Sound
from benchmarks.scenarios import Oop_Is_Undead
from benchmarks.scenarios import Oop_Is_Wizard
from benchmarks.scenarios import Oop_Leave
from benchmarks.scenarios import Oop_Leave_Registry
from benchmarks.scenarios import Oop_Person
from benchmarks.scenarios import Oop_Recruit_List
from benchmarks.scenarios import Oop_Recruit_Registry
from benchmarks.scenarios import Oop_Sentinel_Registry
from benchmarks.scenarios import Oop_Vigil
from benchmarks.scenarios import Oop_Walk_List
from benchmarks.scenarios import Oop_Walk_Registry
from benchmarks.scenarios import Oop_Walk_Warded
from benchmarks.scenarios import Oop_Ward
from benchmarks.scenarios import POPULATION
from benchmarks.scenarios import Person
from benchmarks.scenarios import REPEAT
from benchmarks.scenarios import Race
from benchmarks.scenarios import Read_Level
from benchmarks.scenarios import Read_Spell_Slots
from benchmarks.scenarios import Side
from benchmarks.scenarios import Tag_Asleep
from benchmarks.scenarios import Tag_Poisoned
from benchmarks.scenarios import Top_Ari
from benchmarks.scenarios import Top_Bruk
from benchmarks.scenarios import Top_Build
from benchmarks.scenarios import Top_Champion_Bruk
from benchmarks.scenarios import Top_Enrol
from benchmarks.scenarios import Top_Guild
from benchmarks.scenarios import Top_Herd
from benchmarks.scenarios import Top_Is_Flying
from benchmarks.scenarios import Top_Is_Sound
from benchmarks.scenarios import Top_Is_Undead
from benchmarks.scenarios import Top_Is_Wizard
from benchmarks.scenarios import Top_Leave
from benchmarks.scenarios import Top_Recruits
from benchmarks.scenarios import Top_Sentinels
from benchmarks.scenarios import Top_Vigil
from benchmarks.scenarios import Top_Walk_Recruits
from benchmarks.scenarios import Top_Walk_Sentinels
from benchmarks.scenarios import Top_Ward
from benchmarks.scenarios import Write_Spell_Slots


TURNS = 100


# ------------------------------------------------------------------
# The harness
# ------------------------------------------------------------------


@dataclass(frozen=True)
class Scenario:
    label: str
    number: int
    oop: Side
    top: Side
    weight: int = 1   # operations per step


@dataclass(frozen=True)
class Passing_State:
    label: str
    oop: Side
    record: Side
    tag: Side


def Require_Same(
        label: str,
        sides: dict[str, Side],
        number: int,
        ) -> None:
    """The comparison is fair only if every side does the same thing."""

    results = {
            way: Observe(side, number)
            for way, side in sides.items()
            }
    first = next(iter(results.values()))

    if any(result != first for result in results.values()):
        raise AssertionError(
                f"{label}: the versions disagree: {results!r}"
                )


def Bytes_Alive(
        build: Callable[[], Any],
        number: int,
        ) -> float:
    """Traced bytes still alive per character once ``build()`` returns
    what it made, measured in a pass of its own. A first build outside the
    trace pays the one-time costs (runtime types, declaration caches), so
    the figure is what each further character costs."""

    warm = build()
    del warm
    gc.collect()
    tracemalloc.start()
    before, _peak = tracemalloc.get_traced_memory()
    made = build()
    gc.collect()
    after, _peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    del made

    return (after - before) / number


def Built(
        side: Side,
        number: int,
        ) -> Callable[[], Any]:
    """Build ``number`` characters the way ``side`` does, keeping them."""

    def Build() -> Any:
        fixture = side.prepare()
        side.run(
                fixture,
                number,
                )

        return fixture

    return Build


def Size(
        count: float,
        ) -> str:
    return f"{count:8,.0f} B "


def Duration(
        seconds: float,
        ) -> str:
    if seconds < 1e-6:
        return f"{seconds * 1e9:7.1f} ns"

    if seconds < 1e-3:
        return f"{seconds * 1e6:7.2f} us"

    if seconds < 1:
        return f"{seconds * 1e3:7.2f} ms"

    return f"{seconds:7.2f} s "


def Row(
        label: str,
        oop: float,
        top: float,
        ) -> str:
    return f"{label:<58} {Duration(oop)} {Duration(top)} {top / oop:8.1f}x"


SCENARIOS = [
        Scenario(
                "a. build: 1-layer class vs host + Form of 1 Tag",
                2_000,
                Side(New_Party, Oop_Build(Oop_Person, 1)),
                Side(New_Party, Top_Build(Person, 1)),
                ),
        Scenario(
                "a. build: 3-layer class vs host + Form of 3 Tags",
                2_000,
                Side(New_Party, Oop_Build(Oop_Caster, 3)),
                Side(New_Party, Top_Build(Caster, 3)),
                ),
        Scenario(
                "a. build: 6-layer class vs host + Form of 6 Tags",
                2_000,
                Side(New_Party, Oop_Build(Oop_Archmage, 6)),
                Side(New_Party, Top_Build(Archmage, 6)),
                ),
        Scenario(
                "b. read: attribute vs Record",
                300_000,
                Side(Oop_Ari, Read_Spell_Slots),
                Side(Top_Ari, Read_Spell_Slots),
                ),
        Scenario(
                "b. read: attribute vs host attribute of an Agent",
                300_000,
                Side(Oop_Ari, Read_Level),
                Side(Top_Ari, Read_Level),
                ),
        Scenario(
                "b. write: attribute vs Record",
                300_000,
                Side(Oop_Ari, Write_Spell_Slots),
                Side(Top_Ari, Write_Spell_Slots),
                ),
        Scenario(
                "c. call: method vs Action",
                300_000,
                Side(Oop_Bruk, Call_Attack),
                Side(Top_Bruk, Call_Attack),
                ),
        Scenario(
                "c. 3-layer chain: super() vs @Underlay",
                100_000,
                Side(Oop_Champion_Bruk, Call_Attack),
                Side(Top_Champion_Bruk, Call_Attack),
                ),
        Scenario(
                "d. is it a Wizard: isinstance vs agent in Wizard",
                300_000,
                Side(Oop_Ari, Oop_Is_Wizard),
                Side(Top_Ari, Top_Is_Wizard),
                ),
        Scenario(
                "d. is it a Wizard: role set vs agent in Wizard",
                300_000,
                Side(Oop_Ari, Oop_Has_Wizard_Role),
                Side(Top_Ari, Top_Is_Wizard),
                ),
        Scenario(
                "d. keyword hit: set lookup vs \"Undead\" in agent",
                300_000,
                Side(Oop_Ari, Oop_Is_Undead),
                Side(Top_Ari, Top_Is_Undead),
                ),
        Scenario(
                "d. keyword miss: set lookup vs \"Flying\" in agent",
                300_000,
                Side(Oop_Ari, Oop_Is_Flying),
                Side(Top_Ari, Top_Is_Flying),
                ),
        Scenario(
                "e. walk 1,000: list registry vs for a in Tag",
                30,
                Side(Oop_Recruit_List, Oop_Walk_List),
                Side(Top_Recruits, Top_Walk_Recruits),
                ),
        Scenario(
                "e. walk 1,000: WeakSet registry vs for a in Tag",
                30,
                Side(Oop_Recruit_Registry, Oop_Walk_Registry),
                Side(Top_Recruits, Top_Walk_Recruits),
                ),
        Scenario(
                "e. walk 1,000 sound: WeakSet + check vs Tag with @Post",
                30,
                Side(Oop_Sentinel_Registry, Oop_Walk_Warded),
                Side(Top_Sentinels, Top_Walk_Sentinels),
                ),
        Scenario(
                "f. gate passes: check in __init__ vs @Pre",
                2_000,
                Side(Nothing, Oop_Enrol(3)),
                Side(Nothing, Top_Enrol(3)),
                ),
        Scenario(
                "f. gate refuses: ValueError vs Precondition (rollback)",
                2_000,
                Side(Nothing, Oop_Enrol(0)),
                Side(Nothing, Top_Enrol(0)),
                ),
        Scenario(
                "f. invariant, 1 check: property vs bool(agent), 1 @Post",
                100_000,
                Side(Oop_Ward, Oop_Is_Sound),
                Side(Top_Ward, Top_Is_Sound),
                ),
        Scenario(
                "f. invariant, 3 checks: property vs bool(agent), 3 @Post",
                100_000,
                Side(Oop_Vigil, Oop_Is_Sound),
                Side(Top_Vigil, Top_Is_Sound),
                ),
        Scenario(
                "g. leave a role: attribute reset vs del Tag[agent]",
                POPULATION,
                Side(Oop_Guild, Oop_Leave),
                Side(Top_Guild, Top_Leave),
                ),
        Scenario(
                "g. leave: reset + WeakSet discard vs del Tag[agent]",
                POPULATION,
                Side(Oop_Guild, Oop_Leave_Registry),
                Side(Top_Guild, Top_Leave),
                ),
        ]


MEMORY = [
        (
            "i. a character: 1-layer class vs Form of 1 Tag",
            Side(New_Party, Oop_Build(Oop_Person, 1)),
            Side(New_Party, Top_Build(Person, 1)),
            ),
        (
            "i. a character: 3-layer class vs Form of 3 Tags",
            Side(New_Party, Oop_Build(Oop_Caster, 3)),
            Side(New_Party, Top_Build(Caster, 3)),
            ),
        (
            "i. a character: 6-layer class vs Form of 6 Tags",
            Side(New_Party, Oop_Build(Oop_Archmage, 6)),
            Side(New_Party, Top_Build(Archmage, 6)),
            ),
        ]


PASSING_STATES = [
        Passing_State(
                "Asleep",
                Side(Oop_Herd, Flip_Asleep),
                Side(Top_Herd(Creature), Flip_Asleep),
                Side(Top_Herd(Mortal), Tag_Asleep),
                ),
        Passing_State(
                "Poisoned(damage=3)",
                Side(Oop_Herd, Flip_Poison),
                Side(Top_Herd(Creature), Flip_Poison),
                Side(Top_Herd(Mortal), Tag_Poisoned),
                ),
        Passing_State(
                "Stunned, a @Flag",
                Side(Oop_Herd, Flip_Stunned),
                Side(Top_Herd(Creature), Flip_Stunned),
                Side(Top_Herd(Mortal), Flag_Stunned),
                ),
        ]


def main() -> None:
    print(
            f"TOP vs OOP on {platform.python_implementation()}"
            f" {platform.python_version()}, {platform.system()}"
            f" {platform.machine()}; fastest of {REPEAT} runs, per operation"
            )
    print()
    print(f"{'scenario':<58} {'OOP':>10} {'TOP':>10} {'TOP/OOP':>9}")

    for scenario in SCENARIOS:
        Require_Same(
                scenario.label,
                {
                    "OOP": scenario.oop,
                    "TOP": scenario.top,
                    },
                min(scenario.number, CHECK),
                )
        oop, top = Race(
                [
                    scenario.oop,
                    scenario.top,
                    ],
                scenario.number,
                )
        operations = scenario.number * scenario.weight
        print(
                Row(
                        scenario.label,
                        oop / operations,
                        top / operations,
                        )
                )

    turns = POPULATION * TURNS
    measured: list[tuple[str, list[float]]] = []

    for state in PASSING_STATES:
        sides = {
                "OOP": state.oop,
                "Record": state.record,
                "Tag": state.tag,
                }
        Require_Same(
                state.label,
                sides,
                CHECK,
                )
        seconds = Race(
                list(sides.values()),
                TURNS,
                )
        measured.append(
                (
                    state.label,
                    seconds,
                    )
                )
        print(
                Row(
                        f"h. {state.label}: attribute vs Record (right)",
                        seconds[0] / turns,
                        seconds[1] / turns,
                        )
                )
        print(
                Row(
                        f"h. {state.label}: attribute vs Tag (misuse)",
                        seconds[0] / turns,
                        seconds[2] / turns,
                        )
                )

    print()
    print(
            f"h. a passing state every turn: {POPULATION:,} Agents x {TURNS}"
            f" turns = {turns:,} agent-turns"
            )
    print(f"   {'state':<20} {'kept as':<32} {'per loop':>10} {'per turn':>10} {'vs OOP':>8}")

    for label, seconds in measured:
        for way, elapsed in zip(
                (
                    "OOP attribute, flipped",
                    "TOP Record, flipped (the Guide)",
                    "TOP Tag, applied and Ripped",
                    ),
                seconds,
                ):
            print(
                    f"   {label:<20} {way:<32} {Duration(elapsed)}"
                    f" {Duration(elapsed / turns)} {elapsed / seconds[0]:7.1f}x"
                    )

            label = ""

    print()
    print(
            f"i. memory still alive per character, {POPULATION:,} characters,"
            " traced apart from the timing"
            )
    print(f"{'scenario':<58} {'OOP':>10} {'TOP':>10} {'TOP/OOP':>9}")

    for label, oop, top in MEMORY:
        oop_bytes = Bytes_Alive(
                Built(oop, POPULATION),
                POPULATION,
                )
        top_bytes = Bytes_Alive(
                Built(top, POPULATION),
                POPULATION,
                )
        print(f"{label:<58} {Size(oop_bytes)} {Size(top_bytes)} {top_bytes / oop_bytes:8.1f}x")

    print()
    print(
            f"i. memory per creature after {TURNS} turns of a passing state,"
            f" {POPULATION:,} creatures"
            )
    print(f"   {'state':<20} {'kept as':<32} {'bytes':>10} {'vs OOP':>8}")

    for state in PASSING_STATES:
        label = state.label
        oop_bytes = 0.0

        for way, side in zip(
                (
                    "OOP attribute, flipped",
                    "TOP Record, flipped (the Guide)",
                    "TOP Tag, applied and Ripped",
                    ),
                (
                    state.oop,
                    state.record,
                    state.tag,
                    ),
                ):
            alive = Bytes_Alive(
                    Built(side, TURNS),
                    POPULATION,
                    )
            oop_bytes = oop_bytes or alive
            print(f"   {label:<20} {way:<32} {Size(alive)} {alive / oop_bytes:7.1f}x")
            label = ""


if __name__ == "__main__":
    main()
