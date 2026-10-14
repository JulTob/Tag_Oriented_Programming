"""Conformance tests: kernel."""

from __future__ import annotations

import gc
import unittest
import weakref
from TopKit import Form
from TopKit import Tag
from TopKit import TagCompositionError
from TopKit import Tags

from ._fixtures import Agent
from ._fixtures import Arithmetic
from ._fixtures import Bridge
from ._fixtures import Elf
from ._fixtures import Field_Member
from ._fixtures import Knighted
from ._fixtures import Left
from ._fixtures import Paladin
from ._fixtures import Person
from ._fixtures import Right
from ._fixtures import Root
from ._fixtures import Slotted_Agent
from ._fixtures import Squire
from ._fixtures import Stocked


class KernelTests(unittest.TestCase):
    def test_tagging_preserves_identity_and_builds_base_membership(self) -> None:
        ari = Agent()
        returned = Elf(ari)

        self.assertIs(returned, ari)
        self.assertIn(ari, Elf)
        self.assertIn(ari, Person)
        self.assertIsInstance(ari, Elf)
        self.assertIsInstance(ari, Person)

    def test_runtime_type_keeps_the_host_name(self) -> None:
        ari = Agent()

        Elf(ari)

        self.assertEqual(type(ari).__name__, "Agent")
        self.assertIsInstance(ari, Agent)

    def test_direct_bases_apply_in_declaration_order_and_diamond_once(self) -> None:
        ari = Agent()

        Bridge(ari)

        self.assertEqual(ari.events, ["Root", "Left", "Right", "Bridge"])
        self.assertIn(ari, Root)
        self.assertIn(ari, Left)
        self.assertIn(ari, Right)
        self.assertEqual(Form(Bridge), (Root, Left, Right, Bridge))

    def test_active_reapply_is_a_strict_noop(self) -> None:
        ari = Agent()

        Stocked(ari)
        ari.supplies.append("torch")
        ari.events.append("between")
        Stocked(ari)

        self.assertEqual(ari.supplies, ["ration", "torch"])
        self.assertEqual(ari.events, ["Stocked", "between"])
        self.assertEqual(list(Stocked[:]).count(ari), 1)

    def test_fields_are_non_owning_and_iterable_from_the_tag(self) -> None:
        ari = Agent()
        Field_Member(ari)
        reference = weakref.ref(ari)

        self.assertEqual(list(Field_Member[:]), [ari])
        self.assertEqual(list(Field_Member), [ari])
        self.assertEqual(len(Field_Member[:]), 1)
        self.assertEqual(len(Field_Member), 1)
        self.assertGreater(len(Field_Member), 0)
        self.assertTrue(Field_Member[:])
        self.assertFalse(~Field_Member)

        del ari
        gc.collect()

        self.assertIsNone(reference())
        self.assertEqual(list(Field_Member[:]), [])
        self.assertEqual(len(Field_Member), 0)
        self.assertFalse(Field_Member[:])

    def test_fields_index_by_identity_not_equality(self) -> None:
        class Twin:
            def __eq__(self, other) -> bool:
                return True

            def __hash__(self) -> int:
                return 1

        one = Twin()
        two = Twin()

        Field_Member(one)
        Field_Member(two)

        self.assertEqual(len(Field_Member[:]), 2)

        del Field_Member[one]

        self.assertEqual(list(Field_Member[:]), [two])

    def test_a_field_offers_no_public_way_around_tagging_and_rip(self) -> None:
        class Membership(Tag):
            pass

        agent = Agent()
        field = Membership[:]

        self.assertFalse(hasattr(field, "Add"))
        self.assertFalse(hasattr(field, "Remove"))

        Membership(agent)

        self.assertIn(agent, Membership)
        self.assertIn(agent, field)

        del Membership[agent]

        self.assertNotIn(agent, Membership)
        self.assertNotIn(agent, field)

    def test_targets_that_cannot_carry_top_state_fail_explicitly(self) -> None:
        target = Slotted_Agent()

        with self.assertRaises(TagCompositionError):
            Person(target)

    def test_membership_queries_do_not_actualize_an_untagged_target(self) -> None:
        ari = Agent()

        self.assertNotIn(ari, Person)
        self.assertFalse(hasattr(ari, "_TOPKIT_STATE"))
        self.assertEqual(Tags(ari), ())

    def test_a_tag_needs_a_target(self) -> None:
        with self.assertRaises(TypeError):
            Person()

        with self.assertRaises(TypeError):
            Person(Agent)

    def test_isinstance_is_a_reliable_has_been_check(self) -> None:
        ari = Agent()

        Squire(ari)
        self.assertIsInstance(ari, Squire)

        del Squire[ari]
        self.assertNotIn(ari, Squire)
        self.assertIsInstance(ari, Squire)

        Knighted(ari)
        self.assertIsInstance(ari, Squire)
        self.assertIsInstance(ari, Knighted)

    def test_runtime_types_are_shared_across_agents_and_shapes(self) -> None:
        ari = Agent()
        bea = Agent()

        Elf(ari)
        Paladin(bea)

        # The runtime type is neutral: it does not depend on which Tags are
        # active, only on what the host needs at type level.
        self.assertIs(type(ari), type(bea))

    def test_special_method_actions_actualize_the_agent(self) -> None:
        ari = Agent()
        bea = Agent()

        Arithmetic(ari)
        Arithmetic(bea)

        self.assertEqual(ari + 4, 5)
        self.assertEqual(bea + 1, 2)
