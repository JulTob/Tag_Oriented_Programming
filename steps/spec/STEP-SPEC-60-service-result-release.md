# STEP-SPEC-60: Recheck Authority Before Releasing a Service Result

- **STEP:** SPEC-60
- **Desk:** spec
- **Title:** Recheck Authority Before Releasing a Service Result
- **Author:** Codex, recording the Director's 2026-10-20 ruling
- **Status:** Brief
- **Created:** 2026-10-20
- **Issue:** [#389](https://github.com/JulTob/Tag_Oriented_Programming/issues/389)
- **Related:** [STEP-SPEC-3](STEP-SPEC-3-member-publication.md), [STEP-SPEC-10](STEP-SPEC-10-published-members-answer-members.md), [STEP-SPEC-40](STEP-SPEC-40-agent-contract-truth.md), [STEP-SPEC-41](STEP-SPEC-41-synchronous-protocol-results.md)

> One STEP, one topic. This Brief governs the point at which a published
> Report or Operation releases a result to one Agent. It does not define
> recursive Post evaluation, Service deletion, Safehouse arrest, or a
> multi-threaded execution profile.

## Summary

A published Report or Operation first checks whether the requesting Agent may
use it. Arbitrary user code can then run while the value is being prepared.
The Agent may leave the publishing Field, become Broken, lose a future
per-Agent Grant, or cross a Secret-door boundary before the result is ready.

The Director's rule is:

1. check live authority before protected work begins;
2. check it again before releasing a result whenever relevant Agent or access
   state may have changed;
3. omit the release check only when TOP can establish that the relevant state
   stayed unchanged.

The first check refuses early and avoids wasted work. The release check keeps
a result prepared under old credentials from escaping after those credentials
have gone away.

This Brief uses **Service** for a Tag-owned Report or Operation and **Grant**
for one Agent's path to a published Service, following the vocabulary proposed
in [issue #385](https://github.com/JulTob/Tag_Oriented_Programming/issues/385).
The rule is meaningful under the current Report/Operation terminology even if
that vocabulary STEP has not yet landed.

## Problem

The current public-member guard is an entry check. A synchronous Operation can
pass it, Rip its caller or make a Post false inside its body, and still return
protected data. A coroutine or generator widens the gap: creating the lazy
result can happen while authority holds, while its body and returned values run
later after authority changes.

A Report usually reads a stored Tag value, but Python descriptor, metaclass,
or other user code can run during resolution. An entry-only check is therefore
not a general release boundary.

STEP-SPEC-50's proposed Post memo solves a different problem. It prevents a
completed Post verdict from being reused across a Secret-door change inside
one validity query. It does not guard the result of the Service whose access
triggered that query.

## Proposed specification

### 1. The authority predicate

Each check asks the same live question the published access already asks:

- does the Agent still belong to the publishing Tag where active membership is
  required;
- does the Agent still have a Valid Contract;
- is the relevant Secret composition door open; and
- once Agent-level Service revocation exists, does this Agent still hold the
  Grant?

The check retains the existing specific failure. Membership loss, a Void
Contract, Secret denial, Grant revocation, and Safehouse arrest do not collapse
into one generic exception. The underlying Post failure and its cause remain
available.

A direct Tag-side protocol that does not act through an Agent Grant keeps its
own access law. This STEP does not project every internal Report or Operation
onto Agent access.

### 2. Synchronous Operations

A published synchronous Operation checks authority immediately before its body
runs. After the body returns, TOP checks again before handing the returned
object to the caller. If the second check fails, TOP discards the result and
raises that live access failure.

If the body raises, its exception remains primary because no Service result is
being released. This STEP does not run an extra authority check merely to mask
or replace that failure.

An Operation body is arbitrary user code. TOP must therefore assume relevant
state may have changed, even when no TOP mutation was observed: Posts may read
ordinary Python attributes, external state, time, or another Agent. A runtime
epoch is not proof that arbitrary user code preserved authority.

### 3. Reports

A published Report checks before resolution. When resolving the value can run
user code, TOP checks again before returning it. A plain stored value may use a
proven no-user-code fast path and omit duplicate Contract work.

Once a Report value has been returned, it is an ordinary Python object. TOP
cannot revoke a raw value already delivered to the caller. The rule controls a
new read, not all later uses of an old reference.

### 4. Lazy Operation results

For a coroutine or generator, authority is checked at execution and at every
continuation boundary:

- before resuming the body, so revoked work does not restart;
- after the body reaches a yield or return, before releasing that yielded item
  or final result;
- again at the next resume, because authority may change while the consumer
  holds the suspended object.

This includes a generator's `StopIteration.value` and a coroutine's awaited
result. Exceptions raised by the lazy body remain its own failures when no
item or final result is released.

The implementation may generalize the Safehouse lazy-result guard rather than
create a second proxy. That guard must evaluate the Service authority predicate
defined here, not only arrest. Proxying changes reflection such as
`inspect.isgenerator` or `inspect.iscoroutine`; the compatibility cost must be
documented and tested.

Native async-generator support remains a language-profile boundary until the
shared lazy guard can preserve `async for`, `asend`, `athrow`, and `aclose`
correctly. A profile must either guard every async continuation or refuse that
published return shape clearly; an unguarded async stream is not conforming.

### 5. Saved handles and live views

A public Operation handle captured while authority holds applies the same live
checks when later invoked and while its lazy result runs. Capturing a handle is
not a permanent credential. Likewise, an Agent-bound Tag view resolves the
Agent's current membership, Contract, door, and future Grant rather than
bypassing them with a captured verdict.

This rule does not retroactively erase an ordinary Agent Action callable or a
raw Report value already delivered under their separate laws.

### 6. When the second check may be omitted

TOP may skip a release check only when it can establish all inputs to the
authority predicate stayed unchanged between entry and release. Examples may
include a kernel-only path that reads a plain stored value without invoking
user code.

The following are not sufficient proof:

- no recorded TOP mutation;
- the same runtime type or Overlay key;
- a state epoch that does not cover ordinary Python data read by Posts;
- continued possession of a captured callable or view.

The optimization is optional. Conservatively checking twice is conforming.
Any fast path needs a focused test and performance evidence showing both the
saved work and the absence of an authorization leak.

## Execution profile and race boundary

This STEP follows the current one-Agent, one-thread profile. Async tasks may
interleave at suspension points, which is why each continuation is checked.

In a free-threaded or shared-Agent profile, another thread can change authority
after the final check and before Python hands the object to the caller. Closing
that race requires synchronization spanning check and release; it cannot be
solved by adding one more unlocked check. That task-safety profile belongs to
a separate STEP.

The result itself may be mutable and may outlive its Grant. Once released,
ordinary Python ownership applies unless a separate revocable-object design is
used.

## Rationale

Entry-only authorization answers “may this work start?” Release authorization
answers “may this result cross the boundary now?” Both questions matter when
the work can change the very Agent it serves or can be suspended.

The rule stays small by reusing the existing authority predicate and by
allowing a demonstrably pure path to avoid duplicate work. It does not pretend
that TOP can observe arbitrary Python state changes. When user code runs, a
fresh check is the honest answer.

The lazy rule treats every yield as a small result release. This aligns
coroutines and generators with synchronous Operations instead of granting a
permanent capability merely because the lazy object was created earlier.

## Backwards compatibility

An Operation that deliberately invalidates or Rips its caller and returns a
value currently may expose that value. It will instead fail at release. Code
that intends to return a result after ending membership must copy it through an
unprotected ordinary Python path or change the Service's authority rule
explicitly.

Lazy results become guarding proxies where native return objects cannot carry
continuation checks. Reflection that insists on an exact generator/coroutine
type may need to inspect the underlying callable declaration or use the
documented TOP result category instead.

The extra Contract evaluation can affect hot Operations. A safe no-user-code
fast path is allowed, but performance budgets do not justify skipping a check
after arbitrary user code.

## Alternatives considered

| Alternative | Assessment |
| --- | --- |
| Check only at entry | Reject: work may invalidate its caller or resume after authority changes. |
| Check only at return | Reject: unauthorized work runs and consumes resources before refusal. |
| Trust a TOP mutation epoch after arbitrary user code | Reject: Posts can depend on state outside that epoch. |
| Snapshot the entry verdict into a permanent handle | Reject: capture becomes an undeclared authority bypass. |
| Copy every result before release | Does not answer whether it may be released and cannot safely copy arbitrary Python objects. |
| Lock every Agent for the whole Operation | Outside the current profile and unsafe across arbitrary awaits; a future concurrency STEP must define it. |

## Acceptance requirements

- A synchronous published Operation that Rips the caller, breaks any visible
  Post, revokes its future Grant, or closes its required door cannot release
  its returned value.
- A published Report whose resolution runs user code has the same entry and
  release boundary; a proven plain-value path may demonstrate omission of the
  second check.
- Captured public Operation handles and Agent-bound Tag views cannot bypass a
  later authority change.
- Coroutine and generator results check before and after every continuation,
  including each yielded item and final result. Supported async generators do
  the same; unsupported ones fail clearly before an unguarded stream escapes.
- Body exceptions remain primary when no result is released. Exit-check
  failures preserve their exact membership, Contract, Secret, Grant, or
  Safehouse category and cause.
- Tests include authority changing inside a body, between lazy resumes, from a
  copied async context, and during Report resolution.
- The implementation documents the one-Agent, one-thread boundary and does
  not claim an unlocked final check provides free-threaded atomicity.
- Normal access, protected access, lazy continuation, memory retention, and
  any unchanged-state fast path meet the project's performance budgets.

## Open implementation choices

1. Generalize the Safehouse continuation proxy into one composable guard, or
   layer a Service predicate around it? One guard avoids wrapper-order gaps.
2. Which Report paths can mechanically prove that no Python callback ran and
   safely use the one-check fast path?
3. Refuse native async generators in the first deployed profile, or implement
   the complete guarded async-generator protocol now?
4. What public introspection should identify the original callable shape once
   a lazy result is proxied?

---

### Decision

> **Brief.** The Director settled entry checking, conditional release
> rechecking, and the unchanged-state exception on 2026-10-20. The four
> implementation choices above remain open; this STEP changes no runtime by
> itself.
