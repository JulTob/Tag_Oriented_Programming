"""Lazy rejection preserves ordinary values and cannot lose Rip failures."""

import gc
import types
import unittest
import warnings

from TopKit import (Imprint, Pin, Post, Pre, Rip, Tag, TagCompositionError,
                    TagContractError, Underlay)


class Host:
    pass


def target_for(pinned):
    return type("Target", (Tag,), {}) if pinned else Host()


class LazyProtocolBoundaryTests(unittest.TestCase):
    def check_ordinary_result(self, mark, pinned, advertised):
        calls = []

        class Value:
            @property
            def __class__(self):
                calls.append("class")
                if isinstance(advertised, BaseException):
                    raise advertised
                return advertised

            def close(self):
                calls.append("close")

        value = Value()

        def Complete(agent):
            return value

        role = type("Role", (Pin if pinned else Tag,), {"Complete": mark(Complete)})
        target = target_for(pinned)
        if mark in (Pre, Post):
            with self.assertRaises(TagContractError):
                role(target)
            self.assertEqual(target in role[:], mark is Post)
        else:
            role(target)
            if mark is Rip:
                del role[target]
            self.assertEqual(target in role, mark is Imprint)
        self.assertEqual(calls, [])

    def test_ordinary_protocol_results_never_run_class_or_close_hooks(self):
        advertised = (object, types.CoroutineType, types.GeneratorType,
                      types.AsyncGeneratorType, RuntimeError("class unavailable"),
                      SystemExit(7))
        for mark in (Imprint, Rip):
            for pinned in (False, True):
                for kind in advertised:
                    with self.subTest(mark=mark, pinned=pinned, kind=kind):
                        self.check_ordinary_result(mark, pinned, kind)

    def test_conditions_still_reject_ordinary_objects_without_class_hooks(self):
        for mark in (Pre, Post):
            for pinned in (False, True):
                for kind in (types.CoroutineType, types.GeneratorType,
                             types.AsyncGeneratorType, SystemExit(7)):
                    with self.subTest(mark=mark, pinned=pinned, kind=kind):
                        self.check_ordinary_result(mark, pinned, kind)

    def check_chain_metadata(self, pinned, teardown, interruption=None):
        class Prior:
            def __getattribute__(self, name):
                if name == "__topkit_action_chain__":
                    raise interruption if interruption is not None else RuntimeError(
                        "optional chain metadata unavailable")
                return object.__getattribute__(self, name)

            def __call__(self, agent):
                return 17

        mark = Rip if teardown else lambda function: function
        base = type("Base", (Pin if pinned else Tag,), {"Complete": mark(Prior())})

        def Complete(agent, underlay):
            return underlay() + 1

        shape = type("Shape", (base,), {"Complete": mark(Underlay(Complete))})
        target = target_for(pinned)
        if interruption is not None:
            with self.assertRaises(type(interruption)) as raised:
                shape(target)
            self.assertIs(raised.exception, interruption)
        else:
            shape(target)
            self.assertEqual(target.Complete(), 18)
            if teardown:
                del shape[target]
                self.assertNotIn(target, shape)

    def test_optional_chain_metadata_does_not_refuse_callable_underlays(self):
        for pinned in (False, True):
            for teardown in (False, True):
                with self.subTest(pinned=pinned, teardown=teardown):
                    self.check_chain_metadata(pinned, teardown)

    def test_chain_metadata_python_interruptions_keep_their_identity(self):
        for pinned in (False, True):
            for error in (KeyboardInterrupt(), SystemExit(7), GeneratorExit()):
                with self.subTest(pinned=pinned, error=type(error).__name__):
                    self.check_chain_metadata(pinned, True, error)

    def test_direct_rip_tolerates_missing_chain_metadata_but_keeps_interruptions(self):
        for pinned in (False, True):
            for interruption in (None, KeyboardInterrupt(), SystemExit(7), GeneratorExit()):
                with self.subTest(pinned=pinned, interruption=type(interruption).__name__):
                    calls = []

                    class Complete:
                        def __getattribute__(self, name):
                            if name == "__topkit_action_chain__":
                                if interruption is not None:
                                    raise interruption
                                raise RuntimeError("optional chain metadata unavailable")
                            return object.__getattribute__(self, name)

                        def __call__(self, agent):
                            calls.append("complete")

                    role = type("Role", (Pin if pinned else Tag,), {"Complete": Rip(Complete())})
                    target = target_for(pinned)
                    role(target)
                    if interruption is None:
                        del role[target]
                        self.assertEqual(calls, ["complete"])
                    else:
                        with self.assertRaises(type(interruption)) as raised:
                            del role[target]
                        self.assertIs(raised.exception, interruption)
                        self.assertEqual(calls, [])
                    self.assertNotIn(target, role)

    def check_rip_underlay(self, prior, pinned):
        caught = []
        base = type("Base", (Pin if pinned else Tag,), {"Close": Rip(prior)})

        def Close(agent, underlay):
            try:
                underlay()
            except Exception as error:
                caught.append(error)

        shape = type("Shape", (base,), {"Close": Rip(Underlay(Close))})
        target = target_for(pinned)
        shape(target)
        with self.assertRaises(TagCompositionError) as raised:
            del shape[target]
        self.assertNotIn(target, shape)
        self.assertIn(target, base[:])
        self.assertNotIn(target, base)
        self.assertNotIn(target, ~base)
        failure = raised.exception.__cause__
        self.assertIsInstance(failure, TagCompositionError)
        self.assertEqual(caught, [failure])
        return failure

    def check_callable_lazy(self, pinned, kind, hostile):
        started = []
        if kind == "coroutine":
            async def Deferred():
                started.append(True)
        elif kind == "generator":
            def Deferred():
                started.append(True)
                yield None
        else:
            async def Deferred():
                started.append(True)
                yield None
        lazy = Deferred()
        metadata = []

        class Prior:
            def __getattribute__(self, name):
                if name == "__qualname__" and hostile:
                    metadata.append(name)
                    raise RuntimeError("optional callable label unavailable")
                return object.__getattribute__(self, name)

            def __call__(self, agent):
                return lazy

        failure = self.check_rip_underlay(Prior(), pinned)
        self.assertIn(kind, str(failure))
        self.assertEqual(started, [])
        if kind == "coroutine":
            self.assertIsNone(lazy.cr_frame)
        elif kind == "generator":
            self.assertIsNone(lazy.gi_frame)
        else:
            self.assertFalse(lazy.ag_running)

    def test_callable_labels_cannot_hide_lazy_rip_underlay_failures(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            for pinned in (False, True):
                for kind in ("coroutine", "generator", "async generator"):
                    for hostile in (False, True):
                        with self.subTest(pinned=pinned, kind=kind, hostile=hostile):
                            self.check_callable_lazy(pinned, kind, hostile)
            gc.collect()
        self.assertFalse(any("was never awaited" in str(item.message) for item in caught))

    def check_unprintable_close(self, pinned, hostile_type):
        metadata = []

        class ErrorMeta(type):
            @property
            def __name__(cls):
                metadata.append("type")
                if hostile_type:
                    raise RuntimeError("error type metadata unavailable")
                return "CloseError"

        class CloseError(RuntimeError, metaclass=ErrorMeta):
            def __str__(self):
                raise ValueError("error text unavailable")

        error = CloseError()

        def Deferred():
            try:
                yield None
            finally:
                raise error

        lazy = Deferred()
        next(lazy)

        def Close(agent):
            return lazy

        failure = self.check_rip_underlay(Close, pinned)
        self.assertIs(failure.__cause__, error)
        self.assertIn("CloseError: <exception text unavailable>", str(failure))
        self.assertIn("Close", str(failure))
        self.assertIsNone(lazy.gi_frame)
        self.assertEqual(metadata, [])

    def test_unprintable_close_errors_remain_recorded_rip_failures(self):
        for pinned in (False, True):
            for hostile_type in (False, True):
                with self.subTest(pinned=pinned, hostile_type=hostile_type):
                    self.check_unprintable_close(pinned, hostile_type)

    def test_disposal_runs_finally_of_a_generator_already_started_by_the_caller(self):
        for mark in (Imprint, Rip):
            with self.subTest(mark=mark):
                events = []

                def Deferred():
                    try:
                        events.append("started by caller")
                        yield None
                        events.append("advanced past yield")
                    finally:
                        events.append("closed")

                lazy = Deferred()
                next(lazy)

                def Complete(agent):
                    return lazy

                role = type("Role", (Tag,), {"Complete": mark(Complete)})
                target = Host()
                if mark is Imprint:
                    from TopKit import TagImprintError
                    with self.assertRaises(TagImprintError.Complete):
                        role(target)
                    self.assertNotIn(target, role)
                    self.assertNotIn(target, role[:])
                    self.assertFalse(isinstance(target, role))
                else:
                    role(target)
                    with self.assertRaises(TagCompositionError):
                        del role[target]
                    self.assertNotIn(target, role)
                self.assertEqual(events, ["started by caller", "closed"])
                self.assertIsNone(lazy.gi_frame)
