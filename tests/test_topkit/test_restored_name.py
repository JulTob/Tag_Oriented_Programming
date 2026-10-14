"""Conformance tests: restored name."""

from __future__ import annotations

import unittest
from TopKit import Delete
from TopKit import Flag
from TopKit import Post
from TopKit import Tag


class RestoredNameTests(unittest.TestCase):
    """A name a Tag deleted and a later Layer stored again keeps its gate
    on the runtime type, so a type rebuilt for any later reason (a Flag,
    a Postcondition, another deletion) never lets the host's own member
    back over the Layer's."""

    class Host:
        @property
        def speak(self) -> str:
            return "host property"

    def setUp(self) -> None:
        class Mute(Tag):
            @Delete
            def speak(agent): ...

        class Talker(Mute):
            def speak(agent) -> str:
                return "Talker action"

        self.Talker = Talker

    def test_a_later_tag_that_rebuilds_the_type_keeps_the_layer(self) -> None:
        @Flag("Wolf")
        class Werewolf(Tag):
            pass

        class Promised(Tag):
            @Post
            def Fine(agent) -> bool:
                return True

        class Gone(Tag):
            @Delete
            def unrelated(agent): ...

        for later in (Werewolf, Promised, Gone):
            host = self.Host()
            self.Talker(host)
            self.assertEqual(host.speak(), "Talker action")

            later(host)

            self.assertEqual(host.speak(), "Talker action", later.__name__)

    def test_the_order_of_a_flag_does_not_change_the_layer(self) -> None:
        @Flag
        class Werewolf(Tag):
            pass

        first, second = self.Host(), self.Host()
        self.Talker(first)
        Werewolf(first)
        Werewolf(second)
        self.Talker(second)

        self.assertEqual(first.speak(), "Talker action")
        self.assertEqual(second.speak(), "Talker action")
        self.assertIs(type(first), type(second))
