"""Whole-contract diagnostics cannot finish the Post they are running in."""

import unittest

from TopKit import Contract, Post, Tag, TagContractError


class Host:
    pass


class ContractDiagnosticRecursionTests(unittest.TestCase):
    def test_status_refuses_its_own_unfinished_post_without_repeating_it(self):
        calls = []

        class Checking(Tag):
            @Post
            def Ready(agent):
                calls.append("Ready")
                return Contract.Status(agent)["Ready"]

        agent = Host()

        with self.assertRaisesRegex(TagContractError, "Ready.*Contract.Status"):
            Checking(agent)

        self.assertEqual(calls, ["Ready"])
        self.assertIn(agent, Checking[:])

        with self.assertRaisesRegex(TagContractError, "Contract.Status"):
            Contract.Status(agent)

        self.assertEqual(calls, ["Ready", "Ready"])

    def test_display_refuses_its_own_unfinished_post_without_repeating_it(self):
        calls = []

        class Checking(Tag):
            @Post
            def Ready(agent):
                calls.append("Ready")
                return bool(Contract.Display(agent))

        agent = Host()

        with self.assertRaisesRegex(TagContractError, "Ready.*Contract.Display"):
            Checking(agent)

        self.assertEqual(calls, ["Ready"])
        self.assertIn(agent, Checking[:])

    def test_other_agent_diagnostics_and_raw_field_queries_still_work(self):
        class Existing(Tag):
            @Post
            def Ready(agent):
                return True

        other = Host()
        Existing(other)

        class Checking(Tag):
            @Post
            def Ready(agent):
                return (
                        agent in Checking[:]
                        and Contract.Status(other)["Ready"]
                        and "Ready" in Contract.Display(other)
                        )

        agent = Host()
        Checking(agent)
        self.assertTrue(agent.Ready)

    def test_indirect_status_cycle_through_another_agent_is_bounded(self):
        calls = []

        class Checking(Tag):
            @Post
            def Ready(agent):
                calls.append(agent)
                return (
                        True if agent.linked is None
                        else Contract.Status(agent.linked)["Ready"]
                        )

        left, right = Host(), Host()
        left.linked = right.linked = None
        Checking(left)
        Checking(right)
        calls.clear()
        left.linked, right.linked = right, left

        with self.assertRaisesRegex(TagContractError, "Contract.Status"):
            Contract.Status(left)

        self.assertEqual(calls, [left, right])

    def test_a_post_may_read_a_different_named_post(self):
        class Checking(Tag):
            @Post
            def Ready(agent):
                return True

            @Post
            def Prepared(agent):
                return agent.Ready

        agent = Host()
        Checking(agent)
        self.assertTrue(agent.Prepared)


if __name__ == "__main__":
    unittest.main()
