# STEP-SPEC-53: Posts at Each Tag Turn

- **STEP:** SPEC-53
- **Desk:** spec
- **Title:** Posts at Each Tag Turn
- **Author:** Codex, recording the Director's 2026-10-20 ruling
- **Status:** Brief
- **Created:** 2026-10-20
- **Issue:** [#369](https://github.com/JulTob/Tag_Oriented_Programming/issues/369)
- **Amends, if cleared:** [STEP-SPEC-39](STEP-SPEC-39-tagging-admission.md), rule 5 and its Rationale

## Summary

Judge an Agent's visible Posts after **each completed Tag turn**, before the
next Tag in a Form begins its Gate. A Form orders independent Taggings; it does
not defer their contract checks until the whole Form has run. This is a
proposal recording the Director's ruling. It changes no runtime behavior
while it remains a Brief.

## Current rule and reason for change

Cleared STEP-SPEC-39 says, “Once the whole Form finishes, every visible Post
checks the resulting Agent.” Current TopKit follows that timing. Consequently
a Base can enter its Field with a failing Post and a later Shape can start
training before that failure is reported. The Director ruled that Posts are
checked **on each Tagging**: layering does not make the earlier Tag's promise
wait for a later layer.

For example, `Body` declares a Post `Sound`, and `Vehicle(Body)` is a Shape.
Applying `Vehicle(car)` first applies `Body`. If `Body`'s `Sound` fails after
Body's admission, TOP must report that failure before Vehicle's Gate or Gains
run. The car remains admitted to `Body[:]`; it belongs to Body's broken
population when it is free and its Posts fail. Vehicle has not yet started.

## Proposed rule

1. Keep STEP-SPEC-39's independent Base-first Tag turns and the within-Tag
   order **Gate → Gainings → Imprints → Field → Posts**. Once a Tag finishes
   its Field entry, evaluate the Agent's currently visible Posts for that
   turn. Only then consider the next Tag's Gate.
2. A failed Post does not undo that Tag's Field entry, Gains, or earlier
   completed Taggings. It stops progression to the next Tag turn and reports
   the contract failure through the existing named Post diagnostics.
3. A later Shape does not implicitly supply what an earlier Base promised.
   If that relationship is wanted, the programmer must express it through
   an explicit protocol that is valid at the time of the Base's check.
4. This STEP does not change which Posts are visible, how a Post computes its
   verdict, or how sound and broken Field populations are queried. The
   separate valid-source rule will govern attempts to start an unrelated
   Tagging on an already unsound Agent.

## Boundary with other work

The Director subsequently chose best-effort Imprints: an Imprint failure may
still admit an Agent, with training diagnostics and final Posts judging it.
That change requires its own amendment to STEP-SPEC-39 ([#368](https://github.com/JulTob/Tag_Oriented_Programming/issues/368)).
Record preparation, `@Fix` recovery, and sound-source admission also have
separate designs. This Brief chooses **when** to judge Posts between Tag
turns, not those training or recovery mechanisms.

## Compatibility and acceptance

This reverses STEP-SPEC-39's whole-Form Post timing. Programs that relied on
a later Shape repairing a Base's failing Post before any check must move
that repair into the Base's own training or an explicit earlier step.

Acceptance requires a Form test in which Base admits an Agent with a failing
Post: Base remains in `Base[:]`, Shape's Gate and Gains do not run, and the
failure names the Base Post. A passing Base proceeds to Shape's Gate. A
later independent Tag failure must preserve Tags already completed.

---

### Decision

> **Brief.** The Director ruled on 2026-10-20 that Posts are checked after
> each Tagging, because a Form is layering of independent Tags. Clearance and
> implementation remain separate review steps.
