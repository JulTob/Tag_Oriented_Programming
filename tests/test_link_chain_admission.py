"""Independent Link turns and the lifetime of retained Rogue Pairs."""

import gc
import unittest
import weakref

from TopKit import Imprint, Link, Pre, Record, Tag
from TopKit import TagCompositionError, TagImprintError, TagPreconditionError
from TopKit.links import _pair_ends, _record_of


class Host:
    pass


class LinkChainAdmissionTests(unittest.TestCase):
    def test_completed_base_link_survives_later_shape_gate_refusal(self):
        trained = []

        class Social(Tag):
            @Link
            class Knows(Tag):
                @Record
                def card(agent, contact):
                    return "known"

                @Imprint
                def Train(agent, contact):
                    trained.append("base")

            @Link
            class Trusts(Knows):
                @Pre
                def Allowed(agent, contact):
                    return contact.allowed

                @Imprint
                def Train(agent, contact):
                    trained.append("shape")

        owner, contact = Host(), Host()
        contact.allowed = False
        Social(owner)
        with self.assertRaises(TagPreconditionError):
            owner.Trusts(contact)

        self.assertIn(contact, owner.Knows)
        self.assertNotIn(contact, owner.Trusts)
        pair = owner.Knows[contact]
        self.assertEqual(pair.card, "known")
        self.assertEqual(trained, ["base"])

        contact.allowed = True
        owner.Trusts(contact)
        self.assertIn(contact, owner.Trusts)
        self.assertIs(owner.Trusts[contact], pair)
        self.assertEqual(trained, ["base", "shape"])

    def test_completed_base_link_survives_later_shape_imprint_failure(self):
        trained = []

        class Social(Tag):
            @Link
            class Knows(Tag):
                @Imprint
                def Train(agent, contact):
                    trained.append("base")

            @Link
            class Trusts(Knows):
                @Record
                def badge(agent, contact):
                    return "offered"

                @Imprint
                def Train(agent, contact):
                    trained.append("shape")
                    if not contact.allowed:
                        raise ValueError("unfinished training")

        owner, contact = Host(), Host()
        contact.allowed = False
        Social(owner)
        with self.assertRaises(TagImprintError):
            owner.Trusts(contact)

        self.assertIn(contact, owner.Knows)
        self.assertNotIn(contact, owner.Trusts)
        pair = owner.Knows[contact]
        self.assertEqual(pair.badge, "offered")
        self.assertEqual(trained, ["base", "shape"])

        contact.allowed = True
        owner.Trusts(contact)
        self.assertIn(contact, owner.Trusts)
        self.assertIs(owner.Trusts[contact], pair)
        self.assertEqual(trained, ["base", "shape", "shape"])

    def test_refused_contact_actualization_retries_completed_pair_training(self):
        trained = []

        class Contact:
            def __init__(contact):
                contact.blocked = True

            def __setattr__(contact, name, value):
                if name == "__class__" and contact.blocked:
                    raise ValueError("host declines actualization")
                object.__setattr__(contact, name, value)

        class Social(Tag):
            @Link
            class Knows(Tag):
                @Record
                def ticket(agent, contact):
                    return len(trained) + 1

                @Imprint
                def Train(agent, contact):
                    trained.append("trained")

        owner, contact = Host(), Contact()
        Social(owner)
        with self.assertRaises(TagCompositionError):
            owner.Knows(contact)
        pair = _record_of(owner.Knows).family.Pair_Of(contact)
        self.assertNotIn(contact, owner.Knows)
        self.assertEqual(pair.ticket, 1)
        self.assertEqual(trained, ["trained"])
        self.assertIs(type(contact), Contact)
        self.assertEqual(vars(contact), {"blocked": True})

        contact.blocked = False
        owner.Knows(contact)
        self.assertIn(contact, owner.Knows)
        self.assertIs(owner.Knows[contact], pair)
        self.assertEqual(pair.ticket, 2)
        self.assertEqual(trained, ["trained", "trained"])

    def test_explicit_contact_truth_is_refused_before_pair_training(self):
        trained = []

        class Contact:
            def __bool__(contact):
                raise AssertionError("host truth must not be evaluated")

        class Social(Tag):
            @Link
            class Knows(Tag):
                @Imprint
                def Train(agent, contact):
                    trained.append(contact)

        owner, contact = Host(), Contact()
        Social(owner)
        with self.assertRaisesRegex(TagCompositionError, "defines __bool__"):
            owner.Knows(contact)
        self.assertEqual(trained, [])
        self.assertIs(type(contact), Contact)
        self.assertEqual(vars(contact), {})
        self.assertEqual(_record_of(owner.Knows).family.pairs, {})

    def test_shape_training_can_rip_its_candidate_base_before_admission(self):
        training = []

        class Social(Tag):
            @Link
            class Candidate(Tag):
                @Record
                def evaluation(agent, contact):
                    return "passed"

            @Link
            class CIA(Candidate):
                @Record
                def clearance(agent, contact):
                    return "active"

                @Imprint
                def Join(agent, contact):
                    training.append((contact in agent.Candidate,
                                     contact in agent.CIA))
                    pair = agent.CIA[contact]
                    self.assertEqual(pair.evaluation, "passed")
                    self.assertEqual(pair.clearance, "active")
                    del agent.Candidate[contact]

        agent, contact = Host(), Host()
        Social(agent)
        agent.CIA(contact)

        self.assertEqual(training, [(True, False)])
        self.assertNotIn(contact, agent.Candidate)
        self.assertIn(contact, agent.CIA)
        pair = agent.CIA[contact]
        self.assertEqual((pair.evaluation, pair.clearance),
                         ("passed", "active"))
        agent.CIA(contact)  # an already completed Tagging remains a no-op
        self.assertEqual(training, [(True, False)])

    def test_contact_death_releases_unadmitted_pair_after_family_join(self):
        class Social(Tag):
            @Link
            class Knows(Tag):
                pass

            @Link
            class Likes(Tag):
                @Record
                def card(agent, contact):
                    return "partial"

                @Imprint
                def Train(agent, contact):
                    raise ValueError("unfinished")

        class Joined(Social):
            @Link
            class Both(Social.Knows, Social.Likes):
                pass

        owner, contact = Host(), Host()
        Social(owner)
        with self.assertRaises(TagImprintError):
            owner.Likes(contact)
        original_family = _record_of(owner.Likes).family
        pair = original_family.Pair_Of(contact)

        Joined(owner)
        family = _record_of(owner.Both).family
        self.assertIsNot(family, original_family)
        self.assertIs(family.Pair_Of(contact), pair)
        reference = weakref.ref(contact)
        del contact
        gc.collect()

        self.assertIsNone(reference())
        self.assertEqual(family.pairs, {})
        self.assertTrue(_pair_ends(pair).ended)

    def test_owner_death_releases_unadmitted_pair_while_link_handle_remains(self):
        class Social(Tag):
            @Link
            class Knows(Tag):
                @Record
                def card(agent, contact):
                    return "partial"

                @Imprint
                def Train(agent, contact):
                    raise ValueError("unfinished")

        owner, contact = Host(), Host()
        Social(owner)
        link = owner.Knows
        with self.assertRaises(TagImprintError):
            link(contact)
        family = _record_of(link).family
        pair = family.Pair_Of(contact)
        reference = weakref.ref(owner)
        del owner
        gc.collect()

        self.assertIsNone(reference())
        self.assertEqual(family.pairs, {})
        self.assertTrue(_pair_ends(pair).ended)
        self.assertTrue(_record_of(link).ended)


if __name__ == "__main__":
    unittest.main()
