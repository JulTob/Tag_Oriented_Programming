# TagKit Implementation Notes

[Manifesto](../spec/MANIFESTO.md) →
[Technical Specification](../spec/SPECIFICATION.md) →
[TagKit Guide](GUIDE.md) → **Implementation Notes**

Optimization + semantics + multi-paradigm pass over the `TagKit` package
and its regression suites. These notes are non-normative.

**Test result: 173 tests, all passing on Python 3.12 and 3.14**
(`PYTHONPATH=. python3 -X dev -m unittest discover -s tests`).

The separate state-machine and capacity profiles are documented in
[`tests/STRESS_TESTING.md`](../tests/STRESS_TESTING.md).

---

## Internal package map

The public API remains available from `TagKit` and, for compatibility, from
`TagKit.TagKit`. Internally, each module now has one primary responsibility:

- `api.py` assembles the stable public surface;
- `declarations.py` defines contribution decorators and declarations;
- `fields.py` owns weak, ordered Tag Fields;
- `geometry.py` traverses Bases, Shapes, and Forms;
- `overlays.py` binds and layers contributions;
- `records.py` materializes and restores Agent Records;
- `contracts.py` evaluates Preconditions and Postconditions;
- `transactions.py` owns atomic Tagging, rollback, Rip, and Scope;
- `pins.py` applies Tags to Tags;
- `runtime_types.py` owns Agent state, views, and runtime actualization;
- `lifecycle.py` integrates finalization and `At_Exit`;
- `queries.py` implements `Has` and `Tags`; and
- `errors.py` defines the failure and warning hierarchy.

`TagKit.py` is now a compatibility facade rather than a second
implementation. New internal work should import from the owning module,
while application code should continue importing from `TagKit`.

---

## Reports use ordinary Tag data

Every public, non-callable data value declared on a Tag participates as a
Report. The class namespace remains natural Python:

```python
class Fire( Tag ):
    """Fire elemental creature."""

    COLOR = "#ef5b35"
```

TagKit does not inject `NAME`, `DESCRIPTION`, `ABSTRACT`, or other
application Reports into the Tag primitive. Unset names remain absent.
`Label()` and `Describe()` are likewise not core Tag methods.
If a program declares `NAME` or `DESCRIPTION`, they remain ordinary Report
names and do not affect TagKit's display behavior.

Tag classes use Python's own representation hooks:

- `str( Fire )` returns `Fire.__name__`;
- `Fire.__doc__` retains ordinary class-docstring semantics; and
- `repr( Fire )` returns the name followed by that documentation when it
  exists.

The explicit `Report( value )` wrapper remains compatible and is useful when
a callable or descriptor must be treated as shared data rather than as a
contribution of its ordinary callable kind.

---

## 1. Underlay syntax: explicit `@Underlay` only (backcompat removed)

The implicit "second positional parameter literally named `underlay`"
convention is gone. Extension is declared explicitly:

```python
class Paladin(Person):
    @Underlay
    def Attack(agent, past):        # name the underlay anything you like
        return past() + " with a holy oath."
```

- `@Underlay` marks an Action **or** Record as extending the prior visible
  contribution; the captured underlay arrives as the second positional
  parameter under whatever name the author chooses. Decorators mark the
  first parameter as the `agent` (self-like) binding by convention.
- Stacks with `@Action` / `@Record` in either order.
- A function marked `@Underlay` with fewer than two positional parameters
  raises `TagResolutionError` (clear diagnostic, raised once).
- The verdict is cached per hashable function (`_underlay_cache`), so
  `signature()` is inspected at most once per declaration rather than per
  application. Unhashable callable strategy objects remain valid and are
  inspected without caching.

## 2. Active reapply is a strict no-op

Re-applying a Tag that is already active does **nothing**: Records are not
reset and Imprints do not re-run. The previous "crunch" behaviour and the
`is_root` machinery were removed. Rationale (your call): in a complex
system a Tag is far more likely to be re-applied by accident than as a
deliberate reset, so reset must be explicit — `Rip` then apply again.
Re-applying a Tag that was previously Ripped starts a new Tagging and runs
its protocols again. Rip deliberately leaves Rogue contributions sticky, so
an `@Underlay` on that re-Tagging sees the sticky visible layer and may
accumulate it. That is historical layering, not a clean-object reset.

## 3. Pins: applying a Tag to another Tag

The Python profile now supports Pins directly:
see the non-normative
[`PIN_GUIDE.md`](PIN_GUIDE.md) for authoring guidance.

```python
class Available(
        Tag
        ):
    @Action
    def Explain(
            background,
            ):
        return background.__name__

    @Record
    def abilities(
            background,
            ):
        return []


class Acolyte(
        Tag
        ):
    pass

Available(
        Acolyte
        )

Acolyte.Explain()      # Operation on the Acolyte Tag
Acolyte.abilities      # Report on the Acolyte Tag
```

`Acolyte` keeps its identity and metaclass while becoming an Agent of
`Available`. Base membership, Fields, application inputs, Preconditions,
Postconditions, atomic rollback, strict no-op reapplication, Rip, and
historical `isinstance` behave as they do for ordinary Agents.

When the Target is itself a Tag, contributions use their matching Tag-level
forms:

- an Action becomes an Operation bound to the Target Tag;
- a Record materializes as a Report on the Target Tag;
- Pre, Imprint, and Post govern the Pinning;
- the Pin's own Reports and Operations remain on the Pin.

`Acolyte.Tag(Available)` provides exact Pin-bound snapshot access.
Pin-provided Reports and Operations enter snapshots for Characters tagged
with `Acolyte` after the Pinning; already-captured snapshots do not change.
Pin Reports and Operations are tracked by their originating Tag.
Rip revokes them from already-captured views, and later snapshots reveal the
latest provider that is still active. Reconstruction replays active Delete
layers too, so fallback never crosses a still-visible mask.

Underlay composes with prior Pin-provided contributions or native Operations
and Reports on the Target Tag. Delete masks the Target Tag member without
deleting Pin Field resources. Rip ends membership and snapshot access,
while Pin-provided Operations and Reports remain sticky.

Structural dunders and the core Tag API cannot be replaced by a Pin:
changing them would silently break the Target's continued meaning as a Tag.
TagKit raises `TagCompositionError` before mutation.

Tag-target state lives in one private, directly owned class slot read only
from that class's own namespace. Shapes do not inherit it semantically.
Because the state is owned by the class instead of a weak-map value, a
Pin-provided Report may safely refer to its own Target without keeping that
Target alive.

Conditions and Imprints may perform side effects. Direct class-member
assignments, replacements, deletions, metadata changes, and reachable
built-in container mutations are provisional and roll back if the complete
tagging fails; they commit if it succeeds. The container journal is shallow
and structural over exact `list`, `dict`, `set`, and `bytearray` objects,
including those nested through tuples. It preserves their identities,
aliases, and cycles without calling user copy hooks. Side-effecting
Conditions are permitted but discouraged because every later tagging
rechecks visible Conditions.

Nested application of a different Tag, or Ripping any membership on the same
Target, is rejected while a protocol is running. This applies to ordinary
Agents and Tag Targets. Such relationships must be expressed through Bases
or a Shape, or performed after the current tagging boundary, so one outer
transaction retains one coherent candidate state and Field membership.

The Target Tag may have any normal Tag contributions of its own and remains
callable as a Tag for ordinary Agents. Arbitrary non-Tag Python classes retain
their previous construction behavior.

## 4. Exit protocols: `__del__`, `Scope`, `At_Exit`

"Deletion always Rips on `del`" is now implemented, with honest tiers:

- **`__del__` (best-effort).** When an Agent is garbage-collected, its
  still-active `@Rip` teardown Actions run (reverse application order).
  The teardown's value is its outside-world side effect (release a lock,
  revoke a token, log) — mutating the dying Agent is moot. The whole
  finalizer body is guarded, so a dying Agent never raises, even at
  interpreter shutdown when module globals are torn down. A host
  `__del__` shadowed by `Tagged.__del__` is still called (`_host_finalizer`).
  Caveat: Python does **not** guarantee `__del__` at interpreter shutdown
  or inside reference cycles — so for anything critical, use:
- **`Scope(agent, *tags)` (guaranteed).** Context manager: records the exact
  membership delta it creates, including missing Bases pulled in by Shapes.
  It Rips that owned delta specific-first on exit via `try/finally`, even if
  setup or the block raises. Memberships active before entry are borrowed
  and remain active. If teardown fails after a successful body, Scope raises
  a `TagCompositionError`; if the body already failed, its original exception
  remains primary and receives the cleanup error as diagnostic context.
- **`At_Exit(agent)` (best-effort, opt-in).** Registers the Agent's
  teardown to also run at normal interpreter exit. Registration is weak,
  identity-indexed, self-pruning, and idempotent, so it neither keeps the
  Agent alive nor accumulates duplicate registrations.

A `ripped` flag on the Agent state makes teardown run at most once, so an
explicit `Rip` followed by collection does not double-fire.

Ripping a Base now follows the Guide: dependent Shapes are Ripped first in
reverse application order, then the requested Base. Unrelated Bases remain
active, and all committed contributions retain their normal sticky history.

## API verbs: Tags are Ripped, Records are deleted

`Clear` was removed (it overloads "empty everything" and "approved", and
collides with names users will want). The only Tag-extraction verb is
`Tag.Rip(agent)`. Records are removed with the language's own
`del agent.record` — TOP adds no verb. `Tagged.__getattribute__` resolves a
Record name to its Agent instance value only, so after `del` the name is
absent (and re-assignable), never the builder declaration retained by the
Tag.

## Application inputs to protocols

`Tag(target, **inputs)` passes keyword inputs to every Imprint, Precondition,
Postcondition, and Record applied during that call. A Record on a Pin receives
the same inputs while materializing its Tag-scope Report. Each protocol
receives the inputs whose names match its parameters; a declared parameter
the caller did not supply is passed as `None` — the application call is the
single source of truth (a function default is not consulted). Inputs
propagate to Bases too, so any protocol in the chain that declares `code`
gets it; unknown inputs are ignored.

Each visible condition keeps the inputs from the Tagging that installed it.
Later Tagging and on-demand `Contract` checks re-evaluate the condition
against those captured inputs instead of replacing them with unrelated
inputs.

    MI6(bond, code="007")   # every Imprint that declares `code` receives "007"

The Agent binding is the first positional parameter and its name is the
author's free choice — `agent` is a convention, never a reserved word (no
second `self`). The per-function parameter spec is cached.

## 5. Procedural facade and reusable contributions

The canonical `Tag(target)` call is already an identity-preserving unary
transformer and works directly with `map` and ordinary function composition.
TagKit adds three small module-level helpers rather than a pipeline framework:

- `Apply(target, *tags, **inputs)` validates every Tag before mutation,
  applies them in order, and returns the same Target;
- `Tags(target)` returns committed leaf Tags without actualizing a raw Target;
- `Has(target, *probes)` checks committed Tags and Tag names plus contributions
  carried by a successfully applied Tag, including aliased Actions, ordinary
  Records, and Pin Reports.

The facade avoids dependence on injected Target methods, so host objects and
domain Actions may use names such as `Tags` or `Has` without blocking TOP
queries. Existing `Tagged` methods remain as compatibility delegates, but
pre-existing host methods with those names keep their native meaning.

Contribution decorators now return independent, signature-preserving adapters
instead of marking the source function in place. Python function adapters
also retain coroutine and generator identity. One ordinary module function
can therefore be adapted independently as an Action, Record, condition, or
other contribution without one use silently changing another.

The package includes `py.typed`; the procedural `Apply` contract is typed
`Target -> Target`, which exposes stable identity to static tooling.
Contribution decorators use `ParamSpec` and a result `TypeVar`, so decorating
a function preserves its callable type instead of widening it to
`Callable[..., Any]`. `Operation` exposes a typed class-method descriptor
rather than the previous bare `classmethod` result.

## 6. Resource optimizations (no wasted work)

- **Neutral runtime types.** Runtime adapters inherit only `Tagged` and the
  host type, never Tag classes. Reports, Operations, Tag names, private members,
  and ordinary Tag attributes therefore remain on the Tag or its bound view
  instead of leaking onto the Agent. Conflicting Python base orders between
  semantic Tags no longer create accidental runtime MRO failures.
  Dunder Actions are installed explicitly because Python requires
  special-method behavior on the runtime type. Lifecycle, access, contract,
  membership, and Tag-application dunders remain TOP-managed and cannot be
  replaced by a Tag.
- **Host protocol coexistence.** Pre-existing host methods such as `Tags` and
  `Has` remain reachable with normal data-descriptor, instance, and host-class
  precedence. Non-Tag `|` operands and native containment (`__contains__`,
  iteration, or indexed fallback) delegate to the host; Tag operands retain
  TOP application. Static methods, class methods, callable objects, and
  arbitrary callable descriptors keep their binding, while disabled or
  non-callable protocols retain Python's native errors. Host truthiness
  remains active until a visible TOP Postcondition gives truthiness its
  contract meaning. Records use one descriptor-aware storage path, so host
  slots and data descriptors work for values, Underlays, snapshots, views,
  deletion, rollback, and `Has`.
- **Shared runtime types.** When a composition contributes no dunder Action,
  its neutral runtime type depends on `(host, leaves)` and is shared across
  every Agent of that shape through a `WeakValueDictionary`. Compositions
  with dunder behavior retain a distinct runtime type because that behavior
  may capture an Agent-specific Overlay.
- **Cached declarations.** `_declarations_for` scans a Tag's `__dict__`
  once per Tag class (`WeakKeyDictionary`), not once per application.
- **Identity-indexed Fields.** Fields retain weak, ordered iteration while
  indexing Agents by identity. Registration and Rip removal are constant-time
  and equal-but-distinct, even unhashable, Agents remain separate members.
  Public Fields are read-only: membership can change only through successful
  Tagging or Rip. Iteration streams live weak references instead of retaining
  a second strong population list, and rechecks each registration before
  yielding so an Agent Ripped during iteration is not returned afterward.
- **Tag subscription.** `Tag[target]` returns the Target's active Tag-bound
  view, including `Pin[Pinned_Tag]`. `Tag[:]` returns the Tag's existing weak
  Field view; partial slices reject rather than implying positional access.
- **Relationship queries.** `Tag.Form()` returns one Tag's deterministic,
  Base-first closure. `agent.Forms()` returns the active leaf Forms, optionally
  cropped through the host's `FORM_ROOTS`. `agent.Geometry()` combines those
  Forms into the Agent's current Base-to-Shape adjacency graph for
  `Outline()`. Diamonds remain diamonds instead of being flattened into false
  chains.
- **Commit-only observation.** `agent in Tag`, `agent in Tag[:]`,
  `Tag[agent]`, `Has(...)`, and historical `isinstance` cannot observe a
  provisional candidate while Preconditions, Imprints, Records, or
  Postconditions run. `Has(...)` and contribution probes through
  `probe in agent` continue to see the entry Overlay during a transaction,
  even while direct Action access intentionally sees the candidate Overlay
  for contract evaluation. Missing Bases pulled in by a Shape publish
  together at the outer transaction boundary, for ordinary Agents and Pins
  alike.
- **Smaller transaction state.** Internal state records use slots, immutable
  nested contribution maps are shared across candidate copies, active
  reapplication returns before snapshots, and rollback restores the original
  entry-state object instead of copying it only to discard it. Rollback
  snapshots direct values from both `__dict__` and declared host slots, plus
  an identity-preserving structural journal of reachable built-in mutable
  containers. The journal ignores immutable leaves before identity indexing,
  avoiding population-sized transient sets for large scalar collections.
  Journal and Form traversal are iterative, so deeply nested data and Base
  chains do not consume Python recursion depth.
- **Context-local guards.** Reentrancy tracking uses `ContextVar`, so
  independent threads and asynchronous contexts do not share diagnostic or
  active Tagging guard state. A mutable boundary marker becomes inactive when
  its parent transaction ends, preventing child `asyncio` Tasks from retaining
  a stale copied guard. `Contract.Status` stops nested diagnostic evaluation
  immediately.
- **Explicit async boundary.** Async Actions and Operations remain valid and
  preserve coroutine, generator, and async-generator introspection after
  binding. Tag application itself is synchronous: awaitables and async
  generators returned by Preconditions, Imprints, Postconditions, or Records
  reject the Tagging atomically. Lazy generator Preconditions, Imprints, and
  Postconditions also reject because their bodies have not run; a synchronous
  generator remains valid Record data. Lazy or awaitable Rip results are
  reported as failed teardown after membership has ended. Best-effort
  finalizer and at-exit paths discard them without leaking unawaited work.
- **Complete Rip teardown.** Every teardown Action for one Tag runs before an
  explicit Rip reports collected failures.
- **Precise materialization failures.** A failing Record or Tag-scope Report
  now names its declared contribution when TagKit wraps a non-TagKit failure
  in `TagCompositionError`. An existing `TagError` passes through unchanged,
  preserving custom subtype state. A builder's `TypeError` is no longer
  mislabeled as an Agent runtime-type failure.
- Caches are weakly keyed/valued. A declaration that closes over its own Tag
  class can still form a value-to-key retention path; this pre-existing
  Python weak-map limitation remains.

### Measured effect

In an illustrative three-run sample on 2026-07-31, the same 10,000-Agent
`Person + Wizard` microbenchmark used before this pass tagged in median
**2.047 s on Python 3.12** and **1.870 s on Python 3.14**, compared with
earlier samples of 2.981 s and 2.745 s: about 31% and 32% faster,
respectively. All 10,000 Agents still shared one runtime type, and median
Field iteration remained around or below 1 ms. Peak `tracemalloc` usage was
58.8 MB (56.1 MiB) on Python 3.12 and 58.7 MB (56.0 MiB) on Python 3.14,
compared with earlier samples of 65.3 MB and 65.5 MB. These are directional
workstation measurements, not performance guarantees; CPU load and
interpreter behavior cause meaningful run-to-run variance.

An independent-empty-Tag composition probe measured median application times
of 0.2 / 0.8 / 2.5 / 8.9 ms for 10 / 20 / 40 / 80 Tags on Python 3.12.
Leaf discovery normally uses direct Base relations: upward-closed membership
means every non-leaf is the direct Base of another active Tag. If a successful
Imprint deliberately changes the Geometry of an already-active Tag, the query
detects that the active set is no longer upward-closed and falls back to live
Form discovery. Independent width still grows super-linearly because every
committed Overlay captures history; a cached immutable composition plan
remains the next larger optimization boundary.

The stress pass also changed the practical deep-Form boundary. A 500-level
application that previously took about 29 seconds now completes in
approximately 0.33 seconds on Python 3.12 and 0.40 seconds on Python 3.14.
A 1,500-level Form applies and Rips without Python recursion failure.
Full commands, state-machine seeds, capacity measurements, and open semantic
decisions are recorded in
[`tests/STRESS_TESTING.md`](../tests/STRESS_TESTING.md).

## 7. Cleanup

- Removed the dead `Action = Callable[...]` type alias that was shadowed by
  the `Action` decorator; `Action` now unambiguously means the decorator.
- Added `Apply`, `Has`, `Tags`, `Scope`, and `At_Exit` to `__all__` and the
  package `__init__`.

---

## Decisions / edge cases (judgment calls)

- **`in` vs `isinstance` (IS vs HAS-BEEN) — now reliable.** `agent in Tag`
  is the IS check (current Field membership); it becomes `False` immediately
  after `Rip`. `isinstance(agent, Tag)` is the HAS-BEEN check: a per-Agent
  `ever_tags` set records every Tag ever applied, and
  `_Tag_Type.__instancecheck__` consults it, so isinstance stays `True` after
  `Rip` and through later re-composition ("ever an X, always an X"). It is a
  deliberate, dependable signal now — useful for spotting rogue / expelled
  Agents — rather than the fragile artifact it was. (OOP-flavoured rather
  than pure TOP, kept because it is genuinely handy. A failed tagging rolls
  `ever_tags` back atomically, so only committed memberships count.)
- **Reapply/Imprint:** active reapply = no-op; post-Rip reapply = a new
  Tagging whose protocols run again over sticky Rogue contributions
  (see §2).
- **Side-effect boundary:** rollback restores TOP-managed state, direct
  `__dict__`, slot, or Tag-class assignment/deletion, and reachable exact
  built-in containers (`list`, `dict`, `set`, `bytearray`). It cannot undo
  external I/O, mutations inside opaque/custom objects, inherited mutable
  class state outside the pinned Target, or effects in another object graph.
  Those remain the contribution author's transactional responsibility.
- **Concurrency boundary:** reentrancy guards are context-local, but Field and
  Agent state mutation is not locked. Concurrent Tagging of the same Target
  remains unsupported, and the kit does not yet promise general thread-safe
  mutation. Separate contexts no longer create false reentrancy failures.
- **Runtime-class boundary:** preserving Agent identity currently requires a
  synthesized subclass. `isinstance(agent, Host)` remains true, but code that
  demands `type(agent) is Host` can observe actualization. Exact-class
  equality generated by tools such as `dataclasses` can likewise change when
  one operand is tagged and the other is not. A fully transparent functional
  profile would require external state plus explicit operations/views instead
  of runtime subclassing; that is a separate architecture, not hidden here.
- **Private state name:** a host that already owns `_TAGKIT_STATE` is rejected
  before mutation with `TagCompositionError`; TagKit does not overwrite the
  domain value.
- **Copy and serialization:** dynamic runtime adapters still need an explicit
  clone/snapshot protocol before `copy`, `deepcopy`, or pickle can be treated
  as semantic TOP operations. That contract is intentionally deferred rather
  than guessing whether membership history or active Field identity should be
  copied.

## Guide alignment and profile policies

The TagKit Guide now reflects explicit `@Underlay`, active no-op
reapplication, Pin conversion, application inputs, `Scope`, `At_Exit`, and
the supported Target boundary.

Two Python-profile boundaries remain deliberate:

- With no visible Postconditions, an Agent preserves its host object's native
  `__bool__` or `__len__`. Tagging therefore does not silently change the
  truth behavior of an ordinary domain object.
- Copying and serialization are not semantic TOP operations yet. Applications
  must define whether a clone receives active membership, historical
  membership, both, or neither.

These boundaries are documented in the Guide and are not hidden
conformance claims.
