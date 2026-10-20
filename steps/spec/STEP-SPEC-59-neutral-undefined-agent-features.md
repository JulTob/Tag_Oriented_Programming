# STEP-SPEC-59: Neutral Resolution of Undefined Agent Features

- **STEP:** SPEC-59
- **Desk:** spec
- **Title:** Neutral Resolution of Undefined Agent Features
- **Author:** Codex, recording and evaluating the Director's 2026-10-20 proposal
- **Status:** Brief
- **Created:** 2026-10-20
- **Issue:** [#386](https://github.com/JulTob/Tag_Oriented_Programming/issues/386)
- **Related:** [STEP-SPEC-58](STEP-SPEC-58-agent-feature-deletion.md), Agent Feature deletion and Service Grants

> One STEP, one topic. This Brief evaluates the neutral result of asking an
> Agent for an undefined Feature. It does not define Feature deletion,
> Contract sandboxing, population commands, or exception recovery.

## Summary

An Agent may legally lack a Feature that a broader Agency normally gives.
Instead of aborting a long-running program when that missing Feature is used,
TOP can resolve a **known undeclared Feature coordinate** to its algebraic
neutral value and emit a mandatory warning:

| Known Feature kind | Neutral use |
| --- | --- |
| Action or published Operation Grant | a no-op with the ended callable's synchronous or lazy shape |
| Record, Tool value, or published Report Grant | the value `None` |
| Agent Contract check | either absent, or boolean `True` if the broader proposal is cleared |

This Brief recommends the bounded form: neutral resolution applies when TOP
knows the coordinate and its Feature kind, such as after deliberate deletion
or Grant revocation. A name never declared to TOP keeps ordinary
`AttributeError`, preserving typo detection. The broader total-Agent form is
recorded as an alternative for Director review.

## Motivation

Overlay makes specialization ordinary. A pacifist academy can legally remove
`Fireball` from its Wizards, while an older population protocol still says:

```python
for wizard in Wizard:
    wizard.Fireball()
```

No TOP rule was broken. One member simply cannot answer that Call to Action.
Crashing an hours-long game or simulation may be disproportionate. A neutral
Action lets the protocol continue, while a warning makes the mismatch visible
to operators and tests.

The same algebra is being established elsewhere in TOP. STEP-SPEC-44 clears
the pass/no-op function for a missing Action Underlay. Record Underlays use
`None`. STEP-SPEC-50 separately proposes neutral `True` for a recursive Post
edge. Applying those identities to an intentionally undeclared Agent
coordinate could give deletion a usable operational meaning, but the status
of each dependency must remain explicit.

## The Python context problem

Python resolves `agent.name` before it knows what the caller will do with the
result. One value cannot simultaneously be literal `None`, a callable no-op,
and boolean `True`:

```python
agent.unknown          # Record recall? Which kind?
agent.unknown()        # Call to Action?
if agent.unknown:      # Contract check?
    ...
```

A blanket `__getattr__` would need a polymorphic null proxy. That proxy would
not be `is None`, would make `hasattr(agent, typo)` true, and could let spelling
mistakes travel far from their cause. TOP avoids that ambiguity when it has a
deletion or revocation ledger recording whether the missing coordinate was an
Action, Record, Contract check, Report Grant, or Operation Grant.

## Proposed specification

### 1. Eligibility

Neutral resolution applies only to an ordinary Agent name that TOP records as
a known Feature coordinate in the undeclared state. This includes a Gain
ended by `del agent.name` and a Grant revoked at that coordinate. A name that
has never been a TOP Feature on that Agent raises ordinary `AttributeError`.

The following never become neutral missing Features:

- Python dunder/protocol seats;
- a Secret denied by a closed composition door;
- a Constant whose deletion was refused;
- a Service accessed directly on its Tag;
- access blocked because the Agent is arrested;
- a malformed declaration, bad Target, failed Gate, or other existing TOP
  failure.

Those cases already have specific meanings and diagnostics.

Broken and Rogue status is resolved per Feature. An ended own Gain may still
resolve neutrally because TOP deliberately permits own Actions and Records
needed for inspection and repair. Broken or Rogue access to a published
Service remains a membership or Contract failure; it cannot be converted into
a neutral Grant. Likewise, loss of membership is not the deliberate Grant
revocation defined by STEP-SPEC-58.

### 2. Neutral algebra

For a known undeclared coordinate:

- Calling a synchronous Action or Operation Grant runs a synchronous null
  Action and returns `None` without other effects.
- Calling an ended coroutine Action or Operation Grant returns an empty
  awaitable whose awaited result is `None`. An ended generator or
  async-generator callable returns an empty iterator of the same broad result
  shape. The deletion ledger therefore retains declared native callable form
  as well as Feature kind. It does not preserve reflection such as
  `inspect.iscoroutinefunction` on the null wrapper, and a plain synchronous
  function that dynamically returns an awaitable remains classified as
  synchronous.
- Recalling a Record, Tool value, or published Report Grant returns literal
  `None`. Ending a Tool value does not erase the Tool's kind rule for later
  assignment.
- The safe first stage keeps a directly deleted Agent Contract name absent.
  Neutral `True` remains the internal identity for an absent Underlay,
  recursive Contract edge, and aggregate validity with no failed visible
  Posts. Returning `True` from direct named reads remains the broader option
  for Director review.

Presence stays false in every case. Therefore `"answer" @ agent` distinguishes
an absent Record from a present Record whose actual value is `None`.

TOP's `@` query is the authority for Feature presence. Python implements
`hasattr` by performing attribute lookup and checking for `AttributeError`, so
a known coordinate that directly returns a neutral value necessarily makes
`hasattr(agent, name)` true. TOP cannot promise both neutral direct lookup and
false `hasattr` for the same name without adding an explicit tolerant syntax.

If a newer real Feature later occupies and then leaves that coordinate, the
boundary records the newer visible Feature's semantic kind and declared
callable form. It still hides every removable layer below the boundary. This
prevents an old Action tombstone from making a later deleted Record callable.

### 3. Mandatory warning

Every neutral use calls `warnings.warn` with `MissingFeatureWarning` at the
program's call/read site. The message identifies:

- the Agent and Feature name;
- the recorded Feature kind;
- whether a Gain ended or a Grant was revoked;
- the neutral result used.

It never silently turns a missing Feature into success. Standard Python
warning filters decide what is displayed and let applications promote the
warning to an exception in strict, test, or security-sensitive environments.
For an Action, capturing the null handle is not yet a use; invocation emits
the warning before the null body runs, after Python has evaluated the call's
arguments. A Record, Tool, or Report Grant read is a use at resolution. A
direct condition read joins that list only if the broader neutral-`True`
option is cleared. If a warning promoted to an error occurs inside a Post,
ordinary Contract handling makes that Post fail. Detailed checks such as
`Contract.Postconditions` preserve the warning as the cause of the named
failure. Boolean Agent truth, sound population checks, named condition reads,
and `Contract.Status` currently expose the false verdict rather than that
cause.

Python reflection inherits an unavoidable warning asymmetry. `hasattr` on a
neutral Record, Tool value, or Report Grant performs the read, emits the
warning attempt, and returns true. `hasattr` on a neutral Action or Operation
Grant only captures the null handle, returns true, and emits no warning until
that handle is invoked.

### 4. Vocabulary at use

TOP may describe invocation as a **Call to Action** and Record access as a
**Recall**. These are explanatory verbs, not new decorators or runtime kinds:

```text
Call to Action: wizard.Fireball()
Recall a Record: wizard.spellbook
Reach a Service: wizard.Dispatch()
Check a Contract: if wizard.Ready
```

`Protocol` remains TOP's word for an algorithm. A population protocol can
therefore issue Calls to Action without assuming every legal member has the
same Gain.

## Worked cases

### Deliberate specialization

```text
Pacifist(wiz)              # its protocol executes: del wiz.Fireball
wiz.Fireball()             # MissingFeatureWarning; null Action returns None
"Fireball" @ wiz           # False
```

### Typo

```text
wiz.Firebal()              # AttributeError: never a known Feature coordinate
```

### Revoked Service Grant

```text
del wiz.Send
wiz.Send("status")         # MissingFeatureWarning; no-op, Service untouched
Dispatch.Send              # the Tag's Service still exists
```

### Captured handles

```text
send = wiz.Send
del wiz.Send
send("status")             # rechecks; warns and returns the neutral result

del wiz.Fireball
missing = wiz.Fireball
Other(wiz)                  # establishes a new real Fireball
missing()                   # remains the captured null Action
wiz.Fireball()              # resolves the new Gain
```

The first rule is an access boundary and remains an open dependency of
STEP-SPEC-58 until the Director clears captured Grant behavior. The second
follows ordinary Python capture: a null callable already handed to user code
does not transform when a later Overlay changes the coordinate.

### Missing Record versus stored None

```text
del wiz.spellbook
wiz.spellbook              # MissingFeatureWarning, returns None
"spellbook" @ wiz          # False

Other(wiz)                 # establishes a real Record with value None
wiz.spellbook is None      # True
"spellbook" @ wiz          # True
```

## Safety and debugging analysis

### Benefits

- Long-running simulations, games, services, and population protocols can
  survive a legal capability mismatch.
- Deliberate specialization composes with old protocols without a guard at
  every call site.
- The neutral values match TOP's existing Overlay algebra.
- Warnings preserve evidence and can become errors under a strict filter.
- Restricting the rule to known coordinates keeps ordinary typos local.

### Costs

- A warning may be ignored, filtered, or missed in production logs.
- Returning `None` can move a failure to later code that assumes another
  value.
- A no-op may preserve execution while violating a domain expectation the
  author forgot to express as a Post.
- The Agent runtime needs deletion/revocation kind metadata even after the
  visible Feature is gone.
- Python `hasattr` becomes true for a known coordinate whose direct lookup
  returns a neutral value. TOP's `@` query remains false and is the presence
  authority.
- Hot missing-name paths need performance measurement.

Authors should state essential Features with presence Posts. A check such as
`return "Fireball" @ agent` makes the missing Gain break the Contract. Merely
calling a missing Action returns `None`, which existing condition semantics
do not treat as a false verdict. A missing optional Gain warns and resolves
neutrally; a presence-required Gain also makes the Agent Broken, so sound
population walks omit it before issuing commands.

## Why not every unknown name?

The Director also proposed a fully total Agent handler: any ordinary unknown
reference, such as `agent.ResolveRubik()`, would become a warning and neutral
answer. That model is conceptually elegant—an Agent answers requests rather
than acting as a storage object—but Python cannot infer the intended Feature
kind from attribute syntax. It needs a universal null proxy with surprising
identity, truth and introspection behavior.

The bounded proposal solves the motivating deletion/Overlay case and leaves a
future total-Agent STEP possible after real experience. If the Director
chooses total resolution now, this Brief must add the proxy's exact behavior
for `is None`, `bool`, calls, iteration, awaiting, context management,
operators, `hasattr`, serialization, and static tooling before clearance.

## Backwards compatibility

Known Features deliberately deleted today usually raise `AttributeError` or
a TOP access error when used. They would instead warn and provide a neutral
result. Programs relying on that exception should enable an error filter for
`MissingFeatureWarning` or check presence explicitly.

Names never managed by TOP continue raising `AttributeError`; Host objects
before actualization are unchanged. Python special method lookup remains
strict. Existing Secret, Constant, membership, soundness, and Safehouse
failures retain their classes.

## Alternatives considered

| Alternative | Assessment |
| --- | --- |
| Neutralize every unknown ordinary Agent name | Elegant total-handler model, but loses kind information, weakens typo detection, changes `hasattr`, and requires a pervasive null proxy. |
| Neutralize only known undeclared coordinates | **Recommended:** solves deliberate deletion and Grant revocation with exact kind and literal neutral values. |
| Keep every missing use strict | Strong debugging, but one optional mismatch can abort long-running population work. |
| Add tolerant syntax, such as an explicit resolve operator | Precise but adds a second language path and does not help old protocols automatically. |
| Make population commands skip members lacking a Feature | Useful and compatible, but solves only population dispatch rather than direct Agent requests. It can be designed separately. |
| Emit no warning | Rejected: unexpected neutral behavior must never pass silently. |

## Acceptance requirements

- Cover each known Feature kind, the latest ended visible layer's kind,
  neutral value, TOP presence result, Python `hasattr` result, and warning
  message/stack location.
- Prove an unknown typo remains `AttributeError` and its Python `hasattr`
  remains false. Prove a neutral known coordinate is absent under `@` even
  though `hasattr` is true.
- Prove Secret denial, Constant refusal, arrested access, Tag Services and
  dunders retain their existing behavior. Prove Broken/Rogue own Gains and
  published Grants follow their distinct access rules.
- Test warning filters, warning-as-error, repeated sites, captured handles,
  Underlays, Pins, live Tag views, Tools, Links, and synchronous, coroutine,
  generator and async-generator null Actions and Operation Grants. Cover the
  documented reflection limits and dynamic-return classification.
- Demonstrate the pacifist Wizard population scenario and a required-Feature
  Post that keeps such a member out of the sound walk.
- Measure normal reads/calls, neutral reads/calls, runtime type creation and
  memory retention against project budgets.
- Fuzz Overlay, deletion, new Gain, Rip, reTag, Grant revocation and later
  publication so stale lower Features never leak through the neutral boundary.

## Open Director decisions

1. Clear the recommended **known-coordinate** boundary, or require the fully
   total Agent null proxy now?
2. Keep direct deleted Contract names absent as recommended, or return
   neutral `True` and supersede the earlier “absent name; neutral Underlay
   only” ruling?
3. Confirm that mandatory warning means TOP calls `warnings.warn` on every
   neutral use while the application's Python warning filter controls which
   diagnostics are displayed.
4. Clear the captured-Grant rule in STEP-SPEC-58: saved Service handles
   recheck the live Grant, while ordinary Action and captured null handles
   retain normal Python capture behavior.

---

### Decision

> **Brief.** The Director proposed neutral missing Agent Features with a
> mandatory warning on 2026-10-20. This Brief recommends limiting the first
> implementation to TOP-known undeclared coordinates. The four choices above
> remain open before clearance.
