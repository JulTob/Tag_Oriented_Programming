# STEP-ADA-2: Experimental Geometry law tests

- **STEP:** ADA-2
- **Desk:** ada
- **Title:** Experimental Geometry law tests
- **Author:** Codex, at the Director's request
- **Status:** Brief
- **Created:** 2026-10-10
- **Related:** [ADA-1 / #5](https://github.com/JulTob/Tag_Oriented_Programming/issues/5)

> One STEP, one topic: test TOP's existing ordered Form law in Ada without
> selecting the final language profile or implementing lifecycle semantics.

## Summary

Propose a small, explicitly experimental Ada Geometry kernel. It exercises
the established Base-first, declaration-ordered, duplicate-free Form law
from Specification §0.4. No Target, Field, Tagging or Rip implementation is
claimed, and no Ring 0 conformance designation is requested.

## Motivation

Geometry is independent of the open Target-lifetime and Tagging-failure
choices. It gives the Ada Desk a compiling, verifiable first experiment while
the Director considers ADA-1. TOP permits several independent Bases, so
its Geometry must not be confused with a Target's nominal Ada inheritance.

## Experiment specification

The proposed namespace is `TOP_Experimental.Geometry`, under
`experimental/ada/geometry/`. Its names are internal to this experiment,
not final TOP language spellings.

A limited Registry owns an append-only vector of Tag descriptors. Each
descriptor captures a detached, ordered list of already-issued Base IDs
from that same Registry. The experiment offers no rebasing operation;
this construction makes cycles impossible without choosing TOP's general
future mutation policy.

`Form` performs an iterative, ordered traversal with identity-based
deduplication. It returns the requested Tag's reachable Bases first, in
declaration order, each once, then the requested Tag. Its result is a
detached value; changing an input list or returned Form does not mutate
the declared Geometry.

Opaque IDs contain a Registry identity and a position. Invalid, foreign
or ended-Registry IDs cannot be mistaken for local Tags. The provisional
Registry identity counter is single-threaded and never recycles IDs;
exhaustion fails instead of aliasing a previous Registry. These are test
storage choices, not Agent identity rules or final public APIs.

Ada containers own the descriptor and traversal storage. The caller does
not acquire individually allocated descriptors requiring manual cleanup.

## Verification

Compile with GNAT, Ada 2022 and assertions enabled. A runtime assertion
sentinel must fail the suite if assertions are disabled. A shell runner
builds outside the checkout and cleans its temporary output on exit.

Ten tests cover:

- empty Registry rejection and a single root;
- a chain;
- independent Base declaration order;
- a diamond, each Base once;
- overlapping Bases;
- repeated Base IDs, deduplicated by Form;
- detached declaration/result lists;
- a 3,000-Tag chain without recursive host calls;
- invalid/foreign handles and atomic declaration validation;
- an ended Registry's ID not becoming valid in a later Registry.

Also compile with all GNAT warnings enabled and treated as errors. The
experiment must not alter the Python package or add Ada tooling to Python's
runtime dependency declarations.

## Acceptance and limits

The Director may approve the experiment independently of the final ADA-1
profile. Approval of this internal test kernel does not Clear a Target
carrier, reserve programmer Contribution names, decide task safety, or
establish Field ownership. Full Ring 0 conformance still requires the
identity, membership and lifecycle law tests for a selected supported profile.

## Alternatives

A whole Ring 0 port would force unresolved lifetime and failure decisions.
A syntax-only document would not demonstrate that the established Form law
can execute in Ada. This experiment supplies that evidence without choosing
those independent features.

## Backwards compatibility

No Python behavior, normative Specification or existing STEP status changes.
Only experimental Ada files and this Brief are proposed.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
