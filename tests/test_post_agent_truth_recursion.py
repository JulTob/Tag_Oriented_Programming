"""An unfinished Post cannot certify its own Agent's truth."""

import unittest

from TopKit import Action, Contract, Post, Tag
from TopKit import TagContractError


class Host:
    pass


class PostAgentTruthRecursionTests(unittest.TestCase):
    def test_circular_truth_queries_raise_instead_of_certifying_a_post(self):
        for query in (bool, Contract.Postconditions, Contract.Conditions):
            with self.subTest(query=query):
                class Circular(Tag):
                    @Post
                    def Safe(agent):
                        return query(agent)

                agent = Host()

                with self.assertRaisesRegex(TagContractError, "Safe.*Tag\\[:\\]"):
                    Circular(agent)

                # Post failure does not reverse Field admission.
                self.assertIn(agent, Circular[:])
                with self.assertRaisesRegex(TagContractError, "Tag\\[:\\]"):
                    bool(agent)

    def test_action_truth_guards_cannot_pass_during_an_unfinished_post(self):
        for named_guard in (False, True):
            with self.subTest(named_guard=named_guard):
                class Guarded(Tag):
                    @Action
                    def Launch(agent):
                        if (
                                Contract.Postconditions(agent)
                                if named_guard else agent
                                ):
                            agent.launched += 1

                    @Post
                    def Safety(agent):
                        if agent.probe:
                            agent.Launch()
                        return agent.safe

                agent = Host()
                agent.safe = True
                agent.probe = False
                agent.launched = 0
                Guarded(agent)
                agent.safe = False
                agent.probe = True

                with self.assertRaisesRegex(TagContractError, "Tag\\[:\\]"):
                    bool(agent)
                self.assertEqual(agent.launched, 0)

    def test_raw_field_and_another_agents_truth_remain_available(self):
        class Existing(Tag):
            @Post
            def Ready(agent):
                return agent.ready

        other = Host()
        other.ready = True
        Existing(other)

        class Checking(Tag):
            @Post
            def Safe(agent):
                return (
                        agent in Checking[:]
                        and bool(other)
                        and Contract.Postconditions(other)
                        )

        agent = Host()
        Checking(agent)
        self.assertTrue(bool(agent))


if __name__ == "__main__":
    unittest.main()
