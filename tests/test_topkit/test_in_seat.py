"""Conformance tests: in seat."""

from __future__ import annotations

import collections.abc
import unittest
from TopKit import Delete
from TopKit import Flag
from TopKit import Keyword
from TopKit import Imprint
from TopKit import Operation
from TopKit import Pin
from TopKit import Post
from TopKit import Public
from TopKit import Record
from TopKit import Tag
from TopKit import TagCompositionError
from TopKit import TagDeclarationError

from ._fixtures import Agent
from ._fixtures import Bag
from ._fixtures import Elf


class InSeatTests(unittest.TestCase):
    """STEP-SPEC-7, amended: a Flag's words need the Agent's `in`. The host
    (through __contains__ or __iter__) or a Tag's Action of either name
    may already answer it; the two collide, in either order, and the
    collision is refused and named. `in` never changes meaning in silence."""

    class Party:
        def __init__(self) -> None:
            self.members = ["alice", "bob"]

        def __iter__(self):
            return iter(self.members)

    def setUp(self) -> None:
        @Flag("Wolf")
        class Werewolf(Tag):
            pass

        class Roster(Tag):
            def __iter__(agent):
                return iter(["alice", "bob"])

        class Gate(Tag):
            def __contains__(agent, key) -> bool:
                return key == "alice"

        self.Werewolf, self.Roster, self.Gate = Werewolf, Roster, Gate

    def refused(self, act, *mentions: str) -> None:
        with self.assertRaises(TagCompositionError) as caught:
            act()

        for mention in mentions:
            self.assertIn(mention, str(caught.exception))

    def test_an_iterable_host_refuses_a_flag(self) -> None:
        for tagged_first in (False, True):
            party = self.Party()

            if tagged_first:
                Elf(party)

            self.refused(lambda: self.Werewolf(party), "Werewolf", "Party.__iter__")

            self.assertIn("alice", party)                 # membership keeps its meaning
            self.assertNotIn(party, self.Werewolf)
            self.assertFalse(Keyword(party, "Wolf"))

    def test_the_refusal_names_the_class_that_answers(self) -> None:
        class Crew(self.Party):
            pass

        class Deck:
            def __iter__(self):
                yield "ace"

        self.refused(lambda: self.Werewolf(Crew()), "Crew already answers", "Party.__iter__")
        self.refused(lambda: self.Werewolf(Deck()), "Deck.__iter__")
        self.refused(lambda: self.Werewolf(Bag()), "Bag.__contains__")

    def test_a_host_that_declares_no_in_is_a_free_seat(self) -> None:
        class Loud(self.Party):
            __contains__ = None                           # Python: `in` is unavailable

        class Mute:
            __iter__ = None

        class Guild(collections.abc.Sequence):            # the parent owns `in`; the child says no
            __contains__ = None

            def __getitem__(self, index):
                return ["alice"][index]

            def __len__(self) -> int:
                return 1

        for host in (Loud(), Mute(), Guild()):
            with self.assertRaises(TypeError):
                "alice" in host

            self.Werewolf(host)

            self.assertIn("Wolf", host)                   # the Flag holds the seat
            self.assertNotIn("alice", host)

        self.assertEqual(list(Loud()), ["alice", "bob"])  # iteration is untouched

    def test_a_keyed_host_gives_its_seat_to_a_flag(self) -> None:
        class Sheet:
            def __init__(self) -> None:
                self.scores = {"STR": 16}

            def __getitem__(self, key):
                return self.scores[key]

        sheet = Sheet()

        with self.assertRaises(KeyError):
            "STR" in sheet                                # Python's fallback asks sheet[0]

        self.Werewolf(sheet)

        self.assertIn("Wolf", sheet)
        self.assertEqual(sheet["STR"], 16)

    def test_a_tag_that_answers_in_then_a_flag(self) -> None:
        for answering, method in (
                (self.Roster, "Roster.__iter__"),
                (self.Gate, "Gate.__contains__"),
                ):
            ari = Agent()
            answering(ari)
            before = "alice" in ari

            self.refused(lambda: self.Werewolf(ari), "Werewolf", method)

            self.assertIs("alice" in ari, before)         # unchanged
            self.assertTrue(before)
            self.assertNotIn(ari, self.Werewolf)

    def test_a_flag_then_a_tag_that_answers_in(self) -> None:
        for answering, method in (
                (self.Roster, "Roster.__iter__"),
                (self.Gate, "Gate.__contains__"),
                ):
            ari = Agent()
            self.Werewolf(ari)

            self.refused(lambda: answering(ari), method, "Flag Werewolf")

            self.assertIn("Wolf", ari)                    # the words keep the seat
            self.assertNotIn(ari, answering)

    def test_a_shape_collision_keeps_its_completed_flag_base(self) -> None:
        Werewolf = self.Werewolf

        class Pack_Leader(Werewolf):
            def __iter__(agent):
                return iter(["alice"])

        ari = Agent()

        self.refused(lambda: Pack_Leader(ari), "Pack_Leader.__iter__", "Flag Werewolf")

        self.assertIn(ari, Werewolf)
        self.assertNotIn(ari, Pack_Leader)
        self.assertIn("Wolf", ari)

    def test_a_flag_cannot_answer_in_itself(self) -> None:
        class Pack(Tag):
            def __iter__(agent):
                return iter(())

        class Den(Tag):
            def __contains__(agent, key) -> bool:
                return False

        for tag, method in (
                (Pack, "__iter__"),
                (Den, "__contains__"),
                ):
            with self.assertRaises(TagDeclarationError) as caught:
                Flag("Wolf")(tag)

            self.assertIn(method, str(caught.exception))
            self.assertIsNone(vars(tag).get("__topkit_flag__"))   # nothing was marked

        @Flag
        class Quiet(Tag):                                 # a Record by that name answers nothing
            @Record
            def __iter__(agent):
                return None

    def test_after_the_flag_is_ripped_a_tag_may_answer_in(self) -> None:
        ari = Agent()
        self.Werewolf(ari)
        del self.Werewolf[ari]

        self.Roster(ari)

        self.assertIn("alice", ari)                       # iteration answers again
        self.assertNotIn("Wolf", ari)

    def test_a_ripped_tag_leaves_its_answer_and_the_refusal(self) -> None:
        ari = Agent()
        self.Roster(ari)
        del self.Roster[ari]                              # Actions are sticky (§0.7)

        self.assertIn("alice", ari)
        self.refused(lambda: self.Werewolf(ari), "Roster.__iter__")

    def test_contains_is_read_before_iter(self) -> None:
        class Odd(Bag):
            __iter__ = None                               # the parent's __contains__ still answers

        class Hushed(self.Party):
            __iter__ = None                               # Python: `in` is unavailable

        odd = Odd()

        self.refused(lambda: self.Werewolf(odd), "Bag.__contains__")
        self.assertIn("x", odd)

        hushed = Hushed()
        self.Werewolf(hushed)
        self.assertIn("Wolf", hushed)

    def test_a_published_operation_answers_in_too(self) -> None:
        class Keeper(Tag):
            @Public
            @Operation
            def __contains__(tag, agent, key) -> bool:
                return key == "alice"

        class Promised(Keeper):
            @Post
            def Fine(agent) -> bool:
                return True

        for keeper in (Keeper, Promised):
            ari = Agent()
            self.Werewolf(ari)

            self.refused(lambda: keeper(ari), "Keeper.__contains__", "Flag Werewolf")
            self.assertIn("Wolf", ari)

        bob = Agent()
        Keeper(bob)

        self.refused(lambda: self.Werewolf(bob), "Keeper.__contains__")

        class Den(Tag):
            @Public
            @Operation
            def __contains__(tag, agent, key) -> bool:
                return False

        with self.assertRaises(TagDeclarationError):
            Flag("Wolf")(Den)

    def test_a_flag_shape_over_a_base_that_answers_in(self) -> None:
        for answering, method in (
                (self.Roster, "Roster.__iter__"),
                (self.Gate, "Gate.__contains__"),
                ):
            @Flag("Alpha")
            class Alpha(answering):
                pass

            carrying, fresh = Agent(), Agent()
            answering(carrying)

            self.refused(lambda: Alpha(carrying), "Alpha", method)
            self.refused(lambda: Alpha(fresh), "Alpha", method)

            self.assertIn(carrying, answering)            # it keeps what it had
            self.assertIn(fresh, answering)               # its Base turn completed
            self.assertIn("alice", carrying)
            self.assertIn("alice", fresh)

    def test_a_later_collision_keeps_the_completed_base(self) -> None:
        log: list[str] = []

        @Flag
        class Wolfkin(Tag):
            @Imprint
            def Note(agent) -> None:
                log.append("Wolfkin")

        class Alpha(Wolfkin):
            def __iter__(agent):
                return iter(())

        ari = Agent()

        self.refused(lambda: Alpha(ari), "Alpha.__iter__", "Flag Wolfkin")

        self.assertEqual(log, ["Wolfkin"])
        self.assertIn(ari, Wolfkin)
        self.assertNotIn(ari, Alpha)
        self.assertIn("Wolfkin", ari)

    def test_a_form_may_free_the_seat_before_its_flag(self) -> None:
        class Ungate(self.Gate):
            @Delete
            def __contains__(agent): ...

        @Flag("Wolf")
        class Freed(Ungate):
            pass

        ari = Agent()
        Freed(ari)

        self.assertIn("Wolf", ari)

    def test_a_flag_given_an_in_method_later_is_refused_on_use(self) -> None:
        for method in ("__iter__", "__contains__"):
            @Flag("Beast")
            class Howler(Tag):
                pass

            setattr(Howler, method, lambda agent, *rest: iter(()))
            ari = Agent()

            self.refused(lambda: Howler(ari), f"Howler.{method}")
            self.assertNotIn(ari, Howler)

    def test_deleting_the_in_method_leaves_the_flag_its_words(self) -> None:
        class Ungate(Tag):
            @Delete
            def __contains__(agent): ...

            @Post
            def Fine(agent) -> bool:
                return True

        first, second = Agent(), Agent()
        self.Gate(first)
        Ungate(first)
        self.Werewolf(first)                              # the seat was freed
        self.Werewolf(second)
        Ungate(second)                                    # a later rebuild keeps the Flag's hook

        self.assertIn("Wolf", first)
        self.assertIn("Wolf", second)

    def test_a_pin_is_untouched(self) -> None:
        @Flag("Obsolete")
        class Deprecated(Pin):
            pass

        class Wizard(Tag):
            pass

        Deprecated(Wizard)

        self.assertIn("Obsolete", Wizard)
