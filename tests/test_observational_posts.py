"""TOP Tagging and Rip acts are refused while Posts inspect state."""

import unittest

from TopKit import Contract
from TopKit import Post
from TopKit import Record
from TopKit import Tag
from TopKit import TagCompositionError
from TopKit import TagPostconditionError


class Host:
    pass


class ObservationalPostTests(unittest.TestCase):
    def test_caught_rip_still_fails_each_post_query_without_removing_member(self):
        class Existing(Tag):
            @Post
            def Ready(agent):
                if agent.try_rip:
                    try:
                        del Existing[agent]
                    except TagCompositionError:
                        pass
                return True

        agent = Host()
        agent.try_rip = False
        Existing(agent)
        agent.try_rip = True

        self.assertFalse(bool(agent))
        self.assertFalse(agent.Ready)
        self.assertEqual(Contract.Status(agent), {"Ready": False})
        with self.assertRaises(TagPostconditionError.Ready) as caught:
            Contract.Postconditions(agent)
        self.assertIn("cannot Rip a Tag", str(caught.exception))
        self.assertNotIn(agent, Existing)
        self.assertIn(agent, Existing[:])

    def test_post_cannot_tag_another_target_during_field_inspection(self):
        other = Host()

        class Changed(Tag):
            pass

        class Incomplete(Tag):
            @Post
            def Ready(agent):
                Changed(other)
                return True

        agent = Host()
        with self.assertRaises(TagPostconditionError.Ready) as caught:
            Incomplete(agent)

        self.assertIn("cannot apply a Tag or Pin", str(caught.exception))
        self.assertIn(agent, Incomplete[:])
        self.assertNotIn(other, Changed[:])

    def test_post_can_call_read_only_action_for_calculation(self):
        class Gauge(Tag):
            @Record
            def level(agent):
                return 5

            def Read(agent):
                return agent.level

            @Post
            def Healthy(agent):
                return agent.Read() == 5

        agent = Host()
        Gauge(agent)
        self.assertTrue(agent.Healthy)
        self.assertTrue(bool(agent))
        self.assertEqual(Contract.Status(agent), {"Healthy": True})

    def test_python_interruption_from_post_remains_primary(self):
        original = KeyboardInterrupt("stop")

        class Interrupted(Tag):
            @Post
            def Ready(agent):
                raise original

        agent = Host()
        with self.assertRaises(KeyboardInterrupt) as caught:
            Interrupted(agent)

        self.assertIs(caught.exception, original)
        self.assertIn(agent, Interrupted[:])


if __name__ == "__main__":
    unittest.main()
