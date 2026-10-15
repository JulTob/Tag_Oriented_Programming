"""A failed single-Agent Rip saves its original ordered teardown work."""

from __future__ import annotations

import unittest
from unittest.mock import patch

import TopKit.lifecycle as lifecycle
import TopKit.transactions as transactions
from TopKit import Action
from TopKit import Rip
from TopKit import Tag
from TopKit import TagArrestedAccessError
from TopKit import TagCompositionError
from TopKit import TagResolutionError
from TopKit.arrest import _safehouse
from TopKit.fields import _field_of
from TopKit.state import _state_of


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

    def test_retry_after_interrupted_revocation_keeps_fresh_membership(self) -> None:
        events = []

        class Guard(Tag):
            @Rip
            def Clean(agent):
                events.append("clean")

        agent = Host()
        Guard(agent)
        state = _state_of(agent)
        old_rips = state.rips[Guard]
        old_snapshot = state.snapshots[Guard]
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

        Guard(agent)   # a new application after the old Field was removed
        fresh_rips = state.rips[Guard]
        fresh_snapshot = state.snapshots[Guard]
        self.assertIsNot(fresh_rips, old_rips)
        self.assertIsNot(fresh_snapshot, old_snapshot)
        self.assertIn(agent, Guard[:])
        del Tag[agent]
        self.assertEqual(events, ["clean"])
        self.assertIn(agent, Guard[:])
        self.assertIs(state.rips[Guard], fresh_rips)
        self.assertIs(state.snapshots[Guard], fresh_snapshot)
        self.assertNotIn(agent, Tag[...])

        del Guard[agent]
        self.assertEqual(events, ["clean", "clean"])

    def test_interrupt_before_or_after_field_removal_keeps_old_application(self) -> None:
        for after_field_removal in (False, True):
            with self.subTest(after_field_removal=after_field_removal):
                events = []

                class Guard(Tag):
                    @Rip
                    def Clean(agent):
                        events.append("clean")

                agent = Host()
                Guard(agent)
                state = _state_of(agent)
                old_rips = state.rips[Guard]
                old_snapshot = state.snapshots[Guard]
                field = _field_of(Guard)
                remove = field._Remove
                interrupted = False

                def Interrupt(target):
                    nonlocal interrupted
                    if after_field_removal:
                        remove(target)
                    if not interrupted:
                        interrupted = True
                        raise KeyboardInterrupt
                    if not after_field_removal:
                        remove(target)

                with patch.object(field, "_Remove", Interrupt):
                    with self.assertRaises(KeyboardInterrupt):
                        del Guard[agent]

                self.assertEqual(agent in Guard[:], not after_field_removal)
                self.assertIn(Guard, state.active)
                self.assertIs(state.rips[Guard], old_rips)
                self.assertIs(state.snapshots[Guard], old_snapshot)
                self.assertIn(agent, Guard[...])

                # An active old application still makes this Tagging a
                # no-op; the old run may safely finish its removal.
                Guard(agent)
                self.assertIs(state.rips[Guard], old_rips)
                del Tag[agent]
                self.assertEqual(events, ["clean"])
                self.assertNotIn(agent, Guard[:])
                self.assertNotIn(Guard, state.active)
                self.assertNotIn(Guard, state.rips)
                self.assertNotIn(Guard, state.snapshots)

    def test_interrupt_after_active_removal_preserves_fresh_application(self) -> None:
        events = []

        class Guard(Tag):
            @Rip
            def Clean(agent):
                events.append("clean")

        class InterruptingActive(list):
            interrupted = False

            def pop(self, index=-1):
                result = super().pop(index)
                if not self.interrupted:
                    self.interrupted = True
                    raise KeyboardInterrupt
                return result

        agent = Host()
        Guard(agent)
        state = _state_of(agent)
        old_rips = state.rips[Guard]
        old_snapshot = state.snapshots[Guard]
        state.active = InterruptingActive(state.active)

        with self.assertRaises(KeyboardInterrupt):
            del Guard[agent]

        self.assertNotIn(agent, Guard[:])
        self.assertNotIn(Guard, state.active)
        self.assertIs(state.rips[Guard], old_rips)
        self.assertIs(state.snapshots[Guard], old_snapshot)
        self.assertIn(agent, Guard[...])

        Guard(agent)
        fresh_rips = state.rips[Guard]
        fresh_snapshot = state.snapshots[Guard]
        self.assertIsNot(fresh_rips, old_rips)
        self.assertIsNot(fresh_snapshot, old_snapshot)
        self.assertIn(agent, Guard[:])

        del Tag[agent]
        self.assertEqual(events, ["clean"])
        self.assertIn(agent, Guard[:])
        self.assertIs(state.rips[Guard], fresh_rips)
        self.assertIs(state.snapshots[Guard], fresh_snapshot)
        self.assertNotIn(agent, Tag[...])

    def test_rip_tuple_identity_is_fresh_for_same_callbacks(self) -> None:
        class Guard(Tag):
            @Rip
            def Clean(agent):
                pass

        agent = Host()
        Guard(agent)
        state = _state_of(agent)
        first = state.rips[Guard]
        del Guard[agent]
        Guard(agent)
        self.assertIsNot(state.rips[Guard], first)
        self.assertEqual(state.rips[Guard], first)

    def test_no_rip_tag_has_no_saved_application(self) -> None:
        class Plain(Tag):
            pass

        agent = Host()
        Plain(agent)
        state = _state_of(agent)
        self.assertNotIn(Plain, state.rips)
        self.assertIn(Plain, state.no_rip_applications)
        del Plain[agent]
        self.assertNotIn(agent, Plain[:])
        self.assertNotIn(agent, Tag[...])
        self.assertNotIn(Plain, state.no_rip_applications)
        Plain(agent)
        self.assertIn(agent, Plain[:])
        self.assertNotIn(Plain, state.rips)

    def test_no_rip_interrupted_field_removal_is_saved_for_retry(self) -> None:
        for remove_first in (False, True):
            with self.subTest(remove_first=remove_first):
                class Plain(Tag):
                    pass

                agent = Host()
                Plain(agent)
                state = _state_of(agent)
                field = _field_of(Plain)
                remove = field._Remove
                interrupted = False

                def Interrupt(target):
                    nonlocal interrupted
                    if remove_first:
                        remove(target)
                    if not interrupted:
                        interrupted = True
                        raise KeyboardInterrupt
                    if not remove_first:
                        remove(target)

                with patch.object(field, "_Remove", Interrupt):
                    with self.assertRaises(KeyboardInterrupt):
                        del Plain[agent]

                self.assertEqual(agent in Plain[:], not remove_first)
                self.assertIn(Plain, state.active)
                self.assertIn(agent, Plain[...])
                self.assertFalse(bool(agent))

                # The old admission still blocks another Tagging until its
                # interrupted revocation is completed.
                Plain(agent)
                self.assertEqual(agent in Plain[:], not remove_first)
                del Plain[agent]
                self.assertNotIn(Plain, state.active)
                self.assertNotIn(agent, Plain[:])
                self.assertNotIn(agent, Plain[...])

                Plain(agent)
                self.assertIn(agent, Plain[:])

    def test_no_rip_retry_keeps_new_tagging_after_active_removal(self) -> None:
        class Plain(Tag):
            pass

        class InterruptingActive(list):
            interrupted = False

            def remove(self, tag):
                result = super().remove(tag)
                if not self.interrupted:
                    self.interrupted = True
                    raise KeyboardInterrupt
                return result

        agent = Host()
        Plain(agent)
        state = _state_of(agent)
        old_snapshot = state.snapshots[Plain]
        state.active = InterruptingActive(state.active)

        with self.assertRaises(KeyboardInterrupt):
            del Plain[agent]

        self.assertNotIn(agent, Plain[:])
        self.assertNotIn(Plain, state.active)
        self.assertIn(agent, Plain[...])

        Plain(agent)
        fresh_snapshot = state.snapshots[Plain]
        self.assertIsNot(fresh_snapshot, old_snapshot)
        self.assertIn(agent, Plain[:])

        del Plain[agent]
        self.assertIn(agent, Plain[:])
        self.assertIs(state.snapshots[Plain], fresh_snapshot)
        self.assertNotIn(agent, Plain[...])

    def test_no_rip_retry_keeps_fresh_admission_without_either_snapshot(self) -> None:
        class Plain(Tag):
            pass

        class InterruptingActive(list):
            interrupted = False

            def remove(self, tag):
                super().remove(tag)
                if not self.interrupted:
                    self.interrupted = True
                    raise KeyboardInterrupt

        agent = Host()
        with patch.object(transactions, "_snapshot", side_effect=RuntimeError("view")):
            with self.assertRaisesRegex(RuntimeError, "view"):
                Plain(agent)

            state = _state_of(agent)
            old_application = state.no_rip_applications[Plain]
            self.assertNotIn(Plain, state.snapshots)
            self.assertIn(agent, Plain[:])
            state.active = InterruptingActive(state.active)

            with self.assertRaises(KeyboardInterrupt):
                del Plain[agent]

            self.assertIn(agent, Plain[...])
            self.assertNotIn(agent, Plain[:])
            with self.assertRaisesRegex(RuntimeError, "view"):
                Plain(agent)

        self.assertNotIn(Plain, state.snapshots)
        self.assertIsNot(state.no_rip_applications[Plain], old_application)
        self.assertIn(agent, Plain[:])

        del Tag[agent]
        self.assertIn(agent, Plain[:])
        self.assertNotIn(agent, Plain[...])

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

    def test_rip_may_run_another_tags_rip_before_it_finishes(self) -> None:
        events = []

        class Fighter(Tag):
            @Rip
            def Leave_Fighter(agent):
                events.append("fighter")

        class Wizard(Tag):
            @Rip
            def Leave_Wizard(agent):
                events.append("wizard start")
                del Fighter[agent]
                events.append("wizard end")

        agent = Host()
        Fighter(agent)
        Wizard(agent)
        del Wizard[agent]

        self.assertEqual(events, ["wizard start", "fighter", "wizard end"])
        self.assertNotIn(agent, Tag[...])
        self.assertNotIn(agent, Wizard[:])
        self.assertNotIn(agent, Fighter[:])

    def test_root_retry_requested_inside_own_rip_defers_its_current_step(self) -> None:
        events = []

        class Wizard(Tag):
            @Rip
            def Leave(agent):
                events.append("enter")
                del Tag[agent]
                events.append("return")

        agent = Host()
        Wizard(agent)
        del Wizard[agent]
        self.assertEqual(events, ["enter", "return"])
        self.assertNotIn(agent, Tag[...])

    def test_nested_rip_failure_keeps_original_cause_and_retries(self) -> None:
        ready = False
        events = []
        original = ValueError("fighter not ready")

        class Fighter(Tag):
            @Rip
            def Leave_Fighter(agent):
                events.append("fighter")
                if not ready:
                    raise original

        class Wizard(Tag):
            @Rip
            def Leave_Wizard(agent):
                events.append("wizard")
                del Fighter[agent]

        agent = Host()
        Fighter(agent)
        Wizard(agent)
        with self.assertRaises(TagCompositionError) as caught:
            del Wizard[agent]

        self.assertIs(caught.exception.__cause__.__cause__, original)
        self.assertEqual(events, ["wizard", "fighter"])
        self.assertIn(agent, Wizard[...])
        self.assertIn(agent, Fighter[...])

        ready = True
        del Tag[agent]
        self.assertEqual(events, ["wizard", "fighter", "wizard", "fighter"])
        self.assertNotIn(agent, Tag[...])

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
        state = _state_of(agent)
        first_rips = state.rips[Wizard]
        with self.assertRaises(TagCompositionError):
            del Wizard[agent]

        self.assertIsNot(state.rips[Wizard], first_rips)
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
