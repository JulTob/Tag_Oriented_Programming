# STEP-SPEC-5: Records Receive the Stored Value

- **STEP:** SPEC-5
- **Desk:** spec
- **Title:** Records Receive the Stored Value
- **Author:** Julio Toboso (@JulTob)
- **Status:** Deployed
- **Created:** 2026-09-04
- **Deployed:** 2026-09-05

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

A Record builder may declare a second positional parameter. It receives the
value already stored under that name on the Agent, or `None` when there is
none. The author writes the merge. Independent Tags can therefore **pile
up** on one Record, in application order, without naming each other.

```python
class Elf(Species):
    @Record
    def spells(agent, stored):
        return (stored or []) + ["Light"]
```

## Motivation

The inspiration for TOP is character creation: species, class, background
and feats are independent, and the spell list is written by all of them.
Before this STEP the last Tag won unless each one used `@Underlay`, whose
Record form passed a callable (`underlay()`) and failed when nothing was
stored, so unrelated Tags could not compose a list without knowing which
came first.

## Specification

1. A Record builder with one positional parameter replaces. With two, the
   second receives the stored value or `None`.
2. "Stored" is the Agent's current value under that name: a prior Record,
   or an ordinary attribute the host already had. A name deleted by a Tag,
   or occupied by an Action, yields `None`.
3. `@Underlay` on a Record is accepted as documentation and means the same
   thing.
4. A replacing builder (one parameter) that overwrites an independent Tag's
   Record is diagnosed with an Overwrite Warning. An extending builder is
   silent.
5. Actions keep the callable Underlay and keep failing when none exists:
   behaviour has no natural empty value; data has `None`.
6. Application inputs bind by name to a builder's parameters after the
   Agent and the stored value, so `def code(agent, *, code)` stores the
   input directly. A second positional parameter named like a supplied
   input is refused with a Declaration Failure that shows the keyword-only
   spelling.

## Rationale

The user writes `return stored + new` and `if stored is None`. No merge
registry, no strategy names, nothing to look up: the merge is the one line
the author would have written anyway.

## Backwards compatibility

Record builders that took `underlay` as a callable must drop the `()`.
Builders that relied on a resolution error when nothing was stored must
test for `None`.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Named merge strategies (`add`, `union`, `sum`, `max`) | Set aside; the author's line is shorter than the strategy name |
| Collections only pile up, numbers replace | Rejected; hit points from several sources are the common case |
| Keep the callable form for Records | Rejected; a value is not a call |

## Acceptance requirements

Covered by `tests/test_tagkit.py::RecordTests`.

---

### Decision *(filled by the Director)*

> Status set to **Deployed** on 2026-09-05, because the Director approved
> the whole review in PR #3 ("all changes approved"), the rule is
> reflected in `spec/SPECIFICATION.md`, and TagKit 0.2.0a2 covers it in
> `tests/test_tagkit.py`. Cleared on 2026-09-05, per the
> Director's direction in review ("a default input variable stored/new
> inside the record definition, like `return stored + new`, and
> `if stored is None: X`").
