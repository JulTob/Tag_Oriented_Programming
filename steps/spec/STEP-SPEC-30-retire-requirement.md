# STEP-SPEC-30: Retire `@Requirement`

- **STEP:** SPEC-30
- **Desk:** spec
- **Title:** Retire `@Requirement`
- **Author:** Julio Toboso (@JulTob)
- **Status:** Brief
- **Created:** 2026-10-09

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

`@Requirement` leaves TOP. A claim that must hold to enter a Tag and to
stay in it is written as two marks stacked on one function, `@Pre` and
`@Post`. That is what `@Requirement` already meant (§2.7), so nothing
else changes: the failures keep their two names, `Precondition.Alive` at
the door and `Postcondition.Alive` afterwards.

```python
class Crew(Tag):

    @Pre
    @Post
    def Alive(agent):                 # needed to come aboard, and to stay sound
        return agent.alive
```

## Motivation

The Director, on 2026-10-09: "@Requirement is not maquing it for me as a
special word. I think we could go back to just using @Pre and @Post
simultaneously".

- **One word for two checks hides them.** A reader of `@Requirement`
  must remember that it is a gate *and* a promise. The two marks say it
  on the page.
- **It has no failure of its own.** §2.7 says so: "A Requirement names
  no failure of its own." A program catches `Precondition.Alive` or
  `Postcondition.Alive`, never `Requirement.Alive`. The word exists only
  at the declaration.
- **It hides a trap.** STEP-SPEC-26 found one: a `@Requirement` that
  names a Base, `agent in Human[:]`, refuses every fresh Agent, because
  its gate half runs before the Form applies the Base (§2.2). With two
  marks the gate is visible, and so is the fix: keep the `@Post`, drop
  the `@Pre`.
- **Explicit beats implicit**, the maxim the Director used to choose
  STEP-SPEC-26's model.

Stacking already works on TopKit 0.2.0a4 (checked): a stacked `Alive`
refuses a dead Agent at the door with `Precondition.Alive`, and an Agent
that dies afterwards is defective, in `~Crew`, with
`Postcondition.Alive`.

## Specification

1. **`@Requirement` is withdrawn.** §2.7 drops its paragraph and example
   (spec lines 1161-1176). The §0.8 row "necessary to enter and to stay
   (§2.7)" reads `@Pre` + `@Post` only (line 280). Ring 2's conformance
   line drops "`@Requirement` in one word" (line 1368).
2. **The stacked form is the one spelling.** `@Pre` above `@Post`, or
   `@Post` above `@Pre`: the order of the two marks changes nothing.
3. **The kit.** Recommended: one release of warning, then removal.
   `@Requirement` still works in the next release, and raises a
   `DeprecationWarning` at class use that prints the two marks to write.
   The release after removes `TopKit.Requirement` and its export. Open
   question 1 offers removal at once instead.

## Rationale

A mark is worth a word of its own when it adds meaning. `@Requirement`
adds none: it is `@Pre` + `@Post`, and §2.7 is careful that it never
fails under its own name. Two short marks the reader already knows are
plainer than a third word that stands for them.

## Backwards compatibility

1. Programs that write `@Requirement` keep working for one release, with
   a warning naming the replacement. After that they fail at import:
   `from TopKit import Requirement` is an `ImportError`.
2. Files to change: `TopKit/declarations.py` (`Requirement`, lines
   239-246), `TopKit/__init__.py` (lines 17 and 63), `TopKit/GUIDE.md`
   (lines 32 and 446-451), `TopKit/CONTRACTS.md` (lines 19, 283-299, 506
   and 614), `TopKit/IMPLEMENTATION_NOTES.md` (lines 247-250),
   `spec/SPECIFICATION.md` (lines 280, 1161-1176 and 1368),
   `CONFORMANCE.md` (line 16), `tests/test_topkit.py` (five uses),
   `tests/differential_fuzz.py` (three uses).
3. STEP-SPEC-12, STEP-SPEC-14, STEP-SPEC-22 and STEP-SPEC-26 mention
   `@Requirement`. STEP-SPEC-22 lists it among the marks a Relation
   declares; STEP-SPEC-26 explains why a `@Requirement` naming a Base
   cannot work. Both read the same with `@Pre` + `@Post`.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Keep `@Requirement` | The Director: "not maquing it for me as a special word". |
| Keep it as a silent alias | Two spellings for one thing, and the trap of STEP-SPEC-26 stays hidden. |
| Rename it, for example `@Invariant` | An invariant usually means a promise that always holds, which is `@Post` alone. The new name would mislead. |

## Open questions for the Director

1. **Warn first, or remove at once?** TopKit is still an alpha
   (0.2.0a4), so a breaking change is allowed. Recommended: one release
   of `DeprecationWarning`, because a program then learns the
   replacement from the warning instead of from an `ImportError`.

## Acceptance requirements

- `tests/test_topkit.py`: the five `@Requirement` tests are rewritten
  with `@Pre` + `@Post` and still pass, failure names included; one test
  checks the `DeprecationWarning` and its message.
- `tests/differential_fuzz.py`: writes `@Pre` + `@Post` instead.
- The Specification, the Guide, the Contracts Guide and the
  implementation notes drop `@Requirement`, as in rule 1 and Backwards
  compatibility 2.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
>
> *Asked for by the Director on 2026-10-09:* "@Requirement is not
> maquing it for me as a special word. I think we could go back to just
> using @Pre and @Post simultaneously".
