"""Refused tagging restores the receiver's Fields, including their order.

The destructive Gates below are adversarial probes, not authoring examples.
"""

import gc
import unittest
import weakref
from unittest.mock import patch

from TopKit import (Action, Imprint, Pin, Post, Pre, Record, Secret, Tag,
                    TagCompositionError, TagPostconditionError,
                    TagPreconditionError, Tags)


class Host:
    pass


class FieldRestorationTests(unittest.TestCase):
    def test_refused_gate_restores_multiple_fields_and_their_partitions(self):
        class Existing(Tag):
            @Record
            def badge(agent):
                return "original"

            @Post
            def Ready(agent):
                return agent.ready

        class Other(Tag):
            pass

        class Refused(Tag):
            @Pre
            def Refuse(agent):
                del Existing[agent]
                del Other[agent]
                agent.badge = "changed"
                return False

        first, receiver, last = Host(), Host(), Host()
        for agent, ready in ((first, True), (receiver, True), (last, False)):
            agent.ready = ready
            try:
                Existing(agent)
            except TagPostconditionError.Ready:
                self.assertFalse(ready)
        for agent in (last, receiver, first):
            try:
                Other(agent)
            except TagPostconditionError.Ready:
                self.assertFalse(agent.ready)
        original_type = type(receiver)

        with self.assertRaises(TagPreconditionError.Refuse):
            Refused(receiver)

        self.assertEqual(list(Existing[:]), [first, receiver, last])
        self.assertEqual(list(Other[:]), [last, receiver, first])
        self.assertEqual(list(Existing), [first, receiver])
        self.assertEqual(list(~Existing), [last])
        self.assertEqual(list(Existing[:] & Other[:]), [first, receiver, last])
        self.assertIn(receiver, Existing)
        self.assertEqual(Tags(receiver), (Existing, Other))
        self.assertIs(type(receiver), original_type)
        self.assertEqual(receiver.badge, "original")
        self.assertEqual(Existing[receiver].badge, "original")
        self.assertFalse(isinstance(receiver, Refused))

    def test_raising_record_restores_the_original_entry_after_rip_and_reapply(self):
        builds = []

        class Existing(Tag):
            @Record
            def serial(agent):
                builds.append("built")
                return len(builds)

        class Introduced(Tag):
            pass

        class Refused(Tag):
            @Record
            def item(agent):
                del Existing[agent]
                Existing(agent)
                Introduced(agent)
                raise RuntimeError("refuse Parts")

        first, receiver, last = Host(), Host(), Host()
        for agent in (first, receiver, last):
            Existing(agent)
        original_type = type(receiver)

        with self.assertRaises(TagCompositionError):
            Refused(receiver)

        self.assertEqual(list(Existing[:]), [first, receiver, last])
        self.assertEqual(receiver.serial, 2)
        self.assertEqual(Existing[receiver].serial, 2)
        self.assertEqual(Tags(receiver), (Existing,))
        self.assertIs(type(receiver), original_type)
        self.assertFalse(isinstance(receiver, Introduced))
        self.assertEqual(list(Introduced[:]), [])
        self.assertEqual(builds, ["built"] * 4)

    def test_restoring_the_receiver_preserves_other_agents_joins_and_removals(self):
        class Existing(Tag):
            pass

        first, receiver, removed, last, joined = (Host() for _ in range(5))
        for agent in (first, receiver, removed, last):
            Existing(agent)

        class Refused(Tag):
            @Pre
            def Refuse(agent):
                del Existing[agent]
                del Existing[removed]
                Existing(joined)
                return False

        with self.assertRaises(TagPreconditionError.Refuse):
            Refused(receiver)

        self.assertEqual(list(Existing[:]), [first, receiver, last, joined])
        self.assertNotIn(removed, Existing)
        self.assertTrue(isinstance(removed, Existing))
        self.assertIn(joined, Existing)

    def test_gc_finalizer_changes_survive_field_rebuilding(self):
        class Existing(Tag):
            pass

        first, receiver, last, joined = (Host() for _ in range(4))
        for agent in (first, receiver, last):
            Existing(agent)

        class Collected:
            def __del__(agent):
                Existing(joined)
                del Existing[first]

        class Refused(Tag):
            @Pre
            def Refuse(agent):
                del Existing[agent]
                return False

        real_sorted = sorted

        def collect_then_sort(*args, **kwargs):
            # Schedule real finalization while restoration constructs its
            # replacement. Production allocations can trigger the same GC.
            gc.collect()
            return real_sorted(*args, **kwargs)

        was_enabled = gc.isenabled()
        gc.disable()
        try:
            collected = Collected()
            collected.cycle = collected
            Existing(collected)
            reference = weakref.ref(collected)
            del collected

            with patch("TopKit.fields.sorted", collect_then_sort, create=True):
                with self.assertRaises(TagPreconditionError.Refuse):
                    Refused(receiver)

            self.assertIsNone(reference())
            self.assertIn(joined, Existing)
            self.assertNotIn(first, Existing)
            self.assertEqual(list(Existing[:]), [receiver, last, joined])
        finally:
            if was_enabled:
                gc.enable()

    def test_the_whole_form_gate_refuses_before_parts_write_or_new_membership(self):
        events = []
        at_gate = []

        class Existing(Tag):
            @Record
            def badge(agent):
                return "original"

        class Base(Tag):
            @Pre
            def BaseGate(agent):
                events.append("base gate")
                return True

            @Record
            def built(agent):
                events.append("parts")
                return True

            @Imprint
            def Train(agent):
                events.append("write")

        class Shape(Base):
            @Pre
            def ShapeGate(agent):
                events.append("shape gate")
                at_gate.append((Tags(agent), agent in Base[:],
                                agent in Shape[:], hasattr(agent, "built")))
                agent.temporary = True
                return False

        receiver = Host()
        Existing(receiver)
        original_type = type(receiver)
        with self.assertRaises(TagPreconditionError.ShapeGate):
            Shape(receiver)

        self.assertEqual(events, ["base gate", "shape gate"])
        self.assertEqual(at_gate, [((Existing,), False, False, False)])
        self.assertEqual(Tags(receiver), (Existing,))
        self.assertEqual(list(Existing[:]), [receiver])
        self.assertEqual(list(Base[:]), [])
        self.assertEqual(list(Shape[:]), [])
        self.assertIs(type(receiver), original_type)
        self.assertFalse(isinstance(receiver, Base))
        self.assertFalse(isinstance(receiver, Shape))
        self.assertFalse(hasattr(receiver, "temporary"))
        self.assertFalse(hasattr(receiver, "built"))
        self.assertEqual(receiver.badge, "original")

    def test_later_parts_failure_restores_existing_fields_and_removes_the_prefix(self):
        class Existing(Tag):
            pass

        class Base(Tag):
            @Record
            def new_badge(agent):
                return "built"

        class Shape(Base):
            @Record
            def item(agent):
                del Existing[agent]
                raise RuntimeError("refuse later Parts")

        first, receiver, last = Host(), Host(), Host()
        for agent in (first, receiver, last):
            Existing(agent)
        with self.assertRaises(TagCompositionError):
            Shape(receiver)

        self.assertEqual(list(Existing[:]), [first, receiver, last])
        self.assertEqual(Tags(receiver), (Existing,))
        self.assertEqual(list(Base[:]), [])
        self.assertEqual(list(Shape[:]), [])
        self.assertFalse(isinstance(receiver, Base))
        self.assertFalse(hasattr(receiver, "new_badge"))

    def test_restoration_keeps_an_open_composition_door_and_closes_it_afterward(self):
        class Existing(Tag):
            @Secret
            @Record
            def badge(agent):
                return "secret"

            @Action
            def Check(agent):
                try:
                    Refused(agent)
                except TagPreconditionError.Refuse:
                    return agent.badge

        class Refused(Tag):
            @Pre
            def Refuse(agent):
                del Existing[agent]
                return False

        receiver = Host()
        Existing(receiver)
        self.assertEqual(receiver.Check(), "secret")
        self.assertEqual(list(Existing[:]), [receiver])
        with self.assertRaises(AttributeError):
            receiver.badge

    def test_a_refused_pin_restores_the_pinned_tags_original_field_position(self):
        @Pin
        class Existing(Tag):
            @Record
            def badge(tag):
                return "original"

        @Pin
        class Refused(Tag):
            @Pre
            def Refuse(tag):
                del Existing[tag]
                return False

        first, receiver, last = (
                type(name, (Tag,), {})
                for name in ("First", "Receiver", "Last")
                )
        for tag in (first, receiver, last):
            Existing(tag)
        with self.assertRaises(TagPreconditionError.Refuse):
            Refused(receiver)

        self.assertEqual(list(Existing[:]), [first, receiver, last])
        self.assertEqual(Tags(receiver), (Existing,))
        self.assertEqual(Existing[receiver].badge, "original")
        self.assertFalse(isinstance(receiver, Refused))

    def test_restored_field_members_remain_weak_after_handled_refusal(self):
        class Existing(Tag):
            pass

        class Refused(Tag):
            @Pre
            def Refuse(agent):
                del Existing[agent]
                return False

        def attempt():
            receiver = Host()
            reference = weakref.ref(receiver)
            Existing(receiver)
            try:
                Refused(receiver)
            except TagPreconditionError.Refuse:
                pass
            self.assertEqual(list(Existing[:]), [receiver])
            return reference

        was_enabled = gc.isenabled()
        gc.disable()
        try:
            reference = attempt()
            self.assertIsNone(reference())
            self.assertEqual(list(Existing[:]), [])
        finally:
            if was_enabled:
                gc.enable()
