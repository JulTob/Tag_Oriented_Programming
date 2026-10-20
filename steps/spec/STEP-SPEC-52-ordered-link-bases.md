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

The following Python-valid spelling is **provisional**. The Director's
conceptual `class Trusts(agent, contact, Network, agent.Knows)` cannot be
evaluated as Python class bases: neither `agent` nor `contact` exists when
Python creates the Relation. Resolving a Relation declaration token at the
later Contact Tagging turn supplies that intended meaning without a TOP
parser or an extra function call at the use site.

## Motivation

An owner may know a Contact and then trust that Contact. The trust Link may
need the Contact to gain an ordinary `Network` Tag and to enter this owner's
actual `Knows` Link first. That is an ordered chain of distinct Taggings.
Making Trusts, Knows, and Network share one Field or Pair would erase the
separate Gates, Posts, Rip protocols, and memberships that TOP gives Tags.

## Specification

1. **Declaration spelling.** A `@Link` Relation may name ordinary Tag and
   Relation declarations among its Python class bases. Their written order
   specifies the order in which the corresponding actual Tags are applied to
   a Contact. This use of Python class bases describes a TOP Tagging order;
   it does not copy a base declaration's Contributions, actual Field, or
   Pair into the selected Link. Each layer owns the Contributions it declares.
2. **Ordinary Tag base.** For an ordinary Tag declaration `Network`, the
   underlay turn is `Network(contact)`. The Tag's own Gate, Gains, Field
   admission, Posts, and failure rules apply.
3. **Relation base.** For a Relation declaration `Knows`, TOP resolves the
   actual Link granted to the same owner by the Tag that declared `Knows`.
   The underlay turn is that Link's call on the Contact, equivalent to
   `DeclaringTag[owner].Knows(contact)`. `Knows` by itself has no Contact
   Field. If the owner has no such actual Link, the call fails with a clear
   Link resolution error before this Relation's own Pair training. TOP does
   not automatically Tag the owner to manufacture a missing Link.
4. **Selected Link last.** After the underlay turns, TOP applies the selected
   actual Link to the Contact. Its Pair is distinct from every underlay
   Link's Pair, even when the same owner and Contact occur in both Links.
   The selected Link's `@Imprint` may explicitly call other Links, including
   a reciprocal `contact.Knows(owner)`; no reciprocal Link is implied.
5. **Independent completed turns.** A later underlay or selected Link failure
   does not erase an earlier completed Tagging. Each turn follows TOP's
   ordinary Tagging and recovery rules. This Brief does not decide the open
   best-effort Imprint and Fix details of those rules.

For example, both Relation declarations are written inside `Social`, where
the name `Knows` is available when Python creates `Trusts`:

```python
class Network(Tag):
    pass

class Social(Tag):
    @Link
    class Knows(Tag):
        pass

    @Link
    class Trusts(Network, Knows):
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
`Social(ben)` and `ben.Trusts(ruth)`, the `Knows` base resolves to
`ben.Knows`, not Ari's Link.

## Rationale

The syntax uses class bases, which already express an ordered Tag Form in
TOP. Resolution waits until the owner and Contact exist, so the program can
write the abstract Relation `Knows` in the declaration and get that owner's
actual Link at use time. This is a Tag redirection, not Field sharing.

The selected Link stays a separate Tagging turn. Its declaration can state
which preparatory Tags it needs while its Imprint retains full control over
additional, including reciprocal, operations.

## Backwards compatibility

Links are still a Vetting draft. PR #171 currently rejects ordinary Tag
bases on Relations and joins Relation bases into one Link family. Before any
Links runtime is cleared, it must instead accept the specified declaration
shape, resolve each underlay at Contact Tagging, and keep Fields and Pairs
independent as STEP-SPEC-51 proposes. Current #171 tests, STEP-SPEC-22 text,
and wiki examples that expect shared family membership need focused review.

Python itself may refuse an inconsistent or duplicate class-base ordering.
TOP does not reinterpret a class Python could not create.

## Alternatives considered

| Alternative | Why this Brief sets it aside |
| --- | --- |
| Write `class Trusts(agent, contact, Network, agent.Knows)` literally | Python evaluates bases before `agent` and `contact` are bound. This requires a new parser. |
| Apply every Relation base as its standalone Tag | A Relation is a blueprint; the actual Link belongs to one owner and has that owner's Field. |
| Put every underlay call in the Imprint | It works now, and remains available, but hides the declared Contact Tagging order inside training code. |
| Join Base and Shape Link families | It makes independent Links share membership, Pair Gains, and Rip state. |

## Acceptance requirements

- A Relation accepts an ordinary Tag base and a Relation base in their written
  order. The selected actual Link is applied after both.
- The Relation base resolves through the current owner on every Link call;
  two owners reach different actual Links. It is never a standalone Field.
- The Contact may belong to all three Fields but has a distinct Pair in each
  actual Link. Ripping one Link does not remove another membership.
- A missing owner Link fails clearly before the selected Pair's training;
  completed earlier Tagging turns remain as ordinary TOP Taggings.
- No reciprocal Contact Link appears unless an Imprint or other explicit
  program act requests it.
- STEP-SPEC-22, tests, the Specification, and Link guides agree on the
  cleared spelling and behavior before deployment.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
