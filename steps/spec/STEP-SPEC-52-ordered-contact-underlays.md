# STEP-SPEC-52: Ordered Contact Underlays for Links

- **STEP:** SPEC-52
- **Desk:** spec
- **Title:** Ordered Contact Underlays for Links
- **Author:** Codex, recording the Director's 2026-10-20 design sketch
- **Status:** Brief
- **Created:** 2026-10-20
- **Issue:** [#347](https://github.com/JulTob/Tag_Oriented_Programming/issues/347)
- **Related Brief:** [STEP-SPEC-51 / PR #352](https://github.com/JulTob/Tag_Oriented_Programming/pull/352)
- **Related runtime draft:** [STEP-SPEC-22 / PR #171](https://github.com/JulTob/Tag_Oriented_Programming/pull/171)

> One STEP, one topic. This Brief proposes how a Link declaration names Tags
> to apply to its Contact before its own Pair training. STEP-SPEC-51 separately
> defines who owns each actual Link Field and Pair.

## Summary

A Relation may list ordinary Tags and actual Links as ordered Contact
underlays. When `owner.Trusts(contact)` is called, TOP applies each listed
underlay to that Contact in declaration order, then runs the selected actual
Trusts Link's own Tagging. An owner-relative selector such as `Agent.Knows`
resolves to the actual `owner.Knows` Tag at that call. An expression such as
`server.Registre` names the Link held by that particular Agent. A bare
Relation declaration such as `Knows` is a blueprint and is never applied as
though it were a Tag.

The following Python-valid spelling is **provisional** and awaits one naming
decision:

```python
@Link(underlays=(Network, Agent.Knows, server.Registre))
class Trusts(Tag):
    pass
```

`Agent` means "the Agent whose Link is being called". `Owner.Knows` is the
other candidate spelling for the same selector; this Brief does not choose
between `Agent` and `Owner`. The Director's conceptual
`class Trusts(agent, contact, Network, agent.Knows)` cannot be evaluated as
Python class bases because neither runtime seat exists when Python creates
the Relation. The modifier records the order while postponing only the
owner-relative lookup until both seats exist.

## Motivation

An owner may know a Contact and then trust that Contact. The trust Link may
need the Contact to gain an ordinary `Network` Tag and to enter this owner's
actual `Knows` Link first. That is an ordered chain of distinct Taggings.
Making Trusts, Knows, and Network share one Field or Pair would erase the
separate Gates, Posts, Rip protocols, and memberships that TOP gives Tags.

## Specification

1. **Declaration spelling.** The proposed modifier
   `@Link(underlays=(Network, Agent.Knows, server.Registre))` lists ordinary
   Tags and actual-Link selectors in their Contact Tagging order. The
   Relation itself declares `class Trusts(Tag)`; the listed underlays are not
   its Python class bases. Bare `@Link` remains valid when no underlay is
   declared. No underlay's Contributions, Field, or Pair is copied into the
   selected Link. Each Tag owns the Contributions it declares.
2. **Ordinary Tag underlay.** For an ordinary Tag declaration `Network`, the
   underlay turn is `Network(contact)`. The Tag's own Gate, Gains, Field
   admission, Posts, and failure rules apply.
3. **Owner-relative Link underlay.** `Agent.Knows` is resolved afresh when
   `owner.Trusts(contact)` runs. Its underlay turn is the ordinary call
   `owner.Knows(contact)`, with the Link currently visible at that coordinate.
   Two owners therefore reach two independent Links. `Knows` alone is not an
   accepted token: the Relation is a blueprint, with no Contact Field. If the
   owner has no actual `Knows` Link when this turn arrives, resolution fails
   clearly before the selected Trusts Gate. TOP does not Tag the owner merely
   to manufacture a missing Link.
4. **A particular Agent's Link underlay.** `server.Registre` records a soft
   reference to the Agent and the Link coordinate rather than copying its
   current Field or Pair. Each later Trusts call resolves the current
   `server.Registre` and calls it on the Contact. If the Agent or that Link is
   gone, resolution fails clearly. The Relation declaration does not keep the
   Agent alive.
5. **Complete ordered turns.** Each underlay is a complete ordinary Tagging,
   not a fragment of the selected Link's training. Its own Gate, Gainings,
   Imprints, Field admission, Posts, diagnostics, and recovery rules run
   before the next turn begins. The same named call inputs are available to
   every turn under the ordinary input abstraction. A failed turn stops the
   sequence; a completed earlier turn remains complete.
6. **Selected Link last.** After the underlay turns, TOP applies the selected
   actual Link to the Contact. Its Pair is distinct from every underlay
   Link's Pair, even when the same owner and Contact occur in both Links.
   The selected Link's `@Imprint` may explicitly call other Links, including
   a reciprocal `contact.Knows(owner)`; no reciprocal Link is implied.
7. **Independent completed turns.** A later underlay or selected Link failure
   does not erase an earlier completed Tagging. Each turn follows TOP's
   ordinary Tagging and recovery rules. This Brief does not decide the open
   best-effort Imprint and Fix details of those rules.

**Open extension boundary.** An ordinary repeated call to an already admitted
Tag is a no-op. This Brief therefore recommends that a repeated
`owner.Trusts(contact)` does not apply newly changed underlays as a side
effect. It does not yet decide how a later Relation layer with additional
underlays trains Contacts already admitted to the Link. That extension turn
must be decided before clearance.

For example, `Agent.Knows` redirects through whichever Social Agent calls
Trusts, while `server.Registre` redirects through one particular Agent:

```python
class Network(Tag):
    pass

class Host:
    pass

server = Host()

class Registry(Tag):
    @Link
    class Registre(Tag):
        pass

Registry(server)

class Social(Tag):
    @Link
    class Knows(Tag):
        pass

    @Link(underlays=(Network, Agent.Knows, server.Registre))
    class Trusts(Tag):
        @Imprint
        def connect(agent, contact):
            contact.Knows(agent)  # explicit reciprocal Link

Social(ari)
Social(ruth)  # gives Ruth her own Knows Link for the reciprocal call
ari.Trusts(ruth)
```

The first four Tagging turns are `Network(ruth)`, `ari.Knows(ruth)`,
`server.Registre(ruth)`, and `ari.Trusts(ruth)`. The Imprint's reciprocal call
is a fifth, explicitly programmed turn. If Ruth lacks `Knows`, that Imprint
follows the ordinary training-failure rule; no reciprocal membership is
invented. The Fields of `Network`, `ari.Knows`, `server.Registre`, and
`ari.Trusts` remain independent.

The same owner-relative selector can be used by multiple owners. For
`Social(ben)` and `ben.Trusts(ruth)`, `Agent.Knows` resolves to `ben.Knows`,
not Ari's Link. `server.Registre` still resolves through `server` in both
calls.

## Rationale

The proposed syntax uses `@Link`, which already marks a Relation, in the
same parameterized modifier style as `@Flag(...)` and `@Tool(...)`.
`underlays=` is keyword-only. Python passes the decorated class as the sole
argument to bare `@Link`, so `@Link(Network)` cannot unambiguously mean
"Network is one underlay"; write `@Link(underlays=(Network,))` for that case.
Resolution waits until the Link's Agent and Contact exist, so `Agent.Knows`
reaches that Agent's actual Link at use time. A concrete expression such as
`server.Registre` already names an actual Link, but TOP retains its Agent and
coordinate as a soft reference so later execution still performs the current
call. This is Tag redirection, not Field sharing or Relation inheritance.

The earlier provisional `class Trusts(Network, Knows)` spelling creates real
Python base relationships. It makes `issubclass(Trusts, Network)` true and
lets Python find `Network` members through `Trusts`, although the actual
Contact Tags and Link Pairs are independent. More seriously, `MetaTag`
checks Constants while Python creates the class, before `@Link` runs. A
Constant `Network.label` can therefore refuse a separately declared
`Trusts.label`. The parameterized modifier keeps `Trusts` based on `Tag`
and avoids that false coupling.

The selected Link stays a separate Tagging turn. Its declaration can state
which preparatory Tags it needs while its Imprint retains full control over
additional, including reciprocal, operations.

## Backwards compatibility

Links are still a Vetting draft. PR #171 currently gets Contact underlays
from Relation class bases, rejects ordinary Tag bases, and joins those
Relation bases into one Link family. This proposal would add the
parameterized `@Link` form and read its ordered tokens at Contact Tagging.
Before deployment, the Director must decide how to migrate the existing
Relation class-base form; it should not silently acquire a different
meaning. Tests, STEP-SPEC-22, the Specification, and Link guides that expect
shared family membership or Python class bases need focused review.

## Alternatives considered

| Alternative | Why this Brief sets it aside |
| --- | --- |
| Write `class Trusts(agent, contact, Network, agent.Knows)` literally | Python evaluates bases before `agent` and `contact` are bound. This requires a new parser. |
| Write `@Link class Trusts(Network, Knows)` | Real Python bases expose members and Constants across independent Contact layers before `@Link` can intervene. |
| Write `@Link class Trusts(Tag, underlays=(Network, Agent.Knows))` | A class keyword can work, but `MetaTag` must consume and validate it before Python calls `__init_subclass__`; an omitted `@Link` then needs another guard. |
| Write `@Link(Network)` for one underlay | Python already calls `Link(Network)` for bare `@Link` on `Network`. The keyword-only `underlays=` removes that ambiguity. |
| Accept bare `Knows` as an underlay | A Relation is a blueprint; only `Agent.Knows` or an actual Link such as `server.Registre` identifies a Tag that can be applied. |
| Put every underlay call in the Imprint | It works now, and remains available, but hides the declared Contact Tagging order inside training code. |
| Join Base and Shape Link families | It makes independent Links share membership, Pair Gains, and Rip state. |

## Acceptance requirements

- A Relation accepts an ordinary Tag, an owner-relative actual-Link selector,
  and a particular Agent's actual Link in its ordered `underlays=` tuple. The
  selected actual Link is applied after all three; bare `@Link` remains valid.
- `Agent.Knows` (or the finally chosen `Owner.Knows`) resolves through the
  calling owner on every Link call; two owners reach different actual Links.
  Bare `Knows` is refused because it is never a standalone Field.
- `server.Registre` resolves softly through that Agent's current coordinate
  without keeping the Agent alive.
- The Contact may belong to every underlay Field and the selected Field but
  has a distinct Pair in each actual Link. Ripping one Link does not remove
  another membership.
- A missing owner Link fails clearly before the selected Pair's training;
  completed earlier Tagging turns remain as ordinary TOP Taggings.
- The Director chooses the owner-relative word, `Agent` or `Owner`, and
  resolves the later-Relation-extension boundary before clearance.
- No reciprocal Contact Link appears unless an Imprint or other explicit
  program act requests it.
- STEP-SPEC-22, tests, the Specification, and Link guides agree on the
  cleared spelling and behavior before deployment.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
