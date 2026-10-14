# STEP-SPEC-35: Population membership at each turn

- **STEP:** SPEC-35
- **Desk:** spec
- **Title:** Population membership at each turn
- **Author:** Codex, extracting the Director's approved rule
- **Status:** Cleared
- **Created:** 2026-10-10

## Summary

Membership stays live during a population walk. An Agent or Tag that was
Ripped is out; the same object tagged again before its turn is in again.
TopKit keeps its existing saved join-order turns when applying this rule.

## Motivation

Before this change, `_Field.__iter__` returned every object that was a
member at the start. An earlier turn could Rip a later member and the
later member would still be yielded. The loop then acted on an object
that was no longer in the population it was walking.

## Specification

At an Agent's or Tag's turn in a Field walk, membership is current. A
member Ripped before that turn is skipped. If the same object was tagged
again before its turn, it belongs again and must not be skipped merely
because it was previously Ripped.

## TopKit implementation and preserved behavior

The details below describe the Python kit's implementation of that ruling.
They preserve its existing saved turns, join order and lazy operand timing;
they are not additional traversal laws cleared by the Director's quote.

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
6. After judging a partition's condition, TopKit checks membership in that
   Field again. Its truth and length paths use the same membership checks
   as iteration. Each call is a separate live walk; conditions that change
   state can therefore produce different answers on successive calls.

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
Code that needs to retain what one walk yields can write
`members = [member for member in population]` before performing its acts.
The built-in `list(population)` may first ask `len(population)` for a size
hint, which is a separate live walk and can repeat Postconditions; it is
not the one-pass snapshot spelling. Join order, weak ownership, soundness
and combination operators otherwise keep their existing behavior.

## Implementation alternatives considered

- Freezing membership for the whole walk was rejected because it calls a
  Ripped object a member after it has left.
- Iterating the live dictionary directly was rejected because new members
  would enter the current walk and mutation would invalidate iteration.
- Tracking the original weak-reference seat was rejected because Rip and
  re-Tagging creates a new seat even though the same Agent is in again.

## Validation

Focused regressions cover sound, whole and defective Tag views, Pins, all
three combined operators, Rip, re-Tagging before and after a saved turn,
new members, agreement among truth, length and iteration, and the explicit
one-pass materialization pattern.

### Decision

The Director decided on 2026-10-09: "If the agent is in, it was tagged,
if the agent was ripped it's out so it does not make it to the list, and
if an agent is tagged again, it is in the list so you shouldn't skip it."
This focused STEP records that membership ruling as **Cleared**. The quote
does not separately clear snapshot timing, new-member scheduling, saved
positions, operand timing or Python length hints; those details above
document TopKit's implementation and preserved behavior. No unresolved
filters, picks, safehouse or deletion proposals are imported from the
earlier broad draft of STEP-SPEC-29. The separately extracted absorbing-`~`
rule is recorded in [STEP-SPEC-38](STEP-SPEC-38-absorbing-defective-population.md).
