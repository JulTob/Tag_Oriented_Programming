# STEP-SPEC-33: Contribution presence by name

- **STEP:** SPEC-33
- **Desk:** spec
- **Title:** Contribution presence by name
- **Author:** Codex, recording the Director's approved design
- **Status:** Cleared
- **Created:** 2026-10-09

## Summary

An Agent answers whether it currently provides a named Contribution.
The Python spelling is `"name" @ agent`, read as "name at agent".
The answer is a Boolean, independent of the Contribution's kind, origin
or value. A Tag-bound view answers from its captured Overlay.

## Motivation

A Post needs to distinguish a missing gain from a gain whose value is
`False` or `None`. Actions and Records can change kind as Layers arrive;
requiring an Action or Record identifier would make the question depend
on that implementation choice. Contributions supplied by the Python host
must participate in the same question.

## Specification

1. A string at an Agent asks about the current binding of that name.
   A stored `False`, `None`, zero or empty value is present. A declaration
   or stale registry entry without a binding is absent.
2. The query does not execute an Action, Operation, Report builder,
   property getter or Postcondition. A host property counts as a binding;
   successful reading or calling is a separate requirement. An unfilled
   host slot is absent. Names synthesized only by `__getattr__` do not count.
3. TOP and host bindings count alike. The question requires no indication
   of Contribution kind or declaring Tag.
4. Secret names follow the Agent's composition door. Shared names on the
   Agent require publication. A published Report requires its active
   publisher; a published Operation's sticky Action can remain present
   after Rip even though its use is refused.
5. `"name" @ Tag[agent]` checks the Tag view's captured Contributions,
   including shared Contributions, and respects the composition door.
   It does not certify that the live Agent still provides the same name.
6. The query evaluates no Postconditions. A Post can require presence;
   absence of an optional Contribution does not itself add a failing Post.
7. The Python operator is installed on TOP Agents, including pinned Tags,
   and Tag-bound views. A raw host before its first Tagging, including its
   first Precondition, has no TOP presence operator. A bare unpinned Tag
   receives no new presence API.
8. String left operands select this meaning. Other operands preserve the
   effective host or Tag matrix-operator behavior and Python dispatch order.

## Rationale

The Agent is the subject of the question. A name remains useful as its
Contribution changes between data and behavior. Presence can be composed
with ordinary Boolean expressions, assertions, Posts and Field selection
without adding a helper function to TOP's vocabulary.

## Backwards compatibility

String-left matrix multiplication on an Agent now asks about presence,
including when the host or a Tag supplies `__rmatmul__`. Nonstring matrix
operands keep their prior behavior. Existing membership, Field selection,
Contract lifecycle and deletion rules are unchanged by this STEP.

## Alternatives considered

- Kind-qualified queries were set aside because Contributions change kind.
- Queries against a Tag declaration were set aside for the Agent-led query.
- Reading the value or using `hasattr` would conflate inspection with
  execution and would not express the agreed TOP question.

## Validation

The implementation has 27 presence regressions, including false values,
missing bindings, kind changes, host Contributions, Secret and publication
boundaries, snapshots, Pins, getter-free inspection, matrix dispatch and
Underlays. The wiki page's seven Python examples run in the document suite.

### Decision

The Director approved the name-based `@` design in the task conversation:
"I like it. @ is read as 'at' ... let's make it happen", and clarified that
Actions and Records change category, so no kind identifier is needed.
On 2026-10-09 the Director explicitly authorized merging the tested feature
and publishing its wiki page. This records that approval as **Cleared**;
it does not introduce a separate design decision.
