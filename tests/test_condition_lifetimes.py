"""The three condition lifetimes: Service, membership Gain, lifetime term."""

import unittest

from TopKit import (Constant, Contract, Post, Pre, Record, Rip, Tag,
                    TagCompositionError, TagContractWarning,
                    TagPreconditionError, Underlay)


class Host:
    pass


class ConditionLifetimeTests(unittest.TestCase):
    def test_pre_is_a_transient_tagging_service_not_an_agent_member(self):
        checks = []

        class Qualified(Tag):
            @Pre
            def Invited(target):
                checks.append(target.invited)
                return target.invited

        refused = Host()
        refused.invited = False
        with self.assertRaises(TagPreconditionError.Invited):
            Qualified(refused)
        self.assertEqual(Contract.Status(refused), {})
        self.assertFalse(hasattr(refused, "Invited"))

        agent = Host()
        agent.invited = True
        Qualified(agent)
        self.assertEqual(checks, [False, True])
        self.assertEqual(Contract.Status(agent), {})
        self.assertFalse(hasattr(agent, "Invited"))
        agent.Invited = "ordinary host value"
        self.assertEqual(agent.Invited, "ordinary host value")

        del Qualified[agent]
        agent.invited = False
        with self.assertRaises(TagPreconditionError.Invited):
            Qualified(agent)

    def test_pre_underlay_is_local_to_the_current_form(self):
        calls = []

        class Base(Tag):
            @Pre
            def Ready(target):
                calls.append("Base")
                return True

        class Shape(Base):
            @Pre
            @Underlay
            def Ready(target, prior):
                calls.append("Shape")
                return prior()

        agent = Host()
        Shape(agent)
        self.assertEqual(calls, ["Base", "Shape", "Base"])
        self.assertFalse(hasattr(agent, "Ready"))

        class Independent(Tag):
            @Pre
            @Underlay
            def Ready(target, prior):
                return prior()

        with self.assertRaisesRegex(Exception, "no prior condition"):
            Independent(agent)

    def test_stacked_pre_and_post_have_independent_lifetimes(self):
        class Guild(Tag):
            @Pre
            @Post
            def Keeps_Oath(agent):
                return agent.keeps_oath

        agent = Host()
        agent.keeps_oath = True
        Guild(agent)
        self.assertEqual(Contract.Status(agent), {"Keeps_Oath": True})
        agent.keeps_oath = False
        self.assertFalse(agent.Keeps_Oath)

        del Guild[agent]
        self.assertEqual(Contract.Status(agent), {})
        self.assertFalse(hasattr(agent, "Keeps_Oath"))

    def test_top_rip_reveals_lower_post_and_last_rip_ends_the_name(self):
        class Base(Tag):
            @Post
            def Ready(agent):
                return agent.ready

        class Later(Tag):
            @Post
            def Ready(agent):
                return True

        agent = Host()
        agent.ready = True
        Base(agent)
        with self.assertWarns(TagContractWarning):
            Later(agent)
        agent.ready = False
        self.assertTrue(agent.Ready)

        del Later[agent]
        self.assertFalse(agent.Ready)
        self.assertEqual(Contract.Status(agent), {"Ready": False})

        del Base[agent]
        self.assertEqual(Contract.Status(agent), {})
        with self.assertRaises(AttributeError):
            agent.Ready

    def test_middle_rip_reconnects_surviving_post_underlay(self):
        called = []

        class Base(Tag):
            @Post
            def Ready(agent):
                called.append("Base")
                return True

        class Middle(Tag):
            @Post
            @Underlay
            def Ready(agent, prior):
                called.append("Middle")
                return prior()

        class Top(Tag):
            @Post
            @Underlay
            def Ready(agent, prior):
                called.append("Top")
                return prior()

        agent = Host()
        Base(agent)
        Middle(agent)
        Top(agent)
        called.clear()
        self.assertTrue(agent.Ready)
        self.assertEqual(called, ["Top", "Middle", "Base"])

        del Middle[agent]
        called.clear()
        self.assertTrue(agent.Ready)
        self.assertEqual(called, ["Top", "Base"])

        del Base[agent]
        called.clear()
        self.assertTrue(agent.Ready)
        self.assertEqual(called, ["Top"])

    def test_posts_are_discarded_when_the_attempt_never_enters_the_field(self):
        for constant in (False, True):
            with self.subTest(constant=constant):
                def Ready(agent):
                    return True

                if constant:
                    Ready = Constant(Ready)

                Broken = type(
                        "Broken",
                        (Tag,),
                        {
                            "Ready": Post(Ready),
                            "value": Record(lambda agent: (_ for _ in ()).throw(
                                RuntimeError("no value"))),
                            },
                        )
                agent = Host()
                with self.assertRaises(TagCompositionError):
                    Broken(agent)
                self.assertNotIn(agent, Broken[:])
                self.assertEqual(Contract.Status(agent), {})
                self.assertFalse(hasattr(agent, "Ready"))

    def test_failed_constant_attempt_restores_a_same_named_ordinary_post_gate(self):
        class Base(Tag):
            @Post
            def Ready(agent):
                return agent.ready

        class Failed(Tag):
            @Constant
            @Post
            def Ready(agent):
                return True

            @Record
            def value(agent):
                raise RuntimeError("no value")

        agent = Host()
        agent.ready = True
        Base(agent)

        with self.assertWarns(TagContractWarning):
            with self.assertRaises(TagCompositionError):
                Failed(agent)

        self.assertTrue(agent.Ready)
        with self.assertRaises(TagCompositionError):
            agent.Ready = False
        with self.assertRaises(TagCompositionError):
            del agent.Ready

    def test_field_removal_ends_post_before_even_a_failed_teardown(self):
        observed = []

        class Car(Tag):
            @Post
            def Ready(agent):
                return True

            @Rip
            def Fail(agent):
                observed.append(Contract.Status(agent))
                raise RuntimeError("cleanup failed")

        agent = Host()
        Car(agent)
        with self.assertRaises(TagCompositionError):
            del Car[agent]
        self.assertEqual(observed, [{}])
        self.assertNotIn(agent, Car[:])
        self.assertEqual(Contract.Status(agent), {})

    def test_old_rip_does_not_remove_a_fresh_same_tag_application(self):
        class Car(Tag):
            @Post
            def Ready(agent):
                return agent in Car[:]

            @Rip
            def Rejoin(agent):
                Car(agent)

        agent = Host()
        Car(agent)
        del Car[agent]
        self.assertIn(agent, Car[:])
        self.assertEqual(Contract.Status(agent), {"Ready": True})

    def test_constant_post_stays_for_the_agents_lifetime_after_admission(self):
        class Employer(Tag):
            @Constant
            @Post
            def NDA(agent):
                return agent.keeps_secret

        agent = Host()
        agent.keeps_secret = True
        Employer(agent)
        del Employer[agent]
        self.assertEqual(Contract.Status(agent), {"NDA": True})
        agent.keeps_secret = False
        self.assertFalse(bool(agent))
        self.assertFalse(agent.NDA)

    def test_one_application_can_end_ordinary_posts_and_keep_its_constant(self):
        class Employer(Tag):
            @Constant
            @Post
            def NDA(agent):
                return agent.keeps_secret

            @Post
            def On_Duty(agent):
                return agent.working

        agent = Host()
        agent.keeps_secret = True
        agent.working = True
        Employer(agent)
        del Employer[agent]
        self.assertEqual(Contract.Status(agent), {"NDA": True})
        self.assertFalse(hasattr(agent, "On_Duty"))

    def test_old_rip_deletion_is_idempotent_after_automatic_post_end(self):
        class Guild(Tag):
            @Post
            def Ready(agent):
                return True

            @Rip
            def End_Old_Style(agent):
                Contract.Delete(agent, "Ready")

        agent = Host()
        Guild(agent)
        del Guild[agent]
        Contract.Delete(agent, "Ready")
        self.assertEqual(Contract.Status(agent), {})

    def test_pre_history_is_not_a_contract_api(self):
        self.assertFalse(hasattr(Contract, "Preconditions"))
        self.assertFalse(hasattr(Contract, "Conditions"))


if __name__ == "__main__":
    unittest.main()
