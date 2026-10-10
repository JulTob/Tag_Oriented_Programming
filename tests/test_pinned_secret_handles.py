"""Secret Pin Operations require their pinned Tag's existing composition."""

import gc
import unittest
import weakref

from TopKit import (Action, Constant, Pin, Pre, Record, Secret, Tag,
                    TagCompositionError, TagPreconditionError)


class PinnedSecretHandleTests(unittest.TestCase):
    def test_captured_secret_and_constant_secret_operations_require_authority(self):
        for constant in (False, True):
            with self.subTest(constant=constant):
                def Read(tag, suffix=""):
                    """Read the Pin-private code."""
                    return tag, tag.code + suffix

                declaration = Secret(Action(Read))
                if constant:
                    declaration = Constant(declaration)

                @Pin
                class Private(Tag):
                    Read = declaration

                    @Secret
                    @Record
                    def code(tag):
                        return "private"

                    @Action
                    def Capture(tag):
                        return tag.Read

                    @Action
                    def Invoke(tag, operation):
                        return operation(suffix=" authorized")

                class Target(Tag):
                    pass

                Private(Target)
                operation = Target.Capture()

                self.assertEqual(operation.__name__, "Read")
                self.assertEqual(operation.__doc__, "Read the Pin-private code.")
                with self.assertRaises(AttributeError):
                    operation()
                receiver, value = Target.Invoke(operation)
                self.assertIs(receiver, Target)
                self.assertEqual(value, "private authorized")
                with self.assertRaises(AttributeError):
                    operation()
                self.assert_closed(Target, "Read", "code")

    def test_a_pure_secret_body_is_guarded_without_a_secret_record_dependency(self):
        @Pin
        class Private(Tag):
            @Secret
            @Action
            def Read(tag):
                return "private"

            @Action
            def Capture(tag):
                return tag.Read

        class Target(Tag):
            pass

        Private(Target)
        operation = Target.Capture()
        with self.assertRaises(AttributeError):
            operation()
        self.assert_closed(Target, "Read")

    def test_another_pinned_tags_door_does_not_authorize_the_operation(self):
        @Pin
        class Private(Tag):
            @Secret
            @Action
            def Read(tag):
                return tag

            @Action
            def Capture(tag):
                return tag.Read

            @Action
            def Invoke(tag, operation):
                return operation()

        class Target(Tag):
            pass

        class Other(Tag):
            pass

        Private(Target)
        Private(Other)
        operation = Target.Capture()

        with self.assertRaises(AttributeError):
            Other.Invoke(operation)
        self.assertIs(Target.Invoke(operation), Target)
        self.assert_closed(Target, "Read")
        self.assert_closed(Other, "Read")

    def test_different_pins_on_the_same_target_share_the_targets_authority(self):
        @Pin
        class Private(Tag):
            @Secret
            @Action
            def Read(tag):
                return tag

            @Action
            def Capture(tag):
                return tag.Read

        @Pin
        class Caller(Tag):
            @Action
            def Invoke(tag, operation):
                return operation()

        class Target(Tag):
            pass

        Private(Target)
        operation = Target.Capture()
        Caller(Target)

        self.assertIs(Target.Invoke(operation), Target)
        with self.assertRaises(AttributeError):
            operation()

    def test_rip_and_reapplication_keep_the_captured_operation_secret(self):
        for constant in (False, True):
            with self.subTest(constant=constant):
                def Read(tag):
                    return tag

                declaration = Secret(Action(Read))
                if constant:
                    declaration = Constant(declaration)

                @Pin
                class Private(Tag):
                    Read = declaration

                    @Action
                    def Capture(tag):
                        return tag.Read

                    @Action
                    def Invoke(tag, operation):
                        return operation()

                class Target(Tag):
                    pass

                Private(Target)
                operation = Target.Capture()
                del Private[Target]

                self.assertIs(Target.Invoke(operation), Target)
                with self.assertRaises(AttributeError):
                    operation()
                Private(Target)
                self.assertIs(Target.Invoke(operation), Target)
                with self.assertRaises(AttributeError):
                    operation()
                self.assert_closed(Target, "Read")

    def test_public_shadow_and_its_deletion_do_not_authorize_a_secret_capture(self):
        @Pin
        class Private(Tag):
            @Secret
            @Action
            def Read(tag):
                return "private"

            @Action
            def Capture(tag):
                return tag.Read

            @Action
            def Invoke(tag, operation):
                return operation()

        class Target(Tag):
            pass

        Private(Target)
        operation = Target.Capture()
        Target.Read = classmethod(lambda tag: "public")

        self.assertEqual(Target.Read(), "public")
        self.assertEqual(Target.Invoke(operation), "private")
        with self.assertRaises(AttributeError):
            operation()

        del Target.Read                           # deletes the public class-namespace shadow
        self.assertEqual(Target.Invoke(operation), "private")
        with self.assertRaises(AttributeError):
            operation()
        self.assert_closed(Target, "Read")

    def test_a_constant_secret_operation_refuses_a_public_class_shadow(self):
        @Pin
        class Private(Tag):
            @Secret
            @Constant
            @Action
            def Read(tag):
                return "private"

            @Action
            def Capture(tag):
                return tag.Read

        class Target(Tag):
            pass

        Private(Target)
        operation = Target.Capture()
        with self.assertRaises(TagCompositionError):
            Target.Read = classmethod(lambda tag: "public")
        with self.assertRaises(AttributeError):
            operation()
        self.assert_closed(Target, "Read")

    def test_a_refused_pinning_preserves_authority_for_the_same_target(self):
        @Pin
        class Refused(Tag):
            @Pre
            def No(tag):
                return False

        @Pin
        class Private(Tag):
            @Secret
            @Action
            def Read(tag):
                return tag

            @Action
            def Capture(tag):
                return tag.Read

            @Action
            def Try(tag, operation):
                try:
                    Refused(tag)
                except TagPreconditionError.No:
                    return operation()

        class Target(Tag):
            pass

        Private(Target)
        operation = Target.Capture()

        self.assertIs(Target.Try(operation), Target)
        with self.assertRaises(AttributeError):
            operation()
        self.assert_closed(Target, "Read")

    def test_secret_operation_failure_preserves_only_the_callers_open_door(self):
        for error in (LookupError("stop"), KeyboardInterrupt(), SystemExit(7)):
            with self.subTest(error=type(error).__name__):
                @Pin
                class Private(Tag):
                    @Secret
                    @Record
                    def code(tag):
                        return "private"

                    @Secret
                    @Action
                    def Fail(tag):
                        self.assertEqual(tag.code, "private")
                        raise error

                    @Action
                    def Capture(tag):
                        return tag.Fail

                    @Action
                    def Continue(tag, operation):
                        try:
                            operation()
                        except type(error) as caught:
                            self.assertIs(caught, error)
                            return tag.code

                class Target(Tag):
                    pass

                Private(Target)
                operation = Target.Capture()

                self.assertEqual(Target.Continue(operation), "private")
                try:
                    operation()
                except BaseException as raised:
                    self.assertIsInstance(raised, AttributeError)
                else:
                    self.fail("the captured Secret operation ran outside composition")
                self.assert_closed(Target, "Fail", "code")

    def test_captured_pin_operation_keeps_its_existing_strong_receiver_ownership(self):
        @Pin
        class Private(Tag):
            @Secret
            @Action
            def Read(tag):
                return "private"

            @Action
            def Capture(tag):
                return tag.Read

        class Target(Tag):
            pass

        Private(Target)
        operation = Target.Capture()
        reference = weakref.ref(Target)
        del Target
        gc.collect()

        self.assertIsNotNone(reference())
        del operation
        gc.collect()
        self.assertIsNone(reference())

    def test_a_pin_field_without_a_captured_operation_still_holds_targets_weakly(self):
        @Pin
        class Private(Tag):
            @Secret
            @Action
            def Read(tag):
                return "private"

        class Target(Tag):
            pass

        Private(Target)
        reference = weakref.ref(Target)
        del Target
        gc.collect()
        self.assertIsNone(reference())
        self.assertEqual([tag for tag in Private[:]], [])

    def assert_closed(self, target, *names):
        for name in names:
            with self.assertRaises(AttributeError):
                getattr(target, name)
            self.assertFalse(name @ target)


if __name__ == "__main__":
    unittest.main()
