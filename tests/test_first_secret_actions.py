"""Current synchronous Actions compose before the first Secret exists."""

import gc
import unittest
import weakref

from TopKit import Action, Pin, Record, Secret, Tag, Underlay


class Host:
    pass


class FirstSecretActionTests(unittest.TestCase):
    def receiver(self, pinned=False):
        class Private(Tag):
            @Secret
            @Record
            def code(agent):
                return "private"

            @Secret
            @Action
            def SecretRead(agent):
                return agent.code

        class Reader(Tag):
            @Action
            def Read(agent):
                """Read the current private Contribution."""
                return (agent.code, Private[agent].code,
                        "code" @ agent, "code" @ Private[agent],
                        agent.SecretRead())

            @Action
            def Prepare(agent):
                Private(agent)
                return (agent.code, Private[agent].code,
                        "code" @ agent, "code" @ Private[agent],
                        agent.SecretRead())

            @Action
            def Capture(agent):
                Private(agent)
                return agent.SecretRead

            @Action
            def Fail(agent, error):
                Private(agent)
                self.assertEqual(agent.code, "private")
                raise error

        if pinned:
            Private = Pin(Private)
            Reader = Pin(Reader)

            class Target(Tag):
                pass

            agent = Target
        else:
            agent = Host()

        Reader(agent)
        return agent, Private

    def test_public_action_can_introduce_and_read_the_first_secret(self):
        for pinned in (False, True):
            with self.subTest(pinned=pinned):
                agent, private = self.receiver(pinned)
                self.assertEqual(agent.Prepare(),
                                 ("private", "private", True, True, "private"))
                self.assert_closed(agent, private)

    def test_public_handle_captured_before_secrets_still_composes(self):
        for pinned in (False, True):
            with self.subTest(pinned=pinned):
                agent, private = self.receiver(pinned)
                read = agent.Read
                private(agent)

                self.assertEqual(read.__name__, "Read")
                self.assertEqual(read.__doc__, "Read the current private Contribution.")
                self.assertEqual(read(),
                                 ("private", "private", True, True, "private"))
                self.assert_closed(agent, private)

    def test_captured_public_action_can_itself_introduce_the_first_secret(self):
        for pinned in (False, True):
            with self.subTest(pinned=pinned):
                agent, private = self.receiver(pinned)
                prepare = agent.Prepare
                self.assertEqual(prepare(),
                                 ("private", "private", True, True, "private"))
                self.assert_closed(agent, private)

    def test_first_secret_action_capture_does_not_authorize_itself(self):
        for pinned in (False, True):
            with self.subTest(pinned=pinned):
                agent, private = self.receiver(pinned)
                handle = agent.Capture()
                with self.assertRaises(AttributeError):
                    handle()
                self.assertEqual(agent.Read(),
                                 ("private", "private", True, True, "private"))
                self.assert_closed(agent, private)

    def test_first_secret_and_action_failure_close_the_door(self):
        for pinned in (False, True):
            for error in (LookupError("stop"), KeyboardInterrupt(), SystemExit(7)):
                with self.subTest(pinned=pinned, error=type(error).__name__):
                    agent, private = self.receiver(pinned)
                    fail = agent.Fail
                    with self.assertRaises(type(error)) as caught:
                        fail(error)
                    self.assertIs(caught.exception, error)
                    self.assert_closed(agent, private)

    def test_underlay_chain_keeps_composition_open_after_first_secret(self):
        class Private(Tag):
            @Secret
            @Record
            def code(agent):
                return "private"

        class Reader(Tag):
            @Action
            def Prepare(agent):
                Private(agent)
                return agent.code

        class Shape(Reader):
            @Underlay
            def Prepare(agent, underlay):
                return underlay(), agent.code

        agent = Host()
        Shape(agent)
        prepare = agent.Prepare
        self.assertEqual(prepare(), ("private", "private"))
        with self.assertRaises(AttributeError):
            agent.code

    def test_plain_host_method_does_not_gain_a_top_composition_door(self):
        class Private(Tag):
            @Secret
            @Record
            def code(agent):
                return "private"

        class PlainHost:
            def Prepare(agent):
                Private(agent)
                return agent.code

        agent = PlainHost()
        with self.assertRaises(AttributeError):
            agent.Prepare()
        with self.assertRaises(AttributeError):
            agent.code

    def test_public_handle_keeps_an_ordinary_agent_weakly(self):
        agent, private = self.receiver()
        prepare = agent.Prepare
        reference = weakref.ref(agent)
        del agent
        gc.collect()

        self.assertIsNone(reference())
        self.assertEqual(list(private[:]), [])
        with self.assertRaises(ReferenceError):
            prepare()

    def test_public_pin_handle_preserves_its_existing_strong_receiver(self):
        target, private = self.receiver(pinned=True)
        prepare = target.Prepare
        reference = weakref.ref(target)
        del target
        gc.collect()

        self.assertIsNotNone(reference())
        self.assertEqual(prepare(),
                         ("private", "private", True, True, "private"))
        del prepare
        gc.collect()
        self.assertIsNone(reference())
        self.assertEqual(list(private[:]), [])

    def test_a_host_context_can_invoke_a_captured_public_top_action(self):
        class ContextHost:
            def __enter__(agent):
                return agent.prepare()

            def __exit__(agent, kind, value, traceback):
                return False

        class Private(Tag):
            @Secret
            @Record
            def code(agent):
                return "private"

        class Reader(Tag):
            @Action
            def Prepare(agent):
                Private(agent)
                return agent.code

        agent = ContextHost()
        Reader(agent)
        agent.prepare = agent.Prepare

        with agent as value:
            self.assertEqual(value, "private")
            with self.assertRaises(AttributeError):
                agent.code
        with self.assertRaises(AttributeError):
            agent.code

    def assert_closed(self, agent, private):
        for name in ("code", "SecretRead"):
            with self.assertRaises(AttributeError):
                getattr(agent, name)
            self.assertFalse(name @ agent)
            self.assertFalse(name @ private[agent])


if __name__ == "__main__":
    unittest.main()
