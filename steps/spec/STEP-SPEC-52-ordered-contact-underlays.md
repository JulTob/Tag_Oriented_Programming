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

A Relation may list ordinary Tag declarations and other Relation declarations
as ordered Contact underlays. When `owner.Trusts(contact)` is called, TOP
applies each listed underlay to that Contact in declaration order, then runs
the selected actual Trusts Link's own Tagging. A Relation name in that list
resolves through this owner to an **actual** `owner.Knows` Link. It does not
denote a standalone Contact Tag or a shared Field.

The following Python-valid spelling is **provisional** and awaits the
Director's syntax decision. The Director's conceptual
`class Trusts(agent, contact, Network, agent.Knows)` cannot be evaluated as
Python class bases: neither `agent` nor `contact` exists when Python creates
the Relation. `@Link(underlays=(Network, Knows))` instead records the ordered
declarations. TOP resolves the Relation token `Knows` when the owner and
Contact exist, without a TOP parser or an extra function call at the use site.

## Motivation

An owner may know a Contact and then trust that Contact. The trust Link may
need the Contact to gain an ordinary `Network` Tag and to enter this owner's
actual `Knows` Link first. That is an ordered chain of distinct Taggings.
Making Trusts, Knows, and Network share one Field or Pair would erase the
separate Gates, Posts, Rip protocols, and memberships that TOP gives Tags.

## Specification

1. **Declaration spelling.** The proposed modifier
   `@Link(underlays=(Network, Knows))` lists ordinary Tag and Relation
   declarations in their Contact Tagging order. The Relation itself declares
   `class Trusts(Tag)`; the listed underlays are not its Python class bases.
   Bare `@Link` remains valid when no underlay is declared. No underlay's
   Contributions, actual Field, or Pair is copied into the selected Link.
   Each layer owns the Contributions it declares.
2. **Ordinary Tag underlay.** For an ordinary Tag declaration `Network`, the
   underlay turn is `Network(contact)`. The Tag's own Gate, Gains, Field
   admission, Posts, and failure rules apply.
3. **Relation underlay.** For a Relation declaration `Knows`, TOP resolves the
   actual Link granted to the same owner by the Tag that declared `Knows`.
   The underlay turn calls that exact Link on the Contact, even if another
   same-name Link is currently visible on the owner. While the owner belongs
   to the declaring Tag, this is equivalent to
   `DeclaringTag[owner].Knows(contact)`. `Knows` by itself has no Contact
   Field. If the owner has no such actual Link when this underlay turn
   arrives, the call fails clearly before the selected Relation's own Pair
   training. TOP does not automatically Tag the owner to make a missing Link.
4. **Selected Link last.** After the underlay turns, TOP applies the selected
   actual Link to the Contact. Its Pair is distinct from every underlay
   Link's Pair, even when the same owner and Contact occur in both Links.
   The selected Link's `@Imprint` may explicitly call other Links, including
   a reciprocal `contact.Knows(owner)`; no reciprocal Link is implied.
5. **Independent completed turns.** A later underlay or selected Link failure
   does not erase an earlier completed Tagging. Each turn follows TOP's
   ordinary Tagging and recovery rules. This Brief does not decide the open
   best-effort Imprint and Fix details of those rules.

**Open lifetime boundary.** Today, a gained Link may remain on the owner
after the Tag that declared it is Ripped. The owner can still reach the gained
Link, while `DeclaringTag[owner]` refuses its Agent view because the owner
left that Field. This Brief does not decide whether a Relation token may use
that retained Link after Rip or requires current membership in the declaring
Tag. Either rule must select the exact gained Link, never a later same-name
Overlay. The Director must settle this boundary before clearing this STEP.

For example, both Relation declarations are written inside `Social`, where
the name `Knows` is available when Python evaluates the `Trusts` modifier:

```python
class Network(Tag):
    pass

class Social(Tag):
    @Link
    class Knows(Tag):
        pass

    @Link(underlays=(Network, Knows))
    class Trusts(Tag):
        @Imprint
        def connect(agent, contact):
            contact.Knows(agent)  # explicit reciprocal Link

Social(ari)
Social(ruth)  # gives Ruth her own Knows Link for the reciprocal call
ari.Trusts(ruth)
```

The first three Tagging turns are `Network(ruth)`, `ari.Knows(ruth)`, and
`ari.Trusts(ruth)`. The Imprint's reciprocal call is a fourth, explicitly
programmed turn. If Ruth lacks `Knows`, that Imprint follows the ordinary
training-failure rule; no reciprocal membership is invented. The Fields of
`Network`, `ari.Knows`, and `ari.Trusts` remain independent.

The same Relation declaration token can be used by multiple owners. For
`Social(ben)` and `ben.Trusts(ruth)`, the `Knows` underlay resolves to
`ben.Knows`, not Ari's Link.

## Rationale

The proposed syntax uses `@Link`, which already marks a Relation, in the
same parameterized modifier style as `@Flag(...)` and `@Tool(...)`.
`underlays=` is keyword-only. Python passes the decorated class as the sole
argument to bare `@Link`, so `@Link(Network)` cannot unambiguously mean
"Network is one underlay"; write `@Link(underlays=(Network,))` for that case.
Resolution waits until the owner and Contact exist, so the abstract Relation
`Knows` reaches that owner's actual Link at use time. This is Tag
redirection, not Field sharing.

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
| Write `@Link class Trusts(Tag, underlays=(Network, Knows))` | A class keyword can work, but `MetaTag` must consume and validate it before Python calls `__init_subclass__`; an omitted `@Link` then needs another guard. |
| Write `@Link(Network)` for one underlay | Python already calls `Link(Network)` for bare `@Link` on `Network`. The keyword-only `underlays=` removes that ambiguity. |
| Apply every Relation base as its standalone Tag | A Relation is a blueprint; the actual Link belongs to one owner and has that owner's Field. |
| Put every underlay call in the Imprint | It works now, and remains available, but hides the declared Contact Tagging order inside training code. |
| Join Base and Shape Link families | It makes independent Links share membership, Pair Gains, and Rip state. |

## Acceptance requirements

- A Relation accepts an ordinary Tag and a Relation token in its ordered
  `underlays=` tuple. The selected actual Link is applied after both; bare
  `@Link` remains valid.
- The Relation token resolves through the current owner on every Link call;
  two owners reach different actual Links. It is never a standalone Field.
- The Contact may belong to all three Fields but has a distinct Pair in each
  actual Link. Ripping one Link does not remove another membership.
- A missing owner Link fails clearly before the selected Pair's training;
  completed earlier Tagging turns remain as ordinary TOP Taggings.
- The Director resolves the retained-Link-after-declaring-Tag-Rip boundary,
  and the runtime never substitutes a same-name Overlay for that Link.
- No reciprocal Contact Link appears unless an Imprint or other explicit
  program act requests it.
- STEP-SPEC-22, tests, the Specification, and Link guides agree on the
  cleared spelling and behavior before deployment.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
