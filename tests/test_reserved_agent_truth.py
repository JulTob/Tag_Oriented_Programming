"""Agent truth belongs to visible Posts, while other values keep Python truth."""

import unittest

from TopKit import (Action, Delete, Imprint, Operation, Pin, Post, Pre,
                    Public, Record, Report, Tag, TagCompositionError,
                    TagDeclarationError, Tags)


class Host:
    pass


def _member_for(kind):
    """Create fresh marks: declaration names, rather than function names, bind."""
    def calculate(receiver, *arguments):
        raise AssertionError("validation must not execute a Contribution")

    if kind == "bare Action":
        return calculate
    if kind == "Action":
        return Action(calculate)
    if kind == "Record":
        return Record(calculate)
    if kind == "Delete":
        return Delete(calculate)
    if kind == "Public Report":
        return Public(Report(calculate))
    if kind == "Report Public":
        return Report(Public(calculate))
    if kind == "Public Operation":
        return Public(Operation(calculate))
    if kind == "Operation Public":
        return Operation(Public(calculate))
    raise AssertionError(kind)


AGENT_TRUTH_MEMBERS = (
        "bare Action", "Action", "Record", "Delete", "Public Report",
        "Report Public", "Public Operation", "Operation Public",
        )


class ReservedAgentTruthTests(unittest.TestCase):
    def test_truth_reads_posts_without_using_host_length(self):
        class EmptyShelf:
            def __len__(agent):
                return 0

        class Member(Tag):
            pass

        class Checked(Tag):
            @Post
            def Ready(agent):
                return agent.ready

        agent = EmptyShelf()
        agent.ready = True
        Member(agent)
        self.assertEqual(len(agent), 0)
        self.assertTrue(agent)

        Checked(agent)
        agent.ready = False
        self.assertFalse(agent)
        agent.ready = True
        self.assertTrue(agent)

    def test_precondition_truth_does_not_become_a_post_requirement(self):
        class Admitted(Tag):
            @Pre
            def Ready(agent):
                return agent.ready

        agent = Host()
        agent.ready = True
        Admitted(agent)
        agent.ready = False

        self.assertFalse(hasattr(agent, "Ready"))
        self.assertTrue(agent)

    def test_explicit_host_truth_is_refused_before_any_tagging_effect(self):
        for inherited in (False, True):
            for truth in (None, False, True):
                with self.subTest(inherited=inherited, truth=truth):
                    events = []

                    def host_truth(agent):
                        events.append("host truth")
                        return truth

                    # Explicit None occupies the protocol seat too; it is not
                    # the absence of a host protocol.
                    binding = None if truth is None else host_truth
                    base = type("TruthHost", (), {"__bool__": binding})
                    host_type = type("InheritedTruthHost", (base,), {}) if inherited else base

                    class Prepared(Tag):
                        @Pre
                        def Accepted(agent):
                            events.append("Gate")
                            return True

                        @Record
                        def value(agent):
                            events.append("Record")
                            return "gain"

                        @Imprint
                        def Train(agent):
                            events.append("Imprint")

                    agent = host_type()
                    agent.existing = "unchanged"
                    before = dict(vars(agent))
                    with self.assertRaises(TagCompositionError):
                        Prepared(agent)

                    self.assertEqual(events, [])
                    self.assertIs(type(agent), host_type)
                    self.assertEqual(vars(agent), before)
                    self.assertEqual(Tags(agent), ())
                    self.assertNotIn(agent, Prepared[:])
                    if truth is not None:
                        self.assertIs(bool(agent), truth)
                        self.assertEqual(events, ["host truth"])

    def test_synthetic_truth_in_an_inherited_runtime_type_is_supported(self):
        class Member(Tag):
            pass

        class Checked(Tag):
            @Post
            def Ready(agent):
                return agent.ready

        first = Host()
        Member(first)

        class Derived(type(first)):
            pass

        agent = Derived()
        agent.ready = True
        self.assertIs(Checked(agent), agent)
        self.assertTrue(agent)
        agent.ready = False
        self.assertFalse(agent)

    def test_host_truth_descriptor_is_not_evaluated_during_refusal(self):
        events = []

        class TruthDescriptor:
            def __get__(descriptor, instance, owner):
                events.append("truth descriptor")
                raise AssertionError("host truth was evaluated")

        class TruthHost:
            __bool__ = TruthDescriptor()

        class Member(Tag):
            pass

        agent = TruthHost()
        with self.assertRaises(TagCompositionError):
            Member(agent)
        self.assertEqual(events, [])
        self.assertIs(type(agent), TruthHost)
        self.assertEqual(vars(agent), {})
        self.assertNotIn(agent, Member[:])

    def test_metaclass_getattribute_cannot_hide_explicit_host_truth(self):
        for masked_name in ("__mro__", "__dict__", "__name__"):
            with self.subTest(masked_name=masked_name):
                events = []

                class MaskingMeta(type):
                    def __getattribute__(host, name, masked_name=masked_name):
                        if name == masked_name:
                            events.append("metaclass lookup")
                            if name == "__mro__":
                                return (object,)
                            if name == "__name__":
                                return "HiddenHost"
                            namespace = dict(type.__dict__["__dict__"].__get__(host, type(host)))
                            namespace.pop("__bool__", None)
                            return namespace
                        return type.__getattribute__(host, name)

                class TruthHost(metaclass=MaskingMeta):
                    def __bool__(agent):
                        events.append("host truth")
                        return False

                class Prepared(Tag):
                    @Pre
                    def Accepted(agent):
                        events.append("Gate")
                        return True

                    @Record
                    def value(agent):
                        events.append("Record")
                        return 1

                    @Imprint
                    def Train(agent):
                        events.append("Imprint")

                agent = TruthHost()
                agent.existing = "unchanged"
                before = dict(vars(agent))
                with self.assertRaises(TagCompositionError) as caught:
                    Prepared(agent)
                self.assertIn("TruthHost", str(caught.exception))
                self.assertIn("__bool__", str(caught.exception))
                self.assertEqual(events, [])
                self.assertIs(type(agent), TruthHost)
                self.assertEqual(vars(agent), before)
                self.assertEqual(Tags(agent), ())
                self.assertNotIn(agent, Prepared[:])

    def test_metaclass_data_descriptors_cannot_hide_explicit_host_truth(self):
        for masked_name in ("__mro__", "__dict__", "__name__"):
            with self.subTest(masked_name=masked_name):
                events = []

                def masked_structure(host, masked_name=masked_name):
                    events.append("metaclass descriptor")
                    if masked_name == "__mro__":
                        return (object,)
                    if masked_name == "__name__":
                        return "HiddenHost"
                    namespace = dict(type.__dict__["__dict__"].__get__(host, type(host)))
                    namespace.pop("__bool__", None)
                    return namespace

                MaskingMeta = type("MaskingMeta", (type,), {
                        masked_name: property(masked_structure),
                        })

                class TruthHost(metaclass=MaskingMeta):
                    def __bool__(agent):
                        events.append("host truth")
                        return False

                class Prepared(Tag):
                    @Pre
                    def Accepted(agent):
                        events.append("Gate")
                        return True

                    @Record
                    def value(agent):
                        events.append("Record")
                        return 1

                    @Imprint
                    def Train(agent):
                        events.append("Imprint")

                agent = TruthHost()
                agent.existing = "unchanged"
                before = dict(vars(agent))
                with self.assertRaises(TagCompositionError) as caught:
                    Prepared(agent)
                self.assertIn("TruthHost", str(caught.exception))
                self.assertIn("__bool__", str(caught.exception))
                self.assertEqual(events, [])
                self.assertIs(type(agent), TruthHost)
                self.assertEqual(vars(agent), before)
                self.assertEqual(Tags(agent), ())
                self.assertNotIn(agent, Prepared[:])

    def test_pinned_tag_truth_reads_its_own_posts(self):
        class Agency(Tag):
            ready = True

        @Pin
        class Certified(Tag):
            @Post
            def Ready(tag):
                return tag.ready

        Certified(Agency)
        self.assertTrue(Agency)
        self.assertEqual(len(Agency), 0)

        agent = Host()
        Agency(agent)
        Agency.ready = False
        self.assertFalse(Agency)
        self.assertIn(Agency, ~Certified)
        self.assertEqual(len(Agency), 1)

    def test_custom_truth_on_a_runtime_subclass_is_still_a_host_protocol(self):
        class Member(Tag):
            pass

        first = Host()
        Member(first)
        events = []

        class WithTruth(type(first)):
            def __bool__(agent):
                events.append("custom truth")
                return False

        class InheritedTruth(WithTruth):
            pass

        class DisabledTruth(type(first)):
            __bool__ = None

        class Prepared(Tag):
            @Imprint
            def Train(agent):
                events.append("training")

        for host_type in (WithTruth, InheritedTruth, DisabledTruth):
            with self.subTest(host=host_type):
                agent = host_type()
                with self.assertRaises(TagCompositionError):
                    Prepared(agent)
                self.assertIs(type(agent), host_type)
                self.assertEqual(vars(agent), {})
                self.assertEqual(Tags(agent), ())
        self.assertEqual(events, [])

    def test_agent_scope_bool_declarations_are_refused_by_binding_name(self):
        for kind in AGENT_TRUTH_MEMBERS:
            with self.subTest(kind=kind):
                with self.assertRaises(TagDeclarationError) as caught:
                    type("InvalidTruth", (Tag,), {"__bool__": _member_for(kind)})
                self.assertIn("__bool__", str(caught.exception))

    def test_late_agent_scope_bool_assignment_is_refused_atomically(self):
        for kind in AGENT_TRUTH_MEMBERS:
            with self.subTest(kind=kind):
                class Member(Tag):
                    pass

                agent = Host()
                Member(agent)
                with self.assertRaises(TagDeclarationError):
                    Member.__bool__ = _member_for(kind)
                self.assertNotIn("__bool__", vars(Member))
                self.assertTrue(agent)
                later = Host()
                Member(later)
                self.assertTrue(later)

    def test_function_named_bool_can_bind_an_ordinary_action_name(self):
        def __bool__(agent):
            return False

        NamedTruth = type("NamedTruth", (Tag,), {"ReadTruth": Action(__bool__)})
        agent = Host()
        NamedTruth(agent)
        self.assertFalse(agent.ReadTruth())
        self.assertTrue(agent)

    def test_scan_refuses_truth_publication_marked_after_declaration(self):
        for mark in (Report, Operation):
            with self.subTest(mark=mark):
                def calculate(receiver, *arguments):
                    raise AssertionError("publication validation ran the builder")

                Shared = type("SharedTruth", (Tag,), {"__bool__": mark(calculate)})
                Public(vars(Shared)["__bool__"])
                agent = Host()
                before = dict(vars(agent))
                with self.assertRaises(TagDeclarationError):
                    Shared(agent)
                self.assertEqual(vars(agent), before)
                self.assertIs(type(agent), Host)
                self.assertNotIn(agent, Shared[:])

    def test_unpublished_bool_reports_and_operations_remain_tag_members(self):
        class SharedReport(Tag):
            @Report
            def __bool__(tag):
                return False

        class SharedOperation(Tag):
            @Operation
            def __bool__(tag):
                return False

        self.assertIs(SharedReport.__bool__, False)
        self.assertIs(SharedOperation.__bool__(), False)
        for tag in (SharedReport, SharedOperation):
            with self.subTest(tag=tag):
                agent = Host()
                tag(agent)
                self.assertTrue(agent)

    def test_other_python_protocol_actions_remain_available(self):
        events = []

        class Protocols(Tag):
            def __add__(agent, value):
                return agent.number + value

            def __enter__(agent):
                events.append("enter")
                return agent

            def __exit__(agent, exception_type, exception, traceback):
                events.append("exit")
                return False

        agent = Host()
        agent.number = 3
        Protocols(agent)
        self.assertEqual(agent + 4, 7)
        with agent as entered:
            self.assertIs(entered, agent)
        self.assertEqual(events, ["enter", "exit"])
        self.assertTrue(agent)

    def test_record_objects_keep_their_own_truth_without_becoming_agents(self):
        class ToolValue:
            def __init__(tool):
                tool.ready = False

            def __bool__(tool):
                return tool.ready

        value = ToolValue()

        class Equipped(Tag):
            @Record
            def weapon(agent):
                return value

        agent = Host()
        Equipped(agent)
        self.assertIs(agent.weapon, value)
        self.assertTrue("weapon" @ agent)
        self.assertFalse(agent.weapon)
        self.assertTrue(agent)
        value.ready = True
        self.assertTrue(agent.weapon)
        self.assertIs(type(value), ToolValue)
        self.assertEqual(Tags(value), ())


if __name__ == "__main__":
    unittest.main()
