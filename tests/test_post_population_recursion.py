"""Population queries share neutral recursive Post edges."""

from contextvars import copy_context
import gc
import unittest
from weakref import ref

from TopKit import Contract, Post, Pre, Tag
from TopKit import TagContractError, TagPostconditionError, TagPreconditionError
from TopKit import TagCompositionError


class Host:
    pass


class PostPopulationRecursionTests(unittest.TestCase):
    def test_same_agent_sound_membership_uses_a_neutral_recursive_edge(self):
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

    def test_sound_population_spellings_allow_the_same_post_cycle(self):
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
                self.assertTrue(bool(agent))
                del Existing[agent]

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

    def test_pre_soundness_query_exists_only_during_its_gate(self):
        class Base(Tag):
            pass

        class Checking(Tag):
            @Pre
            def Existing(agent):
                return agent in Base

        agent = Host()
        Base(agent)
        Checking(agent)

        self.assertFalse(hasattr(agent, "Existing"))
        self.assertEqual(Contract.Status(agent), {})
        self.assertTrue(agent in Base)

    def test_pre_can_query_existing_posts_at_the_gate_but_is_not_retained(self):
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
        self.assertFalse(hasattr(agent, "Standing"))
        self.assertEqual(Contract.Status(agent), {"Ready": False})

        refused = Host()
        refused.ready = False
        with self.assertRaises(TagPostconditionError.Ready):
            Existing(refused)
        with self.assertRaises(TagCompositionError):
            Checking(refused)

    def test_a_continuing_responsibility_must_be_written_as_a_post(self):
        class Existing(Tag):
            @Pre
            def Allowed(agent):
                return agent.allowed

        class Checking(Tag):
            @Post
            def AllowedStillHolds(agent):
                return agent.allowed

        agent = Host()
        agent.allowed = True
        Existing(agent)
        Checking(agent)
        agent.allowed = False

        self.assertIn(agent, Checking[:])
        self.assertFalse(hasattr(agent, "Allowed"))
        self.assertFalse(agent.AllowedStillHolds)
        self.assertFalse(bool(agent))
        self.assertNotIn(agent, Checking)
        self.assertIn(agent, ~Checking)
        with self.assertRaises(TagPostconditionError.AllowedStillHolds):
            Contract.Postconditions(agent)

        refused = Host()
        refused.allowed = True
        Existing(refused)
        refused.allowed = False
        with self.assertRaises(TagPostconditionError.AllowedStillHolds):
            Checking(refused)

    def test_bool_inside_its_own_post_uses_neutrality_then_checks_its_data(self):
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
