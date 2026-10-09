# STEP-SPEC-24: Field Rip and the End of a Tag

- **STEP:** SPEC-24
- **Desk:** spec
- **Title:** Field Rip and the End of a Tag
- **Author:** Julio Toboso (@JulTob)
- **Status:** Brief
- **Created:** 2026-10-08. First drafted as STEP-SPEC-21; renumbered
  because 21 is reserved by other open work.
- **Revised:** 2026-10-08, after the Director's decisions on order (join
  order), on Shapes (STEP-SPEC-26: a Shape keeps no Base hostage) and on
  the stop (STEP-SPEC-27: revoke everyone, then the teardowns).

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

`del Wizard[:]` Rips every member of a Tag's Field, and every member's
teardowns run: the whole Agency closes at once. Everyone leaves first;
then the teardowns run, in join order. STEP-SPEC-27 reads the same act
as the deletion protocol of a Tag: gain control, stop gently, and the
Tag stays ready to tag again.

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
  del Sentry[sentry]`. It is not one act. If one Rip fails or is refused
  (on TopKit 0.2.0a4, a member that still holds a Shape), the loop stops
  halfway, and half the Field has left.
- **`del Sentry[:]` is an error today.** It reads the slice as an Agent:
  "Sentry is not active on this Agent". So the spelling is free.

Links (STEP-SPEC-22) need this. When an Agent is deleted, the Links it
holds end, and each Link's Field is Ripped like any Tag's, with the
Link's teardowns run for every Contact. Only the moment differs: the
finalizer of the Link's Agent runs that Field Rip, while the
dying Agent is still in hand to fill the first seat (rule 3.1).

## Specification

A new section, **§3.3 The end of a Tag**, in Ring 3, and one row in §0.8.

In this STEP, § cites the Specification only. This STEP's own parts are
cited as "section N" or "rule N.M".

### 1. Field Rip

1. **`del Tag[:]` Rips every member of the whole Field**, sound and
   defective. It is the spelling the language uses to empty a list,
   `del items[:]`, and the Field-wide form of `del Tag[agent]`. Every law
   of Rip (§0.7) holds for each member.
2. **Shapes do not hold the Field.** A member that holds a Shape of the
   Tag leaves the Tag and keeps the Shape: it becomes a spin-off
   (STEP-SPEC-26, the model the Director chose: "a shape should not keep
   a base hostage"). Nothing cascades (§0.7): `del Class[:]` Rips no one
   from `Wizard`, a Shape of Class. So nothing at the door refuses a
   Field Rip.
3. **Everyone leaves first, then the teardowns run.** The act has two
   phases, in the order the Director gave for a stop (STEP-SPEC-27):
   "revoke all - rip protocols (teardowns)".
   - First, every member's membership ends and every member leaves the
     Field. No user code runs in this phase.
   - Then each member's teardowns run (§3.1), one member at a time.

   Both phases go in the order the members joined, the order `for` walks
   (the Director: "We'll follow [your] fifo recommendation on deletion").
   So when the first teardown runs, nobody is a member any more: no
   member keeps access while the others are cleaned up. Only a teardown
   that applies the Tag again can make a member (rule 1.5).
4. **Failures are collected.** A teardown that fails does not stop the
   others, nor the next member's. The failures are reported once, as a
   Composition Failure, after the walk (§3.1). At a Tag's end there is no
   caller, and failures stay silent (rule 3.1). Where a member whose
   teardown failed ends up (out of the Field, back in it, or kept in the
   safehouse) is open question 1.
5. **The Field as it was.** The Field Rip revokes the members the Field
   had when it began. A teardown that applies the Tag again, to a member
   or to an Agent for the first time, makes that Agent a member again,
   and it stays a member (§3.1: outside good TOP use, but not
   forbidden).
6. **Every kind of Tag.**
   - On a Pin, `del Rare[:]` un-pins every Tag. A Pin's `@Rip` that
     declares the second seat receives its originals (§1.9).
   - On a Link, `del charlie.Knows[:]` unlinks every Contact
     (STEP-SPEC-22).
   - A Relation has no Field to Rip: `del Social.Knows[:]` is refused
     (STEP-SPEC-22, section 9).
7. **A part of the Field.** `del X[:]` on a population drawn from one
   Tag Rips that Tag from every member of the population, by rules 1.1
   to 1.5. Decided by the Director on 2026-10-09: "del (~Wizard)[:] is
   good to delete all broken wizards. Also filtered groups... I like it a
   lot! very useful."

   ```python
   del (~Wizard)[:]                 # every broken Wizard leaves Wizard
   weak = Wizard[:].level < 3       # the root for the sound members: STEP-SPEC-29
   del weak[:]                      # every Wizard under level 3 leaves
   ```

   - The population is read once, when the act begins (rule 1.5). A
     Filter is not asked again during the walk.
   - Recommended: a population drawn from two Tags, `del (Wizard |
     Fighter)[:]`, is refused, because it does not say which Tag to
     Rip. The program writes one line per Tag. Under STEP-SPEC-28 the
     refusal is a category error.

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
   - `__class__`, or a `super()` with no arguments, in an Action: both
     make the same hidden reference to the class.

   A Tag held this way does not end while any Agent keeps that function,
   as a pending teardown or as a sticky Action or condition, and Agents
   that already left count too. For such a Tag, `del Tag[:]` is the act.
   A published member refers to its Tag weakly; once that Tag has ended,
   using it is a Rogue Access Failure (§1.5).

### 3. The end of a Tag

1. **When a Tag ceases to exist, its Field is Ripped**, as by `del Tag[:]`
   (rules 1.1, 1.3, 1.5 and 1.6), with one difference. As at an Agent's
   deletion (§3.2), teardowns at a Tag's end are best effort and silent:
   no failure is raised (open question 1 asks whether a member whose
   teardown failed is kept in the safehouse instead). The
   teardowns of every member still alive at that collection run, then the
   Tag is gone. A member collected in the same pass as its Tag has
   already left the Field, and leaves with no teardown, best effort as at
   any deletion (§3.2).

   A Link's Field is Ripped the same way, at a different moment: by the
   finalizer of the Link's Agent, while that Agent can still fill
   the first seat, and never by the Link's own end. A Contact that
   finalizer never reached ends silently when the Link ends, with no
   teardown (STEP-SPEC-22, rules 8.3 and 8.7).
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
   Field of any of its Bases, the most specific Shape first. That is how
   a program would Deform them by hand (§0.4), and it keeps one order
   whatever the collector does.

   This is not a cascade (§0.7): every Shape of an ending Base is ending
   too. By then the language has cleared every weak reference to these
   Tags, so the kit keeps each Field's teardowns where it can run them
   without the Tag.
5. **A pinned Tag that ends** first has its own Field Ripped, before it
   leaves its Pins. Then it leaves its Pins, as an Agent's deletion Rips
   it from its Tags (§3.2), and the Pins' teardowns run.
6. **Which Tags end in practice.**
   - Tags made at run time that none of their own functions names (rule
     2.3): a Tag declared inside a function, and a Tag built from data.
   - Every Link once its Agent is gone and no name holds the
     Link (STEP-SPEC-22, rule 8.3).

   A Tag declared at the top of a module lives until the interpreter
   exits, where rule 3.3 applies. For those Tags, `del Tag[:]` is the
   act.

## Rationale

**Two acts, two guarantees.** The Director asked whether a Tag's end, which
nothing can refuse, contradicts a Field Rip, which could then be refused
at the door. With STEP-SPEC-26 the question goes away: a Shape no longer
refuses anything, so neither act is refused. They are still two different
acts, and TOP already has the same pair for Agents (§3.2).

| | Rip demanded: `del Tag[:]` | Deletion happened: the Tag's end |
| --- | --- | --- |
| Who acts | the program, on purpose | the language, when nothing can reach the Tag |
| When | at that line | at the next collection, or never |
| Can it be refused? | not at the door: Shapes stay as spin-offs (rule 1.2) | no: there is no one to refuse to |
| Teardowns | certain, in order, failures reported (rule 1.4) | best effort, Shapes first, failures silent (rules 3.1 and 3.4) |
| For Agents, the same pair | `del Tag[agent]` (§0.7) | the Agent's deletion (§3.2) |

So the safe act is the one the program writes. A program that needs its
teardowns to run (a lock released, a line stopped) says `del Tag[:]`, as
it says `del Tag[agent]` for an Agent, in a `finally` when a block must
end with it (STEP-SPEC-31). It never waits for the language to collect a
Tag.

Neither act contradicts "membership never keeps a Tag alive" (rule 2.1).
Membership does not keep a Base alive; its Shapes do, by inheritance,
because Python cannot take a Base out of a class. A Base therefore never
ends while one of its Shapes is still reachable, and when both end
together, the Shapes go first (rule 3.4).

**`del Tag` is not an act on the Tag.** In Python, `del Wizard` removes the
name `Wizard` from one namespace. It never destroys an object, and the
language calls nothing on the Tag, so TOP cannot see it. The Tag lives on
while anything else reaches it: another name, a Shape, a function that
names it (rule 2.3). If that name was the last reference, the Tag ends
later, at a collection (rule 3.2), by the forced path. That is why the
demanded act is spelt on the Tag, `del Tag[:]`, where the language does
call the Tag.

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

**Revoke first, then clean up.** A Field Rip that stopped halfway would
leave a Field that is neither open nor closed. So the act has nothing that
can stop it once it starts: no refusal at the door (rule 1.2), and
membership ends for everyone before any teardown runs (rule 1.3). It is
the order of safety engineering and of incident response: reach the safe
state first (nobody holds the Tag's access), then do the paperwork (the
teardowns). After that, as in §3.1, failures are collected and never stop
the act.

**Symmetry.** §0.3 already says a Field never keeps an Agent alive. If
membership kept a Tag alive, a Tag with members could never end, and rule
3.1 would never fire. With both directions weak, membership is a bond
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
| A method on the Field, `Wizard[:].clear()` | Populations carry no public names (STEP-SPEC-23, rule 1.4), and Rip is spelt with `del`. |
| The loop by hand | Not one act: a Rip that fails or is refused stops it halfway. |
| A Tag's end with strong history | It never fires while a member lives, so it would only happen to Tags that are already empty. |
| A Tag's end that drops members without teardowns | Rejected by the Director: "it should launch the rip protocols to ensure safety in the program status". |
| A Field Rip that deforms Shapes first, on a live Base (a forced `del Tag[:]`) | Rejected: Rip never cascades (§0.7), because a cascade runs other Tags' teardowns behind the program's back. With STEP-SPEC-26 the Shapes simply stay, as spin-offs. A Tag's end is different (rule 3.4): there the Shapes are ending too. |
| Refuse the whole Field Rip while a member holds a Shape | The first draft of this STEP. Replaced by STEP-SPEC-26: "a shape should not keep a base hostage". |
| Each member leaves and is torn down before the next one leaves | The first draft of this STEP. Replaced by the Director's order for a stop, "revoke all - rip protocols (teardowns)": while one member's teardowns ran, the others still held the Tag's access. |
| `del Tag` as the safe act, and `del Tag[:]` as the forced one | Not possible in Python: `del Tag` removes a name, calls nothing on the Tag, and destroys nothing (Rationale, *`del Tag` is not an act on the Tag*). The safe act is `del Tag[:]`, and the forced one is the Tag's end. |
| Reverse order, last in first out | Set aside by the Director, who chose join order: "We'll follow [your] fifo recommendation on deletion". Members of a Field are peers, not a stack, and join order is the order every other walk uses. |

## Open questions for the Director

1. **A member whose teardown fails: where does it go?** Two lines of
   work disagree, and both carry the Director's words.
   - STEP-SPEC-18, amendment D, on the `step-19-sound-in` line (Vetting,
     2026-10-02): "a failed rip blocks an agent's expulsion". A single Rip
     whose teardown fails is refused and rolled back: the Agent is a
     member again. Rule 1.1 ("every law of Rip holds for each member")
     would carry that into this act.
   - The Director on 2026-10-08: "The safehouse: ends membership first
     and runs teardowns after is the sensible choice. Right... any
     safehouse can be accessed from Tag[...] so it's ok if the tag is
     deleted and no myTag[...] access exists. We don't need to worry
     about safehoused agents (arrested?)".

   The options:
   - **(a) Arrest.** Membership never comes back. A member whose teardown
     failed is kept in the safehouse as a non-member, under the Tag's
     department and under `Tag[...]`, until it is repaired or triaged
     (`del Tag[...]`, the triage of STEP-SPEC-18 amendment F). Simplest
     to teach, and the access is gone. It
     replaces amendment D's rollback for every Rip.
   - **(b) The act decides.** Acts the program demands keep amendment D:
     the failed member is rolled back and stays in the Field, and the
     walk goes on ("leave only the agents that raised errors"). Ends that
     just happen (an Agent's deletion, a Tag's end) arrest.
   - **(c) Today's kit.** The member stays out, half torn down, and only
     the error remains.

   Recommended: (a). A failed cleanup should not hand the Agent its badge
   back. Keeping it in the safehouse answers the worry behind amendment
   D, "deleting to uncertain states can be problematic", without the
   access. STEP-SPEC-27 adds no rule of its own here. Under (a), a
   member kept after a gentle stop can then be triaged with
   `del Human[...]`.

## Acceptance requirements

- `tests/test_topkit.py`: a `FieldRipTests` class, covering:
  - `del Tag[:]` with teardowns in order;
  - every member is revoked before the first teardown runs: a teardown
    sees `len(Tag[:]) == 0`;
  - a member that holds a Shape leaves the Tag and keeps the Shape (no
    refusal, no cascade);
  - failures collected after the walk, with the outcome open question 1
    chooses;
  - a teardown that applies the Tag again, to a member and to a new
    Agent: both stay members;
  - rule 1.7: `del (~Wizard)[:]` and `del weak[:]` Rip
    exactly those members; a population of two Tags is refused;
  - Pins, Links, and the refused Relation.
- `tests/test_topkit.py`: a `TagEndTests` class, covering:
  - a Tag made in a function, unreachable after the function returns,
    ends at the next collection (the test calls `gc.collect()`), and its
    Field is Ripped; before that collection its members are still
    members;
  - Shapes end before their Bases: a Base, a Shape of it, and a Shape of
    that Shape, declared in one function, only the most specific applied,
    all three dropped together. Under each collection order, every
    member's teardowns run for the most specific Shape first, then the
    Shape, then the Base, and nothing is
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
    `reports`, `operations`, `words` (the Flag Tags behind each keyword),
    and the keys of `rips` and `snapshots`, with the origins inside a
    snapshot;
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
