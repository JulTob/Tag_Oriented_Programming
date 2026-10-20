"""An ordinary Tag Operation stays revocable after its handle is saved."""

from __future__ import annotations

import asyncio
import gc
from inspect import signature
from types import MethodType
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from TopKit import Operation
from TopKit import Pin
from TopKit import Public
from TopKit import Tag
from TopKit import TagArrestedAccessError
from TopKit.arrest import _Arrest
from TopKit.arrest import _rip_door
from TopKit.arrest import _safehouse


class Host:
    pass


def _arrest(tag: type, pin: type) -> _Arrest:
    arrest = _Arrest(tag)
    arrest.runs.append(SimpleNamespace(tag=pin))
    return arrest


class SafehouseTagOperationTests(unittest.TestCase):
    def test_saved_ordinary_operation_checks_the_tag_at_call_time(self):
        def do_work(tag, value: int = 2, /) -> tuple:
            """A Tag's own work."""
            return tag, value

        class Crew(Tag):
            Work = Operation(do_work)

        saved = Crew.Work
        native = MethodType(do_work, Crew)
        self.assertIs(saved.__self__, Crew)
        self.assertIs(saved.__func__, do_work)
        self.assertEqual(signature(saved), signature(native))
        self.assertEqual(saved.__qualname__, native.__qualname__)
        self.assertEqual(saved.__annotations__, native.__annotations__)
        self.assertEqual(saved.__name__, "do_work")
        self.assertEqual(saved.__doc__, do_work.__doc__)
        self.assertEqual(repr(saved), "<Operation Work of Crew>")
        self.assertEqual(saved, Crew.Work)
        self.assertEqual(saved, native)
        self.assertEqual(hash(saved), hash(native))
        self.assertEqual({saved: "kept"}[Crew.Work], "kept")

        @Pin
        class Licensed(Tag):
            pass

        Licensed(Crew)
        with patch.dict(_safehouse, {id(Crew): _arrest(Crew, Licensed)}, clear=True):
            for call in (saved, Crew.Work):
                with self.assertRaises(TagArrestedAccessError):
                    call()
            with _rip_door(Crew):
                self.assertEqual(saved(3), (Crew, 3))
            with self.assertRaises(TagArrestedAccessError):
                saved()

        self.assertEqual(saved(), (Crew, 2))

    def test_dynamic_callable_operation_keeps_its_name_and_optional_metadata(self):
        class CallableOperation:
            def __init__(self):
                self.closed = False

            def __getattribute__(self, name):
                if name == "__doc__" and object.__getattribute__(self, "closed"):
                    raise RuntimeError("documentation unavailable")
                return object.__getattribute__(self, name)

            def __call__(self, tag, value=4):
                return tag, value

        function = CallableOperation()

        class Crew(Tag):
            pass

        Crew.Work = Operation(function)
        function.closed = True
        saved = Crew.Work
        self.assertIs(saved.__self__, Crew)
        self.assertIs(saved.__func__, function)
        self.assertEqual(saved.__name__, "Work")
        self.assertIsNone(saved.__doc__)
        self.assertEqual(repr(saved), "<Operation Work of Crew>")
        self.assertEqual(signature(saved), signature(MethodType(function, Crew)))
        self.assertFalse(hasattr(saved, "__qualname__"))
        self.assertFalse(hasattr(saved, "__annotations__"))
        self.assertEqual(saved(5), (Crew, 5))

    def test_operation_cannot_return_after_arresting_its_own_tag(self):
        @Pin
        class Licensed(Tag):
            pass

        class Crew(Tag):
            @Operation
            def Work(tag):
                _safehouse[id(tag)] = _arrest(tag, Licensed)
                return "should not escape"

        Licensed(Crew)
        with patch.dict(_safehouse, {}, clear=True):
            with self.assertRaises(TagArrestedAccessError):
                Crew.Work()

    def test_started_ordinary_operation_result_stays_in_custody(self):
        events = []

        @Pin
        class Licensed(Tag):
            pass

        class Crew(Tag):
            @Operation
            def Work(tag):
                def Steps():
                    try:
                        yield "started"
                    finally:
                        events.append("finalized")

                source = Steps()
                next(source)
                _safehouse[id(tag)] = _arrest(tag, Licensed)
                return source

        Licensed(Crew)
        saved = Crew.Work
        with patch.dict(_safehouse, {}, clear=True):
            with self.assertRaises(TagArrestedAccessError):
                saved()
            gc.collect()
            self.assertEqual(events, [])
            arrest = _safehouse[id(Crew)]
            self.assertEqual(len(arrest.lazy), 1)
            source = arrest.lazy[0]

        source.close()
        self.assertEqual(events, ["finalized"])

    def test_started_public_operation_result_stays_in_tag_custody(self):
        events = []

        @Pin
        class Licensed(Tag):
            pass

        class Crew(Tag):
            @Public
            @Operation
            def Work(tag, agent):
                def Steps():
                    try:
                        yield "started"
                    finally:
                        events.append("finalized")

                source = Steps()
                next(source)
                _safehouse[id(tag)] = _arrest(tag, Licensed)
                return source

        agent = Host()
        Crew(agent)
        Licensed(Crew)
        saved = agent.Work
        with patch.dict(_safehouse, {}, clear=True):
            with self.assertRaises(TagArrestedAccessError):
                saved()
            gc.collect()
            self.assertEqual(events, [])
            arrest = _safehouse[id(Crew)]
            self.assertEqual(len(arrest.lazy), 1)
            source = arrest.lazy[0]

        source.close()
        self.assertEqual(events, ["finalized"])

    def test_public_operation_checks_both_tag_and_agent(self):
        for public_first in (True, False):
            with self.subTest(public_first=public_first):
                def Work(tag, agent, value=7):
                    return tag, agent, value

                marked = (
                        Public(Operation(Work))
                        if public_first else Operation(Public(Work))
                        )

                class Crew(Tag):
                    Work = marked

                @Pin
                class Licensed(Tag):
                    pass

                agent = Host()
                Crew(agent)
                Licensed(Crew)
                saved = agent.Work
                direct = Crew.Work
                with patch.dict(
                        _safehouse,
                        {id(Crew): _arrest(Crew, Licensed)},
                        clear=True,
                        ):
                    for call in (saved, direct):
                        with self.assertRaises(TagArrestedAccessError):
                            call(agent)
                    with _rip_door(Crew):
                        self.assertEqual(saved(8), (Crew, agent, 8))

    def test_generator_created_before_pin_checks_each_later_resume(self):
        events = []

        class Crew(Tag):
            @Operation
            def Steps(tag):
                try:
                    events.append("first")
                    yield 1
                    events.append("second")
                    yield 2
                finally:
                    events.append("finally")

        result = Crew.Steps()
        self.assertEqual(next(result), 1)

        @Pin
        class Licensed(Tag):
            pass

        Licensed(Crew)
        with patch.dict(_safehouse, {id(Crew): _arrest(Crew, Licensed)}, clear=True):
            with self.assertRaises(TagArrestedAccessError):
                next(result)
            self.assertEqual(events, ["first"])
            with _rip_door(Crew):
                self.assertEqual(next(result), 2)
            with self.assertRaises(TagArrestedAccessError):
                result.close()
            self.assertEqual(events, ["first", "second"])

        result.close()
        self.assertEqual(events, ["first", "second", "finally"])

    def test_coroutine_created_before_pin_checks_its_later_await(self):
        events = []

        class Crew(Tag):
            @Operation
            async def Work(tag):
                events.append("ran")
                return tag

        result = Crew.Work()

        @Pin
        class Licensed(Tag):
            pass

        Licensed(Crew)
        with patch.dict(_safehouse, {id(Crew): _arrest(Crew, Licensed)}, clear=True):
            async def Denied():
                return await result

            with self.assertRaises(TagArrestedAccessError):
                asyncio.run(Denied())
            self.assertEqual(events, [])

            async def Allowed():
                with _rip_door(Crew):
                    return await result

            self.assertIs(asyncio.run(Allowed()), Crew)
            self.assertEqual(events, ["ran"])

    def test_native_async_generator_operation_is_explicitly_refused(self):
        class Crew(Tag):
            @Operation
            async def Steps(tag):
                yield tag

        with self.assertRaisesRegex(TypeError, "async generator results"):
            Crew.Steps()


if __name__ == "__main__":
    unittest.main()
