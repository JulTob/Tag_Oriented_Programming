# STEP-SPEC-21: Field Rip, and the End of a Tag

- **STEP:** SPEC-21
- **Desk:** spec
- **Title:** Field Rip, and the end of a Tag
- **Author:** Julio Toboso (@JulTob)
- **Status:** Brief
- **Created:** 2026-10-08

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

`del Wizard[:]` Rips every member of a Tag's Field, and every member's
teardowns run: the whole Agency closes at once. A Tag that ceases to
exist does the same on its way out, so no Agent is left a member of
something that is gone. For a Tag ever to cease to exist while it has
members, membership must hold neither side alive. A Field already never
keeps an Agent alive (§0.3); now an Agent never keeps a Tag alive.

```python
del Sentry[:]                         # every Sentry stands down; each one's @Rip runs

def Drill(squad):
    class Exercise(Tag):              # a Tag made at run time
        @Rip
        def Dismiss(agent):
            agent.on_drill = False
    for soldier in squad:
        Exercise(soldier)
                                      # Drill returns: nobody can name Exercise any more,
                                      # so it ends, and its Field is Ripped: every Dismiss runs
```

## Motivation

The Director: "we should include a field rip operation to default tag
deletion. It is essentially the same thing to leave all orphaned agents
hanging that to eliminate the agency from the point of view of the
agents. Same result means syntactical equivalence, and for that it should
launch the rip protocols to ensure safety in the program status. for all
tags, including links."

Today TOP has no end for a Tag, and no way to close one in a single act.
Both were checked on TopKit 0.2.0a4:

- **A Tag never ends while a member lives.** Every Agent's history holds
  the Tags it carried, so `isinstance(agent, Tag)` can answer. A Tag made
  at run time and dropped by the program stays alive through its
  members, and its members stay in its Field. No teardown runs.
- **Closing a Tag is a loop by hand**: `for a in list(Sentry[:]): del
  Sentry[a]`. It is not atomic. If one member still holds a Shape, the
  loop fails halfway, and half the Field has left.
- **`del Sentry[:]` is an error today.** It reads the slice as an Agent:
  "Sentry is not active on this Agent". So the spelling is free.

Links (STEP-SPEC-19) need this. When an Owner is deleted, its Links end.
A Link's end should be a Tag's end like any other, with the Contacts'
teardowns run, not a special rule.

## Specification

A new section, **§3.3 The end of a Tag**, in Ring 3, and one row in §0.8.

### 1. Field Rip

1. **`del Tag[:]` Rips every member of the whole Field**, sound and
   defective. The spelling is the one the language uses to empty a
   list, `del items[:]`. It is the Field-wide form of `del Tag[agent]`,
   and every law of Rip (§0.7) holds for each member.
2. **Refused before anyone leaves.** If any member still holds an active
   Shape of the Tag, the whole Field Rip is a Composition Failure, and
   the Field is exactly as it was. The message names the members and the
   Shapes. Rip never cascades (§0.7): `del Elf[:]` comes first.
3. **In the Field's order.** Members leave in the order they joined, the
   order `for` walks. For each member, membership ends and the member
   leaves the Field. Then its teardowns run (§3.1).
4. **Failures are collected.** A teardown that fails does not stop the
   others, nor the next member's. The failures are reported once, as a
   Composition Failure, after every member has left (§3.1).
5. **A snapshot.** The Field Rip walks the Field as it was when it began.
   A member that a teardown applies again stays a member (§3.1: outside
   good TOP use, but not forbidden).
6. **Every kind of Tag.** On a Pin, `del Rare[:]` un-pins every Tag, and
   each Pin `@Rip` receives its originals (§1.9). On a Link, `del
   charlie.Knows[:]` unlinks every Contact (STEP-SPEC-19).

### 2. Membership holds neither side alive

1. **An Agent never keeps a Tag alive.** Neither its active Tags nor its
   history, nor anything the kit keeps for it, holds a Tag strongly. This
   is the mirror of §0.3: a Field never keeps an Agent alive.
2. **History stays true for every Tag that can still be named.**
   `isinstance(agent, Tag)` answers as it does today for any Tag the
   program can still reach. A Tag nobody can reach has no question left
   to answer.
3. **What a Tag gave stays** (§0.7). Its Actions and Records remain on its
   Agents after it ends, as after any Rip. They hold its functions and
   values, not the Tag.

### 3. The end of a Tag

1. **When a Tag ceases to exist, its Field is Ripped**, as by `del
   Tag[:]`. Every member's teardowns run, then the Tag is gone.
2. **Best effort, like every finalizer** (§3.2). The language decides
   when an unreachable object ends. Where the end must be certain, the
   program says `del Tag[:]` itself.
3. **Not at interpreter exit.** No Field Rip runs while the interpreter
   is shutting down. At exit, teardowns belong to `At_Exit` (§3.2), and
   this STEP does not change that.
4. **A Base outlives its Shapes.** A Shape holds its Bases, so a Base
   cannot end while a Shape exists, and rule 1.2 never refuses an
   ending.
5. **Which Tags end in practice.** Tags made at run time: a Tag declared
   inside a function, a Tag built from data, and every Link once its
   Owner is gone (STEP-SPEC-19 §8.3). A Tag declared at the top of a
   module lives until the interpreter exits, where rule 3.3 applies. For
   those Tags, `del Tag[:]` is the act.

## Rationale

**Same result, same act.** An Agent left in the Field of a Tag that no
longer exists is a member of nothing. Ending its membership is the only
true state, and running its teardowns is what makes the program's state
safe: the sentry stands down, the lock is released, the counter is
decremented. Ending membership silently, without the teardowns, is the
"orphaned agents hanging" the Director named.

**The language's own spelling.** `del items[:]` empties a list in Python,
and `del Tag[agent]` is already Rip. `del Tag[:]` reads as exactly what
it does.

**Atomic at the door.** A Field Rip that fails halfway leaves a Field
that is neither open nor closed. Checking the Shape refusal for everyone
before anyone leaves keeps the act all or nothing at the door. After
that, as in §3.1, teardowns are collected and never stop the act.

**Symmetry.** §0.3 already says a Field never keeps an Agent alive. If
an Agent kept its Tags alive, a Tag with members could never end, and
rule 3.1 would never fire. With both directions weak, membership is a
relation between two lives, and neither one owns the other.

## Backwards compatibility

1. **A Tag kept alive only by its members now ends.** Before, a Tag made
   at run time and dropped by the program lived on through its members'
   history, and its members stayed in its Field. Now it ends, and its
   teardowns run. Code that recovered such a Tag through `Tags(agent)`
   must keep a name for it instead.
2. **`del Tag[:]` was an error**, and now it Rips the Field.
3. Nothing changes for Tags declared at module level while the program
   runs.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| A function, `Close(Wizard)` | The Director prefers the language's own structures; `del` is Rip's spelling already (§0.8). |
| A method on the Field, `Wizard[:].clear()` | Populations carry no public names (STEP-SPEC-20 §1.3), and Rip is spelt with `del`. |
| The loop by hand | Not atomic: a refused Shape stops it halfway. |
| A Tag's end with strong history | It never fires while a member lives, so it would only happen to Tags that are already empty. |
| A Tag's end that drops members without teardowns | Rejected by the Director: "it should launch the rip protocols to ensure safety in the program status". |
| A Field Rip that deforms Shapes first | Rejected: Rip never cascades (§0.7); the program Rips the Shapes it means to. |
| Reverse order, last in first out | Possible: see Open question 1. |

## Open questions for the Director

1. **Order.** Members leave in join order, the order a reader sees in
   `for`. The alternative is reverse join order, last in first out, as a
   Scope Rips its Tags in reverse, and as a stack is unwound. Join order
   is proposed as the simpler one to read.

## Acceptance requirements

- `tests/test_topkit.py`: a `FieldRipTests` class, covering:
  - `del Tag[:]` with teardowns in order;
  - the atomic Shape refusal;
  - failures collected;
  - the snapshot;
  - Pins and Links.
- `tests/test_topkit.py`: a `TagEndTests` class, covering:
  - a Tag made in a function ends when the function returns, and its
    Field is Ripped;
  - nothing at interpreter exit (a subprocess test);
  - history weak and still true for Tags that can be named;
  - a Base kept by its Shape.
- TopKit holds Tags weakly in an Agent's state, in its history and in
  every cache keyed by Tags (the runtime-type and Overlay caches), and
  the performance budget still holds (`benchmarks/`).
- `tests/oracle_topkit.py`: Field Rips in the random walk, and Tags
  dropped mid-walk.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
