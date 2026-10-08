# STEP-SPEC-24: Field Rip and the End of a Tag

- **STEP:** SPEC-24
- **Desk:** spec
- **Title:** Field Rip and the End of a Tag
- **Author:** Julio Toboso (@JulTob)
- **Status:** Brief
- **Created:** 2026-10-08. First drafted as STEP-SPEC-21; renumbered
  because 21 is reserved by other open work.

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

`del Wizard[:]` Rips every member of a Tag's Field, and every member's
teardowns run: the whole Agency closes at once.

A Tag that ceases to exist does the same on its way out, so no Agent is
left a member of something that is gone. For that to happen while a Tag
still has members, membership must hold neither side alive. A Field
already never keeps an Agent alive (§0.3). Now membership never keeps a
Tag alive either.

```python
del Sentry[:]                         # every Sentry stands down; each one's @Rip runs

def Drill(squad):
    class Exercise(Tag):              # a Tag made at run time
        @Rip
        def Dismiss(agent):
            agent.on_drill = False
    for soldier in squad:
        Exercise(soldier)

# After Drill returns, nothing can name Exercise any more.
# When the language next collects it, it ends:
# its Field is Ripped, and every Dismiss runs.
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
- **Closing a Tag is a loop by hand**: `for sentry in list(Sentry[:]):
  del Sentry[sentry]`. It is not atomic. If one member still holds a
  Shape, the loop fails halfway, and half the Field has left.
- **`del Sentry[:]` is an error today.** It reads the slice as an Agent:
  "Sentry is not active on this Agent". So the spelling is free.

Links (STEP-SPEC-22) need this. When an Agent is deleted, the Links it
holds end. A Link's end should be a Tag's end like any other, with the
Contacts' teardowns run, not a special rule.

## Specification

A new section, **§3.3 The end of a Tag**, in Ring 3, and one row in §0.8.

In this STEP, § cites the Specification only. This STEP's own parts are
cited as "section N" or "rule N.M".

### 1. Field Rip

1. **`del Tag[:]` Rips every member of the whole Field**, sound and
   defective. It is the spelling the language uses to empty a list,
   `del items[:]`, and the Field-wide form of `del Tag[agent]`. Every law
   of Rip (§0.7) holds for each member.
2. **Refused before anyone leaves.** If any member still holds an active
   Shape of the Tag, the whole Field Rip is a Composition Failure, and
   the Field is exactly as it was. The message names the members and the
   Shapes. Rip never cascades (§0.7): `del Wizard[:]` before
   `del Class[:]`, when Wizard is a Shape of Class.
3. **In the Field's order.** Members leave in the order they joined, the
   order `for` walks. For each member, membership ends and the member
   leaves the Field, and then its teardowns run (§3.1).
4. **Failures are collected.** A teardown that fails does not stop the
   others, nor the next member's. The failures are reported once, as a
   Composition Failure, after the walk (§3.1). At a Tag's end there is no
   caller, and failures stay silent (rule 3.1).
5. **A snapshot.** The Field Rip walks the Field as it was when it began,
   and looks at each member again when its turn comes.
   - A member that has already left, because a teardown Ripped it, is
     skipped. Its teardowns ran with that Rip, and a teardown runs at
     most once (§3.2).
   - A member whose Rip is refused when its turn comes, because a
     teardown gave it a Shape of the Tag after the door, stays a member.
     The refusal is collected with the teardown failures (rule 1.4).
   - A member that a teardown applies again, and an Agent that a teardown
     applies for the first time, stay members (§3.1: outside good TOP
     use, but not forbidden).
6. **Every kind of Tag.**
   - On a Pin, `del Rare[:]` un-pins every Tag. A Pin's `@Rip` that
     declares the second seat receives its originals (§1.9).
   - On a Link, `del charlie.Knows[:]` unlinks every Contact
     (STEP-SPEC-22).
   - A Relation has no Field to Rip: `del Social.Knows[:]` is refused
     (STEP-SPEC-22, section 9).

### 2. Membership holds neither side alive

1. **Membership never keeps a Tag alive.**
   - An Agent's active Tags and its history hold a Tag weakly.
   - So does everything else the kit keeps about the Tags an Agent
     carries or carried: where each Action and Record came from, what a
     Rip restores, which teardowns to run, and every cache keyed by Tags.
   - A Tag the Agent holds as a value is held like any value, and stays
     alive while the Agent does. That covers a Record whose value is a
     Tag, and a Link the Agent holds (STEP-SPEC-22, rule 4.1).

   This is the mirror of §0.3: a Field never keeps an Agent alive.
2. **History stays true for every Tag that can still be named.**
   `isinstance(agent, Tag)` answers as it does today, for any Tag the
   program can still reach. A Tag nobody can reach has no question left to
   answer.
3. **What a Tag gave stays** (§0.7). Its Actions, Records and conditions
   remain on its Agents after it ends, as after any Rip. The kit keeps
   its functions and values, never the Tag itself.

   But a function holds what it names, as any Python function does:
   - a teardown or Action that names its own Tag;
   - the guard of §0.7 (`if agent not in Wizard: return True`), written
     in a Tag made at run time;
   - `__class__` in an Action.

   A Tag held this way does not end while any Agent keeps that function,
   as a pending teardown or as a sticky Action or condition, and Agents
   that already left count too. For such a Tag, `del Tag[:]` is the act.
   A published member refers to its Tag weakly; once that Tag has ended,
   using it is a Rogue Access Failure (§1.5).

### 3. The end of a Tag

1. **When a Tag ceases to exist, its Field is Ripped**, as by `del Tag[:]`
   (rules 1.1, 1.3, 1.5 and 1.6), with one difference. As at an Agent's
   deletion (§3.2), teardowns at a Tag's end are best effort and silent:
   no failure is raised, and nothing is refused (rule 3.4). Every
   member's teardowns run, then the Tag is gone.

   A Link is the exception. Its Field is Ripped by the finalizer of the
   Agent who holds it, never by the Link's own end (STEP-SPEC-22, rule
   8.3).
2. **Best effort, like every finalizer** (§3.2). The language decides
   when an unreachable object ends.

   In Python a class always sits in a reference cycle: it is in its own
   `__mro__`. So a Tag never ends the moment its last name goes. It ends
   when the collector next finds it: in CPython, at a cyclic collection
   pass, run automatically or by `gc.collect()`. Until then its members
   are still members, and their teardowns have not run.
   - With automatic collection off (`gc.disable()`), a Tag ends only at
     an explicit `gc.collect()`.
   - A Tag moved to the permanent generation by `gc.freeze()` cannot end
     until `gc.unfreeze()`.

   Where the end must be certain and immediate, the program says
   `del Tag[:]` itself.
3. **Not at interpreter exit.** A Tag that ends while the interpreter
   shuts down Rips nothing: rule 3.1 does not fire there. At exit,
   teardowns run only for Agents registered with `At_Exit` (§3.2), and
   this STEP does not change that. An `At_Exit` Agent still Field-Rips
   the Links it holds in that pass (STEP-SPEC-22, rule 8.3). A
   `del Tag[:]` the program writes runs wherever it is written.
4. **Shapes end before their Bases.** A live Shape holds its Bases, so a
   Base cannot end while one of its Shapes can still be reached.

   But a Base and its Shapes can become unreachable together, and then
   the language does not say which one it ends first. In Python, one
   collection clears every weak reference first, and then runs
   finalizers in no promised order. So the kit sets the order: when Tags
   of one Form end together, each Shape's Field is Ripped before the
   Field of any of its Bases, deepest Shape first. That is how a program
   would Deform them by hand. No Base's teardown runs while a member
   still carries a Shape of it, and rule 1.2 never refuses an ending.

   This is not a cascade (§0.7): every Shape of an ending Base is ending
   too. By then the language has cleared every weak reference to these
   Tags, so the kit keeps each Field's teardowns where it can run them
   without the Tag.
5. **A pinned Tag that ends** first has its own Field Ripped, while it is
   still whole and pinned. Then it leaves its Pins, as an Agent's deletion
   Rips it from its Tags (§3.2), and the Pins' teardowns run.
6. **Which Tags end in practice.**
   - Tags made at run time that none of their own functions names (rule
     2.3): a Tag declared inside a function, and a Tag built from data.
   - Every Link once the Agent who held it is gone and no name holds the
     Link (STEP-SPEC-22, rule 8.3).

   A Tag declared at the top of a module lives until the interpreter
   exits, where rule 3.3 applies. For those Tags, `del Tag[:]` is the
   act.

## Rationale

**Same result, same act.** The Director's argument: from the members'
side, being left in the Field of a Tag that no longer exists and having
the Agency eliminated are the same result, and the same result should be
the same act. So a Tag's end is a Field Rip, teardowns included: the
sentry stands down, the lock is released, the counter goes down. An end
that only dropped the members, without teardowns, would leave the
program's state unsafe.

**The language's own spelling.** `del items[:]` empties a list in Python,
and `del Tag[agent]` is already Rip. `del Tag[:]` reads as exactly what
it does.

**Atomic at the door.** A Field Rip that fails halfway leaves a Field
that is neither open nor closed. Checking the Shape refusal for everyone
before anyone leaves keeps the act all or nothing at the door, for the
Field as it stood. After that, as in §3.1, failures are collected and
never stop the act: a teardown's failure, and a refusal that a teardown
causes for a later member.

**Symmetry.** §0.3 already says a Field never keeps an Agent alive. If
membership kept a Tag alive, a Tag with members could never end, and rule
3.1 would never fire. With both directions weak, membership is a link
between two lives, and neither one owns the other. What an Agent holds by
name, a Record's value or a Link it holds, is not membership, and stays
as strong as any value.

## Backwards compatibility

1. **A Tag kept alive only by its members' history and the kit's records
   now ends** when the language collects it, and its teardowns run then.
   Before, a Tag made at run time and dropped by the program lived on
   through its members' history, and its members stayed in its Field. A
   Tag that one of its own functions names still lives while that
   function does (rule 2.3). Code that recovered a dropped Tag through
   `Tags(agent)` must keep a name for it instead.
2. **`del Tag[:]` was an error**, and now it Rips the Field.
3. Nothing changes for Tags declared at module level while the program
   runs.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| A function, `Close(Wizard)` | The Director prefers the language's own structures; `del` is already Rip's spelling (§0.8). |
| A method on the Field, `Wizard[:].clear()` | Populations carry no public names (STEP-SPEC-23, rule 1.3), and Rip is spelt with `del`. |
| The loop by hand | Not atomic: a refused Shape stops it halfway. |
| A Tag's end with strong history | It never fires while a member lives, so it would only happen to Tags that are already empty. |
| A Tag's end that drops members without teardowns | Rejected by the Director: "it should launch the rip protocols to ensure safety in the program status". |
| A Field Rip that deforms Shapes first, on a live Base | Rejected: Rip never cascades (§0.7). The program Rips the Shapes it means to. A Tag's end is different (rule 3.4): there the Shapes are ending too. |
| Reverse order, last in first out | Possible: see open question 1. |

## Open questions for the Director

1. **Order.** Members leave in join order, the order a reader sees in
   `for`. The alternative is reverse join order, last in first out, as a
   Scope Rips its Tags in reverse and as a stack is unwound. Join order
   is proposed as the simpler one to read.

## Acceptance requirements

- `tests/test_topkit.py`: a `FieldRipTests` class, covering:
  - `del Tag[:]` with teardowns in order;
  - the atomic Shape refusal;
  - failures collected after the walk;
  - the snapshot: a teardown that Rips a later member (skipped), one that
    gives a later member a Shape (that member stays, the refusal is
    collected), and one that applies the Tag to a new Agent (it stays);
  - Pins, Links, and the refused Relation.
- `tests/test_topkit.py`: a `TagEndTests` class, covering:
  - a Tag made in a function, unreachable after the function returns,
    ends at the next collection (the test calls `gc.collect()`), and its
    Field is Ripped; before that collection its members are still
    members;
  - Shapes end before their Bases: a Base, a Shape and a deeper Shape
    declared in one function, only the deepest applied, all three dropped
    together. Under each collection order, every member's teardowns run
    deepest Shape first, then the Shape, then the Base, and nothing is
    reported. The orders to try: one full `gc.collect()`; `gc.collect(0)`
    then `gc.collect()`; the Base aged by an earlier collection;
  - a Tag that ends at interpreter exit Rips nothing, while an `At_Exit`
    Agent's Links are still Field-Ripped (a subprocess test);
  - history is weak, and still true for Tags that can be named;
  - a Tag held as a Record value, and a Link an Agent holds, stay alive
    while that Agent lives;
  - a Tag made at run time whose `@Rip` names it does not end while a
    member lives, and `del Tag[:]` still Rips its Field.
- TopKit holds no Tag strongly from anything it keeps about an Agent's
  membership:
  - in `_State` (state.py): `active`, `ever`, `action_origins`, `records`,
    `reports`, `operations`, and the keys of `rips` and `snapshots`, with
    the origins inside a snapshot;
  - on functions the kit makes: the condition stamp `__topkit_origin__`
    (overlay.py) and the `tag` closed over by the Public Operation adapter
    (overlay.py), which fails closed once its Tag has ended;
  - in every cache keyed by Tags: those caches hold their keys weakly. A
    cache value may hold a Tag's Bases, never the Tag itself (the Form
    cache, geometry.py), and rule 3.4 holds whatever the caches keep.

  It holds strongly what an Agent holds by name: Record values and Links.
  The performance budget still holds (`benchmarks/`).
- `tests/oracle_topkit.py`: Field Rips in the random walk, and Tags
  dropped mid-walk.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
