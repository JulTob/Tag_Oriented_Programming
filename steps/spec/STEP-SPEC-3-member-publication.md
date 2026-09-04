# STEP-SPEC-3: Member Publication

- **STEP:** SPEC-3
- **Desk:** spec
- **Title:** Member Publication
- **Author:** Julio Toboso (@JulTob)
- **Status:** Brief
- **Created:** 2026-09-04

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

This STEP adds a **publication** bit to member contributions, independent of
scope.

- Agent members (Actions, Records) are **external** by default: application
  code may use them on the Agent.
- Tag members (Operations, Reports) are **internal** by default: they remain
  composition-internal, as in STEP-SPEC-2.
- `@Secret` marks an Action or Record internal: composition may use it;
  application code may not.
- `@Public` marks an Operation or Report as the source of an explicit Agent
  adapter. It constructs a normal Action (and, for a Report, a nullary Action
  that reads that Report). It does not change the Tag member's kind or
  storage.

Scope still answers *who owns the value*. Publication answers *who may start
the call from outside composition*.

## Motivation

STEP-SPEC-1 gave every member an address `(scope, name)`. STEP-SPEC-2 made
Tag members composition-internal unless an Action published them.

That left two gaps:

1. **Repeated adapters.** Field-level economy (one Report, one Operation)
   still needs a handwritten Action for every name the world should call.
   STEP-SPEC-1 reserved an Operation-backed Action adapter for this burden.
2. **No internal Agent members.** Every Action and Record is currently a
   public Agent interface. Some Agent procedures and state should exist only
   for composition — the Internal/External distinction the original Guide
   drew for OOP vs TOP, applied inside TOP itself.

Without publication marks, programs either copy Tag data onto every Agent or
write forwarding Actions by hand. The first wastes the Field. The second is
correct but noisy. TOP should say the defaults once, and mark the exceptions.

## Specification

### 1. Two axes

Every Action, Record, Operation, and Report has:

```text
(scope, name, publication)
```

| Axis | Question | Values |
| --- | --- | --- |
| **Scope** | Who is the receiver? Who stores it? | Agent or Tag (STEP-SPEC-1) |
| **Publication** | Who may initiate access outside composition? | External or Internal |

Scope does not imply publication. An Action can be internal. A Report can be
published.

Language profiles may spell publication with their own keywords. This STEP
uses `@Secret` and `@Public` as the reference marks. Ada, Java, and similar
profiles may use `private` / `public` for the same bits. TOP's own words
remain **Internal** and **External**.

### 2. Defaults

| Contribution | Default publication |
| --- | --- |
| Action, Record | External |
| Operation, Report | Internal |

These defaults are STEP-SPEC-2 plus the Agent-side counterpart. Unmarked
`@Action` / `@Record` stay the world's interface. Unmarked `@Operation` /
ordinary Tag data stay composition-internal.

Imprints, Preconditions, Postconditions, Rip protocols, and Delete are not
ordinary members. They are not marked `@Secret` or `@Public`. They already
run only as Tagging or teardown protocols.

### 3. Composition

**Composition** is the same door as STEP-SPEC-2: Actions (including
published adapters), Record materializers, Imprints, Conditions, Rip
protocols, and other Tag-internal work.

Inside composition:

- internal Tag members are in scope (`Fire.color`, `Fire.roster()`);
- internal Agent members are in scope (`agent._charge()`, `agent.hp` when
  that Record is `@Secret`);
- external members remain available.

Outside composition, only **external** Agent members and the Tag control
plane (apply, Rip, Field, membership, Agent-bound views of **carried**
meaning) are usable. Bare internal Tag members still raise a Tag-resolution
failure. Internal Agent members raise the same class of failure: the name
exists, but it is not an application surface.

`@Secret` is not "callable only from other Actions." Imprints, Record
materializers, Conditions, and Rip must still see secret Agent state. The
rule is composition, not method-to-method visibility.

### 4. `@Secret` on Actions and Records

`@Secret` applies only to Agent-scoped members.

```python
class Fire( Tag ):

    @Secret
    @Record
    def ember_heat(
            agent,
            ) -> int:
        return 3

    @Secret
    @Action
    def ignite(
            agent,
            ) -> None:
        agent.hp -= agent.ember_heat

    @Action
    def strike(
            agent,
            enemy,
            ) -> None:
        agent.ignite()
        enemy.hp -= 4
```

From application code:

```python
ember.strike( dummy )     # external Action — allowed
ember.ignite()            # internal Action — Tag-resolution failure
ember.ember_heat          # internal Record — Tag-resolution failure
```

Inside `strike`, `ignite` and `ember_heat` resolve. The Agent still carries
the Record; the world does not read it.

A `@Secret` member occupies the Agent coordinate `(Agent, name)` as usual.
Independent Tags still cannot place an Action and a Record at that
coordinate. Overlay and Underlay follow STEP-SPEC-1. Publication is not a
third kind.

Captured handles fail closed: a `@Secret` Action taken inside composition
and called later from application code is still internal.

### 5. `@Public` on Operations and Reports

`@Public` applies only to Tag-scoped members. It does **not** make the Tag
member itself a gameplay API. Bare `Fire.color` and `Fire.roster()` remain
internal. `@Public` **constructs a normal Agent Action** that publishes the
Tag member.

That Action:

- occupies `(Agent, name)` with the **same name**;
- is external;
- Overlays with other Actions at that Agent coordinate;
- does not replace, Underlay, or merge with the Tag member at `(Tag, name)`.

#### Report

A `@Public` Report constructs a **nullary Action** that returns the current
visible Overlay of that Report. Storage stays on the Tag: one copy for the
Field. Uniform access lets application code read it as `agent.color` or
`agent.color()`.

```python
class Fire( Tag ):

    @Public
    color = "#ef5b35"
```

```python
ember.color               # published Action — "#ef5b35"
Fire.color                # still internal from main
ember.Fire.color          # carried Tag view — still valid
```

Two `@Public` Reports with the same name Overlay **as Actions** on the
Agent. The Reports themselves Overlay **as Reports** on the Tag. Those are
two histories, per STEP-SPEC-1.

```python
class Fire( Tag ):

    @Public
    color = "#ef5b35"


class Electric( Tag ):

    @Public
    color = "#f5cf3d"
```

After `Fire( ember )` then `Electric( ember )`, `ember.color` is the Electric
Action. `ember.Fire.color` remains `"#ef5b35"`. `@Underlay` on a later
published Action may extend the prior published Action; it does not Underlay
the Report.

#### Operation

A `@Public` Operation constructs an **Action** that forwards to that
Operation. The Agent is the caller. If the Operation concerns one Agent, the
Action passes that Agent as an explicit input, as in STEP-SPEC-2.

```python
class Agency( Tag ):

    @Public
    @Operation
    def dispatch(
            agency,
            sender,
            message,
            ):
        if sender not in agency:
            raise PermissionError(
                    "inactive"
                    )
        return network.broadcast(
                sender,
                message,
                )
```

```python
agent.dispatch( message )     # published Action
Agency.dispatch(              # still internal from main
        agent,
        message,
        )
```

The constructed Action is a real Action. Pinning, Overlay, Underlay, Delete,
and Rip treat it as one. The Operation remains the Tag-scoped body. Overlay
on the Tag still crunches the Operation; the Action name remains the Agent
entry.

`@Public` is explicit. Unmarked Operations are not projected onto Agents
(STEP-SPEC-1).

### 6. Mark combination

Publication marks stack with contribution marks. They do not replace them.

| Marks | Meaning |
| --- | --- |
| `@Action` | external Agent behavior (default) |
| `@Secret @Action` | internal Agent behavior |
| `@Record` | external Agent state (default) |
| `@Secret @Record` | internal Agent state |
| Tag data / `@Report` | internal Tag data (default) |
| `@Public` Tag data / `@Public @Report` | internal Report plus published Action |
| `@Operation` | internal Tag behavior (default) |
| `@Public @Operation` | internal Operation plus published Action |

`@Secret` on an Operation or Report is rejected: they are already internal.
`@Public` on an Action or Record is rejected: they are already external.
`@Secret` and `@Public` together on one contribution are rejected.

### 7. Access surface (amended)

Application code may use:

| Surface | Meaning |
| --- | --- |
| `agent.name` | external Agent members only |
| `agent.TagName.name` | Agent-bound Tag context (carried layer) |
| `Tag[ agent ].name` | same contextual view |
| `agent in Tag`, Fields, apply, Rip | control plane |

Application code may not use:

- bare internal Tag members (`Fire.color`, `Fire.roster()`);
- internal Agent members (`agent.ignite` when `@Secret`).

Inside composition, both internal and external members of the relevant
scopes resolve.

Conditions on the Agent (`agent.Has_Spellbook`) remain Agent-facing
diagnostics. They are not `@Secret` / `@Public` members.

### 8. Pins

Pinning still changes receiver, not publication:

- a Pin Action becomes an Operation on the Target Tag;
- a Pin Record becomes a Report on the Target Tag.

Publication of the resulting Tag members follows this STEP's Tag defaults
unless marked `@Public` on the Pin contribution. A Pin Target remains a live
identity: its overlay is readable on that Tag, as in STEP-SPEC-2.

## Rationale

Publication is cheaper than a new kind. Mission / Conspiracy named the same
Internal/External split; they never landed in the Specification. `@Secret` /
`@Public` (or `private` / `public` in other profiles) are the portable marks.

`@Public` constructs an Action so Overlay stays the law programs already
have: co-named published Reports stack as Actions on the Agent, while the
Field still holds one Report Overlay on the Tag. That keeps economy and
gives a world-facing spelling without copying values onto every Agent.

Kind stays honest. A Report remains data on the Tag. The published Action is
the repeated Agency adapter, generated because the programmer asked for it.

## Backwards compatibility

Unmarked programs do not change:

- Actions and Records stay external;
- Operations and Reports stay internal;
- handwritten Action adapters remain valid and are equivalent to `@Public`
  on the Operation they forward to.

Migration is additive:

- replace a forwarding Action with `@Public` on the Operation or Report;
- mark Agent helpers `@Secret` when they should leave the world-facing
  surface.

Existing `agent.Fire.color` / `Fire[ agent ].color` stay valid. `@Public`
does not remove carried Tag views.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Auto-project every Report and Operation onto Agents | Rejected in STEP-SPEC-1; silent name theft |
| `@Public` Report materializes a per-Agent Record copy | Rejected; loses Field economy |
| `@Public` Report publishes a live Record alias | Set aside; uniform access already makes a nullary Action read as data |
| `@Secret` visible only to other Actions | Rejected; Imprints, Records, Conditions, and Rip must participate |
| New kinds (Mission, Conspiracy) | Rejected; publication is a bit, not a kind |
| Language `private` / `public` as TOP vocabulary | Rejected for the stone; allowed as a profile spelling |
| Keep handwritten adapters only | Rejected as the sole publication path; the reserved adapter is this STEP |

## Acceptance requirements

A conforming Specification and profile must demonstrate:

- unmarked Actions/Records are external; unmarked Operations/Reports are
  internal;
- `@Secret` Agent members fail from application code and succeed inside
  composition, including Imprints and Rip;
- `@Public` Operations appear as external Actions and remain internal on
  the Tag;
- `@Public` Reports appear as nullary external Actions, still stored once
  on the Tag;
- published Actions Overlay at `(Agent, name)` independently of Reports
  Overlaying at `(Tag, name)`;
- unmarked Operations are not projected;
- illegal mark combinations are rejected at declaration;
- captured `@Secret` handles fail closed outside composition;
- Pin receiver change still holds, with publication following this STEP.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
