"""Imprints own nested failures after their Tag has committed."""

import gc
import unittest
import weakref

from TopKit import (Action, Contract, Imprint, Post, Pre, Record, Report,
                    Rip, Tag, TagCompositionError, TagContractError,
                    TagImprintError, TagPostconditionError, TagPreconditionError)


class Host:
    pass


class Stop(BaseException):
    pass


class NestedImprintTests(unittest.TestCase):
    def test_nested_gate_failure_is_owned_by_outer_imprint_and_cleanup_survives(self):
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
        self.assertIn(agent, Outer[:])
        self.assertTrue(isinstance(agent, Outer))
        self.assertNotIn(agent, Nested[:])
        del Outer[agent]
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
        self.assertIn(agent, Outer[:])

    def test_interruption_preserves_the_tag_view_and_later_cleanup(self):
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
                self.assertEqual(Trained[agent].Present(), "badge")
                self.assertTrue(Contract.Holds(agent))
                self.assertTrue(bool(agent))
                self.assertNotIn(agent, ~Trained)
                del Trained[agent]
                self.assertEqual(events, ["acquire", "release"])

    def test_nested_interruption_preserves_both_committed_tags(self):
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
        del Outer[agent]
        del Inner[agent]

    def test_interrupted_base_preserves_only_the_committed_form_prefix(self):
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
        self.assertFalse(isinstance(agent, Shape))
        self.assertFalse(hasattr(agent, "later"))
        del Base[agent]

    def test_gate_and_parts_interruptions_still_restore_the_incoming_agent(self):
        for mark in (Pre, Record):
            with self.subTest(phase="Gate" if mark is Pre else "Parts"):
                failure = KeyboardInterrupt()

                def stop(agent):
                    agent.temporary = True
                    raise failure

                Refused = type("Refused", (Tag,), {"Stop": mark(stop)})
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

    def test_record_failure_uses_its_own_phase_despite_nested_post_failure(self):
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
        with self.assertRaises(TagPostconditionError.Ready):
            Outer(agent)
        self.assertNotIn(agent, Inner[:])
        self.assertNotIn(agent, Outer[:])
        self.assertFalse(isinstance(agent, Inner))
        self.assertEqual(vars(agent), {})

    def test_later_parts_failure_restores_the_whole_form_call(self):
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
        original_type = type(agent)
        with self.assertRaises(TagImprintError):
            Shape(agent)
        self.assertEqual(events, ["trained"])
        self.assertEqual(vars(agent), {"original": "kept"})
        self.assertIs(type(agent), original_type)
        self.assertNotIn(agent, Base[:])
        self.assertNotIn(agent, Shape[:])

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
        self.assertTrue(Contract.Holds(agent))
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

            @Imprint
            def Continue(agent):
                if agent.application == 1:
                    del Reapplied[agent]
                    Reapplied(agent)
                    raise failure

        agent = Host()
        with self.assertRaises(KeyboardInterrupt) as caught:
            Reapplied(agent)
        self.assertIs(caught.exception, failure)
        self.assertIn(agent, Reapplied[:])
        self.assertEqual(Reapplied[agent].application, 2)
        self.assertEqual(applications, ["built", "built"])
        del Reapplied[agent]

    def test_snapshot_failure_does_not_replace_the_primary_interruption(self):
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
        self.assertTrue(any("AttributeError" in note for note in failure.__notes__))
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
        self.assertTrue(Contract.Holds(agent))
        del Finished[agent]

    def test_diagnostic_failure_does_not_replace_the_primary_interruption(self):
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
        del Interrupted[agent]
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
                with self.assertRaises(TagImprintError.Train):
                    Trained(agent)
                self.assertIn(agent, Trained[:])
                self.assertEqual(Contract.Holds(agent), prepared)
                self.assertEqual(bool(agent), prepared)
                self.assertEqual(agent in ~Trained, not prepared)
                self.assertEqual(agent in list(Trained), prepared)
                self.assertEqual(later, [])
                del Trained[agent]
