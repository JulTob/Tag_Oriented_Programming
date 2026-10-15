# TopKit Implementation Notes

Non-normative. How the Python reference implementation meets the
Specification, and the judgment calls it makes. The Specification wins
whenever the two disagree.

## Module map

One idea per module, with 600 physical lines as the migration target. The
target is not yet met: `declarations.py`, `overlay.py`, and `state.py` are the
current exceptions. [Issue #15](https://github.com/JulTob/Tag_Oriented_Programming/issues/15)
tracks splitting them by idea without changing semantics.

| Module | Idea |
| --- | --- |
| `errors.py` | the failure types |
| `declarations.py` | the marks (`@Action`, `@Record`, `Report`, `Public`, `@Secret`, …), scanning a Tag class once, binding parameters |
| `geometry.py` | Bases, Shapes, Forms, leaves |
| `fields.py` | the Field and its sound / defective partitions |
| `state.py` | the per-Agent state, bound Actions, the runtime type and its descriptors |
| `overlay.py` | laying one Tag's declarations over a state; materializing Records |
| `contracts.py` | strict verdicts, binding conditions, `Contract` |
| `constants.py` | protecting Constant bindings without freezing their values |
| `tools.py` | Tool slots: a Record's kind, a Tag or a class, admission at the gaining and at every write |
| `presence.py` | Contribution presence without evaluating values or conditions |
| `transactions.py` | the tagging sequence and the call boundary |
| `lifecycle.py` | Rip, teardown, `At_Exit` |
| `access.py` | the hooks on the runtime type, Agent-bound views |
| `tags.py` | `Tag` and its metaclass |
| `queries.py` | `Apply`, `Form`, `Keyword`, `Tags`, `Outline` |

## The access design

The hot path is an Agent reading its own attributes and calling its
Actions; Agents are built once and play for a long time. So:

- **No `__getattribute__` override.** A Record is a plain value in the
  Agent's instance dictionary. An Action is a small bound callable stored
  in the same dictionary. Python's ordinary lookup finds both at native
  speed.
- **Bound Actions hold the Agent weakly.** No reference cycle, so Fields
  (which hold Agents weakly) stay honest and finalizers run promptly. A
  handle whose Agent died raises `ReferenceError`.
- **The runtime type is neutral.** It is `(Host, Tagged)`, host first, so
  every special method of the host keeps working. Its name is the host's
  name. It carries only what Python requires on a type: special-method
  Actions, and one descriptor per deleted, secret, or published name, plus
  the reserved contract `__bool__` from the first Tagging,
  `__getattr__` for views by name, and `__del__` for deletion. Tags
  are **not** in the MRO;
  `isinstance` is answered by the metaclass from the Agent's ever-set.
- **Runtime types are shared** across every Agent whose host and
  type-level facts match, whatever Tags they carry. Ten thousand Agents of
  one host normally share one type.
- **Actualization is verified before Field entry.** The Target must retain
  its state and accept the exact runtime type the kit requested. Host
  `__setattr__` and `__init_subclass__` refusals, and metaclasses that
  substitute another type, become Composition Failures. Rollback restores
  the host type through the kernel path, not through the refusing hook.
- **The composition door** uses a counter on the Agent's state for
  synchronous protocols. Agent-authored context Actions use that door;
  host-authored context hooks keep ordinary host behavior. Entry closes
  its door before the user's `with` block begins. An async context hook adds a
  context-local door while its wrapper awaits. A deliberately derived
  execution context shares the capability while the hook is active; a
  pre-existing sibling does not, and closing clears the state reference so
  a captured context can neither reuse the door nor retain the Agent state.
  Return, errors and cancellation all close the hook's door. These are
  TopKit's context-hook implementation mechanics; they assign no automatic
  Tagging or Rip meaning to `with` and add no rule to STEP-SPEC-31.
  Closing removes inactive doors from the current context instead of
  resetting a token: Python may close a suspended coroutine in another
  context or close interleaved hooks out of order. Other active doors stay
  intact, and later hook entry prunes inert doors in captured contexts.
  Secret gates accept either form. The type-cache key uses the selected raw
  Actions and wrappers are allocated only on a cache miss, so equal
  compositions still share one runtime type. Current synchronous TOP
  Actions, including Pin Actions, open their composition door even before
  any Secret exists: an Action may introduce the first Secret while it
  runs. A public handle captured before that Tagging still composes when
  called afterward. Ordinary host methods are not wrapped. This does not
  change general special-method composition (#93), lazy execution (#94),
  or inherited Pin receiver/authority choices (#98).
  Public Pin handles use a TOP composing callable rather than Python's
  `MethodType`. They preserve their receiving Tag as `__self__`, their
  original callable as `__func__`, strong receiver ownership and available
  `__name__` / `__doc__` metadata. Their bound Python signature is inspected
  only when requested. Equality and hashing follow Python bound methods:
  the callable supplies equality/hash and the receiver is identified by
  identity. Repeated reads therefore work as dictionary keys and set
  members, including alongside matching native methods; custom receiver
  equality/hash hooks are not consulted. A handle's representation names
  its captured Operation and receiving Tag. Callable-kind identity remains
  a separate decision (#87).
  Optional callable metadata does not gate Pin invocation: usable `__name__`
  and `__doc__` are preserved; ordinary failures reading or assigning them
  fall back to the declared name and `None`, respectively. Metadata interrupts
  still propagate. Operation publication is a separate repair (#138).

Synchronous Actions selected through an Agent-bound Tag view use the same
composition door, even when that snapshot preceded the first Secret
Contribution. The view still selects its captured Action; reads inside
that Action resolve against the live Agent unless it explicitly uses a
view. Bindings keep the Agent weakly. A Secret Action selected through a
view requires that same Agent's door to be open before invocation, so a
handle captured during composition cannot authorize itself afterward.
The guard preserves the captured Secret boundary when a later Layer is
public.

Ordinary object Agents also bind their current Secret Actions with this
invocation guard, including Constant Actions. A synchronous call requires
that same Agent's active synchronous or execution-local async-context
door; another Agent's composition grants no access. Capturing a handle,
ending membership, deleting the current binding, or changing the current
Contribution's kind does not turn its captured implementation public.
Authorized calls inside composition remain possible, and captured handles
still hold their Agent weakly. Lazy execution remains a separate concern
(#94).

Current Secret Actions landed by Pins use a Secret-specific Operation
descriptor. Its captured callable checks the pinned Tag's existing
composition before opening its own door; an unrelated pinned Tag's own
door supplies no authority. Ordinary and Constant Secret Operations share
this guard.
Receiver binding and ownership are unchanged: a captured Pin Operation
retains its pinned Tag as existing Operation handles do, while the Pin's
Field remains weak. Rip, fresh pinning, and a refused pinning preserve
the same state, so authorized calls still work across those boundaries.
Inherited public Operations still open their declaring Base's state even
when their receiver is a Shape; such a call can therefore authorize that
Base's captured Secret Operation. This receiver/authority question and
inherited Secret dependencies remain pending (#98). This repair neither
introduces private Pin binding deletion nor governs lazy execution (#94).

### Presence without evaluation

`"name" @ agent` inspects current bindings rather than asking `hasattr`
or evaluating the name. A missing Action or Record is absent even if its
name remains in a sticky registry. False values, including `None`, are
present. Host fields and methods qualify regardless of origin; property
bindings are inspected without running their getters, and synthesized
`__getattr__` names are outside this query.

An actual Agent counts shared Tag names only through publication. A
published Report needs an active publisher; its descriptor supplies the
binding without building the value. A published Operation follows its
actual Action binding, which can remain after Rip although use is refused.
A Tag-bound view checks its captured contributions,
including captured shared entries. Secret names respect the underlying
Agent's composition door. The query never evaluates Posts, so a Post can
require a name without recursively checking soundness.

The runtime hook reserves string left operands for presence and preserves
the effective host or Tag `__rmatmul__` behaviour for other operands. A
descriptor exposes the original reflected method on class access to keep
Python's priority for a right operand whose type is a subtype. A
pinned Tag supports the query as an Agent; an unpinned Tag gains no TOP
operator from this feature.

Measured on Python 3.11 (`benchmarks/bench.py`), nanoseconds per
operation: plain attribute read 42, Agent host-attribute read 65, Record
read 64, plain method call 86, Action call 295, `agent in Tag` 291,
`bool(agent)` with one Post about 1900. Tagging a Record-plus-Post Shape
over a Base costs about 60 µs per Agent; an empty Tag about 22 µs. Peak
memory about 6 KB per Agent with two Tags.

### Population expression evaluation

Lazy combinations use explicit stacks for walks and membership rather
than one Python call per expression node. The expression is not flattened:
each union retains its own left-side identity referents until that node's
walk ends, and each leaf starts only when its branch is reached. A walk
frame also retains its last received Agent, as the recursive generator's
loop variable did. A `finally` clears the frame stack and current iterator,
frame and Agent references on exhaustion, close or failure, including when
an exception traceback remains alive. Cleanup does not call an arbitrary
leaf iterator's `close` method. The population itself keeps no walked
Agents at rest. Membership keeps
the same left-first short circuits and evaluates each reached predicate
in its original order.

## Geometry memo ownership

The first Form query memoizes a Tag's ordered Bases on that Tag itself,
not in a global weak-key table or the public Field. A Base's Contribution
can refer back to its Shape through a closure, default, annotation or
callable object; owner-local memoization leaves that cycle collectible
when the program releases the Tags. Retaining an empty `Tag[:]` does not
retain this memo. A returned Form tuple intentionally retains its Tags
until the program releases the tuple.

Each Tag has identity-qualified private keys and owns both Form and
declaration memos through the same helper. The
lookup never inherits another Tag's memo; an own or inherited program
binding at that key is not overwritten or shadowed, and Geometry simply
recomputes. A foreign internal memo is not accepted as this Tag's memo.
Physical type descriptors read class storage and MROs, without evaluating
metaclass dictionary/MRO properties. Metaclass collisions prevent new memo
publication. Warm reads reuse an exact owned memo without walking the
metaclass or evaluating its descriptor. Invalidation retires the stored value
even when a metaclass descriptor prevents safely deleting the memo attribute.
After the collision ends, a trusted retired wrapper can receive a fresh value;
foreign wrappers and program bindings remain untouched. The immutable wrapper
identifies its owner and key; a private mutable payload holds the cached value.
Memo publication does not hold the helper lock while inspecting user
metadata. Declaration scans, Base Constant inspection, Pin Tool validation
and Tag-as-Agent namespace copies use snapshots rather than iterating the
live class dictionary. Different Agents can therefore share a Tag without memo
publication invalidating one another's iterators; concurrent mutation
of one Agent remains outside this profile.

Non-Tag compatibility inputs retain the original global weak-key
fallback, so ordinary classes and builtins gain no attributes. Form
order, iterative traversal and lazy caching are unchanged; mutation of
`__bases__` remains a separate design question (#97).

## The tagging sequence

`transactions._apply` walks the missing Tags in Base-first Form order.
Before each turn, `_gate` checks only that Tag against the current Overlay.
When a Tag can use the shortcut, `overlay._preflight_ordinary_gains` checks
its ordinary Action and Record names against the live State one by one,
without copying it. An internal Report or Operation does not by itself
require a scratch copy; a public one does. Tags needing full composition
are laid over a scratch copy of the current Overlay. Their composed
Preconditions judge the live Agent. A refusal does not remove Tags whose
turns already finished.
Gainings apply Actions, Records, condition definitions and deletions
incrementally in declaration order, top to bottom,
establishing each before the next declaration runs. The Gate has already
evaluated this Tag's own Preconditions. Imprints run after Gainings and
before FieldAdding. The Tag's published members remain guarded by membership
during this training interval.

`overlay._gainings` walks the scan's ordered declarations. `_record_value`
calculates a Record's returned value before installing its declaration or
Constant lock; a failed builder leaves the previous binding available.
`transactions._actualize` prepares the acquired runtime behaviour independently
of membership. Tag-scope published services are prepared after Imprints.

A Gain needing runtime protection is acquired only when its representation
can be installed. If a Secret or Constant guard cannot be prepared, that
candidate Gain does not stick; the previous binding and earlier acquired
Gains remain. Admission-time shared services are also prepared separately:
if their representation fails before entry, they do not replace services of
an already active Agency. Acquired Gains and completed Imprint effects remain.
The initial host boundary follows Cleared
[STEP-SPEC-37](../steps/spec/STEP-SPEC-37-host-actualization.md): failed
preparation restores the original class, physical dictionary and declared
Python slot bindings. It does not undo mutable value contents, external
effects or later training. Acquired Gains follow STEP-SPEC-39.

FieldAdding establishes active membership, history and the Field together,
then captures the admitted Tag's view. `_inspect` runs visible Posts once
after the completed Form. A Gainings or Imprint failure leaves actually
acquired Gains and completed Tags in place without admitting the unfinished
Tag. A Post failure preserves membership; current Posts determine soundness,
not a permanent failure marker. Retry passes a fresh Gate, overlays ordinary
Gains and restarts Imprints, retaining established Constants. Acquired
conditions, including Posts and Constant Posts, remain even after unfinished
training. They participate in contract queries and published-member guards;
ordinary Actions are not automatically wrapped in Post checks.

`_enter_field` admits only after training. For a Pin, `_publication_plans`
preflights every current Field recipient before admission; `_publish_to_field`
then applies the admitted publication. The old whole-call rollback path is
removed: completed independent Tags and acquired Gains are not restored away.

An in-progress Tagging is tracked separately from membership so applying the
same Tag to the same Agent during its Imprint is a no-op. There is no automatic
Rip for an unfinished never-member and no automatic rollback of training
effects. Preconditions and Record builders are observational authoring
contracts, not sandboxes for arbitrary Python effects.

## Synchronous protocol results

Preconditions, Imprints, Postconditions and scheduled Rip teardowns are
synchronous in the current Python runtime. Native coroutine, generator and
async-generator results fail at their protocol boundary; ordinary Action
returns and stored Record values retain their usual meanings. This does not
amend the Specification: [STEP-SPEC-41](../steps/spec/STEP-SPEC-41-synchronous-protocol-results.md)
separately proposes a language-wide rule.

`declarations._discard_lazy_result` uses actual native types without reading
an ordinary return value's `__class__` hook. It closes coroutines and
synchronous generators, without starting an unentered body. Closing a started
object can run `finally` code and can fail; the failure is reported with its
original cause. Async generators are not driven through a new event loop.

Scheduled Rips retain their declared names alongside the composed Actions.
A flow-local guard checks only the selected teardown's Underlay chain and
remembers a lazy-result failure even if user code catches it. Other Actions
called during cleanup retain their ordinary return semantics. Ordinary
failures are collected after remaining teardowns run; Python interruptions
keep their propagation behavior. Best-effort deletion uses the same checks.

Record and Imprint failures, and invalid Underlay declarations, use their
Contribution names instead of requiring callable naming metadata. Private
helpers retain ordinary exception detail and fall back when formatting it
fails, preserving the original cause. These diagnostics do not alter the
Tagging sequence or expand its rollback boundary.

## Judgment calls

- **`in` vs `isinstance`.** `agent in Tag` is the is-now check; `isinstance`
  is the has-been check and stays true after Rip. History is established at
  FieldAdding. A failed never-member may retain Gains while both checks are
  false; a Rogue who previously entered the Tag retains its has-been history.
- **Records over host descriptors** are refused with a Composition Failure
  rather than silently bypassing a property.
- **The Tag's dotted namespace is the program's.** Every Tag-level act is
  language syntax on the metaclass: `in`, `for`, `~`, `len`, `bool`,
  `[:]`, `[agent]`, `del Tag[agent]`, `format`. The population handle is
  the private `_topkit_field`; Geometry also keeps a private, owner-local
  Form memo as described above. `bool(Tag)` checks the Tag's own visible
  Posts, received from Pins, and is true without Posts. `len(Tag)` counts
  sound members; `len(Tag[:])` counts all and `len(~Tag)` counts broken
  members. Population views retain their existence truth question.
- **The empty-seat rule on Agents.** `__format__`, `__copy__`
  and `__deepcopy__` are installed on the runtime type only when the host
  defines none of its own. Ordinary object Agents always receive the
  contract `__bool__` from first Tagging. An explicit host truth seat is
  refused before Tagging; Agent-scope truth Contributions are refused at
  declaration or late assignment. Synthesized runtime hooks are recognized
  without evaluating host truth. A host's `__len__` keeps `len`. A new
  condition name still rebuilds the type for its protective data
  descriptor. Format specs are the display door: `f"{Tag:form}"`,
  `f"{agent:tags}"`,
  `f"{agent:outline}"`, `f"{agent:contract}"`.
- **Flags own the Agent's `in`.** `__contains__` is installed when a
  `@Flag` Tag lands (a type-level fact, part of the type key; a Flag
  landing on an Agent that is already tagged rebuilds its runtime type).
  After the last Flag is Ripped it stays until the type is next rebuilt,
  answering False. It answers the name, a listed word, or the class of an
  active Flag and nothing else. The mark is the frozenset of the Tag's
  words in its own `__dict__` (empty for bare `@Flag`); the name is read
  live from `__name__`, and the words are never inherited by Shapes.
  Each Agent keeps its active Flags and their aliases in `state.words`
  until its Tags change or any `@Flag` is declared (counted in
  `declarations._flags_declared`). A string probe of a `str` subclass is
  read as its plain text, so matching stays exact and never hashes an
  unhashable subclass. `Keyword()` is the
  function form and works on any object.
- **One seat, one meaning.** `access._host_in_seat` reads the host's `in`
  as Python does: `__contains__`, then `__iter__`; for each, the first
  class in the MRO that defines the name decides, and `None` frees the
  seat (`__getitem__` alone is ignored). The refusal check
  (`overlay._refuse_a_second_in`) and the hook (`_hooks_for`) both use
  it, so they cannot disagree. The same check refuses a Flag while a
  Tag's `__contains__`/`__iter__` Action (a published Operation included)
  is visible, and such an Action while a Flag is active; `@Flag` refuses
  a Tag that declares one. The candidate Overlay check runs at each Tag's
  own turn, so a later collision leaves completed Base Tags in place. No
  type-level gate (`@Delete`, `@Secret`, `@Public` of the same name) can
  overwrite the Flag's hook. Pins are exempt: on a Tag, TOP owns `in`.
- **Deletion in Layers** (STEP-SPEC-18). The runtime type's `__del__` is
  always the kit's finalizer, never a Tag's: a Tag's `__del__` is an
  ordinary Action in `state.actions`, never bound on the Agent, left out of
  the type-level dunders and of the type key (deleted or not). So
  `agent.__del__` always reads the finalizer. It runs the teardowns
  (skipped when `sys.is_finalizing()`: at exit they are `At_Exit`'s), then
  the visible `__del__`: the top Layer, nothing if deleted, else the
  host's own. `_host_finalizer` finds the host's own by walking the MRO
  past the runtime type, as Python does (first definer decides, `None`
  means none, descriptors are bound). The exit path uses no module global
  and no builtin: what it needs is bound as a default argument, because
  late in exit both may be gone. The Layer's errors propagate, so Python
  reports them as unraisable. The first `__del__` Layer's Underlay is
  `_host_finalizer`, or a do-nothing Layer after `@Delete`. The host's
  own is found through `type(agent).__mro__`, skipping every class that
  holds `_TOPKIT_HOST_TYPE` (a runtime type, even one a user built on);
  the Agent's `__dict__` is read with `object.__getattribute__`, never
  through the host's own. An object without TOP state whose class is a
  runtime type is reset to its host class when its state is attached;
  if it is never tagged, the finalizer runs its host's `__del__`.
- **Weak finalization limit.** In a reference cycle, Python clears weak
  references before finalizers run, so a finalizer's
  Tag code cannot call the Agent's bound Actions there (`ReferenceError`).
- **What the kit keeps, and for how long.** Each Tag owns its Form and
  declaration memos through one internal helper, never a global root or
  its public Field. A declaration's references to its Tag or Agents thus
  leave a collectible local cycle. Each key and memo belongs to its exact
  Tag; own or inherited program bindings are left untouched and trigger
  uncached recomputation. Namespace inspection uses a snapshot, so another
  thread publishing either memo cannot invalidate a scan's iterator.
  The Tool checks in `Pin()` use that snapshot too, with callable metadata
  inspected after releasing the helper lock.
  Pin publication invalidates only the receiving Tag's declaration memo.
  These ownership rules are not a blanket lifetime guarantee about
  arbitrary user values that refer back to Tags.
  Protocol parameter memos use
  callable identity, never its custom hash or equality, and hold the
  callable weakly. An expired reference cannot delete a replacement
  entry. An accepted callable without weak-reference support is inspected
  without memoization or added attributes. Native parameter name objects
  are preserved for keyword lookup and the keys passed into the callable.
  When any retained name is a string subclass, inspection is uncached:
  its attached references cannot become owners through the global memo.
  Exact-string names remain safely memoized with the original
  first-inspection timing. Defaults and input-binding policy are preserved.
  This does not choose a different callable introspection profile (#87).
  A Rip drops
  the Tag's view snapshot (a view needs membership). A Field entry is a
  slotted weak reference carrying its key, with one callback per Field;
  `At_Exit` numbers its registrations the same way and drops each one when
  its Agent dies. A scratch pass (the gate, a Pin's publication) silences
  the kit's warnings through a context variable, never
  `warnings.catch_warnings()`, which would reset every warning registry.
  `PERFORMANCE-2026-09-24.md` measures all of it.
- **A restored name keeps its gate.** A name a Tag `@Delete`d and a later
  Layer stored again leaves `state.deleted` for `state.restored`; the type
  key gates both. The gate reads the Agent's own value first, so it is
  harmless for the stored Layer and it keeps a host property of that name
  hidden. A type rebuilt later for another reason keeps it.
- **Reports are builders.** `@Report def r(tag[, inherited])` is a
  descriptor that runs its builder once per Tag on first read and caches
  the value per Tag (weakly). `Tag.r += 1` replaces the descriptor with a
  plain value on that class, which is the documented counter pattern.
  Views snapshot the computed value; a published Report reads live.
- **Failures name their check.** `TagPreconditionError`,
  `TagImprintError` and `TagPostconditionError` use the `_Named`
  metaclass: `Failure.Named("X")` makes, once, the subclass
  `Failure.X` with `name = "X"`, and attribute access answers only names
  that were declared. Names are registered in `MetaTag.__new__`
  (`_name_checks`) so the handler is valid as soon as the Tag class
  exists. The process-wide registry stores plain string text, copied with
  `str.__str__` from a subclass name without calling its conversion hooks;
  it does not own that declaration object's attached references.
  `Precondition`, `Postcondition` and `Imprint` are `_Check_Mark`
  objects: called, they mark; read, they forward to their failure class.
  Per kind, not per Tag, on purpose: the handler reads the program's own
  word, and the Tag is already in the message.
- **Pins reuse the whole sequence.** A pinned Tag is an Agent whose
  namespace is its class dictionary. `_namespace_of` hands the kernel a
  `_Class_Namespace` adapter (get, set, pop, keys) over the proxy, so
  Gate, Gainings, Imprints, FieldAdding and view capture use the same
  code path for objects and pinned Tags. The runtime type is a
  `(MetaTag, Tagged)` metaclass from the same cache. A landed Action is a
  `_Pinned_Operation` descriptor binding to the Tag it is read from (a
  Shape inherits it as it inherits a classmethod). Its public composing
  handle keeps the original callable as `__func__`, the receiving Tag as
  `__self__`, native bound-method equality/hash, and the corresponding bound
  Python signature. Signature inspection is deferred until requested, so
  optional introspection cannot prevent reading or calling an accepted
  callable. A landed Record is a plain class attribute, which is exactly
  a Report's value. `_scan` skips
  names the class state manages, so a pinned Tag never projects them onto
  its Agents. The Tag's own Operations and Reports are host members to a
  Pin (`_pinned_host_function`, `_pinned_stored`); its Agent-scope names
  and protocols are refused, because a class dictionary is both host and
  instance namespace and a write there would remove the declaration.
  No descriptor is ever placed on a metaclass (it would intercept the
  class-attribute writes the kernel makes): a pinned Tag's `@Secret`
  members live in `state.secret_values` and answer on the miss path
  while `composing` is open; `@Public` pinned members are pushed to the
  Field at Field entry (`_publish_to_field`, dry run on copies first) and
  emitted by the Tag's scan for future Agents, so the scan cache is
  dropped at pinning. `_state_of` reads the dictionary directly, which
  is why `agent in Tag` got faster rather than slower.
- **Originals for un-patching.** When a Pin overlays a Tag's own
  Operation, Report or plain value, `_refuse_tag_member` records the
  declared object in `state.originals` (first patch wins). `_call_teardown`
  hands an `_Originals` namespace to a Pin's `@Rip` teardown that declares
  a seat beyond its receiver (and Underlay), read through `__wrapped__`
  of the composed Action.
- **Published members check sound membership at use** (STEP-SPEC-10):
  the adapter and `_Published.__get__` call `_require_membership`, which
  raises `TagRogueAccessError` (a `TagResolutionError`, and nothing from
  the host language: the failure is not an `AttributeError`, so a
  `hasattr` never swallows it and reports a missing name for a name that
  exists) when the Agent left, and
  otherwise runs the Agent's Postconditions through `_guarded` with
  `detailed=True`, which raises the named promise and is re-entrancy
  safe. An Agent without Postconditions pays one dictionary lookup.
- **Conditions are sticky** (STEP-SPEC-12): `_rip` removes membership
  and runs the teardown, nothing else. Every bound check carries its
  origin Tag (`_stamp`) only so that a Tag re-applied after a Rip
  replaces its own promise silently. `Contract.Delete(agent, *names)`
  pops the named conditions from the Agent's state and raises a
  Resolution Failure for a name that is not there; it is written to be
  called from a `@Rip` protocol, and works for a pinned Tag as well.
- **Field algebra** (STEP-SPEC-13): `_Population` in `fields.py` gives
  every population the three operators; `_Combined` holds two sides and
  an operator and walks them lazily (`|` by identity, each once; `&` and
  `-` by `in` on the right side). `_population_of` turns a Tag into its
  sound partition; `MetaTag.__or__` falls back to `type.__or__` when the
  other side is not a population, so `Wizard | None` stays a typing
  union. `_Field.__iter__` holds the starting Agents in join order, then
  checks the live identity entry at each turn. Rip therefore skips a
  coming turn, re-Tagging restores that turn, and a new member waits.
  A union walk retains the Agents it has seen on its left until that walk
  ends, so Python cannot reuse one identity key for a distinct Agent on a
  later side. Partitions—including their fast truth question—and
  combinations all route through that walk. No kernel state changes.
- **Condition members** (STEP-SPEC-14): an ordinary Agent answers a
  condition by name through `_Condition_Gate`; a pinned Tag keeps the
  metaclass miss path. Both call `contracts._condition_member`, which
  evaluates under the re-entrancy guard and returns a plain bool. The
  data gate and `_Binding_Write` refuse assignment
  or deletion before a host hook runs; `Contract.Delete` rebuilds the
  runtime type without the ended name, returning it to ordinary
  attribute behavior. Nothing is written to the Agent's namespace. The
  collision rule lives in three places: `_refuse_condition_collision`
  at install (Actions, Records, host class members),
  `_refuse_member_over_condition` when an Action or Record is installed
  over a condition's name, and
  `_refuse_conditions_shadowed_by_the_agent` in `_apply_one` for a value
  the Agent's own namespace already holds.
- **The guaranteed tier** (§3.2) is the program's own: it tags before
  `try` and Rips in `finally`. The kit has no built-in membership context
  manager and adds
  nothing to the `finally`: a Rip there that fails raises as any Rip
  does, with the block's error, if any, as its context. `Scope` made the
  block's choices out of sight (a Tag already carried, a door failure, a
  Rip that failed) and was removed (STEP-SPEC-31). `TryFinallyTests`,
  the oracle's `Exercise_Block` and the fuzz's `Holding` write the
  pattern.
- **Tool slots ride the Constant path** (STEP-SPEC-36). A `@Tool`
  Record registers its kind in `state.tools`, keyed by name, and the
  runtime type gains a `_Tool_Gate` data descriptor for that name, over
  the Constant or Secret gate when there is one. Every write to the name
  passes `_refuse_misfit` first, `object.__setattr__` included, exactly
  where `_Binding_Write` already intercepts a host's own `__setattr__`;
  `_gainings` validates the builder's proposed result through
  `_refuse_tool_value` before installing its binding or rule.
  A kind is terms, all holding, each a tuple of alternatives: a Tag asks
  `tag in state.active` (membership now, never soundness, never
  `isinstance`), a class asks `isinstance`, with a raising instance test
  wrapped as a Composition Failure and an interrupt left alone. The gate
  reads the kind from the Agent's state, not from the type, so Agents
  whose slots differ only in kind share one runtime type. The rule ends
  as any Record declaration does: a plain Record or an Action at the
  name pops the entry, as `@Delete` does. A Tool under a protocol name
  gets no descriptor, since one there would replace the language's own
  hook (`__rmatmul__` is presence); instead the write hook is forced on
  (`_binding_write_hooks(..., force=True)`), so ordinary writes are
  checked and `object.__setattr__` on that name is the documented
  bypass.

- **The oracle** (`tests/oracle_topkit.py`): an independent model of
  the laws driven by a random walk; `tests/test_oracle.py` runs a short
  walk under the suite. Run it at size with `--seeds 50 --steps 1200
  --population 18` (about 60,000 transitions, under twenty seconds).
- **Stacked `@Pre @Post`** marks the function's kind `"condition"`, in
  either order; the scan appends it to both lists and `_name_checks`
  registers both named failures. It is the only spelling: `@Requirement`,
  which set the same kind in one word, was removed (STEP-SPEC-30), so
  `_Check_Mark` is back to one failure class per mark.
- **Assigning a Tag's name on an Agent** (`ari.Elf = 1`) shadows the view by
  name; plain Python, not intercepted. `Elf[ari]` is unaffected.
- **Inputs and defaults.** A protocol parameter the caller omitted keeps
  its declared default; without one it is `None`.
- **Copying** an Agent is refused explicitly (`copy.copy`, `deepcopy`),
  because the alternative was silently sharing one state between two
  objects. Cloning is domain work: new Target, `Apply(new, *Tags(old))`.
- **Threads.** One Agent, one thread. The composing counter and Fields are
  not synchronized.
- **Pickling** a tagged Agent fails because its runtime type is synthesized.
  Serialize the host's data and the list of Tags instead.

## What was removed from 0.1

- Agent sugar on the mixin (`With`, `As`, `|`, `ApplyTags`, `__contains__`,
  `TagPaths`, `TagTree`): it competed with the host's own methods. The
  queries live in `queries.py` as functions.
- `Tag.NAME`, `DESCRIPTION`, `ABSTRACT`, `Label()`, `Describe()`,
  `Lineage()`, `Path()`: a Tag primitive should not invent application
  data. `Form(Tag)` replaces `Lineage()`.
- `TagDeletionError` (never raised) in favour of `TagDeclarationError`.
- The implicit `underlay`-named-parameter convention.
