"""A starship crew run through published members (STEP-SPEC-10): five
design patterns for access control and error control that need no
security code of their own.

    1. Roles are membership: what the role lends ends when you leave it.
    2. A repair table: catch a promise by name, repair it, retry.
    3. Quarantine for free: one broken promise closes every published door.
    4. Stale handles: a queued command from a relieved officer is refused
       when it runs, not when it was queued.
    5. Requirements: necessary to enter and necessary to stay, in one word.
    6. The author ends the condition: a guard inside it that decides
       which membership it follows, or an explicit deletion from the
       role's own @Rip protocol. Rip itself never touches a condition.

Run:  PYTHONPATH=. python3 examples/crew_access.py
"""

from __future__ import annotations

from typing import Callable

from TopKit import Contract
from TopKit import Flag
from TopKit import Operation
from TopKit import Pin
from TopKit import Post
from TopKit import Postcondition
from TopKit import Pre
from TopKit import Precondition
from TopKit import Public
from TopKit import Record
from TopKit import Report
from TopKit import Requirement
from TopKit import Rip
from TopKit import Tag
from TopKit import TagPostconditionError
from TopKit import TagRogueAccessError
from TopKit import Underlay


class Crew:
    """The host: a name, a pulse, a clean bill of health."""

    def __init__(
            crew,
            name: str,
            ) -> None:
        crew.name = name
        crew.alive = True
        crew.infected = False
        crew.oath = None
        crew.safety_on = True
        crew.decorated = False


# --- The crew's Tags ------------------------------------------------


class Crew_Member(Tag):
    @Requirement
    def Alive(agent) -> bool:
        return agent.alive


class Healthy(Tag):
    @Post
    def Not_Infected(agent) -> bool:
        return not agent.infected


class Sworn(Tag):
    @Post
    def Has_Oath(agent) -> bool:
        return agent.oath is not None

    @Rip
    def Release(agent) -> None:
        Contract.Delete(agent, "Has_Oath")              # the oath ends with the role, visibly


class Bridge(Tag):
    """What the Bridge lends its officers: a shared alert level and the
    weapons. What an officer becomes on the Bridge, a station, is theirs."""

    @Public
    @Report
    def alert(bridge) -> str:
        return "green"

    @Public
    @Operation
    def Fire(bridge, agent, target: str) -> str:
        return f"{agent.name} fires at {target}"

    @Record
    def station(agent) -> str:
        return "tactical"

    def Report_In(agent) -> str:
        return f"{agent.name} at {agent.station}"


# --- Pattern 1 · Roles are membership --------------------------------


def pattern_roles(worf: Crew) -> None:
    print("1. roles are membership")
    assert worf.alert == "green"
    assert worf.Fire("asteroid") == "Worf fires at asteroid"

    del Bridge[worf]                                    # relieved of duty
    assert worf.Report_In() == "Worf at tactical"       # his own: kept
    try:
        worf.Fire("asteroid")
    except TagRogueAccessError:
        print("   relieved: the Bridge's weapons refuse him")

    Bridge(worf)                                        # reinstated
    assert worf.Fire("asteroid") == "Worf fires at asteroid"
    print("   reinstated:", worf.Fire("asteroid"))


# --- Pattern 2 · A repair table --------------------------------------


Repair = Callable[[Crew], None]


def with_repairs(
        act: Callable[[], str],
        repairs: dict[type, Repair],
        agent: Crew,
        ) -> str:
    """Run an act; when a named promise refuses, repair what it names and
    try once more. Unknown promises are not swallowed."""

    try:
        return act()
    except TagPostconditionError as broken:
        repair = repairs.get(type(broken))
        if repair is None:
            raise
        repair(agent)
        return act()


REPAIRS: dict[type, Repair] = {
        Postcondition.Has_Oath: lambda crew: setattr(crew, "oath", "to the Federation"),
        Postcondition.Not_Infected: lambda crew: setattr(crew, "infected", False),
        }


def pattern_repair_table(worf: Crew) -> None:
    print("2. repair table")
    try:
        Sworn(worf)                                     # no oath yet: a defective member
    except Postcondition.Has_Oath:
        pass
    assert worf in ~Sworn

    result = with_repairs(lambda: worf.Fire("probe"), REPAIRS, worf)
    assert result == "Worf fires at probe"
    assert worf.oath == "to the Federation"
    assert worf in list(Sworn)                          # sound again
    print("   repaired and fired:", result)


# --- Pattern 3 · Quarantine for free ---------------------------------


def pattern_quarantine(worf: Crew) -> None:
    print("3. quarantine")
    Healthy(worf)
    worf.infected = True                                # a promise breaks, Healthy's

    try:
        worf.Fire("probe")                              # Bridge's door, closed by Healthy's promise
    except Postcondition.Not_Infected:
        print("   infected: every published door is closed, by name")

    for patient in ~Healthy:                            # sickbay works the defective population
        patient.infected = False
    assert not list(~Healthy)
    assert worf.Fire("probe") == "Worf fires at probe"
    print("   cured:", Contract.Status(worf))


# --- Pattern 4 · Stale handles ----------------------------------------


def pattern_stale_handles(worf: Crew) -> None:
    print("4. stale handles")
    queue = [lambda: worf.Fire("decoy")]                # queued while on duty
    fire = worf.Fire                                    # a captured handle, same thing

    del Bridge[worf]
    for command in queue:
        try:
            command()
        except TagRogueAccessError:
            print("   queued command refused at run time")
    try:
        fire("decoy")
    except TagRogueAccessError:
        print("   captured handle refused the same way")
    Bridge(worf)


# --- Pattern 5 · Requirements ----------------------------------------


def pattern_requirements() -> None:
    print("5. requirements")
    ghost = Crew("Ghost")
    ghost.alive = False
    try:
        Crew_Member(ghost)                              # necessary to enter
    except Precondition.Alive:
        print("   not alive: cannot join the crew")

    dax = Crew("Dax")
    Crew_Member(dax)
    dax.alive = False                                   # necessary to stay
    assert dax in ~Crew_Member
    dax.alive = True
    assert dax in list(Crew_Member)
    print("   Dax:", Contract.Status(dax))


# --- Pattern 6 · The author ends the condition -------------------------
#
# Conditions are sticky: Rip never removes one, so a promise that outlives
# its Tag fails loud, never silently. Two ways to end one, both visible:
# a guard inside the condition, one line of flow control that can follow
# any membership at all (another Tag's, a keyword on a Tag, the Tag under
# an Underlay); or an explicit deletion from the role's own @Rip protocol,
# one name at a time. No law has to guess.


class Armed(Tag):
    """A promise that follows ANOTHER Tag's membership. The weapons lock
    matters only while the officer stands on the Bridge; off the Bridge
    the promise holds, because the author said so."""

    @Post
    def Weapons_Locked(agent) -> bool:
        if agent not in Bridge:                         # not on duty: nothing to lock
            return True
        return agent.safety_on


@Flag
@Pin
class Red_Alert(Tag):
    """A keyword on the Bridge itself: the ship's state, not the crew's."""


class Alert_Protocol(Tag):
    """A promise that follows a keyword on a Tag. It bites only while the
    Bridge is at Red Alert."""

    @Post
    def At_Station(agent) -> bool:
        if "Red_Alert" not in Bridge:                   # peacetime: the protocol sleeps
            return True
        return agent.station == "tactical"


class Officer(Tag):
    """A gate that reads another Tag: you enter the officers' mess only as
    crew. Necessary to enter, written where it is read."""

    @Pre
    def Is_Crew(agent) -> bool:
        return agent in Crew_Member


class Veteran(Tag):
    """An Underlay whose guard says whose promise the underneath is. If the
    crew role is gone, the Veteran holds only his own clause, and the
    chain never calls a check of a Tag the Agent has left."""

    @Post
    @Underlay
    def Alive(agent, base) -> bool:
        underneath = base() if agent in Crew_Member else True
        return underneath and agent.decorated


def pattern_author_guard(worf: Crew) -> None:
    print("6. the author ends the condition")

    del Sworn[worf]                                     # Release runs: Has_Oath is deleted
    worf.oath = None
    assert "Has_Oath" not in Contract.Status(worf)      # no promise left to break
    worf.oath = "to the Federation"
    Sworn(worf)
    print("   Has_Oath ended by Sworn's own Rip protocol")

    Armed(worf)
    worf.safety_on = False
    assert worf in ~Armed                               # on the Bridge: the lock matters
    del Bridge[worf]
    assert worf in list(Armed)                          # off the Bridge: it does not
    worf.safety_on = True                               # a tagging re-checks every promise
    Bridge(worf)
    print("   Weapons_Locked follows the Bridge, not Armed")

    Alert_Protocol(worf)
    worf.station = "mess hall"
    assert worf in list(Alert_Protocol)                 # peacetime: nobody minds
    Red_Alert(Bridge)
    assert worf in ~Alert_Protocol                      # red alert: to your station
    worf.station = "tactical"
    assert worf in list(Alert_Protocol)
    del Red_Alert[Bridge]
    print("   At_Station follows a keyword on the Bridge")

    civilian = Crew("Guinan")
    try:
        Officer(civilian)
    except Precondition.Is_Crew:
        print("   Is_Crew: a gate that reads Crew_Member")

    kurn = Crew("Kurn")
    kurn.decorated = True
    Crew_Member(kurn)
    Veteran(kurn)                                       # Alive, laid over Crew_Member's
    del Crew_Member[kurn]                               # the underneath leaves
    kurn.alive = False                                  # its promise no longer counts
    assert kurn in list(Veteran)                        # only the Veteran's own clause
    kurn.decorated = False
    assert kurn in ~Veteran
    print("   Veteran.Alive guards its own Underlay")


def main() -> None:
    worf = Crew("Worf")
    Crew_Member(worf)
    Bridge(worf)

    pattern_roles(worf)
    pattern_repair_table(worf)
    pattern_quarantine(worf)
    pattern_stale_handles(worf)
    pattern_requirements()
    pattern_author_guard(worf)
    print(f"\n{worf:contract}")


if __name__ == "__main__":
    main()
