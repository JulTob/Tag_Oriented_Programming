"""Initial preparation restores physical bindings, including Python slots."""

from dataclasses import dataclass
from dataclasses import FrozenInstanceError
import unittest
import weakref
import time

from TopKit import (Action, Flag, Imprint, Keyword, Post, Pre, Record,
                    Tag, TagCompositionError, TagImprintError,
                    TagPreconditionError, Tags)


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

    def test_completed_nested_tagging_survives_host_actualization_refusal(self):
        class Inner(Tag):
            @Record
            def value(agent):
                return 3

            @Post
            def Ready(agent):
                return agent.value == 3 and agent.kept == "inner imprint"

            @Imprint
            def Train(agent):
                agent.kept = "inner imprint"

        class Outer(Tag):
            @Record
            def unfinished(agent):
                return "never built"

        class Host:
            __slots__ = ("kept", "__dict__", "__weakref__")

            def __setattr__(self, name, value):
                if name == "__class__":
                    object.__setattr__(self, "kept", "outer preparation")
                    object.__setattr__(self, name, value)
                    Inner(self)
                    # A hostile setter may put the requested outer runtime
                    # back after Inner has already installed its Post gate.
                    object.__setattr__(self, name, value)
                    raise RuntimeError("outer refusal")
                object.__setattr__(self, name, value)

        host = Host()
        host.kept = "original"

        with self.assertRaisesRegex(TagCompositionError, "actualized in place") as raised:
            Outer(host)

        self.assertIsInstance(raised.exception.__cause__, RuntimeError)
        self.assertEqual(str(raised.exception.__cause__), "outer refusal")
        self.assertIsNot(type(host), Host)
        self.assertEqual(Tags(host), (Inner,))
        self.assertIn(host, Inner[:])
        self.assertIn(host, Inner)
        self.assertTrue(isinstance(host, Inner))
        self.assertTrue(host.Ready)
        self.assertTrue(bool(host))
        self.assertEqual(host.kept, "inner imprint")
        self.assertEqual(host.value, 3)
        self.assertNotIn(host, Outer[:])
        self.assertNotIn("unfinished", vars(host))

        host.kept = "broken"
        self.assertFalse(host.Ready)
        self.assertFalse(bool(host))
        self.assertIn(host, Inner)   # raw admission remains until Rip
        self.assertIn(host, ~Inner)
        self.assertIn(host, Inner[:])

    def test_failed_nested_imprint_keeps_its_host_write(self):
        class Inner(Tag):
            @Imprint
            def Write(agent):
                agent.kept = "inner imprint"
                raise ValueError("unfinished")

        class Outer(Tag):
            pass

        class Host:
            def __setattr__(self, name, value):
                if name == "__class__":
                    object.__setattr__(self, name, value)
                    try:
                        Inner(self)
                    except TagImprintError.Write:
                        pass
                    raise RuntimeError("outer refusal")
                object.__setattr__(self, name, value)

        host = Host()
        host.kept = "original"
        with self.assertRaises(TagCompositionError):
            Outer(host)

        self.assertIsNot(type(host), Host)
        self.assertEqual(host.kept, "inner imprint")
        self.assertNotIn(host, Inner[:])
        self.assertNotIn(host, Outer[:])

    def test_nested_gate_refusal_still_restores_unacquired_host_bindings(self):
        class Inner(Tag):
            @Pre
            def Refuse(agent):
                return False

        class Outer(Tag):
            pass

        class Host:
            def __setattr__(self, name, value):
                if name == "__class__":
                    object.__setattr__(self, "kept", "temporary")
                    object.__setattr__(self, name, value)
                    try:
                        Inner(self)
                    except TagPreconditionError.Refuse:
                        pass
                    raise RuntimeError("outer refusal")
                object.__setattr__(self, name, value)

        host = Host()
        host.kept = "original"
        with self.assertRaises(TagCompositionError):
            Outer(host)

        self.assertIs(type(host), Host)
        self.assertEqual(host.kept, "original")
        self.assertEqual(Tags(host), ())

    def test_unfinished_flag_does_not_leave_its_protocol_on_a_nested_agent(self):
        class Inner(Tag):
            @Record
            def value(agent):
                return 1

        @Flag("outer")
        class Outer(Tag):
            pass

        class Host:
            def __setattr__(self, name, value):
                if name == "__class__":
                    object.__setattr__(self, name, value)
                    Inner(self)
                    raise RuntimeError("outer refusal")
                object.__setattr__(self, name, value)

        host = Host()
        with self.assertRaises(TagCompositionError):
            Outer(host)

        self.assertIn(host, Inner[:])
        self.assertFalse(Keyword(host, "outer"))
        self.assertFalse(Keyword(host, Outer))
        with self.assertRaises(TypeError):
            "outer" in host

    def test_completed_nested_tagging_keeps_its_post_when_outer_runtime_succeeds(self):
        class Inner(Tag):
            @Record
            def value(agent):
                return 3

            @Post
            def Ready(agent):
                return agent.value == 3

        class Outer(Tag):
            pass

        turn = {"host": None, "fired": False}

        class Host:
            def __init_subclass__(cls, **kwargs):
                if not turn["fired"]:
                    turn["fired"] = True
                    Inner(turn["host"])

        host = turn["host"] = Host()
        Outer(host)

        self.assertEqual(Tags(host), (Inner, Outer))
        self.assertTrue(host.Ready)
        self.assertTrue(bool(host))
        with self.assertRaises(TagCompositionError):
            host.Ready = False
        self.assertTrue(host.Ready)


if __name__ == "__main__":
    unittest.main()
