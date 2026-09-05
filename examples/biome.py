"""A pokemon-style biome: creatures are mixed and matched from small Tags.
No two need the same type to be predictable; every one answers the same
questions.

Run:  PYTHONPATH=. python3 examples/biome.py
"""

from __future__ import annotations

import random

from TagKit import Action
from TagKit import Flag
from TagKit import Keyword
from TagKit import Post
from TagKit import Public
from TagKit import Record
from TagKit import Report
from TagKit import Tag
from TagKit import Tags
from TagKit import Underlay


class Creature:
    def __init__(
            creature,
            name: str,
            ) -> None:
        creature.name = name


class Element(Tag):
    @Public
    @Report
    def colour(tag) -> str:
        return "grey"

    @Record
    def attacks(agent, stored) -> list[str]:
        return stored or []

    @Post
    def Has_An_Attack(agent):
        return len(agent.attacks) > 0


@Flag
class Fire(Element):
    @Public
    @Report
    def colour(tag) -> str:
        return "red"

    @Record
    def attacks(agent, stored) -> list[str]:
        return (stored or []) + ["Ember"]


@Flag
class Water(Element):
    @Public
    @Report
    def colour(tag) -> str:
        return "blue"

    @Record
    def attacks(agent, stored) -> list[str]:
        return (stored or []) + ["Bubble"]


@Flag
class Electric(Element):
    @Public
    @Report
    def colour(tag) -> str:
        return "yellow"

    @Record
    def attacks(agent, stored) -> list[str]:
        return (stored or []) + ["Spark"]


class Body(Tag):
    @Record
    def hp(agent) -> int:
        return 20

    @Action
    def Describe(agent) -> str:
        return f"{agent.name} ({agent.colour}, {agent.hp} hp): {', '.join(agent.attacks)}"


class Winged(Body):
    @Record
    def hp(agent, stored) -> int:
        return stored - 5

    @Action
    @Underlay
    def Describe(agent, underlay) -> str:
        return underlay() + " [flies]"


class Armoured(Body):
    @Record
    def hp(agent, stored) -> int:
        return stored + 15

    @Action
    @Underlay
    def Describe(agent, underlay) -> str:
        return underlay() + " [armoured]"


# A type chart as data: keywords, not imports. It ports to any program
# whose Flags carry these names.
STRONG_AGAINST = {
        "Water": "Fire",
        "Fire": "Electric",
        "Electric": "Water",
        }


def advantage(
        attacker: Creature,
        defender: Creature,
        ) -> bool:
    return any(
            Keyword(attacker, mine) and Keyword(defender, theirs)
            for mine, theirs in STRONG_AGAINST.items()
            )


def main() -> None:
    random.seed(7)
    elements = (Fire, Water, Electric)
    bodies = (Body, Winged, Armoured)
    biome = []

    for index in range(8):
        creature = Creature(f"creature-{index}")

        for element in random.sample(elements, k=random.randint(1, 2)):
            element(creature)

        random.choice(bodies)(creature)
        biome.append(creature)

    for creature in biome:
        print(creature.Describe(), "<-", [tag.__name__ for tag in Tags(creature)])

    print()
    first, second = biome[0], biome[1]
    print(f"{first.name} vs {second.name}: advantage", advantage(first, second))
    print("keywords of", first.name, "->", [w for w in STRONG_AGAINST if w in first])
    print()
    print("runtime types in the biome:", len({type(c) for c in biome}))
    print("Fire creatures:", [c.name for c in Fire])
    print("sound Elements:", len(Element), "of", len(Element[:]))


if __name__ == "__main__":
    main()
