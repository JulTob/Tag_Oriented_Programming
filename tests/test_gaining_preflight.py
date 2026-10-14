"""Ordinary Gains still pass the whole Gate before any builder runs."""

import itertools
import unittest
from unittest import mock

import TopKit.transactions as transactions
from TopKit import (Constant, Operation, Pin, Public, Record, Rip, Tag,
                    TagCompositionError, TagResolutionError, Tool, Underlay)
from TopKit.state import _State, _state_of


class Host:
    pass


class GainingPreflightTests(unittest.TestCase):
    def test_a_late_host_property_or_slot_refuses_before_earlier_builders(self):
        class PropertyHost:
            @property
            def occupied(self):
                return "host"

        class SlotHost:
            __slots__ = ("occupied", "__dict__", "__weakref__")

        for host_type in (PropertyHost, SlotHost):
            with self.subTest(host=host_type):
                built = []

                class Arriving(Tag):
                    @Record
                    def earlier(agent):
                        built.append("earlier")
                        return 1

                    @Record
                    def occupied(agent):
                        return "replacement"

                agent = host_type()
                with self.assertRaises(TagCompositionError):
                    Arriving(agent)
                self.assertEqual(built, [])
                self.assertNotIn("earlier", agent.__dict__)
                self.assertNotIn(agent, Arriving)

    def test_a_missing_underlay_refuses_before_earlier_builders(self):
        built = []

        class Arriving(Tag):
            @Record
            def earlier(agent):
                built.append("earlier")
                return 1

            @Underlay
            def Work(agent, underlay):
                return underlay()

        agent = Host()
        with self.assertRaises(TagResolutionError):
            Arriving(agent)
        self.assertEqual(built, [])
        self.assertNotIn("earlier", agent.__dict__)
        self.assertNotIn(agent, Arriving)

    def test_a_valid_underlay_composes_and_is_visible_to_the_next_builder(self):
        class WorkingHost:
            def Work(self):
                return 3

        class Arriving(Tag):
            @Underlay
            def Work(agent, underlay):
                return underlay() + 2

            @Record
            def result(agent):
                return agent.Work()

        agent = WorkingHost()
        Arriving(agent)
        self.assertEqual(agent.result, 5)
        self.assertEqual(agent.Work(), 5)

    def test_independent_kind_conflicts_refuse_before_earlier_builders(self):
        for existing_record in (False, True):
            with self.subTest(existing_record=existing_record):
                built = []

                def previous(agent):
                    return "previous"

                class Existing(Tag):
                    occupied = Record(previous) if existing_record else previous

                def replacement(agent):
                    return "replacement"

                class Arriving(Tag):
                    @Record
                    def earlier(agent):
                        built.append("earlier")
                        return 1

                    occupied = replacement if existing_record else Record(replacement)

                agent = Host()
                Existing(agent)
                with self.assertRaises(TagCompositionError):
                    Arriving(agent)
                self.assertEqual(built, [])
                self.assertNotIn("earlier", agent.__dict__)
                self.assertIn(agent, Existing)
                self.assertNotIn(agent, Arriving)
                value = agent.occupied if existing_record else agent.occupied()
                self.assertEqual(value, "previous")

    def test_late_record_metadata_failure_still_precedes_earlier_builders(self):
        class Builder:
            armed = False

            def __getattribute__(self, name):
                if name == "__func__" and object.__getattribute__(self, "armed"):
                    raise RuntimeError("metadata unavailable")
                return object.__getattribute__(self, name)

            def __call__(self, agent):
                return "value"

        builder = Record(Builder())
        built = []

        class Arriving(Tag):
            @Record
            def earlier(agent):
                built.append("earlier")
                return 1

            later = builder

        warm = Host()
        Arriving(warm)
        built.clear()
        builder.armed = True

        agent = Host()
        with self.assertRaisesRegex(RuntimeError, "metadata unavailable"):
            Arriving(agent)
        self.assertEqual(built, [])
        self.assertNotIn("earlier", agent.__dict__)
        self.assertNotIn(agent, Arriving)

    def test_a_refused_overlay_preserves_the_existing_tool_value_and_rule(self):
        class Sword:
            pass

        class Equipped(Tag):
            @Tool(Sword)
            def weapon(agent, *, weapon):
                return weapon

        built = []

        class Arriving(Equipped):
            @Record
            def weapon(agent):
                built.append("replacement")
                return None

            @Underlay
            def Missing(agent, underlay):
                return underlay()

        agent = Host()
        sword = Sword()
        Equipped(agent, weapon=sword)

        with self.assertRaises(TagResolutionError):
            Arriving(agent)
        self.assertEqual(built, [])
        self.assertIs(agent.weapon, sword)
        self.assertIn(agent, Equipped)
        self.assertNotIn(agent, Arriving)
        with self.assertRaises(TagCompositionError):
            agent.weapon = object()
        self.assertIs(agent.weapon, sword)


class PropertyHost:
    @property
    def occupied(self):
        return "host"


class HasAction(Tag):
    def taken_by_action(agent):
        return "action"


class HasRecord(Tag):
    taken_by_record = Record(lambda agent: "record")


def a_record_over_a_host_property():
    return "occupied", Record(lambda agent: 1), TagCompositionError, "host"


def an_underlay_with_nothing_beneath():
    def Missing(agent, underlay):
        return underlay()
    return "Missing", Underlay(Missing), TagResolutionError, "requires a visible Underlay"


def a_record_over_an_independent_action():
    return ("taken_by_action", Record(lambda agent: 2), TagCompositionError,
            "is a Record but HasAction")


def an_action_over_an_independent_record():
    def taken_by_record(agent):
        return 3
    return ("taken_by_record", taken_by_record, TagCompositionError,
            "is an Action but HasRecord")


WAYS_TO_BE_REFUSED = (
    a_record_over_a_host_property,
    an_underlay_with_nothing_beneath,
    a_record_over_an_independent_action,
    an_action_over_an_independent_record,
)


class GainingPreflightGuardTests(unittest.TestCase):
    """What the shortcut for ordinary Tags must keep, and where it must hand
    the Tag back to the full scratch check."""

    def test_the_first_declared_refusal_is_the_one_reported(self):
        for first, second in itertools.permutations(WAYS_TO_BE_REFUSED, 2):
            with self.subTest(first=first.__name__, second=second.__name__):
                members = {}
                expected = None
                for make in (first, second):
                    name, member, error, text = make()
                    members[name] = member
                    if expected is None:
                        expected = (name, error, text)
                Arriving = type("Arriving", (Tag,), members)

                agent = PropertyHost()
                HasAction(agent)
                HasRecord(agent)
                name, error, text = expected
                with self.assertRaisesRegex(error, text) as caught:
                    Arriving(agent)
                self.assertIn(name, str(caught.exception))
                self.assertNotIn(agent, Arriving)

    def test_a_held_constant_is_refused_before_any_other_clash(self):
        class Earlier(Tag):
            b = Record(lambda agent: 1)

            @Constant
            @Record
            def occupied(agent):
                return 2

        class Arriving(Tag):
            def b(agent):              # an Action over Earlier's Record: a kind clash
                return "action"

            @Record
            def occupied(agent):       # a Record over Earlier's Constant: a locked name
                return 3

        agent = Host()
        Earlier(agent)
        with self.assertRaisesRegex(TagCompositionError, "Earlier.occupied is Constant"):
            Arriving(agent)

    def test_a_refused_public_operation_stops_earlier_builders(self):
        built = []

        class Holder(Tag):
            @Record
            def work(agent):
                return "record"

        class Arriving(Tag):
            @Record
            def earlier(agent):
                built.append("earlier")
                return 1

            @Public
            @Operation
            def work(tag, agent=None):
                return "operation"

        agent = Host()
        Holder(agent)
        with self.assertRaises(TagCompositionError):
            Arriving(agent)
        self.assertEqual(built, [])
        self.assertNotIn("earlier", vars(agent))
        self.assertNotIn(agent, Arriving)

    def test_a_refused_pin_leaves_no_originals_on_the_receiver(self):
        class Receiver(Tag):
            @Operation
            def strike(tag):
                return "declared"

            @Record
            def info(agent):
                return 1

        @Pin
        class Warm(Tag):
            @Record
            def unrelated(tag):
                return 0

        @Pin
        class Bad(Tag):
            def strike(tag, *words):   # patches the Operation first ...
                return "patched"

            @Record
            def info(tag):             # ... then collides with a declaration of the Agent
                return 2

        Warm(Receiver)
        with self.assertRaises(TagCompositionError):
            Bad(Receiver)
        self.assertEqual(dict(_state_of(Receiver).originals), {})
        self.assertEqual(Receiver.strike(), "declared")

    def test_a_refused_pin_hands_nothing_to_an_earlier_pins_teardown(self):
        class Receiver(Tag):
            @Operation
            def strike(tag):
                return "declared"

            @Record
            def info(agent):
                return 1

        seen = []

        @Pin
        class Warm(Tag):
            @Record
            def unrelated(tag):
                return 0

            @Rip
            def Unpatch(tag, original):
                seen.append(sorted(original))

        @Pin
        class Bad(Tag):
            def strike(tag, *words):
                return "patched"

            @Record
            def info(tag):
                return 2

        Warm(Receiver)
        with self.assertRaises(TagCompositionError):
            Bad(Receiver)
        del Warm[Receiver]
        self.assertEqual(seen, [[]])

    def test_an_ordinary_tag_builds_no_scratch_overlay_in_the_gate(self):
        class Ordinary(Tag):
            def act(agent, *words):
                return 1

            @Record
            def rec(agent):
                return 2

        def refuse(*arguments, **keywords):
            raise AssertionError("the Gate built a scratch Overlay for an ordinary Tag")

        agent = Host()
        with mock.patch.object(transactions, "_install", refuse), \
                mock.patch.object(_State, "Copy", refuse):
            Ordinary(agent)
        self.assertEqual(agent.rec, 2)
        self.assertEqual(agent.act(), 1)


if __name__ == "__main__":
    unittest.main()
