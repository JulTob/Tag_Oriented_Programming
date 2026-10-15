"""TOP context Actions share the entered cleanup rule with Host hooks."""

from __future__ import annotations

import asyncio
import unittest
from unittest.mock import patch

from TopKit import Action
from TopKit import Rip
from TopKit import Tag
from TopKit import TagArrestedAccessError
from TopKit import TagCompositionError
from TopKit import Underlay
from TopKit.arrest import _safehouse


class SafehouseActionContextTests(unittest.TestCase):
    def setUp(self) -> None:
        empty_ledger = patch.dict(_safehouse, clear=True)
        empty_ledger.start()
        self.addCleanup(empty_ledger.stop)

    def test_entered_top_exit_runs_after_rip_and_cannot_suppress_it(self) -> None:
        events = []
        ready = False

        class Context(Tag):
            @Action
            def __enter__(agent):
                events.append("enter")
                return agent

            @Action
            def __exit__(agent, kind, value, traceback):
                events.append(("exit", kind))
                return True

            @Rip
            def Leave(agent):
                if not ready:
                    raise RuntimeError("unfinished")

        agent = type("Host", (), {})()
        Context(agent)
        captured_exit = type(agent).__dict__["__exit__"]

        with self.assertRaises(TagCompositionError):
            with agent:
                del Context[agent]

        self.assertEqual(events, ["enter", ("exit", TagCompositionError)])
        with self.assertRaises(TagArrestedAccessError):
            captured_exit(agent, None, None, None)
        ready = True
        del Tag[agent]

    def test_top_exit_first_arrest_surfaces_rip_over_body_error(self) -> None:
        class Context(Tag):
            @Action
            def __enter__(agent):
                return agent

            @Action
            def __exit__(agent, kind, value, traceback):
                del Custody[agent]

        class Custody(Tag):
            @Rip
            def Leave(agent):
                raise RuntimeError("rip failed")

        agent = type("Host", (), {})()
        Context(agent)
        Custody(agent)

        with self.assertRaises(TagCompositionError) as caught:
            with agent:
                raise ValueError("body failed")

        self.assertIsInstance(caught.exception.__cause__, RuntimeError)
        self.assertIn(agent, Tag[...])

    def test_async_top_exit_cannot_hide_its_caught_first_rip_failure(self) -> None:
        class Context(Tag):
            @Action
            async def __aenter__(agent):
                return agent

            @Action
            async def __aexit__(agent, kind, value, traceback):
                try:
                    del Custody[agent]
                except TagCompositionError:
                    return True

        class Custody(Tag):
            @Rip
            def Leave(agent):
                raise RuntimeError("rip failed")

        agent = type("Host", (), {})()
        Context(agent)
        Custody(agent)

        async def Scenario() -> None:
            with self.assertRaises(TagArrestedAccessError) as caught:
                async with agent:
                    pass
            self.assertIsInstance(caught.exception.__cause__, RuntimeError)

        asyncio.run(Scenario())
        self.assertIn(agent, Tag[...])

    def test_host_entry_and_top_exit_share_one_cleanup_entry(self) -> None:
        events = []

        class Host:
            def __enter__(self):
                events.append("host enter")
                return self

            def __exit__(self, kind, value, traceback):
                events.append("host exit")

        class Context(Tag):
            @Action
            def __exit__(agent, kind, value, traceback):
                events.append("top exit")

            @Rip
            def Leave(agent):
                raise RuntimeError("unfinished")

        agent = Host()
        Context(agent)
        with self.assertRaises(TagCompositionError):
            with agent:
                del Context[agent]

        self.assertEqual(events, ["host enter", "top exit"])

    def test_top_entry_and_host_exit_share_one_cleanup_entry(self) -> None:
        events = []

        class Host:
            def __exit__(self, kind, value, traceback):
                events.append("host exit")

        class Context(Tag):
            @Action
            def __enter__(agent):
                events.append("top enter")
                return agent

            @Rip
            def Leave(agent):
                raise RuntimeError("unfinished")

        agent = Host()
        Context(agent)
        with self.assertRaises(TagCompositionError):
            with agent:
                del Context[agent]

        self.assertEqual(events, ["top enter", "host exit"])

    def test_context_underlay_does_not_leave_old_host_cleanup_permission(self) -> None:
        events = []

        class Host:
            def __enter__(self):
                events.append("host enter")
                return self

            def __exit__(self, kind, value, traceback):
                events.append("host exit")

        class Seed(Tag):
            pass

        class Context(Tag):
            @Underlay
            def __enter__(agent, underlay):
                events.append("top enter")
                return underlay()

            @Underlay
            def __exit__(agent, underlay, kind, value, traceback):
                events.append("top exit")
                return underlay()

            @Rip
            def Leave(agent):
                raise RuntimeError("unfinished")

        agent = Host()
        Seed(agent)
        captured_host_exit = agent.__exit__
        Context(agent)
        with agent:
            events.append("body")

        self.assertEqual(
                events,
                ["top enter", "host enter", "body", "top exit", "host exit"],
                )
        with self.assertRaises(TagCompositionError):
            del Context[agent]
        with self.assertRaises(TagArrestedAccessError):
            captured_host_exit(None, None, None)

    def test_entered_async_top_exit_runs_after_rip(self) -> None:
        events = []

        class Context(Tag):
            @Action
            async def __aenter__(agent):
                return agent

            @Action
            async def __aexit__(agent, kind, value, traceback):
                await asyncio.sleep(0)
                events.append(("exit", kind))
                return True

            @Rip
            def Leave(agent):
                raise RuntimeError("unfinished")

        agent = type("Host", (), {})()
        Context(agent)

        async def Scenario() -> None:
            with self.assertRaises(TagCompositionError):
                async with agent:
                    del Context[agent]

        asyncio.run(Scenario())
        self.assertEqual(events, [("exit", TagCompositionError)])

    def test_suspended_async_top_entry_stops_before_resuming_arrested(self) -> None:
        events = []
        started = asyncio.Event()
        finish = asyncio.Event()
        ready = False

        class Context(Tag):
            @Action
            async def __aenter__(agent):
                events.append("entry started")
                started.set()
                await finish.wait()
                events.append("entry resumed")
                return agent

            @Action
            async def __aexit__(agent, kind, value, traceback):
                events.append("exit")

            @Rip
            def Leave(agent):
                if not ready:
                    raise RuntimeError("unfinished")

        agent = type("Host", (), {})()
        Context(agent)

        async def Scenario() -> None:
            async def Use() -> None:
                async with agent:
                    events.append("body")

            task = asyncio.create_task(Use())
            await started.wait()
            with self.assertRaises(TagCompositionError):
                del Context[agent]
            finish.set()
            with self.assertRaises(TagArrestedAccessError):
                await task

        asyncio.run(Scenario())
        self.assertEqual(events, ["entry started"])
        ready = True
        del Tag[agent]

    def test_custom_awaitable_top_entry_stops_before_resuming_arrested(self) -> None:
        events = []
        started = asyncio.Event()
        finish = asyncio.Event()

        class Pending:
            def __await__(self):
                async def Run():
                    events.append("entry started")
                    started.set()
                    await finish.wait()
                    events.append("entry resumed")
                    return agent

                return Run().__await__()

        class Context(Tag):
            @Action
            def __aenter__(agent):
                return Pending()

            @Action
            async def __aexit__(agent, kind, value, traceback):
                events.append("exit")

            @Rip
            def Leave(agent):
                raise RuntimeError("unfinished")

        agent = type("Host", (), {})()
        Context(agent)

        async def Scenario() -> None:
            async def Use() -> None:
                async with agent:
                    events.append("body")

            task = asyncio.create_task(Use())
            await started.wait()
            with self.assertRaises(TagCompositionError):
                del Context[agent]
            finish.set()
            with self.assertRaises(TagArrestedAccessError):
                await task

        asyncio.run(Scenario())
        self.assertEqual(events, ["entry started"])

    def test_async_top_exit_stays_open_when_arrest_starts_during_await(self) -> None:
        events = []
        started = asyncio.Event()
        finish = asyncio.Event()

        class Context(Tag):
            @Action
            async def __aenter__(agent):
                return agent

            @Action
            async def __aexit__(agent, kind, value, traceback):
                events.append("exit started")
                started.set()
                await finish.wait()
                events.append(("exit finished", agent.resource))

            @Rip
            def Leave(agent):
                raise RuntimeError("unfinished")

        agent = type("Host", (), {"resource": "open"})()
        Context(agent)

        async def Scenario() -> None:
            async def Use() -> None:
                async with agent:
                    pass

            task = asyncio.create_task(Use())
            await started.wait()
            with self.assertRaises(TagCompositionError):
                del Context[agent]
            finish.set()
            with self.assertRaises(TagArrestedAccessError):
                await task

        asyncio.run(Scenario())
        self.assertEqual(events, ["exit started", ("exit finished", "open")])


if __name__ == "__main__":
    unittest.main()
