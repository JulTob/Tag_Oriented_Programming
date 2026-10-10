"""Synchronous view Actions run inside their bound Agent's composition."""

import gc
import unittest
import weakref

from TopKit import Action, Delete, Pin, Pre, Record, Secret, Tag, TagPreconditionError


class Host:
    pass


class ViewActionTests(unittest.TestCase):
    def test_a_view_action_reads_the_same_secrets_as_the_current_action(self):
        class Fire(Tag):
            @Secret
            @Record
            def heat(agent):
                return 3

            @Action
            def Strike(agent, factor=2):
                return agent.heat * factor

        agent = Host()
        Fire(agent)

        self.assertEqual(agent.Strike(factor=4), 12)
        self.assertEqual(Fire[agent].Strike(factor=4), 12)
        self.assertEqual(agent.Fire.Strike(), 6)
        self.assert_closed(agent, Fire, "heat")

    def test_the_view_selects_its_action_but_reads_the_current_agent(self):
        class Base(Tag):
            @Secret
            @Record
            def code(agent):
                return "base"

            @Action
            def Inspect(agent):
                return "base action", agent.code, Base[agent].code

        class Shape(Base):
            @Secret
            @Record
            def code(agent, stored):
                return "shape"

            @Action
            def Inspect(agent):
                return "shape action", agent.code

        agent = Host()
        Shape(agent)

        self.assertEqual(agent.Inspect(), ("shape action", "shape"))
        self.assertEqual(Base[agent].Inspect(), ("base action", "shape", "base"))
        self.assertEqual(Shape[agent].Inspect(), ("shape action", "shape"))
        self.assert_closed(agent, Base, "code")
        self.assert_closed(agent, Shape, "code")

    def test_a_view_action_can_read_secrets_contributed_by_another_tag(self):
        class Reader(Tag):
            @Action
            def Inspect(agent):
                return agent.code, Private[agent].code, "code" @ Private[agent]

        class Private(Tag):
            @Secret
            @Record
            def code(agent):
                return "private"

        agent = Host()
        Reader(agent)
        Private(agent)

        self.assertEqual(agent.Inspect(), ("private", "private", True))
        self.assertEqual(Reader[agent].Inspect(), ("private", "private", True))
        self.assert_closed(agent, Private, "code")

    def test_a_pin_view_action_opens_the_pinned_tags_composition(self):
        @Pin
        class Sealed(Tag):
            @Secret
            @Record
            def code(tag):
                return "pin"

            @Action
            def Inspect(tag):
                return tag.code, Sealed[tag].code

        class Wizard(Tag):
            pass

        Sealed(Wizard)

        self.assertEqual(Wizard.Inspect(), ("pin", "pin"))
        self.assertEqual(Sealed[Wizard].Inspect(), ("pin", "pin"))
        self.assert_closed(Wizard, Sealed, "code")

    def test_a_view_action_keeps_its_door_open_when_it_introduces_the_first_secret(self):
        class Private(Tag):
            @Secret
            @Record
            def code(agent):
                return "new secret"

        class Reader(Tag):
            @Action
            def Prepare(agent):
                Private(agent)
                return agent.code, Private[agent].code, "code" @ agent

        agent = Host()
        Reader(agent)

        self.assertEqual(Reader[agent].Prepare(), ("new secret", "new secret", True))
        self.assert_closed(agent, Private, "code")

    def test_view_action_exits_close_the_door_even_on_python_interruptions(self):
        for error in (LookupError("stop"), KeyboardInterrupt(), SystemExit(7)):
            with self.subTest(error=type(error).__name__):
                class Private(Tag):
                    @Secret
                    @Record
                    def code(agent):
                        return "private"

                    @Action
                    def Fail(agent):
                        self.assertEqual(agent.code, "private")
                        raise error

                agent = Host()
                Private(agent)

                with self.assertRaises(type(error)) as caught:
                    Private[agent].Fail()
                self.assertIs(caught.exception, error)
                self.assert_closed(agent, Private, "code")

    def test_nested_view_actions_close_only_the_door_they_opened(self):
        class Private(Tag):
            @Secret
            @Record
            def code(agent):
                return "private"

            @Action
            def Fail(agent):
                self.assertEqual(agent.code, "private")
                raise LookupError("inner")

            @Action
            def Continue(agent):
                try:
                    Private[agent].Fail()
                except LookupError:
                    return agent.code

        agent = Host()
        Private(agent)

        self.assertEqual(Private[agent].Continue(), "private")
        self.assert_closed(agent, Private, "code")

    def test_an_action_captured_from_a_view_keeps_its_agent_weakly(self):
        class Worker(Tag):
            @Action
            def Work(agent, value):
                """Return the received value."""
                return value

        agent = Host()
        Worker(agent)
        action = Worker[agent].Work

        self.assertEqual(action("done"), "done")
        self.assertEqual(action.__name__, "Work")
        self.assertEqual(action.__doc__, "Return the received value.")
        self.assertIs(action.__func__, Worker.__dict__["Work"])
        reference = weakref.ref(agent)
        del agent
        gc.collect()

        self.assertIsNone(reference())
        with self.assertRaises(ReferenceError):
            action("gone")

    def test_a_captured_secret_view_action_requires_an_already_open_door(self):
        captured = []

        class Private(Tag):
            @Secret
            @Record
            def code(agent):
                return "private"

            @Secret
            @Action
            def Read(agent):
                """Read the private code."""
                return agent.code

            @Action
            def Capture(agent):
                captured.append(Private[agent].Read)
                return captured[-1]()

        agent = Host()
        Private(agent)

        self.assertEqual(agent.Capture(), "private")
        self.assertEqual(Private[agent].Capture(), "private")
        for action in captured:
            self.assertEqual(action.__name__, "Read")
            self.assertEqual(action.__doc__, "Read the private code.")
            self.assertIs(action.__func__, Private.__dict__["Read"])
            with self.assertRaises(AttributeError):
                action()
        self.assert_closed(agent, Private, "code")
        self.assert_closed(agent, Private, "Read")

        reference = weakref.ref(agent)
        del agent
        gc.collect()
        self.assertIsNone(reference())
        with self.assertRaises(ReferenceError):
            captured[0]()

    def test_a_captured_view_action_retains_its_secret_boundary_after_a_public_layer(self):
        captured = []

        class Private(Tag):
            @Secret
            @Action
            def Read(agent):
                return "private"

            @Action
            def Capture(agent):
                captured.append(Private[agent].Read)
                return captured[-1]()

        class Removed(Private):
            @Delete
            def Read(agent): ...

        class Public(Removed):
            @Action
            def Read(agent):
                return "public"

        agent = Host()
        Private(agent)
        self.assertEqual(agent.Capture(), "private")
        Public(agent)

        self.assertEqual(agent.Read(), "public")
        with self.assertRaises(AttributeError):
            captured[0]()

    def test_another_agents_composition_does_not_authorize_a_secret_view_action(self):
        captured = []

        class Private(Tag):
            @Secret
            @Action
            def Read(agent):
                return "private"

            @Action
            def Capture(agent):
                captured.append(Private[agent].Read)

            @Action
            def Invoke(agent, action):
                return action()

        target, other = Host(), Host()
        Private(target)
        Private(other)
        target.Capture()

        with self.assertRaises(AttributeError):
            Private[other].Invoke(captured[0])
        self.assert_closed(target, Private, "Read")
        self.assert_closed(other, Private, "Read")

    def test_a_captured_secret_pin_view_action_also_requires_an_open_door(self):
        captured = []

        @Pin
        class Private(Tag):
            @Secret
            @Action
            def Read(tag):
                return "private"

            @Action
            def Capture(tag):
                captured.append(Private[tag].Read)
                return captured[-1]()

        class Wizard(Tag):
            pass

        Private(Wizard)
        self.assertEqual(Private[Wizard].Capture(), "private")
        with self.assertRaises(AttributeError):
            captured[0]()
        self.assert_closed(Wizard, Private, "Read")

    def test_a_refused_tagging_does_not_close_its_calling_view_actions_door(self):
        class Refused(Tag):
            @Pre
            def No(agent):
                return False

        class Private(Tag):
            @Secret
            @Record
            def code(agent):
                return "private"

            @Action
            def Try(agent):
                try:
                    Refused(agent)
                except TagPreconditionError.No:
                    return agent.code

        agent = Host()
        Private(agent)

        self.assertEqual(Private[agent].Try(), "private")
        self.assert_closed(agent, Private, "code")

    def assert_closed(self, agent, tag, name):
        with self.assertRaises(AttributeError):
            getattr(agent, name)
        with self.assertRaises(AttributeError):
            getattr(tag[agent], name)
        self.assertFalse(name @ agent)
        self.assertFalse(name @ tag[agent])


if __name__ == "__main__":
    unittest.main()
