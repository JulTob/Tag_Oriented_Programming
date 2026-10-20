"""Conformance tests: sticky condition."""

from __future__ import annotations

import unittest
from TopKit import Contract
from TopKit import Pin
from TopKit import Post
from TopKit import Postcondition
from TopKit import Pre
from TopKit import Precondition
from TopKit import Rip
from TopKit import Tag
from TopKit import TagResolutionError
from TopKit import Underlay

from ._fixtures import Agent


class StickyConditionTests(unittest.TestCase):
    """STEP-SPEC-12: conditions are sticky, like contributions. Rip never
    touches them. The author ends them: a guard in the condition, or an
    explicit deletion from the Tag's own @Rip protocol."""

    def test_a_ripped_tags_promise_still_binds(self) -> None:
        class Wizard(Tag):
            @Post
            def Has_Book(agent):
                return agent.book is not None

        ari = Agent()
        ari.book = []
        Wizard(ari)
        del Wizard[ari]                                               # a Rogue Agent
        ari.book = None

        self.assertEqual(Contract.Status(ari), {"Has_Book": False})   # the promise stays, and fails loud
        self.assertFalse(bool(ari))

    def test_a_ripped_gate_stays_on_the_record(self) -> None:
        class Gated(Tag):
            @Pre
            def Ready(agent):
                return agent.ready

        ari = Agent()
        ari.ready = True
        Gated(ari)
        del Gated[ari]
        ari.ready = False

        self.assertEqual(Contract.Status(ari), {"Ready": False})      # sticky: still on the Agent's record

        with self.assertRaises(Precondition.Ready):
            Contract.Preconditions(ari)

    def test_the_author_ends_a_promise_from_the_rip_protocol(self) -> None:
        class Sworn(Tag):
            @Post
            def Has_Oath(agent):
                return agent.oath is not None

            @Rip
            def Release(agent):
                Contract.Delete(agent, "Has_Oath")                    # one deliberate name

        ari = Agent()
        ari.oath = "sworn"
        Sworn(ari)
        del Sworn[ari]
        ari.oath = None

        self.assertEqual(Contract.Status(ari), {})
        self.assertTrue(bool(ari))

    def test_the_author_guards_a_promise_with_membership(self) -> None:
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

        self.assertEqual(Contract.Status(ari), {"Has_Oath": True})    # still listed, holds by the guard
        self.assertTrue(bool(ari))

        with self.assertRaises(Postcondition.Has_Oath):
            Sworn(ari)                                                # back in: the promise bites again

        self.assertFalse(bool(ari))

    def test_deleting_a_condition_that_is_not_there_is_refused(self) -> None:
        ari = Agent()

        with self.assertRaises(TagResolutionError):
            Contract.Delete(ari, "Has_Oath")

        class Plain(Tag):
            pass

        Plain(ari)

        with self.assertRaises(TagResolutionError):
            Contract.Delete(ari, "Has_Oath")

    def test_deletion_ends_both_halves_of_a_stacked_condition(self) -> None:
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

    def test_an_underlay_over_a_ripped_tag_keeps_calling_it_unless_guarded(self) -> None:
        class Alive(Tag):
            @Post
            def Fine(agent):
                return agent.alive

        class Elf(Tag):
            @Post
            @Underlay
            def Fine(agent, base):
                underneath = base() if agent in Alive[:] else True    # whose promise base() is
                return underneath and agent.pointy_ears

        ari = Agent()
        ari.alive, ari.pointy_ears = True, True
        Alive(ari)
        Elf(ari)
        del Alive[ari]
        ari.alive = False

        self.assertTrue(bool(ari))                          # the guard skipped the dead beat

    def test_a_pins_promise_is_sticky_and_the_pin_may_end_it(self) -> None:
        class Wizard(Tag):
            pass

        @Pin
        class Promised(Tag):
            @Post
            def Has_Members(tag):
                return bool(tag[:])

            @Rip
            def Release(tag):
                Contract.Delete(tag, "Has_Members")

        with self.assertRaises(Postcondition.Has_Members):
            Promised(Wizard)

        self.assertIn(Wizard, ~Promised)
        del Promised[Wizard]
        self.assertEqual(Contract.Status(Wizard), {})
