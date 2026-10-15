"""A Shape applies its Bases without owning their shared members."""

import unittest

from TopKit import Action, Operation, Pin, Public, Record, Report, Tag, Underlay


class ShapeTagScopeTests(unittest.TestCase):
    def test_a_shape_does_not_read_a_bases_report_or_operation_directly(self):
        class HostMixin:
            host_value = "ordinary Python inheritance"

            @classmethod
            def HostMethod(cls):
                return cls.__name__

        class Base(Tag):
            plain_value = "also inherited"

            @classmethod
            def PlainMethod(cls):
                return cls.__name__

            @Report
            def colour(tag):
                return "blue"

            @Operation
            def Name(tag):
                return tag.__name__

        class Shape(HostMixin, Base):
            pass

        self.assertEqual((Base.colour, Base.Name()), ("blue", "Base"))
        self.assertFalse(hasattr(Shape, "colour"))
        self.assertFalse(hasattr(Shape, "Name"))
        self.assertEqual(Shape.host_value, "ordinary Python inheritance")
        self.assertEqual(Shape.HostMethod(), "Shape")
        self.assertEqual(Shape.plain_value, "also inherited")
        self.assertEqual(Shape.PlainMethod(), "Shape")

        class HostColour:
            colour = "host member"

        class HostFirst(HostColour, Base):
            pass

        self.assertEqual(HostFirst.colour, "host member")

        agent = type("Host", (), {})()
        Shape(agent)
        self.assertEqual(Base[agent].colour, "blue")
        self.assertEqual(Shape[agent].colour, "blue")
        self.assertEqual(Shape[agent].Name(), "Base")

    def test_a_shape_applies_the_bases_published_members_to_its_agent(self):
        class Base(Tag):
            @Public
            @Report
            def colour(tag):
                return "blue"

            @Public
            @Operation
            def Name(tag, agent):
                return tag.__name__

        class Shape(Base):
            pass

        agent = type("Host", (), {})()
        Shape(agent)

        self.assertFalse(hasattr(Shape, "colour"))
        self.assertFalse(hasattr(Shape, "Name"))
        self.assertEqual((agent.colour, agent.Name()), ("blue", "Base"))
        self.assertEqual((Base[agent].colour, Base[agent].Name()),
                         ("blue", "Base"))

    def test_reusing_a_base_descriptor_under_a_shape_name_does_not_reveal_old_name(self):
        report = Report(lambda tag: tag.__name__)
        operation = Operation(lambda tag: tag.__name__)

        class Base(Tag):
            first = report
            First = operation

        class Shape(Base):
            second = report
            Second = operation

        self.assertEqual((Base.first, Base.First()), ("Base", "Base"))
        self.assertEqual((Shape.second, Shape.Second()), ("Shape", "Shape"))
        self.assertFalse(hasattr(Shape, "first"))
        self.assertFalse(hasattr(Shape, "First"))

        Shape.third = Base.__dict__["first"]
        Shape.Third = Base.__dict__["First"]
        self.assertEqual((Shape.third, Shape.Third()), ("Shape", "Shape"))
        self.assertFalse(hasattr(Shape, "first"))
        self.assertFalse(hasattr(Shape, "First"))

        Shape.fourth = Shape.__dict__["third"]
        Shape.Fourth = Shape.__dict__["Third"]
        self.assertEqual((Shape.fourth, Shape.Fourth()), ("Shape", "Shape"))

    def test_marked_classmethod_receives_its_python_set_name_callback(self):
        bindings = []

        class Bound(classmethod):
            def __set_name__(self, owner, name):
                bindings.append((owner, name))
                self.owning_tag = owner
                self.name = name

            def __get__(self, instance, owner=None):
                return (self.owning_tag.__name__, self.name,
                        super().__get__(instance, owner)())

        marked = Operation(lambda tag: tag.__name__)

        class Base(Tag):
            Name = Bound(marked.__func__)

        class Shape(Base):
            pass

        self.assertEqual(bindings, [(Base, "Name")])
        self.assertEqual(Base.Name, ("Base", "Name", "Base"))
        self.assertFalse(hasattr(Shape, "Name"))
        self.assertEqual(bindings, [(Base, "Name")])

    def test_pin_stored_input_does_not_use_a_base_report(self):
        built_for = []

        class Base(Tag):
            @Report
            def label(tag):
                built_for.append(tag)
                return tag.__name__

        class Shape(Base):
            pass

        @Pin
        class Patch(Tag):
            @Record
            def label(tag, stored):
                return f"{tag.__name__}:{stored}"

        Patch(Shape)

        self.assertEqual(Shape.label, "Shape:None")
        self.assertEqual(built_for, [])
        self.assertEqual(Base.label, "Base")
        self.assertEqual(built_for, [Base])

    def test_shape_report_link_reads_a_pinned_base_value(self):
        class Base(Tag):
            @Report
            def label(tag):
                return "original"

        class Shape(Base):
            @Report
            def label(tag, base):
                return f"{base}-shape"

        @Pin
        class Patch(Tag):
            @Record
            def label(tag, stored):
                return "red"

        Patch(Base)
        self.assertEqual(Base.label, "red")
        self.assertEqual(Shape.label, "red-shape")

    def test_pin_action_underlay_on_shape_calls_null_not_base_operation(self):
        class Base(Tag):
            @Operation
            def Work(tag):
                return "Base"

        class Shape(Base):
            pass

        @Pin
        class Patch(Tag):
            @Underlay
            @Action
            def Work(tag, prior):
                return prior()

        Patch(Shape)
        self.assertEqual(Base.Work(), "Base")
        self.assertIsNone(Shape.Work())

    def test_pin_changes_the_shapes_report_without_moving_its_agent_overlay(self):
        class Base(Tag):
            @Public
            @Report
            def label(tag):
                return "base"

        class Shape(Base):
            @Public
            @Report
            def label(tag):
                return "shape"

        class Extra(Tag):
            @Public
            @Report
            def label(tag):
                return "extra"

        agent = type("Host", (), {})()
        Shape(agent)
        Extra(agent)
        self.assertEqual(agent.label, "extra")

        @Pin
        class Patch(Tag):
            @Record
            def label(tag, stored):
                return f"{stored}-patched"

        Patch(Shape)
        self.assertEqual((Base.label, Shape.label), ("base", "shape-patched"))
        self.assertEqual(agent.label, "extra")


if __name__ == "__main__":
    unittest.main()
