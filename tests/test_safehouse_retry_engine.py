"""The private Rip ledger resumes original work without public Rip routing."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from TopKit import TagCompositionError
from TopKit import TagResolutionError
from TopKit.arrest import _arrest_of
from TopKit.arrest import _may_act
from TopKit.arrest import _safehouse
from TopKit.fields import _Safehouse
from TopKit.rip_runs import _RipRun
from TopKit.rip_runs import _finish_run
from TopKit.rip_runs import _pending_run
from TopKit.rip_runs import _retry_arrested
from TopKit.rip_runs import _save_run


class SafehouseRetryEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        empty_ledger = patch.dict(_safehouse, clear=True)
        empty_ledger.start()
        self.addCleanup(empty_ledger.stop)

    @staticmethod
    def _retry(agent, invoke, revoke=None):
        return _retry_arrested(
                agent,
                revoke or (lambda run: None),
                invoke,
                )

    def test_no_saved_work_is_a_resolution_failure(self) -> None:
        with self.assertRaisesRegex(TagResolutionError, "no saved Rip work"):
            self._retry(object(), lambda run, name, teardown: None)

    def test_ledger_uses_agent_and_tag_identity_without_host_protocols(self) -> None:
        class Host:
            def __hash__(self):
                raise AssertionError("host hash ran")

            def __eq__(self, other):
                raise AssertionError("host equality ran")

            def __repr__(self):
                raise AssertionError("host display ran")

        old_tag = type("Wizard", (), {})
        new_tag = type("Wizard", (), {})
        first, second = Host(), Host()
        first_run = _RipRun(old_tag, (("first", object()),))
        second_run = _RipRun(new_tag, (("second", object()),))

        _save_run(first, first_run)
        _save_run(second, second_run)

        self.assertIs(_pending_run(first, old_tag), first_run)
        self.assertIsNone(_pending_run(first, new_tag))
        self.assertIs(_pending_run(second, new_tag), second_run)
        self.assertIn(first, _Safehouse(old_tag))
        self.assertNotIn(second, _Safehouse(old_tag))

        _finish_run(first, second_run)  # another Agent's run cannot be removed
        self.assertIs(_pending_run(first, old_tag), first_run)
        _finish_run(first, first_run)
        self.assertIsNone(_arrest_of(first))
        self.assertIs(_pending_run(second, new_tag), second_run)

    def test_first_run_exists_before_its_arrest_entry_is_published(self) -> None:
        agent = object()
        run = _RipRun(type("Tag", (), {}), (("one", object()),))
        observed = []

        class PublishingLedger(dict):
            def __setitem__(self, key, entry):
                observed.append(("before", len(entry.runs)))
                if not entry.runs:
                    raise AssertionError("published an arrest without Rip work")
                super().__setitem__(key, entry)
                observed.append(("after", _arrest_of(agent, self) is entry))

        ledger = PublishingLedger()

        with patch("TopKit.rip_runs._safehouse", ledger):
            _save_run(agent, run)
            self.assertIs(_arrest_of(agent, ledger).runs[0], run)

        self.assertEqual(observed, [("before", 1), ("after", True)])

    def test_first_failure_saves_original_suffix_and_preserves_cause(self) -> None:
        agent = object()
        tag = type("Wizard", (), {})
        steps: list[str] = []
        failed = False
        run = _RipRun(tag, tuple((name, object()) for name in ("a", "b", "c")))
        _save_run(agent, run)

        def Invoke(current, name, teardown):
            nonlocal failed
            self.assertIs(current, run)
            self.assertTrue(_may_act(agent))
            steps.append(name)
            if name == "b" and not failed:
                failed = True
                raise ValueError("unsafe")

        with self.assertRaisesRegex(TagCompositionError, "Wizard teardown failed in: b") as caught:
            self._retry(agent, Invoke)

        self.assertIsInstance(caught.exception.__cause__, ValueError)
        self.assertEqual(run.cursor, 1)
        self.assertIs(_pending_run(agent, tag), run)
        self.assertFalse(_may_act(agent))
        self.assertEqual(steps, ["a", "b"])

        self.assertIs(self._retry(agent, Invoke), agent)
        self.assertEqual(steps, ["a", "b", "b", "c"])
        self.assertIsNone(_arrest_of(agent))
        self.assertEqual(list(_Safehouse(None)), [])

    def test_hostile_tag_name_cannot_hide_teardown_cause_or_reentry(self) -> None:
        class Hostile(type):
            @property
            def __name__(cls):
                raise RuntimeError("hostile name descriptor")

            def __getattribute__(cls, name):
                if name == "__name__":
                    raise RuntimeError("hostile name getter")
                return super().__getattribute__(name)

        tag = Hostile("Wizard", (), {})
        agent = object()
        run = _RipRun(tag, (("Stop", object()),))
        _save_run(agent, run)
        original = ValueError("original teardown failure")

        def Fail(current, name, teardown):
            raise original

        with self.assertRaisesRegex(TagCompositionError, "Wizard teardown failed in: Stop") as caught:
            self._retry(agent, Fail)

        self.assertIs(caught.exception.__cause__, original)
        self.assertIs(_pending_run(agent, tag), run)

        run.running = True
        with self.assertRaisesRegex(TagCompositionError, "Wizard teardown is already running"):
            self._retry(agent, Fail)

    def test_retry_drains_new_saved_runs_in_live_order(self) -> None:
        agent = object()
        first = _RipRun(type("First", (), {}), (("first", object()),))
        new = _RipRun(type("New", (), {}), (("new", object()),))
        second = _RipRun(type("Second", (), {}), (("second", object()),))
        for run in (first, second):
            _save_run(agent, run)
        visited = []
        revoked = []

        def Revoke(run):
            revoked.append(run.tag.__name__)

        def Invoke(run, name, teardown):
            visited.append(name)
            if run is first:
                _save_run(agent, new)

        self._retry(agent, Invoke, Revoke)

        self.assertEqual(visited, ["first", "second", "new"])
        self.assertEqual(revoked, ["First", "Second", "New"])
        self.assertIsNone(_arrest_of(agent))

    def test_failed_revocation_prevents_teardown_and_is_retried(self) -> None:
        agent = object()
        run = _RipRun(type("Tag", (), {}), (("one", object()),))
        _save_run(agent, run)
        attempts = []
        visited = []

        def Revoke(current):
            attempts.append(current)
            if len(attempts) == 1:
                raise KeyboardInterrupt

        def Invoke(current, name, teardown):
            visited.append(name)

        with self.assertRaises(KeyboardInterrupt):
            self._retry(agent, Invoke, Revoke)

        self.assertFalse(run.revoked)
        self.assertEqual(run.cursor, 0)
        self.assertEqual(visited, [])
        self.assertIs(_pending_run(agent, run.tag), run)

        self._retry(agent, Invoke, Revoke)
        self.assertEqual(attempts, [run, run])
        self.assertEqual(visited, ["one"])
        self.assertIsNone(_arrest_of(agent))

    def test_interrupted_teardown_keeps_cursor_and_closes_door(self) -> None:
        agent = object()
        run = _RipRun(type("Tag", (), {}), (("one", object()),))
        _save_run(agent, run)

        def Interrupt(current, name, teardown):
            raise KeyboardInterrupt

        with self.assertRaises(KeyboardInterrupt):
            self._retry(agent, Interrupt)

        self.assertEqual(run.cursor, 0)
        self.assertFalse(run.running)
        self.assertFalse(_may_act(agent))
        self.assertIs(_pending_run(agent, run.tag), run)

    def test_same_run_cannot_be_reentered_from_its_teardown(self) -> None:
        agent = object()
        run = _RipRun(type("Tag", (), {}), (("one", object()),))
        _save_run(agent, run)
        refusals = []

        def Invoke(current, name, teardown):
            try:
                self._retry(agent, Invoke)
            except TagCompositionError as error:
                refusals.append(str(error))

        self._retry(agent, Invoke)

        self.assertEqual(refusals, ["Tag teardown is already running"])
        self.assertIsNone(_arrest_of(agent))

    def test_same_run_cannot_be_reentered_during_revocation(self) -> None:
        agent = object()
        run = _RipRun(type("Tag", (), {}), (("one", object()),))
        _save_run(agent, run)
        refusals = []
        visited = []

        def Revoke(current):
            try:
                self._retry(agent, lambda *_: None, Revoke)
            except TagCompositionError as error:
                refusals.append(str(error))

        def Invoke(current, name, teardown):
            visited.append(name)

        self._retry(agent, Invoke, Revoke)

        self.assertEqual(refusals, ["Tag teardown is already running"])
        self.assertEqual(visited, ["one"])

    def test_later_run_failure_does_not_repeat_completed_earlier_run(self) -> None:
        agent = object()
        tag = type("Tag", (), {})
        first = _RipRun(tag, (("old", object()),))
        second = _RipRun(tag, (("new", object()),))
        _save_run(agent, first)
        _save_run(agent, second)
        visited = []
        fail_once = True

        def Invoke(current, name, teardown):
            nonlocal fail_once
            visited.append(name)
            if current is second and fail_once:
                fail_once = False
                raise RuntimeError("new failed")

        with self.assertRaises(TagCompositionError):
            self._retry(agent, Invoke)

        self.assertEqual(visited, ["old", "new"])
        self.assertIs(_pending_run(agent, tag), second)
        self.assertNotIn(first, _arrest_of(agent).runs)

        self._retry(agent, Invoke)
        self.assertEqual(visited, ["old", "new", "new"])
        self.assertIsNone(_arrest_of(agent))

    def test_an_empty_run_is_not_an_arrest(self) -> None:
        agent = object()
        _save_run(agent, _RipRun(type("Tag", (), {}), ()))
        self.assertIsNone(_arrest_of(agent))
        self.assertEqual(list(_Safehouse(None)), [])


if __name__ == "__main__":
    unittest.main()
