# TagKit Python Profile

[Manifesto](../spec/MANIFESTO.md) →
[Technical Specification](../spec/SPECIFICATION.md) →
[TagKit Guide](GUIDE.md) → **Python Profile**

This document describes **TagKit-only conveniences**. They help you write
Python with TOP. They are **not** part of the normative Specification.

- **Specification** — observable TOP semantics in any language.
- **TagKit Guide** — how to build with TOP in Python (tutorial depth).
- **This profile** — quick reference for utilities that sit beside the spec.

If TagKit and the Specification disagree on core semantics, the Specification
wins and TagKit must change.

---

## Procedural queries

Use these when a functional or pipeline style reads better than repeated
`Tag( target )` calls.

```python
from TagKit import Apply
from TagKit import Has
from TagKit import Tags


hero = Apply(
        Hero( "Ari" ),
        Human,
        Wizard,
        )

assert Has( hero, Human, Wizard )
assert Wizard in Tags( hero )
```

| Utility | Role |
| --- | --- |
| `Apply( target, *tags )` | Tag a target with several Tags in order |
| `Has( target, *tags )` | True when every Tag is currently active on the target |
| `Tags( target )` | Active leaf Tags on the target (read-only) |

`Tag( target )` remains the smallest identity-preserving transformer.

---

## Uniform access

One visible name, two spellings. The meaning does not change.

```python
assert ember.hp == 30
assert ember.hp() == 30

assert ember.motto == "onward"
assert ember.motto() == "onward"

send = ember.strike          # handle until called
send( dummy )
```

Records return stored values. Nullary Actions evaluate when read bare.
Actions that need arguments stay handles until you call them.

Use the `()` spelling when Python needs the raw object (`is None`,
`isinstance`, JSON).

---

## Fields and membership

```python
assert ember in Fire              # current Field membership
assert isinstance( ember, Fire )  # committed history (survives Rip)

for creature in Fire[:]:          # sound members (Posts hold)
    play( creature )

for broken in ~Fire[:]:           # defective members (Posts fail)
    repair( broken )

assert broken in Fire[:] or broken in ~Fire[:]   # U-set
assert ( Fire[:] | ~Fire[:] ) is Fire.Field
```

| Spelling | Meaning |
| --- | --- |
| `Tag` / `target in Tag` | Current membership |
| `Tag[:]` | Sound Field — iterate agents whose visible Posts hold |
| `~Tag[:]` | Defective complement — still in the Field, Posts fail |
| `Tag[:] \| ~Tag[:]` | Whole Field (U-set) |
| `Tag.Field` | Raw Field object (same agents as the U-set) |

Default iteration on a Tag follows `Tag[:]` (sound members only).

---

## Contracts on the Agent

Preconditions gate **incoming materials** for the layers applied in the
current call. Postconditions are the **finished product** — re-checked at
every Tagging boundary.

```python
if ember.Has_Spellbook:
    proceed( ember )

if not ember.Has_Spellbook():
    restore_spellbook( ember )

if ember:                         # True when every visible Post holds
    proceed( ember )

print( f"{ember:Contract}" )      # mini menu: Pre / Post, OK / XX
print( f"{ember:Display}" )       # same as :Contract
print( f"{ember:Status}" )       # flat OK / XX lines
```

Named failures for recovery:

```python
from TagKit import TagPostconditionError

try:
    Boss( newt )
except TagPostconditionError.has_valid_enrage_threshold:
    repair( newt )
```

`Contract.Preconditions`, `Contract.Postconditions`, and `Contract.Status`
remain for tools and explicit sweeps. Prefer Agent spellings in gameplay code.

---

## Tag context: Reports and Operations

Reports and Operations belong to the **Tag**, not flat Agent access.

```python
assert Fire.color == "#ef5b35"
assert Fire.roster() == ( "Embercub", )

view = Fire[ ember ]              # Agent-bound snapshot after Fire applied
view = ember.Fire                 # same, when Fire is an active leaf name
```

Flat `agent.name` consults Agent scope (Actions, Records, Conditions).
`Tag.name` and `Tag[ agent ]` consult Tag scope (Reports, Operations, and
contributions frozen at that Tagging).

---

## Geometry and Forms

Forms describe how Bases and Shapes compose. Geometry is the Agent's current
Form stack; Outline renders it for tools.

```python
assert Fire.Form() == ( Elemental, Fire )

geometry = ember.Geometry()
print( ember.Outline() )
```

| Utility | On | Role |
| --- | --- | --- |
| `Tag.Form()` | Tag class | Static Form roots for this Tag |
| `agent.Geometry()` | Agent | Current composed Forms |
| `agent.Outline()` | Agent | Human-readable Geometry string |
| `Tag.Forms` | Tag class | Related Form metadata (tooling) |

---

## Delete a visible contribution

Mask a name in the visible Overlay without Rip:

```python
from TagKit import Delete


class Quiet( Tag ):
    @Delete
    def motto( target ) -> None:
        ...
```

Records may also be removed with ordinary assignment semantics where the
profile allows it (`del agent.record`).

---

## Checkpoints

A Checkpoint groups several Taggings into one recoverable design phase.
It is **not** Rip — committed history stays unless you Restore.

```python
checkpoint = Tag.Checkpoint( creature )

try:
    for tag in selected_tags:
        tag( creature )
    if not approved( creature ):
        raise Invalid_Archetype( "rejected" )
except Exception:
    checkpoint.Restore()
    raise
else:
    checkpoint.Commit()
```

Context manager spelling:

```python
with Tag.Checkpoint( creature ) as phase:
    Wizard( creature )
    phase.Commit()
```

Rip is forbidden while a Checkpoint is open. Finish with `Commit()` or
`Restore()`.

---

## Scope and exit cleanup

`Scope` owns bounded membership. Leaving the block Rips the listed Tags.

```python
from TagKit import Scope


with Scope( creature, Arena, Boss ):
    Arena( creature )
    fight( creature )
# Arena and Boss Ripped here
```

`At_Exit( agent )` registers best-effort cleanup when the interpreter exits.
Use it only when teardown cannot be structured with `Scope` or explicit Rip.

---

## Pins

Pins apply Tags **to Tags** — catalogs, bundles, and shared composition
roots. See the [Pin Guide](PIN_GUIDE.md).

```python
Catalogue( Entry )    # Entry is now a pinned Tag on Catalogue
Entry.Describe_Value()  # Tag Operation on the pinned Tag
```

---

## Public imports vs Tag methods

Stable application imports come from `TagKit`:

```python
from TagKit import Tag
from TagKit import Record
from TagKit import Pre
from TagKit import Post
from TagKit import Apply
from TagKit import Has
from TagKit import Tags
from TagKit import Scope
from TagKit import At_Exit
from TagKit import TagPostconditionError
```

These live on `Tag` or `Tagged` agents but are **not** re-exported at package
root:

| Utility | Access |
| --- | --- |
| `Tag.Checkpoint( target )` | `Tag.Checkpoint` |
| `Tag.Form()` / `Tag.Forms` | on Tag class |
| `agent.Geometry()` / `agent.Outline()` | on Tagged agent |
| `Contract.Format( agent, spec )` | prefer `f"{agent:Contract}"` |

Do not import TagKit internal modules (`access`, `transactions`, etc.) from
application code.

---

## Documented boundaries

These are intentional limits of the Python reference profile:

- **Copy / pickle / deepcopy** — define cloning in your domain; do not copy
  `_TAGKIT_STATE`.
- **Concurrent Tagging of one Target** — unsupported; use one thread per
  target or external locking.
- **Runtime subclass** — TagKit synthesizes a runtime type; libraries that
  require exact host classes should read
  [Implementation Notes](IMPLEMENTATION_NOTES.md#decisions--edge-cases-judgment-calls).
- **`Contract.Status`** — flat `{name: holds?}`; if Pre and Post share a name,
  Post wins in that dict. `:Display` / `:Contract` keep Pre and Post separate.

---

## Where to read next

| Document | Use when |
| --- | --- |
| [Specification](../spec/SPECIFICATION.md) | Defining or porting TOP |
| [Guide](GUIDE.md) | Learning TOP with Python |
| [Pin Guide](PIN_GUIDE.md) | Organizing Tags with Pins |
| [Implementation Notes](IMPLEMENTATION_NOTES.md) | TagKit internals |
| [Conformance](../CONFORMANCE.md) | Claiming TOP-conformant behavior |
