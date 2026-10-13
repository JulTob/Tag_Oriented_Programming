# STEP-SPEC-40: Reserved Agent Truth and Host Eligibility

- **STEP:** SPEC-40
- **Desk:** spec
- **Title:** Reserved Agent Truth and Host Eligibility
- **Author:** Codex, recording the Director's Agent-truth rulings
- **Status:** Brief
- **Created:** 2026-10-12
- **Issue:** [#71](https://github.com/JulTob/Tag_Oriented_Programming/issues/71)
- **Implementation proposal:** [#160](https://github.com/JulTob/Tag_Oriented_Programming/pull/160)

## Summary

For an Agent hosted by an ordinary Python object, `bool(agent)` answers
its visible Postconditions from its first Tagging. No Posts means true.
The truth protocol is reserved: a Tag cannot gain or delete `__bool__`,
and a Python host with an explicit `__bool__` is refused as a Target.
Host length and truth of objects held in Records remain separate questions.

## Proposed specification

1. An ordinary object Agent's truth answers every visible Postcondition,
   following the existing verdict, failure and recursive-check rules.
   No visible Posts means true, including after the last Post ends.
2. The Agent's `__bool__` seat is reserved. A Tag cannot provide an Action,
   Record or Delete under that name, or publish a Report/Operation there.
   Refusal is a Declaration Failure, including before accepted late
   assignment replaces an existing binding.
3. An ordinary Python host with an explicit `__bool__`, declared directly
   or inherited, is refused as a Target with a Composition Failure before
   Gate/Gain/Imprint or Target mutation. Refusal does not execute the host
   truth hook. An explicit `None` still occupies the seat.
4. Host `__len__` remains available through `len(agent)`, subject to the
   existing deliberate length Overlay; it does not determine Agent truth.
5. TOP's own synthesized-runtime truth hook is not a custom host
   declaration. A fresh untagged object constructed from such a runtime
   type retains underlying host truth until Tagging. A derived class's
   own explicit truth remains a host declaration and is refused.
6. Objects held in Records keep their own Python truth. A named Action
   can calculate a boolean normally without occupying `__bool__`.
7. Tag truth remains population truth: `bool(Tag)` asks whether its Field
   contains a sound Agent, including when the Tag receives a Pin.
   `Contract.Holds(Tag)` asks about the Tag's contract as a Pin Agent.
   Unpublished Tag-scope Reports/Operations do not occupy an ordinary
   Agent's truth seat.

## Rationale and compatibility

`if agent:` must consistently ask whether its promises hold. An empty
container-like Agent can be sound; an Agent whose Post fails can be
defective regardless of its size. The Director chose refusal of an
explicit host truth hook rather than replacing that host behavior.

Hosts with an explicit truth hook were previously accepted; they must
remain untagged or move that boolean information into an ordinary Action,
Record, or a held object before they can be eligible Targets. Existing
truth Contributions must move to an ordinary name. Host length, permitted
arithmetic/context Actions and Tag population questions remain available.

`"weapon" @ bearer` asks whether the Gain exists. `bool(bearer.weapon)`
asks the held value's own truth. `bool(bearer)` asks the bearer's Posts.
Neither query automatically imposes the held value's contract on its bearer.

## Dependencies and specification amendments

This changes the host-behavior qualification in Specification §0.1 and
Agent truth in §2.5. The corresponding amendments to STEP-SPEC-4 and
STEP-SPEC-6 belong under the Director's formal disposition of this STEP.

Condition binding protection (#59) and condition-dunder refusal (#74 /
STEP-SPEC-42) are separate changes. The agreed Tagging admission sequence
is also independent of this truth policy.

## Acceptance

- Eligible hosts retain zero/nonzero length through contract changes.
- Truth is contractual from first Tagging, before any Post and after
  deliberate removal of the last Post.
- Own, inherited, disabled and descriptor-based host truth is refused
  without evaluation or Target effects.
- Truth Gains, aliases, publication and late assignment are refused.
- Fresh synthesized-runtime objects and inherited runtime layers retain
  the supported host/Agent distinction.
- Record-held value truth and Tag population truth remain separate.
- Supported Python suites and the contract oracle pass.

### Decision

The 2026-10-09 host-length ruling was clarified by the Director on
2026-10-12: Agent truth reads Posts' validity, **“Refuse hosts with an
explicit __bool__”**, and **“Keep Tag population truth”**. These rulings
supersede the proposal's former allowance for explicit host/Tag truth.
This records the accepted design while leaving formal STEP status at
Brief for review; it does not assign a Cleared or Deployed status itself.
