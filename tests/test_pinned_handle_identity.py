"""Public Pin handles preserve bound-method comparison and key behavior."""

from types import MethodType
import unittest

from TopKit import Action, Pin, Record, Secret, Tag, TagOverwriteWarning


class PinnedHandleIdentityTests(unittest.TestCase):
    def receiver(self, function):
        @Pin
        class Patch(Tag):
            Work = Action(function)

        class Target(Tag):
            pass

        Patch(Target)
        return Target

    def test_repeated_reads_and_native_methods_share_equality_and_hash(self):
        def Work(tag):
            return tag

        target = self.receiver(Work)
        first, second = target.Work, target.Work
        native = MethodType(Work, target)

        self.assertIsNot(first, second)
        self.assertEqual(first, second)
        self.assertEqual(first, native)
        self.assertEqual(native, first)
        self.assertEqual(hash(first), hash(second))
        self.assertEqual(hash(first), hash(native))
        self.assertEqual(len({first, second, native}), 1)
        self.assertEqual({first: "registered"}[second], "registered")
        self.assertEqual({native: "native"}[first], "native")
        self.assertEqual({first: "TOP"}[native], "TOP")

    def test_receiving_shapes_and_replacement_actions_remain_distinct(self):
        def Work(tag):
            return "original", tag

        target = self.receiver(Work)

        class Shape(target):
            pass

        original = target.Work
        self.assertNotEqual(original, Shape.Work)
        self.assertEqual(original, target.Work)

        @Pin
        class Replacement(Tag):
            @Action
            def Work(tag):
                return "replacement", tag

        with self.assertWarns(TagOverwriteWarning):
            Replacement(target)
        self.assertNotEqual(original, target.Work)
        self.assertEqual(original(), ("original", target))
        self.assertEqual(target.Work(), ("replacement", target))

    def test_equal_callable_objects_follow_native_function_equality(self):
        class Calculator:
            def __eq__(self, other):
                return isinstance(other, Calculator)

            def __hash__(self):
                return 17

            def __call__(self, tag):
                return tag

        first, second = Calculator(), Calculator()
        target = self.receiver(first)
        other = MethodType(second, target)
        self.assertIsNot(first, second)
        self.assertEqual(target.Work, other)
        self.assertEqual(other, target.Work)
        self.assertEqual(hash(target.Work), hash(other))

    def test_hashing_an_unhashable_callable_matches_python_without_breaking_calls(self):
        class Calculator:
            __hash__ = None

            def __call__(self, tag):
                return tag

        function = Calculator()
        target = self.receiver(function)
        handle = target.Work
        self.assertEqual(handle, target.Work)
        for value in (handle, MethodType(function, target)):
            with self.subTest(kind=type(value)):
                with self.assertRaises(TypeError):
                    hash(value)
        self.assertIs(handle(), target)

    def test_unrelated_operands_follow_normal_reflected_comparison(self):
        def Work(tag):
            return tag

        handle = self.receiver(Work).Work

        class Reflected:
            def __eq__(self, other):
                return other is handle

        self.assertIs(handle.__eq__(object()), NotImplemented)
        self.assertEqual(handle, Reflected())
        self.assertNotEqual(handle, object())
        self.assertNotEqual(handle, None)

    def test_identity_and_repr_do_not_inspect_optional_callable_metadata(self):
        class Calculator:
            def __init__(self):
                self.closed = False

            def __getattribute__(self, name):
                if name in ("__name__", "__doc__", "__signature__", "__qualname__"):
                    if object.__getattribute__(self, "closed"):
                        raise AssertionError("identity inspected callable metadata")
                    raise AttributeError(name)
                return object.__getattribute__(self, name)

            def __call__(self, tag):
                return tag

        function = Calculator()
        target = self.receiver(function)
        first, second = target.Work, target.Work
        function.closed = True
        self.assertEqual(first, second)
        self.assertEqual(hash(first), hash(second))
        self.assertEqual(repr(first), "<pinned Operation Work of Target>")
        self.assertIs(first(), target)

    def test_representation_names_the_function_and_receiving_shape(self):
        def Calculate(tag):
            return tag

        target = self.receiver(Calculate)

        class Shape(target):
            pass

        self.assertEqual(repr(target.Work), "<pinned Operation Calculate of Target>")
        self.assertEqual(repr(Shape.Work), "<pinned Operation Calculate of Shape>")

    def test_handle_keys_survive_first_secret_and_close_composition_after_call(self):
        def Work(tag):
            return tag.code

        target = self.receiver(Work)
        early = target.Work
        before = hash(early)
        handlers = {early: "registered"}

        @Pin
        class Private(Tag):
            @Secret
            @Record
            def code(tag):
                return "private"

        Private(target)
        self.assertEqual(early, target.Work)
        self.assertEqual(hash(early), before)
        self.assertEqual(handlers[target.Work], "registered")
        self.assertEqual(early(), "private")
        self.assertEqual(target.Work(), "private")
        with self.assertRaises(AttributeError):
            target.code


if __name__ == "__main__":
    unittest.main()
