"""Tool admission follows ordered Gainings and keeps acquired Rogue state."""

import unittest

from TopKit import (Action, Contract, Imprint, Post, Record, Tag, Tool,
                    TagCompositionError, TagImprintError)


class Host:
    pass


class Sword:
    pass


class Shield:
    pass


class ToolAdmissionTests(unittest.TestCase):
    def test_rejected_tool_runtime_leaves_earlier_gains_without_an_unguarded_tool(self):
        class HostType(type):
            def __new__(meta, name, bases, namespace):
                if "weapon" in namespace:
                    raise TypeError("Tool descriptor refused")
                return super().__new__(meta, name, bases, namespace)

        class Bearer(metaclass=HostType):
            pass

        class Equipped(Tag):
            @Record
            def earlier(agent):
                return False

            @Tool(Sword)
            def weapon(agent):
                return Sword()

        agent = Bearer()
        with self.assertRaises(TagCompositionError):
            Equipped(agent)
        self.assertNotIn(agent, Equipped[:])
        self.assertIs(agent.earlier, False)
        self.assertFalse("weapon" @ agent)
        agent.weapon = "ordinary host binding"
        self.assertEqual(agent.weapon, "ordinary host binding")

    def test_rejected_tool_rule_removal_keeps_previous_value_and_policy(self):
        class HostType(type):
            reject = False

            def __new__(meta, name, bases, namespace):
                if meta.reject and "__len__" in namespace and "weapon" not in namespace:
                    raise TypeError("Tool removal refused")
                return super().__new__(meta, name, bases, namespace)

        class Bearer(metaclass=HostType):
            pass

        class Equipped(Tag):
            @Tool(Sword)
            def weapon(agent, *, weapon):
                return weapon

        class Ordinary(Equipped):
            @Action
            def __len__(agent):
                return 7

            @Record
            def weapon(agent, stored):
                return None

        agent = Bearer()
        original = Sword()
        Equipped(agent, weapon=original)
        HostType.reject = True
        with self.assertRaises(TagCompositionError):
            Ordinary(agent)
        self.assertIn(agent, Equipped[:])
        self.assertNotIn(agent, Ordinary[:])
        self.assertEqual(len(agent), 7)
        self.assertIs(agent.weapon, original)
        with self.assertRaises(TagCompositionError):
            object.__setattr__(agent, "weapon", Shield())
        self.assertIs(agent.weapon, original)
        HostType.reject = False
        Ordinary(agent)
        self.assertIn(agent, Ordinary[:])
        self.assertIsNone(agent.weapon)
        agent.weapon = Shield()
        self.assertIsInstance(agent.weapon, Shield)

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
