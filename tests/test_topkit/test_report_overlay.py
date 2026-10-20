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

    def test_deleted_shape_report_reveals_base_without_reordering_later_tag(self) -> None:
        class Base(Tag):
            @Public
            @Report
            def colour(tag):
                return "base"

        class Shape(Base):
            @Public
            @Report
            def colour(tag):
                return "shape"

        class Later(Tag):
            @Public
            @Report
            def colour(tag):
                return "later"

        base_only = self.Host()
        with_later = self.Host()
        Shape(base_only)
        Shape(with_later)
        Later(with_later)
        self.assertEqual((base_only.colour, with_later.colour),
                         ("shape", "later"))

        del Shape.colour

        self.assertEqual(base_only.colour, "base")
        self.assertEqual(with_later.colour, "later")
        self.assertEqual(Base[with_later].colour, "base")

        del Later.colour

        self.assertEqual(with_later.colour, "base")
        self.assertTrue("colour" @ with_later)

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

    def test_a_pin_report_reappears_after_a_later_report_is_deleted(self) -> None:
        class Pinned(Tag):
            pass

        @Pin
        class Publish(Tag):
            @Public
            @Record
            def signal(tag):
                return "pinned"

        Publish(Pinned)

        class Later(Tag):
            @Public
            @Report
            def signal(tag):
                return "later"

        agent = self.Host()
        Pinned(agent)
        Later(agent)
        self.assertEqual(agent.signal, "later")

        del Later.signal

        self.assertEqual(agent.signal, "pinned")
        self.assertEqual(Pinned[agent].signal, "pinned")
        self.assertTrue("signal" @ agent)

    def test_each_report_keeps_its_own_publication_status(self) -> None:
        class Internal(Tag):
            @Report
            def signal(tag):
                return "private"

        class Published(Tag):
            @Public
            @Report
            def signal(tag):
                return "public"

        first = self.Host()
        Published(first)
        Internal(first)
        self.assertEqual(Internal[first].signal, "private")
        with self.assertRaises(AttributeError):
            first.signal
        self.assertFalse("signal" @ first)

        del Internal.signal
        self.assertEqual(first.signal, "public")
        self.assertTrue("signal" @ first)

        class EarlierInternal(Tag):
            @Report
            def signal(tag):
                return "private"

        class LaterPublished(Tag):
            @Public
            @Report
            def signal(tag):
                return "public"

        second = self.Host()
        EarlierInternal(second)
        LaterPublished(second)
        self.assertEqual(second.signal, "public")

        del LaterPublished.signal
        self.assertEqual(EarlierInternal[second].signal, "private")
        with self.assertRaises(AttributeError):
            second.signal
        self.assertFalse("signal" @ second)

    def test_a_fresh_report_declaration_updates_publication_in_place(self) -> None:
        class Signal(Tag):
            @Public
            @Report
            def value(tag):
                return "public"

        agent = self.Host()
        Signal(agent)
        self.assertEqual(agent.value, "public")

        @Report
        def value(tag):
            return "internal"

        Signal.value = value
        self.assertEqual(Signal[agent].value, "internal")
        with self.assertRaises(AttributeError):
            agent.value
        self.assertFalse("value" @ agent)

        @Public
        @Report
        def value(tag):
            return "public again"

        Signal.value = value
        self.assertEqual(agent.value, "public again")
        self.assertTrue("value" @ agent)

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
