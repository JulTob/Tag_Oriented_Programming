"""Report values belong to their receiving Tags, even when values refer back."""

import gc
from concurrent.futures import ThreadPoolExecutor
from threading import Event
import unittest
import weakref

from TopKit import Constant, Pin, Record, Report, Rip, Tag, TagCompositionError
from TopKit.declarations import _Report_Value
from TopKit.memo import _memo_key, _namespace_snapshot
from TopKit.tags import MetaTag


class ReportCacheRetentionTests(unittest.TestCase):
    def test_receiving_shape_and_indirect_value_are_collectible(self):
        class Base(Tag):
            @Report
            def owner(tag):
                return [tag]

        def read_shape():
            class Shape(Base):
                pass

            value = Shape.owner
            self.assertIs(value[0], Shape)
            return weakref.ref(Shape)

        shape = read_shape()
        gc.collect()
        self.assertIsNone(shape())
        self.assertEqual(vars(Base)["owner"]._slots, {})

    def test_shape_shadow_does_not_let_base_retain_it(self):
        class Base(Tag):
            @Report
            def owner(tag):
                return tag

        def read_and_shadow():
            class Shape(Base):
                pass

            self.assertIs(Shape.owner, Shape)
            Shape.owner = "shadow"
            return weakref.ref(Shape)

        shape = read_and_shadow()
        gc.collect()
        self.assertIsNone(shape())
        self.assertIn("owner", vars(Base))

    def test_a_value_can_refer_to_its_declaring_report_and_shape(self):
        class Base(Tag):
            @Report
            def owner(tag):
                return tag, vars(Base)["owner"]

        def read_shape():
            class Shape(Base):
                pass

            value = Shape.owner
            self.assertIs(value[0], Shape)
            self.assertIs(value[1], vars(Base)["owner"])
            return weakref.ref(Shape)

        shape = read_shape()
        gc.collect()
        self.assertIsNone(shape())

    def test_live_values_are_built_once_per_tag_including_none_and_false(self):
        builds = []

        class Base(Tag):
            @Report
            def value(tag):
                builds.append(tag)
                return None if tag is Base else False

        class Shape(Base):
            pass

        self.assertIsNone(Base.value)
        self.assertIsNone(Base.value)
        self.assertIs(Shape.value, False)
        self.assertIs(Shape.value, False)
        self.assertEqual(builds, [Base, Shape])

    def test_a_report_assigned_after_class_creation_still_caches(self):
        builds = []

        class Base(Tag):
            pass

        Base.extra = Report(lambda tag: builds.append(tag) or tag)
        self.assertIs(Base.extra, Base)
        self.assertIs(Base.extra, Base)
        self.assertEqual(builds, [Base])

    def test_constant_report_uses_only_its_declaring_tag(self):
        builds = []

        class Base(Tag):
            @Constant
            @Report
            def owner(tag):
                builds.append(tag)
                return [tag]

        def read_shape():
            class Shape(Base):
                pass

            self.assertIs(Shape.owner, Base.owner)
            return weakref.ref(Shape)

        shape = read_shape()
        gc.collect()
        self.assertIsNone(shape())
        self.assertEqual(builds, [Base])

    def test_diamond_receives_one_value_without_being_owned_by_base(self):
        class Base(Tag):
            @Report
            def owners(tag):
                return {"tag": tag}

        class Left(Base):
            pass

        class Right(Base):
            pass

        def read_shape():
            class Shape(Left, Right):
                pass

            self.assertIs(Shape.owners, Shape.owners)
            self.assertIs(Shape.owners["tag"], Shape)
            return weakref.ref(Shape)

        shape = read_shape()
        gc.collect()
        self.assertIsNone(shape())

    def test_direct_replacement_and_deletion_retire_old_values(self):
        class Value:
            pass

        for change in ("replace", "delete"):
            with self.subTest(change=change):
                class Base(Tag):
                    @Report
                    def value(tag):
                        return Value()

                class Shape(Base):
                    pass

                base_value = weakref.ref(Base.value)
                shape_value = weakref.ref(Shape.value)
                if change == "replace":
                    Base.value = "new"
                    self.assertEqual(Shape.value, "new")
                else:
                    del Base.value
                    with self.assertRaises(AttributeError):
                        _ = Shape.value
                gc.collect()
                self.assertIsNone(base_value())
                self.assertIsNone(shape_value())

    def test_removing_a_shapes_own_report_keeps_its_base_report_value(self):
        class Value:
            pass

        class Base(Tag):
            @Report
            def value(tag):
                return Value()

        class Shape(Base):
            @Report
            def value(tag, prior):
                changed = Value()
                changed.prior = prior
                return changed

        changed = Shape.value
        prior = changed.prior
        changed_ref = weakref.ref(changed)
        del changed
        del Shape.value
        gc.collect()
        self.assertIsNone(changed_ref())
        self.assertIs(Shape.value, prior)

    def test_failed_pin_read_preserves_report_initialization(self):
        builds = []

        class Base(Tag):
            @Report
            def label(tag):
                value = object()
                builds.append(value)
                return value

        @Pin
        class Fails(Tag):
            @Record
            def label(tag, stored):
                self.assertIs(stored, builds[0])
                raise ValueError("unfinished")

        for _ in range(2):
            with self.assertRaises(TagCompositionError):
                Fails(Base)
        self.assertEqual(len(builds), 1)
        self.assertIs(Base.label, builds[0])

    def test_pin_original_restores_initialized_report_after_rip(self):
        builds = []

        class Base(Tag):
            @Report
            def label(tag):
                value = object()
                builds.append(value)
                return value

        original = Base.label

        @Pin
        class Patch(Tag):
            @Record
            def label(tag, stored):
                return ("patched", stored)

            @Rip
            def Restore(tag, old):
                tag.label = old.label

        Patch(Base)
        self.assertEqual(Base.label, ("patched", original))
        del Patch[Base]
        self.assertIs(Base.label, original)
        self.assertEqual(len(builds), 1)

    def test_private_slot_collision_does_not_overwrite_programmer_binding(self):
        class Base(Tag):
            @Report
            def label(tag):
                return tag

        class Shape(Base):
            pass

        report = vars(Base)["label"]
        key = _memo_key(Shape, f"REPORT_{id(report):#x}")
        setattr(Shape, key, "programmer value")
        self.assertIs(Shape.label, Shape)
        self.assertIs(Shape.label, Shape)
        self.assertEqual(vars(Shape)[key], "programmer value")
        self.assertTrue(any(type(member) is _Report_Value
                            for member in vars(Shape).values()))

    def test_retired_slot_releases_report_if_a_metaclass_blocks_its_removal(self):
        class Meta(MetaTag):
            pass

        class Base(Tag, metaclass=Meta):
            @Report
            def value(tag):
                return tag

        report = vars(Base)["value"]
        self.assertIs(Base.value, Base)
        slot = next(name for name, member in vars(Base).items()
                    if type(member) is _Report_Value)
        setattr(Meta, slot, property(lambda tag: None))

        Base.value = "changed"
        self.assertIsNone(vars(Base)[slot].report)
        old_report = weakref.ref(report)
        del report
        gc.collect()
        self.assertIsNone(old_report())

    def test_equal_comparing_tags_keep_distinct_report_values(self):
        class Equal_Meta(MetaTag):
            def __eq__(tag, other):
                return isinstance(other, Equal_Meta)

            def __hash__(tag):
                return 1

        class Base(Tag):
            @Report
            def owner(tag):
                return tag

        class First(Base, metaclass=Equal_Meta):
            pass

        class Second(Base, metaclass=Equal_Meta):
            pass

        self.assertIs(First.owner, First)
        self.assertIs(Second.owner, Second)
        self.assertIs(First.owner, First)

    def test_builder_deleting_its_report_cannot_publish_a_stale_value(self):
        class Base(Tag):
            @Report
            def value(tag):
                del Base.value
                return "old"

        self.assertEqual(Base.value, "old")
        self.assertNotIn("value", vars(Base))
        self.assertFalse(any(type(member) is _Report_Value
                             for member in vars(Base).values()))

    def test_builder_replacing_and_restoring_its_report_still_cannot_cache(self):
        calls = []

        class Base(Tag):
            @Report
            def value(tag):
                calls.append(tag)
                if len(calls) == 1:
                    original = vars(Base)["value"]
                    Base.value = "temporary"
                    Base.value = original
                return len(calls)

        self.assertEqual(Base.value, 1)
        self.assertFalse(any(type(member) is _Report_Value
                             for member in vars(Base).values()))
        self.assertEqual(Base.value, 2)
        self.assertEqual(Base.value, 2)
        self.assertEqual(calls, [Base, Base])

    def test_inflight_read_cannot_restore_a_deleted_report_cache(self):
        started = Event()
        finish = Event()

        class Base(Tag):
            @Report
            def value(tag):
                started.set()
                self.assertTrue(finish.wait(5))
                return "old"

        with ThreadPoolExecutor(max_workers=1) as pool:
            read = pool.submit(lambda: Base.value)
            self.assertTrue(started.wait(5))
            del Base.value
            finish.set()
            self.assertEqual(read.result(timeout=5), "old")
        self.assertNotIn("value", vars(Base))
        self.assertFalse(any(type(member) is _Report_Value
                             for member in vars(Base).values()))

    def test_report_cache_publication_and_namespace_scan_share_a_lock(self):
        class Base(Tag):
            @Report
            def value(tag):
                return tag

        for _ in range(80):
            class Shape(Base):
                pass

            with ThreadPoolExecutor(max_workers=2) as pool:
                read = pool.submit(lambda: Shape.value)
                scan = pool.submit(lambda: [_namespace_snapshot(Shape)
                                            for _ in range(30)])
                self.assertIs(read.result(timeout=5), Shape)
                self.assertEqual(len(scan.result(timeout=5)), 30)


if __name__ == "__main__":
    unittest.main()
