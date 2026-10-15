# STEP-SPEC-40: Reserved Agent Truth and Host Eligibility

- **STEP:** SPEC-40
- **Desk:** spec
- **Title:** Reserved Agent Truth and Host Eligibility
- **Author:** Codex, recording the Director's Agent-truth rulings
- **Status:** Deployed
- **Created:** 2026-10-12
- **Cleared:** 2026-10-14
- **Deployed:** 2026-10-14
- **Issue:** [#71](https://github.com/JulTob/Tag_Oriented_Programming/issues/71)
- **Implementation:** [#160](https://github.com/JulTob/Tag_Oriented_Programming/pull/160), [#180](https://github.com/JulTob/Tag_Oriented_Programming/pull/180)

## Summary

`bool(agent)` answers its visible Postconditions, including when the Agent
is a Tag receiving Pins. For ordinary objects this applies from first
Tagging. A Tag with no Posts is true even when its Field is empty.
The truth protocol is reserved: a Tag cannot gain or delete `__bool__`,
and a Python host with an explicit `__bool__` is refused as a Target.
Host length, population size and truth of objects held in Records remain
separate questions. `Contract.Holds` is removed in favour of native truth.

## Specification

1. An Agent's truth answers every visible Postcondition,
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
7. Tag truth follows the same contract rule: `bool(Tag)` checks the Tag's
   own visible Posts received through Pins, not the Posts it declares for
   its members. No Posts means true, including before any Pin and with an
   empty Field. Posts retained after Rip still govern the Tag's truth.
   Unpublished Tag-scope Reports/Operations do not occupy an ordinary
   Agent's truth seat.
8. Population meanings stay unchanged. `len(Tag)` counts sound members,
   `len(Tag[:])` all members and `len(~Tag)` defective members, consistent
   with their respective iterations. `len(Tag) > 0` explicitly asks for a
   sound member. Field views and algebra results retain population truth:
   `bool(Tag[:])`, `bool(~Tag)` and `bool(Tag | Other)` ask whether those
   populations contain a member. A Tag in set algebra is still its sound
   population; `~` remains absorbing.
9. Remove the public `Contract.Holds` spelling, without a compatibility
   alias. Use `bool(agent)` or `if agent:` for a boolean verdict, including
   on Tags. Named checks such as `Contract.Postconditions`, diagnostic
   views and explicit condition deletion retain their separate purposes.

## Rationale and compatibility

`if agent:` must consistently ask whether its promises hold. An empty
container-like Agent can be sound; an Agent whose Post fails can be
defective regardless of its size. The Director chose refusal of an
explicit host truth hook rather than replacing that host behavior.

Hosts with an explicit truth hook were previously accepted; they must
remain untagged or move that boolean information into an ordinary Action,
Record, or a held object before they can be eligible Targets. Existing
truth Contributions must move to an ordinary name. Host length and permitted
arithmetic/context Actions remain available. Existing `if Tag:` and
`while Tag:` population guards must become `len(Tag) > 0`; this keeps their
sound-member meaning. Use `len(Tag[:]) > 0` when deficient members count too.

`"weapon" @ bearer` asks whether the Gain exists. `bool(bearer.weapon)`
asks the held value's own truth. `bool(bearer)` asks the bearer's Posts.
Neither query automatically imposes the held value's contract on its bearer.
For an ordinary untagged held value, `bool(value)` remains Python truth;
it is not a claim that the value is an Agent or has a TOP contract. Migration
from `Contract.Holds` must preserve any required membership check first.

## Dependencies and specification amendments

This changes the host-behavior qualification in Specification §0.1, Tag
spellings in §0.8, Pin truth in §1.9, Agent truth in §2.5 and the explicit
contract API in §2.6. It authorizes the corresponding amendments to
STEP-SPEC-4, STEP-SPEC-6 and STEP-SPEC-9, and the Tool truth guidance in
STEP-SPEC-36. The former Pin population-truth exception is superseded;
the population algebra is not.

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
- Record-held value truth remains separate from its bearer's contract.
- Empty and populated Tags answer their own Pin Posts, independently of
  member soundness; no Posts means true. Pin Overlay, retained Posts after
  Rip and deletion of the last Post follow ordinary contract rules.
- Tag truth does not evaluate its members' Posts. Lengths, iteration,
  partitions and set algebra keep their existing populations and timing.
- `Contract.Holds` is absent; native truth and named diagnostic checks
  cover its former Agent/Tag uses without changing ordinary value truth.
- Supported Python suites and the contract oracle pass.

### Decision

Cleared on **2026-10-14** from the Director's confirmed rulings: Agent
truth reads Posts' validity, explicit host `__bool__` is refused, and a
Tag's truth reads its own Pin contract. The Director confirmed **“Yes: no
Posts means True”**, including for an empty Field; clarified **“len(MyTag)
should be sound members. len(MyTag[:]) should be all members”** and
**“len(~MyTag) should return the cardinality of broken members. Set
algebra, basically, still applies”**; and directed that `Contract.Holds`
**“should be removed”**.

The 2026-10-09 host-length and 2026-10-12 host-refusal decisions remain.
The 2026-10-12 decision to **“Keep Tag population truth”** is superseded
by this unified contract rule. The reason is one meaning for Agent truth,
with explicit population cardinality preserving the existing set algebra.
The Director cleared the design and its specified amendments. The native
truth implementation and removal of `Contract.Holds` merged in #160 and
#180 on 2026-10-14. The corresponding Specification and guide amendments
are on main, and the focused truth and Contract namespace tests pass. This
deploys this STEP only; it clears no other STEP and does not change the
independent Tagging admission sequence.
