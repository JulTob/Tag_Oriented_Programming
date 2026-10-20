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
TOP could resolve it to an algebraic neutral result and emit a mandatory
warning. The first draft limited that rule to a **known undeclared Feature
coordinate**, where TOP retains enough information to answer exactly:

| Known Feature kind | Neutral use |
| --- | --- |
| Action or published Operation Grant | a no-op with the ended callable's synchronous or lazy shape |
| Record, Tool value, or published Report Grant | the value `None` |
| Agent Contract check | either absent, or boolean `True` if the broader proposal is cleared |

That form does not answer the Director's broader case: an Agent whose Tags
never declared the requested name. The Director's desired surface is truthy
inside a boolean check and `None` for an ordinary value or call. Ordinary
Python attribute lookup cannot produce those different literal results from
the same expression. This Brief therefore records the implementable designs
and their costs. It does not select a total-resolution mechanism yet.

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

Returning literal `None` satisfies the first line but makes the call fail and
is false in the condition. Returning literal `True` satisfies the condition
but is neither `None` nor callable. `NoneType` cannot be subclassed to add the
missing protocols. A blanket `__getattr__` therefore needs either a proxy, an
expected-kind declaration, explicit tolerant syntax, or a TOP source
transformer that can see the surrounding expression.

A proxy can be truthy and callable, with its call returning `None`. It cannot
also be literal `None`: `agent.unknown is None`, `type(agent.unknown) is
type(None)`, and `case None` all distinguish it. It also makes
`hasattr(agent, "unknown")` true and prevents `getattr`'s default from being
used. One proxy cannot both make `agent.unknown()` return literal `None` and
make that same call result awaitable or iterable. Python dunders are looked up
on the type and bypass an instance `__getattr__` entirely.

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

The first rule is an access boundary. The Director ruled that a saved public
Operation handle rechecks its live Grant and cannot bypass revocation. Whether
that failed recheck raises or warns and returns a neutral result follows the
missing-Feature profile ultimately selected here. The second follows ordinary
Python capture: a null callable already handed to user code does not transform
when a later Overlay changes the coordinate.

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

## Designs for every unknown ordinary name

The Director proposed a total Agent handler: any ordinary unknown reference,
including `agent.ResolveRubik()` when no applied Tag ever declared that name,
would produce a warning and a neutral answer. The following designs can carry
some or all of that intent.

### A. Literal `None`

Return `None` from every unknown ordinary lookup. This gives exact value
identity, but `if agent.unknown` is false and `agent.unknown()` raises
`TypeError`. It does not meet the stated boolean or Call-to-Action behavior.

### B. Small missing-Feature value

Return an immutable value that is truthy and callable, with a call returning
literal `None`. It can warn at lookup and again when used. This covers boolean
checks, ordinary reads and synchronous calls, but the value is not `None` and
changes `hasattr` and `getattr` behavior. It should refuse subattribute access,
dunders, arithmetic, ordering, awaiting, iteration, context management and
serialization rather than inventing neutral elements for unrelated protocols.

The value should be ephemeral rather than cached by arbitrary typo name. It
must not retain the Agent. Its diagnostic may keep only safe snapshots such as
the requested name, Host type and identity number. Equality and hashing should
use the value's own identity; pretending to equal `None` would break Python's
equality and hashing laws. Copying may return the same immutable value, while
pickling should fail explicitly.

### C. Propagating null object

Return a value that absorbs calls, chaining, iteration, awaiting, context use
and perhaps operators. This lets more programs continue, but each additional
protocol chooses an arbitrary neutral result. Calls would need to return the
proxy rather than literal `None` if later awaiting or iteration must work.
Errors can then travel far from the miss. This is the least auditable option.

### D. Known coordinates plus a small total fallback

Use the deletion or Grant ledger for exact known kinds and native callable
shape. Use the small value from option B only for names that TOP has never
seen. Known ended Records can therefore return literal `None`; known ended
coroutine or generator Actions can preserve their broad lazy shape; a truly
unknown name receives the honest kind-agnostic value. This is the strongest
runtime-only route if total resolution is required.

### E. Declared expected-kind schema

Let a program declare that a name is expected to be an Action, Record,
Contract check or Service Grant even when no current Tag supplies it. TOP can
then choose the exact neutral result without a general proxy. This keeps
behavior explicit, but adds declarations and does not make every unknown name
total.

### F. Explicit tolerant syntax

Keep ordinary lookup strict and add a visibly tolerant request form. This is
precise, preserves Python reflection, and makes security review easy. It does
not help existing code such as `agent.Fireball()` automatically and would
need a TOP-consistent spelling before implementation.

### G. TOP source transformation or compiler

A TOP parser could distinguish a value read, call and condition before Python
attribute lookup, then lower each use to the intended neutral result. This is
the only route to the Director's exact context-dependent literals without a
proxy, but it changes TOP from a Python-embedded kit into a translated language
surface and creates a substantial tooling boundary.

### H. Bytecode or frame inspection

`__getattr__` could try to inspect the caller's bytecode to guess whether the
next operation is a call or condition. Optimizers, Python releases, nested
expressions and alternate runtimes make that brittle. This Brief rejects it.

### I. Global name registry

TOP could remember the kind of every Feature name declared anywhere and apply
that kind to every Agent. Names change categories often in TOP, so independent
Tags can legitimately disagree. A global registry would couple orthogonal
Agencies and is rejected.

### J. Population-only tolerance

A population command could skip or neutralize members lacking the requested
Feature while direct Agent lookup stays strict. This is useful independently,
but does not implement the total Agent request that motivated this section.

If the total rule is cleared, option D is the current architecture
recommendation. It preserves exact information wherever TOP has it and uses a
small, conspicuous value only where Python gives TOP no kind information. The
Director must still accept that the value is not literal `None` and select its
protocol surface before runtime work begins.

## Backwards compatibility

Known Features deliberately deleted today usually raise `AttributeError` or
a TOP access error when used. They would instead warn and provide a neutral
result. Programs relying on that exception should enable an error filter for
`MissingFeatureWarning` or check presence explicitly.

Under the bounded design, names never managed by TOP continue raising
`AttributeError`. A total fallback would instead change every unknown ordinary
Agent lookup, `hasattr`, and `getattr` default as described above. Host objects
before actualization remain unchanged. Python special method lookup remains
strict. Existing Secret, Constant, membership, soundness, and Safehouse
failures retain their classes.

## Alternatives considered

| Alternative | Assessment |
| --- | --- |
| Neutralize every unknown ordinary Agent name with one small value | Meets the total-handler goal for truth, reads and synchronous calls, but the value is not `None` and changes reflection. |
| Known coordinates plus a small total fallback | **Recommended if total resolution is required:** preserve exact kind where known and expose uncertainty honestly elsewhere. |
| Neutralize only known undeclared coordinates | Solves deliberate deletion and Grant revocation with exact kind and literal neutral values, but does not answer never-declared names. |
| Declare an expected kind | Exact and auditable, but declaration-driven rather than fully total. |
| Keep every missing use strict | Strong debugging, but one optional mismatch can abort long-running population work. |
| Add tolerant syntax, such as an explicit resolve operator | Precise but adds a second language path and does not help old protocols automatically. |
| Transform TOP source before Python runs it | Can produce exact context-dependent literals, but introduces a compiler and tooling boundary. |
| Inspect caller bytecode | Rejected as runtime- and optimizer-dependent. |
| Infer kind from a global name registry | Rejected because independent Tags may use one name for different Feature kinds. |
| Make population commands skip members lacking a Feature | Useful and compatible, but solves only population dispatch rather than direct Agent requests. It can be designed separately. |
| Emit no warning | Rejected: unexpected neutral behavior must never pass silently. |

## Acceptance requirements

- Cover each known Feature kind, the latest ended visible layer's kind,
  neutral value, TOP presence result, Python `hasattr` result, and warning
  message/stack location.
- For a bounded profile, prove an unknown typo remains `AttributeError` and its
  Python `hasattr` remains false. For a total profile, prove the exact selected
  behavior of lookup, truth, call, identity, `hasattr` and `getattr` default.
  In both profiles, prove a neutral coordinate is absent under `@`.
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
- If a small total value is selected, test descriptor and property failures,
  subattribute access, equality and hashing, copying, refusal to serialize,
  warning-as-error before call-argument evaluation, and strict refusal of
  unsupported protocols. Prove arbitrary typo names are not cached and the
  value does not retain its Agent.
- Fuzz Overlay, deletion, new Gain, Rip, reTag, Grant revocation and later
  publication so stale lower Features never leak through the neutral boundary.

## Open Director decisions

1. Select the first implementation profile: bounded known coordinates, the
   recommended hybrid of exact known coordinates plus a small total fallback,
   an expected-kind schema, explicit tolerant syntax, or a translated TOP
   surface.
2. If a small total value is selected, accept that it is not literal `None`
   and choose its protocol surface. The recommended minimum is truth and a
   synchronous call only; awaiting, iteration, contexts, operators,
   subattributes and serialization remain strict.
3. Decide how a direct deleted Contract name represents the desired split of
   truthy condition use and `None` value use. Python cannot produce both
   literal values from one untransformed lookup.
4. Confirm that mandatory warning means TOP calls `warnings.warn` on every
   neutral use while the application's Python warning filter controls which
   diagnostics are displayed.
5. For a saved Operation whose live Grant has been revoked, choose strict
   Resolution Failure or the selected warning-plus-neutral behavior. Recheck
   itself is already cleared; ordinary Action and captured null handles retain
   normal Python capture behavior.

---

### Decision

> **Brief.** The Director proposed neutral missing Agent Features with a
> mandatory warning on 2026-10-20, then clarified the desired result for an
> Agent whose Tags never declared the requested name: truthy in a condition
> and `None` for an ordinary value or call. Python cannot provide those exact
> context-dependent literals through ordinary attribute lookup. The five
> choices above remain open before clearance; no runtime proxy is authorized
> by this Brief.
