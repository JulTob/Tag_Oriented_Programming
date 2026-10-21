"""Ordinary Gains still pass the whole Gate before any builder runs."""

import itertools
import unittest
import warnings
from unittest import mock

import TopKit.transactions as transactions
from TopKit import (Action, Constant, Delete, Flag, Operation, Pin, Post, Pre,
                    Public, Record, Report, Rip, Secret, Tag,
                    TagCompositionError, Tool, Underlay)
from TopKit.declarations import _invalidate_declarations
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

    def test_a_missing_underlay_allows_earlier_builders_and_calls_null(self):
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
        Arriving(agent)
        self.assertEqual(built, ["earlier"])
        self.assertEqual(agent.earlier, 1)
        self.assertIsNone(agent.Work())
        self.assertIn(agent, Arriving)

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

        class GuardedHost(Host):
            @property
            def blocked(self):
                return "host value"

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

            @Record
            def blocked(agent):
                return "replacement"

        agent = GuardedHost()
        sword = Sword()
        Equipped(agent, weapon=sword)

        with self.assertRaises(TagCompositionError):
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

    def test_a_collision_is_reported_before_a_failing_metadata_read(self):
        class PropertyHost:
            @property
            def occupied(self):
                return "host"

        class Builder:
            armed = False

            def __getattribute__(self, name):
                if name == "__func__" and object.__getattribute__(self, "armed"):
                    raise RuntimeError("metadata unavailable")
                return object.__getattribute__(self, name)

            def __call__(self, agent):
                return "value"

        builder = Record(Builder())

        class Arriving(Tag):
            occupied = builder

        Arriving(Host())              # warm the declaration cache
        builder.armed = True
        with self.assertRaises(TagCompositionError):
            Arriving(PropertyHost())

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


def copies_made_by_the_gate(tag, agent):
    """How many times the Gate copied the State while ``tag`` was applied."""

    made = []
    gated = []
    real_copy = _State.Copy
    real_gate = transactions._gate

    def counting_copy(state):
        made.append(1)
        return real_copy(state)

    def counting_gate(*arguments):
        before = len(made)
        try:
            return real_gate(*arguments)
        finally:
            gated.append(len(made) - before)

    with mock.patch.object(_State, "Copy", counting_copy), \
            mock.patch.object(transactions, "_gate", counting_gate):
        tag(agent)
    return gated[0]


class GainingPreflightFallbackTests(unittest.TestCase):
    """The Tags and Agents the shortcut must hand back to the scratch pass."""

    def test_a_tag_needing_runtime_protection_keeps_the_scratch_copy(self):
        class WithSecret(Tag):
            @Secret
            @Record
            def hidden(agent):
                return 0

        class WithDelete(Tag):
            @Delete
            def gone(agent): ...

        class WithPre(Tag):
            @Pre
            def Ready(agent):
                return True

        class WithPost(Tag):
            @Post
            def Fine(agent):
                return True

        class WithConstant(Tag):
            @Constant
            @Record
            def fixed(agent):
                return 0

        class WithPublicReport(Tag):
            @Public
            @Report
            def shared(tag):
                return 1

        class WithPublicOperation(Tag):
            @Public
            @Operation
            def op(agent):
                return 1

        class WithSpecialMethod(Tag):
            def __len__(agent):
                return 1

        @Flag
        class Flagged(Tag):
            pass

        self.assertEqual(copies_made_by_the_gate(WithPre, Host()), 0)

        for tag in (WithSecret, WithDelete, WithPost, WithConstant,
                    WithPublicReport, WithPublicOperation, WithSpecialMethod,
                    Flagged):
            with self.subTest(tag=tag.__name__):
                self.assertGreaterEqual(copies_made_by_the_gate(tag, Host()), 1)

    def test_a_pin_keeps_the_scratch_copy(self):
        class Target(Tag):
            pass

        @Pin
        class Patch(Tag):
            @Record
            def extra(agent):
                return 2

        self.assertGreaterEqual(copies_made_by_the_gate(Patch, Target), 1)

    def test_an_agent_holding_a_constant_keeps_the_scratch_copy(self):
        class Locks(Tag):
            @Constant
            @Record
            def fixed(agent):
                return 0

        class Ordinary(Tag):
            @Record
            def a(agent):
                return 1

        agent = Host()
        Locks(agent)
        self.assertGreaterEqual(copies_made_by_the_gate(Ordinary, agent), 1)


class GainingSharedMembersTests(unittest.TestCase):
    """Reports and Operations next to ordinary Gains."""

    def refused_with(self, extra):
        built = []

        def earlier(agent):
            built.append("earlier")
            return 1

        def occupied(agent):
            return "replacement"

        members = {"earlier": Record(earlier), "occupied": Record(occupied)}
        members.update(extra)
        Arriving = type("Arriving", (Tag,), members)

        class PropertyHost:
            @property
            def occupied(self):
                return "host"

        agent = PropertyHost()
        with self.assertRaises(TagCompositionError):
            Arriving(agent)
        self.assertEqual(built, [])
        self.assertNotIn("earlier", agent.__dict__)
        self.assertNotIn(agent, Arriving)

    def test_an_internal_report_does_not_change_the_gate(self):
        self.refused_with({"note": Report(lambda tag: 1)})

    def test_an_internal_operation_does_not_change_the_gate(self):
        self.refused_with({"helper": Operation(lambda tag: 1)})

    def test_a_public_report_does_not_change_the_gate(self):
        self.refused_with({"note": Public(Report(lambda tag: 1))})

    def test_a_tag_with_an_internal_report_or_operation_takes_the_shortcut(self):
        class WithReport(Tag):
            @Record
            def rec(agent):
                return 1

            @Report
            def note(tag):
                return 1

        class WithOperation(Tag):
            @Record
            def rec(agent):
                return 1

            @Operation
            def helper(tag):
                return 1

        for tag in (WithReport, WithOperation):
            with self.subTest(tag=tag.__name__):
                self.assertEqual(copies_made_by_the_gate(tag, Host()), 0)


class GainingReplacementTests(unittest.TestCase):
    """What installing an Action or a Record over another one leaves behind."""

    def test_an_action_over_a_related_record_replaces_it(self):
        class Base(Tag):
            @Record
            def x(agent):
                return 1

        class Shape(Base):
            @Action
            def x(agent):
                return "action"

        class Other(Tag):
            @Action
            def x(agent):
                return "other"

        agent = Host()
        Shape(agent)
        self.assertEqual(_state_of(agent).records, {})
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            Other(agent)
        self.assertEqual(agent.x(), "other")

    def test_a_record_over_a_related_action_clears_the_action_origin(self):
        class Base(Tag):
            @Action
            def x(agent):
                return 1

        class Shape(Base):
            @Record
            def x(agent):
                return "record"

        class Other(Tag):
            @Record
            def x(agent):
                return "other"

        agent = Host()
        Shape(agent)
        self.assertEqual(_state_of(agent).action_origins, {})
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            Other(agent)
        self.assertEqual(agent.x, "other")

    def test_an_action_over_a_tool_slot_ends_the_slots_rule(self):
        class Sword:
            pass

        class Equipped(Tag):
            @Tool(Sword)
            def weapon(agent, *, weapon):
                return weapon

        class Replacing(Equipped):
            @Action
            def weapon(agent):
                return "action"

        agent = Host()
        Equipped(agent, weapon=Sword())
        Replacing(agent)
        self.assertEqual(_state_of(agent).tools, {})
        agent.weapon = object()

    def test_a_scratch_pass_stays_quiet_and_the_real_pass_warns_once(self):
        class A(Tag):
            @Action
            def act(agent):
                return 1

            @Record
            def rec(agent):
                return 1

        class B(Tag):
            @Secret          # forces the scratch pass
            @Record
            def hidden(agent):
                return 0

            @Action
            def act(agent):
                return 2

            @Record
            def rec(agent):
                return 2

        agent = Host()
        A(agent)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            B(agent)
        self.assertEqual(
            sorted(str(warning.message) for warning in caught),
            ["B.act replaces the Action of independent Tag A",
             "B.rec replaces the Record of independent Tag A"],
        )

    def test_a_replaced_postcondition_warns_once(self):
        class A(Tag):
            @Post
            def Fine(agent):
                return True

        class B(Tag):
            @Post
            def Fine(agent):
                return True

        agent = Host()
        A(agent)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            B(agent)
        self.assertEqual(len(caught), 1, [str(warning.message) for warning in caught])

    def test_a_name_deleted_and_stored_again_is_visible_through_the_view(self):
        class MuteAction(Tag):
            @Delete
            def w(agent): ...

        class TalkerAction(MuteAction):
            @Action
            def w(agent):
                return 5

        class MuteRecord(Tag):
            @Delete
            def v(agent): ...

        class TalkerRecord(MuteRecord):
            @Record
            def v(agent):
                return 7

        action_agent, record_agent = Host(), Host()
        TalkerAction(action_agent)
        TalkerRecord(record_agent)
        self.assertEqual(TalkerAction[action_agent].w(), 5)
        self.assertEqual(TalkerRecord[record_agent].v, 7)
        self.assertEqual(_state_of(action_agent).deleted, set())
        self.assertEqual(_state_of(record_agent).deleted, set())


class GainingDeclarationsAfterGateTests(unittest.TestCase):
    def test_a_declaration_added_while_the_gate_checks_is_still_gained(self):
        armed = {"yes": False}

        class Builder:
            def __getattribute__(self, name):
                if name == "__func__" and armed["yes"]:
                    armed["yes"] = False
                    Arriving.late = Record(lambda agent: "late value")
                    _invalidate_declarations(Arriving)
                return object.__getattribute__(self, name)

            def __call__(self, agent):
                return "value"

        class Arriving(Tag):
            hooked = Record(Builder())

        Arriving(Host())          # warm the declaration cache
        armed["yes"] = True
        agent = Host()
        Arriving(agent)
        self.assertEqual(agent.late, "late value")


if __name__ == "__main__":
    unittest.main()
