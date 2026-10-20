"""Draft: a saved Link Pair view resolves the current Pair on every use."""

import gc
import unittest
import weakref

from TopKit import (Contract, Flag, Keyword, Link, Post, Record, Tag,
                    TagResolutionError)
from TopKit.links import _pair_of


class Host:
    pass


class LivePairViewDraftTests(unittest.TestCase):
    def test_saved_view_follows_same_link_after_rip_and_retag(self):
        class Social(Tag):
            @Link
            class Knows(Tag):
                @Record
                def level(owner, contact, *, level=0):
                    return level

                @Post
                def Positive(owner, contact):
                    return owner.Knows[contact].level > 0

        owner, contact = Host(), Host()
        Social(owner)
        link = owner.Knows
        with self.assertRaises(TagResolutionError):
            _ = link[contact]

        link(contact, level=1)
        saved = link[contact]
        first = _pair_of(link, contact)
        self.assertEqual(saved.level, 1)
        self.assertTrue("level" @ saved)
        self.assertTrue(saved)
        self.assertEqual(Contract.Status(saved), {"Positive": True})
        self.assertTrue(Contract.Postconditions(saved))

        del link[contact]
        with self.assertRaises(TagResolutionError):
            _ = saved.level
        with self.assertRaises(TagResolutionError):
            _ = bool(saved)
        with self.assertRaises(TagResolutionError):
            _ = "level" @ saved

        link(contact, level=2)
        second = _pair_of(link, contact)
        self.assertIsNot(first, second)
        self.assertEqual(saved.level, 2)
        self.assertTrue(saved)
        saved.level = 3
        self.assertEqual(link[contact].level, 3)
        del saved.level
        self.assertFalse("level" @ saved)
        self.assertEqual(Contract.Status(saved), {"Positive": False})

    def test_saved_view_does_not_follow_same_name_overlay(self):
        class Base(Tag):
            @Link
            class Knows(Tag):
                @Record
                def base_value(owner, contact):
                    return "base"

        class Shape(Base):
            @Link
            class Knows(Base.Knows):
                @Record
                def shape_value(owner, contact):
                    return "shape"

        owner, contact = Host(), Host()
        Base(owner)
        base_link = owner.Knows
        base_link(contact)
        saved = base_link[contact]

        Shape(owner)
        shape_link = owner.Knows
        shape_link(contact)
        self.assertIsNot(base_link, shape_link)
        self.assertEqual(saved.base_value, "base")
        self.assertFalse("shape_value" @ saved)
        self.assertEqual(shape_link[contact].shape_value, "shape")

        del base_link[contact]
        with self.assertRaises(TagResolutionError):
            _ = saved.base_value
        self.assertEqual(shape_link[contact].shape_value, "shape")

    def test_view_does_not_keep_contact_alive(self):
        class Social(Tag):
            @Link
            class Knows(Tag):
                pass

        owner, contact = Host(), Host()
        Social(owner)
        link = owner.Knows
        link(contact)
        saved = link[contact]
        contact_ref = weakref.ref(contact)

        del contact
        gc.collect()

        self.assertIsNone(contact_ref())
        with self.assertRaises(TagResolutionError):
            _ = bool(saved)

    def test_pair_flag_and_keyword_queries_resolve_the_current_pair(self):
        class Social(Tag):
            @Link
            @Flag("Trusted")
            class Knows(Tag):
                pass

        owner, contact = Host(), Host()
        Social(owner)
        link = owner.Knows
        link(contact)
        saved = link[contact]
        self.assertIn("Knows", saved)
        self.assertIn("Trusted", saved)
        self.assertTrue(Keyword(saved, "Trusted"))

        del link[contact]
        with self.assertRaises(TagResolutionError):
            _ = "Trusted" in saved

    def test_view_does_not_keep_owner_or_link_alive(self):
        class Social(Tag):
            @Link
            class Knows(Tag):
                pass

        owner, contact = Host(), Host()
        Social(owner)
        link = owner.Knows
        link(contact)
        saved = link[contact]
        owner_ref = weakref.ref(owner)
        link_ref = weakref.ref(link)

        del owner, link
        gc.collect()

        self.assertIsNone(owner_ref())
        self.assertIsNone(link_ref())
        with self.assertRaises(TagResolutionError):
            _ = "anything" @ saved

    def test_unrelated_host_metaclass_is_not_asked_to_hash_or_compare(self):
        class HostMeta(type):
            def __hash__(cls):
                raise AssertionError("a plain query hashed the Host type")

            def __eq__(cls, other):
                raise AssertionError("a plain query compared the Host type")

        class Foreign(metaclass=HostMeta):
            pass

        target = Foreign()
        self.assertFalse(Keyword(target, "Unknown"))
        self.assertEqual(Contract.Status(target), {})
        self.assertTrue(Contract.Postconditions(target))


if __name__ == "__main__":
    unittest.main()
