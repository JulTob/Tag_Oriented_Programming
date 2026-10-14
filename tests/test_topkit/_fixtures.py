"""Shared hosts, Tags and subprocess support for the conformance suite."""

from __future__ import annotations

from TopKit import Action
from TopKit import Delete
from TopKit import Imprint
from TopKit import Operation
from TopKit import Post
from TopKit import Postcondition
from TopKit import Pre
from TopKit import Precondition
from TopKit import Record
from TopKit import Report
from TopKit import Rip
from TopKit import Tag
from TopKit import Underlay


def Run_Program(
        source: str,
        ) -> tuple[list[str], str]:
    """Run ``source`` in a fresh interpreter with this TopKit; return its
    output lines and its stderr. What a program does at exit is observable
    only there."""

    import pathlib
    import subprocess
    import sys

    root = pathlib.Path(__file__).resolve().parents[2]
    result = subprocess.run(
            [sys.executable, "-E", "-c", source],   # -E: the caller's PYTHON* settings stay out;
            cwd=root,                               # -c puts this checkout, the cwd, first on the path
            capture_output=True,
            text=True,
            timeout=60,                             # a hang at exit fails the test, not the run
            )

    return result.stdout.splitlines(), result.stderr


class Agent:
    def __init__(
            agent,
            ) -> None:
        agent.events: list[str] = []
        agent.allowed = True
        agent.ready = True
        agent.weapon = "faulty weapon"

    def Attack(
            agent,
            ) -> str:
        return "Faulty OOP attack!"


class Root(Tag):
    @Imprint
    def Mark_Root(agent) -> None:
        agent.events.append("Root")


class Left(Root):
    @Imprint
    def Mark_Left(agent) -> None:
        agent.events.append("Left")


class Right(Root):
    @Imprint
    def Mark_Right(agent) -> None:
        agent.events.append("Right")


class Bridge(Left, Right):
    @Imprint
    def Mark_Bridge(agent) -> None:
        agent.events.append("Bridge")


class Person(Tag):
    def Attack(agent) -> str:
        return "Attack!"


class Elf(Person):
    @Underlay
    def Attack(agent, underlay) -> str:
        return "With elven grace " + underlay()


class Paladin(Person):
    @Underlay
    def Attack(agent, underlay) -> str:
        return underlay() + " with a holy oath."


class Berserker(Tag):
    def Attack(agent) -> str:
        return "Reckless attack!"


class Combatant(Tag):
    def Combat(agent) -> str:
        return agent.Attack()


class OOP_Refinement(Tag):
    @Underlay
    def Attack(agent, underlay) -> str:
        return "Refined " + underlay()


class Inventory(Tag):
    @Record
    def items(agent) -> list[str]:
        return []


class Armed(Tag):
    @Record
    def weapon(agent) -> str:
        return "arcane staff"


class Prepared(Inventory):
    @Record
    def items(agent, stored) -> list[str]:
        return stored + ["rope"]


class Lost_Inventory(Prepared):
    @Delete
    def items(agent) -> None:
        pass


class Rebuilt_Inventory(Lost_Inventory):
    @Record
    def items(agent, stored) -> list[str]:
        assert stored is None
        return ["shield"]


class Pacifist(Tag):
    @Delete
    def Attack(agent) -> None:
        pass

    @Delete
    def weapon(agent) -> None:
        pass


class Needs_Action_Underlay(Pacifist):
    @Underlay
    def Attack(agent, underlay) -> str:
        return underlay()


class Repaired_Pacifist(Pacifist):
    def Attack(agent) -> str:
        return "Defensive action!"

    @Record
    def weapon(agent) -> str:
        return "shield"


class Species(Tag):
    @Imprint
    def Establish_Species(agent) -> None:
        agent.events.append("Species")


class Validated(Tag):
    @Precondition
    def Is_Allowed(agent) -> bool:
        return agent.allowed

    @Postcondition
    def Is_Ready(agent) -> bool:
        return agent.ready


class Advanced(Validated):
    pass


class Candidate_Record(Tag):
    @Record
    def token(agent) -> str:
        return "prepared"

    @Postcondition
    def Accepts_Token(agent) -> bool:
        return agent.ready


class Ordered_Imprints(Tag):
    @Imprint
    def First(agent) -> None:
        agent.events.append("First")

    @Imprint
    def Second(agent) -> None:
        agent.events.append("Second")


class Stocked(Tag):
    @Imprint
    def Note_Stocking(agent) -> None:
        agent.events.append("Stocked")

    @Record
    def supplies(agent) -> list[str]:
        return ["ration"]


class Broken_Imprint(Tag):
    @Imprint
    def Begin_Then_Fail(agent) -> None:
        agent.events.append("before failure")
        raise RuntimeError("expected imprint failure")


class Community(Tag):
    @Report
    def colour(tag) -> str:
        return "green"

    @Operation
    def Greet(tag, name: str) -> str:
        return f"{tag.__name__}:{name}"


class Silent_Community(Community):
    @Delete
    def colour(agent) -> None:
        pass

    @Delete
    def Greet(agent) -> None:
        pass


class Missing_Action(Tag):
    @Underlay
    def Missing(agent, underlay) -> str:
        return underlay()


class Arithmetic(Tag):
    def __add__(agent, amount: int) -> int:
        return amount + 1


class Field_Member(Tag):
    pass


class Territory(Tag):
    @Record
    def banner(agent) -> str:
        return "raised"


class Citadel(Territory):
    @Precondition
    def Has_Charter(agent) -> bool:
        return hasattr(agent, "charter")


class Cursed_Blade(Tag):
    @Record
    def weapon(agent) -> str:
        return "cursed dagger"

    @Postcondition
    def Is_Worthy(agent) -> bool:
        return agent.ready


class Squire(Tag):
    @Imprint
    def Enlist(agent) -> None:
        agent.events.append("Squire")

    @Record
    def rank(agent) -> str:
        return "squire"


class Knighted(Tag):
    @Imprint
    def Knight(agent) -> None:
        agent.events.append("Knighted")

    @Action
    @Rip
    def rank_reset(agent) -> str:
        agent.rank = None
        return "Disrobed"


class Beast(Tag):
    @Record
    def legs(agent) -> int:
        return 4


class Wolf(Beast):
    @Record
    def howl(agent) -> str:
        return "Awooo"


class Base_Greeting(Tag):
    def Greet(agent) -> str:
        return "hi"


class Greeter(Base_Greeting):
    @Action
    @Underlay
    def Greet(agent, base) -> str:
        return "Hello and " + base()


class Politely(Greeter):
    @Action
    @Underlay
    def Greet(agent, prior) -> str:
        return prior() + " good day"


class Slotted_Agent:
    __slots__ = ()


_DEL_LOG: list[str] = []


class Sentry(Tag):
    @Action
    @Rip
    def stand_down(agent) -> str:
        _DEL_LOG.append("stood down")
        return "stood down"


class Recruit(Tag):
    @Imprint
    def assign(spy, code) -> None:
        spy.code = code


class Coded(Tag):
    @Precondition
    def Has_Code(agent, code) -> bool:
        return code is not None


class Scholar(Tag):
    @Pre
    def Level_Over_Zero(agent):
        assert agent.level > 0

    @Imprint
    def Grant_Book(agent):
        agent.spellbook = "Tome"

    @Post
    def Has_Book(agent):
        assert agent.spellbook


class Capped(Tag):
    @Post
    def Strength_Capped(agent):
        return agent.strength <= 20


class Bruiser(Capped):
    @Post
    def Strength_Capped(agent):
        return agent.strength <= 24


class Disciplined(Capped):
    @Post
    @Underlay
    def Strength_Capped(agent, base):
        return base() and agent.strength <= 18


class Reflective(Tag):
    @Post
    def Self_Aware(agent):
        if agent:
            return True


class Slotted(Tag):
    @Post
    def Raw_Slots(agent):
        return agent.spell_slots


class Reserved(Tag):
    @Post
    def Has_Slots_Record(agent):
        assert agent.spell_slots is not None


class Bag:
    def __init__(self) -> None:
        self.items = ["x"]

    def __contains__(self, key) -> bool:
        return key in self.items

    def __len__(self) -> int:
        return len(self.items)

    def __or__(self, other) -> str:
        return "host-or"

    def __getattr__(self, name) -> str:
        if name == "dynamic":
            return "from host getattr"

        raise AttributeError(name)
