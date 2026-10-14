"""Conformance tests: host preservation."""

from __future__ import annotations

import copy
import unittest
from TopKit import Post
from TopKit import Tag
from TopKit import TagCompositionError

from ._fixtures import Agent
from ._fixtures import Bag
from ._fixtures import Community
from ._fixtures import Field_Member
from ._fixtures import Squire


class HostPreservationTests(unittest.TestCase):
    """Tagging must not change what the host object already does."""

    Bag = Bag

    def test_host_special_methods_survive_tagging(self) -> None:
        bag = self.Bag()

        Field_Member(bag)

        self.assertIn("x", bag)
        self.assertNotIn(Field_Member, bag)       # the host keeps its `in`
        self.assertEqual(bag | 1, "host-or")
        self.assertEqual(len(bag), 1)             # and its `len`
        self.assertTrue(bool(bag))

        bag.items.clear()

        self.assertEqual(len(bag), 0)
        self.assertTrue(bool(bag))                # its truth is its contract, not its length
        self.assertEqual(bag.dynamic, "from host getattr")

    def test_an_agents_truth_is_its_contract_while_len_stays_the_hosts(self) -> None:
        class Shelf:
            def __init__(self) -> None:
                self.books: list[str] = []
                self.catalogued = True

            def __len__(self) -> int:
                return len(self.books)

        class Library(Tag):
            pass

        class Catalogue(Tag):
            @Post
            def Catalogued(agent) -> bool:
                return agent.catalogued

        shelf = Shelf()
        Library(shelf)

        self.assertEqual(len(shelf), 0)
        self.assertTrue(shelf)                    # no promise: nothing is broken

        Catalogue(shelf)
        shelf.books.append("Dune")
        shelf.catalogued = False

        self.assertEqual(len(shelf), 1)
        self.assertFalse(shelf)                   # broken, whatever its length

        shelf.books.clear()
        shelf.catalogued = True

        self.assertEqual(len(shelf), 0)
        self.assertTrue(shelf)                    # sound, whatever its length

    def test_an_untagged_object_from_an_agents_type_keeps_host_truth(self) -> None:
        bag = self.Bag()
        Field_Member(bag)
        spare = type(bag)()

        self.assertTrue(spare)
        spare.items.clear()
        self.assertFalse(spare)

        class Host:
            pass

        class Sized(Tag):
            def __len__(agent) -> int:
                raise AssertionError("TOP behaviour leaked into a plain host")

        tagged = Host()
        Sized(tagged)

        self.assertTrue(type(tagged)())            # ignores the Tag's __len__

    def test_plain_runtime_truth_binds_a_non_descriptor_len_as_python_does(self) -> None:
        class Length:
            def __call__(self) -> int:
                return 0

        class Host:
            __len__ = Length()

        host = Host()
        Field_Member(host)

        self.assertFalse(type(host)())

    def test_plain_runtime_truth_skips_every_synthesized_layer(self) -> None:
        class Host:
            pass

        class Sized(Tag):
            def __len__(agent) -> int:
                raise AssertionError("an older TOP layer leaked")

        first = Host()
        Sized(first)

        class Derived(type(first)):
            pass

        second = Derived()
        Field_Member(second)

        self.assertTrue(type(second)())

    def test_tag_members_do_not_leak_onto_the_agent(self) -> None:
        ari = Agent()

        Community(ari)

        self.assertFalse(hasattr(ari, "colour"))
        self.assertFalse(hasattr(ari, "Greet"))
        self.assertFalse(hasattr(ari, "Form"))
        self.assertFalse(hasattr(ari, "Field"))
        self.assertEqual(Community.colour, "green")
        self.assertEqual(Community.Greet("Ari"), "Community:Ari")

    def test_copying_an_agent_is_refused_explicitly(self) -> None:
        ari = Agent()

        Squire(ari)

        with self.assertRaises(TagCompositionError):
            copy.copy(ari)

        with self.assertRaises(TagCompositionError):
            copy.deepcopy(ari)
