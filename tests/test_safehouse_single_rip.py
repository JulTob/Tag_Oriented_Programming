"""A failed single-Agent Rip saves its original ordered teardown work."""

from __future__ import annotations

import unittest
from unittest.mock import patch

import TopKit.lifecycle as lifecycle
from TopKit import Action
from TopKit import Rip
from TopKit import Tag
from TopKit import TagArrestedAccessError
from TopKit import TagCompositionError
from TopKit import TagResolutionError
from TopKit.arrest import _safehouse


class Host:
    pass


class SafehouseSingleRipTests(unittest.TestCase):
    def setUp(self) -> None:
        empty_ledger = patch.dict(_safehouse, clear=True)
        empty_ledger.start()
        self.addCleanup(empty_ledger.stop)

    def test_interrupted_revocation_keeps_its_saved_run(self) -> None:
        events = []

        class Guard(Tag):
            @Rip
            def Clean(agent):
                events.append("clean")

        agent = Host()
        Guard(agent)
        original = lifecycle._revoke
        interrupted = False

        def Interrupt(target, state, run):
            nonlocal interrupted
            original(target, state, run)
            if not interrupted:
                interrupted = True
                raise KeyboardInterrupt

        with patch.object(lifecycle, "_revoke", Interrupt):
            with self.assertRaises(KeyboardInterrupt):
                del Guard[agent]

        self.assertNotIn(agent, Guard[:])
        self.assertIn(agent, Guard[...])
        self.assertEqual(events, [])
        self.assertFalse(bool(agent))

        del Tag[agent]
        self.assertEqual(events, ["clean"])
        self.assertNotIn(agent, Tag[...])

    def test_failed_step_stops_later_work_and_retries_its_own_cursor(self) -> None:
        events = []
        ready = False
        original = RuntimeError("not ready")

        class Workshop(Tag):
            @Rip
            def First(agent):
                events.append("first")

            @Rip
            def Verify(agent):
                events.append("verify")
                if not ready:
                    raise original

            @Rip
            def Last(agent):
                events.append("last")

        agent = Host()
        Workshop(agent)

        with self.assertRaises(TagCompositionError) as caught:
            del Workshop[agent]

        self.assertIs(caught.exception.__cause__, original)
        self.assertEqual(events, ["first", "verify"])
        self.assertNotIn(agent, Workshop[:])
        self.assertIn(agent, Workshop[...])
        self.assertFalse(bool(agent))

        ready = True
        del Workshop[agent]
        self.assertEqual(events, ["first", "verify", "verify", "last"])
        self.assertNotIn(agent, Tag[...])
        self.assertTrue(bool(agent))

        with self.assertRaises(TagResolutionError):
            del Workshop[agent]

    def test_ordinary_action_retries_before_running_and_keeps_failure_cause(self) -> None:
        ready = False
        events = []

        class Workshop(Tag):
            @Action
            def Work(agent):
                events.append("work")
                return "done"

            @Rip
            def Leave(agent):
                events.append("rip")
                if not ready:
                    raise RuntimeError("unready")

        agent = Host()
        Workshop(agent)
        captured = agent.Work

        with self.assertRaises(TagCompositionError):
            del Workshop[agent]

        with self.assertRaises(TagArrestedAccessError) as caught:
            captured()

        self.assertIsInstance(caught.exception.__cause__, RuntimeError)
        self.assertEqual(events, ["rip", "rip"])

        ready = True
        self.assertEqual(captured(), "done")
        self.assertEqual(events, ["rip", "rip", "rip", "work"])
        self.assertNotIn(agent, Tag[...])

    def test_other_tag_rip_runs_first_then_retries_older_saved_work(self) -> None:
        ready = False
        events = []

        class Wizard(Tag):
            @Rip
            def Leave_Wizard(agent):
                events.append("wizard")
                if not ready:
                    raise RuntimeError("wait")

        class Fighter(Tag):
            @Rip
            def Leave_Fighter(agent):
                events.append("fighter")

        agent = Host()
        Wizard(agent)
        Fighter(agent)
        with self.assertRaises(TagCompositionError):
            del Wizard[agent]
        with self.assertRaises(TagCompositionError):
            del Fighter[agent]

        self.assertEqual(events, ["wizard", "fighter", "wizard"])
        self.assertNotIn(agent, Fighter[:])
        self.assertIn(agent, Wizard[...])

        ready = True
        del Tag[agent]
        self.assertEqual(events, ["wizard", "fighter", "wizard", "wizard"])

    def test_old_failed_run_keeps_fresh_same_tag_membership(self) -> None:
        events = []
        ready = False

        class Wizard(Tag):
            @Rip
            def Rejoin(agent):
                events.append("rejoin")
                if len(events) == 1:
                    Wizard(agent)

            @Rip
            def Verify(agent):
                events.append("verify")
                if not ready:
                    raise RuntimeError("wait")

        agent = Host()
        Wizard(agent)
        with self.assertRaises(TagCompositionError):
            del Wizard[agent]

        self.assertIn(agent, Wizard[:])
        self.assertIn(agent, Wizard[...])
        self.assertFalse(bool(agent))

        ready = True
        del Wizard[agent]
        self.assertIn(agent, Wizard[:])
        self.assertNotIn(agent, Wizard[...])
        self.assertTrue(bool(agent))
        self.assertEqual(events, ["rejoin", "verify", "verify"])

        del Wizard[agent]
        self.assertNotIn(agent, Wizard[:])

    def test_root_retry_drains_work_added_during_the_retry(self) -> None:
        old_ready = False
        child_ready = False
        events = []

        class Child(Tag):
            @Rip
            def Leave_Child(agent):
                events.append("child")
                if not child_ready:
                    raise RuntimeError("child wait")

        class Old(Tag):
            @Rip
            def Leave_Old(agent):
                events.append("old")
                if not old_ready:
                    raise RuntimeError("old wait")
                Child(agent)
                try:
                    del Child[agent]
                except TagCompositionError:
                    pass

        agent = Host()
        Old(agent)
        with self.assertRaises(TagCompositionError):
            del Old[agent]

        old_ready = True
        with self.assertRaises(TagCompositionError):
            del Tag[agent]
        self.assertEqual(events, ["old", "old", "child", "child"])
        self.assertIn(agent, Child[...])

        child_ready = True
        del Tag[agent]
        self.assertNotIn(agent, Tag[...])

    def test_redefined_same_name_tag_cannot_receive_old_saved_rip(self) -> None:
        ready = False
        events = []

        def Retire(agent):
            events.append("old")
            if not ready:
                raise RuntimeError("wait")

        old = type("Wizard", (Tag,), {"Retire": Rip(Retire)})
        agent = Host()
        old(agent)
        with self.assertRaises(TagCompositionError):
            del old[agent]

        replacement = type("Wizard", (Tag,), {})
        self.assertIn(agent, old[...])
        self.assertNotIn(agent, replacement[...])

        ready = True
        del Tag[agent]
        self.assertEqual(events, ["old", "old"])
        self.assertNotIn(agent, Tag[...])


if __name__ == "__main__":
    unittest.main()
