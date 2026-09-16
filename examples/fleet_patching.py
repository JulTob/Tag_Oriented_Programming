"""A drone fleet run through Pins (STEP-SPEC-9): four design patterns you
can adopt when the thing you need to describe is a Tag itself.

    1. Hot-fix across a fleet: patch what a Tag shares, roll it back.
    2. Catalog: facts and keywords about Tags, read by the Tags' own gates.
    3. Registry: a Pin that validates what it collects.
    4. Policy fan-out: one published member reaches every Agent, present
       and future, and only while they are members.

Run:  PYTHONPATH=. python3 examples/fleet_patching.py
"""

from __future__ import annotations

from TopKit import Action
from TopKit import Flag
from TopKit import Keyword
from TopKit import Operation
from TopKit import Pin
from TopKit import Pre
from TopKit import Precondition
from TopKit import Public
from TopKit import Record
from TopKit import Report
from TopKit import Rip
from TopKit import Tag
from TopKit import TagRogueAccessError
from TopKit import Underlay


class Drone:
    """The host: a serial number and nothing else."""

    def __init__(
            drone,
            serial: str,
            ) -> None:
        drone.serial = serial


# --- The fleet's Tags -----------------------------------------------


class Flyer(Tag):
    """What every drone in the air shares: one control law."""

    @Report
    def firmware(tag) -> str:
        return "v1"

    @Operation
    def Control(tag, thrust: int) -> str:
        return f"{tag.__name__} {tag.firmware}: thrust {thrust}"

    def Fly(agent, thrust: int) -> str:
        return Flyer.Control(thrust)            # through the Tag, at call time


class Courier(Flyer):
    """A Shape: couriers fly the same way and carry a parcel."""

    @Record
    def parcel(agent) -> str | None:
        return None

    @Pre
    def Not_Retired(agent) -> bool:
        return "Retired" not in Courier         # a Tag reads its own keywords


# --- Pattern 1 · Hot-fix across a fleet ------------------------------


@Pin
class Firmware_2(Tag):
    """A patch is a Pin. Its Action replaces the Tag's Operation with the
    old one as Underlay; its Record replaces the Report with the old value
    in the stored seat. Every drone that flies through the Tag is
    actualized at once. The @Rip teardown is the rollback."""

    @Record
    def firmware(tag, stored: str) -> str:
        return stored.replace("v1", "v2")

    @Action
    @Underlay
    def Control(tag, underlay, thrust: int) -> str:
        return underlay(min(thrust, 80))        # v2 caps the thrust

    @Rip
    def Rollback(tag, original) -> None:
        tag.firmware = original.firmware
        tag.Control = original.Control


def pattern_hot_fix(fleet: list[Drone]) -> None:
    print("1. hot-fix")
    before = [drone.Fly(100) for drone in fleet]
    assert before == ["Flyer v1: thrust 100"] * len(fleet)

    Firmware_2(Flyer)                           # one act
    after = [drone.Fly(100) for drone in fleet]
    assert after == ["Flyer v2: thrust 80"] * len(fleet)
    assert Courier.firmware == "v2"             # Shapes inherit the patched Report
    print("   patched:", after[0])

    del Firmware_2[Flyer]                       # one act back
    assert fleet[0].Fly(100) == "Flyer v1: thrust 100"
    assert isinstance(Flyer, Firmware_2)        # the history stays
    print("   rolled back:", fleet[0].Fly(100))


# --- Pattern 2 · Catalog: facts and keywords about Tags --------------


@Pin
class Certified(Tag):
    """A fact about a Tag: who signed it off. Lands as a Report."""

    @Record
    def certified_by(tag) -> str:
        return "aviation board"


@Flag
@Pin
class Retired(Tag):
    """A keyword on a Tag. Membership, not a value: it has a Field to walk
    and a history, and Flyer's own gate reads it."""


def pattern_catalog() -> None:
    print("2. catalog")
    Certified(Flyer)
    assert Flyer.certified_by == "aviation board"
    assert Courier.certified_by == "aviation board"     # inherited by the Shape
    assert Courier not in Certified                     # membership does not inherit

    Retired(Courier)
    assert "Retired" in Courier                         # a string asks for a keyword
    assert Keyword(Courier, Retired)
    assert list(Retired) == [Courier]                   # walk the retired Tags

    try:
        Courier(Drone("late"))                          # Courier reads its own keyword
    except Precondition.Not_Retired:
        print("   Courier is retired: no new members")
    else:
        raise AssertionError("a retired Tag accepted a member")

    del Retired[Courier]
    Courier(Drone("ok"))                                # open again
    print("   certified by:", Flyer.certified_by)


# --- Pattern 3 · Registry: a Pin that validates what it collects ------


@Pin
class Plugin(Tag):
    """A registry is a Field of Tags. Its gate is the contract every entry
    must meet; a Tag that does not is refused, and the registry never
    holds a half-valid entry."""

    @Pre
    def Has_A_Menu_Entry(tag) -> bool:
        return hasattr(tag, "Menu_Entry")

    @Action
    def Register(tag) -> str:
        return f"[{tag.__name__}] {tag.Menu_Entry()}"


class Mapper(Flyer):
    @Operation
    def Menu_Entry(tag) -> str:
        return "survey a field"


class Sprayer(Flyer):
    pass                                                # forgot its menu entry


def pattern_registry() -> None:
    print("3. registry")
    Plugin(Mapper)

    try:
        Plugin(Sprayer)
    except Precondition.Has_A_Menu_Entry:
        print("   Sprayer refused: no Menu_Entry")

    menu = [tag.Register() for tag in Plugin]
    assert menu == ["[Mapper] survey a field"]
    print("   menu:", menu)


# --- Pattern 4 · Policy fan-out --------------------------------------


@Pin
class Audited(Tag):
    """A policy published onto a Tag's Field: every present drone gets it
    at pinning, every future drone gets it through the Tag, and only
    members can use it. A drone that leaves the Tag loses the door."""

    @Public
    @Action
    def Audit(tag, agent) -> str:
        return f"{agent.serial} audited under {tag.__name__} policy"


def pattern_policy(fleet: list[Drone]) -> None:
    print("4. policy fan-out")
    Audited(Flyer)
    assert fleet[0].Audit() == "d-0 audited under Flyer policy"      # present drone

    newcomer = Drone("d-new")
    Flyer(newcomer)
    assert newcomer.Audit() == "d-new audited under Flyer policy"    # future drone

    grounded = fleet[1]
    del Flyer[grounded]                                 # left the Tag
    try:
        grounded.Audit()
    except TagRogueAccessError:
        print("   grounded drone: audit refused, members only")
    else:
        raise AssertionError("a Rogue Agent used a published member")

    print("   audited:", newcomer.Audit())


def main() -> None:
    fleet = [Drone(f"d-{index}") for index in range(3)]
    for drone in fleet:
        Flyer(drone)

    pattern_hot_fix(fleet)
    pattern_catalog()
    pattern_registry()
    pattern_policy(fleet)
    print(f"\n{Flyer:pins}")


if __name__ == "__main__":
    main()
