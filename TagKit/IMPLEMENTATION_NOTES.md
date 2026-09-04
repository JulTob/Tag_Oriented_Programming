# TagKit Implementation Notes

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
  handle whose Agent died raises `ReferenceError`.
- **The runtime type is neutral.** It is `(Host, Tagged)`, host first, so
  every special method of the host keeps working. Its name is the host's
  name. It carries only what Python requires on a type: special-method
  Actions, and one descriptor per deleted, secret, or published name, plus
  `__bool__` once a Postcondition is visible, `__getattr__` for views by
  name, and `__del__` for teardown. Tags are **not** in the MRO;
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
