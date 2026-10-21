"""Equipment for a GenLegend character: the weapon keeps its own state;
the character holds it through a checked Tool Record.

Run:  PYTHONPATH=. python3 examples/equipment.py
"""

from __future__ import annotations

from TopKit import Action
from TopKit import Post
from TopKit import Record
from TopKit import Tag
from TopKit import TagCompositionError
from TopKit import Tool


class Character:
    def __init__(character, name: str) -> None:
        character.name = name


class Item:
    def __init__(item, name: str) -> None:
        item.name = name


class Weapon(Tag):
    """Damage and wear belong to the weapon, whoever carries it."""

    @Record
    def damage(weapon, *, damage: int = 6) -> int:
        return damage

    @Record
    def durability(weapon, *, durability: int = 2) -> int:
        return durability

    @Post
    def Usable(weapon) -> bool:
        return weapon.damage > 0 and weapon.durability > 0

    @Action
    def Strike(weapon) -> int:
        # Ordinary Actions use explicit guards for the promises they need.
        if not weapon.Usable:
            raise RuntimeError("the weapon needs repair")

        weapon.durability -= 1
        return weapon.damage

    @Action
    def Repair(weapon) -> None:
        # Repair can run while Usable is false; it restores the Record.
        weapon.durability = 2


class Equipped(Tag):
    @Tool(Item, Weapon | None)
    def weapon(agent, *, weapon=None):
        # The forge has already Tagged the item. This builder only reads.
        return weapon

    @Post
    def Equipment_Valid(agent) -> bool:
        # Presence, an empty hand, membership and validity are separate asks.
        return (
                "weapon" @ agent
                and (
                    agent.weapon is None
                    or (
                        agent.weapon in Weapon[:]
                        and bool(agent.weapon)
                        )
                    )
                )

    @Action
    def Attack(agent) -> str:
        if not agent.Equipment_Valid:
            raise RuntimeError("repair or replace the equipped weapon")

        weapon = agent.weapon
        if weapon is None:
            raise RuntimeError("choose a weapon before attacking")

        return f"{agent.name} strikes with {weapon.name} for {weapon.Strike()}"


def main() -> None:
    sword = Item("longsword")
    spare = Item("shortsword")
    Weapon(sword)
    Weapon(spare, damage=4)

    ari = Character("Ari")
    Equipped(ari, weapon=sword)

    print(ari.Attack())
    print(ari.Attack())
    assert sword in Weapon[:]               # a broken weapon is still admitted
    assert sword in ~Weapon
    assert ari in ~Equipped                  # the bearer explicitly requires validity

    try:
        ari.Attack()
    except RuntimeError:
        print("worn weapon: attack refused")
    else:
        raise AssertionError("the guard must refuse a worn weapon")

    sword.Repair()
    assert sword and ari
    print("repaired:", ari.Attack())

    try:
        ari.weapon = Item("walking stick")
    except TagCompositionError:
        print("wrong kind: assignment refused")
    else:
        raise AssertionError("a plain Item is not a Weapon")

    assert ari.weapon is sword               # a refused assignment kept the binding
    ari.weapon = spare
    print("swapped:", ari.Attack())

    ari.weapon = None                        # an explicit empty hand is allowed
    assert "weapon" @ ari and ari.weapon is None and bool(ari)
    try:
        ari.Attack()
    except RuntimeError:
        print("empty hand: attack refused")
    else:
        raise AssertionError("an empty hand cannot strike with a weapon")

    del ari.weapon                          # absence differs from a present None
    assert not ("weapon" @ ari) and not ari
    assert spare in Weapon[:]
    ari.weapon = spare
    assert ari
    print("equipped again:", ari.weapon.name)


if __name__ == "__main__":
    main()
