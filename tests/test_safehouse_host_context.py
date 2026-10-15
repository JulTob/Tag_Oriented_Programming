"""An entered Python Host context may finish cleanup after a failed Rip."""

from __future__ import annotations

import asyncio
from contextvars import copy_context
import unittest
from unittest.mock import patch

from TopKit import Rip
from TopKit import Tag
from TopKit import TagArrestedAccessError
from TopKit import TagCompositionError
from TopKit.arrest import _safehouse


class SafehouseHostContextTests(unittest.TestCase):
    def setUp(self) -> None:
        empty_ledger = patch.dict(_safehouse, clear=True)
        empty_ledger.start()
        self.addCleanup(empty_ledger.stop)

    def test_entered_exit_cleans_up_without_suppressing_rip_failure(self) -> None:
        events = []
        ready = False

        class Host:
            resource = "open"

            def __enter__(self):
                events.append("enter")
                return self

            def __exit__(self, kind, value, traceback):
                events.append(("exit", self.resource, kind))
                return True

        class Custody(Tag):
            @Rip
            def Leave(agent):
                if not ready:
                    raise RuntimeError("unfinished")

        host = Host()
        Custody(host)
        captured_exit = host.__exit__

        with self.assertRaises(TagCompositionError) as caught:
            with host:
                del Custody[host]

        self.assertIsInstance(caught.exception.__cause__, RuntimeError)
        self.assertEqual(events, ["enter", ("exit", "open", TagCompositionError)])
        with self.assertRaises(TagArrestedAccessError):
            captured_exit(None, None, None)

        ready = True
        del Tag[host]

    def test_exit_failure_does_not_hide_the_rip_failure(self) -> None:
        class Host:
            def __enter__(self):
                return self

            def __exit__(self, kind, value, traceback):
                raise LookupError("cleanup failed")

        class Custody(Tag):
            @Rip
            def Leave(agent):
                raise RuntimeError("rip failed")

        host = Host()
        Custody(host)
        with self.assertRaises(TagCompositionError) as caught:
            with host:
                del Custody[host]

        self.assertIsInstance(caught.exception.__cause__, RuntimeError)
        self.assertIsInstance(caught.exception.__context__, LookupError)

    def test_entry_cannot_finish_after_catching_failed_rip(self) -> None:
        events = []
        ready = False

        class Host:
            def __enter__(self):
                try:
                    del Custody[self]
                except TagCompositionError:
                    events.append("rip failed")
                return self

            def __exit__(self, kind, value, traceback):
                events.append("exit")

        class Custody(Tag):
            @Rip
            def Leave(agent):
                if not ready:
                    raise RuntimeError("unfinished")

        host = Host()
        Custody(host)
        with self.assertRaises(TagArrestedAccessError):
            with host:
                events.append("body")

        self.assertEqual(events, ["rip failed"])
        ready = True
        del Tag[host]

    def test_async_exit_stays_open_when_arrest_starts_during_await(self) -> None:
        events = []
        started = asyncio.Event()
        finish = asyncio.Event()

        class Host:
            resource = "open"

            async def __aenter__(self):
                return self

            async def __aexit__(self, kind, value, traceback):
                events.append("exit started")
                started.set()
                await finish.wait()
                events.append(("exit finished", self.resource))

        class Custody(Tag):
            @Rip
            def Leave(agent):
                raise RuntimeError("unfinished")

        host = Host()
        Custody(host)

        async def Scenario() -> None:
            async def Use() -> None:
                async with host:
                    pass

            task = asyncio.create_task(Use())
            await started.wait()
            with self.assertRaises(TagCompositionError):
                del Custody[host]
            finish.set()
            await task

        asyncio.run(Scenario())
        self.assertEqual(events, ["exit started", ("exit finished", "open")])

    def test_entered_async_exit_cannot_suppress_rip_failure(self) -> None:
        events = []

        class Host:
            resource = "open"

            async def __aenter__(self):
                return self

            async def __aexit__(self, kind, value, traceback):
                await asyncio.sleep(0)
                events.append((self.resource, kind))
                return True

        class Custody(Tag):
            @Rip
            def Leave(agent):
                raise RuntimeError("unfinished")

        host = Host()
        Custody(host)

        async def Scenario() -> None:
            with self.assertRaises(TagCompositionError) as caught:
                async with host:
                    del Custody[host]
            self.assertIsInstance(caught.exception.__cause__, RuntimeError)

        asyncio.run(Scenario())
        self.assertEqual(events, [("open", TagCompositionError)])

    def test_suspended_async_entry_does_not_resume_into_arrest(self) -> None:
        events = []
        started = asyncio.Event()
        finish = asyncio.Event()
        ready = False

        class Host:
            async def __aenter__(self):
                events.append("entry started")
                started.set()
                await finish.wait()
                events.append("entry resumed")
                return self

            async def __aexit__(self, kind, value, traceback):
                events.append("exit")

        class Custody(Tag):
            @Rip
            def Leave(agent):
                if not ready:
                    raise RuntimeError("unfinished")

        host = Host()
        Custody(host)

        async def Scenario() -> None:
            async def Use() -> None:
                async with host:
                    events.append("body")

            task = asyncio.create_task(Use())
            await started.wait()
            with self.assertRaises(TagCompositionError):
                del Custody[host]
            finish.set()
            with self.assertRaises(TagArrestedAccessError):
                await task

        asyncio.run(Scenario())
        self.assertEqual(events, ["entry started"])
        ready = True
        del Tag[host]

    def test_entered_async_exit_closes_from_another_context(self) -> None:
        class Host:
            async def __aenter__(self):
                return self

            async def __aexit__(self, kind, value, traceback):
                await asyncio.sleep(0)

        class Custody(Tag):
            @Rip
            def Leave(agent):
                raise RuntimeError("unfinished")

        host = Host()
        Custody(host)
        entry = type(host).__dict__["__aenter__"](host)
        try:
            entry.send(None)
        except StopIteration:
            pass

        with self.assertRaises(TagCompositionError):
            del Custody[host]

        exit_hook = type(host).__dict__["__aexit__"](host, None, None, None)
        self.assertIsNone(exit_hook.send(None))
        copy_context().run(exit_hook.close)
        denied = type(host).__dict__["__aexit__"](host, None, None, None)
        with self.assertRaises(TagArrestedAccessError):
            denied.send(None)


if __name__ == "__main__":
    unittest.main()
