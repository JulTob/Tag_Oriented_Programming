"""A Link extension keeps completed and partial Pair Gainings."""

import unittest

from TopKit import Imprint, Link, Post, Record, Tag, TagCompositionError
from TopKit.links import _pair_tag
from TopKit.state import _state_of


class Host:
    pass


class LinkExtensionAdmissionTests(unittest.TestCase):
    def test_partial_extension_keeps_gains_and_retry_finishes_missing_pairs(self):
        built = []
        trained = []

        class Social(Tag):
            @Link
            class Knows(Tag):
                pass

        class Trained(Social):
            @Link
            class Knows(Social.Knows):
                @Post
                def Ready(agent, contact):
                    return contact.ready

                @Record
                def ticket(agent, contact):
                    built.append(contact.name)
                    return contact.name

                @Record
                def verified(agent, contact):
                    if contact.blocked:
                        raise ValueError("verification failed")
                    return True

                @Imprint
                def Train(agent, contact):
                    trained.append(contact.name)

        owner = Host()
        Social(owner)
        contacts = [Host() for _ in range(3)]
        for name, contact in zip(("first", "second", "third"), contacts):
            contact.name = name
            contact.blocked = name == "second"
            contact.ready = not contact.blocked
            owner.Knows(contact)
        pairs = [owner.Knows[contact] for contact in contacts]
        link = owner.Knows
        extension = _pair_tag(Trained.Knows)

        with self.assertRaises(TagCompositionError):
            Trained(owner)

        self.assertIs(owner.Knows, link)
        self.assertNotIn(owner, Trained)
        self.assertIn(extension, _state_of(pairs[0]).active)
        self.assertNotIn(extension, _state_of(pairs[1]).active)
        self.assertNotIn(extension, _state_of(pairs[2]).active)
        self.assertEqual(pairs[0].ticket, "first")
        self.assertTrue(pairs[0].verified)
        self.assertEqual(pairs[1].ticket, "second")
        self.assertFalse(pairs[1].Ready)
        self.assertFalse(bool(pairs[1]))
        self.assertFalse("verified" @ pairs[1])
        self.assertFalse("ticket" @ pairs[2])
        self.assertEqual(trained, ["first"])
        self.assertEqual(list(link[:]), contacts)

        contacts[1].blocked = False
        contacts[1].ready = True
        Trained(owner)

        self.assertIn(owner, Trained)
        self.assertEqual(built, ["first", "second", "second", "third"])
        self.assertEqual(trained, ["first", "second", "third"])
        for contact, pair in zip(contacts, pairs):
            self.assertIs(link[contact], pair)
            self.assertIn(extension, _state_of(pair).active)
            self.assertTrue(bool(pair))

    def test_later_owner_record_failure_keeps_completed_extension(self):
        trained = []

        class Social(Tag):
            @Link
            class Knows(Tag):
                pass

        class Trained(Social):
            @Link
            class Knows(Social.Knows):
                @Record
                def badge(agent, contact):
                    return "trained"

                @Imprint
                def Train(agent, contact):
                    trained.append(contact)

            @Record
            def ready(agent):
                if not agent.allow_ready:
                    raise ValueError("owner preparation failed")
                return True

        owner, contact = Host(), Host()
        owner.allow_ready = False
        Social(owner)
        owner.Knows(contact)
        pair = owner.Knows[contact]

        with self.assertRaises(TagCompositionError):
            Trained(owner)

        self.assertIn(owner, Social)
        self.assertNotIn(owner, Trained)
        self.assertIn(_pair_tag(Trained.Knows), _state_of(pair).active)
        self.assertEqual(pair.badge, "trained")
        self.assertEqual(trained, [contact])

        owner.allow_ready = True
        Trained(owner)
        self.assertIn(owner, Trained)
        self.assertEqual(trained, [contact])
        self.assertTrue(owner.ready)


if __name__ == "__main__":
    unittest.main()
