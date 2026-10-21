"""Admission follows Gainings and Imprints; unfinished training leaves Gains."""

import gc
import unittest
import weakref

from TopKit import (Action, Constant, Contract, Flag, Imprint, Keyword,
                    Operation, Pin, Post, Pre, Public, Record, Report, Rip, Tag,
                    TagCompositionError, TagContractWarning, TagImprintError,
                    TagPostconditionError, TagPreconditionError,
                    TagResolutionError, Secret)


class Host:
    pass


class Stop(BaseException):
    pass


class TaggingAdmissionTests(unittest.TestCase):
    def assert_not_admitted(self, tag, agent):
        self.assertNotIn(agent, tag)
        self.assertNotIn(agent, tag[:])
        self.assertFalse(isinstance(agent, tag))
        with self.assertRaises(TagResolutionError):
            tag[agent]

    def test_imprints_have_gains_but_no_membership_view_or_published_services(self):
        events = []

        class Assembled(Tag):
            @Record
            def value(agent):
                return None

            @Action
            def Read(agent):
                return agent.value

            @Public
            @Report
            def status(tag):
                return "assembled"

            @Public
            @Operation
            def Identify(tag, agent):
                return tag.__name__

            @Imprint
            def Assemble(agent):
                self.assert_not_admitted(Assembled, agent)
                self.assertTrue("value" @ agent)
                self.assertTrue("Read" @ agent)
                self.assertIsNone(agent.Read())
                with self.assertRaises((AttributeError, TagResolutionError)):
                    agent.status
                with self.assertRaises((AttributeError, TagResolutionError)):
                    agent.Identify()
                events.append("imprint")

            @Post
            def Admitted(agent):
                events.append("post")
                return agent in Assembled[:]

        agent = Host()
        self.assertIs(Assembled(agent), agent)
        self.assertEqual(events, ["imprint", "post"])
        self.assertIn(agent, Assembled[:])
        self.assertTrue(isinstance(agent, Assembled))
        self.assertIsNone(Assembled[agent].Read())
        self.assertEqual(agent.status, "assembled")
        self.assertEqual(agent.Identify(), "Assembled")

    def test_failed_record_retains_only_gains_that_were_acquired(self):
        class Unfinished(Tag):
            @Action
            def Read(agent):
                return agent.value

            @Record
            def value(agent):
                return False

            @Record
            def missing(agent):
                raise ValueError("builder failed")

            @Record
            def later(agent):
                return "not reached"

        agent = Host()
        with self.assertRaisesRegex(TagCompositionError, "builder failed"):
            Unfinished(agent)
        self.assert_not_admitted(Unfinished, agent)
        self.assertTrue("Read" @ agent)
        self.assertTrue("value" @ agent)
        self.assertIs(agent.Read(), False)
        self.assertFalse("missing" @ agent)
        self.assertFalse("later" @ agent)

    def test_interrupted_builder_preserves_earlier_gains_and_its_previous_value(self):
        failure = KeyboardInterrupt()

        class Unfinished(Tag):
            @Action
            def Read(agent):
                return agent.value

            @Record
            def value(agent, stored):
                self.assertIsNone(stored)
                raise failure

        agent = Host()
        agent.value = None
        with self.assertRaises(KeyboardInterrupt) as caught:
            Unfinished(agent)
        self.assertIs(caught.exception, failure)
        self.assert_not_admitted(Unfinished, agent)
        self.assertTrue("Read" @ agent)
        self.assertTrue("value" @ agent)
        self.assertIsNone(agent.Read())

    def test_predecessor_published_services_remain_available_until_field_entry(self):
        class Existing(Tag):
            @Public
            @Report
            def status(tag):
                return "existing"

            @Public
            @Operation
            def Identify(tag, agent):
                return "existing"

        class New(Tag):
            @Public
            @Report
            def status(tag):
                return "new"

            @Public
            @Operation
            def Identify(tag, agent):
                return "new"

            @Imprint
            def Train(agent):
                self.assertEqual(agent.status, "existing")
                self.assertEqual(agent.Identify(), "existing")
                self.assertIn(agent, Existing[:])
                self.assert_not_admitted(New, agent)

        agent = Host()
        Existing(agent)
        New(agent)
        self.assertEqual(agent.status, "new")
        self.assertEqual(agent.Identify(), "new")
        self.assertIn(agent, Existing[:])
        self.assertIn(agent, New[:])

    def test_failed_imprint_and_interruptions_leave_gains_outside_the_tag(self):
        for failure in (ValueError("failed"), KeyboardInterrupt(),
                        SystemExit(7), Stop()):
            with self.subTest(failure=type(failure).__name__):
                events = []

                class Unfinished(Tag):
                    @Record
                    def value(agent):
                        return None

                    @Action
                    def Read(agent):
                        return agent.value

                    @Imprint
                    def Acquire(agent):
                        events.append("acquire")

                    @Imprint
                    def Finish(agent):
                        raise failure

                    @Imprint
                    def Later(agent):
                        events.append("not reached")

                agent = Host()
                expected = TagImprintError.Finish if isinstance(failure, Exception) else type(failure)
                with self.assertRaises(expected) as caught:
                    Unfinished(agent)
                if isinstance(failure, Exception):
                    self.assertIs(caught.exception.__cause__, failure)
                else:
                    self.assertIs(caught.exception, failure)
                self.assert_not_admitted(Unfinished, agent)
                self.assertTrue("Read" @ agent)
                self.assertTrue("value" @ agent)
                self.assertIsNone(agent.Read())
                self.assertEqual(events, ["acquire"])

    def test_retry_runs_a_fresh_gate_gainings_and_all_imprints(self):
        events = []

        class Retried(Tag):
            @Pre
            def Allowed(agent):
                events.append(("gate", agent.round))
                return True

            @Record
            def round(agent, stored):
                return (stored or 0) + 1

            @Imprint
            def First(agent):
                events.append(("first", agent.round))

            @Imprint
            def Finish(agent):
                events.append(("finish", agent.round))
                if agent.round == 1:
                    raise ValueError("retry needed")

        agent = Host()
        agent.round = 0
        with self.assertRaises(TagImprintError.Finish):
            Retried(agent)
        self.assert_not_admitted(Retried, agent)
        self.assertEqual(agent.round, 1)
        self.assertIs(Retried(agent), agent)
        self.assertEqual(agent.round, 2)
        self.assertIn(agent, Retried[:])
        self.assertEqual(events, [("gate", 0), ("first", 1), ("finish", 1),
                                  ("gate", 1), ("first", 2), ("finish", 2)])

    def test_a_refused_retry_keeps_the_rogues_existing_gains(self):
        class Retried(Tag):
            @Pre
            def Allowed(agent):
                return agent.allowed

            @Record
            def value(agent, stored):
                return (stored or 0) + 1

            @Imprint
            def Finish(agent):
                raise ValueError("unfinished")

        agent = Host()
        agent.allowed = True
        with self.assertRaises(TagImprintError.Finish):
            Retried(agent)
        agent.allowed = False
        with self.assertRaises(TagPreconditionError.Allowed):
            Retried(agent)
        self.assert_not_admitted(Retried, agent)
        self.assertEqual(agent.value, 1)

    def test_acquired_constants_stay_locked_but_an_unbuilt_constant_can_retry(self):
        builds = []

        class Retried(Tag):
            @Constant
            @Record
            def token(agent):
                builds.append("token")
                return object()

            @Constant
            @Record
            def value(agent):
                builds.append("value")
                if builds.count("value") == 1:
                    raise ValueError("not built")
                return None

        agent = Host()
        with self.assertRaisesRegex(TagCompositionError, "not built"):
            Retried(agent)
        self.assert_not_admitted(Retried, agent)
        token = agent.token
        self.assertTrue("token" @ agent)
        self.assertFalse("value" @ agent)
        with self.assertRaises(TagCompositionError):
            agent.token = None
        with self.assertRaises(TagCompositionError):
            del agent.token
        Retried(agent)
        self.assertIs(agent.token, token)
        self.assertIsNone(agent.value)
        self.assertTrue("value" @ agent)
        self.assertEqual(builds, ["token", "value", "value"])
        with self.assertRaises(TagCompositionError):
            agent.value = 1
        with self.assertRaises(TagCompositionError):
            del agent.value

    def test_self_tagging_is_a_noop_but_a_shape_needing_training_base_is_refused(self):
        events = []

        class Base(Tag):
            @Pre
            def Allowed(agent):
                events.append("gate")
                return True

            @Record
            def value(agent):
                events.append("gain")
                return 1

            @Imprint
            def Train(agent):
                events.append("imprint")
                self.assertIs(Base(agent), agent)
                self.assert_not_admitted(Base, agent)
                with self.assertRaises(TagCompositionError):
                    Shape(agent)

        class Shape(Base):
            @Record
            def later(agent):
                return "not reached"

        agent = Host()
        Base(agent)
        self.assertEqual(events, ["gate", "gain", "imprint"])
        self.assertIn(agent, Base[:])
        self.assert_not_admitted(Shape, agent)
        self.assertFalse("later" @ agent)

    def test_a_completed_base_survives_a_shapes_failed_builder_or_imprint(self):
        for phase in ("gain", "imprint"):
            with self.subTest(phase=phase):
                class Base(Tag):
                    @Record
                    def base_value(agent):
                        return "base"

                class Shape(Base):
                    @Record
                    def partial(agent):
                        return None

                    @Record
                    def next_value(agent):
                        if phase == "gain":
                            raise ValueError("gain failed")
                        return False

                    @Imprint
                    def Finish(agent):
                        raise ValueError("imprint failed")

                agent = Host()
                expected = TagCompositionError if phase == "gain" else TagImprintError.Finish
                with self.assertRaises(expected):
                    Shape(agent)
                self.assertIn(agent, Base[:])
                self.assertTrue(isinstance(agent, Base))
                self.assertEqual(Base[agent].base_value, "base")
                self.assert_not_admitted(Shape, agent)
                self.assertTrue("partial" @ agent)
                self.assertIsNone(agent.partial)

    def test_nested_tagging_survives_the_outer_imprints_failure(self):
        class Inner(Tag):
            @Record
            def inner_value(agent):
                return None

        class Outer(Tag):
            @Record
            def outer_value(agent):
                return False

            @Imprint
            def Finish(agent):
                Inner(agent)
                raise ValueError("outer failed")

        agent = Host()
        with self.assertRaises(TagImprintError.Finish):
            Outer(agent)
        self.assertIn(agent, Inner[:])
        self.assertTrue(isinstance(agent, Inner))
        self.assertIsNone(Inner[agent].inner_value)
        self.assert_not_admitted(Outer, agent)
        self.assertTrue("outer_value" @ agent)
        self.assertIs(agent.outer_value, False)

    def test_unadmitted_safety_post_ends_but_sticky_actions_fail_closed(self):
        class Existing(Tag):
            @Public
            @Operation
            def Use(agent_tag, agent):
                return "existing service"

        class Safe(Tag):
            @Pre
            def Can_Train(agent):
                return agent.can_train

            @Record
            def insulated(agent):
                return True

            @Post
            def SafetyChecks(agent):
                return agent.insulated

        class Electric(Tag):
            @Record
            def before_safety(agent):
                self.assertNotIn("SafetyChecks", Contract.Status(agent))
                return None

            @Post
            def SafetyChecks(agent):
                return agent.insulated

            @Action
            def TurnOnBattery(agent):
                if not agent.SafetyChecks:
                    raise AssertionError("SafetyChecks")
                agent.battery_on = True

            @Action
            def ReadBattery(agent):
                return agent.battery_on

            @Record
            def after_safety(agent):
                self.assertIs(agent.SafetyChecks, False)
                self.assertIs(agent.ReadBattery(), False)
                return None

            @Imprint
            def Train(agent):
                Safe(agent)

        agent = Host()
        agent.can_train = False
        agent.insulated = False
        agent.battery_on = False
        Existing(agent)
        self.assertEqual(agent.Use(), "existing service")

        with self.assertRaises(TagImprintError.Train) as caught:
            Electric(agent)
        self.assertIsInstance(caught.exception.__cause__, TagPreconditionError.Can_Train)
        self.assert_not_admitted(Electric, agent)
        self.assert_not_admitted(Safe, agent)
        self.assertTrue("before_safety" @ agent)
        self.assertTrue("after_safety" @ agent)
        self.assertFalse(hasattr(agent, "SafetyChecks"))
        self.assertTrue(bool(agent))
        self.assertIn(agent, Existing[:])
        self.assertIn(agent, list(Existing))
        self.assertNotIn(agent, ~Existing)
        self.assertEqual(agent.Use(), "existing service")
        with self.assertRaises(AttributeError):
            agent.TurnOnBattery()
        # Ordinary Actions can still read the Rogue's state. Performative
        # Actions establish their own guards, as TurnOnBattery does above.
        self.assertIs(agent.ReadBattery(), False)
        self.assertIs(agent.battery_on, False)

        agent.can_train = True
        Safe(agent)
        self.assertTrue(agent.insulated)
        self.assertIs(agent.SafetyChecks, True)
        self.assertTrue(bool(agent))
        self.assertIn(agent, list(Existing))
        self.assertEqual(agent.Use(), "existing service")
        self.assert_not_admitted(Electric, agent)
        agent.TurnOnBattery()
        self.assertIs(agent.ReadBattery(), True)

    def test_a_failed_pin_keeps_direct_gains_with_tag_scope_for_future_agents(self):
        class Receiver(Tag):
            @Operation
            def Work(tag):
                return "declared operation"

        # Apply first so the receiver's declarations have already been used.
        # A Pin's acquired Action is an Operation on its receiving Tag.
        existing = Host()
        Receiver(existing)
        self.assertEqual(Receiver.Work(), "declared operation")
        self.assertFalse("Work" @ existing)

        @Pin
        class Unfinished(Tag):
            @Action
            def Work(tag):
                return "pinned operation"

            @Record
            def marker(tag):
                return False

            @Imprint
            def Finish(tag):
                raise ValueError("unfinished Pin")

        with self.assertRaises(TagImprintError.Finish):
            Unfinished(Receiver)
        self.assert_not_admitted(Unfinished, Receiver)
        self.assertTrue("Work" @ Receiver)
        self.assertTrue("marker" @ Receiver)
        self.assertEqual(Receiver.Work(), "pinned operation")
        self.assertIs(Receiver.marker, False)
        self.assertFalse("Work" @ existing)

        future = Host()
        Receiver(future)
        self.assertIn(future, Receiver[:])
        self.assertFalse("Work" @ future)
        self.assertFalse("marker" @ future)

    def test_posts_run_after_the_whole_form_and_failure_means_deficient_membership(self):
        checks = []

        class Base(Tag):
            @Post
            def Has_Shape_Gain(agent):
                checks.append("base post")
                return "ready" @ agent

        class Shape(Base):
            @Record
            def ready(agent):
                return False

            @Post
            def Works(agent):
                checks.append("shape post")
                return agent.ready

        agent = Host()
        with self.assertRaises(TagPostconditionError.Works):
            Shape(agent)
        self.assertEqual(checks, ["base post", "shape post"])
        self.assertIn(agent, Base[:])
        self.assertIn(agent, Shape[:])
        self.assertTrue(isinstance(agent, Shape))
        self.assertIs(Shape[agent].ready, False)
        self.assertIn(agent, ~Shape)
        agent.ready = True
        self.assertTrue(bool(agent))
        self.assertIn(agent, Shape)

    def test_flag_words_begin_at_field_entry(self):
        @Flag("assembled")
        class Marked(Tag):
            @Record
            def value(agent):
                return None

            @Imprint
            def Train(agent):
                self.assertFalse(Keyword(agent, Marked))
                self.assertFalse(Keyword(agent, "assembled"))
                self.assert_not_admitted(Marked, agent)

        agent = Host()
        Marked(agent)
        self.assertTrue(Keyword(agent, Marked))
        self.assertIn("assembled", agent)

    def test_unadmitted_training_does_not_run_rip_on_field_cleanup_or_finalization(self):
        events = []

        class Unfinished(Tag):
            @Imprint
            def Train(agent):
                events.append("train")
                raise ValueError("unfinished")

            @Rip
            def Release(agent):
                events.append("rip")

        agent = Host()
        with self.assertRaises(TagImprintError.Train):
            Unfinished(agent)
        self.assert_not_admitted(Unfinished, agent)
        for member in Unfinished[:]:
            del Unfinished[member]
        self.assertEqual(events, ["train"])
        reference = weakref.ref(agent)
        del agent
        gc.collect()
        self.assertIsNone(reference())
        self.assertEqual(events, ["train"])

    def test_a_runtime_clone_keeps_completed_preparation_after_its_first_builder_fails(self):
        preparations = []

        class CloneHost:
            def __setattr__(self, name, value):
                if name == "__class__":
                    preparations.append(value)
                object.__setattr__(self, name, value)

        class Seed(Tag):
            pass

        class Failed(Tag):
            @Record
            def missing(agent):
                raise ValueError("no value produced")

        class Repaired(Tag):
            @Record
            def ready(agent):
                return True

        seed = CloneHost()
        Seed(seed)
        clone = type(seed)()
        preparations.clear()

        with self.assertRaises(TagCompositionError):
            Failed(clone)
        self.assertNotIn(clone, Failed[:])
        self.assertFalse("missing" @ clone)
        self.assertEqual(len(preparations), 1)

        Repaired(clone)
        self.assertEqual(len(preparations), 1)
        self.assertTrue("ready" @ clone)
        self.assertIn(clone, Repaired)

    def test_view_closing_failure_keeps_completed_admission(self):
        class Finished(Tag):
            @Secret
            @Record
            def hidden(agent):
                return "private"

            @Record
            def ready(agent):
                return True

            @Report
            def status(tag):
                return "ready"

            @Imprint
            def Finish(agent):
                del Finished.status

        agent = Host()
        with self.assertRaises(AttributeError):
            Finished(agent)
        self.assertIn(agent, Finished[:])
        self.assertTrue(isinstance(agent, Finished))
        self.assertTrue("ready" @ agent)
        self.assertTrue(agent.ready)
        self.assertFalse("hidden" @ agent)
        with self.assertRaises(AttributeError):
            agent.hidden


if __name__ == "__main__":
    unittest.main()
