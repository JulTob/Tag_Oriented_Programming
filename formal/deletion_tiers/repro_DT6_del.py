"""Reproducer DT-6 (deletion): an interrupted teardown skips the rest.

Spec promise: "Deletion runs in that order: every teardown still due runs"
(spec/SPECIFICATION.md:1719-1720); "When TOP runs an Agent's teardowns at
deletion or exit, they run in reverse order of application" (spec:158-159).
Model: formal/deletion_tiers/DeletionTiers.tla, invariant DT6_Isolated
(TLC counterexample: tier="del", due=<<2,1>>, first TearStep interrupted,
rest abandoned; replay vector: apply tag 1 then tag 2, tag 2 raises KI).
"""
import gc
import sys

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else ".")
import warnings

warnings.simplefilter("ignore")

from TopKit import Rip, Tag

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


a = Host()
Due(a)
Boom(a)  # applied last -> runs first
del a
gc.collect()
gc.collect()
print("observed:", LOG)
print("expected: ['boom', 'due']")
print("VIOLATION DT-6" if LOG != ["boom", "due"] else "ok: no violation")
