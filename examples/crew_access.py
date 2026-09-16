"""A starship crew run through published members (STEP-SPEC-10): five
design patterns for access control and error control that need no
security code of their own.

    1. Roles are membership: what the role lends ends when you leave it.
    2. A repair table: catch a promise by name, repair it, retry.
    3. Quarantine for free: one broken promise closes every published door.
    4. Stale handles: a queued command from a relieved officer is refused
       when it runs, not when it was queued.
    5. Requirements: necessary to enter and necessary to stay, in one word.

Run:  PYTHONPATH=. python3 examples/crew_access.py
"""

from __future__ import annotations

from typing import Callable

from TopKit import Contract
from TopKit import Operation
from TopKit import Post
from TopKit import Postcondition
from TopKit import Precondition
from TopKit import Public
from TopKit import Record
from TopKit import Report
from TopKit import Requirement
from TopKit import Tag
from TopKit import TagPostconditionError
from TopKit import TagRogueAccessError


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


def main() -> None:
    worf = Crew("Worf")
    Crew_Member(worf)
    Bridge(worf)

    pattern_roles(worf)
    pattern_repair_table(worf)
    pattern_quarantine(worf)
    pattern_stale_handles(worf)
    pattern_requirements()
    print(f"\n{worf:contract}")


if __name__ == "__main__":
    main()
