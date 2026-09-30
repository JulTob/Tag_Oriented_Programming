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
5. **`Wizard | None` keeps the language's meaning; `Wizard | Fighter`
   does not.** A Tag is a class, and `|` with anything that is not a
   population or a Tag falls back to the language's own class union.
   Between two Tags the union is a population, not a type:
   `isinstance(x, Wizard | Fighter)`, `Wizard | Fighter | None` and
   `None | (Wizard | Fighter)` are refused with a `TypeError` naming the
   rewrite, `isinstance(x, (Wizard, Fighter))` and
   `typing.Optional[typing.Union[Wizard, Fighter]]`. Python 3.10 to
   3.13 evaluate `x: Wizard | Fighter | None` at definition, so it fails
   there; 3.14 when the annotations are read. The Director, 2026-09-29:
   "Wizard | Fighter should mean a valid fighter OR a valid Wizard, so
   it is present. A simple isinstance(wizard) or isinstance(fighter)
   can satisfy the other cases, which are rare and not good practice.
   Wizard[:] | Fighter[:] would mean broken wizards or good wizards or
   broken fighters or good fighters, all active agency, all members in
   the sets (broken or not)."
6. Pins are Tags, so a Pin's populations combine the same way over Tags.
   Among themselves: a Pin's population holds Tags and a Tag's holds
   objects, and combining the two in `|`, `&` or `-`, in either order
   and at every level (`Rare[:] & Wizard`, `~Rare - Wizard`, `(Rare[:]
   | Meta) | Wizard`), is refused with a `TypeError` that names both
   sides and says which holds Tags and which objects. The Director:
   "Refuse".
7. Tag-ness in an operator seat is decided by type (the Tag's
   metaclass), never by an attribute named `_sound`: `Wizard |
   SomeClass` where `SomeClass` has its own `_sound` is the language's
   class union, and a Tag declaring a member `_sound` still iterates.

## Rationale

One small class, no kernel change, no new vocabulary: the three
operators are the ones a set has, and the two levels are the ones §2.5
already draws. Laziness is what a Field already is (weak, live,
identity-indexed); a copied result would be a different thing with a
different truth a moment later.

## Backwards compatibility

One spelling changes meaning. In 0.2.0a3 `Wizard | Fighter` was
Python's class union, usable in `isinstance` and in annotations; now it
is a population. `isinstance(x, Wizard | Fighter)`, `issubclass` over
it, and `|` between it and `None`, a class, a union or a `typing` form
are refused with the one-line rewrite in the message: `isinstance(x,
(Wizard, Fighter))`, and for a hint `x: Wizard | Fighter | None`,
`typing.Optional[typing.Union[Wizard, Fighter]]`. A plain hint `x:
Wizard | Fighter` is not refused: it now holds a population, and code
that reads it as a type (`typing.get_type_hints` and then
`isinstance`, or a runtime validator) fails there; write
`typing.Union[Wizard, Fighter]`. The same holds for a union built first
that takes the population in: `typing.Optional[Wizard | Fighter]`, a
`typing` form's own `|`, or on Python 3.14 `(int | str) | (Wizard |
Fighter)`. `Wizard | None` is unchanged. `|`, `&` and `-` on Fields
and views were errors before. Combining two different Tags, and `&`,
are new: the archived 0.2-alpha line combined only views of one Field
and had no `&`. `in` on a combined view follows STEP-SPEC-19: it
answers from the sides, as a set does, and agrees with the loop.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Union only | Set aside: `-` is the roster-of-the-missing case, `&` costs nothing more |
| Each level only with its own kind | Rejected: a population is a population; refusing `Wizard[:] - Sworn` would need a rule nobody can guess |
| Eager results (a list) | Rejected: a Field is live; a snapshot would disagree with the next `in` |
| `~` on a combined view | Rejected: no universe to complement |
| A population that is also a type (answers `isinstance`, unions with `None`) | Rejected: one seat, one meaning; the rewrite is one line |
| A Pin's population combined with a Tag's | Refused by the Director: "Refuse" |
| A named failure for the refusals | Set aside: a `TypeError`, as Python refuses `set \| list`; no named failure of STEP-SPEC-8 fits, and a Composition Failure is an Overlay's |

## Acceptance requirements

Covered by `tests/test_topkit.py::FieldAlgebraTests` and by the oracle
(`tests/oracle_topkit.py`, `Assert_Fields`), which checks the three
operators against its model after every seventeenth transition. The
refusals: a Pin's population with a Tag's in both orders, the three
operators, on Tags, `[:]`, `~` and nested combinations, the message
naming both sides, and a combination taking its kind from its other
side when one side's Tag is gone; `isinstance` and `|` with `None`, a
class, a union, `list[int]` or a `typing` form, in either order, naming
the rewrite, and a hint in a signature where Python evaluates it; a
plain hint and a union built first holding a population until
`isinstance` reaches it; a class with its own `_sound` giving the class
union, and a Tag declaring `_sound` still iterating. The fuzzer asks
the refusals too.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
>
> *Drafted for the Director's confirmation:* Cleared on 2026-09-29. The
> origin is the Director's review of the archived features on
> 2026-09-21: "Bring it back, both levels." On 2026-09-29 the Director
> ruled on `|`: "Wizard | Fighter should mean a valid fighter OR a valid
> Wizard, so it is present. A simple isinstance(wizard) or
> isinstance(fighter) can satisfy the other cases, which are rare and
> not good practice. Wizard[:] | Fighter[:] would mean broken wizards or
> good wizards or broken fighters or good fighters, all active agency,
> all members in the sets (broken or not)." And on mixing a Pin's
> population with a Tag's: "Refuse". `in` on populations was made
> consistent with the loop by STEP-SPEC-19, shipped with this STEP in
> 0.2.0a4.
