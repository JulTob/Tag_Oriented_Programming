"""A fresh Tagging starts only from an Agent whose current Posts hold."""

import unittest

from TopKit import Action
from TopKit import Constant
from TopKit import Contract
from TopKit import Imprint
from TopKit import Post
from TopKit import Pre
from TopKit import Tag
from TopKit import TagCompositionError
from TopKit import TagPostconditionError


class Host:
    pass


class SoundSourceTaggingTests(unittest.TestCase):
    def test_independent_tag_refuses_a_broken_agent_before_its_gate_or_gains(self):
        events = []

        class Car(Tag):
            @Post
            def Drives(agent):
                return agent.running

        class Insured(Tag):
            @Pre
            def Eligible(agent):
                events.append("gate")
                return True

            @Action
            def Claim(agent):
                return "claim"

            @Imprint
            def Register(agent):
                events.append("register")

        car = Host()
        car.running = False
        with self.assertRaises(TagPostconditionError.Drives):
            Car(car)

        with self.assertRaisesRegex(
                TagCompositionError,
                "Insured cannot start Tagging while the Agent's current Posts fail",
                ):
            Insured(car)

        self.assertEqual(events, [])
        self.assertNotIn(car, Insured[:])
        self.assertNotIsInstance(car, Insured)
        self.assertFalse("Claim" @ car)
        self.assertIn(car, ~Car)

        car.running = True
        self.assertIs(Insured(car), car)
        self.assertEqual(events, ["gate", "register"])
        self.assertIn(car, Insured)

    def test_broken_active_reapplication_is_still_a_no_op_but_shape_is_refused(self):
        class Candidate(Tag):
            @Post
            def Ready(agent):
                return agent.ready

        class Worker(Candidate):
            @Action
            def Work(agent):
                return "worked"

        candidate = Host()
        candidate.ready = False
        with self.assertRaises(TagPostconditionError.Ready):
            Candidate(candidate)

        self.assertIs(Candidate(candidate), candidate)
        with self.assertRaises(TagCompositionError):
            Worker(candidate)
        self.assertNotIn(candidate, Worker[:])
        self.assertFalse("Work" @ candidate)

        candidate.ready = True
        Worker(candidate)
        self.assertIn(candidate, Worker)

    def test_retained_constant_post_requires_repair_before_same_tag_retry(self):
        class Car(Tag):
            @Constant
            @Post
            def Ready(agent):
                return agent.ready

        car = Host()
        car.ready = True
        Car(car)
        del Car[car]
        car.ready = False

        with self.assertRaises(TagCompositionError):
            Car(car)
        self.assertNotIn(car, Car[:])

        car.ready = True
        Car(car)
        self.assertIn(car, Car)

    def test_a_deliberately_ended_ordinary_post_no_longer_blocks_tagging(self):
        class Promise(Tag):
            @Post
            def Ready(agent):
                return agent.ready

        class Next(Tag):
            pass

        agent = Host()
        agent.ready = False
        with self.assertRaises(TagPostconditionError.Ready):
            Promise(agent)

        Contract.Delete(agent, "Ready")
        self.assertIs(Next(agent), agent)
        self.assertIn(agent, Next)


if __name__ == "__main__":
    unittest.main()
