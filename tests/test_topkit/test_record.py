"""Conformance tests: record."""

from __future__ import annotations

import unittest
import warnings
from TopKit import Record
from TopKit import Tag
from TopKit import TagCompositionError
from TopKit import TagOverwriteWarning
from TopKit import Underlay
from TopKit import TrainingWarning

from ._fixtures import Agent
from ._fixtures import Armed
from ._fixtures import Cursed_Blade
from ._fixtures import Inventory
from ._fixtures import Lost_Inventory
from ._fixtures import Prepared
from ._fixtures import Rebuilt_Inventory


class RecordTests(unittest.TestCase):
    def test_records_are_fresh_per_agent_and_extend_the_stored_value(self) -> None:
        ari = Agent()
        bea = Agent()

        Prepared(ari)
        Inventory(bea)

        self.assertEqual(ari.items, ["rope"])
        self.assertEqual(bea.items, [])
        self.assertIsNot(ari.items, bea.items)

    def test_independent_tags_pile_up_on_one_record(self) -> None:
        class Elf_Spells(Tag):
            @Record
            def spells(agent, stored):
                return (stored or []) + ["Light"]

        class Wizard_Spells(Tag):
            @Record
            def spells(agent, stored):
                return (stored or []) + ["Fireball"]

        class Sage_Spells(Tag):
            @Record
            @Underlay
            def spells(agent, stored):
                return (stored or []) + ["Identify"]

        ari = Agent()

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            Elf_Spells(ari)
            Wizard_Spells(ari)
            Sage_Spells(ari)

        self.assertEqual(ari.spells, ["Light", "Fireball", "Identify"])
        self.assertEqual(ari.Elf_Spells.spells, ["Light"])

    def test_a_record_can_replace_an_existing_object_attribute(self) -> None:
        ari = Agent()

        Armed(ari)

        self.assertEqual(ari.weapon, "arcane staff")

    def test_a_record_can_extend_an_existing_object_attribute(self) -> None:
        class Sharpened(Tag):
            @Record
            def weapon(agent, stored):
                return "sharpened " + stored

        ari = Agent()

        Sharpened(ari)

        self.assertEqual(ari.weapon, "sharpened faulty weapon")

    def test_independent_record_replacement_without_stored_warns(self) -> None:
        ari = Agent()

        Armed(ari)

        with self.assertWarns(TagOverwriteWarning):
            Cursed_Blade(ari)

        self.assertEqual(ari.weapon, "cursed dagger")

    def test_deleted_record_has_no_stored_value_and_a_shape_can_rebuild_it(self) -> None:
        ari = Agent()

        Lost_Inventory(ari)

        self.assertFalse(hasattr(ari, "items"))

        Rebuilt_Inventory(ari)

        self.assertEqual(ari.items, ["shield"])

    def test_del_removes_a_record_the_native_way(self) -> None:
        ari = Agent()

        Armed(ari)
        del ari.weapon

        self.assertFalse(hasattr(ari, "weapon"))

    def test_record_over_a_host_property_is_refused_and_rolled_back(self) -> None:
        class Prop:
            @property
            def hp(self) -> int:
                return 1

        class Vital(Tag):
            @Record
            def hp(agent) -> int:
                return 99

        target = Prop()

        with self.assertRaises(TagCompositionError):
            Vital(target)

        self.assertNotIn(target, Vital)
        self.assertEqual(target.hp, 1)

    def test_record_builder_failure_warns_by_name_and_leaves_value_absent(self) -> None:
        class Bad(Tag):
            @Record
            def hp(agent):
                return 1 + "x"

        ari = Agent()

        with self.assertWarns(TrainingWarning.hp) as caught:
            Bad(ari)

        self.assertIn("Bad.hp", str(caught.warning))
        self.assertIn(ari, Bad)
        self.assertFalse("hp" @ ari)

    def test_independent_tags_cannot_share_a_name_across_kinds(self) -> None:
        class Data(Tag):
            @Record
            def strike(agent) -> int:
                return 4

        class Behaviour(Tag):
            def strike(agent) -> int:
                return 1

        ari = Agent()
        Data(ari)

        with self.assertRaises(TagCompositionError):
            Behaviour(ari)

        self.assertEqual(ari.strike, 4)

    def test_a_shape_may_turn_a_base_action_into_a_record(self) -> None:
        class Combatant_(Tag):
            def strike(agent) -> int:
                return 1

        class Fire(Combatant_):
            @Record
            def strike(agent) -> int:
                return 4

        ari = Agent()
        Fire(ari)

        self.assertEqual(ari.strike, 4)
        self.assertEqual(ari.Combatant_.strike(), 1)
