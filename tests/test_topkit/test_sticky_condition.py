"""Conformance tests: condition lifetimes."""

from __future__ import annotations

import unittest
from TopKit import Constant
from TopKit import Contract
from TopKit import Pin
from TopKit import Post
from TopKit import Postcondition
from TopKit import Pre
from TopKit import Precondition
from TopKit import Rip
from TopKit import Tag
from TopKit import Underlay

from ._fixtures import Agent


class StickyConditionTests(unittest.TestCase):
    """Pres are transient; Posts follow membership unless Constant."""

    def test_a_ripped_tags_ordinary_promise_ends(self) -> None:
        class Wizard(Tag):
            @Post
            def Has_Book(agent):
                return agent.book is not None

        ari = Agent()
        ari.book = []
        Wizard(ari)
        del Wizard[ari]                                               # a Rogue Agent
        ari.book = None

        self.assertEqual(Contract.Status(ari), {})
        self.assertTrue(bool(ari))
        with self.assertRaises(AttributeError):
            ari.Has_Book

    def test_a_constant_promise_survives_field_removal(self) -> None:
        class Employer(Tag):
            @Constant
            @Post
            def Keeps_NDA(agent):
                return agent.keeps_secret

        ari = Agent()
        ari.keeps_secret = True
        Employer(ari)
        del Employer[ari]

        self.assertEqual(Contract.Status(ari), {"Keeps_NDA": True})
        ari.keeps_secret = False
        self.assertFalse(ari.Keeps_NDA)
        self.assertFalse(bool(ari))

    def test_a_gate_never_lands_on_the_agents_record(self) -> None:
        class Gated(Tag):
            @Pre
            def Ready(agent):
                return agent.ready

        ari = Agent()
        ari.ready = True
        Gated(ari)
        ari.ready = False

        self.assertEqual(Contract.Status(ari), {})
        self.assertFalse(hasattr(ari, "Ready"))
        self.assertTrue(bool(ari))

    def test_an_old_explicit_rip_deletion_is_safe_after_automatic_end(self) -> None:
        class Sworn(Tag):
            @Post
            def Has_Oath(agent):
                return agent.oath is not None

            @Rip
            def Release(agent):
                Contract.Delete(agent, "Has_Oath")                    # already ended at Field removal

        ari = Agent()
        ari.oath = "sworn"
        Sworn(ari)
        del Sworn[ari]
        ari.oath = None

        self.assertEqual(Contract.Status(ari), {})
        self.assertTrue(bool(ari))

    def test_a_membership_guard_is_no_longer_needed_for_lifetime(self) -> None:
        class Sworn(Tag):
            @Post
            def Has_Oath(agent):
                if agent not in Sworn[:]:                             # raw admission, even while this Post runs
                    return True
                return agent.oath is not None

        ari = Agent()
        ari.oath = "sworn"
        Sworn(ari)
        del Sworn[ari]
        ari.oath = None

        self.assertEqual(Contract.Status(ari), {})
        self.assertTrue(bool(ari))

        with self.assertRaises(Postcondition.Has_Oath):
            Sworn(ari)                                                # back in: the promise bites again

        self.assertFalse(bool(ari))

    def test_deleting_an_absent_post_is_neutral_and_repeatable(self) -> None:
        ari = Agent()

        Contract.Delete(ari, "Has_Oath")

        class Plain(Tag):
            pass

        Plain(ari)

        Contract.Delete(ari, "Has_Oath")
        self.assertEqual(Contract.Status(ari), {})

    def test_field_removal_ends_only_the_post_role_of_a_stacked_body(self) -> None:
        class Elf(Tag):
            @Pre
            @Post
            def Alive(agent):
                return agent.alive

            @Rip
            def Release(agent):
                Contract.Delete(agent, "Alive")

        ari = Agent()
        ari.alive = True
        Elf(ari)
        self.assertEqual(Contract.Status(ari), {"Alive": True})

        del Elf[ari]
        self.assertEqual(Contract.Status(ari), {})
        ari.alive = False
        with self.assertRaises(Precondition.Alive):
            Elf(ari)                                                   # the Tag's Pre Service still gates a new attempt

    def test_an_underlay_reconnects_to_neutral_when_its_lower_post_ends(self) -> None:
        class Alive(Tag):
            @Post
            def Fine(agent):
                return agent.alive

        class Elf(Tag):
            @Post
            @Underlay
            def Fine(agent, base):
                return base() and agent.pointy_ears

        ari = Agent()
        ari.alive, ari.pointy_ears = True, True
        Alive(ari)
        Elf(ari)
        del Alive[ari]
        ari.alive = False

        self.assertTrue(bool(ari))                          # missing lower Post contributes neutral True

    def test_a_pins_ordinary_promise_ends_with_pin_membership(self) -> None:
        class Wizard(Tag):
            pass

        @Pin
        class Promised(Tag):
            @Post
            def Has_Members(tag):
                return bool(tag[:])

        with self.assertRaises(Postcondition.Has_Members):
            Promised(Wizard)

        self.assertIn(Wizard, ~Promised)
        del Promised[Wizard]
        self.assertEqual(Contract.Status(Wizard), {})
