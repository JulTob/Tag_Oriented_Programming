# STEP-SPEC-10: Published Members Are Privileges of Membership

- **STEP:** SPEC-10
- **Desk:** spec
- **Title:** Published Members Are Privileges of Membership
- **Author:** Julio Toboso (@JulTob)
- **Status:** Vetting
- **Created:** 2026-09-06

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

A published Report or Operation is the Agency's, lent to the Agent while
it is a member. After Rip, the Agent keeps its own Actions and Records
(the Rogue rule) but the published members **fail closed**: the Action
is still there and refuses with a Resolution Failure; the read-only name
raises an Attribute failure. Membership restores them.

## Motivation

The Director, on Pins: "rogue agents should also lose access to public
operations, as they lost privileges. A public operation could reinforce
this by always checking membership first." Until now the Specification
put that check on the author (§1.5, the guarded `dispatch`). What the
Agency shares is a privilege of belonging; the kernel should say so once
rather than every author remembering to.

## Specification

1. A published Operation's Action on the Agent checks active membership
   of the publishing Tag **at invocation**, before forwarding. A Rogue
   Agent's call raises a Tag Resolution Failure naming the member, the
   Tag and the Agent. A stale handle captured before Rip fails the same
   way.
2. A published Report's read-only name on the Agent checks the same
   membership at every read and raises an Attribute failure otherwise.
3. The Action and the name stay on the Agent after Rip: they are sticky
   as members of the Overlay; only their **use** is revoked. Applying the
   Tag again restores use without re-declaration.
4. Members a Pin publishes onto a Field (STEP-SPEC-9 §5) are published
   members of the pinned Tag and follow the same rule.
5. The Agent's own Actions and Records are unchanged: a Rogue Agent keeps
   what it became.

## Rationale

Two histories, two rules. What the Agent *became* is its own: sticky.
What the Agency *lends* is the Agency's: revoked with membership. Putting
the check in the kernel makes the Agency/Agent picture of STEP-SPEC-3
true by construction and removes a class of author mistakes. Refusing at
invocation rather than removing the Action keeps the Overlay stable (no
name disappears from under a later Layer's Underlay) and keeps
`hasattr` honest about what the Agent carries.

## Backwards compatibility

A program that called a published Operation or read a published Report
on a Rogue Agent now fails instead of reaching the Tag. §1.5's example
no longer needs its own membership check. No other behaviour changes.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Leave the check to the author (0.2.0a2) | Rejected by the Director: a privilege should be enforced where it is granted |
| Remove published Actions at Rip | Rejected: breaks the Overlay under later Layers and the sticky law; refusing at use is enough |
| Revoke the Agent's own Actions too | Rejected: that is what the Agent became; the Rogue rule stands |

## Acceptance requirements

Covered by `tests/test_tagkit.py::RevokedPrivilegeTests` and
`PinTests::test_a_public_pin_member_reaches_the_whole_field`.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
>
> *Drafted for the Director's confirmation:* Cleared on 2026-09-06, per the
> Director's words above.
