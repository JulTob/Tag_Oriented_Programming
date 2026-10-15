"""Public Pin handles retain the callable and the bound Python signature."""

from functools import partial
from inspect import signature
from types import MethodType
import unittest

from TopKit import Action, Pin, Record, Secret, Tag


class PinnedOperationIntrospectionTests(unittest.TestCase):
    def receiver(self, function):
        @Pin
        class Patch(Tag):
            Work = Action(function)

        class Target(Tag):
            pass

        Patch(Target)
        return Patch, Target

    def test_public_function_handle_retains_bound_metadata_and_signature(self):
        def calculate(tag, value: int = 7, /, *, suffix: str = "") -> tuple:
            """Calculate with a fixed receiver."""
            return tag, value, suffix

        _, target = self.receiver(calculate)
        handle = target.Work

        self.assertIs(handle.__self__, target)
        self.assertIs(handle.__func__, calculate)
        self.assertEqual(signature(handle), signature(MethodType(calculate, target)))
        self.assertEqual(str(signature(handle)),
                         "(value: int = 7, /, *, suffix: str = '') -> tuple")
        self.assertEqual(handle(11, suffix="!"), (target, 11, "!"))
        self.assertEqual(handle.__name__, "calculate")
        self.assertEqual(handle.__doc__, calculate.__doc__)
        self.assertFalse(hasattr(handle, "__wrapped__"))

    def test_a_shape_needs_its_own_pin_to_receive_an_operation(self):
        def calculate(tag, value=7):
            return tag, value

        _, target = self.receiver(calculate)

        class Shape(target):
            pass

        with self.assertRaises(AttributeError):
            Shape.Work

        @Pin
        class ShapeWork(Tag):
            Work = Action(calculate)

        ShapeWork(Shape)

        for receiver in (target, Shape):
            with self.subTest(receiver=receiver):
                handle = receiver.Work
                self.assertIs(handle.__self__, receiver)
                self.assertIs(handle.__func__, calculate)
                self.assertEqual(signature(handle),
                                 signature(MethodType(calculate, receiver)))
                self.assertEqual(handle(13), (receiver, 13))

    def test_partial_and_callable_object_retain_their_bound_signatures(self):
        def calculate(tag, value=7, *, suffix=""):
            return tag, value, suffix

        class Calculator:
            def __call__(self, tag, value=7, *, suffix=""):
                return tag, value, suffix

        for function in (partial(calculate, suffix="!"), Calculator()):
            with self.subTest(kind=type(function)):
                _, target = self.receiver(function)
                handle = target.Work
                self.assertIs(handle.__self__, target)
                self.assertIs(handle.__func__, function)
                self.assertEqual(signature(handle),
                                 signature(MethodType(function, target)))
                self.assertEqual(handle(17, suffix="?"), (target, 17, "?"))

    def test_signature_metadata_is_read_only_when_introspection_is_requested(self):
        class Calculator:
            def __init__(self):
                self.inspections = 0

            @property
            def __signature__(self):
                self.inspections += 1
                raise RuntimeError("unavailable signature")

            def __call__(self, tag, value=7):
                return tag, value

        function = Calculator()
        _, target = self.receiver(function)
        handle = target.Work
        self.assertEqual(handle(19), (target, 19))
        self.assertEqual(function.inspections, 0)
        self.assertIs(handle.__self__, target)
        self.assertIs(handle.__func__, function)

        with self.assertRaisesRegex(RuntimeError, "unavailable signature"):
            signature(handle)
        self.assertEqual(function.inspections, 1)
        self.assertEqual(handle(23), (target, 23))

    def test_earlier_public_capture_still_opens_composition_after_first_secret(self):
        def read(tag, *, suffix=""):
            return tag.code + suffix

        _, target = self.receiver(read)
        handle = target.Work
        expected = signature(MethodType(read, target))

        @Pin
        class Private(Tag):
            @Secret
            @Record
            def code(tag):
                return "private"

        Private(target)
        self.assertIs(handle.__self__, target)
        self.assertIs(handle.__func__, read)
        self.assertEqual(signature(handle), expected)
        self.assertEqual(handle(suffix="!"), "private!")
        with self.assertRaises(AttributeError):
            target.code


if __name__ == "__main__":
    unittest.main()
