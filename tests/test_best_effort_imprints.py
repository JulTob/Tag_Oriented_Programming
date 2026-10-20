"""Failed training is reported after the Tag has finished its Field turn."""

import gc
import unittest
import warnings
import weakref

from TopKit import (Imprint, Post, Public, Record, Report, Tag, TagContractError,
                    TagImprintError, TagPostconditionError, TagTrainingWarning,
                    TaggingFailure, TrainingWarning)


class Host:
    pass


class BestEffortImprintTests(unittest.TestCase):
    def test_each_failure_warns_in_order_and_later_training_still_runs(self):
        events = []

        class Vehicle(Tag):
            @Imprint
            def Engine(agent):
                events.append("engine")
                raise ValueError("no engine")

            @Imprint
            def Wheels(agent):
                events.append("wheels")
                agent.wheels = 4

            @Imprint
            def Lights(agent):
                events.append("lights")
                raise RuntimeError("no lights")

            @Post
            def Rolls(agent):
                events.append("post")
                return agent.wheels == 4

        agent = Host()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", TagTrainingWarning)
            self.assertIs(Vehicle(agent), agent)

        self.assertEqual(events, ["engine", "wheels", "lights", "post"])
        self.assertIn(agent, Vehicle)
        self.assertIn(agent, Vehicle[:])
        self.assertEqual([issue.message.name for issue in caught],
                         ["Engine", "Lights"])
        self.assertEqual([issue.message.kind for issue in caught],
                         ["Imprint", "Imprint"])
        self.assertIsInstance(caught[0].message.failure,
                              TagImprintError.Engine)
        self.assertIs(TrainingWarning.Engine, TagTrainingWarning.Engine)
        self.assertIsInstance(caught[0].message, TrainingWarning.Engine)
        self.assertEqual(caught[0].message.cause_type, "ValueError")
        self.assertEqual(caught[0].message.cause_text, "no engine")
        self.assertEqual(caught[0].message.origin,
                         caught[0].message.traceback_summary[-1][:2])
        self.assertEqual(caught[0].filename, __file__)
        self.assertGreater(caught[0].lineno, 0)

    def test_failed_training_admits_broken_member_then_raises_post(self):
        events = []

        class Vehicle(Tag):
            @Record
            def wheels(agent):
                return 0

            @Imprint
            def Wheels(agent):
                events.append("wheels")
                raise ValueError("assembly stopped")

            @Imprint
            def Later(agent):
                events.append("later")

            @Post
            def Rolls(agent):
                events.append("post")
                return agent.wheels == 4

        agent = Host()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", TagTrainingWarning)
            with self.assertRaises(TagPostconditionError.Rolls):
                Vehicle(agent)

        self.assertEqual(events, ["wheels", "later", "post"])
        self.assertEqual(len(caught), 1)
        self.assertIn(agent, Vehicle[:])
        self.assertIn(agent, ~Vehicle)
        self.assertNotIn(agent, Vehicle)
        self.assertIs(Vehicle(agent), agent)  # active reapplication remains a no-op

    def test_interruption_stops_training_but_preserves_admission_and_cause(self):
        events = []
        interruption = KeyboardInterrupt("stop")

        class Vehicle(Tag):
            @Public
            @Report
            def status(tag):
                return "ready"

            @Imprint
            def Engine(agent):
                events.append("engine")
                raise ValueError("not ready")

            @Imprint
            def Stop(agent):
                events.append("stop")
                del Vehicle.status
                raise interruption

            @Imprint
            def Later(agent):
                events.append("later")

            @Post
            def Ready(agent):
                events.append("post")
                return False

        agent = Host()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", TagTrainingWarning)
            with self.assertRaises(KeyboardInterrupt) as raised:
                Vehicle(agent)

        self.assertIs(raised.exception, interruption)
        self.assertEqual(events, ["engine", "stop", "post"])
        self.assertEqual([issue.message.name for issue in caught], ["Engine"])
        self.assertIn(agent, Vehicle[:])
        self.assertIn(agent, ~Vehicle)
        self.assertTrue(any("Post inspection" in note
                            for note in interruption.__notes__))
        self.assertTrue(any("could not be captured" in note
                            for note in interruption.__notes__))

    def test_warnings_as_errors_cannot_stop_field_entry_or_post_check(self):
        events = []

        class Vehicle(Tag):
            @Imprint
            def Fail(agent):
                events.append("fail")
                raise ValueError("no engine")

            @Imprint
            def Continue(agent):
                events.append("continue")

            @Post
            def Ready(agent):
                events.append("post")
                return True

        agent = Host()
        with warnings.catch_warnings():
            warnings.simplefilter("error", TagTrainingWarning)
            with self.assertRaises(TagTrainingWarning):
                Vehicle(agent)

        self.assertEqual(events, ["fail", "continue", "post"])
        self.assertIn(agent, Vehicle[:])

    def test_warnings_as_errors_preserve_later_failure_names(self):
        events = []

        class Vehicle(Tag):
            @Imprint
            def First(agent):
                events.append("first")
                raise ValueError("one")

            @Imprint
            def Second(agent):
                events.append("second")
                raise ValueError("two")

        agent = Host()
        with warnings.catch_warnings():
            warnings.simplefilter("error", TagTrainingWarning)
            with self.assertRaises(TrainingWarning.First) as raised:
                Vehicle(agent)

        self.assertEqual(events, ["first", "second"])
        self.assertIn("Second", " ".join(raised.exception.__notes__))
        self.assertIn(agent, Vehicle[:])

    def test_all_failed_posts_are_named_once_in_declaration_order(self):
        events = []

        class Vehicle(Tag):
            @Imprint
            def Train(agent):
                raise ValueError("training failed")

            @Post
            def HasWheels(agent):
                events.append("wheels")
                return False

            @Post
            def HasEngine(agent):
                events.append("engine")
                raise LookupError("missing")

        agent = Host()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", TagTrainingWarning)
            with self.assertRaises(TaggingFailure) as raised:
                Vehicle(agent)

        self.assertEqual(events, ["wheels", "engine"])
        self.assertEqual(raised.exception.failed_posts,
                         ("HasWheels", "HasEngine"))
        self.assertEqual(len(raised.exception.failure_texts), 2)
        self.assertEqual([issue.message.name for issue in caught], ["Train"])
        self.assertIn(agent, Vehicle[:])
        self.assertIn(agent, ~Vehicle)

    def test_warning_as_error_does_not_mask_failed_post(self):
        class Vehicle(Tag):
            @Imprint
            def Train(agent):
                raise ValueError("training failed")

            @Post
            def Ready(agent):
                return False

        agent = Host()
        with warnings.catch_warnings():
            warnings.simplefilter("error", TagTrainingWarning)
            with self.assertRaises(TagPostconditionError.Ready):
                Vehicle(agent)

        self.assertIn(agent, Vehicle[:])
        self.assertIn(agent, ~Vehicle)

    def test_warning_as_error_does_not_mask_interruption(self):
        interruption = KeyboardInterrupt("stop")

        class Vehicle(Tag):
            @Imprint
            def Failed(agent):
                raise ValueError("training failed")

            @Imprint
            def Stop(agent):
                raise interruption

        agent = Host()
        with warnings.catch_warnings():
            warnings.simplefilter("error", TagTrainingWarning)
            with self.assertRaises(KeyboardInterrupt) as raised:
                Vehicle(agent)

        self.assertIs(raised.exception, interruption)
        self.assertIn(agent, Vehicle[:])

    def test_reporting_hook_cannot_mask_failed_post(self):
        class Vehicle(Tag):
            @Imprint
            def Train(agent):
                raise ValueError("training failed")

            @Post
            def Ready(agent):
                return False

        def broken_report(*args, **kwargs):
            raise RuntimeError("warning output unavailable")

        agent = Host()
        with warnings.catch_warnings():
            warnings.simplefilter("always", TagTrainingWarning)
            warnings.showwarning = broken_report
            with self.assertRaises(TagPostconditionError.Ready) as raised:
                Vehicle(agent)

        self.assertIn(agent, Vehicle[:])
        self.assertTrue(any("warning output unavailable" in note
                            for note in raised.exception.__notes__))

    def test_later_report_snapshot_failure_keeps_imprint_warning(self):
        class Vehicle(Tag):
            @Public
            @Report
            def status(tag):
                raise LookupError("report snapshot failed")

            @Imprint
            def Train(agent):
                raise ValueError("training failed")

        agent = Host()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", TagTrainingWarning)
            with self.assertRaisesRegex(LookupError, "report snapshot failed"):
                Vehicle(agent)

        self.assertEqual([issue.message.name for issue in caught], ["Train"])
        self.assertIn(agent, Vehicle[:])

    def test_missing_report_snapshot_still_inspects_posts(self):
        events = []

        class Vehicle(Tag):
            @Public
            @Report
            def status(tag):
                return "ready"

            @Imprint
            def Train(agent):
                del Vehicle.status
                raise ValueError("training failed")

            @Post
            def Ready(agent):
                events.append("post")
                return False

        agent = Host()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", TagTrainingWarning)
            with self.assertRaises(TagPostconditionError.Ready) as raised:
                Vehicle(agent)

        self.assertEqual(events, ["post"])
        self.assertEqual([issue.message.name for issue in caught], ["Train"])
        self.assertIn("AttributeError", " ".join(raised.exception.__notes__))
        self.assertIn(agent, Vehicle[:])
        self.assertIn(agent, ~Vehicle)

    def test_invalid_post_verdict_keeps_contract_failure(self):
        class Vehicle(Tag):
            @Imprint
            def Train(agent):
                raise ValueError("training failed")

            @Post
            def Invalid(agent):
                return 1

        agent = Host()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", TagTrainingWarning)
            with self.assertRaises(TagContractError):
                Vehicle(agent)

        self.assertEqual([issue.message.name for issue in caught], ["Train"])
        self.assertIn(agent, Vehicle[:])

    def test_self_referential_post_keeps_contract_failure(self):
        class Vehicle(Tag):
            @Imprint
            def Train(agent):
                raise ValueError("training failed")

            @Post
            def Recursive(agent):
                return agent in Vehicle

        agent = Host()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", TagTrainingWarning)
            with self.assertRaisesRegex(TagContractError, "Tag\\[:\\]"):
                Vehicle(agent)

        self.assertEqual([issue.message.name for issue in caught], ["Train"])
        self.assertIn(agent, Vehicle[:])

    def test_multi_post_diagnostic_does_not_retain_agent(self):
        class Vehicle(Tag):
            @Post
            def First(agent):
                return False

            @Post
            def Second(agent):
                return False

        def tagged():
            agent = Host()
            reference = weakref.ref(agent)
            try:
                Vehicle(agent)
            except TaggingFailure:
                pass
            return reference

        gc.collect()
        was_enabled = gc.isenabled()
        gc.disable()
        try:
            reference = tagged()
            self.assertIsNone(reference())
            self.assertEqual(list(Vehicle[:]), [])
        finally:
            if was_enabled:
                gc.enable()


if __name__ == "__main__":
    unittest.main()
