# STEP-SPEC-3: Member Publication

- **STEP:** SPEC-3
- **Desk:** spec
- **Title:** Member Publication
- **Author:** Julio Toboso (@JulTob)
- **Status:** Vetting        <!-- Recon | Brief | Vetting | Cleared | Redacted | Deployed -->
- **Created:** 2026-09-04
- **Revised:** 2026-09-04 (second draft, after review)

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

Every Agent or Tag member has a **publication**, independent of its scope.

- Agent members (Actions, Records) are **external** by default. `@Secret`
  makes one internal.
- Tag members (Operations, Reports) are **internal** by default.
  `Public(...)` publishes one on the Agent by constructing the publishing
  member for the author.

Scope answers *who owns it* (STEP-SPEC-1). Publication answers *who may
reach it from outside composition*. This is the Agency/Agent picture: what
the Agent does is public; what the Agency keeps is internal.

## Motivation

STEP-SPEC-2 made Tag members composition-internal unless an Action
publishes them. Two gaps remained:

1. **Repeated adapters.** Field economy (one Report, one Operation) needed a
   hand-written Action for every published name.
2. **No internal Agent members.** Every Action and Record was public. Some
   Agent procedures and state exist only for composition.

The first draft of this STEP had three defects found in review: its
reference spelling `@Public` over a bare assignment is not valid Python;
its rule for passing the Agent to a published Operation ("if the Operation
concerns one Agent") was not decidable; and it tied a published Report to
uniform access. This draft fixes all three.

## Specification

### 1. Two axes

```text
(scope, name, publication)
```

| Axis | Question | Values |
| --- | --- | --- |
| Scope | Who is the receiver? | Agent or Tag |
| Publication | Who may reach it from outside composition? | External or Internal |

### 2. Defaults and marks

| Contribution | Default | Mark |
| --- | --- | --- |
| Action, Record | External | `@Secret` → Internal |
| Operation, Report | Internal | `Public(...)` → published on the Agent |

Imprints, conditions, Rip protocols and Delete are protocols, not members;
they take neither mark.

### 3. The composition door

*Inside composition* means: while an Action, Imprint, Record builder,
condition, or Rip protocol bound to **this Agent** is running. Inside,
internal members of both scopes resolve. Outside, only external Agent
members and the control plane resolve (apply, Rip, membership, Fields,
Agent-bound views of carried meaning). A secret handle captured inside and
called outside fails closed.

Operations called directly on the Tag are outside the door unless reached
from one of the protocols above.

### 4. `@Secret` on Actions and Records

```python
class Fire(Tag):
    @Secret
    @Record
    def ember_heat(agent) -> int:
        return 3

    @Secret
    @Action
    def ignite(agent) -> int:
        return agent.ember_heat * 2

    @Action
    def strike(agent) -> int:
        return agent.ignite() + 1
```

`ember.strike()` works; `ember.ignite()` and `ember.ember_heat` raise the
language's attribute-missing failure outside composition. A secret member
occupies its `(Agent, name)` slot as usual; publication is not a third
kind.

### 5. `Public(...)` on Reports and Operations

`@Public` is a modifier and spells the same way on data and on behaviour,
because a Report is declared like a Record, as a builder:

```python
class Agency(Tag):

    @Public
    @Report
    def colour(tag):
        return "navy"

    @Public
    @Operation
    def dispatch(agency, sender, message):
        if sender not in agency:
            raise PermissionError("inactive")
        return network.broadcast(sender, message)
```

- A **published Report** appears on the Agent as a **read-only name** that
  reads the Tag's current value. One copy lives on the Tag.
- A **published Operation** appears on the Agent as an **Action** that
  calls the Operation with **the Agent as its second input**, after the
  Tag: `agent.dispatch(m)` is `Agency.dispatch(Agency, agent, m)`. This
  rule is mechanical; there is no "concerns one Agent" judgment.

The published Action is a normal Action: it overlays and underlays at
`(Agent, name)`, it is sticky after Rip, and a guarded Operation therefore
checks membership at invocation.

### 6. Modifiers

`@Secret` and `@Public` are modifiers that stack with `@Action`, `@Record`,
`@Operation` and `@Report` in either order. A modifier that restates the
default (`@Public @Record`, `@Secret @Report`) is accepted. Both on one
member is a contradiction and a Tag Declaration Failure.

## Rationale

Publication is a bit, not a kind. `Public` constructs a normal Action or a
read-only name so Overlay stays the one law programs already have, and the
Field keeps one copy of shared data. `@Secret` reuses the slot model of
STEP-SPEC-1 and adds only a door.

The door is defined by *this Agent's* protocols, not by call-stack
inspection, so an implementation can keep it cheap: a counter on the Agent
that its bound protocols raise while they run. Agents without secrets pay
nothing.

## Backwards compatibility

Unmarked programs do not change. Hand-written adapters remain valid and
are equivalent to `Public` on the Operation they forward to.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Auto-project every Report and Operation onto Agents | Rejected in STEP-SPEC-1 |
| `Public` Report materializes a per-Agent Record copy | Rejected; loses Field economy |
| `Public` Report via uniform access (`agent.colour()` reads a nullary Action) | Rejected; uniform access is Redacted (STEP-SPEC-4 notes) |
| `@Secret` visible only to other Actions | Rejected; Imprints, Records, conditions, Rip must see secret state |
| Underscore prefix as the only spelling of internal | Kept as the Python convention for names that are not contributions at all; `@Secret` is for members that *are* contributions |
| Runtime call-stack inspection for the door | Rejected; leaks through callbacks and threads and costs every call |

## Acceptance requirements

- unmarked Actions/Records external; unmarked Operations/Reports internal;
- `@Secret` members fail from application code and resolve inside Actions,
  Imprints, Record builders, conditions and Rip;
- captured `@Secret` handles fail closed;
- `Public` Reports read live from the Tag and are read-only on the Agent;
- `Public` Operations are Actions with the Agent as second input;
- contradictory marks rejected at declaration; redundant ones accepted.

Covered by `tests/test_tagkit.py::PublicationTests`.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
>
> *Drafted for the Director's confirmation:* Cleared on 2026-09-04, per the
> Director's direction in review ("Tag features are hidden by default, and
> agent's are public by default; `@Secret` for private agent features and
> `@Public` for public agency features, following the Agency-Agent model").
