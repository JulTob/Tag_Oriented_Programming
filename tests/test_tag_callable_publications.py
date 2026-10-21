"""Tag publications use their declaration names, not callable metadata."""

from inspect import signature
from types import MethodType
import unittest

from TopKit import Constant, Operation, Public, Report, Rip, Tag
from TopKit import TagDeclarationError


class Host:
    pass


class Hostile:
    def __init__(self):
        self.reads = []
        self.calls = []

    def __getattribute__(self, name):
        if name in ("__name__", "__qualname__", "__doc__", "__dict__",
                    "__signature__"):
            object.__getattribute__(self, "reads").append(name)
            raise AssertionError(f"optional metadata read: {name}")
        return object.__getattribute__(self, name)

    def __repr__(self):
        raise AssertionError("optional repr read")

    def __call__(self, tag, agent=None, value=7):
        self.calls.append((tag, agent, value))
        return tag, agent, value


class TagCallablePublicationTests(unittest.TestCase):
    def test_report_builder_needs_no_python_name_or_documentation(self):
        builder = Hostile()

        class Crew(Tag):
            score = Public(Report(builder))

        member = Host()
        Crew(member)
        self.assertEqual(Crew.score, (Crew, None, 7))
        self.assertEqual(member.score, (Crew, None, 7))
        self.assertEqual(Crew[member].score, (Crew, None, 7))
        self.assertEqual(builder.calls, [(Crew, None, 7)])
        self.assertEqual(builder.reads, [])
        self.assertEqual(vars(Crew)["score"]._name, "score")

    def test_operation_retains_callable_and_ordinary_binding(self):
        operation = Hostile()

        class Crew(Tag):
            score = Public(Operation(operation))

        member = Host()
        Crew(member)
        declaration = vars(Crew)["score"]
        self.assertIs(declaration.__func__, operation)
        self.assertIs(Crew.score.__func__, operation)
        self.assertIs(Crew.score.__self__, Crew)
        self.assertEqual(Crew.score(value=2), (Crew, None, 2))
        self.assertEqual(member.score(3), (Crew, member, 3))
        self.assertEqual(Crew[member].score(4), (Crew, member, 4))
        # Existing public-call adapters may ask for optional documentation;
        # that failure remains harmless. Names and signatures are not needed.
        self.assertEqual(set(operation.reads), {"__doc__"})

    def test_operation_modifier_orders_on_the_declaring_tag(self):
        before = Hostile()
        after = Hostile()

        class Base(Tag):
            first = Constant(Operation(before))
            second = Operation(Constant(after))

        self.assertEqual(Base.first(), (Base, None, 7))
        self.assertEqual(Base.second(), (Base, None, 7))
        self.assertEqual(before.reads, [])
        self.assertEqual(after.reads, [])

    def test_public_before_operation_and_rip_validation_see_original(self):
        operation = Hostile()

        class Crew(Tag):
            score = Operation(Public(operation))

        member = Host()
        Crew(member)
        self.assertEqual(member.score(5), (Crew, member, 5))
        self.assertIs(vars(Crew)["score"].__func__, operation)

        with self.assertRaises(TagDeclarationError):
            type("Invalid", (Tag,), {"score": Rip(Operation(Hostile()))})

    def test_plain_callable_operation_keeps_bound_python_introspection(self):
        class Calculate:
            """Calculated result from a callable object."""

            def __call__(self, tag, value=7, *, scale=1):
                return tag, value * scale

        operation = Calculate()

        class Crew(Tag):
            score = Operation(operation)

        descriptor = vars(Crew)["score"]
        self.assertEqual(descriptor.__name__, "score")
        self.assertIs(descriptor.__func__, operation)
        self.assertIs(descriptor.__wrapped__, operation)
        self.assertEqual(descriptor.__doc__, Calculate.__doc__)
        self.assertIs(Crew.score.__self__, Crew)
        self.assertIs(Crew.score.__func__, operation)
        self.assertEqual(signature(Crew.score),
                         signature(MethodType(operation, Crew)))
        self.assertEqual(Crew.score(4, scale=3), (Crew, 12))

    def test_callable_descriptor_keeps_native_classmethod_binding(self):
        class Bind:
            def __call__(self, tag, value):
                return "direct", value

            def __get__(self, instance, owner):
                return lambda value: ("descriptor", value)

        baseline = Bind()
        decorated = Bind()

        class Native:
            work = classmethod(baseline)

        class Crew(Tag):
            work = Operation(decorated)

        self.assertEqual(Crew.work(9), Native.work(9))
        self.assertIs(vars(Crew)["work"].__wrapped__, decorated)

    def test_plain_function_publications_keep_existing_metadata(self):
        def builder(tag):
            """A documented Report."""
            return 10

        def work(tag):
            """A documented Operation."""
            return tag

        class Crew(Tag):
            score = Report(builder)
            Work = Operation(work)

        self.assertEqual(Crew.score, 10)
        self.assertIs(type(vars(Crew)["Work"]), classmethod)
        self.assertIs(vars(Crew)["Work"].__func__, work)
        self.assertEqual(vars(Crew)["score"].__name__, "builder")
        self.assertEqual(vars(Crew)["score"].__doc__, builder.__doc__)
        self.assertIs(Crew.Work.__func__, work)


if __name__ == "__main__":
    unittest.main()
