# STEP-SPEC-31: Retire Scope

- **STEP:** SPEC-31
- **Desk:** spec
- **Title:** Retire Scope
- **Author:** Codex, recording the Director's approved design
- **Status:** Cleared
- **Created:** 2026-10-09

## Summary

`TopKit.Scope` is removed. A program that holds a Tag for a block writes
the lifecycle directly in Python: tag before `try`, then Rip in `finally`.
TOP reserves no automatic membership meaning for `with`; ordinary Python
context protocols remain available to hosts and Agent Actions.

## Motivation

`Scope(agent, Tag)` hid several different program decisions behind a
library function: whether an existing membership belonged to the block,
whether a Tag that landed and then failed should be Ripped, and whether a
failed Rip should surface. That spelling felt forced rather than part of
TOP's language. Python already has the exact visible control flow needed.

## Specification

1. `Scope` is absent from `TopKit`, `TopKit.__all__` and the lifecycle API.
2. To hold a Tag for a block, apply it before the `try` and Rip it in the
   `finally`:

   ```python
   Sentry(guard)
   try:
       guard.Patrol()
   finally:
       del Sentry[guard]
   ```

3. Ordinary Tagging and Rip semantics apply. A refusal before the `try`
   does not run the block. A Tagging that lands and then reports a failure
   remains tagged. A Rip failure in `finally` is not swallowed.
4. If a block must preserve a membership the Agent already had, it records
   that fact before Tagging and Rips only a membership it introduced. With
   several Tags, the program states its own application and Rip order.
5. TOP gives `with` no automatic Tagging or Rip rule. A host's normal
   synchronous or asynchronous context protocol is preserved. Context
   dunders supplied as Agent Actions remain normal Python behavior too.

## Rationale

The explicit form uses Python's own lifecycle syntax and keeps every TOP
act visible. It also leaves `with` free until a use arises naturally,
without blocking ordinary context managers that a program already owns.

## Backwards compatibility

Importing `Scope` now fails. Replace `with Scope(agent, Tag): ...` with the
explicit `Tag(agent)` / `try` / `finally` / `del Tag[agent]` form, deciding
openly whether pre-existing memberships and Rip failures need special
handling.

## Alternatives considered

- Keeping `Scope` only as a convenience was rejected because it retained
  the forced vocabulary and its hidden policy choices.
- Giving all TOP objects a context protocol was rejected. TOP does not
  claim `with`; programs remain free to define ordinary context Actions.
- Redesigning `with` immediately was deferred until a TOP need fits the
  syntax naturally.

## Validation

The tests cover removal from the public API, the explicit `try` / `finally`
forms and failure paths, preservation of host context managers, and Agent
Actions implementing synchronous and asynchronous context protocols. The
oracle and differential fuzz program use the explicit lifecycle form.

### Decision

The Director decided: “Remove Scope; preserve ordinary Python contexts,”
and asked to leave `with` free until a fitting TOP use arises naturally.
This STEP records that accepted design as **Cleared**; it adds no separate
decision.
