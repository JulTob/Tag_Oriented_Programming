"""Contract queries save one condition turn despite changes made by Posts."""

import unittest
import warnings

from TopKit import Contract, Post, Pre, Rip, Tag


class Host:
    pass


class ConditionTurnTests(unittest.TestCase):
    def test_a_post_can_rip_itself_and_end_its_own_promise(self):
        class Leaving(Tag):
            @Post
            def Ready(agent):
                if agent.leave:
                    del Leaving[agent]
                return True

            @Rip
            def Release(agent):
                Contract.Delete(agent, "Ready")

        for query, expected in (
                (bool, True),
                (Contract.Postconditions, True),
                (Contract.Status, {"Ready": True}),
                ):
            with self.subTest(query=query):
                agent = Host()
                agent.leave = False
                Leaving(agent)
                agent.leave = True

                self.assertEqual(query(agent), expected)
                self.assertNotIn(agent, Leaving[:])
                self.assertEqual(Contract.Status(agent), {})

        # The last Post check during Tagging uses the same saved-turn rule.
        agent = Host()
        agent.leave = True
        self.assertIs(Leaving(agent), agent)
        self.assertNotIn(agent, Leaving[:])
        self.assertEqual(Contract.Status(agent), {})

        # A sound Field walk asks the same contract question before yielding.
        agent = Host()
        agent.leave = False
        Leaving(agent)
        agent.leave = True
        self.assertEqual(list(Leaving), [])
        self.assertNotIn(agent, Leaving[:])

    def test_a_failing_post_cannot_erase_its_current_verdict(self):
        class Leaving(Tag):
            @Post
            def Ready(agent):
                if agent.leave:
                    del Leaving[agent]
                    return False
                return True

            @Rip
            def Release(agent):
                Contract.Delete(agent, "Ready")

        for query, expected in (
                (bool, False),
                (Contract.Status, {"Ready": False}),
                ):
            with self.subTest(query=query):
                agent = Host()
                agent.leave = False
                Leaving(agent)
                agent.leave = True

                self.assertEqual(query(agent), expected)
                self.assertEqual(Contract.Status(agent), {})

    def test_a_deleted_later_promise_is_not_run_from_the_saved_turn(self):
        events = []

        class Leaving(Tag):
            @Post
            def First(agent):
                events.append("first")
                if agent.end_later:
                    agent.end_later = False
                    Contract.Delete(agent, "Later")
                return True

            @Post
            def Later(agent):
                events.append("later")
                return False if agent.end_later else True

        for query, expected in (
                (bool, True),
                (Contract.Postconditions, True),
                (Contract.Status, {"First": True}),
                ):
            with self.subTest(query=query):
                agent = Host()
                agent.end_later = False
                Leaving(agent)
                events.clear()
                agent.end_later = True

                self.assertEqual(query(agent), expected)
                self.assertEqual(events, ["first"])
                self.assertEqual(Contract.Status(agent), {"First": True})

    def test_replacement_skips_the_old_check_until_the_next_query(self):
        events = []

        class Replacement(Tag):
            @Post
            def Later(agent):
                events.append("replacement")
                return True

        class Original(Tag):
            @Post
            def First(agent):
                events.append("first")
                if agent.replace:
                    agent.replace = False
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        Replacement(agent)
                return True

            @Post
            def Later(agent):
                events.append("old")
                return True

        agent = Host()
        agent.replace = False
        Original(agent)
        events.clear()
        agent.replace = True

        self.assertEqual(Contract.Status(agent), {"First": True})
        # The nested Tagging checked the new promise once; the outer
        # saved turn neither replays it nor invokes the replaced check.
        self.assertEqual(events, ["first", "first", "replacement"])

        events.clear()
        self.assertEqual(Contract.Status(agent), {"First": True, "Later": True})
        self.assertEqual(events, ["first", "replacement"])

    def test_combined_queries_save_both_scopes_before_running_a_pre(self):
        events = []

        class Added(Tag):
            @Post
            def Later(agent):
                events.append("later")
                return True

        class Existing(Tag):
            @Pre
            def Prepare(agent):
                if agent.add_later:
                    agent.add_later = False
                    Added(agent)
                return True

            @Post
            def Ready(agent):
                return True

        for query in (Contract.Status, Contract.Display, Contract.Conditions):
            with self.subTest(query=query):
                agent = Host()
                agent.add_later = False
                Existing(agent)
                agent.add_later = True
                events.clear()

                answer = query(agent)
                if query is Contract.Status:
                    self.assertEqual(answer, {"Prepare": True, "Ready": True})
                elif query is Contract.Display:
                    self.assertNotIn("Later", answer)
                else:
                    self.assertIs(answer, True)
                self.assertEqual(events, ["later"])
                self.assertIn("Later", Contract.Status(agent))

    def test_a_raising_check_still_closes_the_recursion_guard(self):
        class Leaving(Tag):
            @Post
            def First(agent):
                if agent.fail_once:
                    agent.fail_once = False
                    Contract.Delete(agent, "Later")
                    raise ValueError("failed after ending Later")
                return True

            @Post
            def Later(agent):
                return True

        agent = Host()
        agent.fail_once = False
        Leaving(agent)
        agent.fail_once = True

        self.assertEqual(Contract.Status(agent), {"First": False})
        self.assertEqual(Contract.Status(agent), {"First": True})
        self.assertTrue(bool(agent))


if __name__ == "__main__":
    unittest.main()
