"""Record builders calculate values without performing TOP state changes."""

import unittest

from TopKit import At_Exit
from TopKit import Contract
from TopKit import Pin
from TopKit import Post
from TopKit import Pre
from TopKit import Record
from TopKit import Tag
from TopKit import TagCompositionError
from TopKit import lifecycle


class Host:
    pass


class ObservationalRecordTests(unittest.TestCase):
    def test_record_reads_an_earlier_action_and_stores_its_return_afterward(self):
        class Prepared(Tag):
            def Double(agent):
                return agent.seed * 2

            @Record
            def score(agent, *, bonus=0):
                return agent.Double() + bonus

            @Record
            def total(agent):
                return agent.score + 1

        agent = Host()
        agent.seed = 3
        Prepared(agent, bonus=4)

        self.assertEqual(agent.score, 10)
        self.assertEqual(agent.total, 11)
        self.assertIn(agent, Prepared[:])

    def test_caught_rip_refuses_later_record_but_keeps_earlier_gain(self):
        class Existing(Tag):
            pass

        class Incomplete(Tag):
            def Look(agent):
                return "earlier Gain"

            @Record
            def start(agent):
                return 7

            @Record
            def result(agent):
                try:
                    del Existing[agent]
                except TagCompositionError:
                    pass
                return "unusable"

        agent = Host()
        Existing(agent)

        with self.assertRaises(TagCompositionError) as caught:
            Incomplete(agent)

        self.assertIn("Record Incomplete.result builder", str(caught.exception))
        self.assertIn("Rip a Tag", str(caught.exception))
        self.assertIn(agent, Existing[:])
        self.assertNotIn(agent, Incomplete[:])
        self.assertEqual(agent.Look(), "earlier Gain")
        self.assertEqual(agent.start, 7)
        self.assertFalse("result" @ agent)

    def test_record_and_pin_record_cannot_tag_another_target(self):
        class Changed(Tag):
            pass

        other = Host()

        class Ordinary(Tag):
            @Record
            def result(agent):
                Changed(other)
                return 1

        @Pin
        class Pinned(Tag):
            @Record
            def result(tag):
                try:
                    Changed(other)
                except TagCompositionError:
                    pass
                return 2

        class Target(Tag):
            pass

        with self.assertRaises(TagCompositionError):
            Ordinary(Host())
        with self.assertRaises(TagCompositionError) as caught:
            Pinned(Target)

        self.assertIn("Record Pinned.result builder", str(caught.exception))
        self.assertNotIn(other, Changed[:])
        self.assertNotIn(Target, Pinned[:])

    def test_action_called_by_record_cannot_mutate_then_hide_refusal(self):
        class Changed(Tag):
            pass

        other = Host()

        class Incomplete(Tag):
            def Try_Tag(agent):
                Changed(other)

            @Record
            def result(agent):
                try:
                    agent.Try_Tag()
                except TagCompositionError:
                    pass
                return "unusable"

        agent = Host()
        with self.assertRaises(TagCompositionError) as caught:
            Incomplete(agent)

        self.assertIn("Record Incomplete.result builder", str(caught.exception))
        self.assertNotIn(other, Changed[:])
        self.assertNotIn(agent, Incomplete[:])
        self.assertFalse("result" @ agent)

    def test_exception_rendering_cannot_tag_after_builder_raises(self):
        class Changed(Tag):
            pass

        other = Host()

        class HostileError(ValueError):
            def __str__(self):
                Changed(other)
                return "hostile text"

        class Incomplete(Tag):
            @Record
            def result(agent):
                raise HostileError()

        agent = Host()
        with self.assertRaises(TagCompositionError) as caught:
            Incomplete(agent)

        self.assertIn("Record Incomplete.result builder", str(caught.exception))
        self.assertNotIn(other, Changed[:])
        self.assertNotIn(agent, Incomplete[:])

    def test_interruption_after_caught_mutation_keeps_the_interruption(self):
        class Changed(Tag):
            pass

        other = Host()

        for interruption in (KeyboardInterrupt("stop"), SystemExit("stop")):
            with self.subTest(interruption=type(interruption).__name__):
                class Incomplete(Tag):
                    @Record
                    def result(agent):
                        try:
                            Changed(other)
                        except TagCompositionError:
                            pass
                        raise interruption

                agent = Host()
                with self.assertRaises(type(interruption)) as caught:
                    Incomplete(agent)

                self.assertIs(caught.exception, interruption)
                self.assertNotIn(other, Changed[:])
                self.assertNotIn(agent, Incomplete[:])

    def test_record_cannot_delete_contract_change_tag_or_register_exit_work(self):
        class Existing(Tag):
            label = "original"

            @Post
            def Ready(agent):
                return True

        class Incomplete(Tag):
            @Record
            def result(agent):
                for change in (
                        lambda: Contract.Delete(agent, "Ready"),
                        lambda: setattr(Existing, "label", "changed"),
                        lambda: At_Exit(agent),
                        ):
                    try:
                        change()
                    except TagCompositionError:
                        pass
                return 1

        agent = Host()
        Existing(agent)
        exits = lifecycle._exit_count

        with self.assertRaises(TagCompositionError):
            Incomplete(agent)

        self.assertEqual(Contract.Status(agent), {"Ready": True})
        self.assertEqual(Existing.label, "original")
        self.assertEqual(lifecycle._exit_count, exits)

    def test_nested_precondition_read_shares_record_observation(self):
        class Existing(Tag):
            @Pre
            def Ready(agent):
                if agent.attempt:
                    try:
                        del Existing[agent]
                    except TagCompositionError:
                        pass
                return True

        class Incomplete(Tag):
            @Record
            def result(agent):
                try:
                    Contract.Preconditions(agent)
                except Exception:
                    pass
                return 1

        agent = Host()
        agent.attempt = False
        Existing(agent)
        agent.attempt = True

        with self.assertRaises(TagCompositionError) as caught:
            Incomplete(agent)

        self.assertIn("Record Incomplete.result builder", str(caught.exception))
        self.assertIn(agent, Existing[:])
        self.assertNotIn(agent, Incomplete[:])


if __name__ == "__main__":
    unittest.main()
