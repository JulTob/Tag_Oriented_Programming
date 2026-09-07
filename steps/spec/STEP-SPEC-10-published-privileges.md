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
it is a **sound member**: still belonging to the publishing Tag, and with
every promise on the Agent holding. A Rogue Agent (it left) keeps its own
Actions and Records and gets a **Privilege Failure** from the published
ones. A defective Agent (a promise broke) gets the **broken promise by
name**, `except Postcondition.Has_Homeland`, so it can repair and retry.
Membership and repair restore the privilege; nothing is re-declared.

## Motivation

The Director, on Pins: "rogue agents should also lose access to public
operations, as they lost privileges. A public operation could reinforce
this by always checking membership first." Until now the Specification
put that check on the author (§1.5, the guarded `dispatch`). What the
Agency shares is a privilege of belonging; the kernel should say so once
rather than every author remembering to.

## Specification

1. A published member is a privilege of **sound membership**. At every
   use (an Operation's invocation, a Report's read) TOP checks, in this
   order, that the Agent still belongs to the publishing Tag and that
   every visible promise on the Agent holds.
2. **Soundness is holistic.** The promises that count are all of the
   Agent's, whichever Tag made them, exactly the promises `if agent:`
   and the loop `for a in Tag` ask about. One word, one meaning. (The
   Director: "A car that has wheels working, but no honk, is not
   supposed to be on the road anyway.") A Shape that must relax a Base's
   promise deletes it in its Overlay (`@Delete`).
3. **Two failures.** Membership lost raises a **Tag Privilege Failure**,
   a Resolution Failure that is also an Attribute failure, so `hasattr`
   answers False for a published name on a Rogue Agent. A broken promise
   raises the **named Postcondition Failure** of that promise, exactly as
   a tagging would, so a program repairs what the failure names and
   retries: the autofix pattern.
4. Reports and Operations follow the same rule. A defective Agent reads
   the Tag's shared values through the Tag directly, `Wizard.max_spells`,
   which is never a privilege.
5. The Action and the name stay on the Agent after Rip: sticky as members
   of the Overlay; only their **use** is revoked. Applying the Tag again,
   or repairing the promise, restores use without re-declaration.
6. Members a Pin publishes onto a Field (STEP-SPEC-9 §5) are published
   members of the pinned Tag and follow the same rule.
7. The Agent's own Actions and Records are unchanged: a Rogue Agent keeps
   what it became; a defective one keeps what it became and repairs.
8. Cost. Membership is one dictionary lookup. Promises run only when the
   Agent has any, under the same re-entrancy guard as `bool(agent)`, so a
   promise that itself calls a published member does not recurse. An
   Agent without promises pays nothing beyond the lookup.
9. Consequence, accepted: a Tag cannot offer a published Operation as the
   way to repair a defective Agent, because the defective Agent cannot
   call it. Repair happens through the Agent's own Actions or from the
   Tag's side inside the `~Tag` loop.

## Rationale

Two histories, two rules. What the Agent *became* is its own: sticky.
What the Agency *lends* is the Agency's: revoked with membership and
suspended while the product is defective. Putting the check in the
kernel makes the Agency/Agent picture of STEP-SPEC-3 true by
construction and removes a class of author mistakes. Refusing at use
rather than removing the Action keeps the Overlay stable (no name
disappears from under a later Layer's Underlay). Two failures rather
than one because the program must react differently to "you left" and
"you are broken", and reading a message to tell them apart is what named
failures were made to avoid. The Director: "we gain a lot from two
different error codes... The autofix pattern is an amazing feature for
safety."

## Backwards compatibility

A program that called a published Operation or read a published Report
on a Rogue or defective Agent now fails instead of reaching the Tag.
§1.5's example no longer needs its own membership check. `hasattr` on a
published name answers False for a Rogue Agent. No other behaviour
changes.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Leave the check to the author (0.2.0a2) | Rejected by the Director: a privilege should be enforced where it is granted |
| Remove published Actions at Rip | Rejected: breaks the Overlay under later Layers and the sticky law; refusing at use is enough |
| Revoke the Agent's own Actions too | Rejected: that is what the Agent became; the Rogue rule stands |
| Only the publishing Tag's promises count | Rejected by the Director: soundness is holistic; "sound" must mean one thing for the loop and for the privilege |
| One failure for both refusals | Rejected by the Director: two failures give error control and the autofix pattern |
| Reports readable while defective | Set aside: one rule; direct Tag access serves repair |
| Cache soundness between taggings | Rejected: a promise reads live state |

## Acceptance requirements

Covered by `tests/test_topkit.py::RevokedPrivilegeTests` and
`PinTests::test_a_public_pin_member_reaches_the_whole_field`.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
>
> *Drafted for the Director's confirmation:* Cleared on 2026-09-07, per the
> Director's words above and in review ("It should check membership AND
> post-validity"; "soundness is an holistic property"; "we gain a lot
> from two different error codes"; "Apply it").
