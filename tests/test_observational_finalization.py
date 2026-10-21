"""Python finalization has separate cleanup from the active observation."""

import gc
import unittest
import weakref

from TopKit import Contract, Post, Record, Rip, Tag


class Host:
    pass


class ObservationalFinalizationTests(unittest.TestCase):

    def test_unrelated_agent_finalization_does_not_poison_record_calculation(self):
        calls = []

        class Reclaimed(Tag):
            @Post
            def Ready(target):
                return True

            @Rip
            def Clear(target):
                Contract.Delete(target, "Ready")
                calls.append("cleaned")

        class Prepared(Tag):
            @Record
            def position(target):
                gc.collect()
                return "belt"

        enabled = gc.isenabled()
        gc.disable()
        self.addCleanup(gc.enable if enabled else gc.disable)
        discarded = Host()
        discarded.cycle = discarded
        Reclaimed(discarded)
        reference = weakref.ref(discarded)
        del discarded

        target = Host()
        Prepared(target)
        self.assertEqual(target.position, "belt")
        self.assertEqual(calls, ["cleaned"])
        self.assertIsNone(reference())

    def test_unrelated_finalization_does_not_poison_post_or_disable_its_guard(self):
        calls = []
        other = Host()

        class Changed(Tag):
            pass

        class Reclaimed(Tag):
            @Post
            def Ready(target):
                return True

            @Rip
            def Clear(target):
                Contract.Delete(target, "Ready")
                calls.append("cleaned")

        class Checked(Tag):
            @Post
            def Ready(target):
                if target.collect:
                    gc.collect()
                if target.change:
                    Changed(other)
                return True

        target = Host()
        target.collect = target.change = False
        Checked(target)
        enabled = gc.isenabled()
        gc.disable()
        self.addCleanup(gc.enable if enabled else gc.disable)
        discarded = Host()
        discarded.cycle = discarded
        Reclaimed(discarded)
        reference = weakref.ref(discarded)
        del discarded

        target.collect = True
        self.assertTrue(bool(target))
        self.assertEqual(calls, ["cleaned"])
        self.assertIsNone(reference())
        target.change = True
        self.assertFalse(bool(target))
        self.assertNotIn(other, Changed[:])


if __name__ == "__main__":
    unittest.main()
