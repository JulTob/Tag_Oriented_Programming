"""Private continuation guards before public Safehouse routing is enabled."""

from __future__ import annotations

import asyncio
import gc
import inspect
import unittest
from collections.abc import Coroutine
from collections.abc import Generator
from types import SimpleNamespace
from unittest.mock import patch

from TopKit import TagArrestedAccessError
from TopKit.arrest import _Arrest
from TopKit.arrest import _safehouse
from TopKit.lazy_guard import _guard_lazy_result


class Receiver:
    pass


class SafehouseLazyProxyTests(unittest.TestCase):
    def test_denied_generator_continuations_do_not_unwind_the_source(self) -> None:
        receiver = Receiver()
        arrest = _Arrest(receiver)
        arrest.runs.append(SimpleNamespace(tag=object()))
        allowed = True
        events = []

        def Check(target, act):
            self.assertIs(target, receiver)
            self.assertEqual(act, "Action Steps")
            if not allowed:
                raise TagArrestedAccessError("still arrested")

        def Source():
            try:
                events.append("first")
                yield 1
                events.append("second")
                yield 2
            finally:
                events.append("finally")

        with patch.dict(_safehouse, {id(receiver): arrest}, clear=True):
            guarded = _guard_lazy_result(Source(), receiver, "Action Steps", Check)
            self.assertEqual(next(guarded), 1)
            allowed = False

            for resume in (
                    lambda: next(guarded),
                    lambda: guarded.send(None),
                    lambda: guarded.throw(ValueError("stop")),
                    guarded.close,
                    ):
                with self.assertRaises(TagArrestedAccessError):
                    resume()
            self.assertEqual(events, ["first"])

            del resume
            del guarded
            gc.collect()
            self.assertEqual(events, ["first"])
            self.assertEqual(len(arrest.lazy), 1)

            allowed = True
            arrest.lazy.clear()
            gc.collect()
            self.assertEqual(events, ["first", "finally"])

    def test_coroutine_keeps_asyncio_protocol(self) -> None:
        receiver = Receiver()
        checks = []

        def Check(target, act):
            checks.append((target, act))

        async def Value():
            await asyncio.sleep(0)
            return 2

        coroutine = _guard_lazy_result(Value(), receiver, "Action Value", Check)
        self.assertIsInstance(coroutine, Coroutine)
        self.assertFalse(inspect.iscoroutine(coroutine))
        self.assertTrue(inspect.isawaitable(coroutine))

        async def Run():
            task = asyncio.create_task(coroutine)
            return await task

        self.assertEqual(asyncio.run(Run()), 2)
        self.assertTrue(all(target is receiver for target, _ in checks))
        self.assertGreaterEqual(len(checks), 2)

    def test_native_async_generator_is_refused_before_loop_can_close_it(self) -> None:
        receiver = Receiver()
        events = []

        async def Values():
            try:
                events.append("started")
                yield 3
            finally:
                events.append("finally")

        with self.assertRaisesRegex(TypeError, "async generator results"):
            _guard_lazy_result(Values(), receiver, "Operation", lambda *_: None)
        asyncio.run(asyncio.sleep(0))
        self.assertEqual(events, [])

    def test_async_resumption_checks_again_after_suspension(self) -> None:
        receiver = Receiver()
        allowed = True
        events = []

        def Check(target, act):
            if not allowed:
                raise TagArrestedAccessError("still arrested")

        async def Source():
            events.append("start")
            await asyncio.sleep(0)
            events.append("finish")
            return 5

        guarded = _guard_lazy_result(Source(), receiver, "Action", Check)
        self.assertIsNone(guarded.send(None))
        allowed = False
        with self.assertRaises(TagArrestedAccessError):
            guarded.send(None)
        self.assertEqual(events, ["start"])
        allowed = True
        with self.assertRaises(StopIteration) as done:
            guarded.send(None)
        self.assertEqual(done.exception.value, 5)
        self.assertEqual(events, ["start", "finish"])

    def test_stacked_guards_check_both_receivers(self) -> None:
        inner_receiver, outer_receiver = Receiver(), Receiver()
        checks = []

        def Source():
            yield 1

        def Inner(target, act):
            checks.append("inner")

        def Outer(target, act):
            checks.append("outer")

        inner = _guard_lazy_result(Source(), inner_receiver, "Operation", Inner)
        outer = _guard_lazy_result(inner, outer_receiver, "Action", Outer)
        self.assertIsInstance(outer, Generator)
        self.assertFalse(inspect.isgenerator(outer))
        self.assertEqual(next(outer), 1)
        self.assertEqual(checks, ["outer", "inner"])

        value = object()
        self.assertIs(_guard_lazy_result(value, outer_receiver, "Action", Outer), value)


if __name__ == "__main__":
    unittest.main()
