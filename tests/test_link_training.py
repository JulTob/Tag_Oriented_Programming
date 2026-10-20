"""Links follow the same gaining and admission boundaries as ordinary Tags."""
import unittest
from TopKit import (Imprint, Link, Post, Pre, Public, Record, Tag,
                    TagImprintError, TagPostconditionError)
from TopKit.links import _pair_tag, _record_of
from TopKit.state import _state_of

class Host:
    pass

class LinkTrainingTests(unittest.TestCase):
    def test_a_record_reads_an_earlier_link_gaining(self):
        class Social(Tag):
            @Link
            class Knows(Tag):
                pass
            @Record
            def initial_contacts(agent):
                return len(agent.Knows)
        owner = Host()
        Social(owner)
        self.assertEqual(owner.initial_contacts, 0)
        self.assertTrue('Knows' @ owner)

    def test_failed_imprint_retains_gains_and_posts_but_retry_runs_again(self):
        attempts = []
        class Social(Tag):
            @Link
            class Knows(Tag):
                @Post
                def Ready(owner, contact):
                    return contact.ready
                @Record
                def attempts(owner, contact, stored=None):
                    return (stored or 0) + 1
                @Imprint
                def Train(owner, contact):
                    attempts.append(contact in owner.Knows)
                    if not contact.ready:
                        raise ValueError('not ready')
        owner, contact = Host(), Host()
        contact.ready = False
        Social(owner)
        with self.assertRaises(TagImprintError):
            owner.Knows(contact)
        pair = _record_of(owner.Knows).family.Pair_Of(contact)
        self.assertNotIn(contact, owner.Knows)
        self.assertEqual(len(owner.Knows[:]), 0)
        self.assertEqual(pair.attempts, 1)
        self.assertFalse(bool(pair))
        contact.ready = True
        owner.Knows(contact)
        self.assertIs(owner.Knows[contact], pair)
        self.assertEqual(pair.attempts, 2)
        self.assertEqual(attempts, [False, False])
        self.assertIn(contact, owner.Knows)
        self.assertTrue(bool(pair))

    def test_failed_post_keeps_completed_membership_and_does_not_retrain(self):
        trained = []
        class Social(Tag):
            @Link
            class Knows(Tag):
                @Imprint
                def Train(owner, contact):
                    trained.append(contact)
                @Post
                def Ready(owner, contact):
                    return False
        owner, contact = Host(), Host()
        Social(owner)
        with self.assertRaises(TagPostconditionError):
            owner.Knows(contact)
        self.assertIn(contact, owner.Knows[:])
        self.assertNotIn(contact, owner.Knows)
        self.assertIn(contact, ~owner.Knows)
        owner.Knows(contact)
        self.assertEqual(trained, [contact])

    def test_base_post_stops_before_shape_gate_after_base_admission(self):
        seen = []

        class Social(Tag):
            @Link
            class Base(Tag):
                @Post
                def Ready(owner, contact):
                    seen.append(("Base Post", contact in owner.Base[:]))
                    return False

            @Link
            class Shape(Base):
                @Pre
                def Gate(owner, contact):
                    seen.append("Shape Gate")
                    return True

        owner, contact = Host(), Host()
        Social(owner)

        with self.assertRaises(TagPostconditionError):
            owner.Shape(contact)

        self.assertEqual(seen, [("Base Post", True)])
        self.assertIn(contact, owner.Base[:])
        self.assertNotIn(contact, owner.Base)
        self.assertNotIn(contact, owner.Shape[:])

        pair = _record_of(owner.Base).family.Pair_Of(contact)
        pair_state = _state_of(pair)
        self.assertIn(_pair_tag(Social.Base), pair_state.active)
        self.assertNotIn(_pair_tag(Social.Shape), pair_state.active)

    def test_reentering_the_same_link_during_training_is_a_noop(self):
        seen = []
        class Social(Tag):
            @Link
            class Knows(Tag):
                @Imprint
                def Train(owner, contact):
                    seen.append(contact in owner.Knows)
                    owner.Knows(contact)
        owner, contact = Host(), Host()
        Social(owner)
        owner.Knows(contact)
        self.assertEqual(seen, [False])
        self.assertIn(contact, owner.Knows)

    def test_published_lines_arrive_only_after_training(self):
        seen = []
        class Social(Tag):
            @Link
            class Knows(Tag):
                @Public
                def Greet(owner, contact):
                    return 'hello'
                @Imprint
                def Train(owner, contact):
                    seen.append(('Greet' @ contact, contact in owner.Knows))
        class Known(Tag):
            pass
        owner, contact = Host(), Host()
        Known(contact)
        Social(owner)
        owner.Knows(contact)
        self.assertEqual(seen, [(False, False)])
        self.assertEqual(contact.Greet(), 'hello')

    def test_later_gate_sees_completed_base_training_and_membership(self):
        class Social(Tag):
            @Link
            class Knows(Tag):
                @Record
                def credential(owner, contact):
                    return 'trained'
            @Link
            class Trusts(Knows):
                @Pre
                def Trained(owner, contact):
                    return contact in owner.Knows and owner.Knows[contact].credential == 'trained'
        owner, contact = Host(), Host()
        Social(owner)
        owner.Trusts(contact)
        self.assertIn(contact, owner.Knows)
        self.assertIn(contact, owner.Trusts)

if __name__ == '__main__':
    unittest.main()
