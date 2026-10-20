"""Recursive Post validity reads use a neutral True at the cycle edge."""

from contextvars import copy_context
import gc
import unittest
from weakref import ref

from TopKit import Contract, Post, Pre, Tag
from TopKit import TagPostconditionError, TagPreconditionError


class Host:
    pass


class PostPopulationRecursionTests(unittest.TestCase):
    def test_same_agent_sound_membership_uses_a_neutral_cycle_edge(self):
        class Existing(Tag):
            pass

        class Checking(Tag):
            @Post
            def Standing(agent):
                return agent in Existing

        agent = Host()
        Existing(agent)

        Checking(agent)

        self.assertIn(agent, Existing[:])
        self.assertIn(agent, Checking[:])
        self.assertTrue(agent.Standing)
        self.assertEqual(Contract.Status(agent), {"Standing": True})

    def test_all_sound_population_spellings_use_neutral_cycle_edges(self):
        class Existing(Tag):
            pass

        queries = (
                lambda agent: agent in Existing,
                lambda agent: agent in ~Existing,
                lambda agent: list(Existing),
                lambda agent: len(Existing),
                lambda agent: agent in Existing | Existing[:],
                )

        for query in queries:
            with self.subTest(query=query):
                class Checking(Tag):
                    @Post
                    def Standing(agent):
                        query(agent)
                        return True

                agent = Host()
                Existing(agent)

                Checking(agent)
                self.assertTrue(agent.Standing)

    def test_raw_field_and_other_agents_soundness_can_be_read_from_a_post(self):
        class Existing(Tag):
            @Post
            def Ready(agent):
                return agent.ready

        other = Host()
        other.ready = True
        Existing(other)

        class Checking(Tag):
            @Post
            def Standing(agent):
                return agent in Checking[:] and other in Existing

        agent = Host()
        Checking(agent)
        self.assertTrue(agent.Standing)

    def test_indirect_post_pre_soundness_cycle_uses_neutral_true(self):
        class Base(Tag):
            pass

        class Checking(Tag):
            @Pre
            def Existing(agent):
                return agent in Base

        class Witness(Tag):
            @Post
            def Guard(agent):
                return Contract.Preconditions(agent)

        agent = Host()
        Base(agent)
        Checking(agent)

        Witness(agent)

        self.assertIn(agent, Witness[:])
        self.assertTrue(agent.Guard)
        self.assertIn(agent, Base)

    def test_named_pre_queries_existing_posts_without_the_post_cycle_guard(self):
        class Existing(Tag):
            @Post
            def Ready(agent):
                return agent.ready

        class Checking(Tag):
            @Pre
            def Standing(agent):
                return agent in Existing

        agent = Host()
        agent.ready = True
        Existing(agent)
        Checking(agent)

        agent.ready = False
        self.assertFalse(agent.Standing)
        with self.assertRaises(TagPreconditionError.Standing):
            Contract.Preconditions(agent)
        self.assertIs(Contract.Status(agent)["Standing"], False)

        refused = Host()
        refused.ready = False
        with self.assertRaises(TagPostconditionError.Ready):
            Existing(refused)
        with self.assertRaises(TagPreconditionError.Standing):
            Checking(refused)

    def test_post_can_ask_whether_a_stored_precondition_still_holds(self):
        class Existing(Tag):
            @Pre
            def Allowed(agent):
                return agent.allowed

        class Checking(Tag):
            @Post
            def PreStillHolds(agent):
                try:
                    Contract.Preconditions(agent)
                except TagPreconditionError.Allowed:
                    return False
                return True

        agent = Host()
        agent.allowed = True
        Existing(agent)
        Checking(agent)
        agent.allowed = False

        self.assertIn(agent, Checking[:])
        self.assertFalse(agent.PreStillHolds)
        self.assertFalse(bool(agent))
        self.assertNotIn(agent, Checking)
        self.assertIn(agent, ~Checking)
        with self.assertRaises(TagPostconditionError.PreStillHolds):
            Contract.Postconditions(agent)

        refused = Host()
        refused.allowed = True
        Existing(refused)
        refused.allowed = False
        with self.assertRaises(TagPostconditionError.PreStillHolds):
            Checking(refused)

    def test_bool_inside_its_own_post_keeps_the_existing_shortcut(self):
        class Checking(Tag):
            @Post
            def Standing(agent):
                return bool(agent) and agent.ready

        agent = Host()
        agent.ready = True
        Checking(agent)
        self.assertTrue(agent)

        agent.ready = False
        self.assertFalse(agent)
        with self.assertRaises(TagPostconditionError.Standing):
            Contract.Postconditions(agent)

    def test_copied_post_context_does_not_keep_the_agent_alive(self):
        contexts = []

        class Checking(Tag):
            @Post
            def Ready(agent):
                contexts.append(copy_context())
                return True

        agent = Host()
        reference = ref(agent)
        Checking(agent)
        self.assertTrue(contexts)

        del agent
        gc.collect()
        self.assertIsNone(reference())
