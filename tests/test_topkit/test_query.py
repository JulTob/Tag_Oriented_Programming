"""Conformance tests: query."""

from __future__ import annotations

import unittest
from TopKit import Apply
from TopKit import Contract
from TopKit import Flag
from TopKit import Keyword
from TopKit import Outline
from TopKit import Tag
from TopKit import TagCompositionError
from TopKit import TagDeclarationError
from TopKit import Tags

from ._fixtures import Agent
from ._fixtures import Bag
from ._fixtures import Bridge
from ._fixtures import Combatant
from ._fixtures import Elf
from ._fixtures import Field_Member
from ._fixtures import Paladin
from ._fixtures import Person
from ._fixtures import Scholar


class QueryTests(unittest.TestCase):
    def test_flags_are_searchable_from_the_agent_side(self) -> None:
        @Flag
        class Undead(Tag):
            pass

        @Flag
        class Flying(Tag):
            pass

        ghoul = Agent()

        Undead(ghoul)
        Elf(ghoul)                                # an ordinary Tag, not a keyword

        self.assertIn("Undead", ghoul)
        self.assertIn(Undead, ghoul)
        self.assertNotIn("Flying", ghoul)
        self.assertNotIn(Flying, ghoul)
        self.assertNotIn("undead", ghoul)         # names match exactly
        self.assertNotIn("Elf", ghoul)            # Elf is not a Flag
        self.assertNotIn(Elf, ghoul)
        self.assertIn(ghoul, Elf)                 # membership is untouched

        self.assertTrue(Keyword(ghoul, "Undead", Undead))
        self.assertFalse(Keyword(ghoul, "Undead", "Flying"))
        self.assertFalse(Keyword(ghoul, "Elf"))
        self.assertFalse(Keyword(Agent(), "Undead"))   # works before any tagging

        del Undead[ghoul]

        self.assertNotIn("Undead", ghoul)

    def test_a_flag_on_a_container_host_is_refused(self) -> None:
        @Flag
        class Marked(Tag):
            pass

        bag = Bag()

        with self.assertRaises(TagCompositionError):
            Marked(bag)

        self.assertNotIn(bag, Marked)
        self.assertIn("x", bag)

    def test_flag_marks_only_tags(self) -> None:
        with self.assertRaises(TagDeclarationError):
            Flag(Agent)

    def test_rules_written_as_keywords_port_between_programs(self) -> None:
        @Flag
        class Wizard(Tag):
            pass

        @Flag
        class Elven(Tag):
            pass

        rules = {
                "Wizard-Elven": lambda a: "arcane archer",
                "Wizard": lambda a: "caster",
                "Elven": lambda a: "archer",
                }

        def play(agent):
            for rule, act in rules.items():
                if Keyword(agent, *rule.split("-")):
                    return act(agent)

            return "commoner"

        ari = Agent()
        Wizard(ari)
        self.assertEqual(play(ari), "caster")

        Elven(ari)
        self.assertEqual(play(ari), "arcane archer")
        self.assertTrue(all(word in ari for word in "Wizard-Elven".split("-")))
        self.assertEqual(play(Agent()), "commoner")

    def test_apply_and_tags(self) -> None:
        ari = Apply(Agent(), Elf, Combatant)

        self.assertIn(ari, Elf)
        self.assertIn(ari, Person)
        self.assertNotIn(ari, Paladin)
        self.assertEqual(Tags(ari), (Elf, Combatant))

    def test_format_specs_are_the_display_door(self) -> None:
        ari = Agent()
        ari.level = 1

        Elf(ari)
        Scholar(ari)

        self.assertEqual(f"{Elf:form}", "Person → Elf")
        self.assertEqual(f"{Bridge:form}", "Root → Left → Right → Bridge")
        self.assertEqual(f"{Elf}", str(Elf))
        self.assertEqual(f"{ari:tags}", "Elf, Scholar")
        self.assertEqual(f"{ari:outline}", Outline(ari))
        self.assertEqual(f"{ari:contract}", Contract.Display(ari))
        self.assertEqual(f"{ari}", str(ari))

        with self.assertRaises(ValueError):
            f"{Elf:nope}"

        with self.assertRaises(ValueError):
            f"{ari:nope}"

    def test_host_format_keeps_its_seat(self) -> None:
        class Money:
            def __init__(self) -> None:
                self.cents = 1234

            def __format__(self, spec: str) -> str:
                return f"${self.cents / 100:.2f}"

        purse = Money()
        Field_Member(purse)

        self.assertEqual(f"{purse}", "$12.34")

    def test_outline_draws_each_form(self) -> None:
        ari = Agent()

        Elf(ari)
        Combatant(ari)

        self.assertEqual(
                Outline(ari),
                "Agent\n  Person\n    Elf\n  Combatant",
                )
