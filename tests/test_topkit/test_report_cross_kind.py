"""An old Report gate must release a later Action or Record Overlay."""

from __future__ import annotations

import unittest

from TopKit import Action
from TopKit import Pin
from TopKit import Public
from TopKit import Record
from TopKit import Report
from TopKit import Secret
from TopKit import Tag


class ReportCrossKindTests(unittest.TestCase):
    class Host:
        pass

    def test_record_is_read_written_and_deleted_after_later_report_deletion(self) -> None:
        class Earlier(Tag):
            @Public
            @Report
            def answer(tag):
                return "old report"

        class Stored(Tag):
            @Record
            def answer(agent):
                return "record"

        class Later(Tag):
            @Public
            @Report
            def answer(tag):
                return "new report"

        agent = self.Host()
        Earlier(agent)
        Stored(agent)
        Later(agent)
        self.assertEqual(agent.answer, "new report")

        del Later.answer

        self.assertEqual(agent.answer, "record")
        self.assertTrue("answer" @ agent)
        agent.answer = False
        self.assertIs(agent.answer, False)
        self.assertTrue("answer" @ agent)
        del agent.answer
        with self.assertRaises(AttributeError):
            agent.answer
        self.assertFalse("answer" @ agent)
        agent.answer = None
        self.assertIsNone(agent.answer)
        self.assertTrue("answer" @ agent)

    def test_action_is_called_replaced_and_deleted_after_report_deletion(self) -> None:
        class Earlier(Tag):
            @Public
            @Report
            def answer(tag):
                return "old report"

        class Doing(Tag):
            @Action
            def answer(agent):
                return "action"

        class Later(Tag):
            @Public
            @Report
            def answer(tag):
                return "new report"

        agent = self.Host()
        Earlier(agent)
        Doing(agent)
        Later(agent)

        del Later.answer

        self.assertEqual(agent.answer(), "action")
        self.assertTrue("answer" @ agent)
        agent.answer = lambda: "new action"
        self.assertEqual(agent.answer(), "new action")
        del agent.answer
        with self.assertRaises(AttributeError):
            agent.answer
        self.assertFalse("answer" @ agent)

    def test_pin_published_action_returns_after_report_deletion(self) -> None:
        class Source(Tag):
            pass

        @Pin
        class Publish(Tag):
            @Public
            @Action
            def answer(tag, agent):
                return "pin action"

        Publish(Source)

        class Later(Tag):
            @Public
            @Report
            def answer(tag):
                return "report"

        agent = self.Host()
        Source(agent)
        Later(agent)
        self.assertEqual(agent.answer, "report")

        del Later.answer

        self.assertEqual(agent.answer(), "pin action")
        self.assertTrue("answer" @ agent)

    def test_secret_record_is_not_exposed_by_an_old_report_gate(self) -> None:
        class Earlier(Tag):
            @Public
            @Report
            def answer(tag):
                return "old report"

        class Hidden(Tag):
            @Secret
            @Record
            def answer(agent):
                return "secret"

        class Later(Tag):
            @Public
            @Report
            def answer(tag):
                return "new report"

        agent = self.Host()
        Earlier(agent)
        Hidden(agent)
        Later(agent)

        self.assertEqual(agent.answer, "new report")
        self.assertTrue("answer" @ agent)

        del Later.answer

        with self.assertRaises(AttributeError):
            agent.answer
        self.assertFalse("answer" @ agent)
        with self.assertRaises(AttributeError):
            agent.answer = "leaked"


if __name__ == "__main__":
    unittest.main()
