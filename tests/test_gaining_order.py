"""Each Gaining sees the Agent declarations established before it."""

import unittest

from TopKit import (Constant, Delete, Imprint, Pin, Post, Pre, Public,
                    Record, Report, Rip, Secret, Tag, TagCompositionError, Underlay)


class Host:
    pass


class GainingOrderTests(unittest.TestCase):
    def test_a_later_post_is_attached_only_at_its_declaration(self):
        class Given(Tag):
            @Record
            def before(agent):
                try:
                    return agent.Ready
                except AttributeError:
                    return "not established"

            @Post
            def Ready(agent):
                return True

            def Read_Ready(agent):
                return agent.Ready

            @Record
            def after(agent):
                return agent.Read_Ready()

        agent = Host()
        Given(agent)

        self.assertEqual(agent.before, "not established")
        self.assertIs(agent.after, True)

    def test_a_pre_gates_first_and_is_never_attached_as_a_gain(self):
        events = []

        class Given(Tag):
            @Record
            def before(agent):
                events.append("Record")
                try:
                    return agent.Allowed
                except AttributeError:
                    return "not established"

            @Pre
            def Allowed(agent):
                events.append("Pre")
                return True

            @Record
            def after(agent):
                try:
                    return agent.Allowed
                except AttributeError:
                    return "not established"

        agent = Host()
        Given(agent)

        self.assertEqual(events, ["Pre", "Record"])
        self.assertEqual(agent.before, "not established")
        self.assertEqual(agent.after, "not established")

    def test_a_delete_preserves_the_old_value_until_its_declaration(self):
        class Given(Tag):
            @Record
            def before(agent):
                return agent.resource

            @Delete
            def resource(agent): ...

            @Record
            def after(agent):
                return "resource" @ agent

        agent = Host()
        agent.resource = "host resource"
        Given(agent)

        self.assertEqual(agent.before, "host resource")
        self.assertIs(agent.after, False)
        with self.assertRaises(AttributeError):
            agent.resource

    def test_a_constant_post_is_visible_and_protected_before_later_training(self):
        blocked = []

        class Given(Tag):
            @Constant
            @Post
            def Ready(agent):
                return True

            def Read_Ready(agent):
                return agent.Ready

            @Record
            def after(agent):
                return agent.Read_Ready()

            @Imprint
            def Check(agent):
                try:
                    agent.Ready = False
                except TagCompositionError:
                    blocked.append("Ready")

        agent = Host()
        Given(agent)

        self.assertIs(agent.after, True)
        self.assertIs(agent.Ready, True)
        self.assertEqual(blocked, ["Ready"])

    def test_a_combined_pre_and_post_is_composed_once_at_its_declaration(self):
        calls = []

        class Before(Tag):
            @Pre
            @Post
            def Ready(agent):
                calls.append("base")
                return True

        class After(Before):
            @Pre
            @Post
            @Underlay
            def Ready(agent, prior):
                calls.append("shape")
                return prior()

            @Record
            def observed(agent):
                return agent.Ready

        agent = Host()
        Before(agent)
        calls.clear()
        After(agent)

        self.assertIs(agent.observed, True)
        self.assertEqual(calls, ["shape", "base"] * 3)

    def test_actions_and_records_become_visible_in_declaration_order(self):
        observations = []

        class Given(Tag):
            @Record
            def first(agent):
                observations.append(("first", "Calculate" @ agent))
                return 2

            def Calculate(agent):
                return agent.first * 3

            @Record
            def second(agent):
                observations.append(("second", "Calculate" @ agent))
                return agent.Calculate()

            def Describe(agent):
                return (agent.first, agent.second)

            @Record
            def third(agent):
                return agent.Describe()

        agent = Host()
        Given(agent)

        self.assertEqual(observations, [("first", False), ("second", True)])
        self.assertEqual(agent.third, (2, 6))

    def test_a_later_action_does_not_replace_an_earlier_visible_action_yet(self):
        class Before(Tag):
            def Say(agent):
                return "earlier Tag"

        class After(Before):
            @Record
            def before(agent):
                return agent.Say()

            def Say(agent):
                return "later Tag"

            @Record
            def after(agent):
                return agent.Say()

        agent = Host()
        After(agent)

        self.assertEqual((agent.before, agent.after), ("earlier Tag", "later Tag"))
        self.assertEqual(agent.Say(), "later Tag")

    def test_a_record_builder_reads_its_previous_binding_until_it_returns(self):
        observations = []

        class Given(Tag):
            @Record
            def total(agent, stored):
                observations.append((agent.total, stored))
                return stored + 1

            def Read(agent):
                return agent.total

            @Record
            def later(agent):
                return agent.Read()

        agent = Host()
        agent.total = 4
        Given(agent)

        self.assertEqual(observations, [(4, 4)])
        self.assertEqual((agent.total, agent.later), (5, 5))

    def test_an_earlier_secret_action_and_record_can_supply_later_values(self):
        class Given(Tag):
            @Secret
            def Hidden(agent):
                return 8

            @Secret
            @Record
            def hidden_value(agent):
                return agent.Hidden()

            @Record
            def visible(agent):
                return agent.hidden_value + agent.Hidden()

            def Read(agent):
                return agent.hidden_value

        agent = Host()
        Given(agent)

        self.assertEqual((agent.visible, agent.Read()), (16, 8))
        self.assertFalse("Hidden" @ agent)
        self.assertFalse("hidden_value" @ agent)
        with self.assertRaises(AttributeError):
            agent.Hidden

    def test_a_dunder_action_changes_behavior_only_after_its_declaration(self):
        class Sized:
            def __len__(agent):
                return 3

        class Given(Tag):
            @Record
            def before(agent):
                return len(agent)

            def __len__(agent):
                return 9

            @Record
            def after(agent):
                return len(agent)

        agent = Sized()
        Given(agent)

        self.assertEqual((agent.before, agent.after, len(agent)), (3, 9, 9))

    def test_a_record_replacing_a_published_report_is_visible_to_the_next_builder(self):
        class Before(Tag):
            @Public
            @Report
            def value(tag):
                return 7

        class After(Before):
            @Record
            def value(agent):
                return agent.value + 1

            @Record
            def later(agent):
                return agent.value

        agent = Host()
        After(agent)

        self.assertEqual((agent.value, agent.later), (8, 8))

    def test_an_action_replacing_a_published_report_is_visible_to_the_next_builder(self):
        class Before(Tag):
            @Public
            @Report
            def value(tag):
                return 7

        class After(Before):
            def value(agent):
                return 14

            @Record
            def later(agent):
                return agent.value()

        agent = Host()
        After(agent)

        self.assertEqual((agent.value(), agent.later), (14, 14))

    def test_earlier_constants_are_available_and_locked_before_imprints(self):
        blocked = []

        class Given(Tag):
            @Constant
            def Fixed(agent):
                return 7

            @Constant
            @Record
            def fixed_value(agent):
                return agent.Fixed()

            @Record
            def later(agent):
                return agent.fixed_value + agent.Fixed()

            @Imprint
            def Check(agent):
                for name in ("Fixed", "fixed_value"):
                    try:
                        setattr(agent, name, None)
                    except TagCompositionError:
                        blocked.append(name)

        agent = Host()
        Given(agent)

        self.assertEqual(agent.later, 14)
        self.assertEqual(blocked, ["Fixed", "fixed_value"])
        self.assertEqual(agent.Fixed(), 7)
        self.assertEqual(agent.fixed_value, 7)

    def test_retained_constants_do_not_disrupt_the_remaining_gaining_order(self):
        builds = []

        class Given(Tag):
            @Constant
            @Record
            def token(agent):
                builds.append("token")
                return object()

            @Constant
            def Read(agent):
                return agent.token

            @Record
            def round(agent, stored):
                return (stored or 0) + 1

        agent = Host()
        Given(agent)
        token = agent.token
        del Given[agent]
        Given(agent)

        self.assertIs(agent.token, token)
        self.assertIs(agent.Read(), token)
        self.assertEqual((agent.round, builds), (2, ["token"]))

    def test_a_pin_exposes_earlier_gains_to_its_later_builders(self):
        class Library(Tag):
            @Report
            def initial(tag):
                return 4

        class Given(Pin):
            @Record
            def first(tag):
                return tag.initial

            def Calculate(tag):
                return tag.first * 2

            @Record
            def second(tag):
                return tag.Calculate()

        Given(Library)

        self.assertEqual((Library.first, Library.second), (4, 8))
        self.assertEqual(Library.Calculate(), 8)

    def test_all_rip_actions_are_registered_after_ordered_gains(self):
        released = []

        class Given(Tag):
            @Rip
            def First(agent):
                released.append("first")

            @Record
            def middle(agent):
                return "First" @ agent

            @Rip
            def Last(agent):
                released.append("last")

        agent = Host()
        Given(agent)
        self.assertTrue(agent.middle)
        del Given[agent]

        self.assertEqual(released, ["first", "last"])


if __name__ == "__main__":
    unittest.main()
