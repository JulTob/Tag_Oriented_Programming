"""Synchronous Python value protocols obey an authored Action's door."""

import unittest

from TopKit import Action, Record, Secret, Tag, Underlay


class Host:
    pass


class SpecialActionDoorTests(unittest.TestCase):
    def test_python_protocol_and_explicit_action_read_the_same_secret(self):
        class Private(Tag):
            @Secret
            @Record
            def code(agent):
                return "inside"

            @Action
            def Read(agent):
                return agent.code

            def __str__(agent):
                return agent.code

            def __len__(agent):
                return len(agent.code)

            def __add__(agent, suffix):
                return agent.code + suffix

        agent = Host()
        Private(agent)

        self.assertEqual(agent.Read(), "inside")
        self.assertEqual(str(agent), "inside")
        self.assertEqual(agent.__str__(), "inside")
        self.assertEqual(len(agent), 6)
        self.assertEqual(agent + "!", "inside!")
        with self.assertRaises(AttributeError):
            agent.code

    def test_protocol_failure_closes_the_door_and_underlays_share_it(self):
        class Private(Tag):
            @Secret
            @Record
            def code(agent):
                return "inside"

            def __str__(agent):
                return agent.code

        class Shape(Private):
            @Underlay
            def __str__(agent, underlay):
                self.assertEqual(agent.code, "inside")
                self.assertEqual(underlay(), "inside")
                raise LookupError("stop")

        agent = Host()
        Shape(agent)

        with self.assertRaisesRegex(LookupError, "stop"):
            str(agent)
        with self.assertRaises(AttributeError):
            agent.code

    def test_a_host_protocol_does_not_open_a_top_action_door(self):
        class HostProtocol:
            def __str__(agent):
                return agent.code

            def __len__(agent):
                return 3

        class Private(Tag):
            @Secret
            @Record
            def code(agent):
                return "inside"

        agent = HostProtocol()
        Private(agent)

        self.assertEqual(len(agent), 3)
        with self.assertRaises(AttributeError):
            str(agent)
        with self.assertRaises(AttributeError):
            agent.code

    def test_an_untrained_instance_of_the_runtime_type_remains_constructible(self):
        class Label(Tag):
            def __str__(agent):
                return "label"

        agent = Host()
        Label(agent)
        untrained = type(agent)()

        self.assertEqual(str(untrained), "label")

    def test_callable_object_protocol_keeps_its_python_binding(self):
        class Representation:
            def __call__(self):
                return "callable object"

            def __getattribute__(self, name):
                if name in ("__module__", "__name__", "__qualname__",
                            "__doc__", "__annotations__", "__dict__"):
                    raise RuntimeError("metadata is not needed")
                return object.__getattribute__(self, name)

        class Label(Tag):
            __str__ = Representation()

        agent = Host()
        Label(agent)

        self.assertEqual(str(agent), "callable object")

    def test_attribute_miss_hook_cannot_authorize_its_own_secret_read(self):
        class Private(Tag):
            @Secret
            @Record
            def code(agent):
                return "inside"

            def __getattr__(agent, name):
                if name == "code":
                    raise AttributeError(name)
                return agent.code

        agent = Host()
        Private(agent)

        with self.assertRaises(AttributeError):
            agent.missing
        with self.assertRaises(AttributeError):
            agent.code


if __name__ == "__main__":
    unittest.main()
