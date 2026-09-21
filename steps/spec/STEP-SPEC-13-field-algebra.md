# STEP-SPEC-13: Field Algebra

- **STEP:** SPEC-13
- **Desk:** spec
- **Title:** Field Algebra
- **Author:** Julio Toboso (@JulTob)
- **Status:** Vetting
- **Created:** 2026-09-21

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

Populations combine. `Wizard | Fighter` is the sound population of either,
`Wizard & Fighter` the sound Agents who are both, `Wizard - Sworn` the
sound Wizards who have not sworn. The same three operators work on whole
Fields (`Wizard[:] | Fighter[:]`) and on the defective views (`~Wizard |
~Fighter`), and the levels mix (`Wizard[:] - Sworn`). A Tag in an
operator seat means its sound population, as it does in `for w in
Wizard`. The result is a lazy view: it reads the Fields when it is
walked, never copies them, and keeps application order.

## Motivation

The 0.2-alpha line had union and difference on Fields; the 0.2.0a2
rewrite kept only `~Tag` and never said why. A battle loop over every
combatant regardless of class, a report of members missing a required
role, a roster of everyone who is either: each was a comprehension by
hand. Set arithmetic over roles is what Fields are for. Reviewed and
accepted by the Director on 2026-09-21: "Bring it back, both levels."

## Specification

1. Three operators on any population: `|` (either), `&` (both), `-`
   (the left without the right). A population is a whole Field
   (`Tag[:]`), a sound view (`Tag` itself in an operator seat), a
   defective view (`~Tag`), or the result of an operator.
2. **A Tag in an operator seat is its sound population.** `Wizard |
   Fighter` reads as `for w in Wizard` does. `Wizard[:] | Fighter[:]` is
   everyone. The levels mix: `Wizard[:] - Sworn` is everyone who is a
   Wizard and not a sound Sworn.
3. **Lazy, ordered, identity-keyed.** A combined view holds its two
   sides, not their members. `|` walks the left then the right, each
   Agent once, by identity; `&` walks the left and keeps those in the
   right; `-` walks the left and drops those in the right. Application
   order is kept within each side. An Agent that joins after the view
   was made is in it; one that is repaired moves from the defective side
   to the sound side.
4. A combined view answers `in`, `len`, truth and iteration like any
   population. It does not answer `~`: the complement of a union has no
   universe.
5. **`Wizard | None` keeps the language's meaning.** A Tag is a class;
   `|` with anything that is not a population or a Tag falls back to the
   language's own class union, so type annotations are untouched.
6. Pins are Tags, so a Pin's populations combine the same way over Tags.

## Rationale

One small class, no kernel change, no new vocabulary: the three
operators are the ones a set has, and the two levels are the ones §2.5
already draws. Laziness is what a Field already is (weak, live,
identity-indexed); a copied result would be a different thing with a
different truth a moment later.

## Backwards compatibility

No spelling changes meaning. `|`, `&` and `-` were errors on Fields and
Tags before; `Wizard | None` behaved as it does now.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Union only | Set aside: `-` is the roster-of-the-missing case, `&` costs nothing more |
| Each level only with its own kind | Rejected: a population is a population; refusing `Wizard[:] - Sworn` would need a rule nobody can guess |
| Eager results (a list) | Rejected: a Field is live; a snapshot would disagree with the next `in` |
| `~` on a combined view | Rejected: no universe to complement |

## Acceptance requirements

Covered by `tests/test_topkit.py::FieldAlgebraTests` and by the oracle
(`tests/oracle_topkit.py`, `Assert_Fields`), which checks the three
operators against its model after every seventeenth transition.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
>
> *Drafted for the Director's confirmation:* Cleared on 2026-09-21, per
> the Director's review of the archived features: "Bring it back, both
> levels."
