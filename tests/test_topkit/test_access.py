"""Conformance tests: access."""

from __future__ import annotations

import unittest
from TopKit import Form
from TopKit import Report
from TopKit import Tag
from TopKit import TagResolutionError

from ._fixtures import Agent
from ._fixtures import Elf
from ._fixtures import Paladin
from ._fixtures import Person
from ._fixtures import Squire


class AccessTests(unittest.TestCase):
    def test_views_by_name_and_by_class(self) -> None:
        ari = Agent()

        Elf(ari)
        Paladin(ari)

        self.assertEqual(ari.Elf.Attack(), "With elven grace Attack!")
        self.assertEqual(Elf[ari].Attack(), "With elven grace Attack!")

        with self.assertRaises(AttributeError):
            ari.Elf.Attack = None

    def test_view_by_class_distinguishes_tags_that_share_a_name(self) -> None:
        def make(colour: str) -> type:
            class Fire(Tag):
                @Report
                def hue(tag) -> str:
                    return colour

            return Fire

        Fire_A = make("red")
        Fire_B = make("blue")
        ari = Agent()

        Fire_A(ari)
        Fire_B(ari)

        self.assertEqual(Fire_A[ari].hue, "red")
        self.assertEqual(Fire_B[ari].hue, "blue")
        self.assertEqual(ari.Fire.hue, "blue")

    def test_views_end_with_membership(self) -> None:
        ari = Agent()

        Squire(ari)
        del Squire[ari]

        with self.assertRaises(AttributeError):
            ari.Squire

        with self.assertRaises(TagResolutionError):
            Squire[ari]

        Person(ari)

        with self.assertRaises(TagResolutionError):
            Paladin[ari]

    def test_positional_slices_are_rejected(self) -> None:
        with self.assertRaises(TypeError):
            Squire[0:1]

    def test_tag_dotted_namespace_belongs_to_the_program(self) -> None:
        # Nothing TOP-level lives at Tag.name: a program may declare a
        # Report called Field, Form, or Rip without collision.
        class Freehold(Tag):
            @Report
            def Field(tag) -> str:
                return "a farm"

            @Report
            def Form(tag) -> str:
                return "a hut"

            @Report
            def Rip(tag) -> str:
                return "a tear"

        self.assertEqual(Freehold.Field, "a farm")
        self.assertEqual(Freehold.Form, "a hut")
        self.assertEqual(Freehold.Rip, "a tear")
        self.assertEqual(Form(Freehold), (Freehold,))
