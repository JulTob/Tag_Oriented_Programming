"""Conformance tests: try finally."""

from __future__ import annotations

import gc
import unittest
import warnings
import weakref
from TopKit import Post
from TopKit import Postcondition
from TopKit import Pre
from TopKit import Precondition
from TopKit import Record
from TopKit import Secret
from TopKit import Tag
from TopKit import TagOverwriteWarning
from TopKit import Underlay

from ._fixtures import Agent
from ._fixtures import Sentry
from ._fixtures import _DEL_LOG


class TryFinallyTests(unittest.TestCase):
    """A block holds a Tag with Python's own try and finally: tag before
    try, Rip in finally (STEP-SPEC-31)."""

    def setUp(self) -> None:
        _DEL_LOG.clear()

    def test_try_finally_rips_when_the_block_raises(self) -> None:
        ari = Agent()

        with self.assertRaises(LookupError):
            Sentry(ari)
            try:
                raise LookupError("the gate is breached")
            finally:
                del Sentry[ari]

        self.assertNotIn(ari, Sentry)
        self.assertEqual(_DEL_LOG, ["stood down"])

    def test_a_refused_gate_raises_before_the_try(self) -> None:
        class Gated(Tag):
            @Pre
            def Ready(agent):
                return agent.ready

        cal = Agent()
        cal.ready = False
        ran: list[str] = []

        with self.assertRaises(Precondition.Ready):
            Gated(cal)
            try:
                ran.append("block")
            finally:
                del Gated[cal]

        self.assertEqual(ran, [])
        self.assertNotIn(cal, Gated[:])

    def test_a_postcondition_failure_before_the_try_leaves_the_tag(self) -> None:
        class Sworn(Tag):
            @Post
            def Has_Oath(agent):
                return agent.oath is not None

        bo = Agent()
        bo.oath = None
        ran: list[str] = []

        with self.assertRaises(Postcondition.Has_Oath):
            Sworn(bo)
            try:
                ran.append("block")
            finally:
                del Sworn[bo]

        self.assertEqual(ran, [])
        self.assertIn(bo, ~Sworn)                                     # landed, then reported defective

    def test_a_hosts_ordinary_context_protocol_survives_tagging(self) -> None:
        events: list[str] = []

        class Host:
            def __enter__(self):
                events.append("enter")
                return "host value"

            def __exit__(self, kind, value, traceback):
                events.append("exit")

        host = Host()
        Sentry(host)

        with host as value:
            self.assertEqual(value, "host value")

        self.assertEqual(events, ["enter", "exit"])
        self.assertIn(host, Sentry)                                   # `with` does not Rip for TOP

    def test_action_context_dunders_remain_ordinary_python(self) -> None:
        events: list[str] = []

        class Private(Tag):
            @Secret
            @Record
            def key(agent):
                return "open"

        class Context(Tag):
            def __enter__(agent):
                Private(agent)                                     # the hook introduces the first Secret
                events.append(f"enter: {agent.key}")
                return agent.key

            def __exit__(agent, kind, value, traceback):
                events.append(f"exit: {agent.key}")

        ari = Agent()
        Context(ari)

        with ari as value:
            self.assertEqual(value, "open")

            with self.assertRaises(AttributeError):
                _ = ari.key                                         # entry closed its door before the block

        self.assertEqual(events, ["enter: open", "exit: open"])
        self.assertIn(ari, Context)                                   # its Actions decide; TOP adds no Rip

    def test_async_action_context_dunders_remain_ordinary_python(self) -> None:
        import asyncio

        events: list[str] = []

        class Private(Tag):
            @Secret
            @Record
            def key(agent):
                return "open"

        class Context(Tag):
            async def __aenter__(agent):
                await asyncio.sleep(0)
                Private(agent)                                     # the hook introduces the first Secret
                await asyncio.sleep(0)
                events.append(f"enter: {agent.key}")
                return agent.key

            async def __aexit__(agent, kind, value, traceback):
                await asyncio.sleep(0)
                events.append(f"exit: {agent.key}")

        ari = Agent()
        Context(ari)

        async def use_context() -> None:
            async with ari as value:
                self.assertEqual(value, "open")

                with self.assertRaises(AttributeError):
                    _ = ari.key

        asyncio.run(use_context())

        self.assertEqual(events, ["enter: open", "exit: open"])
        self.assertIn(ari, Context)

    def test_context_actions_read_secrets_but_the_block_does_not(self) -> None:
        events: list[tuple[str, str, type | None]] = []

        class Replacement(Tag):
            def __exit__(agent, kind, value, traceback):
                events.append(("replacement", agent.key, kind))
                return False

        class Context(Tag):
            @Secret
            @Record
            def key(agent):
                return agent.name

            def __enter__(agent):
                events.append(("enter", agent.key, None))

                if agent.name == "bo":
                    Replacement(agent)                              # Python already captured Context.__exit__

                return agent

            def __exit__(agent, kind, value, traceback):
                events.append(("exit", agent.key, kind))
                return kind is LookupError

        ari = Agent()
        ari.name = "ari"
        bo = Agent()
        bo.name = "bo"
        Context(ari)
        Context(bo)

        self.assertIs(type(ari), type(bo))                           # raw Actions key the shared type

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", TagOverwriteWarning)

            for agent in (ari, bo):
                with agent as value:
                    self.assertIs(value, agent)

                    with self.assertRaises(AttributeError):
                        _ = agent.key                                # entry did not leave the door open

                    raise LookupError("suppressed by the captured exit Action")

                with self.assertRaises(AttributeError):
                    _ = agent.key                                    # exit closed the door too

        self.assertEqual(
                events,
                [
                        ("enter", "ari", None),
                        ("exit", "ari", LookupError),
                        ("enter", "bo", None),
                        ("exit", "bo", LookupError),
                        ],
                )

    def test_context_action_failure_closes_the_composition_door(self) -> None:
        class Broken_Context(Tag):
            @Secret
            @Record
            def key(agent):
                return "inside"

            def __enter__(agent):
                _ = agent.key
                raise RuntimeError("entry failed")

            def __exit__(agent, kind, value, traceback):
                raise AssertionError("Python does not exit a context that did not enter")

        ari = Agent()
        Broken_Context(ari)

        with self.assertRaisesRegex(RuntimeError, "entry failed"):
            with ari:
                self.fail("the block must not run")

        with self.assertRaises(AttributeError):
            _ = ari.key

    def test_context_action_keeps_an_explicit_host_underlay(self) -> None:
        events: list[str] = []

        class Host:
            def __enter__(self):
                events.append("host enter")
                return self

            def __exit__(self, kind, value, traceback):
                events.append("host exit")
                return kind is ValueError

        class Context(Tag):
            @Secret
            @Record
            def key(agent):
                return "open"

            @Underlay
            def __enter__(agent, underlay):
                events.append(f"TOP enter: {agent.key}")
                return underlay()

            @Underlay
            def __exit__(agent, underlay, kind, value, traceback):
                events.append(f"TOP exit: {agent.key}")
                return underlay()

        host = Host()
        Context(host)

        with host as value:
            self.assertIs(value, host)
            raise ValueError("the host suppresses this")

        self.assertEqual(
                events,
                ["TOP enter: open", "host enter", "TOP exit: open", "host exit"],
                )

    def test_async_context_actions_have_a_context_local_door_across_await(self) -> None:
        import asyncio
        from contextvars import copy_context

        events: list[tuple[str, str, type | None]] = []
        captured_contexts = []
        task_references = []

        async def scenario() -> None:
            entry_waiting = asyncio.Event()
            release_entry = asyncio.Event()
            exit_waiting = asyncio.Event()
            release_exit = asyncio.Event()

            class Context(Tag):
                @Secret
                @Record
                def key(agent):
                    return "open"

                async def __aenter__(agent):
                    captured_contexts.append(copy_context())

                    async def child_task() -> None:
                        self.assertEqual(agent.key, "open")          # work delegated by the hook
                        self.assertTrue("key" @ agent)

                    await asyncio.create_task(child_task())
                    entry_waiting.set()
                    await release_entry.wait()
                    events.append(("enter", agent.key, None))
                    self.assertTrue("key" @ agent)
                    self.assertEqual(agent.Context.key, "open")
                    return agent

                async def __aexit__(agent, kind, value, traceback):
                    exit_waiting.set()
                    await release_exit.wait()
                    events.append(("exit", agent.key, kind))
                    return kind is LookupError

            ari = Agent()
            Context(ari)

            async def use_context() -> None:
                async with ari as value:
                    self.assertIs(value, ari)

                    with self.assertRaises(AttributeError):
                        _ = ari.key                                 # the block is outside composition

                    raise LookupError("suppressed by the async Action")

                with self.assertRaises(AttributeError):
                    captured_contexts[0].run(lambda: ari.key)        # a closed door cannot be replayed

            async def sibling_task() -> None:
                await entry_waiting.wait()

                with self.assertRaises(AttributeError):
                    _ = ari.key                                     # entry awaits in another task

                self.assertFalse("key" @ ari)

                with self.assertRaises(AttributeError):
                    _ = ari.Context.key

                release_entry.set()
                await exit_waiting.wait()

                with self.assertRaises(AttributeError):
                    _ = ari.key                                     # exit awaits in another task

                release_exit.set()

            using = asyncio.create_task(use_context())
            task_references.append(weakref.ref(using))
            sibling = asyncio.create_task(sibling_task())           # created before either door opens
            await asyncio.gather(using, sibling)

            with self.assertRaises(AttributeError):
                _ = ari.key

        asyncio.run(scenario())
        gc.collect()

        self.assertEqual(
                events,
                [("enter", "open", None), ("exit", "open", LookupError)],
                )
        self.assertIsNone(task_references[0]())                       # captured context retains no Task

    def test_cancelled_async_entry_closes_the_composition_door(self) -> None:
        import asyncio

        async def scenario() -> None:
            started = asyncio.Event()
            release = asyncio.Event()

            class Waiting_Context(Tag):
                @Secret
                @Record
                def key(agent):
                    return "open"

                async def __aenter__(agent):
                    await asyncio.sleep(0)
                    self.assertEqual(agent.key, "open")
                    started.set()
                    await release.wait()
                    return agent

                async def __aexit__(agent, kind, value, traceback):
                    return False

            ari = Agent()
            Waiting_Context(ari)

            async def enter() -> None:
                async with ari:
                    self.fail("cancelled entry must not reach the block")

            task = asyncio.create_task(enter())
            await started.wait()
            task.cancel()

            with self.assertRaises(asyncio.CancelledError):
                await task

            with self.assertRaises(AttributeError):
                _ = ari.key

        asyncio.run(scenario())

    def test_a_hosts_async_context_protocol_survives_secret_tagging(self) -> None:
        import asyncio

        events: list[str] = []

        class Host:
            async def __aenter__(self):
                await asyncio.sleep(0)
                events.append("enter")
                return "host value"

            async def __aexit__(self, kind, value, traceback):
                await asyncio.sleep(0)
                events.append("exit")

        class Has_Secret(Tag):
            @Secret
            @Record
            def key(agent):
                return "private"

        host = Host()
        Has_Secret(host)

        async def use_context() -> None:
            async with host as value:
                self.assertEqual(value, "host value")

        asyncio.run(use_context())

        self.assertEqual(events, ["enter", "exit"])
        self.assertIn(host, Has_Secret)

    def test_scope_is_no_longer_exported(self) -> None:
        import TopKit
        import TopKit.lifecycle

        with self.assertRaises(ImportError):
            from TopKit import Scope                                  # removed: tag before try, Rip in finally

        self.assertNotIn("Scope", TopKit.__all__)
        self.assertFalse(hasattr(TopKit, "Scope"))
        self.assertFalse(hasattr(TopKit.lifecycle, "Scope"))
