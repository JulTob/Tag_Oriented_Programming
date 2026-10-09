# STEP-SPEC-35: Population membership at each turn

- **STEP:** SPEC-35
- **Desk:** spec
- **Title:** Population membership at each turn
- **Author:** Codex, extracting the Director's approved rule
- **Status:** Cleared
- **Created:** 2026-10-10

## Summary

A population walk saves join-order turns when it begins, but membership
stays live. Each saved Agent or Tag is visited only if it belongs to that
Field when its turn arrives.

## Motivation

Before this change, `_Field.__iter__` returned every object that was a
member at the start. An earlier turn could Rip a later member and the
later member would still be yielded. The loop then acted on an object
that was no longer in the population it was walking.

## Specification

1. When a Field's part of a walk begins, it saves its current members in
   join order. New members have no turn in that walk and wait for the next.
2. At each saved turn, TOP asks whether the same object is currently a
   member of that Field. If it was Ripped, the turn is skipped.
3. If that object was Ripped and tagged again before its turn, it is a
   member again and is visited once at the saved turn. Its new place in
   the live Field does not add a second turn to the current walk.
4. Re-Tagging after an object's saved turn does not revisit it.
5. The rule applies to a Tag's sound population, `Tag[:]`, `~Tag`, Pins
   and every Field reached through `|`, `&` and `-`. Soundness and live
   operands are still evaluated at the member's turn.
6. `bool` and `len` follow the same membership-at-turn rule as iteration.
   A destructive condition check cannot make those questions count a
   member that the corresponding iteration would skip.

## Rationale

The starting order gives a loop stable turns without turning the Field
into a stale list. Asking membership at the turn preserves TOP's direct
meaning: a Ripped Agent is out; a freshly tagged Agent is in. Holding the
starting objects strongly for that one walk keeps their identities stable
without changing the Field's weak ownership.

For a combined population, each underlying Field begins its walk when the
operator reaches that side. `&` and `-` continue asking their right side
live at each left-side turn; this STEP changes no algebraic meaning.

## Backwards compatibility

A loop no longer yields a later member after an earlier iteration Rips it.
Code that intentionally retained the old starting membership can write
`members = list(population)` before performing its acts. Join order,
weak ownership, soundness and combination operators otherwise keep their
existing behavior.

## Alternatives considered

- Freezing membership for the whole walk was rejected because it calls a
  Ripped object a member after it has left.
- Iterating the live dictionary directly was rejected because new members
  would enter the current walk and mutation would invalidate iteration.
- Tracking the original weak-reference seat was rejected because Rip and
  re-Tagging creates a new seat even though the same Agent is in again.

## Validation

Focused regressions cover sound, whole and defective Tag views, Pins, all
three combined operators, Rip, re-Tagging before and after a saved turn,
new members, and agreement among truth, length and iteration.

### Decision

The Director decided on 2026-10-09: "If the agent is in, it was tagged,
if the agent was ripped it's out so it does not make it to the list, and
if an agent is tagged again, it is in the list so you shouldn't skip it."
This focused STEP records that decision as **Cleared** without importing
the unresolved filters, picks, safehouse or deletion proposals from the
earlier broad draft of STEP-SPEC-29. STEP-SPEC-29 itself is reserved for
the separately extracted absorbing-`~` rule.
