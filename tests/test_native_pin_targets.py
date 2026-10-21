"""Application categories use native identity, including each Form turn."""

import gc
from threading import Event, Thread
import unittest
import weakref

from TopKit import Action, Apply, Form, Imprint, Pin, Pre, Record, Secret, Tag
from TopKit import (TagCompositionError, TagDeclarationError, TagImprintError,
                    TagPreconditionError)
from TopKit.declarations import _is_pin
from TopKit.geometry import _is_tag_class
from TopKit.state import _state_of
from TopKit.tags import MetaPin, MetaTag


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

        class Organised(Pin):
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

        class Organised(Pin):
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

        class Organised(Pin):
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

        class Target(Tag):
            pass

        self.assertEqual(Form(Shape), (Ordinary, Shape))
        with self.assertRaises(TagDeclarationError):
            Shape.__class__ = MetaPin
        self.assertIs(type(Shape), MetaTag)
        self.assertFalse(_is_pin(Shape))
        self.assertEqual(list(Shape[:]), [])

        # Bypass the public mutation guard to retain cached-Form admission
        # coverage for an invalid Pin with an ordinary Tag in its Form.
        type.__setattr__(Shape, "__class__", MetaPin)
        with self.assertRaises(TypeError):
            Shape(Target)
        self.assertNotIn(Target, Ordinary[:])
        self.assertNotIn(Target, Shape[:])
        self.assertIsNone(_state_of(Target))

    def test_earlier_imprint_cannot_change_a_later_turn_to_pin(self):
        events = []

        class Organised(Pin):
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
        with self.assertRaises(TagImprintError.Train) as caught:
            Shape(target)
        self.assertIsInstance(caught.exception.__cause__, TagDeclarationError)
        self.assertEqual(events, ["First"])
        self.assertIs(Shape.__bases__[0], First)
        self.assertFalse(_is_pin(Shape))
        self.assertNotIn(target, First[:])
        self.assertNotIn(target, Shape[:])
        self.assertEqual(list(Organised[:]), [])

    def test_gate_category_change_is_refused_before_gains(self):
        events = []

        class Organised(Pin):
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
        with self.assertRaises(TagPreconditionError.Permit) as caught:
            Role(target)
        self.assertIsInstance(caught.exception.__cause__, TagDeclarationError)
        self.assertEqual(events, ["Gate"])
        self.assertEqual(Role.__bases__, (Tag,))
        self.assertFalse(_is_pin(Role))
        self.assertIs(type(target), Host)
        self.assertIsNone(_state_of(target))
        self.assertNotIn(target, Role[:])
        self.assertEqual(list(Organised[:]), [])

    def test_imprint_category_change_keeps_gains_without_admission(self):
        class Organised(Pin):
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
        with self.assertRaises(TagImprintError.Train) as caught:
            Role(target)
        self.assertIsInstance(caught.exception.__cause__, TagDeclarationError)
        self.assertEqual(target.amount, 7)
        self.assertEqual(Role.__bases__, (Tag,))
        self.assertFalse(_is_pin(Role))
        self.assertNotIn(target, Role[:])
        self.assertNotIn(Role, _state_of(target).training)
        self.assertEqual(list(Organised[:]), [])

    def test_actualization_category_change_is_restored_before_builders(self):
        events = []

        class Organised(Pin):
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
        with self.assertRaises(TagCompositionError) as caught:
            Role(target)
        self.assertIsInstance(caught.exception.__cause__, TagDeclarationError)
        self.assertEqual(events, ["Actualize"])
        self.assertEqual(Role.__bases__, (Tag,))
        self.assertFalse(_is_pin(Role))
        self.assertIs(type(target), Host)
        self.assertEqual(target.__dict__, {})
        self.assertIsNone(_state_of(target))
        self.assertNotIn(target, Role[:])
        self.assertEqual(list(Organised[:]), [])

    def test_pin_preserves_populated_target_category_and_runtime_identity(self):
        class CustomMeta(MetaTag):
            pass

        class Ordinary(Tag, metaclass=CustomMeta):
            pass

        class Organised(Pin):
            @Record
            def label(tag):
                return "organised"

        class Outer(Pin):
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

    def test_public_metaclass_rebase_preserves_populated_fields_and_categories(self):
        class OrdinaryMeta(MetaTag):
            pass

        class PinMeta(MetaPin):
            pass

        class Ordinary(Tag, metaclass=OrdinaryMeta):
            pass

        class Organised(Pin, metaclass=PinMeta):
            pass

        class Host:
            pass

        class Target(Tag):
            pass

        host = Host()
        Ordinary(host)
        Organised(Target)
        for meta, proposed, receiver, pinned, member in (
                (OrdinaryMeta, MetaPin, Ordinary, False, host),
                (PinMeta, MetaTag, Organised, True, Target),
                ):
            with self.subTest(receiver=receiver):
                bases, field = meta.__bases__, receiver[:]
                with self.assertRaises(TagDeclarationError):
                    meta.__bases__ = (proposed,)
                self.assertEqual(meta.__bases__, bases)
                self.assertIs(type(receiver), meta)
                self.assertIs(_is_pin(receiver), pinned)
                self.assertIs(receiver[:], field)
                self.assertEqual(list(field), [member])

    def test_public_metaclass_ancestor_rebase_cannot_change_descendant_categories(self):
        class Host:
            pass

        for original, proposed, root in (
                (MetaTag, MetaPin, Tag), (MetaPin, MetaTag, Pin),
                ):
            with self.subTest(root=root):
                class Ancestor(original):
                    pass

                class CustomMeta(Ancestor):
                    pass

                class Receiver(root, metaclass=CustomMeta):
                    pass

                member = type("Target", (Tag,), {}) if root is Pin else Host()
                Receiver(member)
                bases, field, pinned = Ancestor.__bases__, Receiver[:], _is_pin(Receiver)
                with self.assertRaises(TagDeclarationError):
                    Ancestor.__bases__ = (proposed,)
                self.assertEqual(Ancestor.__bases__, bases)
                self.assertIs(_is_pin(Receiver), pinned)
                self.assertIs(Receiver[:], field)
                self.assertEqual(list(field), [member])

    def test_public_metaclass_class_assignment_cannot_remove_category_guards(self):
        class Unchecked(type):
            pass

        class OrdinaryMeta(MetaTag):
            pass

        class PinMeta(MetaPin):
            pass

        for meta in (OrdinaryMeta, PinMeta):
            with self.subTest(meta=meta):
                before = type(meta)
                with self.assertRaises((TagDeclarationError, TypeError)):
                    meta.__class__ = Unchecked
                self.assertIs(type(meta), before)

    def test_foreign_metaclass_ancestor_rebase_does_not_change_declared_category(self):
        class ForeignMeta(type):
            pass

        class CombinedMeta(ForeignMeta, MetaTag):
            pass

        class Ordinary(Tag, metaclass=CombinedMeta):
            pass

        class Host:
            pass

        class Target(Tag):
            pass

        class Labelled(Pin):
            @Record
            def label(target):
                return "labelled"

        first, second = Host(), Host()
        Ordinary(first)
        field = Ordinary[:]
        ForeignMeta.__bases__ = (MetaPin,)
        self.assertTrue(issubclass(CombinedMeta, MetaPin))
        self.assertTrue(_is_tag_class(Ordinary))
        self.assertFalse(_is_pin(Ordinary))
        self.assertIs(Ordinary[:], field)
        self.assertEqual(list(field), [first])
        with self.assertRaises(TypeError):
            Ordinary(Target)
        self.assertIsNone(_state_of(Target))
        self.assertNotIn(Target, field)
        self.assertIs(Ordinary(second), second)
        self.assertEqual(list(field), [first, second])

        self.assertIs(Labelled(Ordinary), Ordinary)
        self.assertEqual(Ordinary.label, "labelled")
        self.assertFalse(_is_pin(Ordinary))
        self.assertIs(Ordinary[:], field)
        self.assertEqual(list(field), [first, second])

        class NewOrdinary(Tag, metaclass=CombinedMeta):
            pass

        third = Host()
        self.assertFalse(_is_pin(NewOrdinary))
        self.assertIs(NewOrdinary(third), third)
        self.assertEqual(list(NewOrdinary[:]), [third])

    def test_foreign_metaclass_rebase_does_not_make_a_plain_class_a_pin_target(self):
        events = []

        class ForeignMeta(type):
            pass

        class Plain(metaclass=ForeignMeta):
            pass

        class Labelled(Pin):
            @Pre
            def Permit(target):
                events.append("Gate")
                return True

        class Host:
            pass

        ForeignMeta.__bases__ = (MetaTag,)
        self.assertFalse(_is_tag_class(Plain))
        self.assertFalse(_is_pin(Plain))
        with self.assertRaises(TagCompositionError):
            Labelled(Plain)
        with self.assertRaises(TypeError):
            Plain(Host())
        self.assertEqual(events, [])
        self.assertIsNone(_state_of(Plain))
        self.assertEqual(list(Labelled[:]), [])

    def test_copied_category_stamp_cannot_authenticate_foreign_classes(self):
        from TopKit.geometry import _META_KIND

        class Labelled(Pin):
            pass

        for original in (MetaTag, MetaPin):
            with self.subTest(original=original):
                events = []

                class ForeignCategory(type):
                    pass

                class ForeignMeta(type, metaclass=ForeignCategory):
                    pass

                class Plain(metaclass=ForeignMeta):
                    pass

                # Deliberately copy the physical slot, then adopt both the
                # native ancestry and guard: the stamp still belongs elsewhere.
                setattr(ForeignMeta, _META_KIND, vars(original)[_META_KIND])
                ForeignMeta.__bases__ = (original,)
                ForeignMeta.__class__ = type(original)
                self.assertFalse(_is_tag_class(Plain))
                self.assertFalse(_is_pin(Plain))
                with self.assertRaises(TagCompositionError):
                    Labelled(Plain)
                self.assertIsNone(_state_of(Plain))
                self.assertEqual(list(Labelled[:]), [])

                class Member:
                    def __set_name__(self, owner, name):
                        events.append("descriptor")

                class HostBase:
                    def __init_subclass__(cls):
                        events.append("subclass")

                member = Member()
                namespace = {"member": member}
                with self.assertRaises(TagDeclarationError):
                    MetaTag.__new__(ForeignMeta, "Forged", (HostBase,), namespace)
                self.assertEqual(namespace, {"member": member})
                self.assertEqual(events, [])
                self.assertEqual(HostBase.__subclasses__(), [])

    def test_owned_category_stamp_cannot_be_rebound_or_mutated(self):
        from TopKit.geometry import _META_KIND

        class CustomMeta(MetaTag):
            pass

        stamp = vars(CustomMeta)[_META_KIND]
        kind, owner = stamp.kind, stamp.owner
        with self.assertRaises(TypeError):
            stamp.__set_name__(MetaPin, _META_KIND)
        with self.assertRaises(TypeError):
            stamp.__init__(object())
        for name in ("kind", "owner"):
            with self.subTest(name=name):
                with self.assertRaises(AttributeError):
                    setattr(stamp, name, None)
                with self.assertRaises(AttributeError):
                    delattr(stamp, name)
        self.assertIs(stamp.kind, kind)
        self.assertIs(stamp.owner, owner)
        self.assertIs(stamp.owner(), CustomMeta)

    def test_category_stamp_does_not_retain_custom_metaclasses_or_declarations(self):
        def references(meta_base, root):
            class CustomMeta(meta_base):
                pass

            class Declaration(root, metaclass=CustomMeta):
                pass

            return weakref.ref(CustomMeta), weakref.ref(Declaration)

        for meta_base, root in ((MetaTag, Tag), (MetaPin, Pin)):
            with self.subTest(root=root):
                meta_ref, declaration_ref = references(meta_base, root)
                gc.collect()
                gc.collect()
                self.assertIsNone(meta_ref())
                self.assertIsNone(declaration_ref())

    def test_reordered_category_stamp_lookup_does_not_call_colliding_key_hooks(self):
        from TopKit.geometry import _META_KIND, _metaclass_kind

        armed, calls = False, []

        class Name(str):
            def __hash__(self):
                if armed:
                    calls.append("hash")
                    raise AssertionError("category lookup called a stored key")
                return hash(_META_KIND)

            def __eq__(self, other):
                if armed:
                    calls.append("equality")
                    raise AssertionError("category lookup compared a stored key")
                return str.__eq__(self, other)

        for meta_base, root in ((MetaTag, Tag), (MetaPin, Pin)):
            with self.subTest(root=root):
                armed = False
                meta = type(meta_base)("CustomMeta", (meta_base,), {Name("noise"): None})
                receiver = meta("Receiver", (root,), {})
                kind, stamp = _metaclass_kind(meta), vars(meta)[_META_KIND]
                # Deliberately bypass the protected-slot setter to exercise
                # the fallback for an owned stamp outside the first slot.
                type.__delattr__(meta, _META_KIND)
                type.__setattr__(meta, _META_KIND, stamp)
                self.assertIsNot(next(iter(vars(meta))), _META_KIND)
                calls.clear()
                armed = True
                for _ in range(10):
                    self.assertIs(_metaclass_kind(meta), kind)
                    self.assertTrue(_is_tag_class(receiver))
                    self.assertIs(_is_pin(receiver), root is Pin)
                self.assertEqual(calls, [])

    def test_concurrent_metaclass_namespace_updates_preserve_kind_recognition(self):
        from TopKit.geometry import _metaclass_kind

        class OrdinaryMeta(MetaTag):
            pass

        class PinMeta(MetaPin):
            pass

        class Ordinary(Tag, metaclass=OrdinaryMeta):
            pass

        class Organised(Pin, metaclass=PinMeta):
            pass

        started, stop = Event(), Event()
        failures = []
        expected = [(meta, receiver, _metaclass_kind(meta), pinned) for meta, receiver, pinned in (
                (OrdinaryMeta, Ordinary, False), (PinMeta, Organised, True),
                )]

        def update():
            try:
                value = 0
                while not stop.is_set():
                    for meta, _receiver, _kind, _pinned in expected:
                        meta.noise = value
                        meta.temporary = value
                        del meta.temporary
                    started.set()
                    value += 1
            except BaseException as error:
                failures.append(error)

        worker = Thread(target=update, daemon=True)
        worker.start()
        try:
            self.assertTrue(started.wait(2))
            for _ in range(2000):
                for meta, receiver, kind, pinned in expected:
                    self.assertIs(_metaclass_kind(meta), kind)
                    self.assertTrue(_is_tag_class(receiver))
                    self.assertIs(_is_pin(receiver), pinned)
        finally:
            stop.set()
            worker.join(2)
        self.assertFalse(worker.is_alive())
        self.assertEqual(failures, [])

    def test_equal_distinct_tag_is_not_the_pins_self_or_base(self):
        class Equal:
            def __eq__(cls, other):
                return isinstance(other, Equal)

            def __hash__(cls):
                return 17

        class EqualMeta(Equal, MetaTag):
            pass

        class EqualPinMeta(Equal, MetaPin):
            pass

        class Organised(Pin, metaclass=EqualPinMeta):
            pass

        class Other(Tag, metaclass=EqualMeta):
            pass

        self.assertIsNot(Organised, Other)
        self.assertEqual(Organised, Other)
        self.assertIs(Organised(Other), Other)
        self.assertIn(Other, Organised[:])

    def test_real_pin_self_and_base_targets_remain_refused(self):
        class Organised(Pin):
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

        class Organised(Pin):
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
