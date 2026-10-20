"""Admission follows Gainings and Imprints; unfinished training leaves Gains."""

import gc
import unittest
import warnings
import weakref

from TopKit import (Action, Constant, Contract, Flag, Imprint, Keyword,
                    Operation, Pin, Post, Pre, Public, Record, Report, Rip, Tag,
                    TagCompositionError, TagContractWarning, TagImprintError,
                    TagPostconditionError, TagPreconditionError, TagTrainingWarning,
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

    def test_failed_record_keeps_prior_gains_and_later_records_continue(self):
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
                return "reached"

        agent = Host()
        with self.assertWarns(TagTrainingWarning) as caught:
            Unfinished(agent)
        self.assertEqual(caught.warning.name, "missing")
        self.assertIn(agent, Unfinished)
        self.assertTrue("Read" @ agent)
        self.assertTrue("value" @ agent)
        self.assertIs(agent.Read(), False)
        self.assertFalse("missing" @ agent)
        self.assertEqual(agent.later, "reached")

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
        self.assertIn(agent, Unfinished[:])
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

    def test_failed_imprint_and_interruptions_admit_the_trained_tag(self):
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
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always", TagTrainingWarning)
                    if isinstance(failure, Exception):
                        self.assertIs(Unfinished(agent), agent)
                        self.assertEqual(len(caught), 1)
                        self.assertIsInstance(caught[0].message.failure,
                                              TagImprintError.Finish)
                        self.assertEqual(caught[0].message.cause_type,
                                         type(failure).__name__)
                        self.assertEqual(caught[0].message.cause_text,
                                         str(failure))
                    else:
                        with self.assertRaises(type(failure)) as interrupted:
                            Unfinished(agent)
                        self.assertIs(interrupted.exception, failure)
                        self.assertEqual(caught, [])
                self.assertIn(agent, Unfinished[:])
                self.assertIn(agent, Unfinished)
                self.assertTrue("Read" @ agent)
                self.assertTrue("value" @ agent)
                self.assertIsNone(agent.Read())
                self.assertEqual(events, ["acquire", "not reached"] if isinstance(failure, Exception)
                                 else ["acquire"])

    def test_active_reapplication_is_a_noop_and_rip_allows_fresh_training(self):
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
        with self.assertWarns(TagTrainingWarning):
            Retried(agent)
        self.assertIn(agent, Retried[:])
        self.assertEqual(agent.round, 1)
        self.assertIs(Retried(agent), agent)
        self.assertEqual(agent.round, 1)
        del Retried[agent]
        self.assertNotIn(agent, Retried[:])
        Retried(agent)
        self.assertEqual(agent.round, 2)
        self.assertIn(agent, Retried[:])
        self.assertEqual(events, [("gate", 0), ("first", 1), ("finish", 1),
                                  ("gate", 1), ("first", 2), ("finish", 2)])

    def test_a_refused_fresh_tagging_keeps_existing_gains(self):
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
        with self.assertWarns(TagTrainingWarning):
            Retried(agent)
        self.assertIn(agent, Retried[:])
        del Retried[agent]
        agent.allowed = False
        with self.assertRaises(TagPreconditionError.Allowed):
            Retried(agent)
        self.assertNotIn(agent, Retried[:])
        with self.assertRaises(TagResolutionError):
            Retried[agent]
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
        with self.assertWarns(TagTrainingWarning) as caught:
            Retried(agent)
        self.assertEqual(caught.warning.name, "value")
        self.assertIn(agent, Retried[:])
        token = agent.token
        self.assertTrue("token" @ agent)
        self.assertFalse("value" @ agent)
        with self.assertRaises(TagCompositionError):
            agent.token = None
        with self.assertRaises(TagCompositionError):
            del agent.token
        Retried(agent)  # an active Tag does not rerun the failed Record
        self.assertFalse("value" @ agent)
        del Retried[agent]
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
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always", TagTrainingWarning)
                    Shape(agent)
                self.assertEqual(
                        [warning.message.name for warning in caught],
                        ["next_value", "Finish"] if phase == "gain" else ["Finish"],
                        )
                self.assertIn(agent, Base[:])
                self.assertTrue(isinstance(agent, Base))
                self.assertEqual(Base[agent].base_value, "base")
                self.assertIn(agent, Shape[:])
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
        with self.assertWarns(TagTrainingWarning):
            Outer(agent)
        self.assertIn(agent, Inner[:])
        self.assertTrue(isinstance(agent, Inner))
        self.assertIsNone(Inner[agent].inner_value)
        self.assertIn(agent, Outer[:])
        self.assertTrue("outer_value" @ agent)
        self.assertIs(agent.outer_value, False)

    def test_acquired_safety_post_blocks_new_tag_and_existing_service(self):
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

            @Action
            def RepairInsulation(agent):
                agent.insulated = True

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

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", TagTrainingWarning)
            with self.assertRaises(TagPostconditionError.SafetyChecks):
                Electric(agent)
        self.assertEqual(len(caught), 1)
        self.assertIsInstance(caught[0].message.failure,
                              TagImprintError.Train)
        # Electric's false SafetyChecks bars a fresh Safe Tagging before its
        # Gate. Electric still admits the Agent and keeps its training Gains.
        self.assertEqual(caught[0].message.cause_type, "TagCompositionError")
        self.assertIn("current Posts fail", caught[0].message.cause_text)
        self.assertIn(agent, Electric[:])
        self.assert_not_admitted(Safe, agent)
        self.assertTrue("before_safety" @ agent)
        self.assertTrue("after_safety" @ agent)
        self.assertIs(agent.SafetyChecks, False)
        self.assertFalse(bool(agent))
        self.assertIn(agent, Existing[:])
        self.assertNotIn(agent, list(Existing))
        self.assertIn(agent, ~Existing)
        with self.assertRaises(TagPostconditionError.SafetyChecks):
            agent.Use()
        with self.assertRaises(AssertionError):
            agent.TurnOnBattery()
        # Ordinary Actions can still read the broken Agent's state. Performative
        # Actions establish their own guards, as TurnOnBattery does above.
        self.assertIs(agent.ReadBattery(), False)
        self.assertIs(agent.battery_on, False)

        agent.RepairInsulation()
        self.assertTrue(agent.insulated)
        self.assertIs(agent.SafetyChecks, True)
        self.assertTrue(bool(agent))
        self.assertIn(agent, list(Existing))
        self.assertEqual(agent.Use(), "existing service")
        self.assertIn(agent, Electric)
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

        with self.assertWarns(TagTrainingWarning):
            Unfinished(Receiver)
        self.assertIn(Receiver, Unfinished[:])
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

    def test_posts_run_after_each_field_entry_and_failure_means_deficient_membership(self):
        checks = []

        class Base(Tag):
            @Post
            def Base_Ready(agent):
                checks.append("base post")
                return True

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
        self.assertEqual(checks, ["base post", "base post", "shape post"])
        self.assertIn(agent, Base[:])
        self.assertIn(agent, Shape[:])
        self.assertTrue(isinstance(agent, Shape))
        self.assertIs(Shape[agent].ready, False)
        self.assertIn(agent, ~Shape)
        agent.ready = True
        self.assertTrue(bool(agent))
        self.assertIn(agent, Shape)

    def test_failed_base_post_stops_before_shapes_gate_but_keeps_base(self):
        events = []

        class Base(Tag):
            @Record
            def ready(agent):
                events.append("base gain")
                return False

            @Post
            def Ready(agent):
                events.append("base post")
                return agent.ready

        class Shape(Base):
            @Pre
            def Allowed(agent):
                events.append("shape gate")
                return True

            @Record
            def ready(agent):
                events.append("shape gain")
                return True

        agent = Host()
        with self.assertRaises(TagPostconditionError.Ready):
            Shape(agent)
        self.assertEqual(events, ["base gain", "base post"])
        self.assertIn(agent, Base[:])
        self.assertIn(agent, ~Base)
        self.assertNotIn(agent, Shape[:])
        self.assertIs(agent.ready, False)

        # Repair and retry: the admitted Base is not trained again.
        events.clear()
        agent.ready = True
        Shape(agent)
        self.assertEqual(events, ["base post", "shape gate", "shape gain", "base post"])
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

    def test_failed_training_admits_and_runs_rip_on_field_cleanup(self):
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
        with self.assertWarns(TagTrainingWarning):
            Unfinished(agent)
        self.assertIn(agent, Unfinished[:])
        for member in Unfinished[:]:
            del Unfinished[member]
        del member
        self.assertEqual(events, ["train", "rip"])
        reference = weakref.ref(agent)
        del agent
        gc.collect()
        self.assertIsNone(reference())
        self.assertEqual(events, ["train", "rip"])

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

        with self.assertWarns(TagTrainingWarning) as caught:
            Failed(clone)
        self.assertEqual(caught.warning.name, "missing")
        self.assertIn(clone, Failed[:])
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
