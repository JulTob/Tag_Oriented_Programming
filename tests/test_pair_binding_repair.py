"""A Pair view reads physical Gains restored by existing repair Actions."""

import unittest
import warnings

from TopKit import (Action, Link, Post, Record, Report, Secret, Tag,
                    TagPostconditionError, TrainingWarning, agent, contact)


class Host:
    pass


class PairBindingRepairTests(unittest.TestCase):
    def test_existing_action_repairs_a_failed_record_initializer(self):
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Record
                def position(owner, target):
                    raise ValueError("the initial position is unavailable")

                @Post
                def Stored(owner, target):
                    view = owner.Carries[target]
                    return "position" @ view and view.position == "belt"

                @Action
                def Repair(owner, target):
                    owner.Carries[target].position = "belt"

        hero, sword = Host(), Host()
        Inventory(hero)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", TrainingWarning)
            with self.assertRaises(TagPostconditionError.Stored):
                hero.Carries(sword)
        self.assertEqual([item.message.name for item in caught], ["position"])
        view = hero.Carries[sword]
        self.assertNotIn(sword, hero.Carries)
        self.assertIn(sword, ~hero.Carries)
        self.assertFalse("position" @ view)
        view.Repair()
        self.assertTrue("position" @ view)
        self.assertEqual(view.position, "belt")
        self.assertIn(sword, hero.Carries)

    def test_a_deleted_record_can_be_rebound_to_a_false_value(self):
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Record
                def position(owner, target):
                    return "pack"

                @Post
                def Has_Position(owner, target):
                    return "position" @ owner.Carries[target]

                @Action
                def Repair(owner, target, position):
                    owner.Carries[target].position = position

        hero, sword = Host(), Host()
        Inventory(hero)
        hero.Carries(sword)
        view = hero.Carries[sword]
        for value in (None, False):
            del view.position
            self.assertFalse("position" @ view)
            self.assertNotIn(sword, hero.Carries)
            view.Repair(value)
            self.assertTrue("position" @ view)
            self.assertIs(view.position, value)
            self.assertIn(sword, hero.Carries)

    def test_physical_pair_gain_keeps_report_and_secret_boundaries(self):
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Report
                def capacity(link):
                    return 20

                @Secret
                @Record
                def code(owner, target):
                    return "private"

                @Action
                def Repair(owner, target, value):
                    owner.Carries[target].note = value

        hero, sword = Host(), Host()
        Inventory(hero)
        hero.Carries(sword)
        view = hero.Carries[sword]
        for value in (None, False):
            view.Repair(value)
            self.assertIs(view.note, value)
            self.assertEqual(view.capacity, 20)
            self.assertEqual(hero.Carries.capacity, 20)
            self.assertFalse("code" @ view)
            with self.assertRaises(AttributeError):
                _ = view.code


if __name__ == "__main__":
    unittest.main()
