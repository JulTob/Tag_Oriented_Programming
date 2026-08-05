# TagKit stress testing

TagKit uses three verification layers:

1. the ordinary conformance and regression suite;
2. a deterministic state-machine oracle; and
3. isolated capacity probes for individual scaling axes.

In this report, **Geometry** means the overall Base/Shape relationship
structure. A **Form** is the Base-first ordered closure of one Tag.

The capacity probes intentionally run in fresh processes. This keeps a wide
composition, a deep Form, and a large Field from contaminating one another's
memory measurements.

## Commands

Run the ordinary suite:

```bash
python3.12 -X dev -m unittest discover -s tests
python3.14 -X dev -m unittest discover -s tests
```

Run the audited state-machine profile:

```bash
PYTHONPATH=. python3.12 -X dev tests/stress_tagkit_state.py \
        --first-seed 1701 \
        --seeds 50 \
        --steps 1200 \
        --population 18

PYTHONPATH=. python3.14 -X dev tests/stress_tagkit_state.py \
        --first-seed 1701 \
        --seeds 50 \
        --steps 1200 \
        --population 18
```

The state-machine defaults are smaller for quick local checks. Its model is
independent of TagKit's internal state. It compares observable membership,
Fields, leaves, history, and transaction results after every transition.

Run a capacity probe with:

```bash
PYTHONPATH=. python3.12 -X dev tests/stress_tagkit_capacity.py PROBE SIZE
```

Available probes are:

- `deep`
- `form`
- `wide`
- `diamond`
- `population`
- `scopes`
- `rollback`
- `threads`
- `lifecycle`
- `caches`
- `pin-cycles`

## Audited run

Correctness results below were last verified on 2026-08-05. Capacity
measurements are from 2026-07-31. Times are workstation measurements, not
portable performance guarantees.

### Correctness

| Check | Python 3.12 | Python 3.14 |
| --- | ---: | ---: |
| Ordinary suite | 173 passed | 173 passed |
| State-machine seeds | 50 passed | 50 passed |
| State-machine transitions | 60,000 passed | 60,000 passed |
| State-machine duration | 21.640 s | 23.210 s |

The state machine covered:

- ordinary Targets and Tag Targets;
- Base/Shape trees and repeated diamonds;
- single and batch `Apply`;
- invalid batch validation before mutation;
- active no-op reapplication;
- cascading `Rip`;
- nested and failing `Scope`;
- weak Fields and Tag-bound views;
- Actions, Records, Reports, Operations, Underlays, Delete, and Contracts;
- `Has`, Tag names, contributions, and leaf `Tags`;
- historical `isinstance`;
- Pins;
- failed Preconditions, Imprints, and Postconditions; and
- identity-preserving mutable rollback.

### Capacity

| Probe | Size | Python 3.12 | Python 3.14 |
| --- | ---: | ---: | ---: |
| Deep Form apply | 500 Tags | 0.309 s | 0.352 s |
| Wide composition apply | 2,000 Tags | 10.239 s | 12.957 s |
| Diamond Geometry apply | 512 branches | 0.513 s | 0.580 s |
| Field population | 50,000 Agents | 1.160 s | 1.011 s |
| Nested Scopes | 2,000 Scopes | 11.450 s | 14.413 s |
| Transaction rollback | 300,000 items | 0.046 s | 0.051 s |
| Distinct-target threads | 20,000 Targets | 1.280 s | 1.251 s |
| Lifecycle/weak cleanup | 20,000 Targets | 0.079 s | 0.060 s |
| Weak-cache churn | 5,000 compositions | 0.279 s | 0.189 s |
| Self/reciprocal Pin cycles | 10,000 cycles | 0.665 s | 0.580 s |

The 300,000-item rollback probe peaked at approximately 20.7 MB on both
interpreters. The 50,000-Agent Field and 20,000-Agent lifecycle probes
returned to zero live members after collection.
All transient hosts, Tags, runtime types, and Agents in the cache probe were
also reclaimed.

A 1,500-level Form also completed on both interpreters:

```text
Python 3.12  create=4.465 s  apply=4.978 s  cascade-rip=0.561 s
Python 3.14  create=6.072 s  apply=6.135 s  cascade-rip=0.497 s
```

Before iterative Form traversal and direct-Base leaf discovery, a
500/512-level application took roughly 29–31 seconds and a Form around
Python's recursion limit failed with `RecursionError`. The 500-level
application now completes in less than 0.41 seconds on both tested
interpreters, and a 1,500-level Form query completes without recursion.

Wide composition remains the principal scaling boundary. Every independent
Tag is a new leaf and every successful layer captures an additional
historical Overlay. The cost is therefore intentionally greater than a
single deep Base chain.

## Defects exposed and corrected

The stress pass added regressions for:

- `__class__` and `__dict__` Action/Record/Delete corruption;
- a Field iterator yielding a member Ripped after iteration began;
- recursive Form and mutable-journal traversal;
- coroutine, generator, and async-generator Action introspection;
- stale transaction guards inherited by child `asyncio` Tasks;
- silently discarded coroutine, generator, and async-generator application
  protocols;
- lazy automatic Rip results leaking unawaited work;
- static Form snapshots missing a successful mid-Tagging Geometry rebase;
- leaf queries after a committed Pin rebase;
- hosts silently ignoring actualization or vetoing rollback restoration;
- misleading instance namespaces; and
- raw host subclass-hook exceptions escaping runtime actualization without a
  TagKit composition failure.

Tag application remains synchronous. Async Actions and Operations are valid
and retain their Python callable kind. Coroutine and async-generator
Preconditions, Imprints, Postconditions, and Records reject their Tagging
atomically rather than creating deferred work. Generator conditions and
Imprints reject for the same reason, while a synchronous generator remains
valid Record data. Lazy Rip protocols are rejected explicitly after
membership has ended, like any other failing teardown.

A Form's Bases are discovered lazily between applied layers. A successful
earlier Imprint can therefore change a later sibling's Geometry without
leaving the transaction on a stale route. Normal upward-closed active sets
keep the direct-Base leaf fast path; a committed later rebase automatically
uses a live-Form fallback.

## Deliberate boundaries and open decisions

These observations were not silently changed by the stress pass:

- A Rip teardown may reapply its own Tag. The current Guide explicitly
  permits this unusual escape hatch.
- Native declarations can still reuse some Tag control-plane names. A
  reserved-name policy would affect valid Operations and needs an explicit
  API decision.
- `Contract.Status` cannot represent both a Precondition and Postcondition
  carrying the same name in its current flat dictionary. Changing its key
  shape is an API decision.
- `Apply(target, A, B, C)` validates every Tag before starting, but each Tag
  remains its own transaction.
- Concurrent mutation of one Target is unsupported. The thread probe uses
  independent Targets.
- Exact runtime-class identity, copying, serialization, opaque-object
  mutation, and external I/O remain documented Python-profile boundaries.
