# STEP-SPEC-41: Synchronous Protocol Results

- **STEP:** SPEC-41
- **Desk:** spec
- **Title:** Synchronous Protocol Results
- **Author:** Codex, recording the protocol-result review
- **Status:** Brief
- **Created:** 2026-10-12
- **Issue:** [#84](https://github.com/JulTob/Tag_Oriented_Programming/issues/84)
- **Implementation proposal:** [#88](https://github.com/JulTob/Tag_Oriented_Programming/pull/88)

## Summary

Propose that Preconditions, Imprints, Postconditions and Rip protocols
complete their work synchronously. A protocol returning deferred native
execution fails at its phase; an implementation does not silently treat
unexecuted work as a completed protocol or automatically drive it.

TopKit already rejects Python coroutine, generator and async-generator
results in PR #88. That is currently a Python implementation boundary.
Making the restriction a language-wide TOP rule requires the Director's
decision; this Brief does not amend the Specification.

## Motivation

Calling a Python `async def` or generator function can return an object
without running its body. A discarded Imprint or Rip result can therefore
skip intended training or cleanup. Strict Pre/Post verdicts already
reject such results, but discarded coroutines can also produce warnings.

The repair must preserve named failures and continue remaining Rip
teardowns. Optional metadata such as a callable's `__name__` must not
replace a protocol failure with an unrelated diagnostic exception.

## Proposed specification

1. A Pre, Imprint, Post or Rip invocation is a synchronous protocol
   boundary. Returning deferred protocol execution is a failure;
   TOP does not implicitly await or iterate it.
2. The existing phase and failure identity remain. A refused Gate does
   not apply its Tag. Failed training retains acquired Gains on a Rogue
   outside that Tag's Field under the approved admission design in
   [STEP-SPEC-39 / PR #78](https://github.com/JulTob/Tag_Oriented_Programming/pull/78).
   A Post failure judges an admitted member. Rip collects ordinary
   protocol/disposal failures after ending membership and attempting the
   remaining teardowns. Python interruptions retain their propagation
   behavior and may stop further cleanup.
3. Pre/Post verdicts remain strictly True, False or None. This proposal
   does not introduce truth coercion or new meanings for other Imprint
   or Rip return values.
4. A Record builder's returned object is its stored value. Ordinary
   Actions and Operations may return deferred or streaming work; this
   proposal governs their invocation as a protocol, not every call to
   an Action that also carries a Rip mark.
5. Error reporting uses the declared protocol name and preserves the
   original cause when available. Cleanup of a rejected result must
   not silently hide its protocol failure.

## Python implementation boundary

Current TopKit recognizes the actual native coroutine, generator and
async-generator types without evaluating a result's `__class__` hook.
It attempts synchronous closure of coroutines and generators. It does
not start an event loop to drive an async generator.

Closing an already-started object can run pending `finally` code and can
itself fail. Rejection is not a general rollback or side-effect sandbox.
Arbitrary awaitable wrappers and future explicit async TOP protocols
need their own stated support boundary; native-result detection does
not prove that every user function has completed all external work.

## Alternatives

- Keep this exclusively as TopKit's synchronous Python profile boundary.
  Other implementations would state and test their own execution model.
- Adopt synchronous completion as TOP law, then design any future async
  protocol as an explicit separate feature.
- Automatically await or iterate every result. This would change return
  semantics, scheduling, failure timing and teardown behavior, so it is
  not proposed by this repair.

## Acceptance if cleared

- Native lazy returns fail under the declared Pre, Imprint, Post or Rip
  name, including callable objects with absent or hostile metadata.
- Later Rip teardowns still run after ordinary protocol/disposal failures,
  and membership has already ended. Python interruptions remain distinct.
- Rejected native coroutines and generators receive a synchronous close
  attempt within the stated Python limits, without starting their bodies
  unnecessarily; a failed close is reported rather than treated as proof
  that the result was disposed of.
- Caught Underlay failures cannot make an unfinished composed Rip pass.
- Ordinary Action result and stored Record semantics remain intact.
- Tests cover current Tagging admission and original disposal causes.

### Decision

Pending the Director's review. Choose whether this is a universal TOP
rule or a TopKit Python implementation boundary before adding its
requirements to the Specification or conformance-law tables.
