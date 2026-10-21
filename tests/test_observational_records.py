"""Record initialization reads current Gains without performing TOP acts."""

from contextvars import copy_context
import unittest

from TopKit import (Action, Contract, Pin, Post, Record, Tag,
                    TagCompositionError, Tool)


class Host:
    pass


class ObservationalRecordTests(unittest.TestCase):

    def test_records_read_preceding_actions_and_records(self):
        class Prepared(Tag):
            @Action
            def Double(target):
                return target.seed * 2

            @Record
            def score(target, *, bonus=0):
                return target.Double() + bonus

            @Record
            def total(target):
                return target.score + 1

        target = Host()
        target.seed = 3
        Prepared(target, bonus=4)
        self.assertEqual(target.score, 10)
        self.assertEqual(target.total, 11)
        self.assertIn(target, Prepared[:])

    def test_caught_rip_fails_record_without_losing_existing_membership(self):
        class Existing(Tag):
            pass

        class Incomplete(Tag):
            @Record
            def start(target):
                return 7

            @Record
            def result(target):
                try:
                    del Existing[target]
                except TagCompositionError:
                    pass
                return "unusable"

        target = Host()
        Existing(target)
        with self.assertRaises(TagCompositionError) as refusal:
            Incomplete(target)
        self.assertIn("Incomplete.result", str(refusal.exception))
        self.assertIn(target, Existing[:])
        self.assertNotIn(target, Incomplete[:])
        self.assertEqual(target.start, 7)
        self.assertFalse("result" @ target)

    def test_ordinary_and_pin_records_cannot_tag_another_target(self):
        other = Host()

        class Changed(Tag):
            pass

        class Ordinary(Tag):
            @Record
            def result(target):
                Changed(other)
                return 1

        class Pinned(Pin):
            @Record
            def result(target):
                try:
                    Changed(other)
                except TagCompositionError:
                    pass
                return 2

        class Target(Tag):
            pass

        with self.assertRaises(TagCompositionError):
            Ordinary(Host())
        with self.assertRaises(TagCompositionError):
            Pinned(Target)
        self.assertNotIn(other, Changed[:])
        self.assertNotIn(Target, Pinned[:])

    def test_called_action_cannot_mutate_then_hide_the_refusal(self):
        other = Host()

        class Changed(Tag):
            pass

        class Incomplete(Tag):
            @Action
            def Try_Tag(target):
                Changed(other)

            @Record
            def result(target):
                try:
                    target.Try_Tag()
                except TagCompositionError:
                    pass
                return "unusable"

        target = Host()
        with self.assertRaises(TagCompositionError):
            Incomplete(target)
        self.assertNotIn(other, Changed[:])
        self.assertFalse("result" @ target)
        self.assertTrue("Try_Tag" @ target)

    def test_record_cannot_delete_a_contract(self):
        class Existing(Tag):
            @Post
            def Ready(target):
                return True

        class Incomplete(Tag):
            @Record
            def result(target):
                try:
                    Contract.Delete(target, "Ready")
                except TagCompositionError:
                    pass
                return 1

        target = Host()
        Existing(target)
        with self.assertRaises(TagCompositionError):
            Incomplete(target)
        self.assertEqual(Contract.Status(target), {"Ready": True})

    def test_exception_rendering_remains_inside_the_record_observation(self):
        other = Host()

        class Changed(Tag):
            pass

        class HostileError(ValueError):
            def __str__(self):
                Changed(other)
                return "hostile text"

        class Incomplete(Tag):
            @Record
            def result(target):
                raise HostileError()

        with self.assertRaises(TagCompositionError) as refusal:
            Incomplete(Host())
        self.assertIn("Incomplete.result", str(refusal.exception))
        self.assertNotIn(other, Changed[:])

    def test_tool_value_validation_cannot_change_another_field(self):
        other = Host()

        class Changed(Tag):
            pass

        class Weapon:
            pass

        class Invalid:
            def __repr__(self):
                Changed(other)
                return "not a weapon"

        class Equipped(Tag):
            @Tool(Weapon)
            def weapon(target):
                return Invalid()

        target = Host()
        with self.assertRaises(TagCompositionError):
            Equipped(target)
        self.assertNotIn(other, Changed[:])
        self.assertFalse("weapon" @ target)

    def test_saved_context_is_not_read_only_after_the_record_returns(self):
        saved = []

        class Changed(Tag):
            pass

        class Prepared(Tag):
            @Record
            def score(target):
                saved.append(copy_context())
                return 7

        target, other = Host(), Host()
        Prepared(target)
        saved[0].run(Changed, other)
        self.assertIn(other, Changed[:])
        self.assertEqual(target.score, 7)

    def test_python_writes_are_the_authors_responsibility(self):
        class Prepared(Tag):
            @Record
            def score(target):
                target.note = "ordinary Python effect"
                return 7

        target = Host()
        Prepared(target)
        self.assertEqual(target.score, 7)
        self.assertEqual(target.note, "ordinary Python effect")


if __name__ == "__main__":
    unittest.main()
