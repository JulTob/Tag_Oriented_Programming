"""Rip failures name Contributions, without requiring callable metadata."""

from __future__ import annotations

import gc
from inspect import Parameter
from inspect import Signature
import unittest
import warnings
from typing import Any

from TopKit import Pin
from TopKit import Record
from TopKit import Rip
from TopKit import Tag
from TopKit import TagCompositionError
from TopKit import TagResolutionError
from TopKit import Underlay
from TopKit.lifecycle import _teardown_all


class Agent:
    pass


def _target(pinned: bool) -> object:
    return type("Receiver", (Tag,), {}) if pinned else Agent()


class RipDiagnosticTests(unittest.TestCase):
    def test_callable_failures_keep_the_cause_and_run_later_cleanup(self) -> None:
        for pinned in (False, True):
            for hostile_metadata in (False, True):
                with self.subTest(pinned=pinned, hostile_metadata=hostile_metadata):
                    events = []
                    original = RuntimeError("cleanup failed")

                    class Failing:
                        # Pin still inspects its seats; Python need not infer this
                        # signature through the deliberately hostile metadata.
                        __signature__ = Signature([
                                Parameter("agent", Parameter.POSITIONAL_OR_KEYWORD),
                                ])

                        def __getattribute__(self, name: str) -> Any:
                            if hostile_metadata and name in ("__name__", "__qualname__"):
                                raise AssertionError("callable metadata was read")
                            return object.__getattribute__(self, name)

                        def __call__(self, agent: object) -> None:
                            events.append("first")
                            raise original

                    class Closing(Tag):
                        First = Rip(Failing())

                        @Rip
                        def Later(agent: object) -> None:
                            events.append("later")

                    if pinned:
                        Closing = Pin(Closing)
                    target = _target(pinned)
                    Closing(target)

                    with self.assertRaises(TagCompositionError) as failure:
                        del Closing[target]

                    self.assertEqual(str(failure.exception), "Closing teardown failed in: First")
                    self.assertIs(failure.exception.__cause__, original)
                    self.assertEqual(events, ["first", "later"])
                    self.assertNotIn(target, Closing)
                    self.assertNotIn(target, Closing[:])

                    with self.assertRaises(TagResolutionError):
                        del Closing[target]
                    _teardown_all(target)
                    self.assertEqual(events, ["first", "later"])

    def test_aliased_functions_report_declaration_names_in_order(self) -> None:
        events = []
        original = RuntimeError("first failure")

        def Implementation(agent: object) -> None:
            events.append("first")
            raise original

        def Other_Implementation(agent: object) -> None:
            events.append("second")
            raise ValueError("second failure")

        class Closing(Tag):
            First = Rip(Implementation)
            Second = Rip(Other_Implementation)

            @Rip
            def Later(agent: object) -> None:
                events.append("later")

        target = Agent()
        Closing(target)
        with self.assertRaises(TagCompositionError) as failure:
            del Closing[target]

        self.assertEqual(str(failure.exception), "Closing teardown failed in: First, Second")
        self.assertIs(failure.exception.__cause__, original)
        self.assertEqual(events, ["first", "second", "later"])
        self.assertEqual(Implementation.__name__, "Implementation")
        self.assertEqual(Other_Implementation.__name__, "Other_Implementation")

    def test_callable_lazy_results_keep_named_failures_and_disposal(self) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            for pinned in (False, True):
                for kind in ("coroutine", "generator", "async generator"):
                    with self.subTest(pinned=pinned, kind=kind):
                        events = []
                        returned = []

                        class Lazy:
                            def __call__(self, agent: object) -> Any:
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

                        class Closing(Tag):
                            First = Rip(Lazy())

                            @Rip
                            def Later(agent: object) -> None:
                                events.append("later")

                        if pinned:
                            Closing = Pin(Closing)
                        target = _target(pinned)
                        Closing(target)

                        with self.assertRaises(TagCompositionError) as failure:
                            del Closing[target]

                        cause = failure.exception.__cause__
                        self.assertIsInstance(cause, TagCompositionError)
                        self.assertIn("Rip protocol 'First' returned", str(cause))
                        self.assertIn(kind, str(cause))
                        self.assertEqual(events, ["later"])
                        self.assertNotIn(target, Closing[:])
                        if kind == "coroutine":
                            self.assertIsNone(returned[0].cr_frame)
                        elif kind == "generator":
                            self.assertIsNone(returned[0].gi_frame)

            gc.collect()
        self.assertFalse(any("was never awaited" in str(item.message) for item in caught))

    def test_rip_keeps_its_selected_callable_underlay_after_a_later_layer(self) -> None:
        for pinned in (False, True):
            with self.subTest(pinned=pinned):
                events = []

                class Earlier:
                    def __call__(self, agent: object) -> None:
                        events.append("base")

                class Added:
                    def __call__(self, agent: object, underlay) -> None:
                        underlay()
                        events.append("shape")

                class Base(Tag):
                    Close = Earlier()

                if pinned:
                    Base = Pin(Base)

                class Shape(Base):
                    Close = Rip(Underlay(Added()))

                class Later(Tag):
                    def Close(agent: object) -> None:
                        events.append("replacement")

                if pinned:
                    Later = Pin(Later)
                target = _target(pinned)
                Shape(target)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    Later(target)

                del Shape[target]
                self.assertEqual(events, ["base", "shape"])
                target.Close()
                self.assertEqual(events, ["base", "shape", "replacement"])

    def test_a_callable_pin_rip_still_receives_original_declarations(self) -> None:
        class Receiver(Tag):
            colour = "original"

        class Unpatch:
            def __call__(self, tag: type, original) -> None:
                tag.colour = original.colour

        @Pin
        class Patch(Tag):
            @Record
            def colour(tag: type, stored: str) -> str:
                return stored + "-patched"

            Restore = Rip(Unpatch())

        Patch(Receiver)
        self.assertEqual(Receiver.colour, "original-patched")
        del Patch[Receiver]
        self.assertEqual(Receiver.colour, "original")

    def test_catching_a_callable_lazy_underlay_cannot_hide_a_rip_failure(self) -> None:
        for pinned in (False, True):
            with self.subTest(pinned=pinned):
                events = []
                captured = []
                returned = []

                class Lazy:
                    def __call__(self, agent: object) -> Any:
                        def Values():
                            events.append("started")
                            yield "value"

                        result = Values()
                        returned.append(result)
                        return result

                class Base(Tag):
                    Close = Rip(Lazy())

                if pinned:
                    Base = Pin(Base)

                class Shape(Base):
                    @Rip
                    @Underlay
                    def Close(agent: object, underlay) -> None:
                        captured.append(underlay)
                        try:
                            underlay()
                        except (TagCompositionError, AttributeError):
                            events.append("caught")

                target = _target(pinned)
                Shape(target)
                with self.assertRaises(TagCompositionError) as failure:
                    del Shape[target]

                self.assertIsInstance(failure.exception.__cause__, TagCompositionError)
                self.assertIn("Rip protocol 'Close' returned a generator", str(failure.exception.__cause__))
                self.assertEqual(events, ["caught"])
                self.assertIsNone(returned[0].gi_frame)
                self.assertNotIn(target, Shape)
                self.assertIn(target, Base)

                # A captured Underlay is not a teardown after the Rip guard closes.
                values = captured[0]()
                self.assertIsNotNone(values.gi_frame)
                self.assertEqual(list(values), ["value"])
                self.assertEqual(events, ["caught", "started"])

    def test_best_effort_cleanup_keeps_reverse_tag_order_and_does_not_repeat(self) -> None:
        for pinned in (False, True):
            with self.subTest(pinned=pinned):
                events = []

                class Failing:
                    def __call__(self, agent: object) -> None:
                        events.append("first")
                        raise RuntimeError("best effort")

                class Earlier(Tag):
                    @Rip
                    def Earlier_End(agent: object) -> None:
                        events.append("earlier")

                class Later(Tag):
                    First = Rip(Failing())

                    @Rip
                    def End(agent: object) -> None:
                        events.append("later")

                if pinned:
                    Earlier, Later = Pin(Earlier), Pin(Later)
                target = _target(pinned)
                Earlier(target)
                Later(target)
                _teardown_all(target)
                self.assertEqual(events, ["first", "later", "earlier"])
                _teardown_all(target)
                self.assertEqual(events, ["first", "later", "earlier"])

    def test_unprintable_disposal_errors_cannot_hide_a_lazy_underlay_failure(self) -> None:
        for pinned in (False, True):
            with self.subTest(pinned=pinned):
                events = []

                class ErrorMeta(type):
                    def __getattribute__(cls, name: str) -> Any:
                        if name == "__name__":
                            raise RuntimeError("exception type-name lookup failed")
                        return type.__getattribute__(cls, name)

                class Unprintable(RuntimeError, metaclass=ErrorMeta):
                    def __str__(self) -> str:
                        raise RuntimeError("exception formatting failed")

                    def __repr__(self) -> str:
                        raise RuntimeError("exception representation failed")

                original = Unprintable("close failed")

                def Values():
                    try:
                        yield None
                    finally:
                        raise original

                value = Values()
                next(value)

                class Lazy:
                    def __init__(self, value: Any) -> None:
                        self.value = value

                    def __call__(self, agent: object) -> Any:
                        return self.value

                class Base(Tag):
                    Close = Rip(Lazy(value))

                if pinned:
                    Base = Pin(Base)

                class Shape(Base):
                    @Rip
                    @Underlay
                    def Close(agent: object, underlay) -> None:
                        try:
                            underlay()
                        except Exception:
                            events.append("caught")

                    @Rip
                    def Later(agent: object) -> None:
                        events.append("later")

                target = _target(pinned)
                Shape(target)
                with self.assertRaises(TagCompositionError) as failure:
                    del Shape[target]

                cause = failure.exception.__cause__
                self.assertIsInstance(cause, TagCompositionError)
                self.assertIs(cause.__cause__, original)
                self.assertIn("Rip protocol 'Close' returned a lazy result", str(cause))
                self.assertIn("Unprintable: <exception text unavailable>", str(cause))
                self.assertEqual(events, ["caught", "later"])
                self.assertIsNone(value.gi_frame)
                self.assertNotIn(target, Shape[:])


if __name__ == "__main__":
    unittest.main()
