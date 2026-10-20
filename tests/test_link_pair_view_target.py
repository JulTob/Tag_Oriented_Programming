"""A saved Pair view follows its current Pair at TOP Target/query boundaries."""

import unittest

from TopKit import Link, Outline, Record, Tag, TagResolutionError, Tags
from TopKit.links import _pair_of


class Host:
    pass


class LivePairTargetTests(unittest.TestCase):
    def test_tagging_membership_view_and_rip_follow_current_pair(self):
        class Social(Tag):
            @Link
            class Knows(Tag):
                @Record
                def level(owner, contact, *, level=0):
                    return level

        class Mark(Tag):
            @Record
            def label(pair):
                return "marked"

        owner, contact = Host(), Host()
        Social(owner)
        link = owner.Knows
        link(contact, level=1)
        saved = link[contact]
        first = _pair_of(link, contact)

        self.assertIs(Mark(saved), first)
        self.assertIn(saved, Mark)
        self.assertIn(saved, Mark[:])
        self.assertIn(saved, Mark | ~Mark)
        self.assertIsInstance(saved, Mark)
        self.assertEqual(Mark[saved].label, "marked")
        self.assertEqual(Tags(saved), (Mark,))
        self.assertIn("Mark", Outline(saved))

        del Mark[saved]
        self.assertNotIn(saved, Mark[:])
        del link[contact]
        with self.assertRaises(TagResolutionError):
            _ = saved in Mark

        link(contact, level=2)
        second = _pair_of(link, contact)
        self.assertIsNot(first, second)
        self.assertEqual(saved.level, 2)
        self.assertNotIn(saved, Mark[:])
        self.assertNotIsInstance(saved, Mark)
        self.assertEqual(Tags(saved), ())
        self.assertIs(Mark(saved), second)
        self.assertIn(saved, Mark)
        self.assertEqual(Mark[saved].label, "marked")


if __name__ == "__main__":
    unittest.main()
