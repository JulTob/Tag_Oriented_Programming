# STEP-SPEC-4: Defective Taggings and Field Partitions

- **STEP:** SPEC-4
- **Desk:** spec
- **Title:** Defective Taggings and Field Partitions
- **Author:** Julio Toboso (@JulTob)
- **Status:** Vetting
- **Created:** 2026-09-04

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

A Tagging whose Postcondition fails is **applied and defective**: the call
raises, the Tags stay, and the Agent is a member whose promise is broken.
An Imprint failure likewise leaves the Tags applied. Preconditions and
Record failures still roll the whole call back.

Fields partition into the **sound** population (`Tag[:]`) and the
**defective** one (`~Tag[:]`); their union is the Field. The plain loop
over a Tag is the whole Field.

## Motivation

The factory analogy: a Precondition inspects the incoming materials and may
refuse them; nothing is produced. A Postcondition inspects the finished
product. A defective product is not melted back to materials; it is flagged
and repaired, or thrown away. Rolling back a finished product hides the
defect and loses the work of every Base and Imprint in the call.

The second half (partitions) is what makes defective members manageable:
gameplay loops over sound members, repair loops over defective ones, and
nobody disappears from a plain loop silently.

## Specification

1. The tagging sequence: once per call, the gate (the Preconditions
   visible in the composed Form of the call, so a Shape relaxes its Base);
   then per Tag in the Form: parts, commit, write; then once per call,
   after the whole Form: quality check (every visible Postcondition).
2. A failure in gate or parts, for any Tag in the Form, rolls the whole
   call back (STEP-SPEC-6 keeps that law).
3. A failure in write raises a Tag Imprint Failure; the Tags stay.
4. A failure in quality check raises a Tag Postcondition Failure; the Tags
   stay; the Agent is defective while any visible Postcondition fails.
5. `bool(agent)` is true exactly when every visible Postcondition holds.
   A host's own truthiness is kept until a Postcondition is visible.
6. `Tag[:]` iterates and tests membership of the sound population;
   `~Tag[:]` the defective one; `Tag[:] | ~Tag[:]` is the Field; iterating
   the Tag itself is the whole Field.
7. Postconditions take no application inputs.

## Rationale

Checking Postconditions once per call, after the whole Form, lets a Base
promise what its Shape delivers ("an Element has an attack"). Checking
per Tag would refuse every such Base at its own step.

The plain loop is the whole Field because a defective Agent that vanishes
from `for wizard in Wizard` is the silent failure this STEP exists to
prevent. The partitions are one character away.

## Backwards compatibility

Programs that relied on a failed Postcondition rolling back must Rip the
defective Tag themselves, or check `bool(agent)` after the call. The
`CONFORMANCE.md` line "atomic taggings, all-or-nothing" is reworded: gate
and parts are atomic; write and quality check are not.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Roll back on any failure (0.1 behaviour) | Rejected by the Director: a product is not unmade |
| Author chooses per Tag | Set aside; two laws to explain |
| Default iteration is the sound population (0.2 alpha) | Rejected; hides members from the most basic loop |
| Uniform access (`agent.hp()` and `agent.hp`) | Redacted with this STEP's review: it returns a proxy that leaks into host code and violates "explicit before magical" |

## Acceptance requirements

Covered by `tests/test_tagkit.py::DefectiveTaggingTests`.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
>
> *Drafted for the Director's confirmation:* Cleared on 2026-09-04, per the
> Director's direction in review ("If a product leaves a factory defective
> you don't roll it back to materials, you try fixing it first, or delete
> it"; partitions spelled `Wizard[:]` and `~Wizard[:]`).
