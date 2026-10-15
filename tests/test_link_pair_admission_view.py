"""A Link view follows Field admission while the Pair keeps partial Gains."""

from contextvars import copy_context
import unittest

from TopKit import Imprint, Link, Record, Rip, Tag
from TopKit import TagImprintError, TagResolutionError
from TopKit.links import _record_of


class Host:
    pass


class LinkPairAdmissionViewTests(unittest.TestCase):
    def test_failed_training_keeps_a_private_pair_and_retry_reuses_it(self):
        seen = []
        copied = []

        class Social(Tag):
            @Link
            class Knows(Tag):
                @Record
                def attempts(agent, contact, prior=None):
                    return (prior or 0) + 1

                @Imprint
                def Train(agent, contact):
                    seen.append(agent.Knows[contact])
                    copied.append(copy_context())
                    if not contact.ready:
                        raise ValueError("training unfinished")

        owner, contact = Host(), Host()
        contact.ready = False
        Social(owner)

        with self.assertRaises(TagImprintError):
            owner.Knows(contact)

        pair = _record_of(owner.Knows).family.Pair_Of(contact)
        self.assertIs(seen[0], pair)
        self.assertEqual(pair.attempts, 1)
        self.assertNotIn(contact, owner.Knows[:])
        with self.assertRaises(TagResolutionError):
            owner.Knows[contact]
        with self.assertRaises(TagResolutionError):
            copied[0].run(lambda: owner.Knows[contact])

        contact.ready = True
        owner.Knows(contact)
        self.assertIn(contact, owner.Knows[:])
        self.assertIs(owner.Knows[contact], pair)
        self.assertIs(seen[1], pair)
        self.assertEqual(pair.attempts, 2)

    def test_ripped_base_view_closes_but_shape_keeps_the_shared_pair(self):
        teardowns = []

        class Social(Tag):
            @Link
            class Candidate(Tag):
                @Record
                def credential(agent, contact):
                    return "trained"

                @Rip
                def Leave(agent, contact):
                    teardowns.append(agent.Candidate[contact].credential)

            @Link
            class CIA(Candidate):
                pass

        owner, contact = Host(), Host()
        Social(owner)
        owner.CIA(contact)
        pair = owner.CIA[contact]

        del owner.Candidate[contact]

        self.assertEqual(teardowns, ["trained"])
        self.assertNotIn(contact, owner.Candidate[:])
        self.assertIn(contact, owner.CIA[:])
        with self.assertRaises(TagResolutionError):
            owner.Candidate[contact]
        self.assertIs(owner.CIA[contact], pair)
        self.assertEqual(pair.credential, "trained")


if __name__ == "__main__":
    unittest.main()
