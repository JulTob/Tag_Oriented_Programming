# STEP-SPEC-10: Published Members Answer Members Only

- **STEP:** SPEC-10
- **Desk:** spec
- **Title:** Published Members Answer Members Only
- **Author:** Julio Toboso (@JulTob)
- **Status:** Cleared
- **Created:** 2026-09-06
- **Cleared:** 2026-09-16

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

A published Report or Operation is the Agency's, lent to the Agent while
it is a **sound member**: still belonging to the publishing Tag, and with
every promise on the Agent holding. A Rogue Agent (it left) keeps its own
Actions and Records and gets a **Rogue Access Failure** from the
published ones. A defective Agent (a promise broke) gets the **broken
promise by name**, `except Postcondition.Has_Homeland`, so it can repair
and retry. Membership and repair open the member again; nothing is
re-declared.

## Motivation

The Director, on Pins: "rogue agents should also lose access to public
operations, as they lost privileges. A public operation could reinforce
this by always checking membership first." Until now the Specification
put that check on the author (§1.5, the guarded `dispatch`). What the
Agency shares, it shares with its members; the kernel should say so once
rather than every author remembering to.

## Specification

1. A published member **answers members only, and only sound ones**. At
   every use (an Operation's invocation, a Report's read) TOP checks, in
   this order, that the Agent still belongs to the publishing Tag and
   that every visible promise on the Agent holds.
2. **Soundness is holistic.** The promises that count are all of the
   Agent's, whichever Tag made them, exactly the promises `if agent:`
   and the loop `for a in Tag` ask about. One word, one meaning. (The
   Director: "A car that has wheels working, but no honk, is not
   supposed to be on the road anyway.") A Shape that must relax a Base's
   promise deletes it in its Overlay (`@Delete`).
3. **Two failures.** Membership lost raises a **Tag Rogue Access
   Failure**, a Resolution Failure: an access, from a Rogue Agent, said
   in TOP's own words. A broken promise raises the **named Postcondition
   Failure** of that promise, exactly as a tagging would, so a program
   repairs what the failure names and retries: the autofix pattern.
4. **A TOP failure, and nothing else.** The Rogue Access Failure is not
   also a failure of the host language's attribute lookup. Membership is
   TOP's question; answering it in the lower layer's words would let a
   lower-layer question swallow it, so `hasattr` would report *no such
   name* for a name that plainly exists and the program would repair the
   wrong thing. (The Director: "has attr is the lower layer. We
   shouldn't cross the layer's veil.") A caller that wants to ask
   politely catches the failure.
5. Reports and Operations follow the same rule. A defective Agent reads
   the Tag's shared values through the Tag directly, `Wizard.max_spells`,
   which asks nothing about the Agent.
6. The Action and the name stay on the Agent after Rip: sticky as members
   of the Overlay; only their **use** is refused. Applying the Tag again,
   or repairing the promise, restores use without re-declaration.
7. Members a Pin publishes onto a Field (STEP-SPEC-9 §5) are published
   members of the pinned Tag and follow the same rule.
8. The Agent's own Actions and Records are unchanged: a Rogue Agent keeps
   what it became; a defective one keeps what it became and repairs.
9. Cost. Membership is one dictionary lookup. Promises run only when the
   Agent has any, under the same re-entrancy guard as `bool(agent)`, so a
   promise that itself calls a published member does not recurse. An
   Agent without promises pays nothing beyond the lookup.
10. Consequence, accepted: a Tag cannot offer a published Operation as
    the way to repair a defective Agent, because the defective Agent
    cannot call it. Repair happens through the Agent's own Actions or
    from the Tag's side inside the `~Tag` loop.

## Rationale

Two histories, two rules. What the Agent *became* is its own: sticky.
What the Agency *lends* is the Agency's: closed with membership and
closed while the product is defective. Putting the check in the
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
published name of a Rogue Agent raises rather than answering False,
because the failure is a TOP failure and not an attribute failure. No
other behaviour changes.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Leave the check to the author (0.2.0a2) | Rejected by the Director: what a Tag lends should be checked where it is lent |
| Remove published Actions at Rip | Rejected: breaks the Overlay under later Layers and the sticky law; refusing at use is enough |
| Revoke the Agent's own Actions too | Rejected: that is what the Agent became; the Rogue rule stands |
| Only the publishing Tag's promises count | Rejected by the Director: soundness is holistic; "sound" must mean one thing for the loop and for the published member |
| One failure for both refusals | Rejected by the Director: two failures give error control and the autofix pattern |
| Reports readable while defective | Set aside: one rule; direct Tag access serves repair |
| Cache soundness between taggings | Rejected: a promise reads live state |
| Name it a Privilege Failure, also an `AttributeError` (0.2.0a3) | Rejected by the Director: "Privilege is not part of the top vocabulary"; and an OOP failure must not stand in for a TOP one |

## Acceptance requirements

Covered by `tests/test_topkit.py::RogueAccessTests` and
`PinTests::test_a_public_pin_member_reaches_the_whole_field`.

---

### Decision *(filled by the Director)*

> Status set to **Cleared** on 2026-09-16, because the Director reviewed
> the three STEPs against the goals of the project and directed: "clear
> and commit steps 9 and 10. Implement them and test in some examples
> with practical design patterns we can adopt through them."
>
> The direction that shaped the STEP, in the Director's words: "It should
> check membership AND post-validity"; "soundness is an holistic
> property"; "we gain a lot from two different error codes"; "Apply it".
> The failure was renamed and un-crossed from the lower layer on the
> Director's correction of 2026-09-13: "Error Rogue Access is clear... It
> stays TOP vocabulary"; "Do not use AttributeError, which is an OOP
> problem, as a TOP problem".
>
> Deployed follows the merge of the pull request that carries §1.5 of the
> Specification.
