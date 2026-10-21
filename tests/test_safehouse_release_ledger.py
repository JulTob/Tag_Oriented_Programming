"""Saved Rip work keeps identity, cursor and temporary authority."""

from contextvars import copy_context
import unittest
from unittest.mock import patch

from TopKit.arrest import _arrest_of, _may_act, _rip_door, _safehouse
from TopKit.errors import TagArrestedAccessError, TagCompositionError, TagResolutionError
from TopKit.rip_runs import _RipRun, _finish_run, _pending_run, _retry_arrested, _run_saved, _save_run


class SafehouseReleaseLedgerTests(unittest.TestCase):
    def setUp(self):
        ledger = patch.dict(_safehouse, clear=True)
        ledger.start()
        self.addCleanup(ledger.stop)

    def test_arrest_failure_is_a_resolution_failure(self):
        self.assertTrue(issubclass(TagArrestedAccessError, TagResolutionError))

    def test_holding_uses_identity_without_host_protocols(self):
        class Host:
            def __hash__(self):
                raise AssertionError("host hash")
            def __eq__(self, other):
                raise AssertionError("host equality")
            def __repr__(self):
                raise AssertionError("host display")
        old, new = type("Tag", (), {}), type("Tag", (), {})
        first, second = Host(), Host()
        run = _RipRun(old, (("Close", object()),))
        _save_run(first, run)
        self.assertIs(_pending_run(first, old), run)
        self.assertIsNone(_pending_run(first, new))
        self.assertIsNone(_arrest_of(second))
        _finish_run(second, run)
        self.assertIs(_pending_run(first, old), run)

    def test_retry_stops_at_failed_step_and_retains_its_original_suffix(self):
        agent = object()
        run = _RipRun(type("Role", (), {}), tuple((name, object()) for name in ("A", "B", "C")))
        _save_run(agent, run)
        events = []
        failure = RuntimeError("repair required")
        broken = True
        def Invoke(current, name, protocol):
            self.assertTrue(_may_act(agent))
            events.append(name)
            if name == "B" and broken:
                raise failure
        with self.assertRaises(TagCompositionError) as caught:
            _retry_arrested(agent, lambda current: None, Invoke)
        self.assertIs(caught.exception.__cause__, failure)
        self.assertEqual(events, ["A", "B"])
        self.assertEqual(run.cursor, 1)
        self.assertFalse(_may_act(agent))
        broken = False
        _retry_arrested(agent, lambda current: None, Invoke)
        self.assertEqual(events, ["A", "B", "B", "C"])
        self.assertIsNone(_arrest_of(agent))

    def test_interruption_preserves_original_exception_cursor_and_closed_door(self):
        for failure in (KeyboardInterrupt(), SystemExit(9)):
            with self.subTest(failure=type(failure).__name__):
                agent = object()
                run = _RipRun(type("Role", (), {}), (("Close", object()),))
                _save_run(agent, run)
                def Invoke(*arguments):
                    raise failure
                with self.assertRaises(type(failure)) as caught:
                    _retry_arrested(agent, lambda current: None, Invoke)
                self.assertIs(caught.exception, failure)
                self.assertEqual(run.cursor, 0)
                self.assertFalse(run.running)
                self.assertFalse(_may_act(agent))

    def test_failed_revocation_is_retried_before_any_callback(self):
        agent = object()
        run = _RipRun(type("Role", (), {}), (("Close", object()),))
        _save_run(agent, run)
        events = []
        def Revoke(current):
            events.append("revoke")
            if len(events) == 1:
                raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            _retry_arrested(agent, Revoke, lambda *arguments: events.append("close"))
        self.assertFalse(run.revoked)
        _retry_arrested(agent, Revoke, lambda *arguments: events.append("close"))
        self.assertEqual(events, ["revoke", "revoke", "close"])

    def test_selected_run_may_finish_before_an_older_run(self):
        agent = object()
        older = _RipRun(type("Older", (), {}), (("old", object()),))
        later = _RipRun(type("Later", (), {}), (("later", object()),))
        _save_run(agent, older)
        _save_run(agent, later)
        events = []
        _run_saved(agent, later, lambda run: None, lambda run, name, protocol: events.append(name))
        self.assertEqual(events, ["later"])
        self.assertIs(_pending_run(agent, older.tag), older)
        self.assertIsNone(_pending_run(agent, later.tag))

    def test_recursive_retry_cannot_reenter_a_running_protocol(self):
        agent = object()
        run = _RipRun(type("Role", (), {}), (("Close", object()),))
        _save_run(agent, run)
        def Invoke(*arguments):
            with self.assertRaisesRegex(TagCompositionError, "already running"):
                _retry_arrested(agent, lambda current: None, Invoke)
        _retry_arrested(agent, lambda current: None, Invoke)
        self.assertIsNone(_arrest_of(agent))

    def test_copied_context_cannot_keep_permission_after_callback(self):
        agent = object()
        _save_run(agent, _RipRun(type("Role", (), {}), (("Close", object()),)))
        door = _rip_door(agent)
        door.__enter__()
        copied = copy_context()
        self.assertTrue(copied.run(_may_act, agent))
        copied.run(door.__exit__, None, None, None)
        self.assertFalse(_may_act(agent))
        self.assertFalse(copied.run(_may_act, agent))

    def test_retry_reaches_work_saved_during_an_earlier_callback(self):
        agent = object()
        original = _RipRun(type("Original", (), {}), (("old", object()),))
        later = _RipRun(type("Later", (), {}), (("new", object()),))
        _save_run(agent, original)
        events = []
        def Invoke(run, name, protocol):
            events.append(name)
            if run is original:
                _save_run(agent, later)
        _retry_arrested(agent, lambda run: None, Invoke)
        self.assertEqual(events, ["old", "new"])
        self.assertIsNone(_arrest_of(agent))

