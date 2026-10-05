# STEP-SPEC-18: Deletion in Layers

- **STEP:** SPEC-18
- **Desk:** spec
- **Title:** Deletion in Layers
- **Author:** Julio Toboso (@JulTob)
- **Status:** Vetting
- **Created:** 2026-09-29

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

An Agent's `__del__` is a member of its Overlay like any Action. The
host's own finalizer is its first Layer. A Tag's `__del__` replaces the
Layers beneath it, or with `@Underlay` extends them, and `@Delete`
removes them. When an Agent is deleted, every `@Rip` teardown still due
runs, while the Agent is still a member of its Tags, then its `__del__`
runs as the Overlay shows it. When nothing is stated, that is the host's
own `__del__`. A teardown and a `__del__` Layer may call the Agent's own
Actions there, and a teardown that fails at deletion, or in the
`At_Exit` pass, is reported as a finalizer's error. Once the
interpreter is finalizing at exit, only the `__del__` Layers run;
teardowns there stay opt-in through `At_Exit`. As amended on 2026-10-02,
a failed teardown blocks the act it belongs to: an explicit Rip is
refused and rolled back; at deletion the Agent is rolled back and kept
in the safehouse, `Tag[...]`, instead of destroyed; and triage,
`del Tag[...]`, is the last resort that lets the kept Agents go.

## Motivation

Found in the performance work (PERFORMANCE-2026-09-24.md, §5.6). Tagging
took behaviour away from the host at its end:

```python
class Door:
    def __del__(self): print("the door's own __del__")

plain = Door()                     # at exit: prints
guarded = Door(); Guard(guarded)   # at exit: prints nothing
```

The kit's finalizer imported its teardown runner at call time. At
interpreter exit that import fails, and the finalizer swallowed the error
and skipped everything after it, the host's own `__del__` included. §0.1
promises that every method the Target had keeps working unless a Tag
deliberately contributes a member of that name. Here no Tag had.

A Tag that did contribute a `__del__` broke deletion in other ways. A
plain `def __del__` replaced the kit's finalizer, so no `@Rip` teardown ran
when the Agent was collected. An `@Underlay def __del__` reached the
host's finalizer but still skipped the teardowns. `@Delete def __del__`
left a gate where the finalizer should be, and nothing ran at all.

The Director: "then it should del in layers, as an overlay. We should be
able to overrun it, but if nothing is stated, just overlay the del with a
call to the underlaying del."

## Specification

1. **`__del__` is a member of the Overlay.** The host's own `__del__` is
   its first Layer, found as the language finds it (in Python: the first
   class that defines it decides, `None` means none, a descriptor is
   bound, and one added after tagging counts). A Tag's `__del__` without
   `@Underlay` replaces the Layers beneath it; with `@Underlay` it
   receives them as a callable and decides when to call them. `@Delete`
   removes them (§1.6). The ordinary rules of §1.2 hold: replacing an
   independent Tag's `__del__` without an Underlay is diagnosed, and the
   Layer is sticky after its Tag is Ripped.
2. **With nothing stated, the host's own `__del__` runs**, exactly as it
   would for the untagged object.
3. **The Layer beneath a `__del__` is always callable.** Where the host
   has no finalizer, or a Tag deleted it, calling it does nothing, so
   `@Underlay def __del__(agent, underlay): ...; underlay()` is safe on
   any host.
4. **Deletion order.** When the Agent is collected, every teardown still
   due runs, best effort (§3.1). Then its `__del__` runs as the Overlay
   shows it, top Layer first. Both run inside the composition door
   (§1.5), so a Tag's teardown and Layer read its own `@Secret` members.
   The teardowns run while the Agent is still a member of its Tags,
   unlike after a Rip: `agent in Tag` answers yes, and a walk of the
   Field (`Tag[:]`, and `for a in Tag` while it is sound) finds it,
   except where the language has already cleared the Field's weak
   references, as Python does for a collected cycle. A later STEP may
   end membership first; it would have to let a Rip inside a finalizer
   skip the refusal that protects a Base a Shape needs, and decide what
   a `__del__` Layer that reads a published member does, since published
   members answer members only. Where the language has cleared the
   Actions' weak references (Python does in a collected cycle, and so
   for a Layer at program end), the Agent's own Actions are tied to it
   again before the teardowns run, so a teardown and a Layer call them
   as anywhere (`agent.Ring()`). Only the Agent's own Actions are tied,
   the ones the kit bound for it: another Agent's Action that the
   program stored under one of its names is not, even when it is the
   same Action of the same Tag. The tie ends with the finalizer: every
   Action it tied, and every Action the Agent holds then (one a
   teardown bound by tagging the Agent again, say), is pointed at the
   gone Agent, so an Action kept past the finalizer (by an object a
   teardown built) meets `ReferenceError` (item 10 names the two it does
   not reach), and the Agent is still freed afterwards.
5. **A `__del__` never stops a teardown.** Replacing the `__del__` Layers
   replaces only them; running the teardowns is a protocol of its own
   (§3.2), so no Tag can skip another Tag's teardown. A teardown that
   fails stops none of the other teardowns; it is reported once they ran
   (item 7), and it blocks the deletion (item 12), so the Layers do not
   run then. A teardown interrupted by the language (a `Ctrl-C`) does
   not skip the Layers when no teardown failed; the interruption is
   reported after them. A Layer that raises then is reported by the kit,
   before the interruption, since raising the interruption would hide
   it. (The teardowns not yet run then do not run: the interrupted Tag's
   were already taken off its list, and the other Tags' are not
   reached.) When a teardown failed before the interruption, the Agent
   is kept, the kit reports that, and the interruption is raised last.
6. **At interpreter exit**, once the interpreter is finalizing (in Python,
   `sys.is_finalizing()`, after the `atexit` functions ran), only the
   `__del__` Layers run. A deletion before that point, such as one made by
   an `atexit` function that runs after the `At_Exit` pass, is an ordinary
   deletion: its teardowns run, and a failed one is reported and keeps the
   Agent (item 12). Teardowns at exit stay opt-in: `At_Exit` runs them
   while the interpreter is still whole and the Agent is still a member (a
   walk finds it there); a teardown that fails in that pass rolls that
   Agent back (item 11) and is reported as at deletion (item 7), before an
   interruption that stops the pass. A Rip, a deletion or a pass whose
   teardowns all succeed runs each of them once, whichever tier reaches it
   first; one where a teardown fails is rolled back, and its teardowns are
   due again.
7. **A `__del__` Layer's own error** is reported the way the language
   reports any finalizer's error (in Python, through
   `sys.unraisablehook`). The kit no longer swallows it. A teardown that
   fails at deletion is reported the same way, once every teardown has
   run, and then the Agent is kept (item 12), which the finalizer reports
   too; one that fails in the `At_Exit` pass is reported once that
   Agent's teardowns in the pass have run (its Layers run later, when it
   is deleted). One report each, on stderr, naming the Agent and the
   teardown (`Exception ignored in teardown Hold of Stubborn, deleting
   Bell`; in the pass, `..., in the At_Exit pass of Bell`). No other
   teardown is stopped by it, nor by a `sys.unraisablehook` that raises:
   its error goes to Python's default hook, as Python does for its own
   reports; where `sys.unraisablehook` is `None` or missing, the default
   hook reports, as it does for Python's own. A teardown that failed on a
   Rip was rolled back with the Rip (item 11), so it is due again at
   deletion.
8. **`@Rip` on `__del__` is a Declaration Failure.** A `__del__` Layer
   already runs at deletion; as a teardown too it would run twice.
9. **The language calls `__del__`, not the program.** In Python the
   finalizer must be found on the runtime type, so `agent.__del__` always
   reads the kit's finalizer, whatever the Layers are, even after
   `@Delete`. Calling it by hand runs the whole deletion, teardowns
   included, on a live Agent the program still holds: end an Agent with
   `del`, a Rip, or `Scope` instead. A teardown that fails there keeps the
   Agent (item 12), and the Composition Failure reaches the caller.
10. **Known limits.** Late in interpreter exit, after the kit's own
    modules are cleared, the Layers still run and still reach the host's
    own `__del__`, and a plain Action call still answers; but a Layer that
    reads a member the kit gates (a `@Secret`, a view or a condition by
    name, a published member, `bool(agent)`, a keyword) or asks for
    membership (`agent in Tag`, a walk of a Field) fails there, and so
    does any Action of an Agent that has `@Secret` members. In a collected
    cycle, an Action taken through a view during the finalizer
    (`Tag[agent].Ring`), or bound there and then replaced by a later
    tagging there, is not pointed at the gone Agent: kept past the
    finalizer, it answers the Agent, which the collection may already have
    cleared, until Python frees it, as before this STEP. Where another
    finalizer of the same collection tagged the Agent again before its own
    ran, some of its Actions may still raise `ReferenceError` there, as
    before. And an Agent that its own teardown or Layer keeps alive in a
    collected cycle (by storing it somewhere) keeps no working Action of
    its own, not even one bound during the finalizer: the untie cannot
    tell it from a freed one. At a plain `del` such an Agent keeps every
    Action, since nothing was tied there.
11. **A failed Rip blocks the expulsion** (amendment D, 2026-10-02). An
    explicit Rip (`del Tag[agent]`, a Scope's exit) whose teardown fails
    is refused and rolled back. The teardowns run as before, after
    membership has ended; when one fails, membership comes back: the Agent
    is a member of the Tag again, in its place in the Field, with its
    Form, Overlay and views as before the Rip, and every change the Rip
    and its teardowns made to its TOP state, to the attributes in its
    `__dict__` and to its keeping in the safehouse (item 12) is undone,
    the way a failed tagging's rollback undoes its changes (§0.6), a Rip
    one of them made included. Then the Composition Failure is raised,
    saying the Rip was refused and rolled back, with the first failed
    teardown's own error as its cause. Every teardown of the Tag is due
    again, so a Rip made again once the cause is repaired runs them all.
    The rollback restores the Agent's TOP state and the attributes in its
    `__dict__`, not the outside world: a file a teardown already deleted
    stays deleted, a value the Agent held and a teardown changed in place
    stays changed (Ring 4), and so does a slot a teardown set, as after a
    failed tagging. A Shape's Rip that fails leaves its Base alone:
    nothing cascades, as before. A Rip the language interrupts in a
    teardown (a `Ctrl-C`) is rolled back the same way, and the
    interruption leaves. In the `At_Exit` pass, a teardown that fails
    rolls back what that Agent's teardowns changed on it in the pass, and
    is reported (item 7); the pass goes on for the others. What a teardown
    sees is what it saw before this amendment: on a Rip it runs once
    membership has ended, and membership comes back only if one fails.
    Nothing had to change for the rollback to be clean.
12. **A failed teardown blocks the deletion: the safehouse** (amendment
    E, 2026-10-02). At deletion (the last reference gone, or the
    collector), when a teardown fails, the finalizer keeps the Agent
    alive instead of letting it be destroyed: it reports each failed
    teardown (item 7), rolls the Agent back as item 11 does (still a
    member of its Tags, its state as before the deletion's teardowns),
    and puts it in the **safehouse**, a set of kept Agents the kit holds
    strongly. The safehouse joins TOP's spy words (Mission, Secret, Plot,
    Asset). Then it raises the Composition Failure, saying the teardown
    failed at the deletion of that Agent and that the Agent was kept,
    with the teardown's own error as its cause (`teardown failed at the
    deletion of Page: Clear of Cached; Page was kept, still a member of
    its Tags, in the safehouse, Cached[...]`); Python reports it as a
    finalizer's error, through `sys.unraisablehook`. The `__del__` Layers
    do not run: the Agent is not destroyed. The Agent's Actions stay tied
    to it, in a collected cycle too, so they answer the live Agent.

    The safehouse is organized by department. A kept Agent is kept by the
    Tag or Tags whose teardown failed. `Cached[...]` is the population of
    the Agents kept by Cached or by any Tag in the whole tree of Shapes
    over Cached (its Shapes, theirs, at any depth), and the root's,
    `Tag[...]`, is every Agent in the safehouse, since every Tag lies
    under the root. Listing and triage (item 13) read this same tree. It
    is a population like the others: walked, counted, asked with `in` and
    for truth, and combined with `|`, `&` and `-`. A kept Agent stays a
    member of its Tags as usual, and is in their other populations too.
    In Python `Tag[...]` is a subscript by `Ellipsis`; every other key
    keeps its meaning (`Tag[agent]`, `Tag[:]`).

    An explicit Rip of a Tag that keeps the Agent, once it goes through,
    takes it out of that Tag's keeping; with nothing keeping it, it leaves
    the safehouse, and dropping the last reference then lets it go. A Rip
    whose teardown keeps failing is refused (item 11), and the Agent stays
    kept. Python runs a finalizer once per object, so the finalizer of a
    kept Agent does not run again: when it is let go, neither the
    teardowns of the Tags it still carries nor its `__del__` Layers run. A
    kept Agent is therefore ended with an explicit Rip of each Tag whose
    teardown should run.

    Limits, stated plainly. A finalizer runs once per object. Once the
    interpreter is finalizing (program end), nothing can be kept and no
    teardown runs (item 6); a failure in the `At_Exit` pass is reported
    and rolled back, not kept, and an Agent kept by a deletion an `atexit`
    function made goes when the interpreter clears the kit. A kept Agent
    holds its memory until the program deals with it. An Agent kept from
    a collected cycle keeps what it references alive, the rest of its
    cycle included, whose own finalizers have already run; and Python
    cleared its weak references before the finalizer, so it rejoins each
    Field at the end of the order, a weak reference the program held to
    it stays dead, and an `At_Exit` registration is gone.
13. **Triage** (amendment F, 2026-10-02). `del Tag[...]` (the root: the
    whole safehouse) and `del Cached[...]` (exactly the Agents
    `Cached[...]` lists, kept by Cached or by its Shapes) are the last
    resort. For each Agent, the kit Rips it from every Tag it carries
    without running any teardown again (they already failed; triage gives
    them up), takes it out of the safehouse, and lets go of it, so Python
    frees it, unless the program still holds it elsewhere, in which case
    it lives on as a plain object of its host class, no longer an Agent:
    in no Field, a member of no Tag, with what its Tags left on it and
    its has-been check (`isinstance`), as after any Rip. Each Agent gets
    one `TagTriageWarning` (a named warning beside the others, as
    STEP-SPEC-8 names them), naming the Agent and the teardowns that
    never finished; the warnings come once every Agent is let go, so a
    warning made an error finds the work done. Triage is the author's
    deliberate act: it is never refused (no gate, no rollback) and it
    never raises for a teardown. It is the one way to end an Agent
    without its teardowns. The Director asked for "a full destruction
    button ... to blow up the safehouse and all the kept agent objects
    ... a last resource recovery system. Triage. This for myTag[...]
    too", and chose "End it, then let it go" over "Only let it go". An
    empty safehouse makes `del Tag[...]` do nothing.

```python
class Lantern:
    def __del__(self):
        print("wick out")                  # the first Layer

class Carried(Tag):
    @Rip
    def Put_Down(agent):
        print("put down")                  # a teardown: runs first

class Enchanted(Tag):
    @Underlay
    def __del__(agent, underlay):          # a Layer over the host's own
        print("spell fades")
        underlay()

lamp = Lantern()
Carried(lamp)
Enchanted(lamp)
del lamp          # put down / spell fades / wick out

class Cached(Tag):
    @Rip
    def Clear(agent):
        agent.cache.clear()          # a cache that cannot clear raises here

page = Page()
Cached(page)
del page          # Clear fails: reported, and the page is kept
kept, = Cached[...]
assert kept in Cached and kept in Tag[...]
del kept
del Cached[...]   # triage: let go, with one TagTriageWarning
```

## Rationale

**One rule, not a special case.** Actions already compose in Layers: the
latest contribution is visible, `@Underlay` reaches the one beneath, and
`@Delete` frees the name. `__del__` is a method like any other, so it
follows the same rule. The one thing it cannot be is the kit's own entry
point, because Python calls a type's `__del__` directly. So the finalizer
stays on the runtime type and serves the Agent's `__del__` Layers after
the teardowns.

**Teardowns are not a Layer.** The teardowns belong to the Tags; the
`__del__` belongs to the object. Letting a `__del__` skip teardowns would
let one Tag break another's clean-up, which §3.1 rules out ("every one of
them").

**Why nothing at exit but the Layers.** An untagged object's `__del__`
runs at exit, so the tagged one's must too (§0.1). Teardowns at exit
would run while the interpreter is half shut down, where a teardown that
uses other modules can fail, and its report would come from a half-shut
interpreter; and many programs would print new output at exit. `At_Exit`
already offers them, at a safer moment.

**A failed teardown blocks its act** (amendments D, E, F). A teardown is
the Tag's clean-up; one that fails leaves the Agent half cleaned up. The
tagging sequence already answers that for the way in (§0.6): a call that
fails is rolled back, and the Agent is as it was. A Rip is the way out,
so it answers the same, with the same machinery. A deletion cannot be
refused to a caller, since the language calls the finalizer, so the
Agent is kept where the program can find it, by the Tags that failed,
and the failure is raised where the language reports it. Triage exists
because some failures cannot be repaired: the program must be able to
give the teardowns up, deliberately and visibly, and let the memory go.

## Backwards compatibility

- A tagged object's own `__del__` now runs at interpreter exit, as it
  does untagged. (Before, it ran only when a Tag's `@Underlay __del__`
  sat over it on the runtime type.)
- A Tag's `__del__` no longer stops the teardowns.
- `@Delete def __del__` no longer stops the teardowns.
- An error raised by a host's `__del__` is now reported (on stderr,
  through `sys.unraisablehook`) instead of being swallowed. A Tag's
  `__del__` errors were already reported, and still are.
- Programs whose teardowns already failed at deletion (a `del`, a
  collection) or in the `At_Exit` pass now see each failure on stderr,
  through `sys.unraisablehook`, naming the Agent and the teardown.
  Before, the failure was dropped. (Teardowns are skipped only once
  the interpreter is finalizing; a deletion before that, even one made
  by an `atexit` function that runs after the pass, is an ordinary one,
  and reports.)
- Amendment D: a Rip whose teardown fails (`del Tag[agent]`, a Scope's
  exit) no longer removes the Tag. It is refused and rolled back, and
  the Composition Failure says so; before, the membership ended and
  whatever the teardowns had changed stayed changed. The teardowns are
  due again, so a program that caught the failure and went on now finds
  the Agent still a member, and its next Rip runs them all again. A Rip
  interrupted in a teardown is rolled back too; before, the membership
  had ended. A failure in the `At_Exit` pass rolls that Agent back.
- Amendment E: an Agent whose teardown fails at deletion is no longer
  destroyed. It is rolled back and kept in the safehouse, its
  `__del__` Layers do not run, and the finalizer raises the Composition
  Failure, a second report after the teardown's own. Before, it was
  freed, with its Layers run and the failure dropped (0.2.0a4). Memory a
  program expected back stays held until it Rips or triages the Agent.
  `Tag[...]` answered `TagResolutionError` (a view of `...`); it is now
  the safehouse.
- Amendment F: `del Tag[...]` raised `TagResolutionError`; it is now
  triage. `TagTriageWarning` is new.
- Fixed with amendment D: an Agent whose Rip failed is freed with its
  last reference. Before, the failed teardown's error held the frame
  that held the list of failures, a cycle that kept the Agent until the
  next collection.
- A `__del__` Layer that raises after a teardown was interrupted is now
  reported, before the interruption. Before, only the interruption was,
  carrying the Layer's error as its context.
- A teardown interrupted at deletion (a `Ctrl-C`) no longer keeps the
  Agent until the next collection: the interruption's traceback held
  the finalizer's frame. The Agent is freed at once, and leaves its
  Fields, unless a teardown failed too (amendment E keeps it then).
- A teardown or a `__del__` Layer that calls one of the Agent's own
  Actions no longer raises `ReferenceError` when the Agent was collected
  in a cycle, and neither does a `__del__` Layer when the Agent is
  cleared at program end. Every tagged object still held at program
  end by a module that defines a function (a Tag's Actions, a method,
  any `def`) is in such a cycle, because that function's `__globals__`
  is the module's namespace; so a Layer that called an Action there
  failed at every program end. An Action kept past the finalizer (by an
  object a teardown built) meets `ReferenceError`; before, one a
  teardown bound by tagging the Agent again answered the Agent after
  the collection had cleared it, or failed inside the kit (item 10
  names what is still not reached).
- Teardowns of Agents collected as cyclic garbage during interpreter exit
  no longer run (before, they ran when that collection came while the
  kit's modules were still loaded); `At_Exit` runs them, while the
  interpreter is whole.
- `@Rip def __del__` is refused; `agent.__del__` reads the kit's
  finalizer where it used to read a Tag's Layer or, after `@Delete`, raise
  `AttributeError`.
- Agents whose only difference is their `__del__` Layers, deleted ones
  included, now share a runtime type.
- A host class that subclasses `Tagged` but cannot be subclassed itself
  (an `Enum`, a class whose `__init_subclass__` refuses) is now refused at
  its first tagging, as any such host already was; before, it was tagged
  in place and kept its own class.
- Fixed with it: an object built from an Agent's runtime type
  (`dataclasses.replace`, `type(self)(...)`) is tagged as a plain host,
  and one that is never tagged runs its own `__del__`; a
  host class that subclasses `Tagged` gets its runtime type at the first
  tagging, and with it the finalizer (and views by name and format specs,
  which it also lacked until a Tag brought a type-level fact); the
  finalizer works late in interpreter exit, after the kit's modules are
  cleared.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Run the host's own `__del__` at exit and change nothing else | Set aside by the Director in favour of Layers: a Tag must be able to overrun the finalizer |
| `__del__` Layers first, then the teardowns | Rejected by the Director: the teardowns run first, as the kit already did for the host's finalizer |
| A replacing `__del__` owns the whole deletion, teardowns included | Rejected by the Director: one Tag could break another's clean-up |
| Teardowns also at interpreter exit, best effort | Rejected by the Director: they stay opt-in through `At_Exit` |
| An `@Underlay` with nothing beneath is an error, as for other Actions | Set aside: every object can be finalized, so "nothing" is a valid Layer beneath a finalizer |
| At deletion, end membership before the teardowns, as a Rip does | Deferred by the Director ("Fix the words now, STEP later"): a Rip inside a finalizer would have to skip the refusal that protects a Base a Shape needs, and a `__del__` Layer that reads a published member would fail; a later STEP may take it |
| Leave a teardown that fails at deletion or in the `At_Exit` pass unreported, as §3.2 said | Rejected by the Director ("Print them") |
| Leave the Agent's Actions unanswered in a collected cycle, a known limit | Rejected by the Director ("Fix it now"); the re-tie is weak and ends with the finalizer, so nothing is resurrected |
| A Rip whose teardown fails ends the membership and reports, as before | Replaced by the Director's ruling of 2026-10-02, "Refuse and roll back" (amendment D) |
| At deletion, let the Agent go and only report the failure, as ruling (C) first had it | Replaced by the Director's ruling of 2026-10-02 (amendment E): "deletion should be blocked" |
| At a blocked deletion, run the `__del__` Layers all the same | Set aside in this draft: the Agent is not destroyed, and the host's own finalizer would leave a kept Agent half finalized; Python will not run them later, so a kept Agent ends without them. For the Director's confirmation |
| Spell the safehouse `+Tag` or `-Tag` | Set aside by the Director, who chose `Tag[...]`, "similar" to `Tag[:]` |
| Triage that only lets go, leaving the Agents tagged | Set aside by the Director, who chose "End it, then let it go" (amendment F) |
| Leave a kept Agent's department to the Tag that failed alone, so `Cached[...]` lists only Cached's | Set aside by the Director: "also standard Catched[...] should list the subtags tree and overlays. Departments are part of the agency. A branch has subranches." |

## Acceptance requirements

Covered by `tests/test_topkit.py::LayeredDeletionTests`, including real
interpreter exits in a subprocess (one of them late, after the kit's
modules are cleared), and by the existing `ExitProtocolTests`. Two
rounds of adversarial verification (kernel edge cases, a differential
fuzz against `main`, a docs-and-tests lens, then the fixed code and a
mutation lens) found eleven defects in the first draft and seven in the
fixes; each is fixed here and pinned by a test, and every mutation that
undid a fix now fails a test. The amendment below adds its own tests to
the same class: the Agent's Actions answer a teardown and a Layer in a
collected cycle, at a plain `del`, at program end and in the `At_Exit`
pass, and the Agent is freed afterwards; an Action kept past the
finalizer meets `ReferenceError`; a failed teardown is reported once
every teardown ran, naming the Agent and the teardown, once each, in the
`At_Exit` pass too, and before an interruption, at deletion and in the
pass; one that ran on a Rip has nothing left to report at deletion; and
membership is visible inside a teardown at deletion, as the words now
say. Each test of a fix fails when its fix is undone. The differential
fuzz against the base (300 seeds, and 100 heavy) found one defect in the
first draft of the reports: a failure's traceback held the frames that
held the Agent, through the list that held the failure, so a reported
teardown resurrected the Agent until the next collection, and a walk of
its Fields still found it; the failures are dropped once reported, and a
test pins the Agent freed at once with the collector off. A review of
the amendment found two more: the re-tie outlived the finalizer, so an
Action kept past it answered an Agent the collection had already cleared
(or, with `@Secret` members, failed inside the kit); and the `At_Exit`
pass dropped a failure gathered before an interruption. Both are fixed
and pinned. A second review found two more: a `sys.unraisablehook` that
raised stopped the `At_Exit` pass (and, at deletion, dropped the
remaining reports and the interruption), and the cycle tests could not
tell a resurrected Agent from a freed one, since Python clears weak
references before the finalizer runs; the hook's error now goes to
Python's default hook, and the tests ask the heap. It also found, from
before this STEP, that an interrupted teardown kept the Agent until the
next collection, through the interruption's traceback; the finalizer now
lets go of it. A third review found six more: an Action a teardown bound
by tagging the Agent again outlived the finalizer, as before this STEP;
a `__del__` Layer's own error was hidden when an interruption followed
it; a `sys.unraisablehook` set to `None` or removed dropped every
report; the re-tie walked every Action at a plain `del`, where none
needs it; two of the second round's protections (a hook that raises an
interruption, a default hook that fails) had no test; and the words said
no teardown runs at program end outside the `At_Exit` pass, though one
an `atexit` function releases after the pass does, and is reported. Each
is fixed, and each but the cost is pinned by a test. It also found that
the fuzzer saw almost nothing of program end on Python 3.12, where
`sys.stdout` is closed and the builtins cleared before the last
finalizers run; the fuzzer now writes the exit events to the file
descriptor and binds what they use, so it judges program end on both
interpreters. Every remaining difference is a report block, or an Action
that answers a teardown or a Layer where it raised `ReferenceError` (or,
late in exit on 3.12, `TypeError`, since the kit's own names were gone).
A fourth review found that the re-tie knew the Agent's own Actions by
their function, so another Agent's binding of the same Action, stored
under its name, was tied to the dying Agent (and, at a plain `del`, made
the finalizer untie the Agent's own); that importing the kit failed
where `sys.unraisablehook` was removed; and that the guards keeping a
plain `del` from untying had no test. Each is fixed and pinned: the kit
now knows its own bindings by identity.

Amendments D, E and F are covered by `RipTests` and `ScopeTests` (a
failed Rip refused and rolled back: one teardown, a later one failing
after earlier ones changed the Agent, `Contract.Delete` before the
failure, a Rip made inside a teardown, a Shape's Rip, an interrupted
Rip, a Scope's exit with and without the block's own exception, a retry
after repair, no cycle left behind), by the oracle (`Stubborn`, whose
teardown fails while the Agent is not ok: the Rip is refused, and the
Agent keeps the Tag, its place in each Field and none of what the
teardown did), by `LayeredDeletionTests` (the `At_Exit` pass rolls that
Agent back and goes on; the reports at deletion, before the Agent is
kept), by `SafehouseTests` (a plain `del` and a collected cycle keep the
Agent, a member, rolled back, reported; the departments and the
population; repair and an explicit Rip free it once dropped; a Rip that
keeps failing stays refused; program end reports only; nothing kept, and
nothing left on the heap, when every teardown succeeds) and by
`TriageTests` (the root, one department with its Shapes at any depth,
and a Shape's own branch; the Agents freed, one still held left
carrying no Tag, one warning each naming the teardowns that
never finished, no teardown run, an empty safehouse, a warning made an
error). The oracle found that a failed Rip left the Agent in a cycle
until the next collection, through the list of failures its teardowns'
errors held; it is freed with its last reference now, and a test pins
it. A review of the three amendments found that a refused Rip did not
give back the keeping that a Rip inside its teardown had ended, so the
Agent could then be freed with a teardown that never finished, without
triage; what a failed teardown gives back now records the Tags that
keep the Agent, and `SafehouseTests` pins it, with a keeping a
teardown made undone too. It also found five protections no test
pinned: the `At_Exit` pass dropping its failures (a cycle until the
next collection), triage ending the Agent's words, the warning's line
and its class, an Agent kept once when its finalizer is called twice by
hand, and a Layer's `SystemExit` reported before an interruption. Each
is pinned now. And it found that the rollback gives back the
attributes in the Agent's `__dict__`, not a slot, as a failed tagging
does; item 11 says so, and a test pins it. The differential fuzzer,
which now looks at the safehouse (walked, counted, asked with `in` and
for truth, combined), Rips what it keeps, once repaired too, and
triages it, was run against the kit before the amendment (300 seeds,
and 100 heavy, on Python 3.14 and 3.12). Every difference is one this
STEP announces: a kit built with none of them reads as the base on
every program, and each differing line is explained by the smallest set
of them that reproduces it.

---

## Amendment, 2026-09-29, and its second round, 2026-10-02

Rulings (A), (B) and (C) were found after the merge, in the review of
the fixes; (D), (E) and (F) came on 2026-10-02, with STEP-SPEC-6's Scope
rule. The Summary, items 4 to 7 and 9 to 13, the Rationale, the
Alternatives, Backwards compatibility and the Acceptance requirements
above carry the amended text. The words said the Agent "leaves its Tags"
at deletion, but the kit runs the teardowns while it is still a member
(in the Tag, and found by a walk unless Python collected it in a cycle),
unlike after a Rip; a teardown or a `__del__` Layer that called one of
the Agent's own Actions raised `ReferenceError` in a collected cycle,
which includes a tagged object still held at program end by a module
that defines a function, because Python clears the Actions' weak
references before the finalizer runs; and a teardown that failed at
deletion, or in the `At_Exit` pass, was dropped.

| Question | The Director's decision |
| --- | --- |
| (A) Membership during deletion: end it first, as after a Rip, or keep the teardowns running while the Agent is still a member, as today and in 0.2.0a3 | "Fix the words now, STEP later": no behaviour change; the STEP, §3.1, §3.2, CONFORMANCE and the Guide say the teardowns at deletion and in the `At_Exit` pass run while the Agent is still a member; a later STEP may end membership first |
| (B) Actions at deletion: a teardown or a `__del__` Layer cannot call the Agent's own Actions where Python cleared their weak references | "Fix it now": the finalizer ties the Actions to the Agent again before the teardowns and the Layers run, with weak references, until the finalizer is done, so `agent.Ring()` works there as anywhere and the Agent is still freed |
| (C) Teardown failures at deletion (`del`, a collection, program end, the `At_Exit` pass): swallowed or printed | "Print them": each failed teardown is reported through `sys.unraisablehook`, naming the Agent and the teardown: at deletion, after every teardown and every Layer has run; in the `At_Exit` pass, once that Agent's teardowns in the pass have run, since its Layers run only when it is deleted; nothing else is stopped; a teardown still runs at most once. Since (E), at deletion the report comes once every teardown ran, and the Layers do not run, since the Agent is kept |
| (D), 2026-10-02. An explicit Rip whose teardown fails: what should happen? | The Director chose "Refuse and roll back", and then said: "I was gonna suggest to just ammend the rule to a failed rip blocks an agent's expulsion". Item 11: the Rip (`del Tag[agent]`, a Scope's exit) is refused and rolled back, and the Composition Failure is raised with the teardown's own error chained; the `At_Exit` pass rolls that Agent back too |
| (E), 2026-10-02. A teardown that fails at deletion: let the Agent be destroyed, or block the deletion | "deletion should be blocked, yeah, and an error raised the good contract thing to do, because deleting to uncertain states can be problematic." Item 12: the finalizer rolls the Agent back, keeps it in the safehouse and raises the Composition Failure. Its spelling: he asked for something "similar" to `Tag[:]` "for unbreakable... Like a safehouse", and chose `Tag[...]` over `+Tag` and `-Tag`. Its departments: "Catched teardown and overlays or subtags. Tag then means from the root of all tags, and catched all the catched agents in safehouses. Doesn't matter the 'department' if the agency is cleaning up all assets." and "also standard Catched[...] should list the subtags tree and overlays. Departments are part of the agency. A branch has subranches." |
| (F), 2026-10-02. A way out of the safehouse when nothing can be repaired | The Director asked for "a full destruction button ... to blow up the safehouse and all the kept agent objects ... a last resource recovery system. Triage. This for myTag[...] too", and chose "End it, then let it go" over "Only let it go". Item 13: `del Tag[...]` and `del Cached[...]` Rip each listed Agent from every Tag without its teardowns, take it out and let it go, with one `TagTriageWarning` each |

Notes on the second round. Ruling (C) holds for a teardown such as a
cache clear: it runs at deletion, and its failure is printed. The
Director confirmed it on 2026-10-02: "It makes sense to me now that a
'clear caché' action would be called at deletion." With (E), that
failure then keeps the Agent. Three readings in items 11 to 13 are this
draft's, for the Director's confirmation: an interrupted Rip is rolled
back like a failed one; a kept Agent's `__del__` Layers do not run, at
the blocked deletion or later; and a successful Rip of one Tag that
keeps an Agent releases it from that Tag's keeping only, so it leaves
the safehouse once every such Tag is Ripped.

Covered by `tests/test_topkit.py::LayeredDeletionTests`, `RipTests`,
`ScopeTests`, `SafehouseTests` and `TriageTests`.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
>
> *Drafted for the Director's confirmation:* Cleared on 2026-09-29, per
> the Director's direction: "then it should del in layers, as an overlay.
> We should be able to overrun it, but if nothing is stated, just overlay
> the del with a call to the underlaying del"; with teardowns first, a
> `__del__` that never stops a teardown, and only the Layers at exit; and
> as amended the same day by the Director's three rulings ("Fix the words
> now, STEP later", "Fix it now", "Print them").
>
> *Added 2026-10-02, drafted for the Director's confirmation:* amended by
> the Director's rulings (D) "Refuse and roll back", (E) "deletion should
> be blocked", with the safehouse spelled `Tag[...]` and organized by
> department, and (F) triage, "End it, then let it go"; with his
> confirmation of (C) for a teardown such as a cache clear.
