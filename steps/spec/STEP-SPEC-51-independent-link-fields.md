# STEP-SPEC-51: Independent Link Fields and Pairs

- **STEP:** SPEC-51
- **Desk:** spec
- **Title:** Independent Link Fields and Pairs
- **Author:** Codex, recording the Director's 2026-10-20 ruling
- **Status:** Brief
- **Created:** 2026-10-20
- **Issue:** [#347](https://github.com/JulTob/Tag_Oriented_Programming/issues/347)
- **Related draft:** [STEP-SPEC-22 / PR #171](https://github.com/JulTob/Tag_Oriented_Programming/pull/171)

> One STEP, one topic. This Brief says which actual Link owns a Field and a
> Pair. The ordered application of other Tags from a Link declaration belongs
> to a separate STEP.

## Summary

Each Link held by an Agent is an actual Tag with **its own Field**. For one
Link's Agent and one Contact, each actual Link has **its own Pair**. A Link
declared in a later Tag does not absorb, share, or retrain the Contacts of a
Link from an earlier Tag layer, even when both declarations use the same
name. A declared ordered underlay may apply another Link to the Contact in
its own separate Tagging turn; it never fuses their Fields or Pairs.

This records a correction to the Vetting Links draft in PR #171. Links are
not yet a Deployed feature of TopKit; this Brief does not claim a runtime
change on main.

## Motivation

TOP Tags have independent Fields. A Shape brings its Base Tags to an Agent,
but each Tag has its own membership and can be Ripped on its own. A Link is a
Tag of the Link's Agent, so the same rule must hold for Links. The current
#171 draft instead joins Base and Shape Link families and reuses a Pair
across their Fields. That makes a new Link call admit a Contact into another
Link without its own stated Tagging and makes a Shape train Contacts already
held by a Base Link. Those effects contradict the independence of Tags.

## Specification

1. **The Relation is a declaration.** `@Link class Knows(Tag)` inside a
   declaring Tag is a Relation blueprint. `Knows` alone is not an actual
   Contact Tag and has no Contact Field. For a tagged Agent `ari`,
   `ari.Knows` is an actual Link Tag with its own Field.
2. **One Field per actual Link.** Applying a declaring Tag grants its own
   actual Links to the Agent. A later Tag's same-name Link is another actual
   Link. The Agent's ordinary Overlay shows the latest `ari.Knows`;
   `Base[ari].Knows` selects the Link of the Base Tag layer. Reading either
   Link does not add a Contact.
3. **One Pair per Link and Contact.** If the same Contact is admitted into
   two actual Links of one Agent, each Link holds a different Pair. Their
   Actions, Records, conditions, and saved Rip work remain independent.
   Tagging a Contact in one Link does not automatically admit her to the
   other Link. An explicit Link call, or an ordered underlay declared by a
   later Link under the separate proposal, is required for that admission.
4. **One Link turn.** Calling `ari.Knows(contact)` runs the selected Link's
   Gate, training, Field admission, and Posts under the ordinary Tag rules
   that apply at the time Links are deployed. Another Link's Contact
   Tagging, if expressly requested by a declared ordered underlay or a
   protocol, remains its own turn and its own Field admission. A shared
   declaration name or declaring-Tag Form alone does not apply the other
   Link. `Base[ari].Knows(contact)` selects that Base layer's Link explicitly.
5. **Independent Rip and views.** Ripping one actual Link's Contact or whole
   Field acts on that Link's own membership, Pair, and saved teardown. It
   does not remove the Contact from another Link. A Pair view never silently
   switches to the Pair of another same-name Link. Whether a saved Pair
   view follows a new Pair after Rip and reTag remains open.

For example, this proposed behavior distinguishes two same-name Links:

```python
class Social(Tag):
    @Link
    class Knows(Tag):
        @Record
        def since(agent, contact, *, since=None):
            return since

class Spy(Social):
    @Link
    class Knows(Tag):
        @Record
        def cover(agent, contact, *, cover=None):
            return cover

Spy(ari)
base_link = Social[ari].Knows
spy_link = ari.Knows
assert base_link is not spy_link

spy_link(ruth, cover="colleague")
assert ruth in spy_link[:]
assert ruth not in base_link[:]

base_link(ruth, since=2024)  # separate, explicit Link Tagging
assert ruth in base_link[:]
assert base_link[ruth].since == 2024
assert spy_link[ruth].cover == "colleague"
```

Neither Relation in this example names the other as an underlay. A separate
proposal defines how a Relation may name an earlier Relation as an ordered
Contact underlay without sharing either actual Link's Field or Pair.

## Rationale

The selected Link is visible in TOP syntax. Its Field and Pair should be
just as explicit as an ordinary Tag's Field and Agent Gains. Independent
membership also lets a programmer deliberately connect Links, including
reciprocal Links, through an Imprint. A Relation's Python Base can describe
an ordered underlay without making two actual Fields into one Field.

## Backwards compatibility

Links are still a Vetting draft. PR #171 must replace its fused family and
Pair code, tests, STEP-SPEC-22 text, and wiki examples before merging. Its
current extension behavior would change: gaining `Spy` would not retrain
Contacts already in `Social[ari].Knows`, and a direct call to the independent
`ari.Knows(ruth)` would not add Ruth to the Base Link. The explicit Base Link
call shown above remains available.

## Alternatives considered

| Alternative | Why this Brief sets it aside |
| --- | --- |
| Fuse all same-name Links in the declaring Tag's Form | The Links would share membership even though their declaring Tags have independent Fields. |
| Share one Pair while keeping separate Link Fields | Pair Gains and Post truth would still cross Link boundaries, and Rip of one Link could disturb the other. |
| Train all Base Link Contacts when a Shape appears | A Shape would cause Tagging in another actual Link without naming the Contact or passing that Link's own Gate at a clear turn. |

## Acceptance requirements

- Two actual Links on one Agent keep independent Field membership and Pair
  Gains for the same Contact, including two same-name Links in different
  declaring Tag layers.
- A later declaring Tag does not retrain Contacts already held by an earlier
  Link merely because the Relations have a Base relationship.
- Direct Agent access chooses the visible Link; a declaring Tag view chooses
  that Tag's Link. Reads do not admit Contacts.
- Ripping one Link leaves another Link's Field, Pair, and saved Rip work
  intact. The Pair's access permissions remain scoped to its chosen Link.
- STEP-SPEC-22, current specification text introduced by #171, wiki, and
  tests agree before a Links implementation is cleared or deployed.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
