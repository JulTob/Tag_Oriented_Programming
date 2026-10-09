"""A name queries the contribution currently available on a TOP Agent."""

import unittest

from TopKit import (Action, Contract, Delete, Imprint, Operation, Pin, Post,
                    Public, Record, Report, Secret, Tag, TagPostconditionError,
                    TagResolutionError, Underlay)


class Host:
    pass


class ContributionPresenceTests(unittest.TestCase):
    def test_records_count_as_present_independently_of_their_values(self):
        class Values(Tag):
            @Record
            def none(agent):
                return None

            @Record
            def false(agent):
                return False

            @Record
            def zero(agent):
                return 0

            @Record
            def empty(agent):
                return []

        agent = Host()
        Values(agent)

        for name in ("none", "false", "zero", "empty"):
            with self.subTest(name=name):
                self.assertIs(name @ agent, True)
        self.assertIs("missing" @ agent, False)

    def test_unapplied_declarations_and_deleted_bindings_are_absent(self):
        class Given(Tag):
            @Record
            def value(agent):
                return None

            @Action
            def Work(agent):
                raise AssertionError("presence must not execute an Action")

        class NotGiven(Tag):
            @Record
            def future(agent):
                return 1

        agent = Host()
        Given(agent)
        self.assertTrue("value" @ agent)
        self.assertTrue("Work" @ agent)
        self.assertFalse("future" @ agent)

        del agent.value
        del agent.Work
        self.assertFalse("value" @ agent)
        self.assertFalse("Work" @ agent)

    def test_layer_deletion_hides_host_and_top_members(self):
        class WithHost(Host):
            def inherited(agent):
                raise AssertionError("presence must not execute a host method")

        class Given(Tag):
            @Record
            def value(agent):
                return False

        class Removed(Given):
            @Delete
            def value(agent): ...

            @Delete
            def inherited(agent): ...

        agent = WithHost()
        Removed(agent)

        self.assertFalse("value" @ agent)
        self.assertFalse("inherited" @ agent)

    def test_presence_follows_action_record_changes_on_the_current_overlay(self):
        class Behaviour(Tag):
            @Action
            def gain(agent):
                raise AssertionError("presence must not execute an Action")

        class Data(Behaviour):
            @Record
            def gain(agent):
                return False

        class BehaviourAgain(Data):
            @Action
            def gain(agent):
                return "current Action"

        agent = Host()
        Behaviour(agent)
        self.assertTrue("gain" @ agent)
        Data(agent)
        self.assertTrue("gain" @ agent)
        self.assertIs(agent.gain, False)
        BehaviourAgain(agent)
        self.assertTrue("gain" @ agent)
        self.assertEqual(agent.gain(), "current Action")

    def test_host_fields_and_inherited_methods_count_without_execution(self):
        calls = []

        class Parent:
            inherited_value = None

            def Work(agent):
                calls.append("Work")

        class Child(Parent):
            def __init__(agent):
                agent.value = 0

        class Marked(Tag):
            pass

        agent = Child()
        Marked(agent)

        self.assertTrue("value" @ agent)
        self.assertTrue("inherited_value" @ agent)
        self.assertTrue("Work" @ agent)
        self.assertFalse("missing" @ agent)
        self.assertEqual(calls, [])

    def test_a_host_property_is_present_without_running_its_getter(self):
        calls = []

        class WithProperty:
            @property
            def value(agent):
                calls.append("getter")
                raise AssertionError("presence must not evaluate a property")

        class Marked(Tag):
            pass

        agent = WithProperty()
        Marked(agent)

        self.assertTrue("value" @ agent)
        self.assertEqual(calls, [])

    def test_a_host_slot_counts_only_after_a_value_is_stored(self):
        class WithSlots:
            __slots__ = ("value", "__dict__", "__weakref__")

        class Marked(Tag):
            pass

        agent = WithSlots()
        Marked(agent)

        self.assertFalse("value" @ agent)
        agent.value = None
        self.assertTrue("value" @ agent)
        del agent.value
        self.assertFalse("value" @ agent)

    def test_post_can_require_presence_while_a_gain_remains_optional(self):
        class Prepared(Tag):
            @Record
            def required(agent):
                return None

            @Imprint
            def Optional(agent):
                if agent.want_optional:
                    agent.optional = False

            @Post
            def Equipped(agent):
                return "required" @ agent

        agent = Host()
        agent.want_optional = False
        Prepared(agent)

        self.assertTrue(Contract.Holds(agent))
        self.assertFalse("optional" @ agent)
        agent.optional = False
        self.assertTrue("optional" @ agent)
        del agent.required
        self.assertFalse(Contract.Holds(agent))

    def test_a_post_requiring_a_missing_name_raises_and_keeps_the_tag(self):
        class Promised(Tag):
            @Post
            def Equipped(agent):
                return "missing" @ agent

        agent = Host()
        with self.assertRaises(TagPostconditionError.Equipped):
            Promised(agent)

        self.assertIn(agent, Promised[:])
        self.assertFalse("missing" @ agent)
        self.assertFalse(Contract.Holds(agent))

    def test_nonstring_matrix_operands_keep_the_host_operators(self):
        calls = []

        class NumericHost:
            def __rmatmul__(agent, operand):
                calls.append(("reflected", operand))
                return operand * 3

            def __matmul__(agent, operand):
                calls.append(("forward", operand))
                return operand * 5

        class Given(Tag):
            @Record
            def value(agent):
                return None

        agent = NumericHost()
        Given(agent)

        self.assertTrue("value" @ agent)
        self.assertFalse("missing" @ agent)
        self.assertEqual(calls, [])
        self.assertEqual(4 @ agent, 12)
        self.assertEqual(agent @ 4, 20)
        self.assertEqual(calls, [("reflected", 4), ("forward", 4)])

    def test_nonstring_matrix_operands_keep_a_top_reflected_action(self):
        calls = []

        class Numeric(Tag):
            @Record
            def value(agent):
                return 0

            @Action
            def __rmatmul__(agent, operand):
                calls.append(operand)
                return operand * 2

        agent = Host()
        Numeric(agent)

        self.assertTrue("value" @ agent)
        self.assertFalse("missing" @ agent)
        self.assertEqual(calls, [])
        self.assertEqual(6 @ agent, 12)
        self.assertEqual(calls, [6])

    def test_tagging_does_not_give_an_unchanged_host_reflection_priority(self):
        calls = []

        class NumericHost:
            def __matmul__(agent, operand):
                calls.append("direct")
                return "host direct"

            def __rmatmul__(agent, operand):
                calls.append("reflected")
                return "host reflected"

        class Marked(Tag):
            pass

        left, right = NumericHost(), NumericHost()
        Marked(right)

        self.assertEqual(left @ right, "host direct")
        self.assertEqual(calls, ["direct"])

    def test_not_implemented_keeps_subtype_host_call_order_without_retries(self):
        calls = []

        class NumericHost:
            def __matmul__(agent, operand):
                calls.append("direct")
                return NotImplemented

            def __rmatmul__(agent, operand):
                calls.append("reflected")
                return NotImplemented

        class Child(NumericHost):
            pass

        class Marked(Tag):
            pass

        left = NumericHost()
        with self.assertRaises(TypeError):
            left @ Child()
        self.assertEqual(calls, ["direct", "reflected"])
        calls.clear()

        right = NumericHost()
        Marked(right)
        with self.assertRaises(TypeError):
            left @ right
        self.assertEqual(calls, ["direct", "reflected"])

    def test_a_new_top_reflected_action_keeps_right_subtype_priority(self):
        calls = []

        class NumericHost:
            def __matmul__(agent, operand):
                calls.append("host direct")
                return "host direct"

            def __rmatmul__(agent, operand):
                calls.append("host reflected")
                return "host reflected"

        class Reflected(Tag):
            @Action
            def __rmatmul__(agent, operand):
                calls.append("TOP reflected")
                return "TOP reflected"

        left, right = NumericHost(), NumericHost()
        Reflected(right)

        self.assertEqual(left @ right, "TOP reflected")
        self.assertEqual(calls, ["TOP reflected"])

    def test_a_host_subclass_of_an_agent_runtime_keeps_its_numeric_fallback(self):
        calls = []

        class NumericHost:
            def __rmatmul__(agent, operand):
                calls.append(operand)
                return operand * 3

        class Marked(Tag):
            @Record
            def value(agent):
                return None

        first = NumericHost()
        Marked(first)

        class Derived(type(first)):
            pass

        second = Derived()
        Marked(second)

        self.assertTrue("value" @ second)
        self.assertEqual(5 @ second, 15)
        self.assertEqual(calls, [5])

    def test_an_underlay_can_extend_the_fallback_of_an_inherited_agent_runtime(self):
        calls = []

        class NumericHost:
            def __rmatmul__(agent, operand):
                calls.append("host")
                return operand * 3

        class Marked(Tag):
            pass

        first = NumericHost()
        Marked(first)

        class Derived(type(first)):
            pass

        class Extended(Tag):
            @Action
            @Underlay
            def __rmatmul__(agent, underlay, operand):
                calls.append("TOP")
                return underlay(operand) + 1

        second = Derived()
        Extended(second)

        self.assertEqual(5 @ second, 16)
        self.assertEqual(calls, ["TOP", "host"])

    def test_the_presence_hook_is_not_an_underlay_when_the_host_has_no_operator(self):
        class Marked(Tag):
            pass

        first = Host()
        Marked(first)

        class Derived(type(first)):
            pass

        class RequiresUnderlay(Tag):
            @Action
            @Underlay
            def __rmatmul__(agent, underlay, operand):
                return underlay(operand)

        second = Derived()
        with self.assertRaises(TagResolutionError):
            RequiresUnderlay(second)
        self.assertNotIn(second, RequiresUnderlay[:])

    def test_a_nonstring_operand_without_a_matrix_operator_is_unsupported(self):
        class Marked(Tag):
            pass

        agent = Host()
        Marked(agent)

        with self.assertRaises(TypeError):
            5 @ agent
        with self.assertRaises(TypeError):
            agent @ 5

    def test_a_nonstring_operand_is_classified_without_reading_its_class_attribute(self):
        inspected = []
        received = []

        class Operand:
            @property
            def __class__(operand):
                inspected.append("class getter")
                raise AssertionError("operator dispatch must not inspect the operand")

        class NumericHost:
            def __rmatmul__(agent, operand):
                received.append(operand)
                return "host result"

        class Marked(Tag):
            pass

        agent = NumericHost()
        Marked(agent)
        operand = Operand()

        self.assertEqual(operand @ agent, "host result")
        self.assertEqual(len(received), 1)
        self.assertIs(received[0], operand)
        with self.assertRaises(TypeError):
            operand @ Marked[agent]
        self.assertEqual(inspected, [])

    def test_presence_does_not_evaluate_a_host_shadowing_dict(self):
        calls = []

        class Base:
            pass

        class WithShadowedDict(Base):
            @property
            def __dict__(agent):
                calls.append("dict getter")
                return Base.__dict__["__dict__"].__get__(agent, type(agent))

        class Given(Tag):
            @Record
            def value(agent):
                return None

        agent = WithShadowedDict()
        Given(agent)
        calls.clear()

        self.assertTrue("value" @ agent)
        self.assertFalse("missing" @ agent)
        self.assertEqual(calls, [])

    def test_presence_does_not_run_a_host_getattribute_override(self):
        calls = []

        class ObservedHost:
            def __getattribute__(agent, name):
                calls.append(name)
                return object.__getattribute__(agent, name)

            def Work(agent):
                raise AssertionError("presence must not execute a host method")

        class Marked(Tag):
            pass

        agent = ObservedHost()
        agent.value = None
        Marked(agent)
        calls.clear()

        self.assertTrue("value" @ agent)
        self.assertTrue("Work" @ agent)
        self.assertFalse("missing" @ agent)
        self.assertEqual(calls, [])

    def test_a_stored_slot_descriptor_is_a_value_rather_than_an_unfilled_slot(self):
        class Slotted:
            __slots__ = ("value",)

        descriptor = Slotted.__dict__["value"]

        class Given(Tag):
            @Record
            def record(agent):
                return descriptor

        agent = Host()
        agent.field = descriptor
        Given(agent)

        self.assertTrue("record" @ agent)
        self.assertTrue("field" @ agent)
        self.assertIs(agent.record, descriptor)
        self.assertIs(agent.field, descriptor)

    def test_a_host_class_value_is_classified_without_reading_its_class_attribute(self):
        inspected = []

        class Value:
            @property
            def __class__(value):
                inspected.append("class getter")
                raise AssertionError("presence must not inspect the value dynamically")

        class WithClassValue:
            value = Value()

        class Marked(Tag):
            pass

        agent = WithClassValue()
        Marked(agent)

        self.assertTrue("value" @ agent)
        self.assertFalse("missing" @ agent)
        self.assertEqual(inspected, [])

    def test_shared_members_follow_the_agent_or_view_scope_without_execution(self):
        calls = []

        class Shared(Tag):
            @Report
            def internal_report(tag):
                calls.append("internal Report")
                return False

            @Operation
            def InternalOperation(tag):
                raise AssertionError("presence must not execute an Operation")

            @Public
            @Report
            def published_report(tag):
                calls.append("published Report")
                return None

            @Public
            @Operation
            def PublishedOperation(tag, agent):
                raise AssertionError("presence must not execute an Operation")

        agent = Host()
        Shared(agent)
        before = list(calls)

        self.assertTrue("published_report" @ agent)
        self.assertTrue("PublishedOperation" @ agent)
        self.assertFalse("internal_report" @ agent)
        self.assertFalse("InternalOperation" @ agent)
        view = Shared[agent]
        for name in ("internal_report", "InternalOperation",
                     "published_report", "PublishedOperation"):
            with self.subTest(name=name):
                self.assertTrue(name @ view)
        self.assertEqual(calls, before)

        del Shared[agent]
        self.assertFalse("published_report" @ agent)
        # A published Operation remains a bound contribution after Rip;
        # presence alone does not promise that its origin can still serve it.
        self.assertTrue("PublishedOperation" @ agent)
        self.assertEqual(calls, before)

    def test_view_presence_uses_its_captured_context_after_live_deletion(self):
        class First(Tag):
            @Record
            def value(agent):
                return 1

        class Later(First):
            @Record
            def value(agent):
                return 2

            @Record
            def later(agent):
                return False

        agent = Host()
        Later(agent)
        first_view = First[agent]
        later_view = Later[agent]
        del agent.value

        self.assertFalse("value" @ agent)
        self.assertTrue("value" @ first_view)
        self.assertTrue("value" @ later_view)
        self.assertFalse("later" @ first_view)
        self.assertTrue("later" @ later_view)
        self.assertEqual(first_view.value, 1)
        self.assertEqual(later_view.value, 2)

    def test_secret_presence_follows_the_receiver_composition_context(self):
        observed = []

        class Hidden(Tag):
            @Secret
            @Record
            def token(agent):
                return None

            @Secret
            @Action
            def Conceal(agent):
                raise AssertionError("presence must not execute a Secret Action")

            @Imprint
            def Inspect(agent):
                observed.append(("token" @ agent, "Conceal" @ agent))

            @Post
            def Equipped(agent):
                return "token" @ agent

            @Action
            def InspectAgain(agent):
                return "token" @ agent, "Conceal" @ agent

        agent = Host()
        Hidden(agent)

        self.assertEqual(observed, [(True, True)])
        self.assertFalse("token" @ agent)
        self.assertFalse("Conceal" @ agent)
        self.assertFalse("token" @ Hidden[agent])
        self.assertFalse("Conceal" @ Hidden[agent])
        self.assertEqual(agent.InspectAgain(), (True, True))

    def test_a_pin_answers_as_the_agent_without_executing_its_operation(self):
        @Pin
        class Given(Tag):
            @Record
            def value(tag):
                return None

            @Action
            def Work(tag):
                raise AssertionError("presence must not execute a pinned Action")

        class Receiver(Tag):
            pass

        Given(Receiver)

        self.assertTrue("value" @ Receiver)
        self.assertTrue("Work" @ Receiver)
        self.assertFalse("missing" @ Receiver)
        self.assertTrue("value" @ Given[Receiver])
        self.assertTrue("Work" @ Given[Receiver])


if __name__ == "__main__":
    unittest.main()
