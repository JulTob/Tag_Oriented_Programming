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

**Words used here.**
- **At the door**: while a tagging runs, before the Agent is handed back.
  A Precondition can refuse there. An Imprint or a Postcondition can fail
  there after the Tag has landed (§0.6).
- **Context** (of an error): the earlier error Python keeps inside a new
  one, when the new one is raised while the earlier one is still on its
  way out. Python prints both.

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
  - to Rip a Tag that failed at the door (on `main`, only after a
    Postcondition);
  - to leave a Base that a Shape pulled in (open for the Director since
    2026-10-02, on `step-19-sound-in`);
  - what to do with a Rip it could not make: drop it on `main`, report it
    on `step-19-sound-in`;
  - to leave a Tag the block had Ripped itself, on `step-19-sound-in`.

  Six rows of STEP-SPEC-6's amendment on `step-19-sound-in` (rows 1 to
  6) are about these choices. Four are drafted for the Director's
  confirmation (rows 1, 4, 5 and 6), one is open (row 3), and row 2 has
  neither mark. With `try` and `finally`, each choice is a line the
  program writes, or does not write.
- **It hid failures.** On `main`, a Rip that `Scope` could not make on
  the way out is dropped in silence: `except TagError: pass`
  (`TopKit/lifecycle.py:207-208`). A plain `finally` hides nothing (rule
  4).
- **It frees `with`.** The Director, on 2026-10-09: "with is ill-defined
  and not necessary. We should clean up the use for a possible future
  use." `Scope` is the only place the Specification uses `with`.
  Without it, the Specification gives `with` no meaning, and a later
  STEP may. (STEP-SPEC-15, still Brief, proposes `with Try(agent):`;
  rule 6 says what this STEP means for it.)

**Checked on TopKit 0.2.0a4** (`main`):

1. The block raises. The teardown runs, the guard leaves Sentry, and the
   block's own error reaches the caller.
2. The guard was a Sentry before the block. With the Summary's spelling,
   he is not a Sentry after it: the `finally` Rips him. With the check of
   form 2 (rule 3), he stays one.
3. A teardown fails in the `finally` while the block is raising. The
   caller gets the Rip's Composition Failure. Its cause is the
   teardown's own error, and the block's error is kept inside both, as
   their context. Python prints all three, in order: the block's error;
   "During handling of the above exception, another exception
   occurred"; the teardown's error; "The above exception was the direct
   cause of the following exception"; the Composition Failure.
4. A Postcondition fails at the door. The tagging raises before the
   `try`, so the block never runs and nothing is Ripped. The guard stays
   a defective Sentry, as after any tagging whose Postcondition fails
   (§0.6, §2.5).
5. A Precondition refuses at the door. The tagging raises before the
   `try`, and there is nothing to undo.
6. A Shape pulls in its Base: `Dire(bo)` brings `Wolf`. Then `del
   Dire[bo]` in the `finally` leaves `Wolf` on bo. A block that should
   take `Wolf` away too writes `del Wolf[bo]`.
7. The tagging is put *inside* the `try`, and is refused. The `del` in
   the `finally` then finds no member and raises a Resolution Failure.
   The caller gets that failure, not the refusal. The refusal is only
   kept inside it, as its context. That is why the rule says: tag
   *before* the `try`.
8. Several Tags, one `try` nested inside another, and the inner Tag
   fails at the door. Checked with Watch, a Shape over Sentry whose
   Postcondition fails. The outer `finally` still runs, `del
   Sentry[guard]` is refused ("Sentry is required by active Shape(s):
   Watch"), and the caller gets that Composition Failure, not Watch's
   broken promise. That is why form 3 (rule 3) tags every Tag before one
   `try`. `Scope` Ripped both Tags here, on `main` and on
   `step-19-sound-in`.

## Specification

1. **`Scope` is withdrawn.** The Specification drops:
   - the §0.7 rule "A Scope Rips what it applied, and only that" (lines
     248-251);
   - `Scope` from §0.8's list of functions (line 298);
   - the `Scope` row of §3.2's table (line 1231), and its example (lines
     1277-1281);
   - the word from Ring 3's line in the table of contents (line 29);
   - from §3.1, "`__enter__` and `__exit__`" in "constructor and
     destructor, `__enter__` and `__exit__`" (lines 1195-1196): those
     are the two hooks of a `with`, which TOP no longer gives (rule 6).
2. **§3.2's guaranteed tier is a Rip in a `finally`.** The row becomes:

   | Tier | Guarantee |
   | --- | --- |
   | **`del Tag[agent]` in a `finally`** | guaranteed: the language runs a `finally` whenever its block ends, by finishing or by raising |

   §3.2's sentence "An implementation provides three tiers and says which
   is which" (lines 1225-1226) becomes "There are three tiers. The
   implementation provides the first and the third; the program writes
   the second." §3.2's example becomes the Summary's.
3. **The pattern, in four forms.** The rule for all four: **tag before
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

      Write `Sentry[:]`, with the brackets. `guard in Sentry[:]` asks the
      whole Field, sound or broken. On `step-19-sound-in`, `guard in
      Sentry` asks only for a sound Sentry: a guard who was a broken
      Sentry would read `False`, and the `finally` would take away a Tag
      he already had.
   3. Several Tags. Tag them all before the `try`, and Rip them in the
      `finally` in reverse order:

      ```python
      Sentry(guard)
      Watch(guard)
      try:
          guard.Patrol()
      finally:
          del Watch[guard]
          del Sentry[guard]
      ```

      If Watch fails at the door, the error is raised before the `try`:
      the caller gets Watch's own failure, and both Tags stay. If a Rip
      in the `finally` fails, its error leaves at once, and the Rips
      after it do not run: their Tags stay, and the error says which Rip
      failed. A program that must try every Rip even when one fails can
      nest one `try` per Tag. Then a door failure of an inner Tag runs
      the outer `finally` (Motivation, check 8).
   4. A Tag that may fail at the door, and must not stay when it does:

      ```python
      try:
          Sentry(guard)
      except (TagPostconditionError, TagImprintError):
          if guard in Sentry[:]:          # it landed, then failed: take it back
              del Sentry[guard]
          raise
      try:
          guard.Patrol()
      finally:
          del Sentry[guard]
      ```

      Check before the `del`. A Shape that fails through its Base's
      Imprint never lands, so `del Dire[bo]` would raise "Dire is not
      active on this Agent" and hide the real failure. The Base stays
      either way (rule 5).
4. **A failure on the way out is never silent.** A Rip in a `finally`
   that fails raises, as every Rip does (§3.1). If the block was raising
   too, Python keeps the block's error inside the new one, as its
   context, and prints both. TOP adds nothing to this.
5. **What the program now decides, that `Scope` decided for it:**

   | Case | `Scope` did | Now |
   | --- | --- | --- |
   | The Agent already carries the Tag | left it | form 2, or the program Rips it anyway |
   | The Tag fails at the door (a Postcondition or an Imprint) | `main`: Ripped it after a Postcondition, left it after an Imprint (it caught only `TagPostconditionError`, `TopKit/lifecycle.py:193`); `step-19-sound-in`: Ripped it after either. The block did not run | the tagging raises before `try`; the block does not run; the Tag stays on the Agent (§0.6), and the Agent is defective if a Postcondition failed; form 4 takes it back |
   | A Shape pulled in its Base | left the Base (open in STEP-SPEC-6, on `step-19-sound-in`) | the Base stays; `del Wolf[bo]` takes it away |
   | A Rip cannot be made on the way out | `main`: dropped it in silence; `step-19-sound-in`: reported it once every Rip was done, as a note on the block's own error when the block raised | raised (rule 4). If the block was raising too, the Rip's failure now leaves, and the block's error is only its context: a caller's `except LookupError:` for the block's error no longer catches it |
   | The block Ripped the Tag itself | `main`: tried to Rip it again, and dropped the failure in silence; `step-19-sound-in`: left it | the `del` in `finally` finds no member and raises a Resolution Failure. A block that may Rip the Tag itself checks first, in the `finally`: `if guard in Sentry[:]: del Sentry[guard]` |
   | The block Ripped the Tag, then applied it again | `main`: Ripped the block's new one; `step-19-sound-in`: left it, as the block's | the `del` in `finally` Rips the block's new one, with no error, and its teardown runs a second time |

6. **TOP gives `with` no meaning.** No TOP object can follow `with`. A
   later STEP may give `with` a meaning (the Director: "for a possible
   future use"). STEP-SPEC-15 (Trials), still Brief, proposes `with
   Try(agent):`. If the Director keeps Trials, they need another
   spelling, or that later STEP.
7. **The kit.** Recommended: the same path as STEP-SPEC-30. In the next
   release `Scope` still works, and issues a `DeprecationWarning` that
   shows the pattern of rule 3. Python shows that warning by default only
   for a call in the main script, or under a test runner (`unittest`
   turns it on). The release after removes `TopKit.Scope` and its
   export. Open question 1 offers removal at once, or a warning Python
   always shows.

## Rationale

**One line, one step.** `with Scope(guard, Sentry):` did four things on
one line. It checked whether the guard was a Sentry. It applied the Tag.
It promised a Rip at the end. And it decided what to do if that Rip
failed. The pattern spends a line on each step, so a reader sees every
one.

**The language's own guarantee.** `try`/`finally` is how Python promises
that something happens at the end of a block. Every Python programmer
knows it from files and locks. A TOP program that uses it needs no TOP
rule to read it.

**Fewer rules in TOP.** `Scope` needed its own rules: §0.7's rule, a
tier in §3.2, six amendment rows in STEP-SPEC-6 on `step-19-sound-in`,
and the oracle's `Exercise_Scope`. The pattern needs none: it is a
tagging and a Rip, which TOP already defines.

**The cost, honestly.**
- The pattern is longer: five lines instead of two, more with several
  Tags.
- It can be written wrong. The tagging inside the `try` buries a refusal
  (check 7). Nested `try`s for several Tags bury a door failure of an
  inner Tag (check 8). Forms 3 and 4 and the rule "tag before `try`, Rip
  in `finally`" are the answer. Python asks the same discipline for a
  lock.
- When both the block and a Rip fail, the caller now gets the Rip's
  failure, not the block's own error (rule 5). That is Python's rule for
  every `finally`.

## Backwards compatibility

1. If the Director chooses the warning (rule 7), programs that use
   `Scope` keep working for one release, with a warning that shows the
   pattern. After that, `from TopKit import Scope` is an `ImportError`.
2. **Files to change on `main`:**
   - `TopKit/lifecycle.py`: `Scope` (lines 166-208), the imports only it
     uses (lines 10, 12, 18 and 19), and the module docstring (line 1);
   - `TopKit/__init__.py`: lines 33 and 65;
   - `TopKit/GUIDE.md`: the import list (line 32), Pattern 9 "Roles that
     end" (lines 641-668 and 707), and the Do/Don't table (line 1009,
     "guarantee it with `Scope`");
   - `TopKit/IMPLEMENTATION_NOTES.md`: lines 21 and 238-240;
   - `spec/SPECIFICATION.md`: as in rules 1 and 2;
   - `tests/test_topkit.py`: the ring line (line 6), the import (line
     40), two `ExitProtocolTests` (lines 2465-2483), and `ScopeTests`
     (lines 2517-2565);
   - `tests/spec_examples.py`: the "# 3.2 scope" example (lines
     187-193);
   - `tests/oracle_topkit.py`: `Exercise_Scope` (lines 660-711), its
     call (line 619), the import (line 50) and the docstring (line 6);
   - `tests/differential_fuzz.py`: `Scoping` (lines 1299-1340), its row
     in `STEPS` (line 1847), the import (line 108) and the docstring
     (line 8).

   `CHANGELOG.md` does not change: it keeps its history.
3. **On `step-19-sound-in`**, `Scope` grew. Its sites there:
   - `TopKit/lifecycle.py`: `Scope` and its four helpers, `_rip_all`,
     `_report`, `_carries` and `_application` (lines 545-696), which
     nothing else uses; the imports only they use (for example
     `contextmanager`, line 14, and `TagError`, line 25); and the module
     docstring (line 1);
   - `TopKit/__init__.py`: lines 34 and 66;
   - `TopKit/GUIDE.md`: the import list (line 32); Pattern 9, its parts
     about `Scope` (lines 689-693, 700-710 and 750-773, and the sentence
     "`Scope` is the guaranteed path." on line 812) and its "`__enter__`
     and `__exit__`" (lines 697-698); and line 1142;
   - `spec/SPECIFICATION.md`: lines 29, 304, 1265-1266, 1296, 1340,
     1346, 1464-1498 and 1619-1621;
   - `CONFORMANCE.md`, line 17;
   - `TopKit/IMPLEMENTATION_NOTES.md`, lines 21 and 389-413;
   - `tests/test_topkit.py`: the ring line (6), the import (43), one test
     (lines 2097-2105), two `ExitProtocolTests` (lines 3291-3309), and
     `ScopeTests` (lines 3381-3743);
   - `tests/spec_examples.py`: the "# 3.2 scope" example (lines
     207-220);
   - `tests/oracle_topkit.py`: `Exercise_Scope` (lines 702-824), its
     call (lines 654-655), the import (line 51) and the docstring (line
     7);
   - `tests/differential_fuzz.py`: lines 8, 29-35 and 152, `Scoping`
     (lines 1521-1569), and its row in `STEPS` (line 2131).

   STEP-SPEC-6's amendment there is about `Scope` in all seven rows. Its
   rulings end with `Scope`, and its text stays as the record (item 4).
   The Director's ruling on a failed teardown (the Rip is refused and
   rolled back) still holds for every Rip, through STEP-SPEC-18
   amendment D. The amendment's draft that the block's own error leaves,
   with a failed Rip as a note (rows 4 and 5), is reversed: now the
   failed Rip leaves, and the block's error is its context (rule 5). The
   Specification there drops "a Scope's exit" from line 1296, so the list
   reads `del Tag[agent]`. STEP-SPEC-18's own text stays (item 4).
4. **Other STEPs.** The Brief STEPs of PR #26 are updated with this one:
   STEP-SPEC-22 (rule 4.5 and section 9), STEP-SPEC-24 (its Rationale),
   STEP-SPEC-26 (the title of section 8, rule 8.2, Backwards
   compatibility 3, Implementation plan 6 and Acceptance) and
   STEP-SPEC-28 (rule 3, and its Backwards compatibility 2). Older STEPs
   keep their text as the record of their day: STEP-SPEC-6 and
   STEP-SPEC-18, and STEP-SPEC-19 on `step-19-sound-in`. This STEP
   supersedes them where they speak of `Scope`. STEP-SPEC-15 is still
   Brief: rule 6 applies to its `with Try(agent):`. In STEP-SPEC-1 and
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

1. **Where to build it.** `Scope` is named on about 45 lines in 10 files
   on `main`, and on about 120 lines in 11 files on `step-19-sound-in`.
   Removing it on `main` first would make many of those a merge
   conflict. Recommended: retire it on the branch that merges last, or
   after `step-19-sound-in` merges.
2. **The oracle and the fuzz.** `Scoping` (the fuzz) runs a teardown
   that fails while the block raises. Rewrite it to the pattern, with
   its keyword inputs on each tagging line (`Sentry(guard,
   rank="knight")`). `Exercise_Scope` (the oracle) models the choices
   `Scope` made. Those choices leave the kit, so that part of the model
   goes. Rewrite the rest to form 3, to keep two paths the oracle takes
   nowhere else: a Rip made while the block's error is on its way out,
   and a Tag that fails at the door before an outer `try`.
3. **The warning release**, if chosen (rule 7): `Scope` keeps its body
   and warns once per call site.

## Open questions for the Director

1. **Warn first, or remove at once?** This is STEP-SPEC-30's open
   question 1 again. Recommended: answer both the same way, with one
   release of `DeprecationWarning`. A program's own tests then show the
   pattern, instead of an `ImportError`. If the warning should show
   everywhere, Python's `FutureWarning` is always shown.
2. **How far does "no function calls as methodology" reach?** TOP has
   other functions. Recommended line: **TOP spells each act and each
   read the way Python spells its own.** Where Python has syntax (a
   call, `in`, `del`, `try` and `finally`), TOP uses it. Where Python
   itself uses a function (`len()`, `isinstance()`,
   `atexit.register()`), a TOP function is fine. Under that line:

   | Function | What it is | Today's language spelling |
   | --- | --- | --- |
   | `Apply(ari, Wizard, Sworn)` | an act: apply several Tags | one line each, `Wizard(ari)`, `Sworn(ari)`. The closest relative of `Scope`; a candidate to retire. |
   | `Contract.Delete(ari, "Alive")` | an act: end one promise | none yet. STEP-SPEC-27 proposes `del` for Reports, and could look at promises too. |
   | `At_Exit(ari)` | a request for later: it changes nothing now | none. Python's own `atexit.register()` is a function, so a function here follows the language. |
   | `Tags(ari)`, `Outline(ari)`, `Form(Wizard)` | reads | as text only, and only on a tagged Agent whose class has no formatting of its own: `f"{ari:tags}"`, `f"{ari:outline}"`, `f"{Wizard:form}"`. On an untagged object, `f"{x:tags}"` is a `TypeError`, and `Tags(x)` is `()`. |
   | `Keyword(x, "Undead")` | a read | `"Undead" in x`, one word at a time, and only on a tagged Agent whose class has no `in` of its own (§1.8). On an untagged object it is a `TypeError`. `Keyword(x, ...)` works on any object, with several words. |
   | `Contract.Status`, `Holds`, `Display` | reads | `bool(ari)`, `f"{ari:contract}"`. |
   | `Contract.Preconditions(ari)`, `Contract.Postconditions(ari)`, `Contract.Conditions(ari)` | reads: check now, and raise the failure by name | none. |

   The marks (`@Pre`, `@Post`, `@Flag("Wolf")`, `@Pin`, `@Record` and
   the rest) are calls written in Python's own decorator syntax. They
   stay. Each function the Director wants changed gets its own STEP.

## Acceptance requirements

- The files of Backwards compatibility 2 (or 3, on the branch where it
  is built) no longer offer `Scope`, or offer it only with the warning
  of rule 7.
- The Guide's Pattern 9 teaches forms 1 and 2 of rule 3, with the rule
  "tag before `try`, Rip in `finally`", and is run by
  `tests/test_documents.py`.
- `tests/test_topkit.py`: the `ScopeTests` are rewritten to the pattern,
  covering the cases of rule 5 and forms 3 and 4; one test checks the
  warning, if chosen.
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
