"""A deleted Tag Report reveals the next Report in the Agent Overlay."""

from __future__ import annotations

import unittest

from TopKit import Delete
from TopKit import Pin
from TopKit import Public
from TopKit import Record
from TopKit import Report
from TopKit import Tag
from TopKit import TagRogueAccessError


class ReportOverlayTests(unittest.TestCase):
    class Host:
        pass

    def test_deleting_latest_report_reveals_earlier_report_and_its_value(self) -> None:
        class First(Tag):
            @Public
            @Report
            def colour(tag):
                return None

        class Second(Tag):
            @Public
            @Report
            def colour(tag):
                return False

        agent = self.Host()
        First(agent)
        Second(agent)
        first_view, second_view = First[agent], Second[agent]
        self.assertIs(agent.colour, False)
        self.assertTrue("colour" @ agent)

        del Second.colour

        self.assertIsNone(agent.colour)
        self.assertTrue("colour" @ agent)
        self.assertIsNone(first_view.colour)
        with self.assertRaises(AttributeError):
            second_view.colour
        self.assertFalse("colour" @ second_view)

        del First.colour
        with self.assertRaises(AttributeError):
            agent.colour
        self.assertFalse("colour" @ agent)

    def test_pin_published_report_takes_one_overlay_turn(self) -> None:
        class Earlier(Tag):
            @Public
            @Report
            def signal(tag):
                return "earlier"

        class Later(Tag):
            pass

        agent = self.Host()
        Earlier(agent)
        Later(agent)
        captured = Earlier[agent]

        @Pin
        class Publish(Tag):
            @Public
            @Record
            def signal(tag):
                return "later"

        Publish(Later)
        self.assertEqual(agent.signal, "later")
        self.assertEqual(Later[agent].signal, "later")

        del Later.signal

        self.assertEqual(agent.signal, "earlier")
        self.assertTrue("signal" @ agent)
        self.assertEqual(captured.signal, "earlier")
        with self.assertRaises(AttributeError):
            Later[agent].signal

    def test_delete_clears_earlier_report_layers(self) -> None:
        class Earlier(Tag):
            @Public
            @Report
            def signal(tag):
                return "earlier"

        class Clear(Tag):
            @Delete
            def signal(agent):
                pass

        class Later(Tag):
            @Public
            @Report
            def signal(tag):
                return "later"

        agent = self.Host()
        Earlier(agent)
        Clear(agent)
        Later(agent)
        self.assertEqual(agent.signal, "later")

        del Later.signal

        with self.assertRaises(AttributeError):
            agent.signal
        self.assertFalse("signal" @ agent)
        self.assertEqual(Earlier[agent].signal, "earlier")

    def test_ripped_latest_report_blocks_fallback_until_deletion(self) -> None:
        class Earlier(Tag):
            @Public
            @Report
            def signal(tag):
                return "earlier"

        class Later(Tag):
            @Public
            @Report
            def signal(tag):
                return "later"

        agent = self.Host()
        Earlier(agent)
        Later(agent)
        del Later[agent]

        with self.assertRaises(TagRogueAccessError):
            agent.signal
        self.assertFalse("signal" @ agent)

        del Later.signal

        self.assertEqual(agent.signal, "earlier")
        self.assertTrue("signal" @ agent)


if __name__ == "__main__":
    unittest.main()
