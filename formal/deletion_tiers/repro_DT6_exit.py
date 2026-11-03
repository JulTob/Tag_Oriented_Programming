"""Reproducer DT-6 (exit): one interruption stops the whole At_Exit pass.

Same spec promise as repro_DT6_del.py. Model invariant DT6_Isolated
(TLC counterexample: tier="exit", agent 1 interrupted, agent 2 never
reached). Same root cause: no per-Agent isolation for BaseException in
TopKit/lifecycle.py _run_exit_protocols (lines 412-423).
"""
import sys

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else ".")
import warnings

warnings.simplefilter("ignore")

import TopKit.lifecycle as L
from TopKit import At_Exit, Rip, Tag

LOG = []


class Due(Tag):
    @Rip
    def Leave(a):
        LOG.append("due")


class Boom(Tag):
    @Rip
    def Leave(a):
        LOG.append("boom")
        raise KeyboardInterrupt("stop")


class Host:
    pass


bad, good = Host(), Host()
Boom(bad)
Due(good)
At_Exit(bad)
At_Exit(good)
try:
    L._run_exit_protocols()
    outcome = "no-raise"
except KeyboardInterrupt:
    outcome = "KeyboardInterrupt escaped"
finally:
    L._exit_registry.clear()
print("observed:", LOG, outcome)
print("expected: ['boom', 'due'] (good agent still runs; pass completes)")
print("VIOLATION DT-6" if LOG != ["boom", "due"] else "ok: no violation")
