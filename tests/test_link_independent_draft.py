"""Draft: each actual Link owns a separate Contact Field and Pair."""

import unittest

from TopKit import Imprint, Link, Record, Rip, Tag, TagCompositionError
from TopKit.links import _pair_of


class Host:
    pass


class IndependentLinkDraftTests(unittest.TestCase):
    def test_relation_base_tags_contact_first_but_keeps_its_own_pair(self):
        turns = []

        class Social(Tag):
            @Link
            class Knows(Tag):
                @Record
                def since(owner, contact):
                    return 2010

                @Imprint
                def Train(owner, contact):
                    turns.append("Knows")

            @Link
            class Trusts(Knows):
                @Record
                def confidence(owner, contact):
                    return 8

                @Imprint
                def Train(owner, contact):
                    turns.append("Trusts")
                    self.assertIn(contact, owner.Knows)

        owner, contact = Host(), Host()
        Social(owner)
        owner.Trusts(contact)

        self.assertEqual(turns, ["Knows", "Trusts"])
        self.assertIn(contact, owner.Knows)
        self.assertIn(contact, owner.Trusts)
        self.assertIsNot(_pair_of(owner.Knows, contact),
                         _pair_of(owner.Trusts, contact))
        self.assertEqual(owner.Knows[contact].since, 2010)
        self.assertEqual(owner.Trusts[contact].confidence, 8)
        self.assertFalse("since" @ owner.Trusts[contact])
        self.assertFalse("confidence" @ owner.Knows[contact])

    def test_ripping_one_link_does_not_rip_its_relation_base(self):
        cleanup = []

        class Social(Tag):
            @Link
            class Knows(Tag):
                @Rip
                def Leave(owner, contact):
                    cleanup.append("Knows")

            @Link
            class Trusts(Knows):
                @Rip
                def Leave(owner, contact):
                    cleanup.append("Trusts")

        owner, contact = Host(), Host()
        Social(owner)
        owner.Trusts(contact)
        del owner.Trusts[contact]

        self.assertEqual(cleanup, ["Trusts"])
        self.assertNotIn(contact, owner.Trusts[:])
        self.assertIn(contact, owner.Knows)
        del owner.Knows[contact]
        self.assertEqual(cleanup, ["Trusts", "Knows"])

    def test_two_relation_bases_keep_three_distinct_pairs(self):
        class Social(Tag):
            @Link
            class Knows(Tag):
                pass

            @Link
            class Likes(Tag):
                pass

            @Link
            class Bonded(Knows, Likes):
                pass

        owner, contact = Host(), Host()
        Social(owner)
        owner.Bonded(contact)

        pairs = (_pair_of(owner.Knows, contact),
                 _pair_of(owner.Likes, contact),
                 _pair_of(owner.Bonded, contact))
        self.assertEqual(len({id(pair) for pair in pairs}), 3)
        self.assertTrue(all(contact in link for link in
                            (owner.Knows, owner.Likes, owner.Bonded)))

    def test_declared_base_must_finish_before_shape_turn(self):
        class Social(Tag):
            @Link
            class Knows(Tag):
                @Imprint
                def Train(owner, contact):
                    with self.assertRaisesRegex(
                            TagCompositionError,
                            "whose Tagging has not finished",
                            ):
                        owner.Trusts(contact)

            @Link
            class Trusts(Knows):
                pass

        owner, contact = Host(), Host()
        Social(owner)
        owner.Knows(contact)
        self.assertIn(contact, owner.Knows)
        self.assertNotIn(contact, owner.Trusts[:])


if __name__ == "__main__":
    unittest.main()
