"""Nested Tagging keeps completed work; failed Imprints still admit members."""

import gc
import unittest
import weakref

from TopKit import (Action, Imprint, Pin, Post, Pre, Record, Report,
                    Rip, Tag, TagCompositionError, TagContractError,
                    TagImprintError, TagPostconditionError,
                    TagTrainingWarning, TagOverwriteWarning)


class Host:
    pass


class Stop(BaseException):
    pass


class NestedImprintTests(unittest.TestCase):
    def test_nested_tag_does_not_replace_outer_rip_teardown(self):
        calls = []

        class Inner(Tag):
            @Action
            def Cleanup(agent):
                calls.append("inner")

        class Outer(Tag):
            @Rip
            def Cleanup(agent):
                calls.append("outer")

            @Imprint
            def Train(agent):
                Inner(agent)

        agent = Host()
        with self.assertWarns(TagOverwriteWarning):
            Outer(agent)
        self.assertIn(agent, Outer[:])
        self.assertIn(agent, Inner[:])

        del Outer[agent]
        self.assertEqual(calls, ["outer"])

    def test_nested_pin_does_not_replace_outer_rip_teardown(self):
        calls = []

        class Receiver(Tag):
            pass

        @Pin
        class Inner(Tag):
            @Action
            def Cleanup(tag):
                calls.append("inner")

        @Pin
        class Outer(Tag):
            @Rip
            def Cleanup(tag):
                calls.append("outer")

            @Imprint
            def Train(tag):
                Inner(tag)

        with self.assertWarns(TagOverwriteWarning):
            Outer(Receiver)
        self.assertIn(Receiver, Outer[:])
        self.assertIn(Receiver, Inner[:])

        del Outer[Receiver]
        self.assertEqual(calls, ["outer"])

    def test_nested_gate_failure_warns_and_admits_outer_without_auto_rip(self):
        events = []

        class Nested(Tag):
            @Pre
            def Refuse(agent):
                return False

        class Outer(Tag):
            @Imprint
            def Acquire(agent):
                events.append("acquire")

            @Imprint
            def Continue(agent):
                Nested(agent)

            @Rip
            def Release(agent):
                events.append("release")

        agent = Host()
        with self.assertWarns(TagTrainingWarning) as warned:
            Outer(agent)
        self.assertIsInstance(warned.warning.failure, TagImprintError.Continue)
        self.assertEqual(warned.warning.cause_type, "Refuse")
        self.assertIn("Precondition 'Refuse'", warned.warning.cause_text)
        self.assertIsNone(warned.warning.failure.__cause__)
        self.assertIn(agent, Outer[:])
        self.assertTrue(isinstance(agent, Outer))
        self.assertNotIn(agent, Nested[:])
        self.assertTrue("Release" @ agent)
        self.assertEqual(events, ["acquire"])
        del Outer[agent]
        self.assertEqual(events, ["acquire", "release"])

    def test_nested_composition_error_is_owned_by_outer_imprint(self):
        class Outer(Tag):
            @Imprint
            def Work(agent):
                raise TagCompositionError("nested refusal")

        agent = Host()
        with self.assertWarns(TagTrainingWarning) as warned:
            Outer(agent)
        self.assertIsInstance(warned.warning.failure, TagImprintError.Work)
        self.assertEqual(warned.warning.cause_type, "TagCompositionError")
        self.assertEqual(warned.warning.cause_text, "nested refusal")
        self.assertIsNone(warned.warning.failure.__cause__)
        self.assertIn(agent, Outer[:])
        self.assertTrue(isinstance(agent, Outer))

    def test_interruption_preserves_gains_admission_and_current_fitness(self):
        for failure in (KeyboardInterrupt(), SystemExit(7), Stop()):
            with self.subTest(failure=type(failure).__name__):
                events = []

                class Trained(Tag):
                    @Record
                    def badge(agent):
                        return "badge"

                    @Action
                    def Present(agent):
                        return agent.badge

                    @Imprint
                    def Acquire(agent):
                        events.append("acquire")

                    @Imprint
                    def Continue(agent):
                        raise failure

                    @Post
                    def Equipped(agent):
                        return agent.badge == "badge"

                    @Rip
                    def Release(agent):
                        events.append("release")

                agent = Host()
                with self.assertRaises(type(failure)) as caught:
                    Trained(agent)
                self.assertIs(caught.exception, failure)
                self.assertIn(agent, Trained[:])
                self.assertTrue(isinstance(agent, Trained))
                self.assertEqual(Trained[agent].badge, "badge")
                self.assertEqual(agent.Present(), "badge")
                self.assertTrue(bool(agent))
                self.assertNotIn(agent, ~Trained)
                self.assertEqual(events, ["acquire"])
                del Trained[agent]
                self.assertEqual(events, ["acquire", "release"])

    def test_nested_interruption_admits_both_started_tags(self):
        failure = KeyboardInterrupt()

        class Inner(Tag):
            @Imprint
            def Stop(agent):
                raise failure

        class Outer(Tag):
            @Imprint
            def Continue(agent):
                Inner(agent)

        agent = Host()
        with self.assertRaises(KeyboardInterrupt) as caught:
            Outer(agent)
        self.assertIs(caught.exception, failure)
        self.assertIn(agent, Inner[:])
        self.assertIn(agent, Outer[:])
        self.assertTrue(isinstance(agent, Inner))
        self.assertTrue(isinstance(agent, Outer))

    def test_interrupted_base_is_admitted_but_does_not_begin_its_shape(self):
        failure = KeyboardInterrupt()

        class Base(Tag):
            @Imprint
            def Stop(agent):
                raise failure

        class Shape(Base):
            @Record
            def later(agent):
                return "not built"

        agent = Host()
        with self.assertRaises(KeyboardInterrupt) as caught:
            Shape(agent)
        self.assertIs(caught.exception, failure)
        self.assertIn(agent, Base[:])
        self.assertNotIn(agent, Shape[:])
        self.assertTrue(isinstance(agent, Base))
        self.assertFalse(isinstance(agent, Shape))
        self.assertFalse("later" @ agent)

    def test_interrupted_gate_does_not_begin_gainings(self):
        failure = KeyboardInterrupt()

        class Refused(Tag):
            @Pre
            def Stop(agent):
                raise failure

            @Record
            def value(agent):
                return None

        agent = Host()
        agent.untouched = "kept"
        original_type = type(agent)
        with self.assertRaises(KeyboardInterrupt) as caught:
            Refused(agent)
        self.assertIs(caught.exception, failure)
        self.assertEqual(vars(agent), {"untouched": "kept"})
        self.assertIs(type(agent), original_type)
        self.assertNotIn(agent, Refused[:])
        self.assertFalse(isinstance(agent, Refused))

    def test_interrupted_record_keeps_earlier_gains_and_admits(self):
        failure = KeyboardInterrupt()

        class Unfinished(Tag):
            @Record
            def value(agent):
                return None

            @Record
            def Stop(agent):
                raise failure

        agent = Host()
        agent.untouched = "kept"
        with self.assertRaises(KeyboardInterrupt) as caught:
            Unfinished(agent)
        self.assertIs(caught.exception, failure)
        self.assertEqual(agent.untouched, "kept")
        self.assertTrue("value" @ agent)
        self.assertIsNone(agent.value)
        self.assertFalse("Stop" @ agent)
        self.assertIn(agent, Unfinished[:])
        self.assertTrue(isinstance(agent, Unfinished))

    def test_record_warning_precedes_the_final_failed_post(self):
        class Outer(Tag):
            @Record
            def item(agent):
                raise RuntimeError("measurement failed")

            @Post
            def Ready(agent):
                return False

        agent = Host()
        with self.assertWarns(TagTrainingWarning) as warned:
            with self.assertRaises(TagPostconditionError.Ready):
                Outer(agent)
        self.assertEqual(warned.warning.name, "item")
        self.assertEqual(warned.warning.cause_type, "RuntimeError")
        self.assertIn(agent, Outer[:])
        self.assertIn(agent, ~Outer)
        self.assertFalse("item" @ agent)

    def test_nested_form_stops_at_base_post_before_shape_imprint(self):
        events = []

        class Base(Tag):
            @Post
            def Ready(agent):
                events.append("base post")
                return False

        class Shape(Base):
            @Imprint
            def Train(agent):
                events.append("shape imprint")

        class Outer(Tag):
            @Imprint
            def Join(agent):
                Shape(agent)

        agent = Host()
        with self.assertWarns(TagTrainingWarning) as warned:
            with self.assertRaises(TagPostconditionError.Ready):
                Outer(agent)
        self.assertIsInstance(warned.warning.failure, TagImprintError.Join)
        self.assertEqual(warned.warning.cause_type, "Ready")
        self.assertIn("Postcondition 'Ready'", warned.warning.cause_text)
        self.assertIsNone(warned.warning.failure.__cause__)
        self.assertEqual(events, ["base post", "base post"])
        self.assertIn(agent, Base[:])
        self.assertNotIn(agent, Shape[:])
        self.assertIn(agent, Outer[:])

    def test_later_record_failure_preserves_the_completed_form_prefix(self):
        events = []

        class Base(Tag):
            @Record
            def badge(agent):
                return "built"

            @Imprint
            def Train(agent):
                events.append("trained")

        class Shape(Base):
            @Record
            def item(agent):
                raise TagImprintError("nested refusal")

        agent = Host()
        agent.original = "kept"
        with self.assertWarns(TagTrainingWarning) as warned:
            Shape(agent)
        self.assertEqual(warned.warning.name, "item")
        self.assertEqual(warned.warning.cause_type, "TagImprintError")
        self.assertEqual(events, ["trained"])
        self.assertEqual(agent.original, "kept")
        self.assertEqual(agent.badge, "built")
        self.assertIn(agent, Base[:])
        self.assertTrue(isinstance(agent, Base))
        self.assertEqual(Base[agent].badge, "built")
        self.assertIn(agent, Shape[:])
        self.assertTrue(isinstance(agent, Shape))
        self.assertFalse("item" @ agent)

    def test_interrupted_quality_check_preserves_the_completed_training(self):
        failure = KeyboardInterrupt()
        checks = []

        class Trained(Tag):
            @Record
            def badge(agent):
                return "badge"

            @Post
            def Equipped(agent):
                checks.append("check")
                if len(checks) == 1:
                    raise failure
                return agent.badge == "badge"

        agent = Host()
        with self.assertRaises(KeyboardInterrupt) as caught:
            Trained(agent)
        self.assertIs(caught.exception, failure)
        self.assertIn(agent, Trained[:])
        self.assertEqual(Trained[agent].badge, "badge")
        self.assertTrue(bool(agent))
        del Trained[agent]

    def test_invalid_post_verdict_keeps_the_agent_in_the_defective_population(self):
        class Invalid(Tag):
            @Post
            def Ready(agent):
                return 1

        agent = Host()
        with self.assertRaises(TagContractError):
            Invalid(agent)
        self.assertIn(agent, Invalid[:])
        self.assertIn(agent, ~Invalid)
        self.assertFalse(bool(agent))
        self.assertNotIn(agent, list(Invalid))
        del Invalid[agent]

    def test_interrupt_does_not_undo_an_explicit_rip_and_reapplication(self):
        failure = KeyboardInterrupt()
        applications = []

        class Reapplied(Tag):
            @Record
            def application(agent):
                applications.append("built")
                return len(applications)

        class Outer(Tag):
            @Imprint
            def Continue(agent):
                Reapplied(agent)
                del Reapplied[agent]
                Reapplied(agent)
                raise failure

        agent = Host()
        with self.assertRaises(KeyboardInterrupt) as caught:
            Outer(agent)
        self.assertIs(caught.exception, failure)
        self.assertIn(agent, Reapplied[:])
        self.assertIn(agent, Outer[:])
        self.assertEqual(Reapplied[agent].application, 2)
        self.assertEqual(applications, ["built", "built"])
        del Reapplied[agent]

    def test_interrupted_training_keeps_its_interruption_after_snapshot_attempt(self):
        failure = KeyboardInterrupt()
        events = []

        class Interrupted(Tag):
            @Report
            def status(tag):
                return "ready"

            @Imprint
            def Continue(agent):
                del Interrupted.status
                raise failure

            @Rip
            def Release(agent):
                events.append("release")

        agent = Host()
        with self.assertRaises(KeyboardInterrupt) as caught:
            Interrupted(agent)
        self.assertIs(caught.exception, failure)
        self.assertIn(agent, Interrupted[:])
        self.assertTrue(isinstance(agent, Interrupted))
        self.assertIn("could not be captured", " ".join(getattr(failure, "__notes__", [])))
        self.assertTrue("Release" @ agent)
        self.assertEqual(events, [])
        del Interrupted[agent]
        self.assertEqual(events, ["release"])

    def test_snapshot_only_failure_preserves_finished_work(self):
        class Finished(Tag):
            @Record
            def ready(agent):
                return True

            @Report
            def status(tag):
                return "ready"

            @Imprint
            def Finish(agent):
                del Finished.status

            @Action
            def Work(agent):
                return agent.ready

        agent = Host()
        with self.assertRaises(AttributeError):
            Finished(agent)
        self.assertIn(agent, Finished[:])
        self.assertTrue(agent.Work())
        self.assertTrue(bool(agent))
        del Finished[agent]

    def test_interrupted_training_preserves_existing_exception_notes(self):
        failure = Stop()
        failure.__notes__ = "legacy notes"
        events = []

        class Interrupted(Tag):
            @Report
            def status(tag):
                return "ready"

            @Imprint
            def Continue(agent):
                del Interrupted.status
                raise failure

            @Rip
            def Release(agent):
                events.append("release")

        agent = Host()
        with self.assertRaises(Stop) as caught:
            Interrupted(agent)
        self.assertIs(caught.exception, failure)
        self.assertEqual(failure.__notes__, "legacy notes")
        self.assertIn(agent, Interrupted[:])
        self.assertTrue(isinstance(agent, Interrupted))
        self.assertEqual(events, [])
        del Interrupted[agent]
        self.assertEqual(events, ["release"])

    def test_failed_post_cannot_mask_an_interruption_with_existing_notes(self):
        failure = Stop()
        failure.__notes__ = "legacy notes"

        class Interrupted(Tag):
            @Post
            def Ready(agent):
                return False

            @Imprint
            def Stop_Training(agent):
                raise failure

        agent = Host()
        with self.assertRaises(Stop) as caught:
            Interrupted(agent)
        self.assertIs(caught.exception, failure)
        self.assertEqual(failure.__notes__, "legacy notes")
        self.assertIn(agent, Interrupted[:])
        self.assertIn(agent, ~Interrupted)

    def test_handled_imprint_warning_does_not_keep_a_collected_agent_in_the_field(self):
        for nested_cause in (False, True):
            with self.subTest(nested_cause=nested_cause):
                class Failed(Tag):
                    @Imprint
                    def Train(agent):
                        if nested_cause:
                            try:
                                raise ValueError("first failure")
                            except ValueError as previous:
                                raise RuntimeError("failed") from previous
                        raise RuntimeError("failed")

                def attempt():
                    agent = Host()
                    reference = weakref.ref(agent)
                    with self.assertWarns(TagTrainingWarning):
                        Failed(agent)
                    self.assertIn(agent, Failed[:])
                    return reference

                was_enabled = gc.isenabled()
                gc.disable()
                try:
                    reference = attempt()
                    self.assertIsNone(reference())
                    self.assertEqual(list(Failed[:]), [])
                finally:
                    if was_enabled:
                        gc.enable()

    def test_failed_imprint_fitness_follows_the_current_training_result(self):
        for prepared in (False, True):
            with self.subTest(prepared=prepared):
                later = []

                class Trained(Tag):
                    @Record
                    def badge(agent):
                        return "badge"

                    @Imprint
                    def Train(agent):
                        if not prepared:
                            agent.badge = None
                        raise RuntimeError("training or later reporting failed")

                    @Imprint
                    def Later(agent):
                        later.append("ran")

                    @Post
                    def Equipped(agent):
                        return agent.badge == "badge"

                agent = Host()
                with self.assertWarns(TagTrainingWarning) as warned:
                    if prepared:
                        self.assertIs(Trained(agent), agent)
                    else:
                        with self.assertRaises(TagPostconditionError.Equipped):
                            Trained(agent)
                self.assertIsInstance(warned.warning.failure, TagImprintError.Train)
                self.assertIn(agent, Trained[:])
                self.assertTrue(isinstance(agent, Trained))
                self.assertTrue("badge" @ agent)
                self.assertEqual(bool(agent), prepared)
                self.assertEqual(agent in ~Trained, not prepared)
                self.assertEqual(agent in list(Trained), prepared)
                self.assertEqual(later, ["ran"])
