# STEP-SPEC-11: Conditions End With Membership

- **STEP:** SPEC-11
- **Desk:** spec
- **Title:** Conditions End With Membership
- **Author:** Julio Toboso (@JulTob)
- **Status:** Vetting
- **Created:** 2026-09-07

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

A Tag's gates and promises are the Tag's. When an Agent leaves the Tag's
Field, they end: Rip removes the Tag's Preconditions and Postconditions
from the Agent, and a condition the Tag had laid over another Tag's (a
Shape over its Base, or one independent Tag over another) gives that
prior condition back. A Rogue Agent keeps what it became, its Actions
and Records, and is no longer held to a role it left.

## Motivation

Until now conditions were sticky like contributions: Rip a Wizard and
the Agent was still held to Wizard's promises, so a Rogue Wizard with an
empty spellbook stayed "defective" under a role it no longer carried.
That contradicts STEP-SPEC-10, where what the Agency imposes ends when
the Agent leaves it. The Director raised the case ("an imprint may add a
lot of conditions, but all of them may be only conditional to the tag")
and asked for the alternatives to be evaluated: a `@Rip` that deletes
conditions by name, a language shortcut to rip them all, a modifier, a
codeword, or "rip all and select which to save". The automatic law
needs none of them.

## Specification

1. Rip removes every Precondition and Postcondition the ripped Tag bound
   on the Agent.
2. Where the ripped Tag's condition was laid over a prior condition of
   the same name (a Shape over its Base with or without `@Underlay`, an
   independent Tag over another), the prior condition whose Tag is still
   active becomes visible again. If no such prior exists, the name is
   free.
3. Ripping a Tag whose condition is not the visible one (another Tag has
   laid over it) changes nothing: the visible condition is the other
   Tag's composition, and it ends with that Tag.
4. Ripping a Base is still refused while a Shape requires it (§0.7), so
   a Shape's `@Underlay` condition never loses the Base check it calls.
5. Pins follow the same rule with the Tag as Agent.
6. Contributions remain sticky (§0.7). Only conditions end.

## Rationale

A condition is a necessity the Tag declares, not something the Agent
became. Necessary to enter, necessary to stay; once the Agent is no
longer in, there is nothing to stay in. A necessity that must outlive a
role belongs to a Tag the Agent still carries: "selecting which
conditions to save" is the Geometry, not a list. With the automatic law,
the per-name deletes, the shortcut and the modifier are all unneeded, and
the `@Rip` protocol stays what it is, a teardown.

## Backwards compatibility

A program that relied on a Ripped Tag's promise still binding the Agent
now sees the Agent as sound under that name. No spelling changes.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Sticky conditions, deleted by name in the teardown (`@Rip @Delete`) | Rejected: a line per promise, and one forgotten line leaves a ghost promise on a Rogue Agent |
| A modifier for a promise that survives Rip (`@Post @Lasting`) | Set aside: no real use that a second Tag does not express better |
| A language shortcut to rip all conditions (`del ~Tag[agent]`) | Rejected: the common case should need no spelling; an obscure one is worse than a line |
| `@Public + @Rip`, `@Pre + @Post + @Rip` | No coherent meaning; a Rip is a teardown protocol and already a callable Action |
| A reserved codeword | Against the namespace principle (§0.8) |

## Acceptance requirements

Covered by `tests/test_topkit.py::ConditionsEndWithMembershipTests`.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
>
> *Drafted for the Director's confirmation:* Cleared on 2026-09-07, per the
> Director's "go on" to the recommendation.
