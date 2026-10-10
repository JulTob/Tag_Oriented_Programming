"""Captured synchronous Secret Actions retain their Agent's access boundary."""

import asyncio
import gc
import unittest
import weakref

from TopKit import Action, Constant, Delete, Record, Secret, Tag


class Host:
    pass


class SecretActionHandleTests(unittest.TestCase):
    def test_captured_secret_and_constant_secret_actions_require_composition(self):
        for constant in (False, True):
            with self.subTest(constant=constant):
                def Read(agent, suffix=""):
                    """Read the private value."""
                    return agent.code + suffix

                declaration = Secret(Action(Read))
                if constant:
                    declaration = Constant(declaration)

                class Private(Tag):
                    Read = declaration

                    @Secret
                    @Record
                    def code(agent):
                        return "private"

                    @Action
                    def Capture(agent):
                        return agent.Read

                    @Action
                    def Invoke(agent, action):
                        return action(suffix=" authorized")

                agent = Host()
                Private(agent)
                handle = agent.Capture()

                self.assertEqual(handle.__name__, "Read")
                self.assertEqual(handle.__doc__, "Read the private value.")
                self.assertIs(handle.__func__, declaration)
                with self.assertRaises(AttributeError):
                    handle()
                self.assertEqual(agent.Invoke(handle), "private authorized")
                with self.assertRaises(AttributeError):
                    handle()
                self.assert_closed(agent, "Read", "code")

    def test_current_and_view_handles_keep_the_selected_implementation(self):
        class Base(Tag):
            @Secret
            @Action
            def Read(agent):
                return "base"

            @Action
            def Capture(agent):
                return agent.Read, Base[agent].Read

            @Action
            def Invoke(agent, action):
                return action()

        class Shape(Base):
            @Secret
            @Action
            def Read(agent):
                return "shape"

        agent = Host()
        Shape(agent)
        current, captured_view = agent.Capture()

        self.assertEqual(agent.Invoke(current), "shape")
        self.assertEqual(agent.Invoke(captured_view), "base")
        for handle in (current, captured_view):
            with self.assertRaises(AttributeError):
                handle()
        self.assert_closed(agent, "Read")

    def test_action_record_category_changes_do_not_remove_captured_secrecy(self):
        class Data(Tag):
            @Secret
            @Record
            def value(agent):
                return None

            @Action
            def Capture(agent):
                return agent.value

            @Action
            def Invoke(agent, action):
                return action()

        class Behaviour(Data):
            @Secret
            @Action
            def value(agent):
                return "captured action"

        class DataAgain(Behaviour):
            @Secret
            @Record
            def value(agent):
                return False

        agent = Host()
        Behaviour(agent)
        handle = agent.Capture()
        DataAgain(agent)

        self.assertIs(agent.Capture(), False)
        self.assertEqual(agent.Invoke(handle), "captured action")
        with self.assertRaises(AttributeError):
            handle()
        self.assert_closed(agent, "value")

    def test_a_public_replacement_does_not_authorize_the_old_secret_handle(self):
        class Private(Tag):
            @Secret
            @Action
            def Read(agent):
                return "private"

            @Action
            def Capture(agent):
                return agent.Read

            @Action
            def Invoke(agent, action):
                return action()

        class Removed(Private):
            @Delete
            def Read(agent): ...

        class Public(Removed):
            @Action
            def Read(agent):
                return "public"

        agent = Host()
        Private(agent)
        handle = agent.Capture()
        Public(agent)

        self.assertEqual(agent.Read(), "public")
        self.assertEqual(agent.Invoke(handle), "private")
        with self.assertRaises(AttributeError):
            handle()

    def test_binding_deletion_does_not_authorize_a_captured_secret_handle(self):
        class Private(Tag):
            @Secret
            @Action
            def Read(agent):
                return "private"

            @Action
            def Capture(agent):
                return agent.Read

            @Action
            def Remove(agent):
                del agent.Read

            @Action
            def Invoke(agent, action):
                return action()

        agent = Host()
        Private(agent)
        handle = agent.Capture()
        agent.Remove()

        self.assertEqual(agent.Invoke(handle), "private")
        with self.assertRaises(AttributeError):
            handle()
        self.assert_closed(agent, "Read")

    def test_rip_and_reapplication_preserve_captured_secrecy(self):
        class Private(Tag):
            @Secret
            @Constant
            @Action
            def Read(agent):
                return "private"

            @Action
            def Capture(agent):
                return agent.Read

            @Action
            def Invoke(agent, action):
                return action()

        agent = Host()
        Private(agent)
        handle = agent.Capture()
        del Private[agent]

        self.assertEqual(agent.Invoke(handle), "private")
        with self.assertRaises(AttributeError):
            handle()
        Private(agent)
        self.assertEqual(agent.Invoke(handle), "private")
        with self.assertRaises(AttributeError):
            handle()
        self.assert_closed(agent, "Read")

    def test_another_agents_open_door_does_not_authorize_the_handle(self):
        class Private(Tag):
            @Secret
            @Action
            def Read(agent):
                return "private"

            @Action
            def Capture(agent):
                return agent.Read

            @Action
            def Invoke(agent, action):
                return action()

        target, other = Host(), Host()
        Private(target)
        Private(other)
        handle = target.Capture()

        with self.assertRaises(AttributeError):
            other.Invoke(handle)
        self.assert_closed(target, "Read")
        self.assert_closed(other, "Read")

    def test_a_captured_secret_handle_keeps_its_agent_weakly(self):
        class Private(Tag):
            @Secret
            @Action
            def Read(agent):
                return "private"

            @Action
            def Capture(agent):
                return agent.Read

        agent = Host()
        Private(agent)
        handle = agent.Capture()
        reference = weakref.ref(agent)
        del agent
        gc.collect()

        self.assertIsNone(reference())
        with self.assertRaises(ReferenceError):
            handle()

    def test_secret_action_failure_does_not_close_the_callers_door(self):
        for error in (LookupError("stop"), KeyboardInterrupt(), SystemExit(7)):
            with self.subTest(error=type(error).__name__):
                class Private(Tag):
                    @Secret
                    @Record
                    def code(agent):
                        return "private"

                    @Secret
                    @Action
                    def Fail(agent):
                        self.assertEqual(agent.code, "private")
                        raise error

                    @Action
                    def Continue(agent):
                        try:
                            agent.Fail()
                        except type(error) as caught:
                            self.assertIs(caught, error)
                            return agent.code

                agent = Host()
                Private(agent)

                self.assertEqual(agent.Continue(), "private")
                self.assert_closed(agent, "Fail", "code")

    def test_async_context_hooks_authorize_synchronous_secret_actions(self):
        captured = []

        class Private(Tag):
            @Secret
            @Record
            def code(agent):
                return "private"

            @Secret
            @Action
            def Read(agent):
                return agent.code

            async def __aenter__(agent):
                captured.append(agent.Read)
                self.assertEqual(captured[-1](), "private")
                await asyncio.sleep(0)
                self.assertEqual(agent.Read(), "private")
                return agent

            async def __aexit__(agent, kind, value, traceback):
                await asyncio.sleep(0)
                self.assertEqual(captured[0](), "private")

        agent = Host()
        Private(agent)

        async def use():
            async with agent:
                with self.assertRaises(AttributeError):
                    captured[0]()
                self.assert_closed(agent, "Read", "code")
            with self.assertRaises(AttributeError):
                captured[0]()

        asyncio.run(use())
        self.assert_closed(agent, "Read", "code")

    def test_closed_async_context_cannot_authorize_an_escaped_constant_handle(self):
        captured, spawned, denied = [], [], []

        class Private(Tag):
            @Constant
            @Secret
            @Action
            def Read(agent):
                return "private"

            async def __aenter__(agent):
                captured.append(agent.Read)
                self.assertEqual(captured[0](), "private")

                async def escaped():
                    await released.wait()
                    with self.assertRaises(AttributeError):
                        captured[0]()
                    denied.append("closed context")

                spawned.append(asyncio.create_task(escaped()))
                return agent

            async def __aexit__(agent, kind, value, traceback):
                self.assertEqual(captured[0](), "private")

        class Other(Tag):
            async def __aenter__(agent):
                with self.assertRaises(AttributeError):
                    captured[0]()
                denied.append("other Agent")
                return agent

            async def __aexit__(agent, kind, value, traceback):
                return False

        target, other = Host(), Host()
        Private(target)
        Other(other)

        async def use():
            async with target:
                with self.assertRaises(AttributeError):
                    captured[0]()
            released.set()
            await spawned[0]
            async with other:
                pass

        released = asyncio.Event()
        asyncio.run(use())
        self.assertEqual(denied, ["closed context", "other Agent"])
        self.assert_closed(target, "Read")

    def assert_closed(self, agent, *names):
        for name in names:
            with self.assertRaises(AttributeError):
                getattr(agent, name)
            self.assertFalse(name @ agent)


if __name__ == "__main__":
    unittest.main()
