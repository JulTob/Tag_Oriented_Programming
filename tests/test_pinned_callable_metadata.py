"""Optional callable metadata must not prevent a landed Pin Action call."""

from functools import partial
import unittest

from TopKit import Action, Pin, Record, Secret, Tag


_MISSING = object()


class CallableAction:
    def __init__(self, name=_MISSING, doc=_MISSING):
        self.metadata = {"__name__": name, "__doc__": doc}
        self.calls = []

    def __getattribute__(self, name):
        if name in ("__name__", "__doc__"):
            value = object.__getattribute__(self, "metadata")[name]
            if value is _MISSING:
                raise AttributeError(name)
            if isinstance(value, BaseException):
                raise value
            return value
        return object.__getattribute__(self, name)

    def __call__(self, tag, value=7, *, suffix=""):
        self.calls.append((tag, value, suffix))
        return tag, value, suffix


def calculate(tag, value=7, *, suffix=""):
    return tag, value, suffix


class PinnedCallableMetadataTests(unittest.TestCase):
    def callables(self):
        implementation = partial(calculate)
        yield "partial", implementation, "Work", implementation.__doc__
        yield "missing", CallableAction(), "Work", None
        yield "missing doc", CallableAction("Implementation"), "Implementation", None
        yield ("raising doc", CallableAction("Implementation", RuntimeError("doc")),
               "Implementation", None)
        yield ("raising", CallableAction(LookupError("name"),
                                         RuntimeError("doc")), "Work", None)
        yield "invalid name", CallableAction(None, "kept doc"), "Work", "kept doc"
        yield ("available", CallableAction("Implementation", "original doc"),
               "Implementation", "original doc")

    def receiver(self, function, *, secret_record=False, secret_action=False):
        work = Action(function)
        if secret_action:
            work = Secret(work)

        @Pin
        class Patch(Tag):
            Work = work

            @Action
            def Capture(tag, view=False):
                return Patch[tag].Work if view else tag.Work

            @Action
            def Invoke(tag, handle, value=7, *, suffix=""):
                return handle(value, suffix=suffix)

        class Target(Tag):
            pass

        if secret_record:
            @Pin
            class Private(Tag):
                @Secret
                @Record
                def code(tag):
                    return "private"

            Private(Target)

        Patch(Target)
        return Patch, Target

    def test_public_calls_and_captures_ignore_missing_or_invalid_metadata(self):
        for secret_record in (False, True):
            for label, function, name, doc in self.callables():
                with self.subTest(secret_record=secret_record, metadata=label):
                    patch, target = self.receiver(function,
                                                  secret_record=secret_record)
                    direct = target.Work
                    view = patch[target].Work
                    self.assertEqual(direct.__name__, name)
                    self.assertEqual(direct.__doc__, doc)
                    for handle in (direct, view, target.Capture(),
                                   target.Capture(view=True)):
                        self.assertEqual(handle(11, suffix="!"),
                                         (target, 11, "!"))
                    self.assertTrue("Work" @ target)
                    self.assertTrue("Work" @ patch[target])
                    if secret_record:
                        with self.assertRaises(AttributeError):
                            target.code

    def test_partial_capture_before_the_first_secret_still_composes(self):
        def read(tag):
            return tag.code

        @Pin
        class Reader(Tag):
            Read = Action(partial(read))

        @Pin
        class Private(Tag):
            @Secret
            @Record
            def code(tag):
                return "private"

        class Target(Tag):
            pass

        Reader(Target)
        direct = Target.Read
        view = Reader[Target].Read
        self.assertEqual(direct.__name__, "Read")
        Private(Target)
        for handle in (direct, view, Target.Read, Reader[Target].Read):
            self.assertEqual(handle(), "private")
            with self.assertRaises(AttributeError):
                Target.code

    def test_secret_captures_keep_their_guard_with_callable_metadata_fallbacks(self):
        for label, function, name, doc in self.callables():
            with self.subTest(metadata=label):
                patch, target = self.receiver(function, secret_action=True)
                with self.assertRaises(AttributeError):
                    target.Work
                with self.assertRaises(AttributeError):
                    patch[target].Work
                self.assertFalse("Work" @ target)
                self.assertFalse("Work" @ patch[target])

                direct = target.Capture()
                view = target.Capture(view=True)
                self.assertEqual(direct.__name__, name)
                self.assertEqual(direct.__doc__, doc)
                for handle in (direct, view):
                    with self.assertRaises(AttributeError):
                        handle()
                    self.assertEqual(target.Invoke(handle, 13, suffix="?"),
                                     (target, 13, "?"))
                    self.assertEqual(patch[target].Invoke(handle, 17, suffix="."),
                                     (target, 17, "."))
                    with self.assertRaises(AttributeError):
                        handle()

    def test_function_metadata_is_preserved_under_a_different_declaration_name(self):
        def Implementation(tag, value=7, *, suffix=""):
            """An existing function's documentation."""
            return tag, value, suffix

        for secret_action in (False, True):
            with self.subTest(secret_action=secret_action):
                _, target = self.receiver(Implementation,
                                          secret_action=secret_action)
                handle = target.Capture()
                self.assertEqual(handle.__name__, "Implementation")
                self.assertEqual(handle.__doc__, Implementation.__doc__)
                self.assertFalse(hasattr(handle, "__wrapped__"))
                self.assertEqual(target.Invoke(handle), (target, 7, ""))
                self.assertEqual(Implementation.__name__, "Implementation")

    def test_body_failures_propagate_unchanged_and_close_composition(self):
        for error in (LookupError("body"), KeyboardInterrupt(), SystemExit(7)):
            with self.subTest(error=type(error).__name__):
                def fail(tag):
                    self.assertEqual(tag.code, "private")
                    raise error

                patch, target = self.receiver(partial(fail), secret_record=True)
                for handle in (target.Work, patch[target].Work):
                    with self.assertRaises(type(error)) as caught:
                        handle()
                    self.assertIs(caught.exception, error)
                    with self.assertRaises(AttributeError):
                        target.code

    def test_metadata_interrupts_are_not_silenced(self):
        for attribute in ("__name__", "__doc__"):
            for error in (KeyboardInterrupt(), SystemExit(9)):
                with self.subTest(attribute=attribute, error=type(error).__name__):
                    values = {"name": "Implementation", "doc": "documentation"}
                    values["name" if attribute == "__name__" else "doc"] = error
                    function = CallableAction(**values)
                    _, target = self.receiver(function, secret_record=True)
                    with self.assertRaises(type(error)) as caught:
                        target.Work
                    self.assertIs(caught.exception, error)
                    self.assertEqual(function.calls, [])
                    with self.assertRaises(AttributeError):
                        target.code


if __name__ == "__main__":
    unittest.main()
