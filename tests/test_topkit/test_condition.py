"""Conformance tests: condition."""

from __future__ import annotations

import unittest
from TopKit import Contract
from TopKit import Post
from TopKit import Postcondition
from TopKit import Pre
from TopKit import Precondition
from TopKit import Tag
from TopKit import TagPostconditionError
from TopKit import TagPreconditionError

from ._fixtures import Agent


class ConditionTests(unittest.TestCase):
    """@Pre and @Post stacked on one function: necessary to enter and
    necessary to stay."""

    def test_a_stacked_condition_gates_and_promises(self) -> None:
        class Elf(Tag):
            @Pre
            @Post
            def Alive(agent):
                return agent.alive

        dead = Agent()
        dead.alive = False

        with self.assertRaises(Precondition.Alive):
            Elf(dead)                                                 # necessary to enter

        ari = Agent()
        ari.alive = True
        Elf(ari)
        self.assertEqual(Contract.Status(ari), {"Alive": True})
        self.assertTrue(ari)

        ari.alive = False                                             # necessary to stay
        self.assertFalse(ari)
        self.assertIn(ari, ~Elf)

        with self.assertRaises(Postcondition.Alive):
            Contract.Postconditions(ari)

        self.assertIs(Precondition.Alive, TagPreconditionError.Alive)
        self.assertIs(Postcondition.Alive, TagPostconditionError.Alive)

    def test_the_two_marks_stack_in_either_order(self) -> None:
        class Vampire(Tag):
            @Post
            @Pre
            def Undead(agent):
                return agent.undead

        mortal = Agent()
        mortal.undead = False

        with self.assertRaises(Precondition.Undead):
            Vampire(mortal)                                           # necessary to enter

        nosferatu = Agent()
        nosferatu.undead = True
        Vampire(nosferatu)

        nosferatu.undead = False                                      # necessary to stay
        with self.assertRaises(Postcondition.Undead):
            Contract.Postconditions(nosferatu)

    def test_a_stacked_condition_fails_under_the_name_of_the_half_that_refused(self) -> None:
        class Vampire(Tag):
            @Pre
            @Post
            def Undead(agent):
                return agent.undead

        mortal = Agent()
        mortal.undead = False

        with self.assertRaises(Precondition.Undead) as at_the_door:
            Vampire(mortal)

        self.assertIsInstance(at_the_door.exception, Precondition.Undead)
        self.assertNotIsInstance(at_the_door.exception, Postcondition.Undead)

        nosferatu = Agent()
        nosferatu.undead = True
        Vampire(nosferatu)
        nosferatu.undead = False

        with self.assertRaises(Postcondition.Undead) as afterwards:
            Contract.Postconditions(nosferatu)

        self.assertIsInstance(afterwards.exception, Postcondition.Undead)
        self.assertNotIsInstance(afterwards.exception, Precondition.Undead)

    def test_requirement_is_no_longer_exported(self) -> None:
        import TopKit
        import TopKit.declarations

        with self.assertRaises(ImportError):
            from TopKit import Requirement

        with self.assertRaises(ImportError):
            from TopKit.declarations import Requirement

        self.assertNotIn("Requirement", TopKit.__all__)
        self.assertFalse(hasattr(TopKit, "Requirement"))
        self.assertFalse(hasattr(TopKit.declarations, "Requirement"))
