# STEP-SPEC-40: Agent Contract Truth and Host Length

- **STEP:** SPEC-40
- **Desk:** spec
- **Title:** Agent Contract Truth and Host Length
- **Author:** Codex, recording the Director's host-length ruling
- **Status:** Brief
- **Created:** 2026-10-12
- **Issue:** [#71](https://github.com/JulTob/Tag_Oriented_Programming/issues/71)
- **Implementation proposal:** [#72](https://github.com/JulTob/Tag_Oriented_Programming/pull/72)

## Summary

When neither the Python host nor a Tag supplies `__bool__`, an Agent's
truth answers its visible Postconditions from its first Tagging. No Posts
means no broken promise, so the Agent is true. A host's `__len__` still
answers `len(agent)`; length does not answer contract truth.

This records the accepted design described in issue #71 as a focused
STEP. It does not silently change a deployed STEP's Decision or clear
itself. The Director can confirm the formal disposition below.

## Motivation

An empty container-like host can have length zero while every visible
Post holds. Letting its length answer `if agent:` confuses the size of
the host with the validity of its promises. Installing contract truth
only after the first Post arrives also changes that question's meaning
when the Agent has no Posts, or its last Post is deliberately ended.

## Proposed specification

1. If neither its host nor the TOP Overlay provides an explicit
   `__bool__`, an Agent's truth answers its visible contract from the
   first Tagging. Existing strict verdict and failure rules still apply.
2. An Agent with no visible Posts is true: no promised condition is
   broken. Ending the last Post does not return truth to host length.
3. This STEP preserves the host's `__len__` through `len(agent)`, subject
   to the existing deliberate `__len__` Overlay. Zero and nonzero length
   do not determine contract truth.
4. An explicit host `__bool__` is preserved. A Tag's deliberate
   `__bool__` Action or Delete keeps the existing Overlay behavior.
   Reserving that Python protocol seat is outside this STEP.
5. When TOP supplies the contract-truth hook, a fresh, untagged object
   constructed from an Agent's synthesized runtime type retains the
   underlying host's ordinary truth. This does not override a Tag's
   deliberate `__bool__` Action. The runtime representation alone does
   not make that new object an Agent.

## Examples

For a host that has `__len__`, but no explicit `__bool__`:

| Agent state | `len(agent)` | `bool(agent)` |
| --- | --- | --- |
| Empty host, no Posts | 0 | True |
| Empty host, every visible Post holds | 0 | True |
| Nonempty host, a visible Post fails | Host length | False |
| Last Post deliberately ended | Host length | True |

Where an explicit host or TOP `__bool__` occupies the seat, use
`Contract.Holds(agent)` for the contract question. This STEP does not
claim that an arbitrary Python truth hook is an automatic safety guard.

## Compatibility and dependencies

This deliberately narrows the host-behavior promise in Specification
§0.1: a host without `__bool__` keeps its length, while TOP supplies the
Agent's truth. Record the corresponding amendment to §2.5,
STEP-SPEC-4 and STEP-SPEC-6 only under the Director's cleared decision.

Condition-name binding protection in PR #59 is an implementation
dependency of current PR #72. The condition-dunder decision in #74 is
separate; this STEP does not decide whether a Pre or Post may have a
dunder name. The agreed Tagging admission sequence is also independent.

## Acceptance

- Zero and nonzero host lengths remain unchanged through Tagging,
  Post failure and deliberate condition removal.
- Truth is contractual from first Tagging, including before any Post
  exists and after the last Post ends.
- Explicit host and TOP truth behavior remains within the stated scope.
- When TOP supplies the contract-truth hook, untagged objects created
  from synthesized runtime types retain host truth, including Python's
  invalid-length failures.
- Supported Python suites and the contract oracle pass.

### Decision

Pending the Director's formal STEP review. Issue #71 records the
2026-10-09 accepted host-length design; this Brief preserves that
evidence without assigning a new Cleared or Deployed status.
