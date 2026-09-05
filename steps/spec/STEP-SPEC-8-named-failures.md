# STEP-SPEC-8: Named Failures

- **STEP:** SPEC-8
- **Desk:** spec
- **Title:** Named Failures
- **Author:** Julio Toboso (@JulTob)
- **Status:** Vetting
- **Created:** 2026-09-05

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

A failed check raises a failure that carries the check's name, as a
subclass of the general failure. The Precondition declared as
`Is_A_Caster` refuses with `TagPreconditionError.Is_A_Caster`, and the
marks are the short spelling of the same classes, so a program writes
`except Precondition.Is_A_Caster:`. Postconditions and Imprints follow
the same rule.

## Motivation

The Director, reading the Guide: "would be cool to have
`except TagPreconditionError.Is_A_Caster` or even nicer
`except Precondition.Is_A_Caster`". A handler that reads the program's
own word is clearer than one that reads a library's class name and then
inspects a message. It also keeps the Tag's dotted namespace for the
program (§0.8): the name lives under the mark, not under the Tag.

## Specification

1. `TagPreconditionError`, `TagImprintError` and `TagPostconditionError`
   each expose, per declared check name, a subclass named after the
   check. The subclass carries `name`; the general failure's `name` is
   `None`.
2. The failure raised for a check is that check's subclass, whether the
   check returned `False` or raised.
3. `Precondition.X`, `Postcondition.X` and `Imprint.X` are the same
   classes as `TagPreconditionError.X`, `TagPostconditionError.X` and
   `TagImprintError.X`.
4. A name exists from the moment a Tag class declaring it exists. Reading
   a name no Tag declared is an `AttributeError` that says so.
5. Names are per kind, shared across Tags: two Tags declaring `Ready`
   share `Precondition.Ready`.
6. Nothing else changes: handlers for the general failures keep working,
   messages are unchanged, `Contract` is unchanged.

## Rationale

Per kind rather than per Tag because the handler should read as the
program's sentence, and because per-Tag names would either put the
failure under the Tag's namespace (refused by §0.8) or need a second
level, `Precondition.Wizard.Can_Study`, which is more to type for the
uncommon case. Declared-only names because a typo in a handler must be
loud: a handler that never fires is the worst kind of silence.
Registration at class creation, not at first tagging, so a handler that
names a Tag not yet applied is still valid.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Any name accepted, subclass made on demand | Rejected: a misspelt handler would never fire and never complain |
| Per-Tag failures, `Wizard.Can_Study` | Rejected: the Tag's dotted namespace is the program's (§0.8) |
| `error.name` only, no subclasses | Set aside: `except` cannot branch on it without a re-raise |
| Also naming `TagCompositionError` by Record | Not now; Records fail on materialization, and the message names them |

## Acceptance requirements

Covered by `tests/test_tagkit.py::NamedFailureTests`.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
>
> *Drafted for the Director's confirmation:* Cleared on 2026-09-05, per the
> Director's request ("even nicer `except Precondition.Is_A_Caster`").
