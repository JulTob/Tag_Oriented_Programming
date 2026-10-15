"""A Tag's truth checks its own Posts; its populations keep their algebra."""

import unittest

from TopKit import (Contract, Pin, Post, Pre, Tag, TagContractError, TagContractWarning,
                    TagPostconditionError)


class Host:
    pass


class TagContractTruthTests(unittest.TestCase):
    def test_an_empty_tag_without_its_own_posts_is_true(self):
        class Agency(Tag):
            @Post
            def Ready(agent):
                return agent.ready

        # Agency's declaration promises something about its members, not
        # about Agency itself. A Pin would add Agency's own Posts.
        self.assertTrue(Agency)
        self.assertEqual(len(Agency), 0)
        self.assertEqual(len(Agency[:]), 0)
        self.assertEqual(len(~Agency), 0)
        self.assertFalse(Agency[:])
        self.assertFalse(~Agency)

    def test_truth_does_not_evaluate_members_posts(self):
        calls = []

        class Agency(Tag):
            @Post
            def Ready(agent):
                calls.append(agent)
                return agent.ready

        agent = Host()
        agent.ready = True
        Agency(agent)
        agent.ready = False
        calls.clear()

        self.assertTrue(Agency)
        self.assertEqual(calls, [])
        self.assertEqual(len(Agency), 0)
        self.assertNotEqual(calls, [])
        self.assertNotIn(agent, Agency)
        self.assertIn(agent, Agency[:])
        self.assertIn(agent, ~Agency)

    def test_own_truth_and_field_cardinalities_are_independent(self):
        class Agency(Tag):
            licensed = True

            @Post
            def Ready(agent):
                return agent.ready

        @Pin
        class Licensed(Tag):
            @Post
            def LicenseValid(tag):
                return tag.licensed

        Licensed(Agency)
        sound, deficient = Host(), Host()
        sound.ready = deficient.ready = True
        Agency(sound)
        Agency(deficient)
        deficient.ready = False

        for licensed in (True, False):
            with self.subTest(licensed=licensed):
                Agency.licensed = licensed
                self.assertIs(bool(Agency), licensed)
                self.assertEqual(list(Agency), [sound])
                self.assertEqual(list(~Agency), [deficient])
                self.assertEqual(list(Agency[:]), [sound, deficient])
                self.assertEqual(len(Agency), 1)
                self.assertEqual(len(~Agency), 1)
                self.assertEqual(len(Agency[:]), 2)
                self.assertEqual(list(Agency | ~Agency), [sound, deficient])
                self.assertEqual(list(Agency & Agency[:]), [sound])
                self.assertEqual(list(Agency[:] - Agency), [deficient])
                self.assertTrue(Agency | ~Agency)
                self.assertEqual(len(Agency & ~Agency), 0)
                self.assertFalse(Agency & ~Agency)

        # The Pin's Field filters Agency by Agency's contract; Agency's own
        # Field still filters its individual members by their contracts.
        self.assertNotIn(Agency, Licensed)
        self.assertIn(Agency, Licensed[:])
        self.assertEqual(list(Licensed), [])
        self.assertEqual(list(~Licensed), [Agency])
        self.assertTrue(Licensed)

    def test_pin_posts_survive_rip_until_explicitly_deleted(self):
        class Agency(Tag):
            ready = True

        @Pin
        class Certified(Tag):
            @Post
            def Ready(tag):
                return tag.ready

        Certified(Agency)
        del Certified[Agency]
        Agency.ready = False
        self.assertNotIn(Agency, Certified)
        self.assertFalse(Agency)
        with self.assertRaises(TagPostconditionError.Ready):
            Contract.Postconditions(Agency)

        Contract.Delete(Agency, "Ready")
        self.assertTrue(Agency)
        self.assertEqual(Contract.Status(Agency), {})
        self.assertEqual(len(Agency), 0)

    def test_only_the_visible_pin_post_controls_truth(self):
        class Agency(Tag):
            ready = True

        @Pin
        class Original(Tag):
            @Post
            def Ready(tag):
                return tag.ready

        @Pin
        class Replacement(Tag):
            @Post
            def Ready(tag):
                return True

        Original(Agency)
        Agency.ready = False
        self.assertFalse(Agency)
        with self.assertWarns(TagContractWarning):
            Replacement(Agency)
        self.assertTrue(Agency)
        self.assertEqual(Contract.Status(Agency), {"Ready": True})

    def test_a_failed_pin_post_leaves_a_false_tag_in_the_pin_field(self):
        class Agency(Tag):
            ready = False

        @Pin
        class Certified(Tag):
            @Post
            def Ready(tag):
                return tag.ready

        with self.assertRaises(TagPostconditionError.Ready):
            Certified(Agency)
        self.assertFalse(Agency)
        self.assertNotIn(Agency, Certified)
        self.assertIn(Agency, Certified[:])
        self.assertIn(Agency, ~Certified)
        Agency.ready = True
        self.assertTrue(Agency)
        self.assertEqual(list(Certified), [Agency])

    def test_post_exceptions_and_non_boolean_verdicts_fail_then_recover(self):
        class Agency(Tag):
            verdict = True

        @Pin
        class Certified(Tag):
            @Post
            def Ready(tag):
                if isinstance(tag.verdict, Exception):
                    raise tag.verdict
                return tag.verdict

        Certified(Agency)
        for verdict in (ValueError("unavailable"), 1):
            with self.subTest(verdict=verdict):
                Agency.verdict = verdict
                self.assertFalse(Agency)
                Agency.verdict = True
                self.assertTrue(Agency)

        # Existing assertion-style Posts return None when their checks pass.
        Agency.verdict = None
        self.assertTrue(Agency)

    def test_a_pinned_tags_post_cannot_certify_its_own_truth(self):
        class Agency(Tag):
            ready = True

        @Pin
        class Reflective(Tag):
            @Post
            def Ready(tag):
                return bool(tag) and tag.ready

        with self.assertRaisesRegex(TagContractError, "Ready.*Tag\\[:\\]"):
            Reflective(Agency)
        with self.assertRaisesRegex(TagContractError, "Tag\\[:\\]"):
            bool(Agency)

    def test_a_pin_precondition_does_not_become_tag_truth(self):
        class Agency(Tag):
            ready = True

        @Pin
        class Admitted(Tag):
            @Pre
            def Ready(tag):
                return tag.ready

        Admitted(Agency)
        Agency.ready = False
        self.assertIs(Agency.Ready, False)
        self.assertTrue(Agency)

    def test_a_shapes_truth_does_not_inherit_the_bases_pin_contract(self):
        class Base(Tag):
            ready = True

        @Pin
        class Certified(Tag):
            @Post
            def Ready(tag):
                return tag.ready

        Certified(Base)

        class Shape(Base):
            pass

        Base.ready = False
        self.assertFalse(Base)
        self.assertTrue(Shape)
        self.assertNotIn(Shape, Certified)


if __name__ == "__main__":
    unittest.main()
