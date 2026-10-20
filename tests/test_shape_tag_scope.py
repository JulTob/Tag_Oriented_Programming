"""A Shape applies its Bases without owning their shared members."""

import unittest
from unittest.mock import patch

from TopKit import Action, Constant, Operation, Pin, Public, Record, Report, Secret, Tag
from TopKit import TagCompositionError, Underlay


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
        self.assertEqual(Shape[agent].Name(), "Base")

    def test_metaclass_data_descriptor_keeps_python_lookup_precedence(self):
        from TopKit.tags import MetaTag

        class Meta(MetaTag):
            @property
            def colour(tag):
                return "metaclass"

        class Base(Tag):
            @Report
            def colour(tag):
                return "base"

        class Shape(Base, metaclass=Meta):
            pass

        self.assertEqual(Shape.colour, "metaclass")

        @Pin
        class Mark(Tag):
            pass

        Mark(Shape)
        self.assertTrue("colour" @ Shape)

    def test_a_shapes_own_report_can_explicitly_extend_a_bases_value(self):
        built_for = []

        class Base(Tag):
            @Report
            def traits(tag):
                built_for.append(tag)
                return [tag.__name__]

        class Shape(Base):
            @Report
            def traits(tag, base_value):
                return base_value + ["armoured"]

            @Operation
            def Name(tag):
                return tag.__name__

        self.assertEqual(Shape.traits, ["Base", "armoured"])
        self.assertEqual(Base.traits, ["Base"])
        self.assertEqual(built_for, [Base])
        self.assertEqual(Shape.Name(), "Shape")

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

    def test_a_constant_base_member_is_hidden_but_still_uncrushable(self):
        class Base(Tag):
            @Constant
            @Report
            def code(tag):
                return "fixed"

            @Constant
            @Operation
            def Act(tag):
                return tag.__name__

        class Shape(Base):
            pass

        self.assertEqual((Base.code, Base.Act()), ("fixed", "Base"))
        for name in ("code", "Act"):
            self.assertFalse(hasattr(Shape, name))
            with self.assertRaises(TagCompositionError):
                setattr(Shape, name, None)
            with self.assertRaises(TagCompositionError):
                delattr(Shape, name)

    def test_pin_gains_belong_to_the_tag_the_pin_actualizes(self):
        @Pin
        class Shared(Tag):
            @Record
            def label(tag):
                return None

            @Action
            def Name(tag):
                return tag.__name__

        class Base(Tag):
            pass

        Shared(Base)

        class Shape(Base):
            pass

        self.assertIsNone(Base.label)  # None is a present Report value.
        self.assertTrue("label" @ Base)
        self.assertEqual(Base.Name(), "Base")
        self.assertFalse(hasattr(Shape, "label"))
        self.assertFalse("label" @ Shape)
        self.assertFalse(hasattr(Shape, "Name"))

        @Pin
        class ShapeOwn(Tag):
            @Record
            def own_label(tag):
                return "Shape"

            @Action
            def OwnName(tag):
                return tag.__name__

        ShapeOwn(Shape)
        self.assertEqual((Shape.own_label, Shape.OwnName()), ("Shape", "Shape"))
        self.assertFalse(hasattr(Base, "own_label"))
        self.assertFalse(hasattr(Base, "OwnName"))

    def test_ordinary_replacements_of_pin_gains_inherit_normally(self):
        @Pin
        class Patch(Tag):
            @Record
            def label(tag):
                return "pin"

            @Action
            def Name(tag):
                return "pin"

        class Base(Tag):
            pass

        Patch(Base)

        class Before(Base):
            pass

        self.assertFalse(hasattr(Before, "label"))
        self.assertFalse(hasattr(Before, "Name"))

        Base.label = "plain"
        Base.Name = classmethod(lambda tag: tag.__name__)

        class After(Base):
            pass

        self.assertEqual(Before.label, "plain")
        self.assertEqual(Before.Name(), "Before")
        self.assertEqual(After.label, "plain")
        self.assertEqual(After.Name(), "After")

        # A deliberate assignment is a new Python binding even if it
        # happens to reuse the Pin's original value object.
        class Same(Tag):
            pass

        Patch(Same)
        original = Same.label
        Same.label = original

        class SameShape(Same):
            pass

        self.assertIs(SameShape.label, original)

    def test_inherited_ordinary_classmethod_does_not_read_callable_metadata(self):
        class Unmarked:
            def __getattr__(self, name):
                if name == "__topkit_kind__":
                    raise RuntimeError("metadata must not be evaluated")
                raise AttributeError(name)

            def __call__(self, tag):
                return tag.__name__

        class Base(Tag):
            pass

        Base.Host = classmethod(Unmarked())

        class Shape(Base):
            pass

        self.assertEqual(Shape.Host(), "Shape")

    def test_marked_callable_operation_stays_on_its_declaring_tag(self):
        class CallableOperation:
            def __call__(self, tag):
                return tag.__name__

        class Base(Tag):
            Name = Operation(CallableOperation())

        class Shape(Base):
            pass

        self.assertEqual(Base.Name(), "Base")
        self.assertFalse(hasattr(Shape, "Name"))

    def test_aliases_are_own_names_without_scanning_the_class_dictionary(self):
        report = Report(lambda tag: "base")
        operation = Operation(lambda tag: "base")

        class Base(Tag):
            first = report
            other = report
            First = operation
            Other = operation

        class Shape(Base):
            pass

        self.assertEqual((Base.first, Base.other), ("base", "base"))
        self.assertEqual((Base.First(), Base.Other()), ("base", "base"))
        for name in ("first", "other", "First", "Other"):
            self.assertFalse(hasattr(Shape, name))

        del Base.other
        del Base.Other
        self.assertEqual((Base.first, Base.First()), ("base", "base"))

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

    def test_reused_declarations_keep_publication_and_constant_protection(self):
        report = Constant(Public(Report(lambda tag: tag.__name__)))
        operation = Constant(Public(Operation(lambda tag, agent=None: tag.__name__)))

        class Base(Tag):
            label = report
            Act = operation

        class Shape(Base):
            own_label = report
            OwnAct = operation

        agent = type("Host", (), {})()
        Shape(agent)
        self.assertEqual((agent.label, agent.own_label), ("Base", "Shape"))
        self.assertEqual((agent.Act(), agent.OwnAct()), ("Base", "Shape"))
        for tag, name in ((Base, "label"), (Base, "Act"),
                          (Shape, "own_label"), (Shape, "OwnAct")):
            with self.assertRaises(TagCompositionError):
                delattr(tag, name)

    def test_reusing_a_report_preserves_its_descriptor_subclass(self):
        class Specialized(Report):
            def __get__(self, instance, owner=None):
                return ("special", super().__get__(instance, owner))

        report = Specialized(lambda tag: tag.__name__)

        class Base(Tag):
            first = report

        class Shape(Base):
            second = report

        self.assertEqual(Base.first, ("special", "Base"))
        self.assertEqual(Shape.second, ("special", "Shape"))
        self.assertFalse(hasattr(Shape, "first"))

    def test_marked_classmethod_subclass_stays_on_its_declaring_tag(self):
        class Specialized(classmethod):
            pass

        marked = Operation(lambda tag: tag.__name__)

        class Base(Tag):
            Name = Specialized(marked.__func__)

        class Shape(Base):
            pass

        self.assertEqual(Base.Name(), "Base")
        self.assertFalse(hasattr(Shape, "Name"))

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

    def test_a_pinned_shape_answers_presence_from_its_own_scope(self):
        class Base(Tag):
            @Report
            def colour(tag):
                return "blue"

            @Operation
            def Act(tag):
                return tag.__name__

            plain = "Python"

        class Shape(Base):
            pass

        @Pin
        class Mark(Tag):
            pass

        Mark(Shape)

        self.assertFalse("colour" @ Shape)
        self.assertFalse("Act" @ Shape)
        self.assertTrue("plain" @ Shape)
        self.assertFalse(hasattr(Shape, "colour"))
        self.assertFalse(hasattr(Shape, "Act"))

    def test_an_own_secret_pin_gain_outranks_a_base_report(self):
        class Base(Tag):
            @Report
            def key(tag):
                return "base"

            @Operation
            def Read(tag):
                return "base"

        class Shape(Base):
            pass

        @Pin
        class Private(Tag):
            @Secret
            @Record
            def key(tag):
                return "shape"

            @Secret
            @Action
            def Read(tag):
                return "shape"

            @Action
            def Probe(tag):
                return tag.key, "key" @ tag, tag.Read(), "Read" @ tag

        Private(Shape)
        self.assertEqual(Shape.Probe(), ("shape", True, "shape", True))
        self.assertFalse("key" @ Shape)
        self.assertFalse("Read" @ Shape)
        self.assertEqual((Base.key, Base.Read()), ("base", "base"))

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

    def test_late_operation_and_ordinary_replacement_update_shape_scope(self):
        class Base(Tag):
            pass

        class Shape(Base):
            pass

        Base.Name = Operation(lambda tag: tag.__name__)
        self.assertEqual(Base.Name(), "Base")
        self.assertFalse(hasattr(Shape, "Name"))

        Base.label = Report(lambda tag: tag.__name__)
        self.assertEqual(Base.label, "Base")
        self.assertFalse(hasattr(Shape, "label"))

        del Base.Name
        Base.Name = classmethod(lambda tag: tag.__name__)
        self.assertEqual(Shape.Name(), "Shape")

        del Base.label
        Base.label = "plain"
        self.assertEqual(Shape.label, "plain")

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

    def test_failed_secret_pin_restores_a_bases_report_visibility(self):
        from TopKit import overlay

        class Base(Tag):
            @Report
            def label(tag):
                return "base"

        class Shape(Base):
            pass

        @Pin
        class Patch(Tag):
            @Secret
            @Record
            def label(tag):
                return "private"

        original_store = overlay._store_record

        def interrupted_store(*args):
            original_store(*args)
            raise RuntimeError("after the class binding changed")

        with patch.object(overlay, "_store_record", interrupted_store):
            with self.assertRaisesRegex(RuntimeError, "class binding"):
                Patch(Base)

        self.assertEqual(Base.label, "base")
        self.assertFalse(hasattr(Shape, "label"))



if __name__ == "__main__":
    unittest.main()
