"""Prepared Tags admit after best-effort training; Posts judge the result."""

import gc
import unittest
import warnings
import weakref

from TopKit import (Action, Constant, Contract, Flag, Imprint, Keyword,
                    Operation, Pin, Post, Pre, Public, Record, Report, Rip, Tag,
                    TagCompositionError,
                    TagPostconditionError, TagPreconditionError,
                    TagResolutionError, TagTrainingWarning, Secret)


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

    def assert_admitted(self, tag, agent):
        self.assertIn(agent, tag[:])
        self.assertTrue(isinstance(agent, tag))
        self.assertIsNotNone(tag[agent])

    def tag_without_training_warning(self, tag, agent, **inputs):
        # An assertion inside an Imprint is an ordinary Exception too. Do not
        # allow best-effort warning semantics to conceal a broken test fixture.
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", TagTrainingWarning)
            result = tag(agent, **inputs)
        self.assertFalse([item for item in caught
                          if isinstance(item.message, TagTrainingWarning)])
        return result

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
        self.assertIs(self.tag_without_training_warning(Assembled, agent), agent)
        self.assertEqual(events, ["imprint", "post"])
        self.assertIn(agent, Assembled[:])
        self.assertTrue(isinstance(agent, Assembled))
        self.assertIsNone(Assembled[agent].Read())
        self.assertEqual(agent.status, "assembled")
        self.assertEqual(agent.Identify(), "Assembled")

    def test_failed_record_warns_and_later_gains_are_acquired_before_admission(self):
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
        with self.assertWarnsRegex(TagTrainingWarning.missing, "builder failed"):
            Unfinished(agent)
        self.assert_admitted(Unfinished, agent)
        self.assertTrue("Read" @ agent)
        self.assertTrue("value" @ agent)
        self.assertIs(agent.Read(), False)
        self.assertFalse("missing" @ agent)
        self.assertTrue("later" @ agent)
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
        self.assert_admitted(Unfinished, agent)
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
        self.tag_without_training_warning(New, agent)
        self.assertEqual(agent.status, "new")
        self.assertEqual(agent.Identify(), "new")
        self.assertIn(agent, Existing[:])
        self.assertIn(agent, New[:])

    def test_failed_imprint_continues_but_interruptions_stop_later_training(self):
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
                        events.append("later")

                agent = Host()
                if isinstance(failure, Exception):
                    with self.assertWarns(TagTrainingWarning.Finish) as caught:
                        self.assertIs(Unfinished(agent), agent)
                    self.assertEqual(caught.warning.cause_type, "ValueError")
                    self.assertEqual(caught.warning.cause_text, "failed")
                    expected_events = ["acquire", "later"]
                else:
                    with self.assertRaises(type(failure)) as caught:
                        Unfinished(agent)
                    self.assertIs(caught.exception, failure)
                    expected_events = ["acquire"]
                self.assert_admitted(Unfinished, agent)
                self.assertTrue("Read" @ agent)
                self.assertTrue("value" @ agent)
                self.assertIsNone(agent.Read())
                self.assertEqual(events, expected_events)

    def test_rip_then_retag_runs_a_fresh_gate_gainings_and_all_imprints(self):
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
        with self.assertWarns(TagTrainingWarning.Finish):
            Retried(agent)
        self.assert_admitted(Retried, agent)
        self.assertEqual(agent.round, 1)
        # An admitted Tagging is a no-op until explicit Rip begins a new turn.
        self.assertIs(Retried(agent), agent)
        self.assertEqual(agent.round, 1)
        del Retried[agent]
        self.assertIs(Retried(agent), agent)
        self.assertEqual(agent.round, 2)
        self.assertIn(agent, Retried[:])
        self.assertEqual(events, [("gate", 0), ("first", 1), ("finish", 1),
                                  ("gate", 1), ("first", 2), ("finish", 2)])

    def test_a_refused_retag_keeps_gains_from_the_previous_ripped_application(self):
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
        with self.assertWarns(TagTrainingWarning.Finish):
            Retried(agent)
        self.assert_admitted(Retried, agent)
        del Retried[agent]
        agent.allowed = False
        with self.assertRaises(TagPreconditionError.Allowed):
            Retried(agent)
        self.assertNotIn(agent, Retried[:])
        self.assertNotIn(agent, Retried)
        self.assertTrue(isinstance(agent, Retried))  # historical Tagging survives Rip
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
        with self.assertWarnsRegex(TagTrainingWarning.value, "not built"):
            Retried(agent)
        self.assert_admitted(Retried, agent)
        token = agent.token
        self.assertTrue("token" @ agent)
        self.assertFalse("value" @ agent)
        with self.assertRaises(TagCompositionError):
            agent.token = None
        with self.assertRaises(TagCompositionError):
            del agent.token
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
        self.tag_without_training_warning(Base, agent)
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
                    warnings.simplefilter("always")
                    self.assertIs(Shape(agent), agent)
                self.assertEqual([item.message.name for item in caught],
                                 ["next_value", "Finish"] if phase == "gain"
                                 else ["Finish"])
                self.assertTrue(all(isinstance(item.message, TagTrainingWarning)
                                    for item in caught))
                self.assertIn(agent, Base[:])
                self.assertTrue(isinstance(agent, Base))
                self.assertEqual(Base[agent].base_value, "base")
                self.assert_admitted(Shape, agent)
                self.assertTrue("partial" @ agent)
                self.assertIsNone(agent.partial)
                self.assertEqual("next_value" @ agent, phase != "gain")

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
        with self.assertWarns(TagTrainingWarning.Finish):
            Outer(agent)
        self.assertIn(agent, Inner[:])
        self.assertTrue(isinstance(agent, Inner))
        self.assertIsNone(Inner[agent].inner_value)
        self.assert_admitted(Outer, agent)
        self.assertTrue("outer_value" @ agent)
        self.assertIs(agent.outer_value, False)

    def test_failed_training_keeps_safety_posts_and_explicit_action_guards(self):
        observations = []

        class Existing(Tag):
            @Public
            @Operation
            def Use(agent_tag, agent):
                return "existing service"

        class Safe(Tag):
            @Pre
            def Can_Train(agent):
                observations.append("Safe Gate")
                return agent.can_train

            @Record
            def insulated(agent):
                return True

        class Electric(Tag):
            @Record
            def before_safety(agent):
                observations.append(("before", dict(Contract.Status(agent))))
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
                observations.append(("after", agent.SafetyChecks, agent.ReadBattery()))
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

        with self.assertWarns(TagTrainingWarning.Train) as caught:
            with self.assertRaises(TagPostconditionError.SafetyChecks):
                Electric(agent)
        # The nested new Tagging is refused by existing broken Posts before its
        # own Gate, so it cannot serve as an implicit recovery mechanism.
        self.assertEqual(caught.warning.cause_type, "TagCompositionError")
        self.assertIn("current Posts fail", caught.warning.cause_text)
        self.assertEqual(observations, [("before", {}), ("after", False, False)])
        self.assert_admitted(Electric, agent)
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
        with self.assertRaisesRegex(AssertionError, "SafetyChecks"):
            agent.TurnOnBattery()
        self.assertIs(agent.ReadBattery(), False)
        self.assertIs(agent.battery_on, False)

        # Ordinary Records and guarded Actions provide explicit repair. New
        # unrelated Tagging is possible only after the existing Posts pass.
        agent.insulated = True
        agent.can_train = True
        self.assertTrue(bool(agent))
        Safe(agent)
        self.assertEqual(observations[-1], "Safe Gate")
        self.assertIn(agent, Safe[:])
        self.assertIn(agent, list(Existing))
        self.assertEqual(agent.Use(), "existing service")
        agent.TurnOnBattery()
        self.assertIs(agent.ReadBattery(), True)

    def test_a_failed_pin_imprint_keeps_admission_and_tag_scoped_gains(self):
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

        with self.assertWarns(TagTrainingWarning.Finish):
            Unfinished(Receiver)
        self.assert_admitted(Unfinished, Receiver)
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

    def test_each_completed_tag_checks_posts_before_the_next_shape_begins(self):
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
        with self.assertRaises(TagPostconditionError.Has_Shape_Gain):
            Shape(agent)
        self.assertEqual(checks, ["base post"])
        self.assertIn(agent, Base[:])
        self.assert_not_admitted(Shape, agent)
        self.assertFalse("ready" @ agent)
        self.assertIn(agent, ~Base)

        # Repair Base before the distinct Shape turn. Its own Post then judges
        # the Shape's new Record, without undoing either completed admission.
        agent.ready = True
        with self.assertRaises(TagPostconditionError.Works):
            Shape(agent)
        self.assertIn(agent, Base[:])
        self.assert_admitted(Shape, agent)
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
        self.tag_without_training_warning(Marked, agent)
        self.assertTrue(Keyword(agent, Marked))
        self.assertIn("assembled", agent)

    def test_failed_training_runs_rip_on_cleanup_or_agent_end_without_replay(self):
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
        with self.assertWarns(TagTrainingWarning.Train):
            Unfinished(agent)
        self.assert_admitted(Unfinished, agent)
        for member in Unfinished[:]:
            del Unfinished[member]
        self.assertEqual(events, ["train", "rip"])
        del member  # the loop variable must not retain the last weak member
        reference = weakref.ref(agent)
        del agent
        gc.collect()
        self.assertIsNone(reference())
        self.assertEqual(events, ["train", "rip"])

        # A separate admitted failed training also tears down when its Agent
        # ends naturally, without requiring an explicit population walk.
        ending = Host()
        with self.assertWarns(TagTrainingWarning.Train):
            Unfinished(ending)
        self.assert_admitted(Unfinished, ending)
        reference = weakref.ref(ending)
        del ending
        gc.collect()
        self.assertIsNone(reference())
        self.assertEqual(events, ["train", "rip", "train", "rip"])

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

        with self.assertWarns(TagTrainingWarning.missing):
            Failed(clone)
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
