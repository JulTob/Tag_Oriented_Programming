"""Conformance tests: publication."""

from __future__ import annotations

import unittest
from TopKit import Action
from TopKit import Imprint
from TopKit import Operation
from TopKit import Public
from TopKit import Record
from TopKit import Report
from TopKit import Rip
from TopKit import Secret
from TopKit import Tag
from TopKit import TagDeclarationError

from ._fixtures import Agent
from ._fixtures import Community
from ._fixtures import Silent_Community


class PublicationTests(unittest.TestCase):
    class Fire(Tag):
        @Public
        @Report
        def colour(tag) -> str:
            return "#ef5b35"

        @Report
        def heat(tag) -> int:
            return 3

        @Public
        @Operation
        def roster(fire, agent) -> tuple:
            return tuple(a for a in fire)

        @Secret
        @Record
        def ember_heat(agent) -> int:
            return 3

        @Secret
        @Action
        def ignite(agent) -> int:
            return agent.ember_heat * 2

        @Action
        def strike(agent) -> int:
            return agent.ignite() + 1

        @Imprint
        def warm_up(agent) -> None:
            agent.warmth = agent.ember_heat

        @Rip
        def cool_down(agent) -> None:
            agent.warmth = agent.ember_heat - 3

    def test_published_report_reads_live_from_the_tag_and_is_read_only(self) -> None:
        ember = Agent()

        self.Fire(ember)

        self.assertEqual(ember.colour, "#ef5b35")
        self.assertFalse(hasattr(ember, "heat"))

        self.Fire.colour = "#ff0000"

        try:
            self.assertEqual(ember.colour, "#ff0000")
        finally:
            self.Fire.colour = "#ef5b35"

        with self.assertRaises(AttributeError):
            ember.colour = "blue"

    def test_published_operation_is_an_action_with_the_agent_as_second_input(self) -> None:
        ember = Agent()

        self.Fire(ember)

        self.assertEqual(ember.roster(), (ember,))
        self.assertEqual(self.Fire.roster(ember), (ember,))

    def test_secret_members_resolve_only_inside_composition(self) -> None:
        ember = Agent()

        self.Fire(ember)

        self.assertEqual(ember.strike(), 7)
        self.assertEqual(ember.warmth, 3)

        with self.assertRaises(AttributeError):
            ember.ignite()

        with self.assertRaises(AttributeError):
            ember.ember_heat

        self.assertFalse(hasattr(ember, "ember_heat"))

        del self.Fire[ember]

        self.assertEqual(ember.warmth, 0)

    def test_captured_secret_handles_fail_closed(self) -> None:
        ember = Agent()
        captured: list = []

        class Leak(self.Fire):
            @Action
            def leak(agent) -> int:
                captured.append(agent.ignite)
                return captured[-1]()

        Leak(ember)
        self.assertEqual(ember.leak(), 6)

        with self.assertRaises(AttributeError):
            captured[0]()

    def test_contradictory_marks_are_rejected_and_redundant_ones_accepted(self) -> None:
        with self.assertRaises(TagDeclarationError):
            class Wrong(Tag):
                @Secret
                @Public
                @Action
                def act(agent) -> None:
                    pass

            Wrong(Agent())

        class Redundant(Tag):
            @Public                     # Records are external already
            @Record
            def hp(agent) -> int:
                return 1

            @Secret                     # Reports are internal already
            @Report
            def lore(tag) -> str:
                return "old"

        ari = Agent()
        Redundant(ari)

        self.assertEqual(ari.hp, 1)
        self.assertEqual(Redundant.lore, "old")
        self.assertFalse(hasattr(ari, "lore"))

    def test_reports_are_builders_that_run_once_per_tag_and_extend_bases(self) -> None:
        calls: list[str] = []

        class Class_(Tag):
            @Report
            def hit_die(tag) -> int:
                calls.append(tag.__name__)
                return 8

            @Report
            def traits(tag, inherited) -> list[str]:
                return (inherited or []) + ["mortal"]

        class Fighter(Class_):
            @Report
            def hit_die(tag) -> int:
                return 10

            @Report
            def traits(tag, inherited) -> list[str]:
                return inherited + ["armoured"]

        self.assertEqual(Class_.hit_die, 8)
        self.assertEqual(Class_.hit_die, 8)
        self.assertEqual(calls, ["Class_"])           # built once
        self.assertEqual(Fighter.hit_die, 10)
        self.assertEqual(Fighter.traits, ["mortal", "armoured"])
        self.assertEqual(Class_.traits, ["mortal"])

        with self.assertRaises(TagDeclarationError):
            Report(8)                                 # a builder, not a value

    def test_reports_operations_and_their_deletion_follow_the_tag_view(self) -> None:
        ari = Agent()

        Community(ari)

        self.assertEqual(ari.Community.colour, "green")
        self.assertEqual(ari.Community.Greet("Ari"), "Community:Ari")

        Silent_Community(ari)

        with self.assertRaises(AttributeError):
            ari.Silent_Community.colour

        with self.assertRaises(AttributeError):
            ari.Silent_Community.Greet
