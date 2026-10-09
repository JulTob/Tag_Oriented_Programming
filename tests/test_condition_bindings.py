"""Computed conditions remain conditions instead of writable attributes."""

import unittest

from TopKit import (Constant, Contract, Pin, Post, Pre, Record, Secret, Tag,
                    TagCompositionError, TagResolutionError, Underlay)


class Host:
    pass


class ConditionBindingTests(unittest.TestCase):
    def test_a_visible_condition_refuses_assignment_and_deletion(self):
        class Qualified(Tag):
            @Post
            def Ready(agent):
                return agent.ready

        agent = Host()
        agent.ready = True
        Qualified(agent)

        self.assertIs(agent.Ready, True)
        self.assertFalse("Ready" @ agent)
        with self.assertRaises(TagCompositionError):
            agent.Ready = False
        with self.assertRaises(TagCompositionError):
            del agent.Ready
        self.assertIs(agent.Ready, True)
        self.assertTrue(Contract.Holds(agent))

    def test_ordinary_attribute_behavior_returns_after_contract_delete(self):
        class Qualified(Tag):
            @Post
            def Ready(agent):
                return True

        agent = Host()
        Qualified(agent)
        Contract.Delete(agent, "Ready")

        agent.Ready = False
        self.assertIs(agent.Ready, False)
        self.assertTrue("Ready" @ agent)
        del agent.Ready
        self.assertFalse("Ready" @ agent)
        with self.assertRaises(AttributeError):
            agent.Ready

    def test_contract_delete_preflights_names_and_keeps_contract_truth(self):
        class Empty_Host:
            def __len__(agent):
                return 0

        class Qualified(Tag):
            @Post
            def Ready(agent):
                return True

        agent = Empty_Host()
        Qualified(agent)
        guarded_type = type(agent)
        self.assertTrue(agent)

        with self.assertRaises(TagResolutionError):
            Contract.Delete(agent, "Ready", "Missing")

        self.assertEqual(Contract.Status(agent), {"Ready": True})
        self.assertIs(type(agent), guarded_type)
        self.assertTrue(agent)

        Contract.Delete(agent, "Ready")
        self.assertEqual(Contract.Status(agent), {})
        self.assertIsNot(type(agent), guarded_type)
        self.assertEqual(len(agent), 0)
        self.assertTrue(agent)  # no visible Post is broken

    def test_host_write_hooks_are_refused_before_their_effects(self):
        writes = []

        class Custom_Host:
            def __setattr__(agent, name, value):
                writes.append(("set", name))
                agent.__dict__[name] = value

            def __delattr__(agent, name):
                writes.append(("delete", name))
                del agent.__dict__[name]

        class Qualified(Tag):
            @Post
            def Ready(agent):
                return agent.ready

        agent = Custom_Host()
        agent.ready = True
        Qualified(agent)
        writes.clear()

        with self.assertRaises(TagCompositionError):
            agent.Ready = False
        with self.assertRaises(TagCompositionError):
            del agent.Ready
        self.assertEqual(writes, [])

        agent.ordinary = 1
        del agent.ordinary
        self.assertEqual(writes, [("set", "ordinary"), ("delete", "ordinary")])

        Contract.Delete(agent, "Ready")
        agent.Ready = "ordinary again"
        del agent.Ready
        self.assertEqual(
                writes[-2:],
                [("set", "Ready"), ("delete", "Ready")],
                )

    def test_object_write_methods_cannot_bypass_a_condition(self):
        class Qualified(Tag):
            @Post
            def Ready(agent):
                return True

        agent = Host()
        Qualified(agent)

        with self.assertRaises(TagCompositionError):
            object.__setattr__(agent, "Ready", False)
        with self.assertRaises(TagCompositionError):
            object.__delattr__(agent, "Ready")

        Contract.Delete(agent, "Ready")
        object.__setattr__(agent, "Ready", False)
        self.assertIs(agent.Ready, False)
        object.__delattr__(agent, "Ready")

    def test_a_precondition_added_to_an_existing_agent_gets_the_same_gate(self):
        class Marked(Tag):
            pass

        class Admitted(Tag):
            @Pre
            def Ready(agent):
                return agent.ready

        agent = Host()
        agent.ready = True
        Marked(agent)
        Admitted(agent)

        self.assertIs(agent.Ready, True)
        with self.assertRaises(TagCompositionError):
            agent.Ready = False
        with self.assertRaises(TagCompositionError):
            del agent.Ready

    def test_runtime_types_are_keyed_by_their_condition_names(self):
        class With_Ready(Tag):
            @Post
            def Ready(agent):
                return True

        class With_Focus(Tag):
            @Post
            def Focus(agent):
                return True

        ready = Host()
        focused = Host()
        With_Ready(ready)
        With_Focus(focused)

        self.assertIsNot(type(ready), type(focused))
        with self.assertRaises(TagCompositionError):
            ready.Ready = False
        with self.assertRaises(TagCompositionError):
            focused.Focus = False
        ready.Focus = "ordinary"
        focused.Ready = "ordinary"
        self.assertEqual((ready.Focus, focused.Ready), ("ordinary", "ordinary"))

    def test_secret_and_underlaid_conditions_keep_their_read_behavior(self):
        class Sealed(Tag):
            @Secret
            @Record
            def code(agent):
                return "swordfish"

            @Post
            def Ready(agent):
                return agent.code == "swordfish"

        class Strengthened(Sealed):
            @Post
            @Underlay
            def Ready(agent, prior):
                return prior() and agent.code.startswith("sword")

        agent = Host()
        Sealed(agent)
        Strengthened(agent)

        self.assertIs(agent.Ready, True)
        with self.assertRaises(AttributeError):
            agent.code
        with self.assertRaises(TagCompositionError):
            agent.Ready = False
        with self.assertRaises(TagCompositionError):
            del agent.Ready

    def test_pinned_tag_conditions_are_read_only_until_ended(self):
        class Guild(Tag):
            pass

        @Pin
        class Governed(Tag):
            @Constant
            @Record
            def token(tag):
                return "fixed"

            @Post
            def Ready(tag):
                return tag.token == "fixed"

        Governed(Guild)
        self.assertIs(Guild.Ready, True)
        with self.assertRaises(TagCompositionError):
            Guild.Ready = False
        with self.assertRaises(TagCompositionError):
            del Guild.Ready

        Contract.Delete(Guild, "Ready")
        Guild.Ready = False
        self.assertIs(Guild.Ready, False)
        del Guild.Ready
        with self.assertRaises(TagCompositionError):
            Guild.token = "changed"
        self.assertEqual(Guild.token, "fixed")

    def test_condition_and_constant_guards_keep_their_own_lifetimes(self):
        class Guarded(Tag):
            @Constant
            @Record
            def token(agent):
                return "fixed"

            @Constant
            @Post
            def Fixed(agent):
                return agent.token == "fixed"

            @Post
            def Temporary(agent):
                return True

        agent = Host()
        Guarded(agent)

        for name in ("Fixed", "Temporary"):
            with self.subTest(name=name):
                with self.assertRaises(TagCompositionError):
                    setattr(agent, name, False)
                with self.assertRaises(TagCompositionError):
                    delattr(agent, name)

        Contract.Delete(agent, "Temporary")
        agent.Temporary = False
        self.assertIs(agent.Temporary, False)
        with self.assertRaises(TagCompositionError):
            Contract.Delete(agent, "Fixed")
        with self.assertRaises(TagCompositionError):
            agent.token = "changed"
        self.assertEqual(agent.token, "fixed")


if __name__ == "__main__":
    unittest.main()
