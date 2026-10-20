"""Draft: each declaring Tag grants its own Link at a shared Agent name."""

import gc
import unittest
import weakref

from TopKit import Imprint, Link, Pre, Record, Rip, Tag, TagPreconditionError
from TopKit.links import _pair_of
from TopKit.state import _state_of


class Host:
    pass


class OwnedLinkIdentityDraftTests(unittest.TestCase):
    def test_same_name_shape_has_its_own_field_pair_and_saved_base_view(self):
        class Base(Tag):
            @Link
            class Knows(Tag):
                @Record
                def base_card(owner, contact):
                    return "base"

        class Shape(Base):
            @Link
            class Knows(Base.Knows):
                @Record
                def shape_card(owner, contact):
                    return "shape"

        owner, contact = Host(), Host()
        Base(owner)
        base_view = Base[owner]
        base_link = base_view.Knows
        Shape(owner)
        shape_link = owner.Knows

        self.assertIsNot(base_link, shape_link)
        self.assertIs(base_view.Knows, base_link)
        self.assertIs(Shape[owner].Knows, shape_link)
        shape_link(contact)
        self.assertIn(contact, base_link)
        self.assertIn(contact, shape_link)
        self.assertIsNot(_pair_of(base_link, contact),
                         _pair_of(shape_link, contact))
        self.assertEqual(base_link[contact].base_card, "base")
        self.assertEqual(shape_link[contact].shape_card, "shape")
        self.assertFalse("shape_card" @ base_link[contact])

        del shape_link[contact]
        self.assertIn(contact, base_link)
        self.assertNotIn(contact, shape_link[:])

    def test_independent_same_name_relation_overlays_without_linking_lower(self):
        class One(Tag):
            @Link
            class Knows(Tag):
                pass

        class Two(Tag):
            @Link
            class Knows(Tag):
                pass

        owner, contact = Host(), Host()
        One(owner)
        lower = owner.Knows
        Two(owner)
        upper = owner.Knows

        self.assertIsNot(lower, upper)
        self.assertIs(One[owner].Knows, lower)
        self.assertIs(Two[owner].Knows, upper)
        upper(contact)
        self.assertIn(contact, upper)
        self.assertNotIn(contact, lower[:])

    def test_nested_independent_tagging_keeps_each_own_link_view(self):
        class Other(Tag):
            @Link
            class Knows(Tag):
                pass

        class First(Tag):
            @Link
            class Knows(Tag):
                pass

            @Imprint
            def Bring_Other(owner):
                Other(owner)

        owner = Host()
        First(owner)

        self.assertIsNot(First[owner].Knows, Other[owner].Knows)
        self.assertIs(owner.Knows, Other[owner].Knows)

    def test_outer_view_does_not_gain_a_nested_tags_later_link(self):
        class Inner(Tag):
            @Link
            class Knows(Tag):
                pass

        class Outer(Tag):
            @Imprint
            def Bring_Inner(owner):
                Inner(owner)

        owner = Host()
        Outer(owner)

        self.assertFalse("Knows" @ Outer[owner])
        with self.assertRaises(AttributeError):
            _ = Outer[owner].Knows
        self.assertIs(Inner[owner].Knows, owner.Knows)

    def test_ripping_base_link_keeps_shape_field_and_pair(self):
        class Base(Tag):
            @Link
            class Knows(Tag):
                @Record
                def base_card(owner, contact):
                    return "base"

        class Shape(Base):
            @Link
            class Knows(Base.Knows):
                @Record
                def shape_card(owner, contact):
                    return "shape"

        owner, contact = Host(), Host()
        Shape(owner)
        base_link = Base[owner].Knows
        shape_link = Shape[owner].Knows
        shape_link(contact)
        shape_pair = _pair_of(shape_link, contact)

        del base_link[contact]

        self.assertNotIn(contact, base_link[:])
        self.assertIn(contact, shape_link)
        self.assertIs(_pair_of(shape_link, contact), shape_pair)
        self.assertEqual(shape_link[contact].shape_card, "shape")

    def test_refused_gate_does_not_publish_scratch_owned_link(self):
        class One(Tag):
            @Link
            class Knows(Tag):
                pass

        class Refused(Tag):
            @Link
            class Knows(Tag):
                pass

            @Pre
            def Gate(owner):
                return False

        owner = Host()
        One(owner)
        lower = owner.Knows
        state = _state_of(owner)
        with self.assertRaises(TagPreconditionError):
            Refused(owner)

        self.assertIs(owner.Knows, lower)
        self.assertIsNone(state.owned_links.get(Refused))
        self.assertIs(state.owned_links[One]["Knows"][0], lower)

    def test_retagging_a_declarer_reselects_its_owned_link(self):
        class One(Tag):
            @Link
            class Knows(Tag):
                pass

        class Two(Tag):
            @Link
            class Knows(Tag):
                pass

        owner = Host()
        One(owner)
        lower = owner.Knows
        Two(owner)
        upper = owner.Knows
        del One[owner]
        One(owner)

        self.assertIs(owner.Knows, lower)
        self.assertIs(One[owner].Knows, lower)
        self.assertIsNot(owner.Knows, upper)

    def test_owner_end_rips_hidden_and_visible_same_name_links(self):
        cleanup = []

        class One(Tag):
            @Link
            class Knows(Tag):
                @Rip
                def Leave(owner, contact):
                    cleanup.append("one")

        class Two(Tag):
            @Link
            class Knows(Tag):
                @Rip
                def Leave(owner, contact):
                    cleanup.append("two")

        owner, contact = Host(), Host()
        One(owner)
        lower = owner.Knows
        lower(contact)
        Two(owner)
        upper = owner.Knows
        upper(contact)
        reference = weakref.ref(owner)
        del owner
        gc.collect()

        self.assertIsNone(reference())
        self.assertEqual(cleanup, ["two", "one"])
        self.assertNotIn(contact, lower[:])
        self.assertNotIn(contact, upper[:])


if __name__ == "__main__":
    unittest.main()
