# STEP-SPEC-4: Defective Taggings and Field Partitions

- **STEP:** SPEC-4
- **Desk:** spec
- **Title:** Defective Taggings and Field Partitions
- **Author:** Julio Toboso (@JulTob)
- **Status:** Deployed
- **Created:** 2026-09-04
- **Deployed:** 2026-09-05

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

A Tagging whose Postcondition fails is **applied and defective**: the call
raises, the Tags stay, and the Agent is a member whose promise is broken.
An Imprint failure likewise leaves the Tags applied. Preconditions and
Record failures still roll the whole call back.

Fields partition into the **sound** population (`for a in Tag`) and the
**defective** one (`for a in ~Tag`); `Tag[:]` is everyone. Membership
(`agent in Tag`) is unchanged by defect.

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
6. Iterating the Tag gives the sound population and `len(Tag)` counts
   it; `~Tag` is the defective population; `Tag[:]` is the whole Field.
   `agent in Tag` stays true for a defective member.
7. Postconditions take no application inputs.

## Rationale

Checking Postconditions once per call, after the whole Form, lets a Base
promise what its Shape delivers ("an Element has an attack"). Checking
per Tag would refuse every such Base at its own step.

The plain loop is the working population: gameplay iterates the Agents
fit to play, repair iterates `~Wizard`, and `Wizard[:]` is there when a
program wants everyone. A defective Agent never loses membership, so
guards on `in` keep working while it waits for repair. The spellings
follow the Director's rule that Tag-level acts use language syntax and
leave `Tag.name` to the program (Specification §0.8).

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
| Default iteration is the whole Field, `Tag[:]` the sound one | Rejected by the Director; the loop should be the working population, with `~Tag` one character away |
| `Tag.Field`, `Tag.Rip(agent)` as dotted methods | Rejected; `Tag.name` belongs to the program (§0.8) |
| Uniform access (`agent.hp()` and `agent.hp`) | Redacted with this STEP's review: it returns a proxy that leaks into host code and violates "explicit before magical" |

## Acceptance requirements

Covered by `tests/test_tagkit.py::DefectiveTaggingTests`.

---

### Decision *(filled by the Director)*

> Status set to **Deployed** on 2026-09-05, because the Director approved
> the whole review in PR #3 ("all changes approved"), the rule is
> reflected in `spec/SPECIFICATION.md`, and TagKit 0.2.0a2 covers it in
> `tests/test_tagkit.py`. Cleared on 2026-09-05, per the
> Director's direction in review ("If a product leaves a factory defective
> you don't roll it back to materials, you try fixing it first, or delete
> it"; partitions spelled `Wizard[:]` and `~Wizard[:]`).
