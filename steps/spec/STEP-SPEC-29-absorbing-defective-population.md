# STEP-SPEC-29: Absorbing Defective Population

- **STEP:** SPEC-29
- **Desk:** spec
- **Title:** Absorbing Defective Population
- **Author:** Codex, recording the Director's approved design
- **Status:** Cleared
- **Created:** 2026-10-09

> One STEP, one topic. This is the Cleared slice extracted from the broader
> population-algebra draft in PR #26. It decides only repeated `~`; the
> draft's other population spellings remain outside this STEP.

## Summary

`~Tag` is the Tag's defective population. Applying `~` to that population
does not return the sound population: `~` absorbs, so `~~Tag`, `~~~Tag`
and every longer run still mean `~Tag`.

## Motivation

TOP reads `~Wizard` as "broken Wizards", not as the set-theoretic
complement of Wizards. "Broken broken Wizard" is still a broken Wizard.
The previous implementation accidentally treated the second `~` as a
toggle and returned the sound population.

## Specification

1. `~Tag` remains the live defective population of that Tag.
2. Applying `~` to a defective Tag population returns that same
   population. Any non-empty run of `~` before a Tag therefore has the
   semantics of one `~`.
3. This does not make `~` a general population complement. A combined
   population still refuses inversion with `TypeError`; write the
   defective parts explicitly, such as `~Wizard | ~Fighter`.
4. Soundness, whole-Field selection, population algebra, membership,
   ordering and repair remain otherwise unchanged.

## Rationale

Absorption preserves TOP's domain word: `~` identifies the repair queue.
Returning the defective partition itself also preserves its live view;
repairing an Agent immediately removes it from every repeated-`~` spelling.

## Backwards compatibility

`~~Tag` previously selected the sound population and now selects the
defective one. Code that means the sound population should use the bare
`Tag`, just as it does in a loop. `~Tag` and combined-population behavior
are unchanged.

## Alternatives considered

- Boolean-style toggling was rejected because `~` means "broken", not
  logical negation.
- Inverting a combined population remains refused; this STEP does not
  introduce a universe or a general complement operation.

## Validation

Focused tests cover double, triple and long runs, empty and non-empty
defective populations, live repair, membership, length, truth, and refused
combined inversion. The randomized oracle checks `~~Tag` against its model.

### Decision

The Director decided on 2026-10-09: "Implement the 'bad bad = bad'
meaning of ~. ~~~~~~~~~~~~~Wizard is still ~Wizards." This records that
already-approved rule as **Cleared** and does not decide the other algebra
questions from PR #26.
