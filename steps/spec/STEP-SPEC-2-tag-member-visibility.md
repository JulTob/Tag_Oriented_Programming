# STEP-SPEC-2: Tag Members Are Composition-Internal

- **STEP:** SPEC-2
- **Desk:** spec
- **Title:** Tag Members Are Composition-Internal
- **Author:** Julio Toboso (@JulTob)
- **Status:** Brief
- **Created:** 2026-09-02

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

This STEP makes **runtime application access** go through Agents and Fields.
Tag Operations and Reports remain real — they hold shared logic and shared
data — but they are **composition-internal**. They are reachable while
building or executing Agent behavior (Actions, Record materializers,
Imprints), not as a public service API from arbitrary application code.

The Tag's public footprint in the world is its **Field**: membership,
iteration, and Field algebra. Everything else about a Tag is read through an
Agent that carries that Tag, or published explicitly through an Action.

## Motivation

STEP-SPEC-1 established two scopes: Agent and Tag. It still allows direct
Tag access such as `Fire.color` or `Fire.roster()` from main application
code.

That creates two problems:

1. **Organization** — Gameplay code can bypass the Agent and call Tag
   behavior directly, leaving the safety layers (membership, Posts, Action
   guards) that live on the Agent-facing path.

2. **Global vs carried meaning** — `Fire.color` always names one Tag class
   in the program. `agent.Fire.color` names the Fire layer **this Agent
   carries**, which supports parallel definitions and modded compositions
   without a single global Fire singleton.

The goal is zen namespaces: Agents are the published objects; Tags are layers
they carry; Fields are the only Tag-facing public sets in the world.

## Specification

### 1. Public runtime surface

At runtime, application code may use:

| Surface | Meaning |
| --- | --- |
| `agent.name` | Agent scope — Actions, Records, Conditions |
| `agent.TagName.name` | Agent-bound Tag context for one active layer |
| `Tag[ agent ].name` | Same contextual view (language profile may prefer one spelling) |
| `agent in Tag`, `Tag[:]`, `~Tag[:]`, Field algebra | Field membership and populations |
| `Tag( agent )`, `Tag.Rip( agent )` | Apply or remove membership |

Application code must **not** treat bare Tag Reports or Operations as the
public gameplay API:

```python
# discouraged at runtime
Fire.color
Fire.roster()
```

Preferred:

```python
for creature in Fire[:]:
    render( creature, creature.Fire.color )

creature.roster_summary()   # Action publishes Tag-wide behavior
```

### 2. Tag members remain composition-internal

Operations and Reports are still declared on Tags. They are used:

- inside Action bodies;
- inside Record materializers and Imprints;
- inside other Tag-internal composition; and
- when an Action adapter forwards to them (the Agency pattern from
  STEP-SPEC-1).

If a capability must be public, declare an **Action** that forwards to the
Operation. Overlay and Pin rules still **crunch** the Operation; the Action
name stays the stable public entry point.

```python
class Fire( Tag ):
    COLOR = "#ef5b35"

    @Operation
    def roster( fire_tag ) -> tuple:
        return tuple( fire_tag[:] )

    @Action
    def roster_summary( agent ) -> tuple:
        return Fire.roster()
```

After a Pin or Shape overlays `roster`, `roster_summary` still calls the
visible Operation — the adapter publishes; the Operation implements.

### 3. Fields are not Tags

A Field is the set of Agents currently tagged. `Fire[:]` lists Agents; it
does not call Tag metadata. Field iteration and algebra remain fully public.

```python
for creature in Fire[:]:
    play( creature )

for broken in ~Fire[:]:
    repair( broken )
```

### 4. Agent-bound Tag context is the namespace

Reports and Operations on a layer are read through the Agent that carries
that layer:

```python
creature.Fire.color
Fire[ creature ].color     # profile may treat these as equivalent views
```

This resolves the active Fire implementation for **this** Agent, not a single
global Tag singleton.

### 5. Tooling and design time

Editors, schema browsers, and bootstrappers still need to read Tag structure
without a live Agent. This STEP does **not** forbid that. It separates:

- **Runtime application API** — Agent + Field (+ Agent-bound Tag context).
- **Tooling introspection** — an explicit, declared surface (language-profile
  specific) that is not the gameplay path.

TagKit may provide something like declaration introspection, `Form()`,
`Outline()`, or class-body Reports for tools. Those are not substitutes for
runtime `Fire.color` from main.

### 6. Pins

Pins remain valid. They group Tags and alter composition. Pinned Tag members
stay Tag-scoped and composition-internal. Public access still goes through
Agent Actions on Agents that carry the pinned structure.

## Rationale

STEP-SPEC-1 answered *who owns a name* — `(scope, name)`.

STEP-SPEC-2 answers *who may call it at runtime* — Agents and Fields are
public; Tag Operations and Reports are internal modules behind Actions.

This matches:

- **OOP owns inherent structure; TOP owns semantic context** — context
  layers stay behind the Agent.
- **Agency pattern** — guarded Operations, public Actions, sticky Rip with
  fail-closed invocation.
- **Parallel mod definitions** — `agent.Fire.*` resolves carried layers.

Alternatives considered:

| Alternative | Verdict |
| --- | --- |
| Keep bare `Fire.color` public | Rejected for runtime; fine for tooling with a separate rule |
| Ban Tag Operations entirely | Rejected; Field-scoped shared logic still needs a home |
| Auto-project Operations onto Agents | Rejected in STEP-SPEC-1 |
| Only document convention, no enforcement | Acceptable as Phase 1; runtime guard is the end state |

## Backwards compatibility

This changes **documented runtime style**, not core TOP identity laws.

Migration:

- Replace `Fire.color` in gameplay code with `agent.Fire.color` or an Action.
- Replace `Fire.roster()` with a `@Action` adapter or per-agent iteration
  over `Fire[:]`.
- Keep Field algebra and membership spellings unchanged.
- Move editor/catalog reads to the tooling introspection path once defined.

TagKit today still allows bare Tag access. Deploying this STEP should follow:
spec update → guide and profile docs → examples → optional runtime
enforcement with clear errors.

## Acceptance requirements

A conforming profile must demonstrate:

- bare Tag Operation/Report access is documented as non-public at runtime;
- Agent + Field remain the public runtime API;
- an Action adapter publishes Tag-wide behavior (including after Pin/Shape
  overlay crunches the Operation);
- `agent.TagName.report` (or equivalent) reads the carried layer;
- Field algebra is unchanged;
- tooling has a documented introspection path that does not require bare
  runtime Tag calls from gameplay code; and
- optional: runtime enforcement raises a clear error for bare Tag member
  access outside composition context.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
