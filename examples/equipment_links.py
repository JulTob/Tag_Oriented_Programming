"""Equipment Links for GenLegend: carrying an item and equipping it are
separate responsibilities. A Link's Pair stores where this character
carries this item; the weapon keeps its own damage and durability.

Run:  PYTHONPATH=. python3 -m examples.equipment_links
"""

from __future__ import annotations

from TopKit import Action
from TopKit import Link
from TopKit import Post
from TopKit import Pre
from TopKit import Record
from TopKit import Report
from TopKit import Tag
from TopKit import TagResolutionError
from TopKit import Underlay
from TopKit import agent
from TopKit import contact

from examples.equipment import Character
from examples.equipment import Equipped
from examples.equipment import Item
from examples.equipment import Weapon


class Inventory(Equipped):
    @Link(agent, contact)
    class Carries(Tag):
        @Pre
        def Is_Equipment(agent, contact) -> bool:
            return isinstance(contact, Item)

        @Report
        def capacity(link) -> int:
            return 20

        @Record
        def position(agent, contact, *, position: str = "pack") -> str:
            return position

        @Post
        def Stored(agent, contact) -> bool:
            return agent.Carries[contact].position in ("hand", "pack", "belt")

        @Action
        def Move(agent, contact, position: str) -> None:
            agent.Carries[contact].position = position

    @Post
    @Underlay
    def Equipment_Valid(agent, prior) -> bool:
        # This layer explicitly adds carrying to the equipment requirement.
        # Sound Link membership checks the Contact and this Link's Pair.
        return (
                prior()
                and (
                    agent.weapon is None
                    or agent.weapon in agent.Carries
                    )
                )


def main() -> None:
    sword = Item("longsword")
    lantern = Item("lantern")
    Weapon(sword)

    ari, bob = Character("Ari"), Character("Bob")
    Inventory(ari)
    Inventory(bob)

    ari.Carries(sword, position="hand")
    ari.Carries(lantern, position="pack")
    bob.Carries(sword, position="pack")
    ari.weapon = sword

    assert sword in ari.Carries and sword in bob.Carries
    assert len(ari.Carries) == 2 and len(bob.Carries) == 1
    assert ari.Carries[sword].position == "hand"
    assert bob.Carries[sword].position == "pack"
    print("distinct Pairs: Ari's hand; Bob's pack")
    print("equipped:", ari.Attack())

    view = ari.Carries[sword]
    move = view.Move
    move("belt")
    assert view.position == "belt"
    assert bob.Carries[sword].position == "pack"
    assert sword.damage == 6 and sword.durability == 1
    print("moved: Ari's belt; weapon and Bob's Pair unchanged")

    ari.Carries.capacity = 2
    assert view.capacity == 2
    assert ari.Carries[lantern].capacity == 2
    assert bob.Carries.capacity == 20
    print("Reports belong to each actual Carries Tag")

    move("floor")
    assert sword in ari.Carries[:] and sword not in ari.Carries
    assert sword in ~ari.Carries
    assert not ari and sword in bob.Carries
    try:
        ari.Attack()
    except RuntimeError:
        print("broken carrying Post: attack refused")
    else:
        raise AssertionError("the equipment guard must require sound carrying")

    move("belt")
    assert ari

    del ari.Carries[sword]
    assert sword not in ari.Carries[:]
    assert lantern in ari.Carries and len(ari.Carries[:]) == 1
    assert sword in bob.Carries[:]
    assert sword in Weapon[:]                 # ending one Link leaves the weapon
    assert "weapon" @ ari and ari.weapon is sword
    assert not ari                            # explicit carrying requirement now fails
    try:
        view.position
    except TagResolutionError:
        print("Ripped: saved Pair view refuses absent membership")
    else:
        raise AssertionError("a saved view must resolve current membership")

    ari.Carries(sword, position="pack")
    assert view.position == "pack"
    move("hand")                              # the saved Action follows the fresh Pair
    assert view.position == "hand"
    assert bob.Carries[sword].position == "pack"
    assert ari
    print("reLinked: saved view and Action follow Ari's current Pair")


if __name__ == "__main__":
    main()
