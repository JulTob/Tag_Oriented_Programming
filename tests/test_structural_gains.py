"""Agent Gains cannot occupy Python's class and instance-dictionary seats."""

import unittest

from TopKit import Action, Delete, Operation, Public, Record, Report
from TopKit import Tag, TagDeclarationError, Tags


def _member(mark):
    def value(receiver):
        raise AssertionError("a refused declaration must not run")

    return value if mark is None else mark(value)


class StructuralGainTests(unittest.TestCase):
    def test_agent_gains_and_deletes_are_refused_at_declaration(self):
        for name in ("__class__", "__dict__"):
            for mark in (None, Action, Record, Delete):
                with self.subTest(name=name, mark=mark):
                    with self.assertRaisesRegex(TagDeclarationError, name):
                        type("Invalid", (Tag,), {name: _member(mark)})

    def test_published_tag_contributions_cannot_occupy_agent_storage(self):
        for name in ("__class__", "__dict__"):
            for mark in (Report, Operation):
                with self.subTest(name=name, mark=mark):
                    with self.assertRaisesRegex(TagDeclarationError, name):
                        type("Invalid", (Tag,), {name: Public(mark(_member(None)))})

    def test_late_declaration_is_refused_before_touching_agent_or_tag(self):
        class Host:
            pass

        class Member(Tag):
            pass

        agent = Host()
        agent.kept = "host value"
        Member(agent)
        before = dict(vars(agent))
        original_type = type(agent)

        for name in ("__class__", "__dict__"):
            with self.subTest(name=name):
                previous = vars(Member).get(name)
                with self.assertRaisesRegex(TagDeclarationError, name):
                    setattr(Member, name, Record(_member(None)))
                self.assertIs(vars(Member).get(name), previous)
                self.assertIs(type(agent), original_type)
                self.assertEqual(vars(agent), before)
                self.assertEqual(Tags(agent), (Member,))
                self.assertIn(agent, Member[:])

    def test_ordinary_special_method_actions_remain_available(self):
        class Named(Tag):
            @Action
            def __repr__(agent):
                return "named Agent"

        class Host:
            pass

        agent = Host()
        Named(agent)
        self.assertEqual(repr(agent), "named Agent")


if __name__ == "__main__":
    unittest.main()
