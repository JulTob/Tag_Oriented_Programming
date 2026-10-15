"""Conformance tests: condition member."""

from __future__ import annotations

import unittest
from TopKit import Contract
from TopKit import Pin
from TopKit import Post
from TopKit import Postcondition
from TopKit import Pre
from TopKit import Record
from TopKit import Tag
from TopKit import TagCompositionError
from TopKit import TagContractError

from ._fixtures import Agent


class ConditionMemberTests(unittest.TestCase):
    """STEP-SPEC-14: a condition is read on the Agent by its name, as a
    plain bool, computed on read. Nothing lands on the Agent."""

    def test_a_condition_reads_as_a_bool_on_the_agent(self) -> None:
        class Wizard(Tag):
            @Post
            def Has_Book(agent):
                return agent.book is not None

            @Pre
            def Is_Awake(agent):
                return agent.awake

        ari = Agent()
        ari.book, ari.awake = [], True
        Wizard(ari)

        self.assertIs(ari.Has_Book, True)
        self.assertIs(ari.Is_Awake, True)
        self.assertTrue(hasattr(ari, "Has_Book"))
        self.assertNotIn("Has_Book", vars(ari))                       # computed on read, not stored

        ari.book = None
        self.assertIs(ari.Has_Book, False)
        self.assertFalse(ari)
        self.assertNotIn("Has_Book", Contract.Status(ari) and vars(ari))

        with self.assertRaises(AttributeError):
            ari.Has_Sword                                             # no such condition

    def test_a_raising_condition_reads_false_and_a_non_bool_is_refused(self) -> None:
        class Loud(Tag):
            @Post
            def Ready(agent):
                assert agent.ready

            @Post
            def Count(agent):
                return agent.count

        ari = Agent()
        ari.ready, ari.count = True, True
        Loud(ari)
        ari.ready = False
        self.assertIs(ari.Ready, False)

        ari.count = 0
        with self.assertRaises(TagContractError):
            ari.Count

    def test_a_pinned_tags_condition_reads_on_the_tag(self) -> None:
        class Wizard(Tag):
            pass

        @Pin
        class Promised(Tag):
            @Post
            def Has_Members(tag):
                return bool(tag[:])

        with self.assertRaises(Postcondition.Has_Members):
            Promised(Wizard)

        self.assertIs(Wizard.Has_Members, False)
        ari = Agent()                                                 # held: Fields are weak
        Wizard(ari)
        self.assertIs(Wizard.Has_Members, True)

    def test_a_condition_cannot_share_a_name_with_an_action_or_record(self) -> None:
        class Named(Tag):
            @Post
            def Has_Book(agent):
                return True

        class Clash_Record(Tag):
            @Record
            def Has_Book(agent):
                return 1

        class Clash_Action(Tag):
            def Has_Book(agent):
                return 1

        ari = Agent()
        Named(ari)

        with self.assertRaises(TagCompositionError):
            Clash_Record(ari)

        with self.assertRaises(TagCompositionError):
            Clash_Action(ari)

        bo = Agent()
        Clash_Record(bo)

        with self.assertRaises(TagCompositionError):
            Named(bo)                                                 # the other way round

        self.assertNotIn(bo, Named)                                   # rolled back

    def test_a_condition_cannot_share_a_name_with_the_host(self) -> None:
        class Host:
            def Has_Book(self):
                return "host"

        class Named(Tag):
            @Post
            def Has_Book(agent):
                return True

        with self.assertRaises(TagCompositionError):
            Named(Host())

        class Valued(Tag):
            @Post
            def book(agent):
                return True

        ari = Agent()
        ari.book = []                                                 # a value the Agent holds

        with self.assertRaises(TagCompositionError):
            Valued(ari)

        self.assertNotIn(ari, Valued)

    def test_the_member_and_the_status_agree(self) -> None:
        class Elf(Tag):
            @Pre
            @Post
            def Alive(agent):
                return agent.alive

        ari = Agent()
        ari.alive = True
        Elf(ari)
        self.assertEqual(Contract.Status(ari), {"Alive": True})
        self.assertIs(ari.Alive, True)

        ari.alive = False
        self.assertEqual(Contract.Status(ari), {"Alive": False})
        self.assertIs(ari.Alive, False)
