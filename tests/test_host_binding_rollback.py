"""Initial preparation restores physical bindings, including Python slots."""

from dataclasses import dataclass
from dataclasses import FrozenInstanceError
import unittest
import weakref
import time

from TopKit import Action, Imprint, Pre, Record, Tag, TagCompositionError, Tags


class HostBindingRollbackTests(unittest.TestCase):
    def setUp(self):
        class Role(Tag):
            @Action
            def Signal(agent):
                return "tagged"

        self.Role = Role

    def assert_unprepared(self, host, host_type):
        self.assertIs(type(host), host_type)
        self.assertEqual(Tags(host), ())
        self.assertNotIn(host, self.Role[:])
        self.assertNotIn("Signal", vars(host))

    def test_refusal_restores_replaced_deleted_and_new_slots(self):
        class Host:
            __slots__ = ("kept", "removed", "new", "__dict__", "__weakref__")

            def __setattr__(self, name, value):
                if name == "__class__":
                    object.__setattr__(self, "kept", "changed")
                    object.__delattr__(self, "removed")
                    object.__setattr__(self, "new", "provisional")
                    object.__setattr__(self, name, value)
                    raise RuntimeError("refused after changing bindings")
                object.__setattr__(self, name, value)

        host = Host()
        original = host.kept = object()
        host.removed = None
        host.ordinary = False
        watcher = weakref.ref(host)

        with self.assertRaises(TagCompositionError):
            self.Role(host)

        self.assert_unprepared(host, Host)
        self.assertIs(host.kept, original)
        self.assertIsNone(host.removed)
        with self.assertRaises(AttributeError):
            host.new
        self.assertEqual(vars(host), {"ordinary": False})
        self.assertIs(watcher(), host)

    def test_inherited_private_and_shadowed_slots_keep_distinct_bindings(self):
        class Base:
            __slots__ = ("same", "__private", "__dict__", "__weakref__")

        class Host(Base):
            __slots__ = ("same", "__private")

            def __setattr__(self, name, value):
                if name == "__class__":
                    for descriptor in descriptors:
                        descriptor.__set__(self, "changed")
                    raise RuntimeError("refused")
                object.__setattr__(self, name, value)

        descriptors = (
                Base.__dict__["same"], Base.__dict__["_Base__private"],
                Host.__dict__["same"], Host.__dict__["_Host__private"],
                )
        originals = (object(), False, None, object())
        host = Host()
        for descriptor, value in zip(descriptors, originals):
            descriptor.__set__(host, value)

        with self.assertRaises(TagCompositionError):
            self.Role(host)

        self.assert_unprepared(host, Host)
        for descriptor, value in zip(descriptors, originals):
            self.assertIs(descriptor.__get__(host), value)

    def test_replaced_dictionary_restores_its_original_identity(self):
        class Host:
            def __setattr__(self, name, value):
                if name == "__class__":
                    vars(self).clear()
                    object.__setattr__(self, "__dict__", {"provisional": 1})
                    raise RuntimeError("refused")
                object.__setattr__(self, name, value)

        host = Host()
        original_value = host.kept = object()
        original_dictionary = vars(host)

        with self.assertRaises(TagCompositionError):
            self.Role(host)

        self.assert_unprepared(host, Host)
        self.assertIs(vars(host), original_dictionary)
        self.assertEqual(vars(host), {"kept": original_value})

    def test_rollback_does_not_call_host_setters_deleters_or_properties(self):
        events = []

        class Host:
            __slots__ = ("kept", "new", "__dict__", "__weakref__")

            @property
            def unrelated(self):
                raise AssertionError("a property is not physical storage")

            def __setattr__(self, name, value):
                events.append(("set", name))
                if name == "__class__":
                    object.__setattr__(self, "kept", 0)
                    object.__setattr__(self, "new", 0)
                    raise RuntimeError("refused")
                object.__setattr__(self, name, value)

            def __delattr__(self, name):
                events.append(("delete", name))
                raise AssertionError("rollback must use native storage")

        host = Host()
        host.kept = 80
        events.clear()

        with self.assertRaises(TagCompositionError):
            self.Role(host)

        self.assert_unprepared(host, Host)
        self.assertEqual(host.kept, 80)
        self.assertEqual(events, [("set", "__class__")])
        with self.assertRaises(AttributeError):
            host.new

    def test_slotted_frozen_host_refusal_restores_field_and_dictionary(self):
        class Storage:
            def __setattr__(self, name, value):
                if name == "__class__":
                    object.__setattr__(self, "kept", 0)
                    object.__setattr__(self, "extra", "provisional")
                    raise RuntimeError("explicit host refusal")
                object.__setattr__(self, name, value)

        @dataclass(frozen=True, slots=True)
        class Host(Storage):
            kept: int = 80

        host = Host()

        with self.assertRaises(TagCompositionError):
            self.Role(host)

        self.assert_unprepared(host, Host)
        self.assertEqual(host.kept, 80)
        self.assertEqual(vars(host), {})
        with self.assertRaises(FrozenInstanceError):
            host.kept = 1

    def test_raising_subclass_hook_restores_target_slot_bindings(self):
        class Host:
            __slots__ = ("kept", "__dict__", "__weakref__")

            def __init_subclass__(cls, **kwargs):
                host.kept = "changed during class creation"
                raise RuntimeError("no runtime subclasses")

        host = Host()
        original = host.kept = object()

        with self.assertRaises(TagCompositionError):
            self.Role(host)

        self.assert_unprepared(host, Host)
        self.assertIs(host.kept, original)

    def test_rollback_keeps_mutations_inside_existing_values(self):
        effects = []

        class Host:
            __slots__ = ("kept", "__dict__", "__weakref__")

            def __setattr__(self, name, value):
                if name == "__class__":
                    self.kept.append("value mutation")
                    effects.append("external effect")
                    object.__setattr__(self, "kept", [])
                    raise RuntimeError("refused")
                object.__setattr__(self, name, value)

        host = Host()
        original = host.kept = []

        with self.assertRaises(TagCompositionError):
            self.Role(host)

        self.assert_unprepared(host, Host)
        self.assertIs(host.kept, original)
        self.assertEqual(original, ["value mutation"])
        self.assertEqual(effects, ["external effect"])

    def test_gate_precedes_host_preparation_and_refusal_prevents_gainings(self):
        events = []

        class Host:
            def __setattr__(self, name, value):
                if name == "__class__":
                    events.append("prepare")
                    raise RuntimeError("refused")
                object.__setattr__(self, name, value)

        class Role(Tag):
            @Pre
            def Gate(agent):
                events.append("gate")
                return True

            @Record
            def part(agent):
                events.append("builder")
                return 1

            @Imprint
            def Train(agent):
                events.append("imprint")

        host = Host()
        with self.assertRaises(TagCompositionError):
            Role(host)

        self.assertEqual(events, ["gate", "prepare"])
        self.assert_unprepared(host, Host)
        self.assertNotIn(host, Role[:])

    def test_interruption_retains_its_type_and_restores_slot_bindings(self):
        interruption = KeyboardInterrupt("cancel preparation")

        class Host:
            __slots__ = ("kept", "__dict__", "__weakref__")

            def __setattr__(self, name, value):
                if name == "__class__":
                    object.__setattr__(self, "kept", 0)
                    object.__setattr__(self, name, value)
                    raise interruption
                object.__setattr__(self, name, value)

        host = Host()
        host.kept = 80

        with self.assertRaises(KeyboardInterrupt) as raised:
            self.Role(host)

        self.assertIs(raised.exception, interruption)
        self.assert_unprepared(host, Host)
        self.assertEqual(host.kept, 80)

    def test_native_readonly_fields_do_not_mask_an_unsupported_host_failure(self):
        host = time.gmtime(0)
        original = tuple(host)

        with self.assertRaisesRegex(TagCompositionError, "no instance dictionary"):
            self.Role(host)

        self.assertIs(type(host), time.struct_time)
        self.assertEqual(tuple(host), original)
        self.assertEqual(Tags(host), ())
        self.assertNotIn(host, self.Role[:])


if __name__ == "__main__":
    unittest.main()
