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
| `links.py` | Links: Relations, each Agent's Link, the Pairs, linking, extension, lines and ending |
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
  `__bool__` once a Postcondition is visible, `__getattr__` for views by
  name, and `__del__` for deletion. Tags are **not** in the MRO;
  `isinstance` is answered by the metaclass from the Agent's ever-set.
- **Runtime types are shared** across every Agent whose host and
  type-level facts match, whatever Tags they carry. Ten thousand Agents of
  one host normally share one type.
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
  compositions still share one runtime type. Ordinary Actions on Agents
  without Secrets use plain callables; context Actions are wrapped even
  then, because a hook may introduce the first Secret while it runs.

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

## The tagging sequence

`transactions._apply` is the call boundary: it snapshots the instance
dictionary, the state, and the class on entry. `_gate` lays every pending
Tag of the Form over a scratch copy and runs the composed Preconditions
once, so a Shape's gate overrides its Base's and declaration errors
surface before anything changes. `_apply_one` then lays each Tag over the
**live** state (no second copy) in the order parts, commit, write; finally
`_inspect` runs every visible Postcondition once. A `TagPreconditionError`, `TagCompositionError`,
`TagResolutionError` or `TagContractError` rolls the call back to the entry
snapshot, including Fields. `TagImprintError` and `TagPostconditionError`
propagate with everything left in place.

Laying over the live state is safe because nothing reads the new Overlay
before commit binds it on the Agent, and the entry snapshot is the only
rollback target.

## Judgment calls

- **`in` vs `isinstance`.** `agent in Tag` is the is-now check; `isinstance`
  is the has-been check and stays true after Rip. Kept because it is a
  dependable signal for spotting Rogue Agents. A rolled-back call also
  rolls the ever-set back.
- **Records over host descriptors** are refused with a Composition Failure
  rather than silently bypassing a property.
- **The Tag's dotted namespace is the program's.** Every Tag-level act is
  language syntax on the metaclass: `in`, `for`, `~`, `len`, `bool`,
  `[:]`, `[agent]`, `del Tag[agent]`, `format`. The only class attribute
  TopKit adds is the private `_topkit_field`. `bool(Tag)` is "any sound
  member", like a collection.
- **The empty-seat rule on Agents.** `__bool__`, `__format__`, `__copy__`
  and `__deepcopy__` are installed on the runtime type only when the host
  defines none of its own (`__bool__` only once a Postcondition is
  visible). Format specs are the display door: `f"{Tag:form}"`,
  `f"{agent:tags}"`, `f"{agent:outline}"`, `f"{agent:contract}"`.
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
  a Tag that declares one. A Form of several Tags is checked as a whole
  before any of it applies (`_refuse_in_collisions_of_the_form`), so a
  Flag Base's Imprint never runs for a Shape that is then refused. No
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
- **A rollback restores the state in place** (`_State.Restore`), keeping
  `composing` and `checking`: a door or a check opened before the call
  that is rolled back closes on the same object. (A copy put in its place
  used to leave the door open for good.) Known limit: in a reference cycle,
  Python clears weak references before finalizers run, so a finalizer's
  Tag code cannot call the Agent's bound Actions there (`ReferenceError`).
- **What the kit keeps, and for how long.** The Form cache holds a Tag's
  Bases only, never the Tag, so a dropped Tag class is freed. A Rip drops
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
  exists. `Precondition`, `Postcondition` and `Imprint` are `_Check_Mark`
  objects: called, they mark; read, they forward to their failure class.
  Per kind, not per Tag, on purpose: the handler reads the program's own
  word, and the Tag is already in the message.
- **Pins reuse the whole sequence.** A pinned Tag is an Agent whose
  namespace is its class dictionary. `_namespace_of` hands the kernel a
  `_Class_Namespace` adapter (get, set, pop, keys) over the proxy, so
  `_apply`, `_materialize`, `_commit`, `_snapshot` and `_rollback` are one
  code path; the class case restores key by key. The runtime type is a
  `(MetaTag, Tagged)` metaclass from the same cache. A landed Action is a
  `_Pinned_Operation` descriptor binding to the Tag it is read from (a
  Shape inherits it as it inherits a classmethod); a landed Record is a
  plain class attribute, which is exactly a Report's value. `_scan` skips
  names the class state manages, so a pinned Tag never projects them onto
  its Agents. The Tag's own Operations and Reports are host members to a
  Pin (`_pinned_host_function`, `_pinned_stored`); its Agent-scope names
  and protocols are refused, because a class dictionary is both host and
  instance namespace and a write there would remove the declaration.
  No descriptor is ever placed on a metaclass (it would intercept the
  class-attribute writes the kernel makes): a pinned Tag's `@Secret`
  members live in `state.secret_values` and answer on the miss path
  while `composing` is open; `@Public` pinned members are pushed to the
  Field at commit (`_publish_to_field`, dry run on copies first) and
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
  union. No kernel state changes.
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
  `_materialize` asks the same question of what the builder returned.
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

- **Links** (`links.py`, STEP-SPEC-22, §1.10). Each Agent's Link is a
  real Tag, made for that Agent at the declaring Tag's Parts
  (`_grant` from `_apply_one`), so its Field, history, algebra and Rip
  are the kit's own. Each Pair is a hidden Agent (`links.Pair`) tagged
  with the Relation's *Pair Tag*: the Relation's Agent-scope
  declarations, each wrapped by `_two_seats` so the Pair's own seat
  becomes the Agent and the Contact. The Pair's gate, Parts, Imprints,
  promises, Underlays, secrets and truth are therefore ordinary tagging.
  Linking runs the Pair's tagging first, then the Contact's membership
  in the Link: a refusal before her entry changes nothing. The Contact
  receives three things only: membership, the `@Public` lines
  (`_publish_lines`), and a teardown in `state.rips[link]` that unlinks
  her when she is deleted. A line shuts her composition door while the
  Link's code runs. The kit holds the Link's Agent weakly (on the
  Link's record and on each Pair's ends), and every `finally` that held
  an error sets its local to `None`, so a traceback cycle never keeps
  the Agent alive.
  The call boundary (`_Call_Boundary`) gained `undo`, `writes` and
  `open`. A linking registers its undo on the call it is part of
  (`_open_boundary()`). A call that rolls back runs its undo steps first,
  then restores its own Agent, so an Agent linked as a Contact during its
  own call ends as it was at the call. A call that does not roll back
  hands its steps to the call around it (`_hand_over`), so a linking made
  anywhere inside a call that later rolls back is undone with it; a
  linking runs its Pair's and its Contact's calls under a boundary of its
  own for the same reason. A boundary closes when its call returns
  (`_close`): an asyncio task that copied the context of a finished call
  links on its own. Extending a held Link runs every Pair's gate first
  (`_gate_form`), then every Pair's Parts (`gated=True`), and defers
  their Imprints and promises until the Agent's Commit. A Contact's
  history of Links is `State.ever_links`, a weak set, so a living Contact
  never keeps a dead Agent's Link. Pair Tags carry their own mark
  (`_is_pair_tag`): out of `Tags`, `Outline` and views, and refused every
  Tag-level act, as a Relation is. A Link name gets a read-only `_Link_Gate`
  descriptor and the binding write hooks, so `object.__setattr__` is
  refused too. `Tags`, `Outline`, the contract title and by-name views
  skip Links: nothing public on a Contact names the Agent who links her.
  At the Agent's deletion `_begin_ending` marks its Links as ending
  before any teardown runs, so a reference cycle, where weak references
  are cleared first, still finds a self-link's Pair and runs its
  teardowns once.
- **The oracle** (`tests/oracle_topkit.py`): an independent model of
  the laws driven by a random walk; `tests/test_oracle.py` runs a short
  walk under the suite. Run it at size with `--seeds 50 --steps 1200
  --population 18` (about 120,000 transitions with the Links walk,
  `Run_Links`, under a minute).
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
