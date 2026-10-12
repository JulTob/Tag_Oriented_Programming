"""Condition Underlays must not require Python callable metadata."""

import gc
import unittest
import warnings

from TopKit import (Pin, Post, Pre, Tag, TagContractError,
                    TagPostconditionError, TagPreconditionError, Underlay)


class Host:
    pass


class CallableConditionUnderlayTests(unittest.TestCase):
    phases = ((Pre, TagPreconditionError, False, "Precondition"),
              (Post, TagPostconditionError, True, "Postcondition"))

    def build(self, mark, prior, pinned=False, ignore=False, ordinary=False,
              hostile=False):
        calls = []

        class Added:
            def __getattribute__(self, name):
                if hostile and name == "__qualname__":
                    calls.append("metadata")
                    raise RuntimeError("metadata lookup must not run")
                return object.__getattribute__(self, name)

            def __repr__(self):
                raise RuntimeError("callable repr must not run")

            def __call__(self, agent, base, minimum=9, *, offset=4):
                calls.append((minimum, offset))
                result = base()
                return True if ignore else result

        if ordinary:
            def Added(agent, base, minimum=9, *, offset=4):
                calls.append((minimum, offset))
                result = base()
                return True if ignore else result

        ready = False

        def Deferred_Prior(agent):
            return prior(agent) if ready else True

        base = type("Base", (Tag,), {"Work": mark(Deferred_Prior)})
        if pinned:
            base = Pin(base)
        shape = type("Shape", (base,), {"Work": mark(Underlay(Added if ordinary else Added()))})
        target = type("Target", (Tag,), {}) if pinned else Host()
        # Test the Underlay after the Base passed its own neutral Gate/Posts.
        # Do not depend on a pending Shape overriding the Base's Gate, or
        # dispose of a lazy prior before the Underlay under test can see it.
        base(target)
        ready = True
        return shape, target, calls

    def test_boolean_and_fallthrough_underlays_match_function_controls(self):
        for mark, failure, keeps_tag, phase in self.phases:
            for pinned in (False, True):
                for ordinary in (False, True):
                    for value in (True, False, None):
                        for ignore in (False, True):
                            def Prior(agent):
                                return value

                            shape, target, calls = self.build(
                                mark, Prior, pinned, ignore, ordinary)
                            with self.subTest(phase=phase, pinned=pinned,
                                              ordinary=ordinary, value=value,
                                              ignore=ignore):
                                if value is False and not ignore:
                                    with self.assertRaises(failure.Work):
                                        shape(target)
                                    self.assertEqual(target in shape[:], keeps_tag)
                                else:
                                    shape(target)
                                    self.assertIn(target, shape[:])
                                self.assertEqual(calls, [(9, 4)])

    def test_underlay_diagnostics_never_read_metadata_or_repr(self):
        for mark, _, _, phase in self.phases:
            for pinned in (False, True):
                def Prior(agent):
                    return True

                shape, target, calls = self.build(mark, Prior, pinned, hostile=True)
                with self.subTest(phase=phase, pinned=pinned):
                    shape(target)
                    self.assertEqual(calls, [(9, 4)])

    def test_default_and_named_input_binding_is_unchanged(self):
        for mark, _, _, phase in self.phases:
            for pinned in (False, True):
                for inputs in ({}, {"minimum": 23, "offset": 7}):
                    def Prior(agent):
                        return True

                    shape, target, calls = self.build(mark, Prior, pinned)
                    with self.subTest(phase=phase, pinned=pinned, inputs=inputs):
                        shape(target, **inputs)
                        expected = (23, 7) if mark is Pre and inputs else (9, 4)
                        self.assertEqual(calls, [expected])

    def test_invalid_underlay_verdicts_remain_contract_errors(self):
        for mark, _, keeps_tag, phase in self.phases:
            for pinned in (False, True):
                for value in (0, 1, "ready", []):
                    for ignore in (False, True):
                        def Prior(agent):
                            return value

                        shape, target, _ = self.build(mark, Prior, pinned, ignore)
                        with self.subTest(phase=phase, pinned=pinned,
                                          value=value, ignore=ignore):
                            with self.assertRaises(TagContractError) as raised:
                                shape(target)
                            self.assertIn(f"{phase} 'Work'", str(raised.exception))
                            self.assertIn("condition Underlay", str(raised.exception))
                            self.assertIn(f"returned {value!r} ({type(value).__name__})",
                                          str(raised.exception))
                            self.assertIsInstance(raised.exception.__cause__, TagContractError)
                            self.assertEqual(target in shape[:], keeps_tag)

    def test_a_prior_contract_error_is_not_converted_to_false(self):
        for mark, _, _, phase in self.phases:
            for pinned in (False, True):
                error = TagContractError("prior contract failure")

                def Prior(agent):
                    raise error

                shape, target, _ = self.build(mark, Prior, pinned)
                with self.subTest(phase=phase, pinned=pinned):
                    with self.assertRaises(TagContractError) as raised:
                        shape(target)
                    self.assertIs(raised.exception.__cause__, error)
                    self.assertIn(f"{phase} 'Work'", str(raised.exception))

    def test_hostile_result_repr_and_type_metadata_cannot_hide_invalidity(self):
        metadata = []

        class HostileMeta(type):
            @property
            def __name__(cls):
                metadata.append(True)
                raise RuntimeError("type metadata must not run")

        class Unshowable(metaclass=HostileMeta):
            def __repr__(self):
                raise RuntimeError("result repr unavailable")

        for mark, _, keeps_tag, phase in self.phases:
            for pinned in (False, True):
                for ignore in (False, True):
                    def Prior(agent):
                        return Unshowable()

                    shape, target, _ = self.build(mark, Prior, pinned, ignore)
                    with self.subTest(phase=phase, pinned=pinned, ignore=ignore):
                        with self.assertRaises(TagContractError) as raised:
                            shape(target)
                        text = str(raised.exception)
                        self.assertIn(f"{phase} 'Work'", text)
                        self.assertIn("<result representation unavailable> (Unshowable)", text)
                        self.assertEqual(target in shape[:], keeps_tag)
        self.assertEqual(metadata, [])

    def test_hostile_close_error_text_preserves_contract_and_original_cause(self):
        metadata = []

        class HostileMeta(type):
            @property
            def __name__(cls):
                metadata.append(True)
                raise RuntimeError("error type metadata must not run")

        class UnprintableError(RuntimeError, metaclass=HostileMeta):
            def __str__(self):
                raise ValueError("error text unavailable")

        for mark, _, keeps_tag, phase in self.phases:
            for pinned in (False, True):
                for ignore in (False, True):
                    error = UnprintableError()

                    def Lazy():
                        try:
                            yield None
                        finally:
                            raise error

                    lazy = Lazy()
                    next(lazy)

                    def Prior(agent):
                        return lazy

                    shape, target, _ = self.build(mark, Prior, pinned, ignore)
                    with self.subTest(phase=phase, pinned=pinned, ignore=ignore):
                        with self.assertRaises(TagContractError) as raised:
                            shape(target)
                        text = str(raised.exception)
                        self.assertIn(f"{phase} 'Work'", text)
                        self.assertIn("UnprintableError: <exception text unavailable>", text)
                        self.assertIs(raised.exception.__cause__.__cause__, error)
                        self.assertIsNone(lazy.gi_frame)
                        self.assertEqual(target in shape[:], keeps_tag)
        self.assertEqual(metadata, [])

    def test_ordinary_prior_exceptions_still_answer_false(self):
        for mark, failure, keeps_tag, phase in self.phases:
            for pinned in (False, True):
                for ignore in (False, True):
                    def Prior(agent):
                        raise RuntimeError("prior predicate failed")

                    shape, target, _ = self.build(mark, Prior, pinned, ignore)
                    with self.subTest(phase=phase, pinned=pinned, ignore=ignore):
                        if ignore:
                            shape(target)
                            self.assertIn(target, shape[:])
                        else:
                            with self.assertRaises(failure.Work):
                                shape(target)
                            self.assertEqual(target in shape[:], keeps_tag)

    def test_diagnostic_helpers_preserve_plain_text_without_subclass_hooks(self):
        from TopKit.contracts import _result_repr
        from TopKit.errors import _exception_text, _type_name

        class HostileText(str):
            def __str__(self):
                raise RuntimeError("text str hook must not run")

            def __format__(self, spec):
                raise RuntimeError("text format hook must not run")

        class Value:
            def __repr__(self):
                return HostileText("ordinary representation")

        class Error(Exception):
            def __str__(self):
                return HostileText("ordinary exception text")

        Value.__name__ = HostileText("Value")
        text = _result_repr(Value())
        error_text = _exception_text(Error())
        name = _type_name(Value())
        self.assertIs(type(text), str)
        self.assertIs(type(error_text), str)
        self.assertIs(type(name), str)
        self.assertEqual(f"{text}: {error_text} ({name})",
                         "ordinary representation: ordinary exception text (Value)")
        self.assertEqual(_exception_text(ValueError("ordinary failure")), "ordinary failure")

    def test_diagnostic_helpers_do_not_swallow_python_interruptions(self):
        from TopKit.contracts import _result_repr
        from TopKit.errors import _exception_text

        for interruption in (KeyboardInterrupt(), SystemExit(7), GeneratorExit()):
            class Value:
                def __repr__(self):
                    raise interruption

            class Error(Exception):
                def __str__(self):
                    raise interruption

            for render, value in ((_result_repr, Value()), (_exception_text, Error())):
                with self.subTest(interruption=type(interruption).__name__, render=render.__name__):
                    with self.assertRaises(type(interruption)) as raised:
                        render(value)
                    self.assertIs(raised.exception, interruption)

    def test_lazy_underlays_are_disposed_without_starting_even_when_ignored(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            for mark, _, keeps_tag, phase in self.phases:
                for pinned in (False, True):
                    for kind in ("coroutine", "generator", "async generator"):
                        for ignore in (False, True):
                            started = []
                            if kind == "coroutine":
                                async def Lazy():
                                    started.append(True)
                            elif kind == "generator":
                                def Lazy():
                                    started.append(True)
                                    yield None
                            else:
                                async def Lazy():
                                    started.append(True)
                                    yield None
                            lazy = Lazy()

                            def Prior(agent):
                                return lazy

                            shape, target, _ = self.build(mark, Prior, pinned, ignore)
                            with self.subTest(phase=phase, pinned=pinned,
                                              kind=kind, ignore=ignore):
                                with self.assertRaises(TagContractError) as raised:
                                    shape(target)
                                self.assertIn(f"{phase} 'Work'", str(raised.exception))
                                self.assertIn(kind, str(raised.exception))
                                self.assertEqual(started, [])
                                self.assertEqual(target in shape[:], keeps_tag)
                                if kind == "coroutine":
                                    self.assertIsNone(lazy.cr_frame)
                                elif kind == "generator":
                                    self.assertIsNone(lazy.gi_frame)
                                else:
                                    self.assertFalse(lazy.ag_running)
            gc.collect()
        self.assertFalse(any("was never awaited" in str(item.message) for item in caught))

    def test_a_lazy_disposal_failure_preserves_the_original_cause(self):
        for mark, _, _, phase in self.phases:
            for pinned in (False, True):
                error = RuntimeError("close exploded")

                def Lazy():
                    try:
                        yield None
                    finally:
                        raise error

                lazy = Lazy()
                next(lazy)

                def Prior(agent):
                    return lazy

                shape, target, _ = self.build(mark, Prior, pinned, ignore=True)
                with self.subTest(phase=phase, pinned=pinned):
                    with self.assertRaises(TagContractError) as raised:
                        shape(target)
                    self.assertIn(f"{phase} 'Work'", str(raised.exception))
                    self.assertIn("close exploded", str(raised.exception))
                    self.assertIs(raised.exception.__cause__.__cause__, error)
                    self.assertIsNone(lazy.gi_frame)


if __name__ == "__main__":
    unittest.main()
