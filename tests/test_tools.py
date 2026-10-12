"""A Tool admits values by host class without owning or training them."""

import gc
import itertools
import unittest
import weakref
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from TopKit import (Action, Constant, Contract, Delete, Imprint, Operation,
                    Pin, Post, Pre, Public, Record, Report, Rip, Secret, Tag,
                    TagCompositionError, TagDeclarationError, TagImprintError,
                    TagPostconditionError, Tool)


class Host:
    pass


class Sword:
    pass


class Shield:
    pass


class ToolTests(unittest.TestCase):
    def test_host_class_admits_tagged_and_untagged_instances_and_subclasses(self):
        class Weapon(Tag):
            pass

        class Longsword(Sword):
            pass

        class Equipped(Tag):
            @Tool(Sword)
            def weapon(agent, *, weapon):
                return weapon

        for sword in (Sword(), Longsword()):
            with self.subTest(host=type(sword)):
                agent = Host()
                Equipped(agent, weapon=sword)
                self.assertIs(agent.weapon, sword)
                self.assertNotIn(sword, Weapon[:])
                Weapon(sword)
                agent.weapon = sword
                self.assertIs(Equipped[agent].weapon, sword)

        shield = Shield()
        Weapon(shield)
        agent = Host()
        with self.assertRaisesRegex(TagCompositionError, r"Equipped\.weapon"):
            Equipped(agent, weapon=shield)
        self.assertNotIn(agent, Equipped[:])
        self.assertIn(shield, Weapon[:])

    def test_union_alternatives_and_none_are_independent_of_presence(self):
        class Equipped(Tag):
            @Tool(Sword | Shield | None)
            def weapon(agent, *, weapon):
                return weapon

        agent = Host()
        Equipped(agent, weapon=Sword())
        shield = Shield()
        agent.weapon = shield
        self.assertIs(agent.weapon, shield)
        agent.weapon = None
        self.assertIsNone(agent.weapon)
        self.assertTrue("weapon" @ agent)
        del agent.weapon
        self.assertFalse("weapon" @ agent)
        with self.assertRaises(TagCompositionError):
            agent.weapon = "not equipment"
        self.assertFalse("weapon" @ agent)
        agent.weapon = sword = Sword()
        self.assertIs(agent.weapon, sword)

    def test_strict_policy_rejects_none_at_gain_and_on_write(self):
        class Equipped(Tag):
            @Tool(Sword)
            def weapon(agent, *, weapon):
                return weapon

        agent = Host()
        with self.assertRaises(TagCompositionError):
            Equipped(agent, weapon=None)
        self.assertFalse("weapon" @ agent)
        self.assertNotIn(agent, Equipped[:])
        sword = Sword()
        Equipped(agent, weapon=sword)
        with self.assertRaises(TagCompositionError):
            agent.weapon = None
        self.assertIs(agent.weapon, sword)

    def test_object_policy_requires_explicit_nullability_and_false_is_present(self):
        class AnyValue(Tag):
            @Tool(object)
            def tool(agent, *, tool):
                return tool

        class OptionalValue(Tag):
            @Tool(object | None)
            def tool(agent, *, tool):
                return tool

        class BooleanValue(Tag):
            @Tool(bool)
            def tool(agent):
                return False

        agent = Host()
        with self.assertRaises(TagCompositionError):
            AnyValue(agent, tool=None)
        self.assertFalse("tool" @ agent)
        OptionalValue(agent, tool=None)
        self.assertIsNone(agent.tool)
        self.assertTrue("tool" @ agent)
        agent = Host()
        BooleanValue(agent)
        self.assertIs(agent.tool, False)
        self.assertTrue("tool" @ agent)

    def test_plain_class_with_a_tag_lookalike_marker_is_still_a_host_policy(self):
        class Lookalike:
            _topkit_field = object()

        class Given(Tag):
            @Tool(Lookalike)
            def tool(agent, *, tool):
                return tool

        agent = Host()
        value = Lookalike()
        Given(agent, tool=value)
        self.assertIs(agent.tool, value)

    def test_admission_and_reads_do_not_evaluate_host_truth_or_posts(self):
        class FalseSword(Sword):
            def __bool__(sword):
                raise AssertionError("admission must not ask for host truth")

        calls = []

        class Weapon(Tag):
            @Post
            def HasEdge(sword):
                calls.append("HasEdge")
                return sword.edge

        class Equipped(Tag):
            @Tool(Sword)
            def weapon(agent, *, weapon):
                return weapon

        plain = FalseSword()
        agent = Host()
        Equipped(agent, weapon=plain)
        self.assertIs(agent.weapon, plain)
        sword = Sword()
        sword.edge = True
        Weapon(sword)
        sword.edge = False
        calls.clear()
        agent.weapon = sword
        self.assertIs(agent.weapon, sword)
        self.assertTrue("weapon" @ agent)
        self.assertEqual(calls, [])
        self.assertFalse(Contract.Holds(sword))
        self.assertEqual(calls, ["HasEdge"])

    def test_compatible_rogue_is_admitted_without_restoring_its_tag(self):
        class Weapon(Tag):
            @Record
            def damage(sword):
                return 6

        class Equipped(Tag):
            @Tool(Sword)
            def weapon(agent, *, weapon):
                return weapon

        sword = Sword()
        Weapon(sword)
        del Weapon[sword]
        agent = Host()
        Equipped(agent, weapon=sword)
        self.assertIs(agent.weapon, sword)
        self.assertNotIn(sword, Weapon[:])
        self.assertEqual(sword.damage, 6)

    def test_self_reference_is_allowed_and_a_post_can_forbid_it(self):
        class SelfHeld(Tag):
            @Tool(Host)
            def tool(agent):
                return agent

        agent = Host()
        SelfHeld(agent)
        self.assertIs(agent.tool, agent)

        class Independent(SelfHeld):
            @Post
            def Other(agent):
                return agent.tool is not agent

        other = Host()
        with self.assertRaises(TagPostconditionError.Other):
            Independent(other)
        self.assertIs(other.tool, other)
        self.assertIn(other, Independent[:])

    def test_subsequent_gains_can_read_the_tool(self):
        class Equipped(Tag):
            @Tool(Sword)
            def weapon(agent, *, weapon):
                return weapon

            @Record
            def same_weapon(agent):
                return agent.weapon

        agent = Host()
        sword = Sword()
        Equipped(agent, weapon=sword)
        self.assertIs(agent.same_weapon, sword)

    def test_failed_admission_retains_earlier_gains_and_posts_without_entry(self):
        class Unfinished(Tag):
            @Record
            def first(agent):
                return "already gained"

            @Post
            def Ready(agent):
                return False

            @Tool(Sword)
            def weapon(agent):
                return "wrong host"

            @Record
            def later(agent):
                return "not reached"

        agent = Host()
        with self.assertRaisesRegex(TagCompositionError, r"Unfinished\.weapon"):
            Unfinished(agent)
        self.assertEqual(agent.first, "already gained")
        self.assertFalse("weapon" @ agent)
        self.assertFalse("later" @ agent)
        self.assertEqual(Contract.Status(agent), {"Ready": False})
        self.assertNotIn(agent, Unfinished[:])

    def test_failed_replacement_preserves_the_previous_value_and_policy(self):
        class Equipped(Tag):
            @Tool(Sword)
            def weapon(agent, *, weapon):
                return weapon

        class Changed(Tag):
            @Tool(Shield)
            def weapon(agent):
                return "wrong host"

        sword = Sword()
        agent = Host()
        Equipped(agent, weapon=sword)
        with self.assertRaises(TagCompositionError):
            Changed(agent)
        self.assertIs(agent.weapon, sword)
        with self.assertRaises(TagCompositionError):
            agent.weapon = Shield()
        self.assertNotIn(agent, Changed[:])

    def test_imprint_failure_retains_the_tool_and_its_admission_rule(self):
        class Unfinished(Tag):
            @Tool(Sword)
            def weapon(agent, *, weapon):
                return weapon

            @Imprint
            def Train(agent):
                raise ValueError("training failed")

        agent = Host()
        sword = Sword()
        with self.assertRaises(TagImprintError):
            Unfinished(agent, weapon=sword)
        self.assertIs(agent.weapon, sword)
        self.assertNotIn(agent, Unfinished[:])
        with self.assertRaises(TagCompositionError):
            agent.weapon = Shield()
        self.assertIs(agent.weapon, sword)

    def test_supported_writes_reject_before_custom_host_effects(self):
        writes = []

        class CustomHost:
            def __setattr__(agent, name, value):
                writes.append((name, value))
                if name == "__class__":
                    object.__setattr__(agent, name, value)
                else:
                    agent.__dict__[name] = value

        class Equipped(Tag):
            @Tool(Sword)
            def weapon(agent, *, weapon):
                return weapon

        agent = CustomHost()
        original = Sword()
        Equipped(agent, weapon=original)
        writes.clear()
        for write in (setattr, object.__setattr__):
            with self.subTest(write=write):
                with self.assertRaisesRegex(TagCompositionError, r"Equipped\.weapon"):
                    write(agent, "weapon", Shield())
                self.assertIs(agent.weapon, original)
        self.assertEqual(writes, [])
        replacement = Sword()
        agent.weapon = replacement
        self.assertIs(agent.weapon, replacement)
        self.assertEqual(writes, [("weapon", replacement)])
        object.__setattr__(agent, "weapon", original)
        self.assertIs(agent.weapon, original)

    def test_initial_gain_uses_kernel_path_on_a_frozen_dataclass(self):
        @dataclass(frozen=True)
        class FrozenHost:
            name: str

        class Equipped(Tag):
            @Tool(Sword)
            def weapon(agent, *, weapon):
                return weapon

        agent = FrozenHost("bearer")
        sword = Sword()
        Equipped(agent, weapon=sword)
        self.assertIs(agent.weapon, sword)
        with self.assertRaises(TagCompositionError):
            object.__setattr__(agent, "weapon", Shield())
        self.assertIs(agent.weapon, sword)

    def test_rip_and_value_deletion_preserve_the_admission_rule(self):
        class Equipped(Tag):
            @Tool(Sword)
            def weapon(agent, *, weapon):
                return weapon

        agent = Host()
        sword = Sword()
        Equipped(agent, weapon=sword)
        del Equipped[agent]
        self.assertIs(agent.weapon, sword)
        del agent.weapon
        self.assertFalse("weapon" @ agent)
        with self.assertRaises(TagCompositionError):
            agent.weapon = Shield()
        self.assertFalse("weapon" @ agent)
        agent.weapon = replacement = Sword()
        self.assertIs(agent.weapon, replacement)
        self.assertNotIn(agent, Equipped[:])

    def test_delete_and_plain_record_overlay_end_the_admission_rule(self):
        class Equipped(Tag):
            @Tool(Sword)
            def weapon(agent, *, weapon):
                return weapon

        class Removed(Tag):
            @Delete
            def weapon(agent): ...

        class Ordinary(Tag):
            @Record
            def weapon(agent):
                return "plain Record"

        for overlay in (Removed, Ordinary):
            with self.subTest(overlay=overlay):
                agent = Host()
                Equipped(agent, weapon=Sword())
                overlay(agent)
                agent.weapon = None
                self.assertIsNone(agent.weapon)
                agent.weapon = Shield()
                self.assertIsInstance(agent.weapon, Shield)

    def test_action_overlay_replaces_the_tool_without_a_result_constraint(self):
        class Equipped(Tag):
            @Tool(Sword)
            def weapon(agent, *, weapon):
                return weapon

        class Query(Equipped):
            @Action
            def weapon(agent):
                return "ordinary Action result"

        agent = Host()
        Equipped(agent, weapon=Sword())
        Query(agent)
        self.assertEqual(agent.weapon(), "ordinary Action result")
        agent.weapon = None
        self.assertIsNone(agent.weapon)

    def test_tool_overlay_replaces_the_class_policy(self):
        class Equipped(Tag):
            @Tool(Sword)
            def weapon(agent, *, weapon):
                return weapon

        class Shielded(Tag):
            @Tool(Shield)
            def weapon(agent, *, shield):
                return shield

        agent = Host()
        Equipped(agent, weapon=Sword())
        shield = Shield()
        Shielded(agent, shield=shield)
        self.assertIs(agent.weapon, shield)
        with self.assertRaises(TagCompositionError):
            agent.weapon = Sword()
        self.assertIs(agent.weapon, shield)

    def test_reapplication_rebuilds_ordinary_tools_and_checks_new_values(self):
        class Equipped(Tag):
            @Tool(Sword)
            def weapon(agent, stored, *, replacement=None):
                return stored if replacement is None else replacement

        agent = Host()
        original = Sword()
        Equipped(agent, replacement=original)
        del Equipped[agent]
        with self.assertRaises(TagCompositionError):
            Equipped(agent, replacement=Shield())
        self.assertIs(agent.weapon, original)
        self.assertNotIn(agent, Equipped[:])
        replacement = Sword()
        Equipped(agent, replacement=replacement)
        self.assertIs(agent.weapon, replacement)

    def test_constant_locks_the_binding_but_not_the_tool_and_builds_once(self):
        builds = []

        class Weapon(Tag):
            pass

        class Equipped(Tag):
            @Constant
            @Tool(Sword)
            def weapon(agent, *, weapon):
                builds.append("weapon")
                return weapon

        sword = Sword()
        Weapon(sword)
        agent = Host()
        Equipped(agent, weapon=sword)
        sword.damage = 10
        del Weapon[sword]
        del Equipped[agent]
        Equipped(agent, weapon=Shield())
        self.assertEqual(builds, ["weapon"])
        self.assertIs(agent.weapon, sword)
        self.assertEqual(sword.damage, 10)
        self.assertNotIn(sword, Weapon[:])
        for write in (setattr, object.__setattr__):
            with self.subTest(write=write):
                with self.assertRaises(TagCompositionError):
                    write(agent, "weapon", Sword())
        with self.assertRaises(TagCompositionError):
            del agent.weapon

        class Removed(Tag):
            @Delete
            def weapon(agent): ...

        class Ordinary(Tag):
            @Record
            def weapon(agent):
                return None

        for overlay in (Removed, Ordinary):
            with self.subTest(overlay=overlay):
                with self.assertRaises(TagCompositionError):
                    overlay(agent)
                self.assertIs(agent.weapon, sword)

    def test_record_and_constant_modifier_orders_keep_the_same_contract(self):
        for marks in itertools.permutations((Tool(Sword), Record, Constant)):
            with self.subTest(marks=marks):
                def weapon(agent, *, weapon):
                    return weapon

                for mark in marks:
                    weapon = mark(weapon)
                Equipped = type("Equipped", (Tag,), {"weapon": weapon})
                agent = Host()
                sword = Sword()
                Equipped(agent, weapon=sword)
                self.assertIs(agent.weapon, sword)
                with self.assertRaises(TagCompositionError):
                    agent.weapon = Sword()

    def test_secret_tool_presence_and_writes_follow_the_bearers_door(self):
        for marks in ((Tool(Sword), Secret), (Secret, Tool(Sword))):
            with self.subTest(marks=marks):
                def weapon(agent, *, weapon):
                    return weapon

                for mark in marks:
                    weapon = mark(weapon)

                def Read(agent):
                    return "weapon" @ agent, agent.weapon

                def Set(agent, replacement):
                    agent.weapon = replacement

                Equipped = type("Equipped", (Tag,), {
                    "weapon": weapon, "Read": Read, "Set": Set,
                })
                agent = Host()
                sword = Sword()
                Equipped(agent, weapon=sword)
                self.assertFalse("weapon" @ agent)
                with self.assertRaises(AttributeError):
                    agent.weapon
                self.assertEqual(agent.Read(), (True, sword))
                with self.assertRaises(TagCompositionError):
                    agent.Set(Shield())
                self.assertEqual(agent.Read(), (True, sword))

    def test_public_modifier_orders_keep_the_tool_available(self):
        for marks in ((Tool(Sword), Public), (Public, Tool(Sword))):
            with self.subTest(marks=marks):
                def weapon(agent, *, weapon):
                    return weapon

                for mark in marks:
                    weapon = mark(weapon)
                Equipped = type("Equipped", (Tag,), {"weapon": weapon})
                agent = Host()
                sword = Sword()
                Equipped(agent, weapon=sword)
                self.assertIs(agent.weapon, sword)
                self.assertTrue("weapon" @ agent)

    def test_constant_stacks_with_visibility_modifiers_in_either_order(self):
        for visibility in (Secret, Public):
            for marks in itertools.permutations((Tool(Sword), Constant, visibility)):
                with self.subTest(visibility=visibility, marks=marks):
                    def weapon(agent, *, weapon):
                        return weapon

                    for mark in marks:
                        weapon = mark(weapon)

                    def Read(agent):
                        return agent.weapon

                    Equipped = type("Equipped", (Tag,), {
                        "weapon": weapon, "Read": Read,
                    })
                    agent = Host()
                    sword = Sword()
                    Equipped(agent, weapon=sword)
                    self.assertIs(agent.Read(), sword)
                    with self.assertRaises(TagCompositionError):
                        object.__setattr__(agent, "weapon", Sword())
                    self.assertIs(agent.Read(), sword)

    def test_callable_value_remains_a_record_and_plain_false_records_are_unchanged(self):
        class CallableSword(Sword):
            def __call__(sword):
                return "held callable"

        class Equipped(Tag):
            @Tool(Sword)
            def weapon(agent, *, weapon):
                return weapon

            @Record
            def false(agent):
                return False

        agent = Host()
        sword = CallableSword()
        Equipped(agent, weapon=sword)
        self.assertIs(agent.weapon, sword)
        self.assertEqual(agent.weapon(), "held callable")
        self.assertIs(agent.false, False)
        self.assertTrue("false" @ agent)

    def test_type_policy_can_hold_a_tag_without_changing_its_population_truth(self):
        class Weapon(Tag):
            pass

        class Catalogued(Tag):
            @Tool(type)
            def tool(agent):
                return Weapon

        agent = Host()
        Catalogued(agent)
        self.assertIs(agent.tool, Weapon)
        self.assertFalse(bool(agent.tool))
        sword = Sword()
        Weapon(sword)
        self.assertTrue(bool(agent.tool))

    def test_tool_record_named_getattribute_does_not_replace_python_lookup(self):
        class Given(Tag):
            @Tool(Sword)
            def __getattribute__(agent, *, tool):
                return tool

            @Record
            def visible(agent):
                return "ordinary lookup"

        agent = Host()
        sword = Sword()
        Given(agent, tool=sword)
        self.assertIs(agent.__getattribute__, sword)
        self.assertEqual(agent.visible, "ordinary lookup")
        with self.assertRaises(TagCompositionError):
            agent.__getattribute__ = Shield()
        self.assertIs(agent.__getattribute__, sword)
        self.assertEqual(agent.visible, "ordinary lookup")
        bypassed = Shield()
        object.__setattr__(agent, "__getattribute__", bypassed)
        self.assertIs(agent.__getattribute__, bypassed)
        self.assertEqual(agent.visible, "ordinary lookup")

    def test_tool_record_named_del_preserves_finalization_and_field_removal(self):
        seen = []

        class FinalizedHost:
            def __del__(agent):
                seen.append("host finalizer")

        class Given(Tag):
            @Tool(Sword)
            def __del__(agent, *, tool):
                return tool

            @Rip
            def StandDown(agent):
                seen.append("Rip")

        agent = FinalizedHost()
        sword = Sword()
        Given(agent, tool=sword)
        self.assertIs(agent.__del__, sword)
        self.assertIn(agent, Given[:])
        reference = weakref.ref(agent)
        del agent
        gc.collect()
        self.assertIsNone(reference())
        self.assertEqual(list(Given[:]), [])
        self.assertEqual(seen, ["Rip", "host finalizer"])

    def test_tool_record_named_rmatmul_preserves_string_presence_queries(self):
        class Given(Tag):
            @Tool(Sword)
            def __rmatmul__(agent, *, tool):
                return tool

            @Record
            def visible(agent):
                return None

        agent = Host()
        sword = Sword()
        Given(agent, tool=sword)
        self.assertIs(agent.__rmatmul__, sword)
        self.assertTrue("__rmatmul__" @ agent)
        self.assertTrue("visible" @ agent)
        self.assertFalse("missing" @ agent)
        object.__setattr__(agent, "__rmatmul__", None)
        self.assertIsNone(agent.__rmatmul__)
        self.assertTrue("__rmatmul__" @ agent)
        self.assertTrue("visible" @ agent)
        self.assertFalse("missing" @ agent)

    def test_shared_tools_have_no_ownership_or_automatic_cleanup(self):
        class Equipped(Tag):
            @Tool(Sword)
            def weapon(agent, *, weapon):
                return weapon

        sword = Sword()
        first, second = Host(), Host()
        Equipped(first, weapon=sword)
        Equipped(second, weapon=sword)
        self.assertIs(first.weapon, second.weapon)
        del first.weapon
        del Equipped[first]
        self.assertIs(second.weapon, sword)
        self.assertIn(second, Equipped[:])

    def test_policy_is_per_agent_and_does_not_retain_held_values(self):
        class Armed(Tag):
            @Tool(Sword)
            def equipment(agent, *, equipment):
                return equipment

        class Shielded(Tag):
            @Tool(Shield)
            def equipment(agent, *, equipment):
                return equipment

        first, second = Host(), Host()
        sword, shield = Sword(), Shield()
        Armed(first, equipment=sword)
        Shielded(second, equipment=shield)
        with self.assertRaises(TagCompositionError):
            first.equipment = shield
        with self.assertRaises(TagCompositionError):
            second.equipment = sword
        self.assertIs(first.equipment, sword)
        self.assertIs(second.equipment, shield)
        first_ref, sword_ref = weakref.ref(first), weakref.ref(sword)
        del first, sword
        gc.collect()
        self.assertIsNone(first_ref())
        self.assertIsNone(sword_ref())
        self.assertIs(second.equipment, shield)

    def test_non_host_policies_are_named_declaration_failures(self):
        class Weapon(Tag):
            pass

        @Pin
        class Program(Tag):
            pass

        policies = (Tag, Weapon, Program, Weapon[:], Weapon | Program,
                    Weapon | Sword, Sword | Weapon,
                    None, type(None), 7, Sword())
        for policy in policies:
            with self.subTest(policy=policy):
                with self.assertRaisesRegex(TagDeclarationError, "weapon"):
                    def weapon(agent):
                        return None

                    type("Invalid", (Tag,), {"weapon": Tool(policy)(weapon)})

    def test_a_tool_requires_a_policy_and_bare_tool_cannot_become_an_action(self):
        with self.assertRaisesRegex(TagDeclarationError, r"Invalid\.weapon"):
            class Invalid(Tag):
                @Tool()
                def weapon(agent):
                    return Sword()

        with self.assertRaises(TagDeclarationError):
            class Bare(Tag):
                @Tool
                def weapon(agent):
                    return Sword()

    def test_custom_class_admission_errors_are_named_and_preserve_the_binding(self):
        failure = RuntimeError("class admission failed")

        class CheckedMeta(type):
            def __instancecheck__(kind, value):
                if getattr(value, "reject", False):
                    raise failure
                return isinstance(value, Sword)

        class Checked(metaclass=CheckedMeta):
            pass

        class Equipped(Tag):
            @Tool(Checked)
            def weapon(agent, *, weapon):
                return weapon

        rejected = Sword()
        rejected.reject = True
        agent = Host()
        with self.assertRaisesRegex(TagCompositionError, r"Equipped\.weapon") as caught:
            Equipped(agent, weapon=rejected)
        self.assertIs(caught.exception.__cause__, failure)
        self.assertFalse("weapon" @ agent)
        self.assertNotIn(agent, Equipped[:])
        original = Sword()
        Equipped(agent, weapon=original)
        with self.assertRaisesRegex(TagCompositionError, r"Equipped\.weapon") as caught:
            agent.weapon = rejected
        self.assertIs(caught.exception.__cause__, failure)
        self.assertIs(agent.weapon, original)

    def test_class_admission_interrupts_propagate_unchanged(self):
        interruption = KeyboardInterrupt("stop admission")

        class CheckedMeta(type):
            def __instancecheck__(kind, value):
                if getattr(value, "interrupt", False):
                    raise interruption
                return isinstance(value, Sword)

        class Checked(metaclass=CheckedMeta):
            pass

        class Equipped(Tag):
            @Tool(Checked)
            def weapon(agent, *, weapon):
                return weapon

        interrupted = Sword()
        interrupted.interrupt = True
        agent = Host()
        with self.assertRaises(KeyboardInterrupt) as caught:
            Equipped(agent, weapon=interrupted)
        self.assertIs(caught.exception, interruption)
        self.assertFalse("weapon" @ agent)
        self.assertNotIn(agent, Equipped[:])
        original = Sword()
        Equipped(agent, weapon=original)
        with self.assertRaises(KeyboardInterrupt) as caught:
            object.__setattr__(agent, "weapon", interrupted)
        self.assertIs(caught.exception, interruption)
        self.assertIs(agent.weapon, original)

    def test_typing_policies_are_refused_without_reserving_a_protocol_marker(self):
        class SwordProtocol(Protocol):
            def Swing(sword): ...

        @runtime_checkable
        class RuntimeSwordProtocol(Protocol):
            def Swing(sword): ...

        for policy in (Any, Protocol, SwordProtocol, RuntimeSwordProtocol):
            with self.subTest(policy=policy):
                with self.assertRaisesRegex(TagDeclarationError, r"Invalid\.weapon"):
                    def weapon(agent):
                        return Sword()

                    type("Invalid", (Tag,), {"weapon": Tool(policy)(weapon)})

        class MarkedHost:
            _is_protocol = True

        class Equipped(Tag):
            @Tool(MarkedHost)
            def weapon(agent, *, weapon):
                return weapon

        agent = Host()
        value = MarkedHost()
        Equipped(agent, weapon=value)
        self.assertIs(agent.weapon, value)

    def test_other_contribution_kinds_cannot_be_tools_in_either_order(self):
        for kind in (Action, Report, Operation, Pre, Post, Imprint, Rip, Delete):
            for outer_tool in (False, True):
                with self.subTest(kind=kind, outer_tool=outer_tool):
                    with self.assertRaisesRegex(TagDeclarationError, "weapon"):
                        def weapon(agent):
                            return Sword()

                        if outer_tool:
                            member = Tool(Sword)(kind(weapon))
                        else:
                            member = kind(Tool(Sword)(weapon))
                        type("Invalid", (Tag,), {"weapon": member})

    def test_tool_on_a_pin_is_a_named_declaration_failure(self):
        with self.assertRaisesRegex(TagDeclarationError, "weapon"):
            @Pin
            class Program(Tag):
                @Tool(Sword)
                def weapon(agent):
                    return Sword()

    def test_late_plain_binding_does_not_read_the_values_class_property(self):
        observed = []

        class Value:
            @property
            def __class__(value):
                observed.append("read")
                raise RuntimeError("a plain value must not be inspected")

        class Example(Tag):
            pass

        value = Value()
        Example.setting = value
        self.assertIs(Example.__dict__["setting"], value)
        self.assertEqual(observed, [])


if __name__ == "__main__":
    unittest.main()
