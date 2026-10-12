"""Ordinary Python context hooks release their composition authority."""

from __future__ import annotations

from contextvars import Context
from contextvars import copy_context
import gc
import unittest
import weakref

from TopKit import Record
from TopKit import Secret
from TopKit import Tag


class Agent:
    pass


class Pause:
    def __await__(self):
        yield


class Test_Context_Finalization(unittest.TestCase):
    def test_async_hooks_can_close_in_a_different_context(self) -> None:
        for name, args in (
                ("__aenter__", ()),
                ("__aexit__", (None, None, None)),
                ):
            with self.subTest(hook=name):
                captured = []
                closed = []

                class Hooks(Tag):
                    @Secret
                    @Record
                    def key(agent):
                        return "private"

                    async def __aenter__(agent):
                        self.assertEqual(agent.key, "private")
                        captured.append(copy_context())

                        try:
                            await Pause()
                        finally:
                            closed.append("entry")

                    async def __aexit__(agent, kind, value, traceback):
                        self.assertEqual(agent.key, "private")
                        captured.append(copy_context())

                        try:
                            await Pause()
                        finally:
                            closed.append("exit")

                agent = Agent()
                Hooks(agent)
                origin = Context()
                finalizer = Context()
                hook = getattr(type(agent), name)(agent, *args)
                origin.run(hook.send, None)
                finalizer.run(hook.close)

                self.assertEqual(len(closed), 1)

                for context in (origin, finalizer, captured[0]):
                    with self.assertRaises(AttributeError):
                        context.run(lambda: agent.key)

                    self.assertFalse(context.run(lambda: "key" @ agent))

                reference = weakref.ref(agent)
                del agent
                gc.collect()
                self.assertIsNone(reference())

    def test_cross_context_close_preserves_the_hooks_own_failure(self) -> None:
        failure = RuntimeError("hook cleanup failed")
        captured = []

        class Hooks(Tag):
            @Secret
            @Record
            def key(agent):
                return "private"

            async def __aenter__(agent):
                self.assertEqual(agent.key, "private")
                captured.append(copy_context())

                try:
                    await Pause()
                finally:
                    raise failure

        agent = Agent()
        Hooks(agent)
        origin = Context()
        hook = type(agent).__aenter__(agent)
        origin.run(hook.send, None)

        with self.assertRaises(RuntimeError) as caught:
            Context().run(hook.close)

        self.assertIs(caught.exception, failure)

        for context in (origin, captured[0]):
            with self.assertRaises(AttributeError):
                context.run(lambda: agent.key)

    def test_closing_one_hook_preserves_another_active_door(self) -> None:
        class Hooks(Tag):
            @Secret
            @Record
            def key(agent):
                return "private"

            async def __aenter__(agent):
                self.assertEqual(agent.key, "private")
                await Pause()
                return agent.key

        first = Agent()
        second = Agent()
        Hooks(first)
        Hooks(second)
        context = Context()
        first_hook = type(first).__aenter__(first)
        second_hook = type(second).__aenter__(second)

        try:
            context.run(first_hook.send, None)
            context.run(second_hook.send, None)
            context.run(first_hook.close)

            with self.assertRaises(AttributeError):
                context.run(lambda: first.key)

            self.assertEqual(context.run(lambda: second.key), "private")

            with self.assertRaises(StopIteration) as finished:
                context.run(second_hook.send, None)

            self.assertEqual(finished.exception.value, "private")

            with self.assertRaises(AttributeError):
                context.run(lambda: second.key)
        finally:
            context.run(first_hook.close)
            context.run(second_hook.close)

    def test_cross_context_close_preserves_the_finalizers_active_door(self) -> None:
        class Hooks(Tag):
            @Secret
            @Record
            def key(agent):
                return "private"

            async def __aenter__(agent):
                self.assertEqual(agent.key, "private")
                await Pause()
                return agent.key

        first = Agent()
        second = Agent()
        Hooks(first)
        Hooks(second)
        origin = Context()
        finalizer = Context()
        first_hook = type(first).__aenter__(first)
        second_hook = type(second).__aenter__(second)

        try:
            origin.run(first_hook.send, None)
            finalizer.run(second_hook.send, None)
            finalizer.run(first_hook.close)
            self.assertEqual(finalizer.run(lambda: second.key), "private")

            with self.assertRaises(AttributeError):
                origin.run(lambda: first.key)
        finally:
            origin.run(first_hook.close)
            finalizer.run(second_hook.close)
