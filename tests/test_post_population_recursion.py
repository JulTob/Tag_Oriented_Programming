"""A Post cannot use a sound population to judge its own Agent."""

from contextvars import copy_context
import gc
import unittest
from weakref import ref

from TopKit import Contract, Link, Post, Pre, Tag
from TopKit import TagContractError, TagPostconditionError, TagPreconditionError


class Host:
    pass


class PostPopulationRecursionTests(unittest.TestCase):
    def test_link_membership_checks_the_pairs_post_like_its_walk(self):
        class Circle(Tag):
            @Link
            class Knows(Tag):
                @Post
                def PairReady(owner, contact):
                    return contact.ready

        owner, contact = Host(), Host()
        contact.ready = True
        Circle(owner)
        owner.Knows(contact)
        self.assertIn(contact, owner.Knows)

        contact.ready = False
        self.assertIn(contact, owner.Knows[:])
        self.assertNotIn(contact, owner.Knows)
        self.assertEqual(list(owner.Knows), [])
        self.assertIn(contact, ~owner.Knows)

    def test_a_links_pair_post_cannot_ask_its_own_sound_membership(self):
        class Circle(Tag):
            @Link
            class Knows(Tag):
                @Post
                def PairSound(owner, contact):
                    return contact in owner.Knows

        owner, contact = Host(), Host()
        Circle(owner)

        with self.assertRaisesRegex(TagContractError, "PairSound.*Tag\\[:\\]"):
            owner.Knows(contact)
        self.assertIn(contact, owner.Knows[:])
        with self.assertRaises(TagContractError):
            _ = contact in owner.Knows

    def test_a_contacts_post_cannot_ask_its_own_link_soundness(self):
        class Circle(Tag):
            @Link
            class Knows(Tag):
                pass

        owner, contact = Host(), Host()
        Circle(owner)
        owner.Knows(contact)

        class Checking(Tag):
            @Post
            def ContactSound(agent):
                return agent in owner.Knows

        with self.assertRaisesRegex(TagContractError, "ContactSound.*Tag\\[:\\]"):
            Checking(contact)
        self.assertIn(contact, owner.Knows[:])

    def test_same_agent_sound_membership_fails_during_post_and_named_reads(self):
        class Existing(Tag):
            pass

        class Checking(Tag):
            @Post
            def Standing(agent):
                return agent in Existing

        agent = Host()
        Existing(agent)

        with self.assertRaisesRegex(TagContractError, "Standing.*Tag\\[:\\]"):
            Checking(agent)

        # Admission happened before the failed Post, and raw Field questions
        # remain available for repair and inspection.
        self.assertIn(agent, Existing[:])
        self.assertIn(agent, Checking[:])
        with self.assertRaisesRegex(TagContractError, "Tag\\[:\\]"):
            agent.Standing
        with self.assertRaisesRegex(TagContractError, "Tag\\[:\\]"):
            Contract.Status(agent)

    def test_all_sound_population_spellings_reject_the_same_post_cycle(self):
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

                with self.assertRaises(TagContractError):
                    Checking(agent)

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

    def test_indirect_post_pre_soundness_cycle_is_not_reported_as_false(self):
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

        with self.assertRaisesRegex(TagContractError, "Guard.*Existing.*Tag\\[:\\]"):
            Witness(agent)

        self.assertIn(agent, Witness[:])
        with self.assertRaises(TagContractError):
            agent.Guard
        with self.assertRaises(TagContractError):
            _ = agent in Base

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
