"""TOP Tagging and Rip acts are refused while Posts inspect state."""

from contextvars import copy_context
import unittest

from TopKit import At_Exit
from TopKit import Contract
from TopKit import Flag
from TopKit import Pin
from TopKit import Post
from TopKit import Record
from TopKit import Tag
from TopKit import TagCompositionError
from TopKit import TagPostconditionError
from TopKit import lifecycle
from TopKit.declarations import _is_flag
from TopKit.declarations import _is_pin


class Host:
    pass


class ObservationalPostTests(unittest.TestCase):
    def test_caught_top_mutations_fail_post_without_changing_state(self):
        class Existing(Tag):
            label = "original"

            @Post
            def Ready(agent):
                return True

        class Checked(Tag):
            @Post
            def Sound(agent):
                if agent.try_changes:
                    for change in (
                            lambda: Contract.Delete(agent, "Ready"),
                            lambda: setattr(Existing, "label", "changed"),
                            lambda: Flag(Existing),
                            lambda: Pin(Existing),
                            lambda: At_Exit(agent),
                            ):
                        try:
                            change()
                        except TagCompositionError:
                            pass
                return True

        agent = Host()
        agent.try_changes = False
        Existing(agent)
        Checked(agent)
        agent.try_changes = True
        registrations = lifecycle._exit_count

        self.assertFalse(agent.Sound)
        self.assertEqual(Contract.Status(agent), {"Ready": True, "Sound": False})
        self.assertEqual(Existing.label, "original")
        self.assertFalse(_is_flag(Existing))
        self.assertFalse(_is_pin(Existing))
        self.assertEqual(lifecycle._exit_count, registrations)
        self.assertTrue(agent.Ready)
        self.assertIn(agent, Checked[:])

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

    def test_query_action_cannot_hide_a_caught_rip_from_its_post(self):
        class Existing(Tag):
            pass

        class Checked(Tag):
            def Look(agent):
                if agent.try_rip:
                    try:
                        del Existing[agent]
                    except TagCompositionError:
                        pass
                return True

            @Post
            def Ready(agent):
                return agent.Look()

        agent = Host()
        agent.try_rip = False
        Existing(agent)
        Checked(agent)
        agent.try_rip = True

        self.assertFalse(agent.Ready)
        self.assertIn(agent, Existing[:])
        with self.assertRaises(TagPostconditionError.Ready) as caught:
            Contract.Postconditions(agent)
        self.assertIsInstance(caught.exception.__cause__, TagCompositionError)

    def test_pin_post_cannot_tag_another_target_even_if_it_catches_refusal(self):
        other = Host()

        class Changed(Tag):
            pass

        class Agency(Tag):
            try_change = False

        @Pin
        class Certified(Tag):
            @Post
            def Sound(tag):
                if tag.try_change:
                    try:
                        Changed(other)
                    except TagCompositionError:
                        pass
                return True

        Certified(Agency)
        Agency.try_change = True

        self.assertFalse(bool(Agency))
        with self.assertRaises(TagPostconditionError.Sound) as caught:
            Contract.Postconditions(Agency)
        self.assertIsInstance(caught.exception.__cause__, TagCompositionError)
        self.assertIn(Agency, Certified[:])
        self.assertNotIn(Agency, Certified)
        self.assertNotIn(other, Changed[:])

    def test_python_interruption_from_post_remains_primary(self):
        original = KeyboardInterrupt("stop")

        class Interrupted(Tag):
            @Post
            def Ready(agent):
                try:
                    del Interrupted[agent]
                except TagCompositionError:
                    pass
                raise original

        agent = Host()
        with self.assertRaises(KeyboardInterrupt) as caught:
            Interrupted(agent)

        self.assertIs(caught.exception, original)
        self.assertIn(agent, Interrupted[:])

    def test_copied_post_observation_expires_when_check_ends(self):
        copied = []

        class Checked(Tag):
            @Post
            def Ready(agent):
                copied.append(copy_context())
                return True

        class Independent(Tag):
            pass

        Checked(Host())
        other = Host()
        copied[-1].run(Independent, other)
        self.assertIn(other, Independent[:])


if __name__ == "__main__":
    unittest.main()
