# STEP-SPEC-7: Flags, Tags as Keywords

- **STEP:** SPEC-7
- **Desk:** spec
- **Title:** Flags, Tags as Keywords
- **Author:** Julio Toboso (@JulTob)
- **Status:** Deployed
- **Created:** 2026-09-04
- **Deployed:** 2026-09-05

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

A Tag marked `@Flag` is a **keyword**: its name is searchable from the
Agent's side, `"Undead" in ghoul` and `Undead in ghoul`, and through the
function `Keyword(ghoul, "Undead", Flying)`. Ordinary Tags are never found
by name. A Flag and anything else that answers the Agent's `in` (the host,
or a Tag's Action) collide, in either order, and the collision is refused
*(amended 2026-09-24)*.

## Motivation

Rules written as data (a table cell reading `"Undead-Flying"`) must be
checkable without importing the Tags, and must port between programs whose
Tags carry the same names. That is the way tabletop keywords work. Making
every Tag searchable by name was considered and set aside: matching by
name is global and implicit, and taking every Agent's `in` silently left
container hosts without it. Opt-in names the concept, contains the risk,
and turns the container case into a loud error.

## Specification

1. `@Flag` marks a Tag class. It is not a Base and does not appear in the
   Form.
2. While any Flag is active on an Agent, `probe in agent` answers True for
   the name or the class of an active Flag, False otherwise, including for
   ordinary active Tags. Names match exactly.
3. `Keyword(agent, *words)` answers the same for any object, tagged or not,
   and is the spelling that works before the first tagging.
   *(Amended 2026-09-24: it no longer claims to work "on a host that owns
   `in`". No Flag can be active there, so it answers False.)*
4. *(Amended 2026-09-24.)* One seat, one meaning. Something else may
   already answer the Agent's `in`:
   - the **host**, through its own `__contains__` or `__iter__`, read as
     the language reads `in`. In Python, for `__contains__` and then
     `__iter__`, the first class in the MRO that defines the name
     decides. A method owns the seat. The value `None`, Python's "`in` is
     unavailable", leaves the seat free, even under a parent that is a
     container;
   - a **Tag's Action** named `__contains__` or `__iter__`, a published
     Operation included, while it is visible (Actions are sticky, so a
     Ripped Tag's Action still counts).

   A Flag and any of these collide, in either order, and within one Form
   before any of it applies. The later one fails at the gate with a
   Composition Failure naming both sides, and nothing changes. A Flag that
   declares such an Action itself is a Declaration Failure. `__getitem__`
   alone is not a seat, and a Flag takes it: on a keyed host its `in`
   fails or never ends; on an index-style host (Python's old sequence
   protocol) its `in` worked, and stops meaning membership once a Flag
   lands.
5. `agent in Tag`, Fields, and every other kernel act are unchanged.

## Rationale

The Agent's `in` is a seat with one meaning: keywords. Membership already
has its spelling from the Tag's side. One hook on the runtime type, present
only while a Flag is active, answers every keyword in one lookup; Agents
without Flags pay nothing.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Every Tag searchable by name, empty-seat rule on containers | Rejected by the Director: "default for everything is a bit messy" |
| `class Undead(Flag)` as a Base | Set aside; puts Flag into every Form and Outline |
| Per-Tag `__contains__` Actions chained by Underlay | Same meaning, more machinery; one hook chosen |
| Case-insensitive names | Rejected; explicit before magical |

## Acceptance requirements

Covered by `tests/test_topkit.py::QueryTests` (flags, container refusal,
rules as keywords).

---

## Amendment, 2026-09-24

Found while building STEP-SPEC-17. Items 3 and 4 above carry the amended
text. Under the original rule, only a host defining `__contains__` was
refused. A host whose `in` came from `__iter__` (a party that iterates its
members) accepted a Flag, and `"alice" in party` flipped from True to
False without a word. A Tag's own `__iter__` Action was flipped the same
way, and a Tag's `__contains__` Action silently disabled the Flag's words.
The kit also read `__contains__ = None` as "keep looking up the MRO",
which is not how Python reads it. A child that set it under a container
parent (a `collections.abc.Sequence`) was refused.

| Question | The Director's decision |
| --- | --- |
| A host whose `in` comes from `__iter__` | Refused: "refuse iter objects by raising errors" |
| A Tag's `__iter__` or `__contains__` Action | Refused in either order: "A tag with iter should not silently flip. Raise error. A tag with contains should exclude the flags too by error raise." |
| The error message | "inform the user of the conflict": it names the Flag and what already answers `in` |
| `__contains__ = None` (or `__iter__ = None`) | A free seat, as Python reads it; the refusal check and the hook share one resolver |
| `None` on a child whose parent is a container | Allowed: the child's word is trusted, as Python does; the Guide notes the risk |
| Suggest `__contains__ = None` in the error | No: the error names the conflict; the Guide documents the free seat and its side effects |
| A host with only `__getitem__` | Not a seat: the Flag takes it, as before, even on an index-style host whose `in` worked |

Covered by `tests/test_topkit.py::InSeatTests`.

---

### Decision *(filled by the Director)*

> Status set to **Deployed** on 2026-09-05, because the Director approved
> the whole review in PR #3 ("all changes approved"), the rule is
> reflected in `spec/SPECIFICATION.md`, and TopKit 0.2.0a2 covers it in
> `tests/test_topkit.py`. Cleared on 2026-09-05, per the
> Director's direction in review ("I confirm the if and in with the
> @Flag"; `Keyword` as the function's name).
