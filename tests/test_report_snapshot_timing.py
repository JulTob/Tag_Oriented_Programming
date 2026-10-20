"""Saving a Tag view does not read the Tag's optional Reports."""

import unittest

from TopKit import Public, Report, Tag


class ReportSnapshotTimingTests(unittest.TestCase):
    def test_builder_runs_on_first_read_after_unrelated_tagging(self):
        calls = []

        class Prepared(Tag):
            @Public
            @Report
            def signal(tag):
                calls.append(tag)
                return "ready"

        class Later(Tag):
            pass

        agent = type("Host", (), {})()
        Prepared(agent)
        Later(agent)

        self.assertEqual(calls, [])
        self.assertTrue("signal" @ Prepared[agent])
        self.assertEqual(calls, [])
        self.assertEqual((Prepared[agent].signal, agent.signal),
                         ("ready", "ready"))
        self.assertEqual(calls, [Prepared])

    def test_failing_optional_report_does_not_interrupt_independent_tagging(self):
        calls = []

        class Unstable(Tag):
            @Report
            def signal(tag):
                calls.append(tag)
                raise ValueError("not ready")

        class Later(Tag):
            pass

        agent = type("Host", (), {})()
        Unstable(agent)
        Later(agent)

        self.assertEqual(calls, [])
        self.assertIn(agent, Unstable[:])
        self.assertIn(agent, Later[:])

        with self.assertRaisesRegex(ValueError, "not ready"):
            _ = Unstable[agent].signal

        self.assertEqual(calls, [Unstable])


if __name__ == "__main__":
    unittest.main()
