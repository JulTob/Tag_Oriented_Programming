"""Pin and ordinary Tag categories are fixed when their classes are declared."""

import gc
import unittest
import weakref

from TopKit import (
    Action, Form, Pin, Post, Pre, Record, Tag,
    TagCompositionError, TagDeclarationError,
    TagPostconditionError, TagPreconditionError, TagResolutionError,
)
from TopKit.tags import MetaTag


class PinCategoryRootTests(unittest.TestCase):
    def assert_no_conversion(self, tag):
        original_meta = type(tag)
        original_bases = type.__dict__["__bases__"].__get__(tag)
        members = tuple(tag[:])
        with self.assertRaises(TagDeclarationError):
            Pin(tag)
        self.assertIs(type(tag), original_meta)
        self.assertEqual(type.__dict__["__bases__"].__get__(tag), original_bases)
        self.assertEqual(tuple(tag[:]), members)

    def test_an_unused_ordinary_tag_cannot_be_converted(self):
        class Ordinary(Tag):
            pass

        self.assert_no_conversion(Ordinary)
        class Host:
            pass
        host = Host()
        self.assertIs(Ordinary(host), host)
        self.assertIn(host, Ordinary[:])

    def test_a_refused_gate_does_not_make_an_ordinary_tag_convertible(self):
        class Ordinary(Tag):
            @Pre
            def Permit(agent):
                return False

        class Host:
            pass
        with self.assertRaises(TagPreconditionError):
            Ordinary(Host())
        self.assert_no_conversion(Ordinary)
        self.assertEqual(len(Ordinary[:]), 0)

    def test_a_broken_application_and_rip_do_not_make_a_pin(self):
        class Ordinary(Tag):
            @Post
            def Ready(agent):
                return False

        class Host:
            pass
        host = Host()
        with self.assertRaises(TagPostconditionError):
            Ordinary(host)
        self.assertIn(host, Ordinary[:])
        del Ordinary[host]
        self.assert_no_conversion(Ordinary)

    def test_a_base_remains_ordinary_after_its_shape_and_members_leave(self):
        class Base(Tag):
            pass
        class Shape(Base):
            pass
        class Host:
            pass
        host = Host()
        Shape(host)
        del Shape[host]
        del Base[host]
        shape_ref = weakref.ref(Shape)
        del Shape, host
        gc.collect()
        self.assertIsNone(shape_ref())
        self.assert_no_conversion(Base)

    def test_category_does_not_depend_on_a_metaclass_history_descriptor(self):
        writes = []
        class HistoryMeta(MetaTag):
            @property
            def __topkit_applied__(cls):
                return False

            @__topkit_applied__.setter
            def __topkit_applied__(cls, value):
                writes.append(value)

        class Ordinary(Tag, metaclass=HistoryMeta):
            pass
        class Host:
            pass
        host = Host()
        Ordinary(host)
        del Ordinary[host]
        self.assert_no_conversion(Ordinary)
        self.assertEqual(writes, [])
        self.assertNotIn("__topkit_applied__", Ordinary.__dict__)

    def test_a_pin_accepts_populated_tags_and_pins_without_reclassifying_them(self):
        class Labelled(Pin):
            @Record
            def label(target):
                return "labelled"

        class Ordinary(Tag):
            @Action
            def Identify(agent):
                return "ordinary"

        class Inner(Pin):
            pass
        class Member(Tag):
            pass
        class Host:
            pass
        host = Host()
        Ordinary(host)
        Inner(Member)
        ordinary_id, pin_id = id(Ordinary), id(Inner)
        self.assertIs(Labelled(Ordinary), Ordinary)
        self.assertIs(Labelled(Inner), Inner)
        self.assertEqual((id(Ordinary), id(Inner)), (ordinary_id, pin_id))
        self.assertEqual(Ordinary.label, "labelled")
        self.assertEqual(Inner.label, "labelled")
        self.assertIn(host, Ordinary[:])
        self.assertIn(Member, Inner[:])
        self.assertEqual(host.Identify(), "ordinary")
        self.assertIs(Labelled(Ordinary), Ordinary)
        other = Host()
        self.assertIs(Ordinary(other), other)
        self.assertIn(other, Ordinary[:])

    def test_a_named_pin_refuses_an_object_before_its_gate(self):
        calls = []
        class Labelled(Pin):
            @Pre
            def Permit(target):
                calls.append("Gate")
                return True
        class Host:
            pass
        host = Host()
        with self.assertRaises(TagCompositionError):
            Labelled(host)
        self.assertEqual(calls, [])
        self.assertEqual(host.__dict__, {})
        self.assertNotIn(host, Labelled[:])

    def test_pin_root_is_not_a_target_or_a_form_contribution(self):
        class Labelled(Pin):
            pass
        class Shape(Labelled):
            pass
        class Ordinary(Tag):
            pass
        self.assertEqual(Form(Labelled), (Labelled,))
        self.assertEqual(Form(Shape), (Labelled, Shape))
        self.assertEqual(Form(Ordinary), (Ordinary,))
        with self.assertRaises(TagCompositionError):
            Labelled(Pin)
        with self.assertRaises(TagDeclarationError):
            Pin(Ordinary)
        with self.assertRaises(TagDeclarationError):
            Pin(Labelled)
        with self.assertRaises(TagResolutionError):
            list(Pin[:])
        self.assertEqual(len(Labelled[:]), 0)

    def test_ordinary_and_pin_bases_cannot_form_one_shape(self):
        class Ordinary(Tag):
            pass
        class Labelled(Pin):
            pass
        with self.assertRaises((TagDeclarationError, TypeError)):
            class Mixed(Ordinary, Labelled):
                pass
        with self.assertRaises((TagDeclarationError, TypeError)):
            class OtherMixed(Labelled, Ordinary):
                pass

    def test_public_base_reassignment_cannot_change_either_category(self):
        class OrdinaryBase(Tag):
            __slots__ = ()
        class LabelledBase(Pin):
            __slots__ = ()
        class Ordinary(OrdinaryBase):
            pass
        class Labelled(LabelledBase):
            pass
        for target, base in ((Ordinary, LabelledBase), (Labelled, OrdinaryBase)):
            before = type.__dict__["__bases__"].__get__(target)
            with self.subTest(target=target):
                with self.assertRaises((TagDeclarationError, TagCompositionError, TypeError)):
                    target.__bases__ = (base,)
                self.assertEqual(type.__dict__["__bases__"].__get__(target), before)
        class Target(Tag):
            pass
        self.assertIs(Labelled(Target), Target)

    def test_public_metaclass_reassignment_cannot_change_either_category(self):
        class Ordinary(Tag):
            pass
        class Labelled(Pin):
            pass
        for target, meta in ((Ordinary, type(Labelled)), (Labelled, type(Ordinary))):
            before = type(target)
            with self.subTest(target=target):
                with self.assertRaises((TagDeclarationError, TagCompositionError, TypeError)):
                    target.__class__ = meta
                self.assertIs(type(target), before)

    def test_a_custom_pin_metaclass_cannot_hide_the_native_category(self):
        reads = []
        class Mask(type(Pin)):
            def __getattribute__(cls, name):
                if name in ("__class__", "__topkit_pin__"):
                    reads.append(name)
                    return type(Tag) if name == "__class__" else False
                return super().__getattribute__(name)
        class Labelled(Pin, metaclass=Mask):
            @Record
            def label(target):
                return "labelled"
        class Target(Tag):
            pass
        identity = id(Labelled)
        self.assertIs(Labelled(Target), Target)
        self.assertEqual(id(Labelled), identity)
        self.assertEqual(Target.label, "labelled")
        self.assertEqual(reads, [])

    def test_a_presented_pin_class_does_not_turn_a_host_into_a_pin_target(self):
        reads = []
        class Host:
            @property
            def __class__(self):
                reads.append("class")
                return type(Pin)
        class Labelled(Pin):
            pass
        host = Host()
        with self.assertRaises(TagCompositionError):
            Labelled(host)
        self.assertEqual(reads, [])
        self.assertEqual(host.__dict__, {})

    def test_public_metaclass_bases_cannot_reclassify_existing_tags(self):
        class OrdinaryMeta(MetaTag):
            pass
        class RareMeta(type(Pin)):
            pass
        class Ordinary(Tag, metaclass=OrdinaryMeta):
            pass
        class Rare(Pin, metaclass=RareMeta):
            pass
        for meta, base in ((OrdinaryMeta, type(Pin)), (RareMeta, MetaTag),
                           (OrdinaryMeta, type)):
            before = type.__dict__["__bases__"].__get__(meta)
            with self.subTest(meta=meta, base=base):
                with self.assertRaises((TagDeclarationError, TypeError)):
                    meta.__bases__ = (base,)
                self.assertEqual(type.__dict__["__bases__"].__get__(meta), before)
        class Host:
            pass
        host = Host()
        self.assertIs(Ordinary(host), host)
        self.assertIs(Rare(Ordinary), Ordinary)
        self.assertIn(host, Ordinary[:])

    def test_custom_metameta_descriptor_cannot_absorb_a_category_stamp(self):
        from TopKit.geometry import _META_KIND
        from TopKit.tags import MetaPin
        calls = []
        class Trap:
            def __get__(self, instance, owner=None):
                calls.append("get")
                raise AssertionError("category must use its physical owner-bound stamp")
            def __set__(self, owner, value):
                calls.append("set")
                raise AssertionError("category must be installed before descriptor hooks")
        CustomMetaMeta = type(
            "CustomMetaMeta", (type(MetaTag),), {_META_KIND: Trap()},
        )
        class OrdinaryMeta(MetaTag, metaclass=CustomMetaMeta):
            pass
        class PinMeta(MetaPin, metaclass=CustomMetaMeta):
            pass
        class Ordinary(Tag, metaclass=OrdinaryMeta):
            pass
        class Rare(Pin, metaclass=PinMeta):
            @Record
            def label(target):
                return "marked"
        class Host:
            pass
        host = Host()
        Ordinary(host)
        self.assertIs(Rare(Ordinary), Ordinary)
        self.assertEqual(Ordinary.label, "marked")
        self.assertIn(host, Ordinary[:])
        self.assertEqual(calls, [])

    def test_new_metaclass_follows_declared_base_role_after_foreign_rebase(self):
        from TopKit.tags import MetaPin
        class ForeignMeta(type):
            pass
        class CombinedMeta(ForeignMeta, MetaTag):
            pass
        ForeignMeta.__bases__ = (MetaPin,)
        class ChildMeta(CombinedMeta):
            pass
        class Ordinary(Tag, metaclass=ChildMeta):
            pass
        class Rare(Pin):
            @Record
            def label(target):
                return "marked"
        class Host:
            pass
        host = Host()
        self.assertIs(Ordinary(host), host)
        self.assertIs(Rare(Ordinary), Ordinary)
        self.assertEqual(Ordinary.label, "marked")
        self.assertIn(host, Ordinary[:])
        with self.assertRaises(TypeError):
            Ordinary(Rare)
