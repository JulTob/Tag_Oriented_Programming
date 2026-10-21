# STEP-SPEC-60: Recheck Authority Before Releasing a Service Result

- **STEP:** SPEC-60
- **Desk:** spec
- **Title:** Recheck Authority Before Releasing a Service Result
- **Author:** Codex, recording the Director's 2026-10-20 ruling
- **Status:** Brief
- **Created:** 2026-10-20
- **Issue:** [#389](https://github.com/JulTob/Tag_Oriented_Programming/issues/389)
- **Related:** [STEP-SPEC-3](STEP-SPEC-3-member-publication.md), [STEP-SPEC-10](STEP-SPEC-10-published-members-answer-members.md), [STEP-SPEC-32](STEP-SPEC-32-the-arrest.md), [STEP-SPEC-40](STEP-SPEC-40-agent-contract-truth.md), and the live-view design in [PR #228](https://github.com/JulTob/Tag_Oriented_Programming/pull/228)

> One STEP, one topic. This Brief governs the point at which a published
> Report or Operation releases a result to one Agent. It does not define
> recursive Post evaluation, Service deletion, Safehouse arrest, or a
> multi-threaded execution profile.

## Summary

A published Report or Operation first checks whether the requesting Agent may
use it. Arbitrary user code can then run while the value is being prepared.
The Agent may leave the publishing Field, become Broken, or lose a future
per-Agent Grant before the result is ready. A public Action may also own a
temporary composition door while its Service body runs; that door must stay
inside the protected execution boundary.

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
for one Agent's publication route, following the vocabulary proposal in
[issue #385](https://github.com/JulTob/Tag_Oriented_Programming/issues/385).
The rule still applies under the current Report/Operation names if that
vocabulary has not yet landed.

## Independently verified problem

The current public-member guard is an entry check. A synchronous Operation can
pass it, Rip its caller or make a Post false inside its body, and still return
protected data. A coroutine or generator widens the gap: creating the lazy
result can happen while authority holds, while its body and returned values run
later after authority changes.

A Report usually reads a stored Tag value, but Python descriptor, metaclass,
or other user code can run during resolution. An entry-only check is therefore
not a general release boundary.

STEP-SPEC-50's Post memo solves a different problem. It prevents a completed
Post verdict from being reused across a Secret-door change inside one validity
query. It does not guard a Service result, and the release check defined here
must start a fresh validity query.

## Proposed specification

### 1. The authority predicate

Each entry and release check asks the live questions that published access
already asks:

- does the Agent still belong to the publishing Tag where active membership is
  required;
- does the Agent currently have a Valid Contract;
- is the Agent free of unresolved Safehouse arrest; and
- once Agent-level Service revocation exists, does this Agent still hold the
  Grant?

The check retains the existing specific failure. Safehouse status is resolved
first: an arrested Agent retries its saved Rip work under STEP-SPEC-32. A
failed retry raises Arrested Access Failure and stops before the other checks;
a successful retry frees the Agent, after which membership, Contract, and
Grant are checked live. Membership loss, a Void Contract, Grant revocation,
and arrest therefore do not collapse into one generic exception.

A published Service is public, not Secret. Its Agent-facing Action may open
the composition door for the Service body so that body can use internal
Features. That owned door is execution context rather than another item in the
caller's authority predicate. It closes before TOP releases control or a value
to the consumer.

A direct Tag-side protocol that does not act through an Agent Grant keeps its
own access law. This STEP does not project every internal Report or Operation
onto Agent access.

### 2. Synchronous Operations

A published synchronous Operation checks authority immediately before its
body runs and opens only the composition door owned by that call. After the
body returns, TOP closes the door and starts a fresh authority query before
handing the object to the caller. The release query cannot reuse the entry
query's Post memo. If it fails, TOP discards the result and raises that live
access failure.

An Operation body is arbitrary user code. TOP must assume relevant state may
have changed even when no TOP mutation was observed: Posts may read ordinary
Python attributes, external state, time, or another Agent. A runtime epoch is
not proof that arbitrary user code preserved authority.

A body exception can itself carry protected text or objects. The Director's
entry/result ruling does not yet decide whether it may cross a now-closed
authority boundary. The recommended fail-closed rule makes the live authority
failure public and stores the body exception only in a private diagnostic
ledger, or discards it. It must not remain reachable through public
`__cause__` or `__context__`. Keeping the body exception primary is the
compatibility alternative and remains an explicit choice below.

### 3. Reports

A published Report checks before resolution. It starts a fresh release query
when resolving the value can run user code or when any Post input may have
changed. Merely reading a stored value is not enough to prove stability: Posts
may depend on time, external state, or another Agent.

A one-check fast path is safe only when TOP proves every authority input
stayed stable. One possible proof is a stored value, no visible Posts, and
unchanged kernel membership/arrest/Grant state. A stronger proof may cover
every Post input, but an epoch that observes only TOP writes does not.

Once a Report value has been returned, it is an ordinary Python object. TOP
cannot revoke a raw value already delivered. This rule controls a new read,
not later uses of an old reference.

### 4. Lazy Operation results

For a native coroutine or generator, authority is checked at execution and at
every result-producing continuation boundary:

- before resuming the body, so revoked work does not restart;
- after the body reaches a yield or return, before releasing that item or
  final result;
- again at the next resume, because authority may change while the consumer
  holds the suspended object.

This includes a generator's `StopIteration.value` and a coroutine's awaited
result. Around every resume, TOP opens the Operation's owned composition door
for its body and closes it before releasing control or a value. The consumer
never receives the open door. Every post-resume authority check starts a fresh
validity query.

Cleanup is a different continuation. Following TOP's existing rule that an
entered Host context may run exit cleanup after arrest, the recommended
profile permits `close`, `aclose`, cancellation, `GeneratorExit`, and
`finally` cleanup through the Operation body's ordinary composition door after
authority loss, while releasing no yielded value or return object. That door
does not currently restrict which Secret Features cleanup can call, so its
exact capabilities and side-effect boundary are part of the open choice.
`send`, ordinary resume, and `throw` that can produce a value stay guarded.
Parking cleanup until Safehouse recovery is the alternative; the Director
must choose before deployment.

The implementation may generalize the Safehouse lazy-result guard rather than
create a second proxy. That guard must evaluate this Service authority
predicate, reopen and close the owned composition context correctly, and not
only check arrest. Proxying changes reflection such as `inspect.isgenerator`
or `inspect.iscoroutine`; the compatibility cost must be documented.

Native async-generator support remains a profile boundary until `async for`,
`asend`, `athrow`, and `aclose` are all guarded. A profile must either support
every async continuation or refuse the published shape clearly.

The first profile classifies the returned object's exact native type. A native
generator or coroutine is guarded even when a synchronous callable returned
it. A custom awaitable, iterator, or stream whose later work TOP cannot
identify safely remains outside that set. The profile must refuse such
deferred results, require an explicit supported adapter, or document them as
outside the protected Service-result model; it cannot call them guarded.

### 5. Saved handles and live views

A public Operation handle captured while authority holds applies the same live
checks when later invoked and while its lazy result runs. Capturing a handle is
not a permanent credential. An Agent-bound Tag view likewise resolves current
membership, Contract, arrest, and future Grant instead of retaining a captured
verdict. This depends on PR #228's separately reviewed soft-view design.

The rule cannot erase an ordinary Agent Action callable or raw Report value
already delivered under their separate laws.

### 6. When the release check may be omitted

TOP may skip a release check only when it can establish all inputs to the
authority predicate stayed unchanged between entry and release. A kernel-only
path with no visible Posts and unchanged membership/arrest/Grant state is one
possible proof. A path with Posts needs proof of every input those Posts read.

The following are not sufficient:

- no recorded TOP mutation;
- no Python callback during the Service value read;
- the same runtime type or Overlay key;
- an epoch that does not cover ordinary Python data read by Posts;
- continued possession of a captured callable or view.

The optimization is optional. Conservatively checking twice conforms. Any
fast path needs focused behavioral and performance evidence.

## Execution profile and race boundary

This STEP follows the current one-Agent, one-thread profile. Async tasks may
interleave at suspension points, which is why every continuation is checked.

In a free-threaded or shared-Agent profile, another thread can change authority
after the final check and before Python hands the object to the caller. Closing
that race requires synchronization spanning check and release. It cannot be
solved by one more unlocked check and belongs to a separate STEP.

The result may be mutable and may outlive its Grant. Once released, ordinary
Python ownership applies unless a separate revocable-object design is used.

## Rationale

Entry authorization asks “may this work start?” Release authorization asks
“may this result cross the boundary now?” Both matter when work can change the
Agent it serves or can be suspended. Each release query is fresh because
reusing the entry memo would miss precisely the state change being checked.

The rule does not pretend TOP can observe arbitrary Python state. When user
code runs, a fresh check is the honest answer. Every lazy yield is a small
result release; creating a coroutine or generator is not a permanent Grant.

## Backwards compatibility

An Operation that invalidates or Rips its caller can currently expose its
return value. It will instead fail at release. Code that intentionally returns
data after ending membership must use an unprotected ordinary Python path or
state a different authority rule explicitly.

Lazy results become proxies where native objects cannot carry continuation
checks. Exact native-type reflection may need the declared callable or a
documented TOP result category. The extra fresh Contract evaluation may affect
hot Services; performance budgets do not justify skipping it after arbitrary
user code.

## Alternatives considered

| Alternative | Assessment |
| --- | --- |
| Check only at entry | Reject: work may invalidate its caller or resume after authority changes. |
| Check only at return | Reject: unauthorized work runs and consumes resources before refusal. |
| Reuse the entry validity query | Reject: it can return the cached Post verdict that the release check exists to reconsider. |
| Trust a TOP mutation epoch after arbitrary user code | Reject: Posts can depend on state outside that epoch. |
| Snapshot the entry verdict into a permanent handle | Reject: capture becomes an undeclared authority bypass. |
| Copy every result before release | Does not answer whether it may be released and cannot copy arbitrary Python objects safely. |
| Lock every Agent for the whole Operation | Outside the current profile and unsafe across arbitrary awaits. |

## Acceptance requirements

- A synchronous published Operation that Rips the caller, breaks any visible
  Post, revokes its future Grant, or arrests the Agent cannot release its
  returned value.
- A Report resolution has the same entry/release boundary unless every
  authority input is proven stable; “no callback” alone is not proof.
- Captured public Operation handles and Agent-bound Tag views cannot bypass a
  later authority change.
- Coroutine and generator results check before and after every
  result-producing continuation, including each yielded item and final result.
  Supported async generators do the same; unsupported ones fail clearly.
- The owned composition door is open only around the Service body and cleanup,
  never while control or a value belongs to the consumer.
- Tests include authority changing inside a body, between resumes, from a
  copied async context, and during Report resolution; a time-sensitive Post;
  cleanup after lost authority; an exception carrying protected data; and a
  body that changes authority and restores it before release.
- Every release check starts a fresh validity query. Failures retain the
  chosen membership, Contract, Grant, or Safehouse category.
- The implementation documents the one-Agent, one-thread boundary and meets
  normal, protected, lazy, memory-retention, and fast-path budgets.

## Open Director and implementation choices

1. Generalize the Safehouse continuation proxy into one composable guard, or
   layer a Service predicate around it? One guard avoids wrapper-order gaps.
2. Which Report paths can prove every authority input stable and safely use
   the one-check fast path? “No callback ran” alone is insufficient.
3. Refuse native async generators in the first profile, or implement the
   complete guarded async-generator protocol now?
4. What public introspection should identify the original callable shape once
   a lazy result is proxied?
5. May cleanup run with the body's ordinary composition door after authority
   loss, releasing no value, or must it park in the Safehouse until recovery?
   If it runs, should cleanup receive a narrower Secret/side-effect profile?
6. If the body raises after authority disappears, does the authority failure
   replace the body exception without exposing its protected payload, as
   recommended, or does compatibility keep the body exception primary?

---

### Decision

> **Brief.** The Director settled entry checking, conditional release
> rechecking, and the unchanged-state exception on 2026-10-20. The six choices
> above remain open; this STEP changes no runtime by itself.
