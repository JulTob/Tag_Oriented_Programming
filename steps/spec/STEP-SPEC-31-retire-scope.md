# STEP-SPEC-31: Retire `Scope`

- **STEP:** SPEC-31
- **Desk:** spec
- **Title:** Retire `Scope`
- **Author:** Julio Toboso (@JulTob)
- **Status:** Brief
- **Created:** 2026-10-09

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

`Scope(agent, *tags)` leaves TOP. A block of code that holds a Tag for a
while says so with Python's own `try` and `finally`: tag the Agent before
the `try`, and Rip it in the `finally`.

```python
Sentry(guard)              # the guard joins Sentry
try:
    guard.Patrol()
finally:
    del Sentry[guard]      # the guard leaves, even if Patrol raised
```

This is the rule Python already teaches for a lock: take it before `try`,
give it back in `finally`. A `finally` block always runs when its `try`
block ends, whether the block finished or raised. That was `Scope`'s
guarantee all along: the kit's `Scope` is built on a `finally`
(`TopKit/lifecycle.py:200`). Now the reader sees it.

## Motivation

The Director, on 2026-10-09: "I don't like Scope as a function call in
TOP. Or generally using function calls as methodology. TOP should
integrate with the language. Also "Scope" is not an informative name.
Get it out".

- **TOP's own rule.** §0.8 says: "TOP borrows the language's own syntax
  for every Tag-level act … TOP should feel like part of the language,
  not a library's naming." Holding a Tag for a block is two acts, apply
  and Rip, and each already has its own syntax: `Sentry(guard)` and
  `del Sentry[guard]`. `Scope` gave the pair a library name.
- **The name says the wrong thing.** In TOP, "scope" already means who
  receives a contribution: Agent scope or Tag scope (§1.1, STEP-SPEC-1).
  `Scope(guard, Sentry)` borrows that word and says nothing about joining
  or leaving.
- **It made choices out of sight.** `Scope` decided, without a line on
  the page:
  - to leave a Tag the Agent already carried;
  - to Rip a Tag that failed at the door;
  - to leave a Base that a Shape pulled in (open for the Director since
    2026-10-01);
  - what to do with a Rip it could not make: drop it on `main`, report it
    on `step-19-sound-in`.

  Five rows of STEP-SPEC-6's amendment on `step-19-sound-in` are about
  these choices. Four are drafted for the Director's confirmation, and
  one is open. With `try` and `finally`, each choice is a line the
  program writes, or does not write.
- **It hid failures.** On `main`, a Rip that `Scope` could not make on
  the way out is dropped in silence: `except TagError: pass`
  (`TopKit/lifecycle.py:207-208`). A plain `finally` hides nothing (rule
  4).
- **It frees `with`.** The Director, on 2026-10-09: "with is ill-defined
  and not necessary. We should clean up the use for a possible future
  use." `Scope` is the only place TOP uses `with`. Without it, TOP gives
  `with` no meaning, and a later STEP may.

**Checked on TopKit 0.2.0a4** (`main`), with the spelling of the
Summary:

1. The block raises. The teardown runs, the guard leaves Sentry, and the
   block's own error reaches the caller.
2. The guard was a Sentry before the block. Checked first, as in rule
   3.2, he stays a Sentry after it.
3. A teardown fails in the `finally` while the block is raising. The
   caller gets the Rip's Composition Failure, and the block's error rides
   along as its *context*. Python prints both: "During handling of the
   above exception, another exception occurred".
4. A Postcondition fails at the door. The tagging raises before the
   `try`, so the block never runs and nothing is Ripped. The guard stays
   a defective Sentry, as after any tagging (§0.6).
5. A Precondition refuses at the door. The tagging raises before the
   `try`, and there is nothing to undo.
6. A Shape pulls in its Base: `Dire(bo)` brings `Wolf`. Then `del
   Dire[bo]` in the `finally` leaves `Wolf` on bo. A block that should
   take `Wolf` away too writes `del Wolf[bo]`.
7. The tagging is put *inside* the `try`, and is refused. The `del` in
   the `finally` then finds no member and raises a Resolution Failure,
   which the caller gets instead of the refusal (the refusal is only its
   context). That is why the rule says: tag *before* the `try`.

## Specification

1. **`Scope` is withdrawn.** The Specification drops:
   - the §0.7 rule "A Scope Rips what it applied, and only that" (lines
     248-251);
   - `Scope` from §0.8's list of functions (line 298);
   - the `Scope` row of §3.2's table (line 1231), and its example (lines
     1277-1280);
   - the word from Ring 3's line in the table of contents (line 29).
2. **§3.2's guaranteed tier is a Rip in a `finally`.** The row becomes:

   | Tier | Guarantee |
   | --- | --- |
   | **`del Tag[agent]` in a `finally`** | guaranteed: the language runs a `finally` whenever its block ends, by finishing or by raising |

   and §3.2's example becomes the Summary's.
3. **The pattern, in three forms.** The rule for all three: **tag before
   `try`, Rip in `finally`.**
   1. One Tag: the Summary.
   2. An Agent that may already carry the Tag. The block takes away only
      what it gave:

      ```python
      was_sentry = guard in Sentry[:]     # in the Field already, sound or not?
      Sentry(guard)                       # does nothing if he was
      try:
          guard.Patrol()
      finally:
          if not was_sentry:
              del Sentry[guard]           # take away only what this block gave
      ```

   3. Several Tags. One `try` for each Tag, so they leave in the reverse
      of the order they came:

      ```python
      Sentry(guard)
      try:
          Watch(guard)
          try:
              guard.Patrol()
          finally:
              del Watch[guard]
      finally:
          del Sentry[guard]
      ```

4. **A failure on the way out is never silent.** A Rip in a `finally`
   that fails raises, as every Rip does (§3.1). If the block was raising
   too, Python keeps the block's error as the context of the new one.
   TOP adds nothing to this.
5. **What the program now decides, that `Scope` decided for it:**

   | Case | `Scope` did | Now |
   | --- | --- | --- |
   | The Agent already carries the Tag | left it | rule 3.2, or the program Rips it anyway |
   | The Tag fails at the door (a Postcondition or an Imprint) | Ripped it; the block did not run | the tagging raises before `try`; the block does not run; the Agent stays a defective member (§0.6), unless the program Rips it in an `except` |
   | A Shape pulled in its Base | left the Base (open in STEP-SPEC-6) | the Base stays; `del Wolf[bo]` takes it away |
   | A Rip cannot be made on the way out | `main`: dropped; `step-19-sound-in`: reported | raised (rule 4) |
   | The block Ripped the Tag itself | `main`: Ripped again; `step-19-sound-in`: left | the `del` in `finally` finds no member and raises a Resolution Failure; a block that Rips its own Tag writes its `finally` to match |

6. **TOP gives `with` no meaning.** No TOP object is a context manager.
   A later STEP may give `with` a meaning (the Director: "for a possible
   future use").
7. **The kit.** Recommended: the same path as STEP-SPEC-30. In the next
   release `Scope` still works, and raises a `DeprecationWarning` that
   prints the pattern of rule 3. The release after removes
   `TopKit.Scope` and its export. Open question 1 offers removal at
   once instead.

## Rationale

**One line, one step.** `with Scope(guard, Sentry):` did four things on
one line: it checked whether the guard was a Sentry, applied the Tag,
promised a Rip at the end in reverse order, and decided what to do if
that Rip failed. The pattern spends a line on each step, so a reader
sees every one.

**The language's own guarantee.** `try`/`finally` is how Python promises
that something happens at the end of a block. Every Python programmer
knows it from files and locks. A TOP program that uses it needs no TOP
rule to read it.

**Fewer rules in TOP.** `Scope` needed its own rules: §0.7's rule, a
tier in §3.2, five amendment rows in STEP-SPEC-6, and the oracle's
`Exercise_Scope`. The pattern needs none: it is a tagging and a Rip,
which TOP already defines.

**The cost, honestly.** The pattern is longer: five lines instead of
two, more with several Tags. And it can be written wrong: the tagging
inside the `try` buries a refusal (Motivation, check 7). The Guide's
pattern and the rule "tag before `try`, Rip in `finally`" are the
answer. Python asks the same discipline for a lock.

## Backwards compatibility

1. Programs that use `Scope` keep working for one release, with a
   warning that shows the pattern. After that, `from TopKit import Scope`
   is an `ImportError`.
2. **Files to change on `main`:**
   - `TopKit/lifecycle.py`: `Scope` (lines 166-208), the `contextmanager`
     import (line 10), and the module docstring (line 1);
   - `TopKit/__init__.py`: lines 33 and 65;
   - `TopKit/GUIDE.md`: the import list (line 32), Pattern 9 "Roles that
     end" (lines 641-663 and 707), and the Do/Don't table (line 1009,
     "guarantee it with `Scope`");
   - `TopKit/IMPLEMENTATION_NOTES.md`: lines 21 and 238-240;
   - `spec/SPECIFICATION.md`: as in rule 1;
   - `tests/test_topkit.py`: the import (line 40), the ring line (line
     6), two `ExitProtocolTests` (lines 2465-2480), and `ScopeTests`
     (lines 2517-2565);
   - `tests/spec_examples.py`: line 192;
   - `tests/oracle_topkit.py`: `Exercise_Scope` (lines 660-713), its
     call (line 619), the import (line 50) and the docstring (line 6);
   - `tests/differential_fuzz.py`: `Scoping` (lines 1299-1342), the
     import (line 108) and the docstring (line 8).
   - `CHANGELOG.md` keeps its history.
3. **On `step-19-sound-in`**, `Scope` grew. Its sites there:
   - `TopKit/lifecycle.py`: `Scope` and its four helpers, `_rip_all`,
     `_report`, `_carries` and `_application` (lines 545-700), which
     nothing else uses;
   - `TopKit/GUIDE.md`: Pattern 9, its parts about `Scope` (lines
     689-812), and line 1142;
   - `spec/SPECIFICATION.md`: lines 29, 304, 1296, 1346, 1464-1497 and
     1620;
   - `CONFORMANCE.md`, line 17;
   - `TopKit/IMPLEMENTATION_NOTES.md`, lines 21 and 389-409;
   - `tests/test_topkit.py`: line 2102, two `ExitProtocolTests` (lines
     3291-3306), and `ScopeTests` (lines 3381-3745);
   - `tests/spec_examples.py`, lines 212-217;
   - `tests/oracle_topkit.py`: `Exercise_Scope` (lines 702-826);
   - `tests/differential_fuzz.py`: lines 29-33, 152, and `Scoping`
     (lines 1521-1571).

   STEP-SPEC-6's amendment there is about `Scope` in rows 2 to 7, and
   goes with it. Its ruling on a failed teardown is kept for every Rip by
   STEP-SPEC-18 amendment D, whose list "`del Tag[agent]`, a Scope's
   exit" becomes `del Tag[agent]`.
4. **Other STEPs.** The Brief STEPs of PR #26 are updated with this one:
   STEP-SPEC-22 (rule 5.5 and section 9), STEP-SPEC-24 (section 3),
   STEP-SPEC-26 (rule 8.2) and STEP-SPEC-28 (rule 3). Older STEPs keep
   their text as the record of their day: STEP-SPEC-6, STEP-SPEC-15 and
   STEP-SPEC-18, and STEP-SPEC-19 on `step-19-sound-in`. This STEP
   supersedes them where they speak of `Scope`. In STEP-SPEC-1 and
   STEP-SPEC-3, "Scope" means a contribution's scope, which stays.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Keep `Scope` | The Director: "Get it out". |
| Rename it: `Temporarily`, `For_Block`, `Holding` | A better name, still a function call as the method. The Director: "Or generally using function calls as methodology." |
| `with Sentry(guard):` or `with Sentry[guard]:` | The language's `with` on TOP's own objects. Set aside by the Director on 2026-10-09: "with is ill-defined and not necessary." Also, `Sentry(guard)` already means "apply, until Ripped"; giving its result a second meaning in a `with` would make one spelling mean two things. |
| `contextlib.ExitStack` | A library object again, and it hides the order of the Rips. |
| A Tag that Rips itself when the function that applied it returns | Magic: the end would happen where no line says so. |

## Implementation plan

1. **Where to build it.** `Scope` has about 15 sites on `main` and about
   40 on `step-19-sound-in`. Removing it on `main` first would make every
   one of those a merge conflict. Recommended: retire it on the line
   that merges last, or after `step-19-sound-in` merges.
2. **The oracle and the fuzz keep their coverage.** `Exercise_Scope` and
   `Scoping` test failure paths that still matter: a teardown that fails
   while the block raises, and a Base a Shape pulled in. Recommended:
   rewrite them to the pattern of rule 3, not delete them.
3. **The warning release**, if chosen (rule 7): `Scope` keeps its body
   and warns once per call site.

## Open questions for the Director

1. **Warn first, or remove at once?** This is STEP-SPEC-30's open
   question 1 again. Recommended: answer both the same way, with one
   release of `DeprecationWarning`, so a program learns the pattern from
   the warning, not from an `ImportError`.
2. **How far does "no function calls as methodology" reach?** TOP has
   other functions. Recommended line: an **act**, something that changes
   an Agent or a Tag, should be the language's syntax. A **read** that
   has no syntax may stay a function, as Python's own `len()` and
   `isinstance()` are. Under that line:

   | Function | Act or read | Today's language spelling |
   | --- | --- | --- |
   | `Apply(ari, Wizard, Sworn)` | act: apply several Tags | one line each, `Wizard(ari)`, `Sworn(ari)`. The closest relative of `Scope`; a candidate to retire. |
   | `Contract.Delete(ari, "Alive")` | act: end one promise | none yet. STEP-SPEC-27 proposes `del` for Reports, and could look at promises too. |
   | `At_Exit(ari)` | act: also run teardowns at interpreter exit | none: Python's own `atexit` is a function too. |
   | `Tags(ari)`, `Outline(ari)`, `Form(Wizard)` | read | as text only: `f"{ari:tags}"`, `f"{ari:outline}"`, `f"{Wizard:form}"`. |
   | `Keyword(x, "Undead")` | read | `"Undead" in x`, on an Agent (§1.8). |
   | `Contract.Status`, `Holds`, `Display` | read | `bool(ari)`, `f"{ari:contract}"`. |

   Each one the Director wants changed gets its own STEP.

## Acceptance requirements

- The files of Backwards compatibility 2 (or 3, on the line where it is
  built) no longer offer `Scope`, or offer it only with the warning of
  rule 7.
- The Guide's Pattern 9 teaches forms 1 and 2 of rule 3, with the rule
  "tag before `try`, Rip in `finally`", and is run by
  `tests/test_documents.py`.
- `tests/test_topkit.py`: the `ScopeTests` are rewritten to the pattern,
  covering the cases of rule 5; one test checks the warning, if chosen.
- The oracle and the fuzz exercise the pattern (Implementation plan 2).
- `steps/CATALOG-tag-algebra.md` marks `Scope` retired.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
>
> *Decided by the Director on 2026-10-09:* "I don't like Scope as a
> function call in TOP. Or generally using function calls as
> methodology. TOP should integrate with the language. Also "Scope" is
> not an informative name. Get it out".
