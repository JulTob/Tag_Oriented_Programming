# STEP-SPEC-61: Maps — Links between Tags

- **STEP:** SPEC-61
- **Desk:** spec
- **Title:** Maps: a Link declared on a Pin connects Tags
- **Author:** Claude, recording the Director's 2026-10-20 direction
- **Status:** Brief
- **Created:** 2026-10-20

> One STEP, one topic. If this grows a second purpose, split it into another STEP.

## Summary

A **Map** is the Tag-level counterpart of a Link. A Link declared in a
**Pin's** body grants each member **Tag** a Map of its own: its Contacts
are Tags, and each Pair connects Tag to Tag. Record-links between Agents
become Report-links between Tags, by the same receiver rule that already
renames a Pin's Record to a Report and its Action to an Operation.

| Agent level | Tag level (receiver rule) |
| --- | --- |
| Record | Report |
| Action | Operation |
| **Link** | **Map** |

The name **Map** was chosen by the Director (2026-10-20) over *Relation*
(already the name of the template declared under `@Link`) and over reusing
*Link* unchanged (which would break the receiver-rule naming pattern).

## Motivation

The Director asked (2026-10-20): *"Should we implement Tag-level-links?
Just like record-tags are links these could be report-links."* Two reasons
to say yes:

1. **The schema already implies it.** A Pin is the same structure one
   level up; the receiver rule lifts every member kind it receives. A
   connection ought to lift the same way, with the same machinery.
2. **It closes a real gap in the Geometry.** TOP's Tag-to-Tag structure
   today is only the Base/Shape order. There is no way to *declare* a
   named, directed connection between two Tags (`Sword —forged_by→ Smith`)
   that is not inheritance. Maps are exactly those missing arrows (see
   wiki chapter 2.1, §3): with them, the Geometry grows from a partial
   order into a richer graph, without touching inheritance at all.

## Specification (sketch — to be completed against the settled Link model)

1. `@Link` inside a **Pin's** body declares a Map template. The Pin's
   members are Tags, so the granted Map's Field holds **Tags as
   Contacts**, never Agents (the levels do not mix, §1.9).
2. Reads and admission follow the Link model the Director settled on
   2026-10-20: one independent Field and Pair per actual Map
   (STEP-SPEC-51), ordered complete underlays (STEP-SPEC-52), live Pair
   views, whole-Field Rip with the ordinary boundary.
3. The Pair's members follow the receiver rule for the level of what
   they land on: a Map Pair's values belong to Tags, so they read as
   Reports of the connected Tag pair.
4. A Map is one-directional, sticky, and Rips as a Tag does — the same
   laws as Links, one level up.
5. A Map template is never itself a Pin, and a Map's Field never holds
   Agents; a Link's Field never holds Tags.

## Rationale

Mechanism reuse over new machinery: a Map is Link code applied where the
members are Tags, plus the receiver rule's renaming. The alternative — a
separate Tag-to-Tag subsystem — would duplicate admission, Pairs, doors
and teardown for no semantic gain.

## Backwards compatibility

New capability; no existing behaviour changes. Today `@Link` in a Pin's
body is simply unexercised territory; this STEP gives it one meaning.

## Alternatives considered

- **Name it Relation** — rejected: *Relation* already names the template
  Tag declared under `@Link`; one word, two jobs.
- **Keep the name Link at both levels** — rejected: the receiver rule
  renames every other lifted member (Record→Report, Action→Operation);
  an unrenamed Link would be the one exception.
- **Do nothing** — rejected by the Director's direction to explore
  report-links; the Geometry gap is real.

---

### Decision *(filled by the Director)*

Status set to **____** on **____** because **____**.
