"""TOP bound calls obey a saved Rip's door, even when captured earlier."""

from __future__ import annotations

import asyncio
import gc
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from TopKit import Action
from TopKit import Pin
from TopKit import Tag
from TopKit import TagArrestedAccessError
from TopKit.arrest import _Arrest
from TopKit.arrest import _rip_door
from TopKit.arrest import _safehouse


class Host:
    pass


class SafehouseBoundGuardTests(unittest.TestCase):
    def test_captured_action_runs_only_through_its_rip_door(self) -> None:
        class Fighter(Tag):
            def Train(agent):
                return "trained"

        agent = Host()
        Fighter(agent)
        captured = agent.Train
        arrest = _Arrest(agent)
        arrest.runs.append(SimpleNamespace(tag=Fighter))

        with patch.dict(_safehouse, {id(agent): arrest}, clear=True):
            with self.assertRaises(TagArrestedAccessError):
                captured()
            with _rip_door(agent):
                self.assertEqual(captured(), "trained")
            with self.assertRaises(TagArrestedAccessError):
                captured()

        self.assertEqual(captured(), "trained")

    def test_action_cannot_return_a_result_after_arresting_its_receiver(self) -> None:
        class Fighter(Tag):
            def Train(agent):
                arrest = _Arrest(agent)
                arrest.runs.append(SimpleNamespace(tag=Fighter))
                _safehouse[id(agent)] = arrest
                return "should not escape"

        agent = Host()
        Fighter(agent)
        with patch.dict(_safehouse, {}, clear=True):
            with self.assertRaises(TagArrestedAccessError):
                agent.Train()

    def test_started_action_generator_is_held_when_its_return_is_denied(self) -> None:
        events = []

        class Fighter(Tag):
            def Train(agent):
                def Steps():
                    try:
                        yield "started"
                    finally:
                        events.append("finalized")

                source = Steps()
                next(source)
                arrest = _Arrest(agent)
                arrest.runs.append(SimpleNamespace(tag=Fighter))
                _safehouse[id(agent)] = arrest
                return source

        agent = Host()
        Fighter(agent)
        with patch.dict(_safehouse, {}, clear=True):
            with self.assertRaises(TagArrestedAccessError):
                agent.Train()
            gc.collect()
            self.assertEqual(events, [])
            arrest = _safehouse[id(agent)]
            self.assertEqual(len(arrest.lazy), 1)
            source = arrest.lazy[0]

        source.close()
        self.assertEqual(events, ["finalized"])

    def test_started_pin_coroutine_is_held_when_its_return_is_denied(self) -> None:
        events = []

        class Fighter(Tag):
            pass

        @Pin
        class Trained(Tag):
            @Action
            def Work(tag):
                async def Steps():
                    try:
                        await asyncio.sleep(0)
                    finally:
                        events.append("finalized")

                source = Steps()
                source.send(None)
                arrest = _Arrest(tag)
                arrest.runs.append(SimpleNamespace(tag=Trained))
                _safehouse[id(tag)] = arrest
                return source

        Trained(Fighter)
        with patch.dict(_safehouse, {}, clear=True):
            with self.assertRaises(TagArrestedAccessError):
                Fighter.Work()
            gc.collect()
            self.assertEqual(events, [])
            arrest = _safehouse[id(Fighter)]
            self.assertEqual(len(arrest.lazy), 1)
            source = arrest.lazy[0]

        source.close()
        self.assertEqual(events, ["finalized"])

    def test_started_action_async_generator_is_held_on_agent_arrest(self) -> None:
        events = []

        class Fighter(Tag):
            def Work(agent):
                async def Steps():
                    try:
                        yield "started"
                    finally:
                        events.append("finalized")

                source = Steps()
                step = source.__anext__()
                with self.assertRaises(StopIteration):
                    step.send(None)
                arrest = _Arrest(agent)
                arrest.runs.append(SimpleNamespace(tag=Fighter))
                _safehouse[id(agent)] = arrest
                return source

        agent = Host()
        Fighter(agent)
        with patch.dict(_safehouse, {}, clear=True):
            with self.assertRaises(TagArrestedAccessError):
                agent.Work()
            gc.collect()
            self.assertEqual(events, [])
            arrest = _safehouse[id(agent)]
            self.assertEqual(len(arrest.lazy), 1)
            source = arrest.lazy[0]

        asyncio.run(source.aclose())
        self.assertEqual(events, ["finalized"])

    def test_captured_pin_operation_checks_its_tag_receiver(self) -> None:
        class Fighter(Tag):
            pass

        @Pin
        class Trained(Tag):
            @Action
            def Check(tag):
                return "ready"

        Trained(Fighter)
        captured = Fighter.Check
        arrest = _Arrest(Fighter)
        arrest.runs.append(SimpleNamespace(tag=Trained))

        with patch.dict(_safehouse, {id(Fighter): arrest}, clear=True):
            with self.assertRaises(TagArrestedAccessError):
                captured()
            with _rip_door(Fighter):
                self.assertEqual(captured(), "ready")
            with self.assertRaises(TagArrestedAccessError):
                captured()

    def test_action_lazy_result_checks_each_later_resume(self) -> None:
        events = []

        class Fighter(Tag):
            def Steps(agent):
                try:
                    events.append("first")
                    yield 1
                    events.append("second")
                    yield 2
                finally:
                    events.append("finally")

        agent = Host()
        Fighter(agent)
        result = agent.Steps()
        self.assertEqual(next(result), 1)
        arrest = _Arrest(agent)
        arrest.runs.append(SimpleNamespace(tag=Fighter))

        with patch.dict(_safehouse, {id(agent): arrest}, clear=True):
            with self.assertRaises(TagArrestedAccessError):
                next(result)
            self.assertEqual(events, ["first"])
            with _rip_door(agent):
                self.assertEqual(next(result), 2)
            with self.assertRaises(TagArrestedAccessError):
                result.close()
            self.assertEqual(events, ["first", "second"])

        result.close()
        self.assertEqual(events, ["first", "second", "finally"])

    def test_native_async_generator_action_result_is_explicitly_refused(self) -> None:
        class Fighter(Tag):
            async def Steps(agent):
                yield 1

        agent = Host()
        Fighter(agent)
        with self.assertRaisesRegex(TypeError, "async generator results"):
            agent.Steps()


if __name__ == "__main__":
    unittest.main()
