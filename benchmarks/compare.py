"""TOP against plain OOP: the same behaviour, written twice, timed.

Run:  PYTHONPATH=. python3 benchmarks/compare.py

Every scenario is one piece of domain behaviour written the idiomatic
Python way (classes, attributes, methods, a registry) and the idiomatic
TOP way (a host, Tags, Records, Actions, Fields). Before anything is
timed, both run once and must give the same observable result, so the
table compares like with like. Each side is then timed as the fastest of
seven runs (time.perf_counter), the sides taking turns so that both meet
the same machine. The loop that drives an operation is the same on both
sides and is counted; the garbage collector stays on, as in a program.

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
import time
import tracemalloc
import weakref

from TopKit import Flag
from TopKit import Keyword
from TopKit import Post
from TopKit import Pre
from TopKit import Precondition
from TopKit import Record
from TopKit import Tag
from TopKit import Underlay


REPEAT = 7
POPULATION = 1_000
TURNS = 100
CHECK = 10   # operations in the equality run that precedes the timing


# ------------------------------------------------------------------
# The host, and one character sheet written both ways
# ------------------------------------------------------------------


class Character:
    """The TOP host: ordinary Python that knows nothing of its roles."""

    def __init__(
            character,
            name: str,
            level: int = 3,
            ) -> None:
        character.name = name
        character.level = level


class Oop_Person(Character):

    def __init__(
            person,
            name: str,
            level: int = 3,
            ) -> None:
        super().__init__(
                name,
                level,
                )
        person.speed = 30
        person.hit_points = 8 * person.level

    def Walk(
            person,
            ) -> str:
        return f"{person.name} walks {person.speed} feet"


class Oop_Adventurer(Oop_Person):

    def __init__(
            adventurer,
            name: str,
            level: int = 3,
            ) -> None:
        super().__init__(
                name,
                level,
                )
        adventurer.gold = 10
        adventurer.hit_points += 2 * adventurer.level

    def Loot(
            adventurer,
            ) -> str:
        return f"{adventurer.name} has {adventurer.gold} gold"


class Oop_Caster(Oop_Adventurer):

    def __init__(
            caster,
            name: str,
            level: int = 3,
            ) -> None:
        super().__init__(
                name,
                level,
                )
        caster.spell_slots = 2
        caster.hit_points += caster.level

    def Cast(
            caster,
            ) -> str:
        return f"{caster.name} casts with {caster.spell_slots} slots"


class Oop_Mage(Oop_Caster):

    def __init__(
            mage,
            name: str,
            level: int = 3,
            ) -> None:
        super().__init__(
                name,
                level,
                )
        mage.spellbook = ["Light"]
        mage.hit_points += mage.level

    def Study(
            mage,
            ) -> str:
        return f"{mage.name} studies {len(mage.spellbook)} spells"


class Oop_Wizard(Oop_Mage):

    def __init__(
            wizard,
            name: str,
            level: int = 3,
            ) -> None:
        super().__init__(
                name,
                level,
                )
        wizard.familiar = "owl"
        wizard.hit_points += wizard.level

    def Summon(
            wizard,
            ) -> str:
        return f"{wizard.name} calls the {wizard.familiar}"


class Oop_Archmage(Oop_Wizard):

    def __init__(
            archmage,
            name: str,
            level: int = 3,
            ) -> None:
        super().__init__(
                name,
                level,
                )
        archmage.tower = "ivory"
        archmage.hit_points += 2 * archmage.level

    def Ascend(
            archmage,
            ) -> str:
        return f"{archmage.name} rules the {archmage.tower} tower"


class Person(Tag):

    @Record
    def speed(agent) -> int:
        return 30

    @Record
    def hit_points(agent, stored) -> int:
        return (stored or 0) + 8 * agent.level

    def Walk(agent) -> str:
        return f"{agent.name} walks {agent.speed} feet"


class Adventurer(Person):

    @Record
    def gold(agent) -> int:
        return 10

    @Record
    def hit_points(agent, stored) -> int:
        return stored + 2 * agent.level

    def Loot(agent) -> str:
        return f"{agent.name} has {agent.gold} gold"


class Caster(Adventurer):

    @Record
    def spell_slots(agent) -> int:
        return 2

    @Record
    def hit_points(agent, stored) -> int:
        return stored + agent.level

    def Cast(agent) -> str:
        return f"{agent.name} casts with {agent.spell_slots} slots"


class Mage(Caster):

    @Record
    def spellbook(agent) -> list[str]:
        return ["Light"]

    @Record
    def hit_points(agent, stored) -> int:
        return stored + agent.level

    def Study(agent) -> str:
        return f"{agent.name} studies {len(agent.spellbook)} spells"


class Wizard(Mage):

    @Record
    def familiar(agent) -> str:
        return "owl"

    @Record
    def hit_points(agent, stored) -> int:
        return stored + agent.level

    def Summon(agent) -> str:
        return f"{agent.name} calls the {agent.familiar}"


class Archmage(Wizard):

    @Record
    def tower(agent) -> str:
        return "ivory"

    @Record
    def hit_points(agent, stored) -> int:
        return stored + 2 * agent.level

    def Ascend(agent) -> str:
        return f"{agent.name} rules the {agent.tower} tower"


@Flag
class Undead(Tag):
    pass


LAYERS = (
        ("speed", "Walk"),
        ("gold", "Loot"),
        ("spell_slots", "Cast"),
        ("spellbook", "Study"),
        ("familiar", "Summon"),
        ("tower", "Ascend"),
        )


def Sheet(
        character: object,
        depth: int,
        ) -> tuple[Any, ...]:
    """What a reader of the sheet sees: the name, the hit points, and every
    Record and Action result the first ``depth`` layers gave."""

    seen: list[Any] = [
            character.name,
            character.hit_points,
            ]

    for record, action in LAYERS[:depth]:
        seen.append(getattr(character, record))
        seen.append(getattr(character, action)())

    return tuple(seen)


def Oop_Ari() -> Oop_Wizard:
    """A Wizard (five layers) whose roles and keywords live in sets."""

    ari = Oop_Wizard("Ari")
    ari.roles = {"Person", "Adventurer", "Caster", "Mage", "Wizard"}
    ari.keywords = {"Undead"}

    return ari


def Top_Ari() -> Character:
    """A Wizard (a Form of five Tags) who is also Undead: six Tags, the
    Flag last."""

    ari = Character("Ari")
    Wizard(ari)
    Undead(ari)

    return ari


# ------------------------------------------------------------------
# a. Building a character
# ------------------------------------------------------------------


def Oop_Build(
        sheet_class: type,
        depth: int,
        ) -> Callable[[Any, int], Any]:
    def Build(
            party: list[object],
            number: int,
            ) -> Any:
        for _ in range(number):
            character = sheet_class("Ari")
            party.append(character)

        return Sheet(
                character,
                depth,
                )

    return Build


def Top_Build(
        tag: type,
        depth: int,
        ) -> Callable[[Any, int], Any]:
    def Build(
            party: list[object],
            number: int,
            ) -> Any:
        for _ in range(number):
            character = Character("Ari")
            tag(character)
            party.append(character)

        return Sheet(
                character,
                depth,
                )

    return Build


def New_Party() -> list[object]:
    return []


# ------------------------------------------------------------------
# b. Reading and writing state
# ------------------------------------------------------------------


def Read_Spell_Slots(
        character: Any,
        number: int,
        ) -> Any:
    for _ in range(number):
        value = character.spell_slots

    return value


def Read_Level(
        character: Any,
        number: int,
        ) -> Any:
    for _ in range(number):
        value = character.level

    return value


def Write_Spell_Slots(
        character: Any,
        number: int,
        ) -> Any:
    for _ in range(number):
        character.spell_slots = 3

    return character.spell_slots


# ------------------------------------------------------------------
# c. Calling behaviour
# ------------------------------------------------------------------


class Oop_Brawler(Character):

    def Attack(
            brawler,
            ) -> str:
        return "Attack!"


class Oop_Duelist(Oop_Brawler):

    def Attack(
            duelist,
            ) -> str:
        return "With a flourish, " + super().Attack()


class Oop_Champion(Oop_Duelist):

    def Attack(
            champion,
            ) -> str:
        return super().Attack() + " For the crowd!"


class Brawler(Tag):

    def Attack(agent) -> str:
        return "Attack!"


class Duelist(Brawler):

    @Underlay
    def Attack(agent, underlay) -> str:
        return "With a flourish, " + underlay()


class Champion(Duelist):

    @Underlay
    def Attack(agent, underlay) -> str:
        return underlay() + " For the crowd!"


def Oop_Bruk() -> Oop_Brawler:
    return Oop_Brawler("Bruk")


def Oop_Champion_Bruk() -> Oop_Champion:
    return Oop_Champion("Bruk")


def Top_Bruk() -> Character:
    return Brawler(Character("Bruk"))


def Top_Champion_Bruk() -> Character:
    return Champion(Character("Bruk"))


def Call_Attack(
        character: Any,
        number: int,
        ) -> Any:
    for _ in range(number):
        value = character.Attack()

    return value


# ------------------------------------------------------------------
# d. Asking what something is
# ------------------------------------------------------------------


def Oop_Is_Wizard(
        character: Any,
        number: int,
        ) -> Any:
    for _ in range(number):
        value = isinstance(character, Oop_Wizard)

    return value


def Oop_Has_Wizard_Role(
        character: Any,
        number: int,
        ) -> Any:
    for _ in range(number):
        value = "Wizard" in character.roles

    return value


def Top_Is_Wizard(
        agent: Any,
        number: int,
        ) -> Any:
    for _ in range(number):
        value = agent in Wizard

    return value


def Oop_Is_Undead(
        character: Any,
        number: int,
        ) -> Any:
    for _ in range(number):
        value = "Undead" in character.keywords

    return value


def Top_Is_Undead(
        agent: Any,
        number: int,
        ) -> Any:
    for _ in range(number):
        value = "Undead" in agent

    return value


def Oop_Is_Flying(
        character: Any,
        number: int,
        ) -> Any:
    for _ in range(number):
        value = "Flying" in character.keywords

    return value


def Top_Is_Flying(
        agent: Any,
        number: int,
        ) -> Any:
    for _ in range(number):
        value = "Flying" in agent

    return value


# ------------------------------------------------------------------
# e. Walking everyone in a role
# ------------------------------------------------------------------


class Oop_Sentinel(Character):

    def __init__(
            sentinel,
            name: str,
            level: int = 3,
            ) -> None:
        super().__init__(
                name,
                level,
                )
        sentinel.ward = 1

    @property
    def is_warded(
            sentinel,
            ) -> bool:
        return sentinel.ward > 0


class Recruit(Tag):
    pass


class Sentinel(Tag):

    @Record
    def ward(agent) -> int:
        return 1

    @Post
    def Is_Warded(agent) -> bool:
        return agent.ward > 0


def Level_Of(
        index: int,
        ) -> int:
    return 1 + index % 5


def Oop_Recruit_List() -> list[Character]:
    return [
            Character(f"Recruit {index}", Level_Of(index))
            for index in range(POPULATION)
            ]


def Oop_Recruit_Registry() -> tuple[weakref.WeakSet, list[Character]]:
    recruits = Oop_Recruit_List()

    return (
            weakref.WeakSet(recruits),
            recruits,
            )


def Top_Recruits() -> list[Character]:
    recruits = [
            Character(f"Recruit {index}", Level_Of(index))
            for index in range(POPULATION)
            ]

    for recruit in recruits:
        Recruit(recruit)

    return recruits


def Oop_Sentinel_Registry() -> tuple[weakref.WeakSet, list[Oop_Sentinel]]:
    sentinels = [
            Oop_Sentinel(f"Sentinel {index}", Level_Of(index))
            for index in range(POPULATION)
            ]

    for sentinel in sentinels[::10]:
        sentinel.ward = 0

    return (
            weakref.WeakSet(sentinels),
            sentinels,
            )


def Top_Sentinels() -> list[Character]:
    sentinels = [
            Character(f"Sentinel {index}", Level_Of(index))
            for index in range(POPULATION)
            ]

    for sentinel in sentinels:
        Sentinel(sentinel)

    for sentinel in sentinels[::10]:
        sentinel.ward = 0   # a broken promise: out of the sound population

    return sentinels


def Oop_Walk_List(
        recruits: list[Character],
        number: int,
        ) -> Any:
    for _ in range(number):
        total = 0

        for recruit in recruits:
            total += recruit.level

    return total


def Oop_Walk_Registry(
        fixture: tuple[weakref.WeakSet, list[Character]],
        number: int,
        ) -> Any:
    registry, _keep = fixture

    for _ in range(number):
        total = 0

        for recruit in registry:
            total += recruit.level

    return total


def Top_Walk_Recruits(
        _keep: list[Character],
        number: int,
        ) -> Any:
    for _ in range(number):
        total = 0

        for recruit in Recruit:
            total += recruit.level

    return total


def Oop_Walk_Warded(
        fixture: tuple[weakref.WeakSet, list[Oop_Sentinel]],
        number: int,
        ) -> Any:
    registry, _keep = fixture

    for _ in range(number):
        total = 0

        for sentinel in registry:
            if sentinel.is_warded:
                total += sentinel.level

    return total


def Top_Walk_Sentinels(
        _keep: list[Character],
        number: int,
        ) -> Any:
    for _ in range(number):
        total = 0

        for sentinel in Sentinel:
            total += sentinel.level

    return total


# ------------------------------------------------------------------
# f. Validation
# ------------------------------------------------------------------


class Oop_Scholar(Character):

    def __init__(
            scholar,
            name: str,
            level: int = 3,
            ) -> None:
        if level < 1:
            raise ValueError("cannot study below level 1")

        super().__init__(
                name,
                level,
                )
        scholar.spell_slots = 2


class Scholar(Tag):

    @Pre
    def Can_Study(agent) -> bool:
        return agent.level >= 1

    @Record
    def spell_slots(agent) -> int:
        return 2


def Oop_Enrol(
        level: int,
        ) -> Callable[[Any, int], Any]:
    def Enrol(
            _nothing: None,
            number: int,
            ) -> Any:
        refused = 0

        for _ in range(number):
            try:
                scholar = Oop_Scholar("Sage", level)
            except ValueError:
                refused += 1

        return refused if refused else scholar.spell_slots

    return Enrol


def Top_Enrol(
        level: int,
        ) -> Callable[[Any, int], Any]:
    def Enrol(
            _nothing: None,
            number: int,
            ) -> Any:
        refused = 0

        for _ in range(number):
            scholar = Character("Sage", level)

            try:
                Scholar(scholar)
            except Precondition.Can_Study:
                refused += 1

        return refused if refused else scholar.spell_slots

    return Enrol


def Nothing() -> None:
    return None


class Oop_Warded(Character):

    def __init__(
            warded,
            name: str,
            level: int = 3,
            ) -> None:
        super().__init__(
                name,
                level,
                )
        warded.spell_slots = 2

    @property
    def is_sound(
            warded,
            ) -> bool:
        return warded.spell_slots >= 0


class Oop_Vigilant(Oop_Warded):

    @property
    def is_sound(
            vigilant,
            ) -> bool:
        return (
                vigilant.spell_slots >= 0
                and vigilant.level >= 1
                and vigilant.name != ""
                )


class Warded(Tag):

    @Record
    def spell_slots(agent) -> int:
        return 2

    @Post
    def Has_Slots(agent) -> bool:
        return agent.spell_slots >= 0


class Vigilant(Warded):

    @Post
    def Has_Level(agent) -> bool:
        return agent.level >= 1

    @Post
    def Has_Name(agent) -> bool:
        return agent.name != ""


def Oop_Ward() -> Oop_Warded:
    return Oop_Warded("Ward")


def Oop_Vigil() -> Oop_Vigilant:
    return Oop_Vigilant("Ward")


def Top_Ward() -> Character:
    return Warded(Character("Ward"))


def Top_Vigil() -> Character:
    return Vigilant(Character("Ward"))


def Oop_Is_Sound(
        character: Any,
        number: int,
        ) -> Any:
    for _ in range(number):
        value = character.is_sound

    return value


def Top_Is_Sound(
        agent: Any,
        number: int,
        ) -> Any:
    for _ in range(number):
        value = bool(agent)

    return value


# ------------------------------------------------------------------
# g. Removing a role
# ------------------------------------------------------------------


class Guild_Member(Tag):

    @Record
    def dues(agent) -> int:
        return 10


def Oop_Guild() -> tuple[weakref.WeakSet, list[Character]]:
    members = [
            Character(f"Member {index}")
            for index in range(POPULATION)
            ]

    for member in members:
        member.is_member = True
        member.dues = 10

    return (
            weakref.WeakSet(members),
            members,
            )


def Top_Guild() -> list[Character]:
    members = [
            Character(f"Member {index}")
            for index in range(POPULATION)
            ]

    for member in members:
        Guild_Member(member)

    return members


def Oop_Leave(
        fixture: tuple[weakref.WeakSet, list[Character]],
        number: int,
        ) -> Any:
    _guild, members = fixture

    for member in members[:number]:
        member.is_member = False

    return member.is_member


def Oop_Leave_Registry(
        fixture: tuple[weakref.WeakSet, list[Character]],
        number: int,
        ) -> Any:
    guild, members = fixture

    for member in members[:number]:
        member.is_member = False
        guild.discard(member)

    return member.is_member


def Top_Leave(
        members: list[Character],
        number: int,
        ) -> Any:
    for member in members[:number]:
        del Guild_Member[member]

    return member in Guild_Member


# ------------------------------------------------------------------
# h. A passing state, every turn
# ------------------------------------------------------------------


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
        creature.hit_points = 20
        creature.asleep = False
        creature.poison = 0
        creature.stunned = False


class Creature(Tag):
    """The Guide's way: how a creature is right now is a Record."""

    @Record
    def hit_points(agent) -> int:
        return 20

    @Record
    def asleep(agent) -> bool:
        return False

    @Record
    def poison(agent) -> int:
        return 0

    @Record
    def stunned(agent) -> bool:
        return False


class Mortal(Tag):
    """What the misuse keeps as a Record: only the hit points."""

    @Record
    def hit_points(agent) -> int:
        return 20


class Asleep(Tag):
    pass


class Poisoned(Tag):

    @Record
    def poison_damage(agent, *, damage) -> int:
        return damage


@Flag
class Stunned(Tag):
    pass


def Oop_Herd() -> list[Oop_Creature]:
    return [
            Oop_Creature(f"Creature {index}")
            for index in range(POPULATION)
            ]


def Top_Herd(
        tag: type,
        ) -> Callable[[], list[Character]]:
    def Herd() -> list[Character]:
        herd = [
                Character(f"Creature {index}")
                for index in range(POPULATION)
                ]

        for creature in herd:
            tag(creature)

        return herd

    return Herd


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


def Tag_Asleep(
        herd: list[Any],
        turns: int,
        ) -> Any:
    sleeping = 0

    for _ in range(turns):
        for creature in herd:
            if creature in Asleep:
                del Asleep[creature]
            else:
                Asleep(creature)
                sleeping += 1

    return sleeping


def Flip_Poison(
        herd: list[Any],
        turns: int,
        ) -> Any:
    for _ in range(turns):
        for creature in herd:
            if creature.poison:
                creature.poison = 0
            else:
                creature.poison = 3
                creature.hit_points -= creature.poison

    return sum(
            creature.hit_points
            for creature in herd
            )


def Tag_Poisoned(
        herd: list[Any],
        turns: int,
        ) -> Any:
    for _ in range(turns):
        for creature in herd:
            if creature in Poisoned:
                del Poisoned[creature]
            else:
                Poisoned(
                        creature,
                        damage=3,
                        )
                creature.hit_points -= creature.poison_damage

    return sum(
            creature.hit_points
            for creature in herd
            )


def Flip_Stunned(
        herd: list[Any],
        turns: int,
        ) -> Any:
    stunned = 0

    for _ in range(turns):
        for creature in herd:
            if creature.stunned:
                creature.stunned = False
            else:
                creature.stunned = True
                stunned += 1

    return stunned


def Flag_Stunned(
        herd: list[Any],
        turns: int,
        ) -> Any:
    stunned = 0

    for _ in range(turns):
        for creature in herd:
            if Keyword(creature, "Stunned"):   # `in` needs a Flag landed first
                del Stunned[creature]
            else:
                Stunned(creature)
                stunned += 1

    return stunned


# ------------------------------------------------------------------
# The harness
# ------------------------------------------------------------------


@dataclass(frozen=True)
class Side:
    """One way of writing the behaviour. ``prepare()`` builds what a run
    needs and is not timed; ``run(fixture, number)`` performs ``number``
    steps, is timed, and returns the observable result."""

    prepare: Callable[[], Any]
    run: Callable[[Any, int], Any]


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


def Observe(
        side: Side,
        number: int,
        ) -> Any:
    fixture = side.prepare()

    return side.run(
            fixture,
            number,
            )


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


def Race(
        sides: list[Side],
        number: int,
        ) -> list[float]:
    """Seconds for one run of ``number`` steps, per side: the fastest of
    REPEAT runs, the sides taking turns."""

    fastest = [float("inf")] * len(sides)

    for _ in range(REPEAT):
        for index, side in enumerate(sides):
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

    return fastest


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
