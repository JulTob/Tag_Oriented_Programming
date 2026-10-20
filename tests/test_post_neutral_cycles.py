"""A recursive Post reads its own unfinished verdict as neutral True."""

import unittest

from TopKit import Contract, Post, Tag, TagCompositionError, Underlay
from TopKit import TagPostconditionError


class Host:
    pass


class PostNeutralCycleTests(unittest.TestCase):
    def test_positive_self_queries_hold_across_truth_membership_status_and_name(self):
        for query in (
                lambda agent, tag: bool(agent),
                lambda agent, tag: Contract.Postconditions(agent),
                lambda agent, tag: Contract.Conditions(agent),
                lambda agent, tag: Contract.Status(agent)["Ready"],
                lambda agent, tag: agent.Ready,
                lambda agent, tag: agent in tag,
                ):
            with self.subTest(query=query):
                class Reading(Tag):
                    @Post
                    def Ready(agent):
                        return query(agent, Reading)

                agent = Host()
                Reading(agent)
                self.assertIn(agent, Reading[:])
                self.assertIn(agent, Reading)
                self.assertTrue(agent.Ready)
                self.assertTrue(bool(agent))

    def test_negating_own_truth_yields_false_and_keeps_field_admission(self):
        class Reading(Tag):
            @Post
            def Ready(agent):
                return not bool(agent)

        agent = Host()
        with self.assertRaises(TagPostconditionError.Ready):
            Reading(agent)

        self.assertIn(agent, Reading[:])
        self.assertFalse(agent.Ready)
        self.assertFalse(bool(agent))
        self.assertEqual(Contract.Status(agent), {"Ready": False})

    def test_recursion_does_not_hide_an_unrelated_failed_post(self):
        class Reading(Tag):
            @Post
            def Ready(agent):
                return bool(agent)

            @Post
            def Safe(agent):
                return agent.safe

        agent = Host()
        agent.safe = True
        Reading(agent)
        agent.safe = False

        self.assertFalse(agent.Ready)
        self.assertFalse(bool(agent))
        self.assertEqual(Contract.Status(agent), {"Ready": False, "Safe": False})

    def test_named_post_cycles_are_neutral_and_acyclic_reads_still_follow_state(self):
        class Mutual(Tag):
            @Post
            def Ready(agent):
                return agent.Safe

            @Post
            def Safe(agent):
                return agent.Ready

        first = Host()
        Mutual(first)
        self.assertTrue(first.Ready)
        self.assertEqual(Contract.Status(first), {"Ready": True, "Safe": True})

        class Acyclic(Tag):
            @Post
            def Ready(agent):
                return agent.Safe

            @Post
            def Safe(agent):
                return agent.safe

        second = Host()
        second.safe = True
        Acyclic(second)
        self.assertTrue(second.Ready)
        second.safe = False
        self.assertFalse(second.Ready)

    def test_lower_underlay_post_can_read_the_visible_upper_post(self):
        class Base(Tag):
            @Post
            def Ready(agent):
                return agent.Ready

        class Shape(Tag):
            @Underlay
            @Post
            def Ready(agent, lower):
                return lower() and agent.safe

        agent = Host()
        agent.safe = True
        Base(agent)
        Shape(agent)
        self.assertTrue(agent.Ready)
        agent.safe = False
        self.assertFalse(agent.Ready)

    def test_a_caught_top_change_still_fails_a_recursive_post(self):
        seen = []
        calls = [0]

        class Checked(Tag):
            @Post
            def Observer(agent):
                seen.append((bool(agent), bool(agent)))
                return True

            @Post
            def Guard(agent):
                calls[0] += 1
                try:
                    del Checked[agent]
                except TagCompositionError:
                    pass
                return True

        with self.assertRaises(TagPostconditionError.Observer):
            Checked(Host())

        self.assertEqual(seen, [(False, False)])
        self.assertEqual(calls[0], 2)


if __name__ == "__main__":
    unittest.main()
