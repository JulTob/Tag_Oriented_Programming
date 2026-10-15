"""A Shape's explicit Base Report link reads the Base's current value."""

import unittest

from TopKit import Constant, Pin, Public, Record, Report, Tag


class BaseReportLinkTests(unittest.TestCase):
    def test_standalone_two_parameter_report_still_builds_once(self):
        calls = []

        class Solo(Tag):
            @Report
            def answer(tag, base_value):
                calls.append(base_value)
                return len(calls)

        self.assertEqual((Solo.answer, Solo.answer), (1, 1))
        self.assertEqual(calls, [None])

    def test_live_link_reads_mutation_rebinding_and_recovers_after_failure(self):
        class Base(Tag):
            @Report
            def count(tag):
                return ["first"]

        class Shape(Base):
            @Public
            @Report
            def count(tag, base_count):
                if base_count == ["blocked"]:
                    raise ValueError("cannot count yet")
                return len(base_count)

        agent = type("Host", (), {})()
        Shape(agent)
        self.assertEqual((Shape.count, agent.count), (1, 1))

        Base.count.append("second")
        self.assertEqual((Shape.count, agent.count), (2, 2))

        Base.count = ["new", "value", "here"]
        self.assertEqual((Shape.count, agent.count), (3, 3))

        Base.count = ["blocked"]
        with self.assertRaisesRegex(ValueError, "cannot count yet"):
            _ = agent.count

        Base.count = ["repaired"]
        self.assertEqual((Shape.count, agent.count), (1, 1))

    def test_pin_changes_base_value_before_and_after_first_link_read(self):
        class Base(Tag):
            @Report
            def label(tag):
                return "start"

        class Shape(Base):
            @Report
            def label(tag, base_label):
                return f"{base_label}/shape"

        @Pin
        class First(Tag):
            @Record
            def label(tag, stored):
                return f"{stored}/first"

        @Pin
        class Second(Tag):
            @Record
            def label(tag, stored):
                return f"{stored}/second"

        self.assertEqual(Shape.label, "start/shape")
        First(Base)
        self.assertEqual((Base.label, Shape.label),
                         ("start/first", "start/first/shape"))
        Second(Base)
        self.assertEqual((Base.label, Shape.label),
                         ("start/first/second", "start/first/second/shape"))

        class OtherBase(Tag):
            @Report
            def label(tag):
                return "other"

        class OtherShape(OtherBase):
            @Report
            def label(tag, base_label):
                return f"{base_label}/shape"

        First(OtherBase)  # The Base changes before OtherShape's first read.
        self.assertEqual(OtherShape.label, "other/first/shape")

    def test_link_follows_next_base_binding_after_deletion(self):
        class Left(Tag):
            @Report
            def label(tag):
                return "left"

        class Right(Tag):
            @Report
            def label(tag):
                return "right"

        class Shape(Left, Right):
            @Report
            def label(tag, base_label):
                return base_label

        self.assertEqual(Shape.label, "left")
        del Left.label
        self.assertEqual(Shape.label, "right")
        del Right.label
        self.assertIsNone(Shape.label)

    def test_constant_link_fixes_first_success_but_other_report_builds_once(self):
        class Base(Tag):
            @Report
            def count(tag):
                return []

        linked_calls = []
        once_calls = []

        class Shape(Base):
            @Constant
            @Report
            def count(tag, base_count):
                linked_calls.append(list(base_count))
                if not base_count:
                    raise ValueError("awaiting items")
                return len(base_count)

            @Report
            def once(tag):
                once_calls.append(tag)
                return len(Base.count)

        with self.assertRaisesRegex(ValueError, "awaiting items"):
            _ = Shape.count

        Base.count.append("first")
        self.assertEqual((Shape.count, Shape.once), (1, 1))
        Base.count.append("second")
        self.assertEqual((Shape.count, Shape.once), (1, 1))
        self.assertEqual(linked_calls, [[], ["first"]])
        self.assertEqual(once_calls, [Shape])


if __name__ == "__main__":
    unittest.main()
