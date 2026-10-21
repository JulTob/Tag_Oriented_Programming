# STEP-SPEC-63: Maps — Links between Tags

- **STEP:** SPEC-63
- **Desk:** spec
- **Title:** Maps: a Link declared on a Pin connects Tags
- **Author:** Claude, recording the Director's 2026-10-20 and 2026-10-21 direction
- **Status:** Brief
- **Created:** 2026-10-20
- **Renumbered:** 2026-10-21, from SPEC-61 — that number is held by the
  Deployed STEP-SPEC-61 (Condition Lifetimes)
- **Depends on:** STEP-SPEC-51 (independent Link Fields and Pairs) and
  STEP-SPEC-52 (ordered Link underlays), both **Brief**; and on the Link core
  existing in TopKit, which it does not yet

> One STEP, one topic. If this grows a second purpose, split it into another STEP.

## Summary

A **Map** is the Tag-level counterpart of a Link. A `@Link` declared in a
**Pin's** body is a Map template: applying that Pin to a Tag grants the Tag a
Map of its own, whose Contacts are Tags and whose Pairs connect Tag to Tag.
Nothing new is invented — the receiver rule already renames every member a Pin
receives, and a connection lifts the same way:

| Agent level | Tag level (receiver rule) |
| --- | --- |
| Record | Report |
| Action | Operation |
| **Link** | **Map** |

The name **Map** is the Director's choice (2026-10-20) over *Relation*, which
already names the template class declared under `@Link`, and over reusing
*Link* unchanged, which would make it the one lifted member that is not
renamed.

## Motivation

The Director asked (2026-10-20): *"Should we implement Tag-level-links? Just
like record-tags are links these could be report-links."* Two reasons to say
yes:

1. **The schema already implies it.** A Pin is the same structure one level
   up, and the receiver rule lifts every member kind a Pin receives. A
   declared connection ought to lift by the same rule, with the same
   machinery, rather than becoming a separate subsystem.
2. **It closes a real gap in the Geometry.** TOP's only Tag-to-Tag structure
   today is the Base/Shape order, which is inheritance. There is no way to
   *declare* a named, directed connection between two Tags
   (`Sword —forged_by→ Smith`) that is not inheritance. Maps are exactly
   those missing arrows (wiki chapter 2.1 §3): with them the Geometry grows
   from a partial order into a graph, without touching inheritance at all.

## Specification

### 1. Declaration and seats

1. **A Map template is a Relation declared in a Pin.** `@Link(tag, contact)`
   on a nested `class Knows(Tag)` inside a **Pin's** body declares a Map
   template. The same decorator declares a Link inside an ordinary Tag; what
   it lands as is decided by the receiver, exactly as `@Record` lands as a
   Report and `@Action` as an Operation when a Pin receives them (§1.1).
2. **Every Map names its seats.** `tag` is the pinned Tag whose actual Map
   receives the call; `contact` is the other Tag in that call. The seat is
   written `tag`, not `agent`, because the receiver is a Tag (the receiver
   rule, §1.1). Bare `@Link` in a Pin body is refused, as it is in a Tag.
3. **Protocol functions receive the two ordered seats.** A Map's members are
   written `def since(tag, contact, *, since=None)`. A Map's Record lands as
   a **Report of the connected Tag pair**, by the same receiver rule that
   makes a Pin's Record a Report of the pinned Tag.
4. **A template owns nothing.** A bare Relation name is a blueprint with no
   Field and no Contacts. An actual Map is reached only through a Tag:
   `Wizard.Knows` is the actual Map of `Wizard`.

### 2. The levels never mix

5. **A Map's Contacts are Tag-level.** A Map's Field holds Tags, Pins and
   Links — never Agents. A Link's Field holds Agents, never Tags. A Map
   template is never itself a Pin.
6. **A Pin may pin a Link** (Director, 2026-10-21: *"pins should also be able
   to tag links"*). A Pin's Field admits Tags, Pins **and Links**, so a Link
   is a legitimate Pin Target. This is the one place the level rule widens: a
   Pin is the *set pointer*, and it may point at a set (a Tag), at another
   pointer (a Pin), or at a connection (a Link). It still may never point at
   an object — that remains the category error of §1.9. When Maps are built,
   `_check_pin_target` must admit a Link alongside Tags and Pins.

### 3. Independence, lifted from STEP-SPEC-51

Each law below is STEP-SPEC-51's law with Tags in the Agent's seat.

7. **One Field per actual Map.** Applying a Pin grants its own actual Maps to
   the pinned Tag. A later Pin's same-name Map is another actual Map. The
   Tag's ordinary Overlay shows the latest `Wizard.Knows`; `Rare[Wizard].Knows`
   selects the Map of that Pin layer. Reading either Map admits no Contact.
8. **One Pair per Map and Contact.** If the same Contact Tag is admitted into
   two actual Maps of one Tag, each Map holds a different Pair. Their
   Operations, Reports, Posts and saved Rip work stay independent. Admitting a
   Contact in one Map never admits it to the other; that needs an explicit Map
   call or a declared ordered underlay.
9. **One Map turn.** `Wizard.Knows(Elf)` runs the selected Map's Gate,
   training, Field admission and Posts as one turn, under the ordinary Tag
   rules. A shared declaration name or Pin Form alone applies no other Map.
   `Rare[Wizard].Knows(Elf)` selects that Pin layer's Map explicitly.
10. **Independent Rip and live Pair views.** Ripping one actual Map's Contact
    or whole Field acts on that Map's own membership, Pair and saved teardown,
    and does not touch another Map. A saved `view = m[contact]` is a lazy
    shortcut to that **same actual Map** and Contact: each use resolves what a
    fresh `m[contact]` would resolve then, reaching the newly current Pair
    after Rip and reTag. It never follows the Tag's name Overlay to a
    different same-name Map.

### 4. The ordered header Form, lifted from STEP-SPEC-52

11. **The class header is the ordered Form.** Entries resolve and apply left
    to right; the selected actual Map runs after the header completes. The
    header is TOP syntax: it grants no Python MRO lookup, copies no members,
    creates no `issubclass` promise and joins no Map families.
12. **An ordinary Pin entry applies to the Contact.** A Pin named in the
    header pins the Contact Tag: `Catalogued(contact)`.
13. **`tag.Knows` is the Tag-seat Map**, taking the opposite seat as its
    Contact. In `Wizard.Allies(Elf)` it means `Wizard.Knows(Elf)`.
14. **`contact.Knows` is the Contact-seat Map**, also taking the opposite
    seat. In `Wizard.Allies(Elf)` it means `Elf.Knows(Wizard)`. It is the
    declarative reciprocal; no reciprocal is otherwise implied.
15. **A particular Tag's Map** such as `Registry.Listed` resolves that Tag's
    current actual Map and applies it to the Contact. The declaration stores a
    soft Tag-and-name reference — not the current Field, not the Pair, and not
    a strong reference keeping the Tag alive.
16. **No bare Relation in the header.** `Knows` alone is refused; it owns no
    Field. Only `tag.Knows`, `contact.Knows` and `Registry.Listed` name actual
    Tags that can take a target.
17. **Complete independent turns.** Every header entry performs a complete
    ordinary Tagging with its own Gate, Gainings, Imprints, Field admission,
    Posts, diagnostics and recovery. A failed turn stops the sequence; earlier
    completed turns stay complete under the ordinary Tagging law.
18. **Selected Map last**, with its Pair distinct from the Pairs of any header
    entry, even when the same two Tags are involved.
19. **A repeated admitted call is the ordinary active no-op.** It does not
    rerun the header because the Relation later changed. Rip the Contact from
    that actual Map, then map it again to run the current Form and training.
20. **Seats resolve live.** `tag.Knows` captures no Tag at declaration; each
    Map call substitutes its own receiver, and `contact.Knows` its own
    Contact. A concrete `Registry.Listed` also resolves live, remembering
    `Registry` weakly and the coordinate `Listed`; if either is gone, that
    turn fails clearly before the selected Map's Gate.

### 5. Proposed language

This is the intended spelling, **not** a runnable example: neither Links nor
Maps exist on `main`.

```python
from TopKit import Link, Pin, Record, Tag, contact, tag


@Pin
class Social(Tag):

    @Link(tag, contact)
    class Knows(Tag):

        @Record
        def since(tag, contact, *, since=None):   # a Report of the Tag pair
            return since


class Wizard(Tag):
    pass


class Elf(Tag):
    pass


Social(Wizard)                      # the Pin grants Wizard its own Map
Social(Elf)

Wizard.Knows(Elf, since=1204)       # one Map turn, Tag to Tag
assert Elf in Wizard.Knows[:]       # a Field of Tags
assert Wizard.Knows[Elf].since == 1204
assert Wizard not in Elf.Knows[:]   # no reciprocal is implied
assert not hasattr(Wizard, "since")  # never on the Tag itself
```

## Rationale

**Mechanism reuse over new machinery.** A Map is Link code applied where the
members are Tags, plus the receiver rule's renaming. A separate Tag-to-Tag
subsystem would duplicate admission, Pairs, doors and teardown for no semantic
gain, and would be a second place for the same bugs to live.

**The seat is named `tag` for the same reason a Pin's Record is a Report.** The
receiver decides the vocabulary. Calling the first seat `agent` inside a Pin
would be the only place in TOP where a Pin's member names its receiver by the
lower level's word.

**Independence is not optional.** Lifting STEP-SPEC-51 unchanged is what keeps
`for t in Wizard.Knows` honest: one actual Map, one Field, one Pair per
Contact. The alternative — sharing a Pair across same-name Maps — is exactly
the defect STEP-SPEC-51 was written to correct one level down.

## Backwards compatibility

New capability; no existing behaviour changes. Today `@Link` in a Pin's body is
unexercised territory, and this STEP gives it one meaning. The only change to
an existing rule is §1.9's Pin-Target list, which gains Links (law 6) — a
widening, so no program that works today stops working.

## Status gate and dependencies

This STEP **cannot be Deployed before Links are**. Specifically:

1. **STEP-SPEC-51 and STEP-SPEC-52 are both Brief.** Maps lift their laws
   verbatim; if either changes under review, laws 7–20 here change with it.
2. **There is no Link core in TopKit.** `Link` is not exported and no Link
   tests exist, so no part of this STEP is implementable today, and none of it
   is claimed as runtime behaviour.
3. **Order of work.** Clear SPEC-51 and SPEC-52, build the Link core, then
   build Maps as that core applied where the members are Tags. Only law 6 (a
   Pin may pin a Link) touches code that exists now, and it is small and
   independent: `_check_pin_target` admits a Link.

Accordingly this STEP asks the Director to Clear the **design**, not to
schedule an implementation.

## Alternatives considered

| Alternative | Why set aside |
| --- | --- |
| Name it **Relation** | *Relation* already names the template class declared under `@Link`; one word, two jobs. |
| Keep the name **Link** at both levels | The receiver rule renames every other lifted member (Record→Report, Action→Operation); an unrenamed Link would be the lone exception. |
| A separate Tag-to-Tag subsystem | Duplicates admission, Pairs, doors and teardown; two homes for one set of bugs. |
| Keep the seat word `agent` inside a Pin | Contradicts the receiver rule, which is the whole reason a Map exists. |
| Imply a reciprocal Map automatically | Hidden Taggings. `contact.Knows` in the header makes the reciprocal explicit and ordered (law 14). |
| Do nothing | The Director asked for report-links, and the Geometry gap is real: no declared, non-inheritance arrow between Tags. |

## Acceptance requirements

When Links exist and this STEP is Cleared, Maps are accepted when:

- A `@Link` in a Pin's body grants each pinned Tag its own actual Map; the
  template alone has no Field, and reading a Map admits no Contact.
- A Map's Field holds Tags, Pins and Links and refuses an Agent; a Link's
  Field refuses a Tag.
- Two same-name Maps from different Pin layers are distinct actual Maps with
  distinct Fields and Pairs; `Rare[Wizard].Knows` selects a layer explicitly.
- A Map's Record reads as a Report of the connected Tag pair, and lands on
  neither Tag's Agents.
- The ordered header applies its entries left to right as complete
  independent turns, with the selected Map last; a failed entry stops the
  sequence and leaves earlier turns complete.
- `tag.Knows` and `contact.Knows` resolve live per call, and a concrete
  `Registry.Listed` holds its Tag weakly and fails clearly when it is gone.
- Ripping one Map's Contact leaves other Maps untouched, and a saved Pair
  view re-resolves to the current Pair after Rip and reTag.
- A repeated admitted Map call is the ordinary no-op and does not rerun the
  header.
- A Pin accepts a Link as a Target and still refuses an object (law 6).

---

### Decision *(filled by the Director)*

Status set to **____** on **____** because **____**.
