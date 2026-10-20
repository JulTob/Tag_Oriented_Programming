"""A Post Underlay starts from the neutral True when no lower Post exists."""

import unittest

from TopKit import Contract, Pin, Post, Pre, Tag, TagResolutionError, Underlay


class Host:
    pass


class PostNeutralUnderlayTests(unittest.TestCase):
    def test_first_post_underlay_receives_callable_true(self):
        seen = []

        class First(Tag):
            @Post
            @Underlay
            def Ready(agent, prior):
                seen.append(prior())
                return prior() and agent.ready

        agent = Host()
        agent.ready = True
        First(agent)
        self.assertEqual(seen, [True])
        self.assertTrue(agent.Ready)

        agent.ready = False
        self.assertFalse(agent.Ready)
        self.assertEqual(Contract.Status(agent), {"Ready": False})

    def test_existing_lower_post_still_runs(self):
        seen = []

        class Lower(Tag):
            @Post
            def Ready(agent):
                seen.append("lower")
                return agent.ready

        class Upper(Tag):
            @Post
            @Underlay
            def Ready(agent, prior):
                seen.append("upper")
                return prior()

        agent = Host()
        agent.ready = True
        Lower(agent)
        Upper(agent)
        seen.clear()
        agent.ready = False
        self.assertFalse(agent.Ready)
        self.assertEqual(seen, ["upper", "lower"])

    def test_first_pin_post_underlay_receives_callable_true(self):
        @Pin
        class Ready_Pin(Tag):
            @Post
            @Underlay
            def Ready(tag, prior):
                return prior()

        class Target(Tag):
            pass

        Ready_Pin(Target)
        self.assertTrue(Target.Ready)

    def test_pre_underlay_without_prior_still_refuses(self):
        class First(Tag):
            @Pre
            @Underlay
            def Ready(agent, prior):
                return prior()

        agent = Host()
        with self.assertRaises(TagResolutionError):
            First(agent)
        self.assertNotIn(agent, First[:])


if __name__ == "__main__":
    unittest.main()
