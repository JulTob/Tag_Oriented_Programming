"""Callable Contributions need no Python function names or signature patch."""

from functools import partial
from inspect import Parameter, Signature
import unittest

from TopKit import Action, Imprint, Pin, Post, Pre, Record, Rip, Tag
from TopKit import TagCompositionError, TagDeclarationError, TagImprintError
from TopKit import TagResolutionError, Underlay
from TopKit.declarations import _parameters_of, _wraps_callable


class Host:
    pass


class _Hostile:
    def __init__(self):
        self.metadata_reads = []

    def __getattribute__(self, name):
        if name in ("__name__", "__qualname__", "__dict__"):
            object.__getattribute__(self, "metadata_reads").append(name)
            raise AssertionError("optional callable name was read")
        return object.__getattribute__(self, name)

    def __repr__(self):
        raise AssertionError("callable repr was read")


class _Fail(_Hostile):
    def __init__(self, original, events):
        super().__init__()
        self.original = original
        self.events = events

    def __call__(self, agent):
        self.events.append("first")
        raise self.original


class _Extend(_Hostile):
    def __call__(self, agent, prior):
        return prior()


class _One(_Hostile):
    def __call__(self, agent):
        return True


class _Stored(_Hostile):
    def __call__(self, agent, stored):
        return stored


def _target(pinned):
    return type("Receiver", (Tag,), {}) if pinned else Host()


class CallableSignatureMetadataTests(unittest.TestCase):
    def test_callable_kind_does_not_read_an_optional_instance_class(self):
        class HostileClass(_Hostile):
            @property
            def __class__(self):
                raise AssertionError("optional callable class was read")

            def __call__(self, agent):
                return True

        callable_object = HostileClass()
        self.assertEqual(_parameters_of(callable_object).named[0][0], "agent")

        @_wraps_callable(callable_object)
        def Wrapper(agent):
            return callable_object(agent)

        self.assertIs(Wrapper.__wrapped__, callable_object)
        self.assertTrue(Wrapper(Host()))
        self.assertEqual(callable_object.metadata_reads, [])

    def test_failing_rips_keep_the_original_and_save_later_teardowns(self):
        for pinned in (False, True):
            with self.subTest(pinned=pinned):
                events = []
                original = RuntimeError("original cleanup failure")
                failing = _Fail(original, events)

                def Later(agent):
                    events.append("later")

                closing = type("Closing", (Tag,), {
                        "First": Rip(failing), "Later": Rip(Later),
                        })
                if pinned:
                    closing = Pin(closing)
                target = _target(pinned)
                closing(target)

                with self.assertRaises(TagCompositionError) as caught:
                    del closing[target]

                self.assertIs(caught.exception.__cause__, original)
                self.assertEqual(str(caught.exception), "Closing teardown failed in: First; the Agent is arrested")
                self.assertEqual(events, ["first"])
                self.assertEqual(failing.metadata_reads, [])

    def test_failing_imprint_and_record_keep_declared_names_and_causes(self):
        for pinned in (False, True):
            for mark in (Imprint, Record):
                with self.subTest(pinned=pinned, mark=mark):
                    events = []
                    original = RuntimeError("original calculation failure")
                    failing = _Fail(original, events)
                    role = type("Role", (Tag,), {"Training": mark(failing)})
                    if pinned:
                        role = Pin(role)
                    target = _target(pinned)
                    failure = (
                            TagImprintError.Training
                            if mark is Imprint else TagCompositionError
                            )

                    with self.assertRaises(failure) as caught:
                        role(target)

                    self.assertIs(caught.exception.__cause__, original)
                    self.assertIn("Training", str(caught.exception))
                    self.assertEqual(events, ["first"])
                    self.assertEqual(failing.metadata_reads, [])
                    self.assertNotIn(target, role[:])

    def test_valid_action_and_condition_underlays_never_read_names(self):
        for pinned in (False, True):
            for mark in (Action, Pre, Post):
                with self.subTest(pinned=pinned, mark=mark):
                    extending = _Extend()
                    calls = []

                    def Check(agent):
                        calls.append(agent)
                        return True

                    base = type("Base", (Tag,), {
                            "Work": mark(Check),
                            })
                    if pinned:
                        base = Pin(base)
                    shape = type("Shape", (base,), {
                            "Work": mark(Underlay(extending)),
                            })
                    target = _target(pinned)

                    shape(target)
                    self.assertIn(target, shape[:])
                    if mark is Pre:
                        self.assertEqual(calls, [target, target])
                        self.assertFalse("Work" @ target)
                        with self.assertRaises(AttributeError):
                            target.Work
                    else:
                        self.assertTrue(
                                target.Work() if mark is Action else target.Work,
                                )
                    self.assertEqual(extending.metadata_reads, [])

    def test_underlay_and_stored_input_diagnostics_use_declared_names(self):
        for pinned in (False, True):
            for mark in (Action, Pre, Post):
                cases = [(_One(), TagDeclarationError)]
                if mark is not Action:
                    cases.append((_Extend(), TagResolutionError))
                for member, failure in cases:
                    with self.subTest(pinned=pinned, mark=mark, failure=failure):
                        role = type("Role", (Tag,), {
                                "Work": mark(Underlay(member)),
                                })
                        if pinned:
                            role = Pin(role)
                        with self.assertRaises(failure) as caught:
                            role(_target(pinned))
                        self.assertIn("Work", str(caught.exception))
                        self.assertEqual(member.metadata_reads, [])

            stored = _Stored()
            role = type("Role", (Tag,), {"Work": Record(stored)})
            if pinned:
                role = Pin(role)
            with self.assertRaises(TagDeclarationError) as caught:
                role(_target(pinned), stored=17)
            self.assertIn("Work", str(caught.exception))
            self.assertIn("stored value", str(caught.exception))
            self.assertEqual(stored.metadata_reads, [])

    def test_explicit_signature_wrapped_and_native_callables_keep_their_seats(self):
        class Explicit(_Hostile):
            __signature__ = Signature([
                    Parameter("agent", Parameter.POSITIONAL_OR_KEYWORD),
                    Parameter("seed", Parameter.KEYWORD_ONLY),
                    ])

            def __call__(self, agent, **kwargs):
                return kwargs["seed"]

        def Source(agent, seed):
            return seed

        class Wrapped(_Hostile):
            def __init__(self):
                super().__init__()
                self.__wrapped__ = Source

            def __call__(self, agent, **kwargs):
                return kwargs["seed"]

        class NoneSignature(_Hostile):
            __signature__ = None

            def __call__(self, agent, stored):
                return stored

        explicit, wrapped, none_signature = Explicit(), Wrapped(), NoneSignature()
        self.assertEqual(_parameters_of(explicit).named[1][0], "seed")
        self.assertEqual(_parameters_of(wrapped).named[1][0], "seed")
        self.assertEqual(_parameters_of(none_signature).named[1][0], "stored")
        self.assertEqual(_parameters_of(Source).named[1][0], "seed")
        self.assertEqual(_parameters_of(partial(Source, Host())).named[0][0], "seed")
        self.assertEqual(explicit.metadata_reads, [])
        self.assertEqual(wrapped.metadata_reads, [])
        self.assertEqual(none_signature.metadata_reads, [])

        @_wraps_callable(Source)
        def Wrapper(*args, **kwargs):
            return Source(*args, **kwargs)

        self.assertEqual(Wrapper.__name__, "Source")
        self.assertIs(Wrapper.__wrapped__, Source)

    def test_host_action_underlay_and_context_hook_wrap_without_names(self):
        class NativeHost:
            Work = _One()

        class Extended(Tag):
            Work = Action(Underlay(_Extend()))

        target = NativeHost()
        Extended(target)
        self.assertTrue(target.Work())
        self.assertEqual(NativeHost.__dict__["Work"].metadata_reads, [])

        class Enter(_Hostile):
            def __call__(self, agent):
                return agent

        class Exit(_Hostile):
            def __call__(self, agent, kind, error, traceback):
                return False

        entering, exiting = Enter(), Exit()
        context = type("Context", (Tag,), {
                "__enter__": Action(entering),
                "__exit__": Action(exiting),
                })
        host = Host()
        context(host)
        with host as entered:
            self.assertIs(entered, host)
        self.assertEqual(entering.metadata_reads, [])
        self.assertEqual(exiting.metadata_reads, [])


if __name__ == "__main__":
    unittest.main()
