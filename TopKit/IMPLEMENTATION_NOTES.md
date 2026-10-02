# TopKit Implementation Notes

Non-normative. How the Python reference implementation meets the
Specification, and the judgment calls it makes. The Specification wins
whenever the two disagree.

## Module map

One idea per module, nothing over 600 lines.

| Module | Idea |
| --- | --- |
| `errors.py` | the failure types |
| `declarations.py` | the marks (`@Action`, `@Record`, `Report`, `Public`, `@Secret`, …), scanning a Tag class once, binding parameters |
| `geometry.py` | Bases, Shapes, Forms, leaves |
| `fields.py` | the Field and its sound / defective partitions |
| `state.py` | the per-Agent state, bound Actions, the runtime type and its descriptors |
| `overlay.py` | laying one Tag's declarations over a state; materializing Records |
| `contracts.py` | strict verdicts, binding conditions, `Contract` |
| `transactions.py` | the tagging sequence and the call boundary |
| `lifecycle.py` | Rip, teardown, `Scope`, `At_Exit` |
| `access.py` | the hooks on the runtime type, Agent-bound views |
| `tags.py` | `Tag` and its metaclass |
| `queries.py` | `Apply`, `Has`, `Tags`, `Outline` |

## The access design

The hot path is an Agent reading its own attributes and calling its
Actions; Agents are built once and play for a long time. So:

- **No `__getattribute__` override.** A Record is a plain value in the
  Agent's instance dictionary. An Action is a small bound callable stored
  in the same dictionary. Python's ordinary lookup finds both at native
  speed.
- **Bound Actions hold the Agent weakly.** No reference cycle, so Fields
  (which hold Agents weakly) stay honest and finalizers run promptly. A
  handle whose Agent died raises `ReferenceError`. In a reference cycle
  (every tagged object still held at exit by a module that defines a
  function is in one: the function's `__globals__` is that module's
  namespace) Python clears those weak references before the finalizer
  runs, so `_agent_del` ties the Agent's Actions to it again first
  (`_retie_actions`: a fresh weak reference on each `_Bound` in the
  Agent's dictionary that the kit made for it, its `_owner` being the
  Agent's state, never a strong one, so nothing is resurrected and the
  Agent is still freed; another Agent's binding stored there keeps its
  dead reference). It does so only when the Agent has no weak reference
  left, or the first of its own bound Actions has a dead one
  (`_ties_cleared`): at a plain `del` the weak references are intact,
  so the finalizer never walks every Action there. Once the Layers ran,
  `_untie_actions` points every `_Bound` it tied, and every one in the
  Agent's dictionary that answers the Agent (a Tag applied by a
  teardown binds fresh ones), at `_GONE`, a weak reference that is dead
  from the start: code run after the finalizer, when the collection may
  already have cleared the Agent, meets `ReferenceError`. A `_Bound`
  made through a view, or bound during the finalizer and then replaced,
  is not reached (STEP-SPEC-18, item 10).
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
- **The composition door is a counter** on the Agent's state. Bound
  protocols raise it while they run; the secret-gate descriptor checks it.
  Agents without secrets use a plain bound callable and pay nothing.

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
  words, each stored as its plain text (`str.__str__`), in its own
  `__dict__` (empty for bare `@Flag`); the name is read live from
  `__name__`, and the words are never inherited by Shapes.
  `_flag_words` flattens the arguments: a string is a word (a `str`
  subclass too, never a collection), a list, tuple, set or frozenset
  gives its strings, one level deep. A word that does not hash, a `str`
  subclass with `__hash__ = None`, is refused by name: a word must be
  able to stand in a set of words. `Flag`
  refuses a Tag whose Field has a live member (`TagDeclarationError`,
  with the count; a Shape's members are in its Base's Field too), so a
  mark never lands under an Agent that carries the Tag. A lone class
  refused this way adds that a word is written as a string. Each Agent keeps
  its active Flags and their aliases in `state.words` until its Tags
  change or any `@Flag` is declared (counted in
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
  ordinary Action in `state.actions`, never bound on the Agent, left out
  of the type-level dunders and of the type key (deleted or not). So
  `agent.__del__` always reads the finalizer. Where Python cleared the
  Actions' weak references, it ties them to the Agent again; it runs the
  teardowns (skipped when `sys.is_finalizing()`: at exit they are
  `At_Exit`'s), then the visible `__del__`: the top Layer, nothing if
  deleted, else the host's own; then it unties what it tied and reports
  each teardown that failed through `sys.unraisablehook`, one
  `UnraisableHookArgs` each, naming the Agent and the teardown
  (`_report_failures`). `_run_exit_protocols` reports the same way once
  each Agent's teardowns in the pass ran, before an interruption leaves
  the pass, with "in the At_Exit pass of" for "deleting". A hook that
  raises stops nothing: its error goes to `sys.__unraisablehook__`, as
  Python does for its own reports; a hook set to `None`, or removed,
  means the default one, as for Python. When a teardown was interrupted
  and a Layer then raises, the kit reports the Layer's error itself
  (`_report_layer_failure`), since raising the interruption would hide
  it, and drops it, since its traceback holds the finalizer's frame.
  Python does not export `UnraisableHookArgs`, so `lifecycle.py` catches
  it once at import, under a temporary hook, from a weak reference whose
  callback raises, and leaves the hook as it found it, removed included.
  `_host_finalizer` finds the host's own by walking the MRO past the
  runtime type, as Python does (first definer decides, `None` means
  none, descriptors are bound). The exit path uses no module global and
  no builtin: what it needs is bound as a default argument, because late
  in exit both may be gone. The Layer's errors propagate, so Python
  reports them as unraisable, unless an interruption is pending. The
  first `__del__` Layer's Underlay is `_host_finalizer`, or a do-nothing
  Layer after `@Delete`. The host's own is found through
  `type(agent).__mro__`, skipping every class that holds
  `_TOPKIT_HOST_TYPE` (a runtime type, even one a user built on); the
  Agent's `__dict__` is read with `object.__getattribute__`, never
  through the host's own. An object without TOP state whose class is a
  runtime type is reset to its host class when its state is attached;
  if it is never tagged, the finalizer runs its host's `__del__`.
- **A failed Rip is rolled back** (STEP-SPEC-18, amendment D). Before a
  Rip whose Tag has a teardown due, `_rip` takes `state._entry_of`: a
  copy of the Agent's dictionary and of its state, its Tags, its
  `_Member` in each of their Fields, and its runtime type. When a
  teardown raises, `state._give_back` restores them as a failed tagging
  is restored (`_rollback`, now in `state.py`), then puts the Agent back
  in each Field in its place: every `_Member` carries its `order`, the
  count of members the Field had when it joined, and `_Field.Rejoin`
  puts the old `_Member` back before the ones that joined after it. A
  Rip with no teardown due takes no copy: nothing there can fail, so
  `del Tag[agent]` costs what it did. The `At_Exit` pass takes the same
  copy before each Agent's teardowns and gives it back when one fails.
- **A rollback restores the state in place** (`_State.Restore`), keeping
  `composing` and `checking`: a door or a check opened before the call
  that is rolled back closes on the same object. (A copy put in its place
  used to leave the door open for good.)
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
  descriptor that runs its builder once per Tag on first read and keeps
  the value on that Tag: in a dict under `_topkit_reports` in the Tag
  class's own `__dict__`, keyed by the Report, read from
  `owner.__dict__` and never through inheritance. `MetaTag` puts the
  dict in the namespace when the Tag is declared (a Tag body that
  defines `_topkit_reports` itself is refused), so a Pin's tagging that
  rolls back, which puts the pinned Tag's namespace back as it was,
  keeps the same dict and the values built during it. A plain class
  that holds a Report gets its own dict at its first build, read again
  after the builder runs. So the value lives and
  dies with the Tag, a Shape and its Base keep separate values, and a
  finalizer at exit reads the value built before (a weak cache could be
  cleared there first). The value is kept with `setdefault`, so a builder
  that reads its own Report while it builds leaves the value kept first,
  and the outer read returns that one too. `Tag.r += 1` replaces the descriptor with a
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
- **Condition members** (STEP-SPEC-14): `_agent_getattr` answers a
  condition by name on the miss path, after Tag views and before the
  host's own `__getattr__`, through `contracts._condition_member`, which
  evaluates one check under the re-entrancy guard and returns a plain
  bool. Nothing is written to the namespace or the runtime type. The
  collision rule lives in three places: `_refuse_condition_collision`
  at install (Actions, Records, host class members),
  `_refuse_member_over_condition` when an Action or Record is installed
  over a condition's name, and
  `_refuse_conditions_shadowed_by_the_agent` in `_apply_one` for a value
  the Agent's own namespace already holds.
- **Scope** (§3.2) skips a Tag the Agent already carries when its turn
  comes, so a Base named after its Shape is skipped too. When a
  tagging raises, it asks whether the Tag is now active (a Postcondition
  or an Imprint failed after commit) and, if so, records it as applied,
  so the teardown Rips what the Scope applied. A Base pulled in with a
  Shape is not recorded (whether it should be is open in STEP-SPEC-6),
  nor is one whose Imprint failed under its Shape. On the way out,
  `_rip_all` skips a Tag the Agent no longer carries (the block Ripped
  it) and collects each `TagError` a Rip raises: a Rip refused for a
  required Base leaves the Tag, and a failed teardown has already ended
  the membership. `_report` then raises the first, with the others as
  `add_note` notes, or, when an exception is leaving the block, adds
  each as a note on it. Every frame of the Scope's that holds a caught
  exception drops it before it leaves, so the Scope adds no cycle of its
  own (`ScopeTests` checks it with the collector off). A teardown that
  fails still holds one, through `_teardown`'s list of failures, on any
  Rip, as before this change: the Agent is then freed by the collector,
  not by its count.
- **The oracle** (`tests/oracle_topkit.py`): an independent model of
  the laws driven by a random walk; `tests/test_oracle.py` runs a short
  walk under the suite. Run it at size with `--seeds 50 --steps 1200
  --population 18` (about 60,000 transitions, under twenty seconds).
- **Stacked `@Pre @Post`** marks the function's kind `"condition"`;
  the scan appends it to both lists and `_name_checks` registers both
  named failures. `@Requirement` is the same mark written once: it sets
  the kind `"condition"` directly, so the two spellings meet in the scan
  and nowhere else. It carries no failure class of its own, and reading
  `Requirement.Something` says which of the two names to catch.
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
