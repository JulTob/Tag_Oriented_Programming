"""Unfinished Imprints retain Gains while completed Tags remain admitted."""

import gc
import unittest
import weakref

from TopKit import (Action, Imprint, Pin, Post, Pre, Record, Report,
                    Rip, Tag, TagCompositionError, TagContractError,
                    TagImprintError, TagPostconditionError, TagPreconditionError,
                    TagResolutionError, TagOverwriteWarning)


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

        class Inner(Pin):
            @Action
            def Cleanup(tag):
                calls.append("inner")

        class Outer(Pin):
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

    def test_nested_gate_failure_keeps_outer_gains_without_admission_or_auto_rip(self):
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
        with self.assertRaises(TagImprintError.Continue) as caught:
            Outer(agent)
        self.assertIsInstance(caught.exception.__cause__, TagPreconditionError.Refuse)
        self.assertNotIn(agent, Outer[:])
        self.assertFalse(isinstance(agent, Outer))
        self.assertNotIn(agent, Nested[:])
        self.assertTrue("Release" @ agent)
        with self.assertRaises(TagResolutionError):
            del Outer[agent]
        self.assertEqual(events, ["acquire"])
        agent.Release()   # the acquired Action remains callable explicitly
        self.assertEqual(events, ["acquire", "release"])

    def test_nested_composition_error_is_owned_by_outer_imprint(self):
        class Outer(Tag):
            @Imprint
            def Work(agent):
                raise TagCompositionError("nested refusal")

        agent = Host()
        with self.assertRaises(TagImprintError.Work) as caught:
            Outer(agent)
        self.assertIsInstance(caught.exception.__cause__, TagCompositionError)
        self.assertNotIn(agent, Outer[:])
        self.assertFalse(isinstance(agent, Outer))

    def test_interruption_preserves_gains_and_current_fitness_without_a_tag_view(self):
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
                self.assertNotIn(agent, Trained[:])
                self.assertFalse(isinstance(agent, Trained))
                with self.assertRaises(TagResolutionError):
                    Trained[agent]
                self.assertEqual(agent.Present(), "badge")
                self.assertTrue(bool(agent))
                self.assertNotIn(agent, ~Trained)
                self.assertEqual(events, ["acquire"])
                agent.Release()
                self.assertEqual(events, ["acquire", "release"])

    def test_nested_interruption_admits_neither_unfinished_tag(self):
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
        self.assertNotIn(agent, Inner[:])
        self.assertNotIn(agent, Outer[:])
        self.assertFalse(isinstance(agent, Inner))
        self.assertFalse(isinstance(agent, Outer))

    def test_interrupted_base_does_not_admit_it_or_begin_its_shape(self):
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
        self.assertNotIn(agent, Base[:])
        self.assertNotIn(agent, Shape[:])
        self.assertFalse(isinstance(agent, Base))
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

    def test_interrupted_record_keeps_earlier_gains_without_admission(self):
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
        self.assertNotIn(agent, Unfinished[:])
        self.assertFalse(isinstance(agent, Unfinished))

    def test_record_cannot_start_tagging_before_a_nested_post_failure(self):
        class Inner(Tag):
            @Post
            def Ready(agent):
                return False

        class Outer(Tag):
            @Record
            def item(agent):
                Inner(agent)
                return "not built"

        agent = Host()
        with self.assertRaises(TagCompositionError) as refusal:
            Outer(agent)
        self.assertIn("Record Outer.item", str(refusal.exception))
        self.assertNotIn(agent, Inner[:])
        self.assertNotIn(agent, Outer[:])
        self.assertFalse(isinstance(agent, Inner))
        self.assertFalse("item" @ agent)

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
        with self.assertRaises(TagImprintError):
            Shape(agent)
        self.assertEqual(events, ["trained"])
        self.assertEqual(agent.original, "kept")
        self.assertEqual(agent.badge, "built")
        self.assertIn(agent, Base[:])
        self.assertTrue(isinstance(agent, Base))
        self.assertEqual(Base[agent].badge, "built")
        self.assertNotIn(agent, Shape[:])
        self.assertFalse(isinstance(agent, Shape))
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
        self.assertNotIn(agent, Outer[:])
        self.assertEqual(Reapplied[agent].application, 2)
        self.assertEqual(applications, ["built", "built"])
        del Reapplied[agent]

    def test_unfinished_training_does_not_attempt_a_snapshot_or_replace_interruption(self):
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
        self.assertNotIn(agent, Interrupted[:])
        self.assertFalse(isinstance(agent, Interrupted))
        self.assertEqual(getattr(failure, "__notes__", []), [])
        self.assertTrue("Release" @ agent)
        self.assertEqual(events, [])
        agent.Release()
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

    def test_unfinished_training_preserves_existing_exception_notes(self):
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
        self.assertNotIn(agent, Interrupted[:])
        self.assertFalse(isinstance(agent, Interrupted))
        self.assertEqual(events, [])
        agent.Release()
        self.assertEqual(events, ["release"])

    def test_handled_imprint_failure_does_not_keep_an_agent_in_the_field(self):
        class Failed(Tag):
            @Imprint
            def Train(agent):
                raise RuntimeError("failed")

        def attempt():
            agent = Host()
            reference = weakref.ref(agent)
            try:
                Failed(agent)
            except TagImprintError:
                pass
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

    def test_failed_imprint_discards_the_unadmitted_post(self):
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
                with self.assertRaises(TagImprintError.Train):
                    Trained(agent)
                self.assertNotIn(agent, Trained[:])
                self.assertFalse(isinstance(agent, Trained))
                self.assertTrue("badge" @ agent)
                self.assertTrue(bool(agent))
                self.assertFalse(hasattr(agent, "Equipped"))
                self.assertNotIn(agent, ~Trained)
                self.assertNotIn(agent, list(Trained))
                self.assertEqual(later, [])
