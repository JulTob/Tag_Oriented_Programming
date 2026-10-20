"""Conformance tests: publication."""

from __future__ import annotations

import gc
import unittest
import weakref
from TopKit import Action
from TopKit import Delete
from TopKit import Imprint
from TopKit import Operation
from TopKit import Pin
from TopKit import Public
from TopKit import Record
from TopKit import Report
from TopKit import Rip
from TopKit import Secret
from TopKit import Tag
from TopKit import TagDeclarationError
from TopKit import TagResolutionError
from TopKit.tags import MetaTag

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

    def test_tag_views_read_the_current_own_report_value(self) -> None:
        class Base(Tag):
            @Public
            @Report
            def colour(tag):
                return "red"

        class Shape(Base):
            @Record
            def rank(agent):
                return 1

        agent = Agent()
        Shape(agent)
        base_view = Base[agent]
        shape_view = Shape[agent]

        self.assertEqual(base_view.colour, "red")
        self.assertTrue("colour" @ base_view)
        self.assertEqual(shape_view.colour, "red")
        self.assertTrue("colour" @ shape_view)

        Base.colour = "blue"
        self.assertEqual(base_view.colour, "blue")
        self.assertEqual(Base[agent].colour, "blue")
        self.assertEqual(shape_view.colour, "blue")
        self.assertEqual(shape_view.rank, 1)
        self.assertTrue("colour" @ base_view)

    def test_shape_view_reads_its_own_report_over_a_base_layer(self) -> None:
        class Base(Tag):
            @Report
            def colour(tag):
                return "red"

        class Shape(Base):
            @Report
            def colour(tag):
                return "green"

        agent = Agent()
        Shape(agent)
        view = Shape[agent]

        self.assertEqual(Base[agent].colour, "red")
        self.assertEqual(view.colour, "green")
        Shape.colour = "blue"
        self.assertEqual(view.colour, "blue")
        self.assertEqual(Base[agent].colour, "red")

    def test_view_reads_its_recorded_overlay_and_skips_departed_sources(self) -> None:
        class Base(Tag):
            @Report
            def colour(tag):
                return "red"

        class Shape(Base):
            pass

        class Unrelated(Tag):
            pass

        agent = Agent()
        Shape(agent)
        Unrelated(agent)

        self.assertEqual(Shape[agent].colour, "red")
        self.assertEqual(Unrelated[agent].colour, "red")

        del Base[agent]
        with self.assertRaises(AttributeError):
            Shape[agent].colour
        with self.assertRaises(AttributeError):
            Unrelated[agent].colour

    def test_a_later_pin_report_reaches_captured_and_fresh_tag_views(self) -> None:
        class Source(Tag):
            @Record
            def count(agent):
                return 1

        agent = Agent()
        Source(agent)
        captured = Source[agent]
        self.assertFalse("mark" @ captured)

        @Pin
        class Stamp(Tag):
            @Public
            @Record
            def mark(tag):
                return None

        Stamp(Source)
        self.assertIsNone(captured.mark)
        self.assertIsNone(Source[agent].mark)
        self.assertTrue("mark" @ captured)
        self.assertTrue("mark" @ Source[agent])
        self.assertEqual(captured.count, 1)

        Source.mark = False
        self.assertIs(captured.mark, False)
        self.assertTrue("mark" @ captured)

        class Later(Source):
            @Record
            def count(agent):
                return 2

        Later(agent)
        self.assertEqual(agent.count, 2)
        self.assertEqual(captured.count, 1)

        @Operation
        def mark(tag):
            return "operation"

        Source.mark = mark
        with self.assertRaises(AttributeError):
            captured.mark
        self.assertFalse("mark" @ captured)

    def test_a_new_report_declaration_reaches_an_old_tag_view(self) -> None:
        builds: list[type] = []

        class Source(Tag):
            @Public
            @Report
            def mark(tag):
                return "old"

        agent = Agent()
        Source(agent)
        captured = Source[agent]
        del Source.mark
        Source.mark = "plain"
        with self.assertRaises(AttributeError):
            captured.mark
        self.assertFalse("mark" @ captured)

        @Public
        @Report
        def mark(tag):
            builds.append(tag)
            return "new"

        Source.mark = mark
        self.assertTrue("mark" @ captured)
        self.assertEqual(builds, [])
        self.assertEqual(captured.mark, "new")
        self.assertEqual(builds, [Source])

    def test_a_pin_report_replaces_a_deleted_report_in_an_old_view(self) -> None:
        class Source(Tag):
            @Public
            @Report
            def mark(tag):
                return "old"

        agent = Agent()
        Source(agent)
        captured = Source[agent]
        del Source.mark
        self.assertFalse("mark" @ captured)

        @Pin
        class Stamp(Tag):
            @Public
            @Record
            def mark(tag):
                return False

        Stamp(Source)
        self.assertTrue("mark" @ captured)
        self.assertTrue("mark" @ Source[agent])
        self.assertIs(captured.mark, False)
        self.assertIs(Source[agent].mark, False)

    def test_tag_report_is_visible_despite_an_agent_side_delete(self) -> None:
        class Gone(Tag):
            @Delete
            def mark(agent):
                pass

        class Source(Tag):
            pass

        agent = Agent()
        Gone(agent)
        Source(agent)
        captured = Source[agent]

        @Pin
        class Stamp(Tag):
            @Public
            @Record
            def mark(tag):
                return "current"

        Stamp(Source)
        self.assertEqual(captured.mark, "current")
        self.assertTrue("mark" @ captured)

    def test_tag_report_is_visible_despite_a_captured_agent_secret(self) -> None:
        class Early(Tag):
            @Secret
            @Action
            def mark(agent):
                return "secret"

        class Source(Tag):
            pass

        agent = Agent()
        Early(agent)
        Source(agent)
        captured = Source[agent]

        @Pin
        class Stamp(Tag):
            @Public
            @Record
            def mark(tag):
                return "report"

        Stamp(Source)
        self.assertEqual(captured.mark, "report")
        self.assertTrue("mark" @ captured)

    def test_late_secret_pin_record_is_not_exposed_by_tag_view_presence(self) -> None:
        class Source(Tag):
            pass

        agent = Agent()
        Source(agent)
        captured = Source[agent]

        @Pin
        class Hidden(Tag):
            @Secret
            @Record
            def password(tag):
                return "key"

            @Action
            def Read_View(tag, agent):
                view = tag[agent]
                return view.password, "password" @ view

        Hidden(Source)
        with self.assertRaises(AttributeError):
            captured.password
        self.assertFalse("password" @ captured)
        self.assertEqual(Source.Read_View(agent), ("key", True))

    def test_late_unmarked_pin_report_is_visible_only_through_tag_views(self) -> None:
        class Source(Tag):
            pass

        agent = Agent()
        Source(agent)
        captured = Source[agent]

        @Pin
        class Internal(Tag):
            @Record
            def budget(tag):
                return None

        Internal(Source)
        self.assertIsNone(Source.budget)
        self.assertIsNone(captured.budget)
        self.assertIsNone(Source[agent].budget)
        self.assertTrue("budget" @ captured)
        self.assertTrue("budget" @ Source[agent])
        self.assertFalse("budget" @ agent)
        with self.assertRaises(AttributeError):
            agent.budget

    def test_an_operation_replacing_a_report_is_not_read_as_a_report(self) -> None:
        class Source(Tag):
            @Public
            @Report
            def mark(tag):
                return "report"

        agent = Agent()
        Source(agent)
        captured = Source[agent]

        @Operation
        def mark(tag):
            return "operation"

        Source.mark = mark
        self.assertEqual(Source.mark(), "operation")
        with self.assertRaises(AttributeError):
            captured.mark
        self.assertFalse("mark" @ captured)

    def test_callable_values_remain_reports_for_existing_bindings(self) -> None:
        class CallableValue:
            def __call__(self):
                return "called"

        value = CallableValue()

        class Source(Tag):
            @Public
            @Report
            def mark(tag):
                return "initial"

        agent = Agent()
        Source(agent)
        captured = Source[agent]
        Source.mark = value

        self.assertIs(agent.mark, value)
        self.assertIs(captured.mark, value)
        self.assertTrue("mark" @ captured)

        class Pinned(Tag):
            pass

        pinned_value = Action(CallableValue())

        @Pin
        class Stamp(Tag):
            @Public
            @Record
            def mark(tag):
                return pinned_value

        Stamp(Pinned)
        another = Agent()
        Pinned(another)
        self.assertIs(Pinned[another].mark, pinned_value)
        self.assertTrue("mark" @ Pinned[another])

    def test_a_pin_operation_replacing_a_report_is_not_read_as_a_report(self) -> None:
        class Source(Tag):
            @Public
            @Report
            def mark(tag):
                return "report"

        agent = Agent()
        Source(agent)
        captured = Source[agent]

        @Pin
        class Work(Tag):
            @Public
            @Action
            def mark(tag):
                return "operation"

        Work(Source)
        self.assertEqual(Source.mark(), "operation")
        with self.assertRaises(AttributeError):
            captured.mark
        self.assertFalse("mark" @ captured)

    def test_a_ripped_agent_cannot_see_a_report_added_later(self) -> None:
        class Source(Tag):
            pass

        agent = Agent()
        Source(agent)
        captured = Source[agent]
        del Source[agent]

        @Public
        @Report
        def mark(tag):
            return "new"

        Source.mark = mark
        with self.assertRaises(TagResolutionError):
            captured.mark
        with self.assertRaises(TagResolutionError):
            "mark" @ captured

    def test_a_ripped_agent_loses_report_view_until_retagging(self) -> None:
        class Source(Tag):
            @Public
            @Report
            def mark(tag):
                return "old"

        agent = Agent()
        Source(agent)
        captured = Source[agent]
        del Source[agent]
        Source.mark = "current"

        with self.assertRaises(TagResolutionError):
            captured.mark
        with self.assertRaises(TagResolutionError):
            "mark" @ captured

        Source(agent)
        self.assertEqual(captured.mark, "current")
        self.assertTrue("mark" @ captured)

    def test_deleting_a_report_removes_its_declaration_without_rebuilding(self) -> None:
        builds: list[type] = []

        class Signal(Tag):
            @Public
            @Report
            def colour(tag) -> str:
                builds.append(tag)
                return "green"

        agent = Agent()
        Signal(agent)
        self.assertEqual(Signal.colour, "green")
        self.assertEqual(agent.colour, "green")
        self.assertEqual(builds, [Signal])
        view = Signal[agent]

        del Signal.colour

        self.assertNotIn("colour", vars(Signal))
        with self.assertRaises(AttributeError):
            Signal.colour
        with self.assertRaises(AttributeError):
            agent.colour
        with self.assertRaises(AttributeError):
            view.colour
        self.assertFalse("colour" @ view)
        self.assertEqual(builds, [Signal])

        class Later(Tag):
            @Record
            def count(agent):
                return 1

        Later(agent)
        self.assertIn(agent, Later[:])
        self.assertEqual(agent.count, 1)
        with self.assertRaises(AttributeError):
            Later[agent].colour

        later = Agent()
        Signal(later)
        self.assertIn(later, Signal[:])
        with self.assertRaises(AttributeError):
            later.colour
        self.assertEqual(builds, [Signal])

        Signal.colour = "plain"
        with self.assertRaises(AttributeError):
            agent.colour
        with self.assertRaises(AttributeError):
            view.colour
        self.assertFalse("colour" @ agent)
        self.assertFalse("colour" @ view)

        newest = Agent()
        Signal(newest)
        self.assertFalse("colour" @ newest)

        @Public
        @Report
        def colour(tag):
            return "rebuilt"

        Signal.colour = colour
        restored = Agent()
        Signal(restored)
        self.assertEqual(restored.colour, "rebuilt")
        self.assertTrue("colour" @ restored)
        self.assertEqual(Signal.colour, "rebuilt")

    def test_deleting_a_pin_published_report_stops_future_publication(self) -> None:
        class Source(Tag):
            pass

        @Pin
        class Stamp(Tag):
            @Public
            @Record
            def mark(tag):
                return None

        Stamp(Source)
        first = Agent()
        Source(first)
        view = Source[first]
        self.assertIsNone(first.mark)
        self.assertIsNone(view.mark)
        self.assertTrue("mark" @ first)

        del Source.mark
        Source.mark = None   # even the same singleton cannot revive the Report

        with self.assertRaises(AttributeError):
            first.mark
        with self.assertRaises(AttributeError):
            view.mark
        self.assertFalse("mark" @ first)
        self.assertFalse("mark" @ view)

        second = Agent()
        Source(second)
        self.assertFalse("mark" @ second)
        with self.assertRaises(AttributeError):
            second.mark

    def test_equal_but_distinct_tags_keep_separate_report_generations(self) -> None:
        class EqualMeta(MetaTag):
            def __eq__(left, right):
                return isinstance(right, EqualMeta)

            def __hash__(tag):
                return 7

        class First(Tag, metaclass=EqualMeta):
            @Public
            @Report
            def colour(tag):
                return "red"

        class Second(Tag, metaclass=EqualMeta):
            @Public
            @Report
            def colour(tag):
                return "blue"

        self.assertIsNot(First, Second)
        self.assertEqual(First, Second)
        self.assertEqual(hash(First), hash(Second))

        first, second = Agent(), Agent()
        First(first)
        Second(second)
        self.assertEqual(second.colour, "blue")

        del First.colour

        with self.assertRaises(AttributeError):
            first.colour
        self.assertFalse("colour" @ first)
        self.assertEqual(second.colour, "blue")
        self.assertTrue("colour" @ second)

    def test_report_generations_do_not_keep_a_tag_alive(self) -> None:
        def make():
            class Temporary(Tag):
                @Report
                def label(tag):
                    return "short lived"

            agent = Agent()
            Temporary(agent)
            self.assertEqual(Temporary.label, "short lived")
            return weakref.ref(Temporary), weakref.ref(agent)

        tag_ref, agent_ref = make()

        for _ in range(3):
            gc.collect()

        self.assertIsNone(agent_ref())
        self.assertIsNone(tag_ref())

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
