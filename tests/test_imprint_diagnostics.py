"""Imprint failures use declaration names, not callable metadata."""

from __future__ import annotations

import asyncio
import gc
from inspect import Parameter
from inspect import Signature
import unittest
import warnings
from typing import Any

from TopKit import Action, Imprint, Pin, Post, Record, Tag
from TopKit import TagImprintError, TagPostconditionError, TagTrainingWarning
from TopKit import state as runtime


class Host:
    pass


class Stop(BaseException):
    pass


class _Callable:
    # Python need not infer a signature through deliberately hostile metadata.
    __signature__ = Signature([
            Parameter("agent", Parameter.POSITIONAL_OR_KEYWORD),
            Parameter("value", Parameter.KEYWORD_ONLY, default=None),
            ])

    def __init__(self, body, hostile_metadata=False):
        self.body = body
        self.hostile_metadata = hostile_metadata

    def __getattribute__(self, name: str) -> Any:
        if name in ("__name__", "__qualname__") and object.__getattribute__(
                self, "hostile_metadata"):
            raise AssertionError("callable metadata was read")
        return object.__getattribute__(self, name)

    def __repr__(self) -> str:
        raise AssertionError("callable repr was read")

    def __call__(self, agent: object, *, value=None) -> Any:
        return self.body(agent, value)


def _target(pinned: bool) -> object:
    return type("Receiver", (Tag,), {}) if pinned else Host()


class ImprintDiagnosticTests(unittest.TestCase):
    def assert_admitted(self, tag, target):
        self.assertIn(target, tag[:])
        self.assertTrue(isinstance(target, tag))
        # A failed training step no longer prevents the completed admission.
        self.assertIsNotNone(tag[target])

    def assert_cause_metadata(self, warning, original, text=None):
        self.assertEqual(
                warning.cause_type, type.__dict__["__name__"].__get__(type(original)))
        if text is not None:
            self.assertEqual(warning.cause_text, text)
        self.assertTrue(warning.traceback_summary)
        self.assertTrue(all(len(frame) == 3 for frame in warning.traceback_summary))
        # Keeping traceback frames here would keep the trained Agent alive.
        self.assertIsInstance(warning.failure, getattr(TagImprintError, warning.name))
        self.assertIsNone(warning.failure.__cause__)
        self.assertIsNone(warning.failure.__traceback__)

    def test_callable_failure_warns_by_name_and_continues_with_acquired_gains(self):
        for pinned in (False, True):
            for hostile_metadata in (False, True):
                with self.subTest(pinned=pinned, hostile_metadata=hostile_metadata):
                    events = []
                    original = RuntimeError("training failed")

                    def fail(agent, value):
                        events.append(("failure", value))
                        raise original

                    protocol = Imprint(_Callable(fail, hostile_metadata))
                    original_namespace = dict(vars(protocol))

                    class Trained(Tag):
                        @Record
                        def badge(agent):
                            return "ready"

                        @Action
                        def Read(agent):
                            return agent.badge

                        @Imprint
                        def Before(agent):
                            events.append("before")

                        Training = protocol

                        @Imprint
                        def Later(agent):
                            events.append("later")

                        @Post
                        def Equipped(agent):
                            return agent.badge == "ready"

                    if pinned:
                        Trained = Pin(Trained)
                    target = _target(pinned)

                    with self.assertWarns(TagTrainingWarning.Training) as caught:
                        Trained(target, value=17)

                    self.assert_cause_metadata(caught.warning, original)
                    self.assertEqual(caught.warning.name, "Training")
                    self.assertEqual(
                            str(caught.warning.failure),
                            "Imprint 'Training' failed: RuntimeError: training failed",
                            )
                    self.assertEqual(events, ["before", ("failure", 17), "later"])
                    self.assertEqual(vars(protocol), original_namespace)
                    self.assert_admitted(Trained, target)
                    self.assertTrue("badge" @ target)
                    self.assertTrue("Read" @ target)
                    self.assertEqual(target.Read(), "ready")
                    self.assertTrue(bool(target))

    def test_aliased_function_reports_its_declaration_without_renaming(self):
        original = ValueError("implementation failed")

        def Implementation(agent):
            raise original

        original_name = Implementation.__name__
        original_qualname = Implementation.__qualname__

        class Trained(Tag):
            Declared = Imprint(Implementation)

        target = Host()
        with self.assertWarns(TagTrainingWarning.Declared) as caught:
            Trained(target)

        self.assertEqual(
                str(caught.warning.failure),
                "Imprint 'Declared' failed: ValueError: implementation failed",
                )
        self.assert_cause_metadata(caught.warning, original)
        self.assertEqual(Implementation.__name__, original_name)
        self.assertEqual(Implementation.__qualname__, original_qualname)
        self.assert_admitted(Trained, target)

    def test_a_successful_callable_needs_no_diagnostic_metadata(self):
        for pinned in (False, True):
            with self.subTest(pinned=pinned):
                events = []

                def calculate(agent, value):
                    events.append(value)
                    return 41

                class Trained(Tag):
                    Training = Imprint(_Callable(calculate, True))

                if pinned:
                    Trained = Pin(Trained)
                target = _target(pinned)
                self.assertIs(Trained(target, value=23), target)
                self.assertEqual(events, [23])
                self.assertIn(target, Trained)

    def test_callable_lazy_results_are_named_and_not_started(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            for pinned in (False, True):
                for kind in ("coroutine", "generator", "async generator"):
                    with self.subTest(pinned=pinned, kind=kind):
                        events = []
                        returned = []

                        def produce(agent, value):
                            async def Coroutine():
                                events.append("started")

                            def Generator():
                                events.append("started")
                                yield None

                            async def Async_Generator():
                                events.append("started")
                                yield None

                            builders = {
                                    "coroutine": Coroutine,
                                    "generator": Generator,
                                    "async generator": Async_Generator,
                                    }
                            result = builders[kind]()
                            returned.append(result)
                            return result

                        class Trained(Tag):
                            @Record
                            def badge(agent):
                                return "ready"

                            Training = Imprint(_Callable(produce, True))

                            @Imprint
                            def Later(agent):
                                events.append("later")

                        if pinned:
                            Trained = Pin(Trained)
                        target = _target(pinned)

                        with self.assertWarns(TagTrainingWarning.Training) as failure:
                            Trained(target)

                        self.assertIn("Imprint 'Training' returned", str(failure.warning.failure))
                        self.assertIn(kind, str(failure.warning.failure))
                        self.assertIsNone(failure.warning.failure.__cause__)
                        self.assertEqual(events, ["later"])
                        self.assert_admitted(Trained, target)
                        self.assertTrue("badge" @ target)
                        self.assertEqual(target.badge, "ready")
                        self.assertTrue(bool(target))
                        if kind == "coroutine":
                            self.assertIsNone(returned[0].cr_frame)
                        elif kind == "generator":
                            self.assertIsNone(returned[0].gi_frame)
                        else:
                            # TOP does not invent an event loop to await aclose.
                            self.assertFalse(returned[0].ag_running)
                            asyncio.run(returned[0].aclose())
                        returned.clear()
            gc.collect()
        self.assertFalse(any("was never awaited" in str(item.message) for item in caught))

    def test_close_failures_warn_by_imprint_name_and_continue_training(self):
        for pinned in (False, True):
            for kind in ("coroutine", "generator"):
                with self.subTest(pinned=pinned, kind=kind):
                    events = []
                    original = RuntimeError("close failed")

                    class Suspend:
                        def __await__(self):
                            yield None

                    async def Coroutine():
                        try:
                            events.append("started")
                            await Suspend()
                        finally:
                            events.append("closed")
                            raise original

                    def Generator():
                        try:
                            events.append("started")
                            yield None
                        finally:
                            events.append("closed")
                            raise original

                    lazy = Coroutine() if kind == "coroutine" else Generator()
                    lazy.send(None)

                    class Trained(Tag):
                        Training = Imprint(_Callable(lambda agent, value: lazy, True))

                        @Imprint
                        def Later(agent):
                            events.append("later")

                    if pinned:
                        Trained = Pin(Trained)
                    target = _target(pinned)
                    with self.assertWarns(TagTrainingWarning.Training) as caught:
                        Trained(target)

                    self.assert_cause_metadata(caught.warning, original)
                    self.assertIn("Imprint 'Training' failed", str(caught.warning.failure))
                    self.assertIn("close failed", str(caught.warning.failure))
                    self.assertEqual(events, ["started", "closed", "later"])
                    self.assert_admitted(Trained, target)
                    self.assertTrue(bool(target))

    def test_python_interruptions_keep_their_original_type_and_gains(self):
        for pinned in (False, True):
            for original in (KeyboardInterrupt(), SystemExit(7), Stop()):
                with self.subTest(pinned=pinned, interruption=type(original).__name__):
                    events = []

                    def interrupt(agent, value):
                        raise original

                    class Trained(Tag):
                        @Record
                        def badge(agent):
                            return "ready"

                        Training = Imprint(_Callable(interrupt, True))

                        @Imprint
                        def Later(agent):
                            events.append("later")

                    if pinned:
                        Trained = Pin(Trained)
                    target = _target(pinned)
                    with self.assertRaises(type(original)) as caught:
                        Trained(target)

                    self.assertIs(caught.exception, original)
                    self.assertEqual(events, [])
                    self.assert_admitted(Trained, target)
                    self.assertTrue("badge" @ target)
                    self.assertEqual(target.badge, "ready")
                    self.assertTrue(bool(target))

    def test_posts_judge_the_admitted_agent_after_imprint_failure(self):
        for pinned in (False, True):
            for ready in (False, True):
                with self.subTest(pinned=pinned, ready=ready):
                    original = RuntimeError("training stopped")

                    def fail(agent, value):
                        raise original

                    class Trained(Tag):
                        Training = Imprint(_Callable(fail, True))

                        @Post
                        def Equipped(agent):
                            return ready

                    if pinned:
                        Trained = Pin(Trained)
                    target = _target(pinned)
                    with self.assertWarns(TagTrainingWarning.Training) as caught:
                        if ready:
                            self.assertIs(Trained(target), target)
                        else:
                            with self.assertRaises(TagPostconditionError.Equipped):
                                Trained(target)
                    self.assert_cause_metadata(caught.warning, original, "training stopped")
                    self.assert_admitted(Trained, target)
                    self.assertEqual(bool(target), ready)
                    self.assertEqual(target.Equipped, ready)
                    self.assertEqual(target in Trained, ready)
                    self.assertEqual(target in ~Trained, not ready)

    def test_a_missing_record_does_not_add_an_implicit_requirement(self):
        for pinned in (False, True):
            with self.subTest(pinned=pinned):
                original = RuntimeError("training stopped")

                def fail(agent, value):
                    del agent.badge
                    raise original

                class Trained(Tag):
                    @Record
                    def badge(agent):
                        return "optional"

                    Training = Imprint(_Callable(fail, True))

                if pinned:
                    Trained = Pin(Trained)
                target = _target(pinned)
                with self.assertWarns(TagTrainingWarning.Training) as caught:
                    Trained(target)

                self.assert_cause_metadata(caught.warning, original)
                self.assertFalse("badge" @ target)
                self.assert_admitted(Trained, target)
                self.assertTrue(bool(target))

    def test_unprintable_exceptions_do_not_replace_the_imprint_failure(self):
        for pinned in (False, True):
            for hostile_name in ("ordinary", "lookup", "descriptor"):
                with self.subTest(pinned=pinned, hostile_name=hostile_name):
                    class ErrorMeta(type):
                        def __getattribute__(cls, name):
                            if hostile_name == "lookup" and name == "__name__":
                                raise AssertionError("exception type metadata was read")
                            return type.__getattribute__(cls, name)

                        @property
                        def __name__(cls):
                            if hostile_name == "descriptor":
                                raise AssertionError("exception type descriptor was read")
                            return type.__dict__["__name__"].__get__(cls)

                    class Unprintable(Exception, metaclass=ErrorMeta):
                        def __str__(self):
                            raise RuntimeError("exception text failed")

                        def __repr__(self):
                            raise AssertionError("exception repr was read")

                    original = Unprintable()

                    def fail(agent, value):
                        raise original

                    class Trained(Tag):
                        Training = Imprint(_Callable(fail, True))

                    if pinned:
                        Trained = Pin(Trained)
                    target = _target(pinned)
                    with self.assertWarns(TagTrainingWarning.Training) as caught:
                        Trained(target)

                    self.assertEqual(
                            str(caught.warning.failure),
                            "Imprint 'Training' failed: Unprintable: <exception text unavailable>",
                            )
                    self.assert_cause_metadata(caught.warning, original)
                    self.assert_admitted(Trained, target)
                    self.assertTrue(bool(target))
                    self.assertEqual(runtime._state_of(target).composing, 0)

    def test_unprintable_disposal_errors_keep_close_failure_metadata(self):
        for pinned in (False, True):
            for kind in ("coroutine", "generator"):
                with self.subTest(pinned=pinned, kind=kind):
                    class Unprintable(Exception):
                        def __str__(self):
                            raise RuntimeError("exception text failed")

                        def __repr__(self):
                            raise AssertionError("exception repr was read")

                    events = []
                    original = Unprintable()

                    class Suspend:
                        def __await__(self):
                            yield None

                    async def Coroutine():
                        try:
                            await Suspend()
                        finally:
                            events.append("closed")
                            raise original

                    def Generator():
                        try:
                            yield None
                        finally:
                            events.append("closed")
                            raise original

                    lazy = Coroutine() if kind == "coroutine" else Generator()
                    lazy.send(None)

                    class Trained(Tag):
                        Training = Imprint(_Callable(lambda agent, value: lazy, True))

                        @Imprint
                        def Later(agent):
                            events.append("later")

                    if pinned:
                        Trained = Pin(Trained)
                    target = _target(pinned)
                    with self.assertWarns(TagTrainingWarning.Training) as caught:
                        Trained(target)

                    self.assertEqual(
                            str(caught.warning.failure),
                            "Imprint 'Training' failed: Unprintable: <exception text unavailable>",
                            )
                    self.assert_cause_metadata(caught.warning, original)
                    self.assertEqual(events, ["closed", "later"])
                    self.assertIsNone(lazy.cr_frame if kind == "coroutine" else lazy.gi_frame)
                    self.assert_admitted(Trained, target)
                    self.assertTrue(bool(target))
                    self.assertEqual(runtime._state_of(target).composing, 0)

    def test_a_synchronous_result_is_discarded_without_observation(self):
        class Unprintable:
            def __repr__(self):
                raise AssertionError("result repr was read")

            def __str__(self):
                raise AssertionError("result text was read")

            def __bool__(self):
                raise AssertionError("result truth was read")

        for pinned in (False, True):
            with self.subTest(pinned=pinned):
                result = Unprintable()

                class Trained(Tag):
                    Training = Imprint(_Callable(lambda agent, value: result, True))

                if pinned:
                    Trained = Pin(Trained)
                target = _target(pinned)
                self.assertIs(Trained(target), target)
                self.assertIn(target, Trained[:])

    def test_exception_text_interruptions_still_propagate(self):
        for pinned in (False, True):
            for interruption in (KeyboardInterrupt(), SystemExit(7), Stop()):
                with self.subTest(pinned=pinned, interruption=type(interruption).__name__):
                    class Interrupted(Exception):
                        def __str__(self):
                            raise interruption

                    original = Interrupted()

                    def fail(agent, value):
                        raise original

                    class Trained(Tag):
                        @Record
                        def badge(agent):
                            return "ready"

                        Training = Imprint(_Callable(fail, True))

                    if pinned:
                        Trained = Pin(Trained)
                    target = _target(pinned)
                    with self.assertRaises(type(interruption)) as caught:
                        Trained(target)

                    self.assertIs(caught.exception, interruption)
                    self.assert_admitted(Trained, target)
                    self.assertTrue("badge" @ target)
                    self.assertEqual(target.badge, "ready")
                    self.assertTrue(bool(target))
                    self.assertEqual(runtime._state_of(target).composing, 0)

    def test_exception_text_does_not_invoke_error_or_string_subclass_format(self):
        class Text(str):
            def __str__(self):
                raise AssertionError("returned text str was read")

            def __format__(self, specification):
                raise AssertionError("returned text format was read")

        class Unformattable(Exception):
            def __str__(self):
                return Text("training failed")

            def __format__(self, specification):
                raise AssertionError("exception format was read")

        for pinned in (False, True):
            with self.subTest(pinned=pinned):
                original = Unformattable()

                def fail(agent, value):
                    raise original

                class Trained(Tag):
                    Training = Imprint(_Callable(fail, True))

                if pinned:
                    Trained = Pin(Trained)
                target = _target(pinned)
                with self.assertWarns(TagTrainingWarning.Training) as caught:
                    Trained(target)

                self.assertEqual(
                        str(caught.warning.failure),
                        "Imprint 'Training' failed: Unformattable: training failed",
                        )
                self.assert_cause_metadata(caught.warning, original)
                self.assert_admitted(Trained, target)
                self.assertEqual(runtime._state_of(target).composing, 0)

    def test_string_subclass_declaration_names_use_only_their_plain_text(self):
        for pinned in (False, True):
            for kind in ("failure", "coroutine", "generator", "async generator"):
                with self.subTest(pinned=pinned, kind=kind):
                    class Name(str):
                        armed = False

                        def __repr__(self):
                            raise AssertionError("declaration name repr was read")

                        def __str__(self):
                            if Name.armed:
                                raise AssertionError("declaration name str was read")
                            return str.__str__(self)

                        def __format__(self, specification):
                            if Name.armed:
                                raise AssertionError("declaration name format was read")
                            return str.__format__(self, specification)

                    original = RuntimeError("training failed")
                    returned = []
                    events = []

                    def Training(agent):
                        if kind == "failure":
                            raise original

                        async def Coroutine():
                            events.append("started")

                        def Generator():
                            events.append("started")
                            yield None

                        async def Async_Generator():
                            events.append("started")
                            yield None

                        builders = {
                                "coroutine": Coroutine,
                                "generator": Generator,
                                "async generator": Async_Generator,
                                }
                        result = builders[kind]()
                        returned.append(result)
                        return result

                    Trained = type("Role", (Tag,), {Name("Training"): Imprint(Training)})
                    if pinned:
                        Trained = Pin(Trained)
                    target = _target(pinned)
                    # Formatted metadata is unnecessary even when the accepted
                    # declaration key only becomes hostile after class creation.
                    Name.armed = True
                    with self.assertWarns(TagTrainingWarning.Training) as caught:
                        Trained(target)

                    self.assertIn("Training", str(caught.warning.failure))
                    if kind == "failure":
                        self.assert_cause_metadata(caught.warning, original, "training failed")
                    else:
                        self.assertIsNone(caught.warning.cause_type)
                        self.assertIsNone(caught.warning.failure.__cause__)
                    self.assert_admitted(Trained, target)
                    self.assertTrue(bool(target))
                    self.assertEqual(events, [])
                    if kind == "coroutine":
                        self.assertIsNone(returned[0].cr_frame)
                    elif kind == "generator":
                        self.assertIsNone(returned[0].gi_frame)
                    elif kind == "async generator":
                        asyncio.run(returned[0].aclose())


if __name__ == "__main__":
    unittest.main()
