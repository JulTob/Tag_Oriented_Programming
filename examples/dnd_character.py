"""A character sheet the D&D way: species, class, background and feats are
independent Tags; the sheet is what they compose.

Run:  PYTHONPATH=. python3 examples/dnd_character.py
"""

from __future__ import annotations

from TagKit import Action
from TagKit import Contract
from TagKit import Imprint
from TagKit import Outline
from TagKit import Post
from TagKit import Pre
from TagKit import Record
from TagKit import Report
from TagKit import Tag
from TagKit import Underlay


class Character:
    """The host: inherent structure only."""

    def __init__(
            character,
            name: str,
            level: int,
            ) -> None:
        character.name = name
        character.level = level


# --- Species ------------------------------------------------------


class Species(Tag):
    @Record
    def speed(agent) -> int:
        return 30


class Elf(Species):
    @Record
    def spells(agent, stored) -> list[str]:
        # Piling up: whatever is stored already, plus the Elf's gift.
        return (stored or []) + ["Light"]

    @Record
    def senses(agent) -> list[str]:
        return ["Darkvision"]


class Dwarf(Species):
    @Record
    def speed(agent) -> int:
        return 25

    @Record
    def hit_points(agent, stored) -> int:
        return (stored or 0) + agent.level      # +1 per level


# --- Class --------------------------------------------------------


class Class(Tag):
    hit_die = Report(8)

    @Record
    def hit_points(agent, stored) -> int:
        return (stored or 0) + agent.level * Class.hit_die


class Wizard(Class):
    hit_die = Report(6)

    @Pre
    def Can_Study(agent):
        return agent.level >= 1

    @Record
    def hit_points(agent, stored) -> int:
        return (stored or 0) + agent.level * Wizard.hit_die

    @Record
    def spells(agent, stored) -> list[str]:
        return (stored or []) + ["Magic Missile", "Shield"]

    @Post
    def Knows_Spells(agent):
        return len(agent.spells) > 0

    @Action
    def Attack(agent) -> str:
        return f"{agent.name} casts {agent.spells[-1]}"


class Fighter(Class):
    hit_die = Report(10)

    @Record
    def hit_points(agent, stored) -> int:
        return (stored or 0) + agent.level * Fighter.hit_die

    @Action
    def Attack(agent) -> str:
        return f"{agent.name} swings a sword"


# --- Background ---------------------------------------------------


class Sage(Tag):
    @Record
    def spells(agent, stored) -> list[str]:
        return (stored or []) + ["Identify"]

    @Record
    def languages(agent, stored) -> list[str]:
        return (stored or ["Common"]) + ["Draconic"]


# --- Feats: synergy through Preconditions --------------------------


class War_Caster(Tag):
    """Only a spellcaster who can also hold the line may take War Caster."""

    @Pre
    def Is_A_Caster(agent):
        return agent in Wizard

    @Action
    @Underlay
    def Attack(agent, underlay) -> str:
        return underlay() + " while holding a shield"


class Tough(Tag):
    @Record
    def hit_points(agent, stored) -> int:
        return (stored or 0) + 2 * agent.level

    @Imprint
    def note(agent) -> None:
        print(f"  {agent.name} took Tough: hit points now {agent.hit_points}")


def main() -> None:
    ari = Character("Ari", level=3)

    Elf(ari)
    Wizard(ari)
    Sage(ari)
    War_Caster(ari)
    Tough(ari)

    print(Outline(ari))
    print()
    print("spells     :", ari.spells)          # Elf + Wizard + Sage
    print("hit points :", ari.hit_points)      # Wizard 3*6 + Tough 2*3
    print("speed      :", ari.speed)
    print("languages  :", ari.languages)
    print("attack     :", ari.Attack())
    print("as a plain Wizard:", ari.Wizard.Attack())
    print()
    print(Contract.Display(ari))
    print()

    bruk = Character("Bruk", level=2)
    Dwarf(bruk)
    Fighter(bruk)

    try:
        War_Caster(bruk)
    except Exception as error:
        print("Bruk cannot take War Caster:", type(error).__name__)

    print("Bruk hit points:", bruk.hit_points, "(Fighter 2*10 + Dwarf 2)")
    print("Bruk attack    :", bruk.Attack())


if __name__ == "__main__":
    main()
