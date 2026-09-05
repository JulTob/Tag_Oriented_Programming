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
by name. Applying a Flag to a host that defines its own `in` is refused.

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
   and is the spelling that works before the first tagging or on a host
   that owns `in`.
4. Applying a Flag to a host that defines `__contains__` (or the language's
   equivalent) fails at the gate with a Composition Failure; nothing
   changes.
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

Covered by `tests/test_tagkit.py::QueryTests` (flags, container refusal,
rules as keywords).

---

### Decision *(filled by the Director)*

> Status set to **Deployed** on 2026-09-05, because the Director approved
> the whole review in PR #3 ("all changes approved"), the rule is
> reflected in `spec/SPECIFICATION.md`, and TagKit 0.2.0a2 covers it in
> `tests/test_tagkit.py`. Cleared on 2026-09-05, per the
> Director's direction in review ("I confirm the if and in with the
> @Flag"; `Keyword` as the function's name).
