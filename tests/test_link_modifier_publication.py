"""Public Pair projections preserve the Constant Gain they expose."""

import unittest

from TopKit import (Action, Constant, Link, Public, Record, Report, Tag,
                    TagCompositionError, TagResolutionError, TagRogueAccessError, agent, contact)


class Host:
    pass


class LinkModifierPublicationTests(unittest.TestCase):
    def test_public_link_reports_work_in_both_decorator_orders(self):
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Public
                @Report
                def empty(link):
                    return None

                @Report
                @Public
                def disabled(link):
                    return False

        hero, sword = Host(), Host()
        Inventory(hero)
        hero.Carries(sword)
        self.assertTrue("empty" @ sword)
        self.assertTrue("disabled" @ sword)
        self.assertIsNone(sword.empty)
        self.assertIs(sword.disabled, False)
        hero.Carries.empty = "current"
        self.assertEqual(sword.empty, "current")
        with self.assertRaises(AttributeError):
            sword.empty = "cannot write a Tag Report here"
        del hero.Carries[sword]
        self.assertFalse("empty" @ sword)
        self.assertFalse("disabled" @ sword)
        with self.assertRaises(TagRogueAccessError):
            _ = sword.empty

    def test_a_later_tag_view_reads_the_current_public_pair_record(self):
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Public
                @Record
                def position(owner, target, *, position="pack"):
                    return position

        class Inspected(Tag):
            pass

        hero, sword = Host(), Host()
        Inventory(hero)
        hero.Carries(sword)
        Inspected(sword)
        view = Inspected[sword]
        self.assertEqual(view.position, "pack")
        hero.Carries[sword].position = "hand"
        self.assertEqual(view.position, "hand")
        del hero.Carries[sword]
        with self.assertRaises(TagResolutionError):
            _ = view.position
        hero.Carries(sword, position="belt")
        self.assertEqual(view.position, "belt")

    def test_constant_public_action_binding_is_protected_on_contact(self):
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Constant
                @Public
                @Action
                def Identify(owner, target):
                    return "carried"

        hero, sword = Host(), Host()
        Inventory(hero)
        hero.Carries(sword)
        call = sword.Identify
        self.assertEqual(call(), "carried")
        with self.assertRaises(TagCompositionError):
            del sword.Identify
        with self.assertRaises(TagCompositionError):
            sword.Identify = lambda: "replacement"

        class Replace(Tag):
            @Action
            def Identify(target):
                return "replacement"

        with self.assertRaises(TagCompositionError):
            Replace(sword)
        del hero.Carries[sword]
        self.assertNotIn(sword, hero.Carries[:])
        with self.assertRaises(TagRogueAccessError):
            call()
        hero.Carries(sword)
        self.assertEqual(call(), "carried")

    def test_constant_public_record_projection_cannot_be_crushed(self):
        values = []

        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Public
                @Constant
                @Record
                def code(owner, target):
                    values.append("application")
                    return len(values)

        class Replace(Tag):
            @Record
            def code(target):
                return "replacement"

        hero, sword = Host(), Host()
        Inventory(hero)
        hero.Carries(sword)
        view = hero.Carries[sword]
        self.assertEqual(sword.code, 1)
        with self.assertRaises(TagCompositionError):
            Replace(sword)
        with self.assertRaises(TagCompositionError):
            del view.code
        del hero.Carries[sword]
        self.assertFalse("code" @ sword)
        with self.assertRaises(TagRogueAccessError):
            _ = sword.code
        hero.Carries(sword)
        self.assertEqual(view.code, 2)
        self.assertEqual(sword.code, 2)


if __name__ == "__main__":
    unittest.main()
