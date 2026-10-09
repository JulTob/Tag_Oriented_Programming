# STEP-SPEC-27: Emergency Stop

- **STEP:** SPEC-27
- **Desk:** spec
- **Title:** Emergency Stop
- **Author:** Julio Toboso (@JulTob)
- **Status:** Brief
- **Created:** 2026-10-08

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

A **stop** ends a Tag's whole population under control. Then it keeps
the Tag closed until a deliberate **reset**. This STEP builds a
**category 1** stop, in the Director's order, in four phases:
1. **Latch.** The Tag is closed first. A latch is a switch that stays
   where it was put until someone resets it.
2. **Revoke.** Every membership ends at once. No user code runs.
3. **Teardowns.** Each revoked member's teardowns run, one member at a
   time, in join order (first in, first out).
4. **Report.** Failed teardowns are reported once, after the walk.

Then the latch stays until reset. Reset brings no one back. Which other
categories to offer is open question 2.

```python
from TopKit import Stopped    # a Pin the kit provides (open question 1)

Stopped(Line)                 # category 1: latch, revoke, teardowns, report
assert Line in Stopped[:]     # the latch is on
assert len(Line[:]) == 0      # nobody is a member
Line(new_worker)              # refused: Line is stopped until reset

del Stopped[Line]             # reset: the latch is off, nobody comes back
Line(new_worker)              # works again
```

## Motivation

The Director: "So how do we implement a category 1 (or higher) stop?
revoke all - rip protocols (teardowns) - close. No cascades. a deletion
protocol may execute a deletion of all bases, but that should be
explicit, not magic. same for paralellism."

**The standards behind the words.** Machine safety names three ways to
stop (IEC 60204-1, clause 9.2.2). A higher number is a milder stop:

| Category | IEC 60204-1 | In TOP |
| --- | --- | --- |
| 0 | "stopping by immediate removal of power to the machine actuators" | revoke everyone; give up the teardowns |
| 1 | "a controlled stop with power available to the machine actuators to achieve the stop and then removal of power when the stop is achieved" | revoke everyone; run the teardowns; stay closed |
| 2 | "a controlled stop with power left available to the machine actuators" | latch only; members keep everything |

An **emergency stop** has more rules (IEC 60204-1 and ISO 13850:2015). It
overrides every other function, in every mode. It is category 0 or 1,
never 2. It is latched until someone deliberately resets it. And the
reset "shall not restart the machinery but only permit restarting".

Today TOP has none of this (checked on TopKit 0.2.0a4). No act empties
a Field and keeps it shut. A loop by hand, `for w in list(Line[:]): del
Line[w]`, ran teardowns that saw the Field at sizes 2, 1, 0: the others
still held access. A latch the program writes itself leaks (rule 2.2).

## Specification

A new section, **§3.4 Emergency stop**, in Ring 3. Section 8 gives a row
for §0.8 and a change to the Failure model. Rule 6.4 changes §1.9. Here §
cites the Specification, and "rule N.M" cites this STEP. The examples use
the recommended spelling, a Pin named `Stopped` (open question 1).

**Words used here.**

| Word | Meaning |
| --- | --- |
| **Field**, **sound**, **defective** | The Field is everyone who is a member of a Tag: `Wizard[:]`. Sound: every promise (Postcondition) on the Agent holds. Defective: one does not (§2.5). |
| **Pin** | A Tag that applies to Tags, not to objects (§1.9). `Stopped(Wizard)` pins Wizard. |
| **Gate**, **commit**, **Imprint** | The gate is the Preconditions that check an Agent before it joins. Commit is the step where it enters the Field (§0.6, steps 1 and 3). An Imprint is an Action that runs when it joins (§2.3). |
| **Rip**, **teardown** | A Rip ends one membership, `del Wizard[agent]` (§0.7). Teardowns are the Tag's `@Rip` Actions, run after it (§3.1). A **Field Rip**, `del Wizard[:]`, Rips every member (STEP-SPEC-24). |
| **Rogue Agent**, **spin-off** | A Rogue Agent left a Tag and keeps what the Tag gave it (§0.7). A spin-off holds a Shape but not its Base (STEP-SPEC-26). |
| **Safehouse**, **arrest** | On the `step-19-sound-in` line, the safehouse is the kit's set of **kept** Agents, held so they are not destroyed half torn down (STEP-SPEC-18, amendment E). New here, an arrest is a kept Agent that is not a member (rule 5.2). |
| **Department**, **triage** | `Wizard[...]` lists the kept Agents of Wizard and its Shapes; `Tag[...]` is the whole safehouse. Triage, `del Wizard[...]`, ends them without teardowns (amendment F). |
| **Strong**, **weak** | A strong reference keeps an object alive; a weak one does not. |
| **Cause**, **note** | An exception's `__cause__`, and the lines `add_note` attaches to it. |
| **Composition**, **Declaration Failure** | Named failures of the Failure model, `TagCompositionError` and `TagDeclarationError`. |

### 1. The stop, category 1

1. **`Stopped(Wizard)` stops Wizard at category 1.** It is one act in
   four phases, always in this order: latch, revoke, teardowns, report.
   Then the latch stays.
2. **Latch first.** Wizard becomes a member of the Pin `Stopped` before
   anything else happens. From then on, Wizard gains no member (rule 2.1).
   Nothing can re-enter while the stop works (with rule 2.3).
3. **Revoke everyone.** Every member of the whole Field, `Wizard[:]`,
   sound and defective, loses its membership and leaves the Field. No
   user code runs in this phase: no teardown, no condition, no Imprint.
   **Recommended:** a member already kept in the safehouse is revoked
   too. Its teardowns run again in phase 3. If they pass, it leaves the
   safehouse, as after any Rip that goes through.
4. **Then the teardowns.** Each revoked member's teardowns of Wizard run
   (§3.1: every one, in declaration order), one member at a time, in the
   order the members joined, the order `for` walks. The Director: "We'll
   follow [your] fifo recommendation on deletion". So inside every
   teardown, `Wizard in Stopped[:]` is True and `len(Wizard[:]) == 0`.
   STEP-SPEC-24's Field Rip runs in the same order (its rule 1.3). So a
   stop is a latch plus a Field Rip that never rolls back (rule 5.1).
5. **What a member keeps** is what any Rip leaves (§0.7). Its Actions and
   Records stay: it is a Rogue Agent of Wizard. Published members and the
   view `Wizard[agent]` refuse it. Its other Tags are untouched.
6. **The Tag stays latched** after the walk, until reset (rule 2.3).
   Stopping it again does nothing (§0.5): pressing twice is safe.
7. **A stop checks no promise (recommended).** §1.9 re-checks a Tag's
   Pin promises "at later pinning boundaries". A stop is not one, so it
   never raises for a promise it has nothing to do with.

### 2. The latch and the reset

1. **A stopped Tag gains no member.** These are refused before anything
   changes, with a named failure (section 8):
   - `Wizard(agent)`, and `Scope(agent, Wizard)` at the Scope's door;
   - **recommended (rule 4.3, open question 5):** a Shape whose Form
     contains Wizard, on an Agent that holds neither: `Archmage(agent)`
     would apply Wizard too;
   - a tagging of Wizard made inside a teardown;
   - a new pinning by a stopped Pin, a new linking by a stopped Link;
   - **recommended:** every rollback that would put an Agent back in the
     Field. That Agent is arrested instead (rule 5.2). Two rollbacks
     could do it: amendment D's, when a teardown of `del Wizard[x]` stops
     Wizard and then fails, and a failed tagging's (§0.6). This is
     reasoned from the `step-19-sound-in` code, not run.
2. **The latch belongs to the kit.** The kit checks it before the gate,
   so no Precondition runs and none can lift it. The kit reads plain
   membership, `Wizard in Stopped[:]`, never soundness. A Tag made
   defective by another Pin's broken promise stays latched (STEP-SPEC-19,
   item 4, on the `step-19-sound-in` line). A latch written as a
   Precondition fails, because a Shape's Precondition of the same name
   replaces its Base's (§2.2):

   ```python
   class Guarded(Tag):
       closed = True                     # the program's own "latch"
       @Pre
       def Open(agent):
           return not Guarded.closed
   class Relaxed(Guarded):
       @Pre
       def Open(agent):                  # same name: replaces Guarded's
           return True
   Relaxed(g2)                           # goes through on TopKit 0.2.0a4
   assert g2 in Guarded                  # inside the "closed" Tag
   ```
3. **Reset is the Rip of the Pin: `del Stopped[Wizard]`.** It lifts the
   latch and restores no one. No Agent comes back, no Imprint runs, and
   an arrested Agent stays arrested (rule 5.5). New taggings work again.
   As ISO 13850 asks, a reset only permits a restart. **Recommended:** a
   reset during the stop's walk is refused, with a Composition Failure.
   Otherwise one teardown could reset, and a later one re-enter.
4. **The questions come with the Pin.** `Wizard in Stopped[:]`: is the
   latch on? `for tag in Stopped[:]`: which Tags are stopped?
   `isinstance(Wizard, Stopped)`: was it ever stopped? `f"{Wizard:pins}"`
   shows `Stopped`. Always write `[:]`: the plain walk (TopKit 0.2.0a4)
   and the plain `in` (`step-19-sound-in`) skip a defective Tag.

### 3. Category 0 (recommended), and category 2

1. **Category 0 (recommended): `Stopped(Wizard, category=0)`.** Latch and
   revoke, as in category 1. Then the teardowns are given up: none runs
   for a revoked member, now or later. After the walk, each such member
   gets one warning naming it and the teardowns given up: a warning of
   its own class, like triage's `TagTriageWarning` (STEP-SPEC-18,
   amendment F). Nothing is arrested. Category 0 is for teardowns that
   are the danger themselves.
2. **Category 2 is not offered by this STEP.** A "hold" would only latch.
   IEC 60204-1 does not allow it as an emergency stop. Open question 2.
3. **The category is an input** of the pinning (§0.5), `1` by default. It
   is the integer `0` or `1`. Anything else, `True` and `1.0` included, is
   refused before anything changes (in Python, `True == 1 == 1.0`).

### 4. No cascades

1. **A stop acts on one Tag.** "Rip never cascades" (§0.7). Stopping a
   Base stops no Shape, and stopping a Shape stops no Base. Stopping a
   Pin stops none of the Tags it pins: `Stopped(Rare)` un-pins them and
   latches Rare.
2. **A member that holds a Shape becomes a spin-off.** This rule needs
   STEP-SPEC-26 (Brief, on this branch; the Director chose its model on
   2026-10-08). With it, the member leaves Wizard and keeps the Shape,
   whose teardowns do not run. So a stop is never refused at the door.
   Without it, §0.7 refuses to Rip a Base while a Shape needs it.
3. **Recommended: a stopped Base refuses new taggings of its Shapes.** A
   Shape applies each of its Bases that the Agent lacks (STEP-SPEC-26,
   rule 1.1). This refuses new members only. It changes no member of any
   Shape, so it is not a cascade. Open question 5.
4. **Several Tags are several stops**, one line each, in the order the
   program chooses. The Director: "a deletion protocol may execute a
   deletion of all bases, but that should be explicit, not magic."

   ```python
   Stopped(Human)                  # the Shape first: Human's teardowns run
   Stopped(Mortal)                 # then its Base
   for tag in Combat[:]:           # every Tag that Combat pins, explicitly
       Stopped(tag)
   ```

### 5. A failed teardown: arrest (recommended)

1. **A failed teardown never brings membership back.** A stopped Tag
   cannot take a member back. So this STEP recommends that amendment D,
   the Director's ruling "a failed rip blocks an agent's expulsion", not
   apply inside a stop.
2. **The Agent is arrested.** The kit keeps it in the safehouse as a
   non-member, held strongly, so it is not destroyed half torn down. The
   word is the Director's, with his question mark: "We don't need to
   worry about safehoused agents (arrested?)". This amends amendment E: a
   kept Agent stays a member of its Tags, unless a stop arrested it. It is
   listed under `Wizard[...]`, under the departments of Wizard's Bases,
   and under `Tag[...]`, but not in `Wizard[:]`.
3. **The walk goes on.** A failure stops neither that member's other
   teardowns (§3.1) nor the next member's.
4. **One report, after the walk:** one Composition Failure that names
   every arrested Agent. Its cause is the first failed teardown's error.
   Each other failure is a note (open question 8). The latch stays: after
   commit, a failure "raises, but the Tags stay" (§0.6).
5. **Release.** Triage, `del Wizard[...]` or `del Tag[...]`, lets the
   arrested Agent go. But it also Rips it from every other Tag it carries,
   without their teardowns (amendment F). Open question 6 asks for a
   release that ends the arrest only.
6. **The arrest names its Tag weakly.** On the `step-19-sound-in` line,
   the safehouse holds the keeping Tag strongly. An arrest must not, so
   that a stopped Tag can still end (STEP-SPEC-24, rule 2.1). The
   Director: "any safehouse can be accessed from Tag[...] so it's ok if
   the tag is deleted and no myTag[...] access exists."
7. **This STEP proposes arrest for a stop only.** A latch rules out
   amendment D's rollback, so inside a stop the choice is arrest or
   today's kit (out of the Field, only the error raised). This STEP
   recommends arrest (open question 6). For an ordinary Rip and a Field
   Rip, STEP-SPEC-24's open question 1 chooses. The Director, on
   2026-10-08: "The safehouse: ends membership first and runs teardowns
   after is the sensible choice."

### 6. Nothing refuses a stop

1. **No Precondition, no Pin's gate, no Shape can refuse it.** `Stopped`
   declares no gate. A Shape of `Stopped` is a Declaration Failure: it
   could add a gate that refuses. Other Pins on Wizard gate only their
   own pinnings (§1.9). No member refuses either (rules 1.3 and 4.2).
2. **The kit refuses only what it cannot read:** an unknown category
   (rule 3.3), a target that is not a Tag, and a Relation (rule 6.3). A
   Pin cannot pin itself, so `Stopped(Stopped)` is refused (§1.9).
3. **Recommended: a Link can be stopped; its Relation cannot.**
   `Stopped(charlie.Knows)` stops one Agent's Link. It unlinks every
   Contact, runs the Link's teardowns with `(charlie, contact)`, and
   refuses `charlie.Knows(dana)` until reset. Other Agents' Links are
   other Tags, untouched (rule 4.1). The Relation is refused too.
   Without STEP-SPEC-23, `Social.Knows` is the Relation, which has no
   Field (STEP-SPEC-22, section 9). With it, `Social.Knows` is a
   Projection, not a Tag (rule 6.2). Under STEP-SPEC-28, either refusal
   is a category error.
4. **§1.9 gains one exception.** "A Pin does not alter the pinned Tag's
   own gate over its Agents": `Stopped` does, and only the kit provides
   it. The next sentence, "A Tag that should refuse new members while
   Deprecated writes that as its own Precondition, reading its Pins",
   gains: "A Shape's Precondition of the same name can relax it (§0.6). A
   Tag that must take no new member, and keep none, uses `Stopped`."

### 7. One thread, in order

1. **Never in parallel by default.** The teardowns run in the caller's
   thread, one at a time, in join order (the Rationale says why). A
   program that wants parallel work writes it itself, for example in a
   teardown that hands slow work to its own threads. Open question 9.
2. **A stop from another thread or a signal handler** is out of scope
   (open question 10). A signal handler is a function the language runs
   when the process gets a signal, such as Ctrl-C.

### 8. The new rows

**§0.8 gains a row:**

| Act | Python spelling |
| --- | --- |
| stop a Tag, and reset it (§3.4) | `Stopped(Wizard)`, `Stopped(Wizard, category=0)`, `Wizard in Stopped[:]`, `del Stopped[Wizard]` |

**The Failure model's Composition row grows.** Recommended: the
Composition Failure, with the message "Wizard is stopped: reset with del
Stopped[Wizard]". The row:

| Failure | Meaning | Effect |
| --- | --- | --- |
| **Tag Composition Failure** | Contributions cannot form the Overlay: cross-kind collision, Record over a host descriptor, a Record builder or teardown that failed, a Target that cannot carry state. Also a tagging of a stopped Tag, and a reset during its stop (§3.4). | call rolled back (or Rip refused); for a stopped Tag, refused, nothing changed |

("a Base still required" leaves the row with STEP-SPEC-26.)

**It is not a category error** (STEP-SPEC-28): the Tag is the right kind
of thing, in a closed state. STEP-SPEC-28's rule 4 sends that to the
Resolution Failure, but its examples are look-ups. This is a refused act,
like the "Rip refused" the Composition row already holds. Open question 8.

## Rationale

**Reach a safe state first.** Safety engineering wants the safe state
before anything else, and reliability before speed. Here the safe state
is "nobody holds the Tag's access". The revoke phase reaches it in about
0.6 µs per member (2,000 members in about 1.2 ms, on Python 3.13). It
runs no user code, so no program error can stop it halfway. If a later
teardown failed, or a Ctrl-C landed in one, the safe state would hold.

**Revoke access, then clean up, then hold apart what failed.** Incident
response works in this order. First the badge stops working, for
everyone at once. Then the paperwork runs. A member whose paperwork
fails is held apart: arrested.

**Why a latch, and a reset that restores no one.** Without a latch, a
teardown may apply the Tag again (§3.1). On a prototype with the latch,
every such try was refused. Restoring members at reset would rerun their
Imprints: a restart behind the program's back. Both standards forbid it.

**Why one thread.** Ring 4 lists what TOP does not promise: "One Agent,
one thread. Fields are not synchronized." Teardowns in parallel would
touch Fields and shared state from several threads at once. Nothing in
TOP makes that safe. It gains little too: in CPython's usual build,
threads speed up waiting (files, network), not work. Earlier the
Director asked: "if the case is that we reaaaaally need to delete it
(like a panic button) then I'd go in parallel to prioritize this
processes and make them as fast as possible. It's what a safety protocol
should do to do a full wipe, right?" He then said: "You are right.
Parallel programming should be explicit. Good point."

**Sources** (secondary copies; the standards' own text was not read):
- [Lenze: stop categories (EN 60204)](https://www.lenze.com/en-de/go/akb/200502242/1)
- [Wenglor: stop category](https://wenglor.com/en/Stop-Category/l/cxmCID123755)
- [ABB PLC help, sf_outcontrol (cites IEC 60204-1 9.2.2)](https://help.plc.abb.com/sf_outcontrol.html)
- [ANSI blog: ISO 13850](https://blog.ansi.org/ansi/iso-13850-safety-of-machinery-emergency-stop/)

## Backwards compatibility

Nothing changes for a program that never stops a Tag. On a prototype, a
tagging cost about 14 µs with or without a stopped Tag. `Stopped` is a
new export. §1.9 and amendment E each gain an exception (rules 6.4, 5.2).

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Teardowns in parallel by default | Rejected by the Director: "Parallel programming should be explicit." It steps outside Ring 4 (Fields are not synchronized), and speeds up only waiting. |
| A stop that cascades to Shapes or Bases | Rejected: "No cascades." Several Tags are several stops (rule 4.4). |
| Refuse the stop while a member holds a Shape | The first prototype did this. A stop that can be refused is not an emergency stop. Replaced by STEP-SPEC-26: spin-offs. |
| No latch, or the program's own Precondition as the latch | The Field refills, and a Shape's Precondition of the same name replaces it (rule 2.2). ISO 13850 asks for a latch. |
| Each member revoked and torn down before the next | While one is cleaned up, the others keep access. |

## Open questions for the Director

1. **Spelling.** Recommended: **a Pin the kit provides, `Stopped`**.
   - **The stop state is membership.** It starts, lasts and ends, with a
     population and a history, as §1.9 argues for *Deprecated*. It is
     TOP's own algebra, with no new function.
   - **The order comes free.** Commit comes before write (§0.6): a Pin's
     Imprint already sees the Tag pinned. A reset is a Rip (§0.7).
   - **Costs:** the first Pin the kit provides, and the one Pin that
     changes a gate (rule 6.4). It must refuse Shapes (rule 6.1), and land
     nothing on the Tag, whose namespace is the program's (§0.8).

   The alternatives:
   - **Functions `Stop(Wizard, category=1)` and `Reset(Wizard)`**, like
     `Scope` and `At_Exit` (§3.2). But "is it stopped?" and "which are
     stopped?" need more names, which the Pin gives for free.
   - **`del Wizard[:]` with a category.** Only through a cryptic key such
     as `del Wizard[:, 0]`: `del` takes no keyword arguments.
   - **Make STEP-SPEC-24's Field Rip latch.** An ordinary act (empty the
     Field, carry on) would become a lock that needs a reset.
   - **`del Wizard[...]`.** Already triage on the `step-19-sound-in` line.
2. **Which categories?** You asked for "a category 1 (or higher) stop".
   In IEC 60204-1 the numbers run the other way: category 0 cuts power at
   once, and category 2 keeps it. So "higher" may mean a hold (category
   2) or a harsher stop (category 0). Recommended: category 1 now,
   category 0 as an option (rule 3.1), category 2 not now.
   - **A hold, if wanted later,** would be a Pin of its own, for example
     `Held`. As `Stopped(Wizard, category=2)`, a later `Stopped(Wizard)`
     would do nothing (§0.5): a hold could never become a stop.
   - **Escalation.** For the same reason, `Stopped(Wizard, category=0)`
     during or after a category 1 stop does nothing: a hung controlled
     stop cannot become a cut of power. Should it give up the teardowns
     not yet run? Only another thread or a signal handler could ask that
     while a teardown hangs (question 10).
3. **What "close" means.** This STEP reads "close" as a latch until a
   deliberate reset, as ISO 13850 asks. The other reading is a permanent
   close, with no reset. Recommended: the latch.
4. **Category 0 and sticky promises.** Conditions outlive a Rip (§0.7),
   and at category 0 no teardown ends them. On TopKit 0.2.0a4, an Agent
   revoked from `Armed` without its teardown later became defective, and
   left the sound population of an unrelated Tag. Should the kit end
   Wizard's promises? Leave them loud, as §0.7 wants? Or warn?
5. **A stopped Base and new members of its Shapes** (rule 4.3). (a)
   Refuse them. (b) Apply the Shape and skip the stopped Base, so the
   Agent starts as a spin-off. Recommended: (a).
6. **Arrest, and release.** Inside a stop, arrest instead of amendment
   D's rollback (section 5)? Recommended: yes. Then how does an arrested
   Agent leave the safehouse? (a) Triage as it is, which also Rips it
   from its other Tags (rule 5.5). (b) `del Wizard[kept]` on an Agent
   that Wizard keeps reruns Wizard's failed teardowns. If they pass, the
   Agent is released and keeps its other Tags. (c) Triage that ends only
   the arrest. Recommended: (b).
7. **Interpreter exit.** `atexit.register(Stopped, Wizard)` runs as
   written. `atexit` functions run before the interpreter is finalizing,
   so that stop arrests as anywhere. An Agent kept then goes when the
   interpreter clears the kit (STEP-SPEC-18, item 12, `step-19-sound-in`
   line). Should the kit offer "stop this Tag at exit"? Recommended: no.
8. **The failures.**
   - The report (rule 5.4). STEP-SPEC-25 (PR #28, rule 2.7) uses an
     `ExceptionGroup` as the cause: one exception that carries several.
     Match it, or say why not. Recommended: match it.
   - Category 0: triage's `TagTriageWarning`, or a warning of its own?
   - A tagging of a stopped Tag (section 8). (a) The Composition Failure.
     (b) The Resolution Failure, as STEP-SPEC-28's rule 4 reads. (c) A
     failure of its own, such as `TagStoppedError`. Recommended: (a).
9. **Parallel teardowns, opt-in,** for teardowns that only wait (files,
   network)? Recommended: not in this STEP.
10. **A stop from another thread or a signal handler** could land in the
    middle of a tagging or a teardown. What should a stop promise there?
    A Ctrl-C in a teardown *would* leave the stop revoked and latched,
    with the later teardowns not run, unless the kit catches it.

## Acceptance requirements

- `tests/test_topkit.py`: a `StopTests` class, one test per rule of
  sections 1 to 7. Among them: inside a teardown, `Wizard in Stopped[:]`
  and `len(Wizard[:]) == 0`; a defective Tag stays latched; every refusal
  of rule 2.1 changes nothing; a reset brings no one back; an arrested
  Agent is in `Wizard[...]`, not in `Wizard[:]`, and the stopped Tag can
  still end (`gc.collect()`); a Link is stopped, its Relation refused.
- `tests/oracle_topkit.py`: stops and resets in the random walk.
  `benchmarks/`: the revoke phase near 0.6 µs per member.
- Spec: §3.4, section 8 and rule 6.4. Needs STEP-SPEC-26 (rule 4.2) and
  the `step-19-sound-in` safehouse.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
