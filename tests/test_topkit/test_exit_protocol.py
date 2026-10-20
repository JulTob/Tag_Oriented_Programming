"""Conformance tests: exit protocol."""

from __future__ import annotations

import gc
import unittest
import weakref
from TopKit import At_Exit

from ._fixtures import Agent
from ._fixtures import Sentry
from ._fixtures import _DEL_LOG


class ExitProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        _DEL_LOG.clear()

    def test_rip_runs_best_effort_on_garbage_collection(self) -> None:
        ari = Agent()
        Sentry(ari)

        del ari
        gc.collect()

        self.assertEqual(_DEL_LOG.count("stood down"), 1)

    def test_explicit_rip_prevents_a_second_rip_on_collection(self) -> None:
        ari = Agent()
        Sentry(ari)
        del Sentry[ari]

        del ari
        gc.collect()

        self.assertEqual(_DEL_LOG.count("stood down"), 1)

    def test_host_finalizer_still_runs(self) -> None:
        seen: list[str] = []

        class Host:
            def __del__(self) -> None:
                seen.append("host del")

        host = Host()
        Sentry(host)

        del host
        gc.collect()

        self.assertEqual(seen, ["host del"])
        self.assertEqual(_DEL_LOG, ["stood down"])

    def test_a_rip_in_a_finally_is_the_guaranteed_teardown(self) -> None:
        ari = Agent()

        held = Sentry(ari)                                            # tag before the try
        try:
            self.assertIs(held, ari)
            self.assertIn(ari, Sentry)
        finally:
            del Sentry[ari]                                           # Rip in the finally

        self.assertNotIn(ari, Sentry)
        self.assertEqual(_DEL_LOG, ["stood down"])

    def test_a_rip_in_a_finally_runs_even_when_the_block_raises(self) -> None:
        ari = Agent()

        with self.assertRaises(ValueError):
            Sentry(ari)
            try:
                raise ValueError("boom")
            finally:
                del Sentry[ari]

        self.assertNotIn(ari, Sentry)
        self.assertEqual(_DEL_LOG, ["stood down"])

    def test_at_exit_registration_is_weak_and_pruned(self) -> None:
        ari = Agent()
        Sentry(ari)
        At_Exit(ari)
        reference = weakref.ref(ari)

        del ari
        gc.collect()

        self.assertIsNone(reference())                 # weak: it never kept the Agent

        import tracemalloc

        gc.collect()
        tracemalloc.start()
        before, _peak = tracemalloc.get_traced_memory()

        for _ in range(2000):
            At_Exit(Agent())                           # each registration dies with its Agent

        gc.collect()
        after, _peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        self.assertLess((after - before) / 2000, 16)   # nothing kept per dead registration
