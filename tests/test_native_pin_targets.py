"""Application categories use native identity, including each Form turn."""

import unittest

from TopKit import Action, Apply, Form, Imprint, Pin, Pre, Record, Secret, Tag
from TopKit import TagCompositionError
from TopKit.declarations import _is_pin
from TopKit.geometry import _is_tag_class
from TopKit.state import _state_of
from TopKit.tags import MetaTag


class NativePinTargetTests(unittest.TestCase):
    def test_a_spoofed_object_is_refused_by_pin_before_gate_or_state(self):
        events = []

        class Host:
            @property
            def __class__(self):
                events.append("spoof read")
                return MetaTag

            @__class__.setter
            def __class__(self, value):
                events.append("class changed")
                object.__dict__["__class__"].__set__(self, value)

        @Pin
        class Organised(Tag):
            @Pre
            def Permit(target):
                events.append("Gate")
                return True

        target = Host()
        with self.assertRaises(TagCompositionError):
            Organised(target)
        self.assertEqual(events, [])
        self.assertIs(type(target), Host)
        self.assertIsNone(_state_of(target))
        self.assertNotIn(target, Organised[:])

    def test_a_spoofed_plain_class_is_refused_without_calling_its_spoof(self):
        events = []

        class Pretend(type):
            def __getattribute__(cls, name):
                if name == "__class__":
                    events.append("spoof read")
                    return MetaTag
                return super().__getattribute__(name)

        class Plain(metaclass=Pretend):
            pass

        @Pin
        class Organised(Tag):
            @Pre
            def Permit(target):
                events.append("Gate")
                return True

        with self.assertRaises(TagCompositionError):
            Organised(Plain)
        self.assertEqual(events, [])
        self.assertIs(type(Plain), Pretend)
        self.assertIsNone(_state_of(Plain))
        self.assertNotIn(Plain, Organised[:])

    def test_an_ordinary_tag_uses_native_record_and_secret_storage(self):
        reads = []

        class Host:
            def __init__(self):
                self.amount = 7

            @property
            def __class__(self):
                reads.append("spoof read")
                return MetaTag

            @__class__.setter
            def __class__(self, value):
                object.__dict__["__class__"].__set__(self, value)

        class Ordinary(Tag):
            @Record
            def amount(agent, stored):
                return stored + 6

            @Secret
            @Record
            def code(agent):
                return "private"

            @Action
            def Inspect(agent):
                return agent.code

        target = Host()
        self.assertIs(Ordinary(target), target)
        self.assertIn(target, Ordinary[:])
        self.assertEqual(target.amount, 13)
        self.assertEqual(target.Inspect(), "private")
        self.assertEqual(reads, [])

    def test_ordinary_tag_refuses_classes_before_gate_or_state(self):
        events = []

        class Ordinary(Tag):
            @Pre
            def Permit(target):
                events.append("Gate")
                return True

        class Other(Tag):
            pass

        @Pin
        class Organised(Tag):
            pass

        class Host:
            pass

        for target in (Other, Organised, Host):
            with self.subTest(target=target), self.assertRaises(TypeError):
                Ordinary(target)
            self.assertIsNone(_state_of(target))
            self.assertNotIn(target, Ordinary[:])
        self.assertEqual(events, [])

    def test_cached_pin_form_cannot_apply_an_ordinary_base_to_a_tag(self):
        class Ordinary(Tag):
            pass

        class Shape(Ordinary):
            pass

        @Pin
        class Organised(Tag):
            pass

        class Target(Tag):
            pass

        self.assertEqual(Form(Shape), (Ordinary, Shape))
        Shape.__bases__ = (Organised,)
        with self.assertRaises(TypeError):
            Shape(Target)
        self.assertNotIn(Target, Ordinary[:])
        self.assertNotIn(Target, Shape[:])
        self.assertIsNone(_state_of(Target))

    def test_earlier_imprint_cannot_change_a_later_turn_to_pin(self):
        events = []

        @Pin
        class Organised(Tag):
            pass

        class First(Tag):
            @Imprint
            def Train(agent):
                events.append("First")
                Shape.__bases__ = (Organised,)

        class Shape(First):
            @Pre
            def Permit(agent):
                events.append("Shape Gate")
                return True

        class Host:
            pass

        target = Host()
        with self.assertRaises(TagCompositionError):
            Shape(target)
        self.assertEqual(events, ["First"])
        self.assertIn(target, First[:])
        self.assertNotIn(target, Shape[:])

    def test_gate_category_change_is_refused_before_gains(self):
        events = []

        @Pin
        class Organised(Tag):
            __slots__ = ()

        class Role(Tag):
            @Pre
            def Permit(agent):
                events.append("Gate")
                Role.__bases__ = (Organised,)
                return True

            @Record
            def amount(agent):
                events.append("Record")
                return 7

        class Host:
            pass

        target = Host()
        with self.assertRaises(TagCompositionError):
            Role(target)
        self.assertEqual(events, ["Gate"])
        self.assertIs(type(target), Host)
        self.assertIsNone(_state_of(target))
        self.assertNotIn(target, Role[:])

    def test_imprint_category_change_keeps_gains_without_admission(self):
        @Pin
        class Organised(Tag):
            __slots__ = ()

        class Role(Tag):
            @Record
            def amount(agent):
                return 7

            @Imprint
            def Train(agent):
                Role.__bases__ = (Organised,)

        class Host:
            pass

        target = Host()
        with self.assertRaises(TagCompositionError):
            Role(target)
        self.assertEqual(target.amount, 7)
        self.assertNotIn(target, Role[:])
        self.assertNotIn(Role, _state_of(target).training)

    def test_actualization_category_change_is_restored_before_builders(self):
        events = []

        @Pin
        class Organised(Tag):
            __slots__ = ()

        class Role(Tag):
            @Record
            def amount(agent):
                events.append("Record")
                return 7

        class Host:
            def __setattr__(self, name, value):
                if name == "__class__":
                    events.append("Actualize")
                    Role.__bases__ = (Organised,)
                object.__setattr__(self, name, value)

        target = Host()
        with self.assertRaises(TagCompositionError):
            Role(target)
        self.assertEqual(events, ["Actualize"])
        self.assertIs(type(target), Host)
        self.assertEqual(target.__dict__, {})
        self.assertIsNone(_state_of(target))
        self.assertNotIn(target, Role[:])

    def test_pin_preserves_populated_target_category_and_runtime_identity(self):
        class CustomMeta(MetaTag):
            pass

        class Ordinary(Tag, metaclass=CustomMeta):
            pass

        @Pin
        class Organised(Tag):
            @Record
            def label(tag):
                return "organised"

        @Pin
        class Outer(Tag):
            pass

        class Host:
            pass

        target = Host()
        Ordinary(target)
        before_identity, before_meta = id(Ordinary), type(Ordinary)
        self.assertIs(Apply(Ordinary, Organised), Ordinary)
        self.assertEqual(id(Ordinary), before_identity)
        self.assertIsNot(type(Ordinary), before_meta)
        self.assertTrue(issubclass(type(Ordinary), CustomMeta))
        self.assertTrue(_is_tag_class(Ordinary))
        self.assertFalse(_is_pin(Ordinary))
        self.assertIn(target, Ordinary[:])
        self.assertIn(Ordinary, Organised[:])
        self.assertEqual(Ordinary.label, "organised")
        self.assertIs(Outer(Organised), Organised)
        self.assertIn(Organised, Outer[:])

    def test_equal_distinct_tag_is_not_the_pins_self_or_base(self):
        class EqualMeta(MetaTag):
            def __eq__(cls, other):
                return isinstance(other, EqualMeta)

            def __hash__(cls):
                return 17

        @Pin
        class Organised(Tag, metaclass=EqualMeta):
            pass

        class Other(Tag, metaclass=EqualMeta):
            pass

        self.assertIsNot(Organised, Other)
        self.assertEqual(Organised, Other)
        self.assertIs(Organised(Other), Other)
        self.assertIn(Other, Organised[:])

    def test_real_pin_self_and_base_targets_remain_refused(self):
        @Pin
        class Organised(Tag):
            pass

        class Shape(Organised):
            pass

        for target in (Organised, Shape):
            with self.subTest(target=target), self.assertRaises(TagCompositionError):
                Shape(target)
        self.assertIsNone(_state_of(Organised))
        self.assertIsNone(_state_of(Shape))

    def test_direct_metaclass_call_refuses_plain_receiver_before_state(self):
        class Plain:
            pass

        class Host:
            pass

        target = Host()
        with self.assertRaises(TypeError):
            MetaTag.__call__(Plain, target)
        self.assertIs(type(target), Host)
        self.assertIsNone(_state_of(target))

    def test_apply_refuses_invalid_pin_turn_and_keeps_completed_tag(self):
        events = []

        class First(Tag):
            @Record
            def amount(agent):
                return 9

        class Host:
            pass

        @Pin
        class Organised(Tag):
            @Pre
            def Permit(target):
                events.append("Pin Gate")
                return True

        target = Host()
        with self.assertRaises(TagCompositionError):
            Apply(target, First, Organised)
        self.assertEqual(events, [])
        self.assertIn(target, First[:])
        self.assertEqual(target.amount, 9)
        self.assertNotIn(target, Organised[:])
