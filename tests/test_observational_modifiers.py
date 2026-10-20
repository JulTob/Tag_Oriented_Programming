"""A check cannot change an existing Contribution through its modifier."""

import unittest

from TopKit import Constant
from TopKit import Post
from TopKit import Pre
from TopKit import Precondition
from TopKit import Public
from TopKit import Report
from TopKit import Secret
from TopKit import Tag
from TopKit import TagCompositionError


class Host:
    pass


class ObservationalModifierTests(unittest.TestCase):
    def test_caught_constant_mark_does_not_change_an_action_during_post(self):
        class Work(Tag):
            def Go(agent):
                return 1

            @Post
            def Ready(agent):
                if agent.try_mark:
                    try:
                        Constant(Work.__dict__["Go"])
                    except TagCompositionError:
                        pass
                return True

        agent = Host()
        agent.try_mark = False
        Work(agent)
        agent.try_mark = True

        self.assertFalse(agent.Ready)
        self.assertIsNone(getattr(Work.__dict__["Go"], "__topkit_constant__", None))
        replacement = lambda agent: 2
        Work.Go = replacement
        self.assertIs(Work.__dict__["Go"], replacement)

    def test_caught_secret_mark_refuses_gate_and_leaves_action_public(self):
        class Work(Tag):
            def Go(agent):
                return 1

        class Gate(Tag):
            @Pre
            def Allowed(agent):
                try:
                    Secret(Work.__dict__["Go"])
                except TagCompositionError:
                    pass
                return True

        agent = Host()
        with self.assertRaises(Precondition.Allowed):
            Gate(agent)

        self.assertIsNone(getattr(Work.__dict__["Go"], "__topkit_secret__", None))
        Work(agent)
        self.assertEqual(agent.Go(), 1)

    def test_caught_public_mark_leaves_existing_report_unpublished(self):
        class Signals(Tag):
            @Report
            def light(tag):
                return "green"

            @Post
            def Ready(agent):
                if agent.try_mark:
                    try:
                        Public(Signals.__dict__["light"])
                    except TagCompositionError:
                        pass
                return True

        agent = Host()
        agent.try_mark = False
        Signals(agent)
        report = Signals.__dict__["light"]
        self.assertFalse(report.public)

        agent.try_mark = True
        self.assertFalse(agent.Ready)
        self.assertFalse(report.public)


if __name__ == "__main__":
    unittest.main()
