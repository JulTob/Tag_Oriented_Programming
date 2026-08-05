# STEP-SPEC-1: Contribution Scope Follows the Receiver

- **STEP:** SPEC-1
- **Desk:** spec
- **Title:** Contribution Scope Follows the Receiver
- **Author:** Julio Toboso (@JulTob)
- **Status:** Brief
- **Created:** 2026-08-05

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

This STEP makes semantic scope part of every public Overlay address. Actions
and Records belong to an Agent. Operations and Reports belong to a Tag.
The place where a contribution is declared does not decide its scope; the
receiver that uses it does. Consequently, Agent and Tag contributions with
the same name remain independent, and Operations and Reports are never
implicitly projected onto flat Agent access.

## Motivation

The current Specification distinguishes Agent-level and Tag-level
contributions, but later describes one visible Overlay "by contribution
name." Name alone is not a complete address. An Agent Action and a Tag
Operation may share a useful name without being the same contribution:
they have different receivers, calling conventions, lifetimes, and access
paths.

One sentence makes that boundary especially unclear:

> An Agent acts through Actions, remembers through Records, coordinates
> through Operations, and gains context by Reports.

It may be read as a promise that Operations and Reports appear directly on
the Agent. That is not the access model described elsewhere, and it makes a
central Action look like it ought to be an Operation merely because its body
is written on a Tag.

This ambiguity matters in ordinary application code and in security-sensitive
code. A centrally governed `agent.broadcast( message )` can already be an
Action with one shared implementation. If membership must remain live, that
implementation can consult a guarded Agency Operation every time it runs.
No implicit projection is needed.

## Specification

### 1. Member scope

Every public member contribution has this Overlay coordinate:

```text
(scope, name)
```

TOP defines two public member scopes:

| Scope | Contributions | Semantic receiver |
| --- | --- | --- |
| **Agent** | Action, Record | one Agent |
| **Tag** | Operation, Report | one Tag, possibly acting over its Field |

The semantic receiver determines the scope.

- An Action is Agent-scoped even when its single implementation is declared
  centrally inside a Tag.
- A Record is Agent-scoped because each Agent carries its own value.
- An Operation is Tag-scoped because the Tag is its receiver.
- A Report is Tag-scoped because the Tag owns the shared value.

The source-code location does not override these rules.

Pinning is an explicit receiver change. When a Tag is applied to another Tag,
an Action may be adapted into an Operation and a Record may be materialized
as a Report. The resulting contributions occupy Tag scope because the Pinned
Tag is their receiver. This is an explicit Pin rule, not an implicit
projection onto every Agent.

### 2. One public slot per scope and name

Within one scope, a name identifies one public member slot.

- Same-kind Layers at the same coordinate follow the existing Overlay and
  Underlay rules.
- An Action and a Record cannot occupy the same Agent coordinate.
- An Operation and a Report cannot occupy the same Tag coordinate.
- A same-scope, cross-kind collision must fail atomically before membership,
  Imprints, Records, or other visible state commit.

Across scopes, equal names do not collide. They do not replace one another,
form an Underlay together, or change one another's history.

Kind alone is not the coordinate. Defining separate `(kind, name)` slots
would permit both callable and data meanings to claim the same
`receiver.name` spelling without saying which one the program receives.

### 3. Contract phases are separate

Preconditions and Postconditions do not occupy Agent or Tag member slots.
They belong to distinct Tagging phases:

```text
(precondition, name)
(postcondition, name)
```

A Precondition and a Postcondition may therefore share a name without
colliding. Each composes only with conditions in its own phase.

Imprints and Rip protocols remain ordered lifecycle protocols. They are not
ordinary public members and are not folded into the member coordinates
defined by this STEP.

### 4. Access follows scope

The canonical access law is:

| Access | Scope consulted |
| --- | --- |
| `agent.name` | Agent |
| `Tag.name` | Tag |
| Agent-bound Tag view | captured Agent context, then captured Tag context |

Flat Agent access must not expose a Report or Operation. Direct Tag access
must not silently bind an Action to an unspecified Agent.

An Agent-bound Tag view is an explicit contextual view over both scopes. If
both captured scopes contain the same name, Agent scope is selected first.
The Tag-scoped contribution remains available through direct Tag access.
This access precedence is only a spelling rule: the two contributions do not
replace or Underlay one another.

The misleading sentence in the Specification is replaced in substance by:

> An Agent acts through Actions and carries state through Records. It may
> consult Reports and invoke Operations only through explicit Tag context.

A language profile may use different syntax, but it must preserve these
semantic distinctions.

### 5. Central Actions and live authority

Declaring an Action on a Tag already provides one central implementation
which is bound to each relevant Agent:

```python
class Agency( Tag ):

    @Operation
    def dispatch(
            agency,
            sender,
            message,
            ):
        if sender not in agency:
            raise PermissionError(
                    "Agency membership is inactive"
                    )

        return network.broadcast(
                sender,
                message,
                )

    @Action
    def broadcast(
            agent,
            message,
            ):
        return Agency.dispatch(
                agent,
                message,
                )
```

The public capability remains an Agent Action:

```python
Agency( agent )

send = agent.broadcast

send( message )
```

Ripping remains sticky. It does not erase the Action:

```python
Agency.Rip( agent )

send( message )  # PermissionError
```

The call fails because the guarded Operation checks active Field membership
at invocation time. Checking only when `send` is captured would allow a stale
handle to bypass revocation.

This rule does not make TOP a concurrency or transaction-security system.
Long-running or asynchronous work may need to check authority again before
an irreversible commit.

### 6. No implicit Operation projection

An Operation is not automatically exposed as `agent.operation()`.

Such projection would invent an Agent receiver for Tag behavior, permit
unannounced shadowing of inherent methods, complicate same-name resolution,
and make revocation dependent on hidden fallback rules. Code that wants an
Agent-facing capability declares an Action explicitly.

An explicit Operation-backed Action adapter may be proposed later if repeated
forwarding becomes a demonstrated burden. Such an adapter would create a
normal Action; it would not make Actions and Operations the same kind.

## Acceptance requirements

A conforming Specification and language profile must demonstrate that:

- a Tag-declared Action is available through flat Agent access with one
  centrally stored body;
- Reports and Operations never appear through flat Agent access;
- direct and delegated guarded Operations validate active membership;
- a bound Action captured before Rip fails closed when its authority is
  checked after Rip;
- Rip leaves sticky Actions and Records intact unless an explicit Rip
  protocol changes them;
- same-name contributions in Agent and Tag scopes do not replace or Underlay
  one another;
- Action/Record and Operation/Report collisions within one scope fail
  atomically;
- an Agent-bound Tag view uses the defined Agent-first access rule without
  merging the two scope histories;
- Preconditions and Postconditions compose only within their own phases; and
- existing same-kind Overlay, Underlay, and captured snapshot behavior
  remains unchanged.

## Rationale

TOP's boundary is:

> **OOP owns inherent structure; TOP owns semantic context.**

Semantic context must still say who owns a value or behavior. Scope by
receiver does that with the least new machinery. It matches normal reading:
an Agent performs an Action, while an Agency performs an Operation over its
Field.

This rule also separates architecture from code placement. A function can be
implemented once, governed centrally, and still be an Action because one
Agent is its semantic receiver. An Operation is not "more central" than an
Action; it simply has a different receiver.

Using one public slot per `(scope, name)` keeps access predictable. It avoids
fixed cross-kind precedence tables while allowing Agent and Tag vocabularies
to evolve independently.

## Backwards compatibility

Programs that do not place different contribution kinds at the same
scope-and-name coordinate keep their existing behavior.

The current Python TagKit already:

- keeps flat Agent access separate from Reports and Operations;
- stores central Action bodies once and binds the current Agent;
- keeps Agent and Tag contribution stores separate;
- applies Agent-first lookup in an Agent-bound Tag view; and
- rejects Report/Operation collisions while Pinning.

To conform fully after this STEP is Deployed, TagKit must also reject an
Action/Record collision in Agent scope before mutation and cover the complete
scope law with tests.

Implementations that currently merge every contribution by bare name must
separate Agent members, Tag members, and the two contract phases. Code that
depends on a silent same-scope cross-kind precedence must rename one member
or introduce an explicit adapter.

## Alternatives considered

### Use bare names globally

Rejected. It makes Agent and Tag contributions compete despite different
receivers and access paths.

### Use `(kind, name)` as the coordinate

Rejected. It permits callable and data contributions to claim the same
public spelling and requires an arbitrary precedence table at access time.

### Project every Operation onto Agents

Rejected. It collapses the access boundary, invents a second calling
convention, creates shadowing and revocation hazards, and gains no central
implementation benefit that Actions do not already provide.

### Determine scope from declaration location

Rejected. Tags are the natural place to declare all semantic contributions.
Their class bodies are not one flat runtime namespace.

### Revoke every Action automatically on Rip

Rejected. TOP contributions are sticky by design. Capabilities requiring
live authority should check Field membership when invoked.

### Add an Operation-backed Action adapter now

Deferred. An explicit adapter may improve ergonomics, but it is a language
profile feature and is unnecessary to define the semantic boundary.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
