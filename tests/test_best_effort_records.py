"""A failed Record calculation remains one failed training step."""

import gc
import unittest
import warnings
import weakref

from TopKit import (Constant, Imprint, Pin, Post, Record, Rip, Tag,
                    TagCompositionError, TagPostconditionError,
                    TagTrainingWarning, Tool)


class Host:
    pass


class BestEffortRecordTests(unittest.TestCase):
    def test_failed_record_keeps_prior_value_and_later_training_runs(self):
        events = []

        class Before(Tag):
            @Record
            def wheels(agent):
                return 3

        class Car(Tag):
            @Record
            def wheels(agent, stored):
                events.append(("wheels", stored))
                raise ValueError("no fourth wheel")

            @Record
            def observed(agent):
                events.append(("observed", agent.wheels))
                return agent.wheels

            @Imprint
            def Paint(agent):
                events.append("paint")

            @Post
            def Counted(agent):
                return agent.observed == 3

        agent = Host()
        Before(agent)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", TagTrainingWarning)
            self.assertIs(Car(agent), agent)

        self.assertEqual(events, [("wheels", 3), ("observed", 3), "paint"])
        self.assertIn(agent, Car)
        self.assertEqual(agent.wheels, 3)
        self.assertEqual(agent.observed, 3)
        self.assertEqual([item.message.name for item in caught], ["wheels"])
        self.assertEqual(caught[0].message.kind, "Record")
        self.assertEqual(caught[0].message.cause_type, "ValueError")

    def test_failed_constant_record_locks_no_binding(self):
        class Given(Tag):
            @Constant
            @Record
            def value(agent):
                raise ValueError("unavailable")

        class Later(Tag):
            @Record
            def value(agent):
                return 7

        agent = Host()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", TagTrainingWarning)
            Given(agent)
        self.assertEqual(len(caught), 1)
        self.assertFalse("value" @ agent)
        Later(agent)
        self.assertEqual(agent.value, 7)

    def test_invalid_tool_value_warns_and_post_judges_missing_slot(self):
        class Weapon(Tag):
            pass

        class Fighter(Tag):
            @Tool(Weapon)
            def weapon(agent):
                return object()

            @Post
            def Armed(agent):
                return "weapon" @ agent

        agent = Host()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", TagTrainingWarning)
            with self.assertRaises(TagPostconditionError.Armed):
                Fighter(agent)

        self.assertIn(agent, Fighter[:])
        self.assertNotIn(agent, Fighter)
        self.assertFalse("weapon" @ agent)
        self.assertEqual([item.message.name for item in caught], ["weapon"])
        self.assertIn("could not be applied", str(caught[0].message.failure))
        self.assertIsInstance(caught[0].message.failure, TagCompositionError)

    def test_failed_value_write_restores_previous_record_and_later_gain_runs(self):
        class RefusingDict(dict):
            refuse = False

            def __setitem__(self, name, value):
                super().__setitem__(name, value)
                if name == "value" and self.refuse:
                    raise ValueError("value write refused after partial binding")

        class Before(Tag):
            @Record
            def value(agent):
                return 4

        class After(Tag):
            @Record
            def value(agent, stored):
                return stored + 1

            @Record
            def seen(agent):
                return agent.value

        agent = Host()
        agent.__dict__ = RefusingDict()
        Before(agent)
        agent.__dict__.refuse = True
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", TagTrainingWarning)
            After(agent)

        training = [item.message for item in caught
                    if isinstance(item.message, TagTrainingWarning)]
        self.assertEqual([item.name for item in training], ["value"])
        self.assertIn("could not be applied", str(training[0].failure))
        self.assertIn(agent, After[:])
        self.assertEqual(agent.value, 4)
        self.assertEqual(agent.seen, 4)

    def test_pinned_record_builder_failure_still_admits_tag(self):
        class Receiver(Tag):
            pass

        class Controller(Tag):
            @Record
            def missing(tag):
                raise RuntimeError("no signal")

            @Record
            def available(tag):
                return 5

        Controller = Pin(Controller)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", TagTrainingWarning)
            Controller(Receiver)

        self.assertIn(Receiver, Controller[:])
        self.assertEqual(Receiver.available, 5)
        self.assertFalse("missing" @ Receiver)
        self.assertEqual([item.message.name for item in caught], ["missing"])

    def test_failed_records_and_imprint_warn_in_training_order_before_post_error(self):
        class Car(Tag):
            @Post
            def Ready(agent):
                return False

            @Record
            def wheels(agent):
                raise ValueError("wheels")

            @Record
            def engine(agent):
                raise RuntimeError("engine")

            @Imprint
            def Paint(agent):
                raise OSError("paint")

        agent = Host()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", TagTrainingWarning)
            with self.assertRaises(TagPostconditionError.Ready):
                Car(agent)

        self.assertEqual([item.message.name for item in caught],
                         ["wheels", "engine", "Paint"])
        self.assertIn(agent, Car[:])

    def test_warnings_as_errors_do_not_mask_a_failed_post(self):
        class Car(Tag):
            @Post
            def Ready(agent):
                return False

            @Record
            def wheels(agent):
                raise ValueError("wheels")

        agent = Host()
        with warnings.catch_warnings():
            warnings.simplefilter("error", TagTrainingWarning)
            with self.assertRaises(TagPostconditionError.Ready):
                Car(agent)
        self.assertIn(agent, Car[:])

    def test_record_interruption_stops_later_training_but_admits(self):
        interruption = KeyboardInterrupt("stop")
        events = []

        class Car(Tag):
            @Post
            def Has_Frame(agent):
                events.append("post")
                return agent.frame == "frame"

            @Record
            def frame(agent):
                return "frame"

            @Record
            def wheels(agent):
                raise interruption

            @Record
            def paint(agent):
                events.append("paint")
                return "red"

            @Imprint
            def Train(agent):
                events.append("imprint")

        agent = Host()
        with self.assertRaises(KeyboardInterrupt) as caught:
            Car(agent)
        self.assertIs(caught.exception, interruption)
        self.assertEqual(events, ["post"])
        self.assertIn(agent, Car[:])
        self.assertEqual(agent.frame, "frame")
        self.assertFalse("wheels" @ agent)
        self.assertFalse("paint" @ agent)

    def test_interruption_before_rip_declaration_saves_no_unacquired_teardown(self):
        interruption = KeyboardInterrupt("stop")
        events = []

        class Car(Tag):
            @Record
            def wheels(agent):
                raise interruption

            @Rip
            def Clean(agent):
                events.append("clean")

        agent = Host()
        with self.assertRaises(KeyboardInterrupt) as caught:
            Car(agent)
        self.assertIs(caught.exception, interruption)
        self.assertIn(agent, Car[:])
        del Car[agent]
        self.assertEqual(events, [])

    def test_retag_interruption_does_not_reuse_the_previous_rip(self):
        interruption = KeyboardInterrupt("stop again")
        events = []
        attempts = []

        class Car(Tag):
            @Record
            def wheels(agent):
                attempts.append(1)
                if len(attempts) == 2:
                    raise interruption
                return 4

            @Rip
            def Clean(agent):
                events.append("clean")

        agent = Host()
        Car(agent)
        del Car[agent]
        self.assertEqual(events, ["clean"])

        with self.assertRaises(KeyboardInterrupt) as caught:
            Car(agent)
        self.assertIs(caught.exception, interruption)
        self.assertIn(agent, Car[:])
        del Car[agent]
        self.assertEqual(events, ["clean"])

    def test_caught_warning_does_not_keep_agent_alive(self):
        class Car(Tag):
            @Record
            def wheels(agent):
                raise ValueError("failed")

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", TagTrainingWarning)
            agent = Host()
            Car(agent)
        reference = weakref.ref(agent)
        del agent
        self.assertIsNone(reference())
        gc.collect()
        self.assertEqual(len(caught), 1)


if __name__ == "__main__":
    unittest.main()
