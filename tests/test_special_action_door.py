"""Synchronous value Actions compose; lookup and write hooks remain outside."""

import operator
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

    def test_item_query_and_write_hooks_do_not_authorize_outside_access(self):
        class Private(Tag):
            @Secret
            @Record
            def code(agent):
                return "inside"

            @Action
            def Inspect(agent):
                return agent["code"]

            def __getitem__(agent, key):
                return agent.code

            def __setitem__(agent, key, value):
                agent.code = value

            def __delitem__(agent, key):
                del agent.code

            def __contains__(agent, key):
                return key == agent.code

        agent = Host()
        Private(agent)

        self.assertEqual(agent.Inspect(), "inside")
        with self.assertRaises(AttributeError):
            agent["code"]
        with self.assertRaises(AttributeError):
            agent["code"] = "outside"
        with self.assertRaises(AttributeError):
            del agent["code"]
        with self.assertRaises(AttributeError):
            "inside" in agent
        self.assertEqual(agent.Inspect(), "inside")

    def test_iteration_hooks_do_not_open_an_ambient_door(self):
        class Private(Tag):
            @Secret
            @Record
            def code(agent):
                return "inside"

            def __iter__(agent):
                return iter(agent.code)

            def __next__(agent):
                return agent.code

            def __reversed__(agent):
                return reversed(agent.code)

            def __length_hint__(agent):
                return len(agent.code)

        agent = Host()
        Private(agent)

        for query in (iter, next, reversed, operator.length_hint):
            with self.subTest(query=query.__name__):
                with self.assertRaises(AttributeError):
                    query(agent)


if __name__ == "__main__":
    unittest.main()
