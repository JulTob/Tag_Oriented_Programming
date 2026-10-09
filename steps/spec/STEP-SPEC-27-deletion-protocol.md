# STEP-SPEC-27: The Deletion Protocol of a Tag

- **STEP:** SPEC-27
- **Desk:** spec
- **Title:** The Deletion Protocol of a Tag
- **Author:** Julio Toboso (@JulTob)
- **Status:** Brief
- **Created:** 2026-10-08, as "Emergency Stop".
- **Revised:** 2026-10-09, after the Director's correction: this STEP is
  the deletion protocol of a Tag, not a latch.

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

To delete a Tag is to **gain control, stop gently, then reset**. Every
membership ends at once. Then each member's teardowns run, one member at
a time. At the end the Tag is still defined and "the power is still on":
it can be tagged again at once, with no error. The act is STEP-SPEC-24's
Field Rip, `del Human[:]`. This STEP proposes a reset of the Tag's own
values, and keeps `del Human` as Python's own act.

```python
from TopKit import Tag, Report, Rip

class Human(Tag):
    @Report
    def colour(tag):
        return "green"
    @Rip
    def Stand_Down(agent):
        agent.on_duty = False

Human(ann)
del Human[:]          # gain control, then stop gently: Stand_Down runs
Human(bob)            # the power is still on: tagging works at once

Human.colour = "red"
del Human.colour      # proposed: forget "red"; the builder runs at next read
assert Human.colour == "green"
```

This parses. No kit runs it yet: `del Human[:]` is STEP-SPEC-24 (Brief),
and the reset of a Report is new here (section 4).

## Motivation

The Director, on 2026-10-08: "So how do we implement a category 1 (or
higher) stop? revoke all - rip protocols (teardowns) - close. No
cascades. a deletion protocol may execute a deletion of all bases, but
that should be explicit, not magic. same for paralellism."

The first draft of this STEP misread those words. It read "close" as a
**latch** (a switch that stays shut until someone resets it), and built
a Pin, `Stopped`, that kept the Tag closed to new members. That was
wrong, and this revision withdraws it. The Director, on 2026-10-09:

> "In the catalog you added something about stopped category that was
> meant for the deletion protocols, that we wanted to gain control, stop
> gently then delete. It looks like you mixed it up a bit."

> ""del Human removes the NAME only" what? The name of the tag? so it
> still exist but is unreachable? that's a bit stupid. We should delete
> the tag with that, and del Human[:] just cleans the field but leaves
> the tag as defined. what I meant by level higher is that a deletion of
> a class doesn't "clean the board" as the tag is a blueprint, just as
> classes, so it may be called again, so a del is more like. reset: the
> tag is reinstantiated at the end, so it's like the power is still on,
> and you can connect (tag) again back to it, not raising a tremendous
> error."

## Specification

**Words used here.** § cites the Specification; "rule N.M" cites this
STEP.

| Word | Meaning |
| --- | --- |
| **Field** | Every member of a Tag: `Human[:]`. |
| **Rip**, **teardown** | A Rip ends one membership, `del Human[ann]` (§0.7). Teardowns are the Tag's `@Rip` Actions, run after it (§3.1). |
| **Field Rip** | `del Human[:]`: a Rip of every member at once (STEP-SPEC-24, Brief). |
| **Report** | A value of the Tag itself. Its **builder** runs once per Tag, on first read (§1.4). |
| **Shape**, **Base**, **spin-off** | In `class Werewolf(Human):`, Werewolf is a Shape and Human its Base. A spin-off holds a Shape but has left its Base (STEP-SPEC-26, Brief). |
| **Safehouse**, **triage** | On the `step-19-sound-in` line (S19): Agents the kit keeps after a failed teardown, `Human[...]`; and `del Human[...]`, which lets them go without teardowns (STEP-SPEC-18, amendments E and F). |

### 1. Why `del Human` cannot be the act

1. **A name is a label on a box.** `class Human(Tag):` makes a box (the
   class) and sticks the label `Human` on it. Other things hold the same
   box: another name, a Shape (Werewolf holds Human as its Base), a
   function, a list. Today each member's history holds it too (probed).
2. **`del Human` peels off one label, and Python tells no one.** It
   calls nothing on the class, and no hook exists for it. A class does
   see `del Human[:]` and `del Human[...]` (its `__delitem__`) and `del
   Human.colour` (its metaclass's `__delattr__`). Probed on Python 3.13:

   ```python
   class Werewolf(Human):             # a Shape: it holds Human as its Base
       pass

   H = Human                          # a second label on the same box
   del Human                          # one label gone; nothing is called
   assert H is Werewolf.__bases__[0]  # the box is still there, the same
   ```

3. **Python never lets one label destroy a box that others still hold.**
   That keeps every other reference safe: if `del Human` destroyed the
   class, `H` would point at nothing, and Werewolf would stand on a Base
   that is gone. Python frees a box only when no label is left. Under
   STEP-SPEC-24 (section 3), a Tag's end then comes later, at a
   collection: its Field is Ripped best effort, failures silent. And a
   teardown that looks up the name `Human` fails, because the name is
   gone (`NameError`, probed).
4. **So, to the Director's question:** after `del Human` the Tag still
   exists, and every other label still reaches it. This matches "the tag
   is a blueprint": deleting one name for it does not "clean the board".
   What can be cleaned is what it holds, its Field and its own values,
   and TOP hears exactly those acts. `del Human` stays Python's: forget
   a name.

### 2. The protocol: gain control, stop gently, reset

The act is `del Human[:]` (STEP-SPEC-24). This STEP names its phases
and what holds at the end.

1. **Gain control.** Every membership ends at once, in join order. No
   user code runs: no teardown, no condition, no Imprint (code run at
   joining). From here on, no member holds the Tag's access
   (STEP-SPEC-24, rule 1.3).
2. **Stop gently.** Then each member's teardowns run (§3.1: every one,
   in declaration order), one member at a time, in join order: first in,
   first out. The Director: "We'll follow [your] fifo recommendation on
   deletion". Inside every teardown, `len(Human[:])` is 0. A failure
   stops neither that member's other teardowns nor the next member's.
   Failures are reported once, after the walk (STEP-SPEC-24, rule 1.4).
   Where a member whose teardown failed ends up is STEP-SPEC-24's open
   question 1; this STEP adds no rule of its own.
3. **Reset: the power is still on.** At the end the Tag is still
   defined: the same class, with its Shapes, Reports, Operations and
   Pins. Its Field is empty, and `Human(bob)` works at once. There is no
   latch, nothing to unlock and no error. What the Tag gave its old members
   stays on them (§0.7): they are Rogue Agents, with what they learned
   but no access.
4. **Nothing refuses it.** A member that holds a Shape leaves Human and
   keeps the Shape (STEP-SPEC-24, rule 1.2, with STEP-SPEC-26). A
   teardown that applies Human again makes a member, and it stays (rule
   1.5 there; §3.1 calls this outside good TOP use).

Today it is a loop by hand, `for h in list(Human[:]): del Human[h]`.
The Tag takes members again afterwards, but with three members the
teardowns saw the Field at sizes 2, 1, 0 (probed on TopKit 0.2.0a4). Phase 1 fixes that.

### 3. The stop categories

Machine safety names three ways to stop (IEC 60204-1, clause 9.2.2;
wording from secondary copies):

| Category | IEC 60204-1 | Power after the stop | In TOP |
| --- | --- | --- | --- |
| 0 | "stopping by immediate removal of power to the machine actuators" | cut at once | give up the teardowns: triage (section 5) |
| 1 | "a controlled stop with power available to the machine actuators to achieve the stop and then removal of power when the stop is achieved" | removed | gain control, stop gently (rules 2.1, 2.2) |
| 2 | "a controlled stop with power left available to the machine actuators" | left on | the Tag stays defined and taggable (rule 2.3) |

1. **Categories 1 and 2 stop the same way, under control.** They differ
   only after the stop: category 1 removes power, category 2 leaves it.
2. **The Director's protocol stops like category 1, then keeps the
   power like category 2.** By the standard's own words, a controlled
   stop with power left available is category 2. So this STEP now reads
   "category 1 (or higher)" as category 1's controlled stop, then
   category 2's power rule. (The first draft read "higher" as a hold in
   which members kept everything. Wrong too: category 2 stops.)
3. **This is not an emergency stop.** IEC 60204-1 and ISO 13850 allow
   only category 0 or 1 for one, latched until a deliberate reset. This
   STEP has no latch, so its title no longer says "Emergency Stop".

### 4. "Reinstantiated": the Tag's own values (open)

"The tag is reinstantiated at the end" can mean three things.

1. **(a) The same Tag, still usable.** Always true after rule 2.3.
   Nothing needs rebuilding: Python never destroyed the class.
2. **(b) The Tag's own values go back to as declared.** A Report's
   builder runs once per Tag, and the value is then held (§1.4). The
   proposed spelling resets one Report: **`del Human.colour`**.
   - Over a declared Report, the Tag forgets its value, built or
     written. The builder runs again at the next read.
   - Over a value written by hand with no declaration (`Human.motto =
     "brave"`), the value is removed, as Python does today.
   - Over a name the Tag gives its Agents (a Record, an Action, a
     condition), it is refused: a category error (STEP-SPEC-28, rule 3).
   - One Tag only: Werewolf's own built value (§1.4: once per Tag) is
     not reset.
   - One name at a time, as `Contract.Delete(agent, "Has_Book")` ends
     one condition (§0.7). Several fit in one statement, done left to
     right (probed): `del Human[:], Human.colour, Human.count`.
3. **(c) A new class from the same class statement.** Set aside. There
   would be two Humans. Werewolf, the members' history and every other
   label would keep the old one, so `isinstance(bob, Human)` would ask
   about a class bob never carried.

**Recommended:** (a), with (b) spelt `del Human.colour`; and `del
Human[:]` does not touch Reports. The Director: "del Human[:] just
cleans the field but leaves the tag as defined" (open question 2).

**What the kit must change for (b).** Probed on TopKit 0.2.0a4: a write
over a declared Report (`Human.count += 1`) replaces the declaration
with a plain value, and `del Human.colour` removes the declaration (the
next read raises `AttributeError`). MetaTag (`TopKit/tags.py:51`) has
no `__setattr__` or `__delattr__`, and a descriptor's own `__set__` and
`__delete__` are not called for a write or a `del` on the class itself.
So MetaTag gains both: to keep each declaration while a written value
is in place, and to bring it back at `del`.

### 5. Category 0 is triage, when it applies

1. **Category 0 gives up the teardowns.** TOP already has one act for
   that: triage, `del Human[...]` (STEP-SPEC-18, amendment F, Vetting on
   S19). It reaches only the Agents in the safehouse, Rips each from
   every Tag it carries, and gives one `TagTriageWarning` each. This
   STEP adds no act that skips the teardowns of a member not kept.
2. **So category 0 follows a gentle stop that failed.** If STEP-SPEC-24
   keeps a member whose teardown failed (its open question 1, option
   (a)), the program may then give up on it:

   ```python
   del Human[:]      # gain control, stop gently; a failed member may be kept
   del Human[...]    # category 0, for the kept ones only: triage
   ```

   On S19 today the safehouse fills only at an Agent's deletion
   (amendment E); a failed explicit Rip is rolled back (amendment D).

### 6. No cascades

1. **One act, one Tag.** "Rip never cascades" (§0.7). `del Human[:]`
   Rips no one from Werewolf: each Werewolf stays one, as a spin-off.
   `del Human.colour` resets Human's value only. `del Rare[:]` un-pins
   every Tag and deletes none of them (STEP-SPEC-24, rule 1.6).
2. **Several Tags are several lines.** The Director: "a deletion
   protocol may execute a deletion of all bases, but that should be
   explicit, not magic."

   ```python
   def Retire_Werewolves():     # the program's own protocol, every step said
       del Werewolf[:]          # the Shape first
       del Human[:]             # then its Base
       del Human.colour         # proposed: back to its builder
   ```

### 7. Parallelism: explicit only

The protocol runs in the caller's thread, one member at a time, in join
order. Ring 4: "One Agent, one thread. Fields are not synchronized." A
program that wants parallel work writes it, for example in a teardown
that hands slow work to its own threads. The Director: "same for
paralellism", and earlier: "Parallel programming should be explicit."

## Rationale

**Reach a safe state first.** Phase 1 runs no user code, so no program
error can stop it halfway. Incident response works in the same order:
first every badge stops working, then the paperwork.

**The power stays on.** A latch needs a second act to undo it, and a
tagging before that act fails: the "tremendous error" the Director does
not want. A blueprint can always be used again.

**Sources** (secondary copies; the standards' own text was not read):
- [Lenze: stop categories (EN 60204)](https://www.lenze.com/en-de/go/akb/200502242/1)
- [Wenglor: stop category](https://wenglor.com/en/Stop-Category/l/cxmCID123755)
- [ABB PLC help, sf_outcontrol (cites IEC 60204-1 9.2.2)](https://help.plc.abb.com/sf_outcontrol.html)
- [ANSI blog: ISO 13850](https://blog.ansi.org/ansi/iso-13850-safety-of-machinery-emergency-stop/)

## Backwards compatibility

- `del Human` is unchanged. `del Human[:]` was an error (STEP-SPEC-24).
- `del Human.colour` over a declared Report today removes the
  declaration; under rule 4.2 it forgets the value only.
- `Stopped` was never built, so withdrawing it breaks nothing.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| The first draft: a Pin `Stopped` that latches the Tag shut, and `del Stopped[Wizard]` as the reset | Withdrawn: a misreading of "close". The Director: "It looks like you mixed it up a bit." The power must stay on. |
| Make `del Human` the act | Impossible: Python calls nothing on the class (rule 1.2). |
| Destroy the class | Unsafe: other labels and Shapes still hold it (rule 1.3). |
| Run the class statement again, a new Human | Two Humans: the members and Shapes keep the old one (rule 4.3). |
| `del Human[:]` also resets every Report | Against "del Human[:] just cleans the field but leaves the tag as defined" (open question 2). |
| A function, `Reset(Human)` | Set aside for now: `del` is already Rip's spelling (§0.8). Open question 4. |
| Category 0 for live members: revoke with no teardowns | Not proposed: the protocol stops gently, and triage covers kept members (section 5). |
| Teardowns in parallel by default, or a cascade | Rejected by the Director (sections 6 and 7). |

## Open questions for the Director

1. **The reading.** "Gain control, stop gently, then delete" is `del
   Human[:]`, and "close" is its end, with the power on. Is that what
   you meant? Recommended: yes.
2. **Does `del Human[:]` reset Reports too?** (a) No, it cleans the
   Field only. (b) Yes, every Report goes back to its builder.
   Recommended: (a), from "just cleans the field".
3. **`del Human.colour` as the reset of one Report** (rule 4.2)?
   Recommended: yes, for that one Tag only.
4. **A full reset in one act** (the Field and every Report)? (a) None:
   write the lines, or one statement, `del Human[:], Human.colour`. (b)
   A function, `Reset(Human)`. Recommended: (a) for now.
5. **Category 0 for live members?** Recommended: no new act (section 5).
6. **An emergency stop with a latch**, as the standards define one?
   Recommended: not now; a STEP of its own if a program needs one.
7. **Parallel teardowns, opt-in?** Recommended: not in this STEP.

## Acceptance requirements

- `tests/test_topkit.py`, `DeletionProtocolTests`: after `del Human[:]`,
  `Human(x)` works at once; every teardown sees `len(Human[:]) == 0`;
  `del Human` leaves every member a member; `del Human.colour` reruns
  the builder after a read and after a write; a value written by hand is
  removed; `del Human.hp` over a Record raises `TagCategoryError`;
  Werewolf's own built value is untouched; `del Human[:], Human.colour`
  runs left to right.
- Kit: MetaTag gains `__setattr__` and `__delattr__` (rule 4.2).
- Spec: §1.4 gains the reset of a Report, and §0.8 a row, "reset a
  Report: `del Wizard.colour`". STEP-SPEC-24's §3.3 names the three
  phases and says `del Tag` is Python's own act.
- Needs STEP-SPEC-24, 26 and 28. Section 5 needs the S19 safehouse.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
