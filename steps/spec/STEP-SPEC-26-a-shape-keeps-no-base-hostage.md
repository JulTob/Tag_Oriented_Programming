# STEP-SPEC-26: A Shape Keeps No Base Hostage

- **STEP:** SPEC-26
- **Desk:** spec
- **Title:** A Shape Keeps No Base Hostage
- **Author:** Julio Toboso (@JulTob)
- **Status:** Brief
- **Created:** 2026-10-08

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

Tagging stays **closed upward**: applying a Shape to an Agent that does
not hold it yet applies each of its Bases that the Agent does not hold,
Bases first (rule 5.1 says what happens to a spin-off). After that, each
membership stands alone. `del Human[bob]` is never refused because bob
holds a Shape of Human. Human's teardowns run, the Shape stays, and
nothing cascades: no other Tag is Ripped. An Agent that holds a Shape
without one of its Bases is a **spin-off**, after the Director's "shapes
just spin-off".

A Shape that truly needs its Base says so in a contract, a Postcondition.
When a Rip breaks it, the Agent turns defective and the promise names
itself. The class tree no longer does that work in secret.

```python
class Student(Tag):
    @Record
    def belt(agent, stored):
        return "white"

class Graduate(Student):
    pass

Graduate(ann)                     # applies Student, then Graduate
del Student[ann]                  # graduation: Student's teardowns run

assert ann not in Student         # she left the Student Field
assert ann in Graduate            # she is still a Graduate: a spin-off
assert isinstance(ann, Student)   # once a Student, always a Student
assert ann.belt == "white"        # what Student gave her stays
```

## Motivation

**The refusal holds the Base hostage.** Today `del Human[bob]` raises
"Human is required by active Shape(s): Werewolf"
(`TopKit/lifecycle.py:39-52`). An Agent cannot leave a Base and keep its
Shape. The Director: "We managed to build a subset without the set.
Weird but I do not see a good reason why not... we allow dels from
Human, right? so... a shape should not keep a base hostage. It should
rebuild it if it needs it."

**Team memory.** Which Tag is whose Base is written in class
declarations, often far away and often refactored. The Director: "I'm
not sure you can expect a full team to keep in their minds if the tag
they used a year ago is base to that  shape or if it was refactored a
month ago. Contracts should be the ones handling this chaos, not our
heads."

**Transitional Tags.** Real systems have stages that are passed and left
behind. The Director: "This way we can have "transitional tags", like a
training or classification belt... it makes sense in real life
systems." Graduation, in the Summary, is one.

**A stop must not be refusable.** STEP-SPEC-27 (the deletion protocol
of a Tag, drafted alongside) reads `del Human[:]` as "gain control,
stop gently": every membership ends before any teardown runs. A refusal
at the door would stop that halfway. STEP-SPEC-24, rule 1.2, already
drops its refusal at the door, citing this STEP.

**The kit already stores each membership alone.** `agent in Tag` reads
the Agent's own active Tags (`tags.py:106-124`); a walk reads the Tag's
own Field (`tags.py:137-159`). Closure comes from applying the Form
(`transactions.py:78-107`), and one refusal keeps it. A prototype without
it ran 254 tests with 2 failures, both asserting the refusal.

## Specification

In this STEP, § cites the Specification only. This STEP's own parts are
cited as "section N" or "rule N.M".

**Words used here.** A **Shape** subclasses a Tag, its **Base**. **Rip**
(`del Human[bob]`) ends one membership; **teardowns** are the Tag's
`@Rip` Actions, run after it. A **spin-off** holds a Shape but not one of
that Shape's Bases. **Sound** means every promise (Postcondition) on the
Agent holds; **defective** means one does not. This STEP does not call
the model "independent Tags": §1.1 uses that phrase for Tags in neither
one's Form.

### 1. Tagging is closed upward; membership stands alone (§0.3)

1. **Tagging is closed upward**, as today. When bob does not hold
   Werewolf yet, `Werewolf(bob)` applies every Tag in Werewolf's Form
   that bob does not hold, Bases first (§0.5). Rule 5.1 covers a
   spin-off.
2. **Afterwards, each membership stands alone.** bob is a Human because
   Human was applied to him, not because he holds Werewolf. So
   `bob in Werewolf` no longer implies `bob in Human`. History does not
   change: `isinstance(bob, Human)` stays True.

§0.3, lines 98-100, becomes: "Tagging is **closed upward** through
Bases: applying a Shape makes the Agent a member of every Base in the
Shape's Form, and it appears in each of those Fields. Each membership
then stands alone: a Rip of a Base ends that membership only (§0.7)."

### 2. Rip of a Base (§0.7)

1. **A Shape never refuses a Rip of its Base.** §0.7's bullet at lines
   232-234 becomes: "**A Shape keeps no Base hostage.** `del Beast[wolf]`
   works while `Wolf` is active: the Agent leaves Beast, Beast's
   teardowns run, and it stays a Wolf. Rip never cascades: TOP does not
   run other Tags' protocols behind your back." On the
   `step-19-sound-in` branch the bullet keeps its last sentence, from
   STEP-SPEC-18 amendment D: "A Rip whose own teardown fails is refused
   too, and rolled back (§3.1): a failed Rip blocks the expulsion."
   STEP-SPEC-24's open question 1 may change that sentence.
2. **What was given stays, including what the Shape crystallized.**
   Contributions are sticky (§0.7). A Shape's `@Underlay` captured the
   Action beneath it when the Shape applied (§1.2; `overlay.py:850`), and
   `_compose` kept a saved copy of that function (`overlay.py:147-193`).
   A Rip never builds the Actions again. The Director asked: "when you tag then the whole stack of
   underlays is build for that agent... right??? If you lose the tag you
   lose the reports and operations... but the actions were solidified
   when tagging? Right?" Yes, as probed:

   ```python
   class Human(Tag):
       def Bite(agent):
           return "human bite"

   class Werewolf(Human):
       @Underlay
       def Bite(agent, underlay):
           return f"werewolf bite over [{underlay()}]"

   Werewolf(bob)
   del Human[bob]
   assert bob.Bite() == "werewolf bite over [human bite]"
   ```

   One caution: the Base's teardowns still run. If a teardown removes
   state that the Base's Action reads, the Shape's Underlay sees the
   change.
3. **Field Rips and Links follow.** STEP-SPEC-24, rule 1.2, already
   refuses nothing at the door (revised 2026-10-08); this STEP is its
   ground. STEP-SPEC-22, rule 5.2, refused to unlink Ruth from a Base
   Link while a Shape Link holds her. That refusal goes too. Her Pair
   stays, as its rule 8.1 says ("unless a Link of the same Form still
   holds her").

### 3. What a spin-off keeps and loses

After `Werewolf(bob)` and then `del Human[bob]`:

| | After the Rip | Why |
| --- | --- | --- |
| `bob in Werewolf`, Werewolf's Field | **kept** | his own membership |
| Actions and Records, Human's included | **kept** | sticky (§0.7) |
| The Shape's view, `Werewolf[bob]` | **kept** | a snapshot taken when Werewolf applied (§1.7); the Base's published members through it: open question 1 |
| Reports read through the class, `Werewolf.motto` | **kept** | Python inheritance (`declarations.py:544-600`) |
| `isinstance(bob, Human)` | **kept** | history (§0.3) |
| `bob in Human`, Human's Field | **lost** | `list(Werewolf - Human)` is `[bob]` |
| Human's view, `Human[bob]` and `bob.Human` | **lost** | a view needs membership |
| Human's Flag words, `"Mortal" in bob` | **lost** | words come from active Tags (`declarations.py:394-416`) |
| Pin publications to Human's Field | **lost** | a Pin publishes to the pinned Tag's own Field (`transactions.py:388-449`) |
| Human's `@Public` members, `bob.motto` | **lost today** | `TagRogueAccessError`; open question 1 |

This is the Director's model: "deleting a base should actually work...
the agents lose the access to the reports of the base, but they may call
the reports of the shape... and those are set by inheritance as the same
or mutated by the shape... but actions and operations are crystallized
when tagged, not when declared the shape".

One part of that differs from the kit. Operations, like Reports, belong
to the Tag (§1.1), so the Base's published Operations go with it (the
table). What is fixed at tagging is the Agent's Actions and Records.

§1.8, lines 750-751, "a Shape answers its Base's words because the Base
is active (§0.3)", becomes: "a Shape answers its Base's words while the
Agent also holds the Base; a spin-off does not".

### 4. Saying that a Shape needs its Base

1. **Recommended: write a Postcondition on the Shape, with the guard of
   §0.7.**

   ```python
   class Werewolf(Human):
       @Post
       def Still_Human(agent):
           if agent not in Werewolf[:]:   # the promise ends with the Shape (§0.7)
               return True
           return agent in Human[:]       # plain membership, sound or not
   ```

   The guard matters. Promises are sticky (STEP-SPEC-12): `Still_Human`
   stays on bob after Werewolf is Ripped. Without the guard, an Agent
   that leaves Werewolf and then Human, in the proper order, stays
   defective for good. A guard that means membership is spelled
   `agent in Tag[:]`, which reads the same on every branch (STEP-SPEC-19,
   item 5).
2. **Recommended: not a `@Requirement`.** The Director said "we can
   impose a requirement for checking underlay's belonging". A
   `@Requirement` cannot carry it as the kit stands. A Requirement is
   also a Precondition (§2.7), and the gate runs before any Base of the
   Form applies (§2.2, lines 924-926; `transactions.py:91-107`). So it
   refuses every fresh Agent: a probe got "Precondition 'Is_Human'
   failed". Open question 5 asks which way to go.
3. **After a Rip breaks it, the Agent is defective.** bob is in
   `~Werewolf`, and `bool(bob)` is False. Soundness is the Agent's whole
   contract (§2.5), so bob also leaves every other sound population until
   repaired (a probe: gone from `list(Guild)`). This is existing law.

   The Rip itself raises nothing, and an Action call does not check
   (§2, lines 889-890). The failure is raised at bob's next tagging
   (§2.4, line 997), at a published member's use, or by a `Contract`
   read, and `except Postcondition.Still_Human` catches it there. That is
   the Director's "hey... we needed that here". Whether the Rip should
   say so at once is open question 3.

### 5. Applying again

1. **With the refusal gone, today's kit lays the Base over its Shape.**
   `Werewolf(bob)` on a spin-off applies only the missing Human, on top
   (`transactions.py:65-82`). A probe: `bob.Bite()` turned to "human
   bite", Human's Records were built again over the Shape's, Human's
   Imprint ran again, and no warning came. For a spin-off, §0.5 disagrees
   with itself: it says both "It applies every Tag in the Form that is
   not yet active" (line 150) and "Reapplying an active Tag does nothing"
   (line 159). And the Base now hides its Shape, although with Base-first
   order a Shape always lies above its Base (§1.2, line 350, "The latest
   applied Layer is the visible Overlay"). **Decided by the Director
   (2026-10-09): `Werewolf(bob)` does nothing.** "if ari is a Wizard,
   this is idempotent, so it does nothing. that's the stablished rule."
   This amends line 150: the missing Bases of a Form are applied only
   when the Shape itself is applied to an Agent that does not hold it.
2. **To bring the Base back, the program says so.** The Director, on
   2026-10-09, of `Officer(ari)` on a spin-off: "it reinstates ari as
   Officer. explicit. good."

   ```python
   Human(bob)          # Human comes back, on top, with a warning (rule 5.3)

   del Werewolf[bob]   # or Rip, then apply again (§0.5):
   Werewolf(bob)       # Human, then Werewolf
   ```

   Both repair a broken `Still_Human` (probed). Only the second keeps
   Werewolf's Bite on top. Neither starts from nothing: Records with a
   stored seat pile up (a list Record held `['human', 'human']`), and
   the Shape's sticky promises stay.
3. **Recommended (open question 2): a Base applied again lands on top
   of its Shape, and warns.** It is a later Tag like any other: "The
   latest applied Layer is the visible Overlay for a name" (§1.2, line
   350); the Guide: "The last one applied is what you see." Today
   `overlay._independent` (`overlay.py:83-92`, which calls
   `geometry._related`) mutes the Overwrite Warning there; it would fire,
   naming the Shape. The Contract Warning (`overlay.py:316-320`) says
   "Human.Sane overrides a Base Postcondition" when the promise it covers
   is the Shape's: it should say "a Base laid over its Shape's sticky
   promise".

### 6. The order of deforming (§0.4)

Recommended. §0.4, lines 139-140, "Deforming (Rip) goes the other way: a
Shape leaves before the Bases that support it", becomes: "Deforming by
hand may go in any order (§0.7). When TOP runs an Agent's teardowns
itself, at its deletion or at exit (§3.2), they run in reverse order of
application: the last Tag applied first. At a Tag's end, Shapes go
before Bases (STEP-SPEC-24, rule 3.4)." The kit already does this
(`lifecycle.py:121`): with a Base applied again over its Shape, a probe
ran the Base's teardown first at deletion.

### 7. A Base's name deleted or declared again

1. **`del Human` removes a name**, never a Tag (STEP-SPEC-24, Rationale).
   Werewolf keeps the Base class it was declared with: the kit reads the
   Form from the class and caches it (`geometry.py:49-75`). So for a
   fresh Agent, `Werewolf(cy)` still applies that Base. The Director's "if
   it doesn't exist, then it should rebuild" happens with no new law.
2. **A new `class Human(Tag)` is a different Tag** that shares a name. A
   contract that names `Human` reads the name when it is checked, so it
   notices both changes:

   ```python
   del Human           # Werewolf still holds its Base
   Werewolf(cy)        # applies that Base, then raises Postcondition.Still_Human:
                       # "raised NameError: name 'Human' is not defined";
                       # the Tags stay (§0.6)

   class Human(Tag):   # a new Tag with an old name
       def Bite(agent):
           return "new human bite"

   Werewolf(dee)       # applies the old Base, then raises Postcondition.Still_Human:
                       # the guard passes, and the new Human does not hold dee
   ```

   Both calls raise the contract failure by name, and both Agents keep
   their Tags, defective (§0.6). That is the Director's "raise a contract
   failure saying (hey... we needed that here)", and, as he asked, "it
   shouldn't block the whole progression".
3. **One Agent can then carry two Tags named Human**: `Human(eve)`, then
   `Werewolf(eve)`. A probe printed `f"{eve:tags}"` as "Human, Werewolf"
   and warned "Human.Bite replaces the Action of independent Tag Human".
   `Still_Human` passes there: it checks the Tag that has the name now.
   Displays and messages must tell the two apart (Acceptance).

### 8. Pins, Scope, the safehouse, displays

1. **Pins follow the same rule** (§1.9). With `Legendary` a Shape of the
   Pin `Rare`, `del Rare[Sword]` works while `Legendary(Sword)` is
   active, and Sword stays Legendary. Today it is refused.
2. **Scope** Rips what it applied, and only that (§0.7). In
   `with Scope(lu, Human): Werewolf(lu)`, the exit now Rips Human, and lu
   leaves as a spin-off. Today's kit swallows that refused Rip in silence
   (`lifecycle.py:201-208`). On `step-19-sound-in`, the tests and
   examples of a reported refused Rip used this refusal; they need a
   failing teardown instead (STEP-SPEC-18 amendment D, if it survives
   STEP-SPEC-24's open question 1).
3. **The safehouse** (`step-19-sound-in`, STEP-SPEC-18 amendment E) sorts
   kept Agents by the class tree (`lifecycle.py:342`, `:354` there). So
   `Wizard[...]` may list a spin-off kept by Archmage who is not in
   `Wizard[:]`, and triage reaches it. Recommended: keep the class tree.
   The Director, on 2026-10-02, before spin-offs existed (STEP-SPEC-18,
   line 435 on `step-19-sound-in`): "also standard Catched[...] should
   list the subtags tree and overlays. Departments are part of the
   agency. A branch has subranches." Open question 6 asks whether that
   still holds for a spin-off.
4. **Displays.** `Tags(bob)` lists the leaves and stays `(Werewolf,)`.
   With the refusal gone, `Outline(bob)` drops the missing Base without a
   sign. Recommended: show where the Base was, marked (open question 4).

## Rationale

**Explicit beats implicit.** The Director called this "my last straw to
decide this is the model we want". Under the refusal, a need hid in the
class tree. Now a need is a line in the Shape, and a broken need is a
failure with that line's name.

**Contracts handle the chaos, not our heads.** No one has to remember
which Tag is whose Base. A Rip does what it says; if it breaks
something, the contract that cared says so.

**No domino effects.** The Director: "I know is weird, but the rule
makes sense. We already built the core so it's normal to have to make
decisions on edge cases. So it's clean, clear, no domino effects... What
do you think?" One Rip touches one Tag. Nothing is refused, and nothing
cascades. A cascade is rejected by §0.7 (it runs other Tags' teardowns
behind the program's back), and it would end the Graduate at graduation.

**Why not keep the refusal.** It holds the Base hostage, asks the team
to remember the class tree, and makes a stop refusable.

**Why a Postcondition, not a Requirement.** The gate inspects the Agent
as it arrives, before any Base applies (§2.2). A Postcondition is
checked when the whole Form stands, at every later tagging boundary,
and whenever soundness is read.

## Backwards compatibility

1. **A program that relied on the refusal** must now state the need as a
   Postcondition on the Shape (rule 4.1).
2. **Code that reads Base membership from Shape membership** (`if x in
   Werewolf:`, then assuming Human) must ask the Base.
3. **Tests that assert the refusal.** On HEAD, two:
   `test_ripping_a_required_base_is_refused` (`tests/test_topkit.py:2228`)
   and `Rip_Refused` (`tests/oracle_topkit.py:176`). On
   `step-19-sound-in`, nine: those two, five ScopeTests (`test_topkit.py`
   3494, 3511, 3534, 3612, 3709), the §3.2 Scope example
   (`spec_examples.py` 214-219) and the Guide's Veteran block (750-773).
4. **Text on HEAD.** `spec/SPECIFICATION.md` 98-100, 139-140, 150 or
   159 (open question 2), 232-234, 750-751, 1316 ("a Base still
   required"), 1334-1335, 1337 and 1341-1342. `CONFORMANCE.md:14`.
   STEP-SPEC-22 rule 5.2 and two passages that cite it, already revised
   with this STEP. STEP-SPEC-24, rule 3.4,
   cites §0.4's "Deform them by hand" (section 6).
   `tests/oracle_topkit.py` lines 5-6, the model's header.
   STEP-SPEC-17 (Vetting) 30, 63 and 132. STEP-SPEC-6 (Deployed) 20-23,
   "The refusal is the law", by an amendment note; STEP-SPEC-11
   (Redacted) 50, a note at most. `TopKit/lifecycle.py:5`.
5. **More on `step-19-sound-in`.** Spec 101-103, 143-145, 237-241,
   764, 950-952, 1346, 1481-1483, 1495-1497, 1533, 1552-1561,
   1620-1621; `CONFORMANCE.md` 14 and 17; STEP-SPEC-19 67-69 and
   125-128; STEP-SPEC-18 86-87 and 427; `IMPLEMENTATION_NOTES.md` 147 and
   404; `declarations.py` 465-466; `lifecycle.py` 5, 438 and 568-572.
   Spec 79 and 1392-1397 stay true with the class tree; they gain one
   sentence: a spin-off may be in `Wizard[...]` and not in `Wizard[:]`.
6. **STEP-SPEC-25** (PR #28). Its rule 2.7 (line 253) cites
   "STEP-SPEC-24, rule 1.2" for failures reported once; that is rule 1.4,
   in its own copy too. With spin-offs, a write through `Human[:]` no
   longer reaches an Agent that left Human and kept a Shape.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Keep the refusal | The Base is held hostage; the team must remember the class tree; a stop becomes refusable. |
| Cascade: Ripping a Base Rips its Shapes | Rejected by §0.7: other Tags' teardowns run behind the program's back. It also ends the Graduate at graduation. |
| Work out Base membership from the Shape at read time | `del Human[bob]` could then end nothing while bob is a Werewolf: the refusal in another form. |
| A `@Requirement` on the Shape | Refuses every fresh Agent: the gate runs before the Bases apply (rule 4.2). |
| Let the gate see the Bases its Form will apply | Changes §2.2 for every Precondition. Open question 5. |
| Re-apply a missing Base beneath its Shape | Every Action above it, fixed at tagging, would have to be built again: a change in the kit's core, against "never resolves again later" (§1.2). |

## Implementation plan

1. **`lifecycle._rip`:** delete the refusal (HEAD 39-52;
   `step-19-sound-in` 51-64) and its import; `geometry._requiring_shapes`
   (101-114) loses its only caller (keep it, renamed, if open question 3
   is answered yes: the Rip check needs it). A prototype: −31/+3 lines.
2. **`transactions._apply`** (65-69), for option A: return when the Tag
   itself is active. A few lines; a prototype on main, refusal tests
   updated, passed main's suite (253 tests).
3. **`overlay` warnings** (`_independent`, 83-92; sites near 868-879
   and 933-944; Contract Warning, 316-320), for rule 5.3. Small.
4. **Publication** (`overlay._require_membership`, 231-258;
   `state._Published.__get__`, 754-774), per open question 1. Medium.
5. **`queries.Outline`** (66-90) and a Rip warning in `_rip`, per open
   questions 4 and 3. Small; the warning is paid only by spin-offs.
6. **Text:** `access._agent_copy`'s copy recipe (389-395); the Scope
   docstring on `step-19-sound-in` (551-576); the oracle's
   `Exercise_Scope` ("a Rip refused for a required Base is swallowed").
7. **No change:** the population operators in `tags.py`, `fields.py`,
   `contracts._holds`, `_gate`, `_teardown_all`, `_publish_to_field`.

**Land it after the `step-19-sound-in` branch, or on top of it.** Both
edit the same Ring 0 lines and `lifecycle._rip` (next to amendment D).
That branch also has about six tests and ten passages resting on the
refusal: a trial merge gave 7 small conflicts, then 7 failing tests.

## Open questions for the Director

1. **A spin-off and the Base's published members.** Today `bob.motto` (a
   `@Public` Report of Human) raises `TagRogueAccessError` once bob
   leaves Human, while `Werewolf.motto` answers through the class.
   (a) Keep that (§1.5). (b) A member of the Shape keeps the published
   members the Shape inherits unchanged, read through the Shape.
   Recommended: (b), the Director's "they may call the reports of the
   shape... and those are set by inheritance as the same or mutated by
   the shape". Then a published Operation gets the Shape as its Tag
   (`Werewolf.Census(bob)` answers "Werewolf counts" today). Right?
2. **Where a reinstated Base lands.** Decided on 2026-10-09:
   `Werewolf(bob)` on a spin-off does nothing (rule 5.1), and
   `Human(bob)` reinstates the Base (rule 5.2). Still open: where its
   layer goes. Recommended: on top, with a warning (rule 5.3). The other
   choices are to install it beneath the Shape, which means building the
   Shape's Actions again (a change in the kit's core), or to refuse it,
   which the Director's "explicit. good." rules out.
3. **Should a Rip that leaves an Agent defective say so at once?**
   Today the failure is raised later (rule 4.3). (a) Nothing, as today.
   (b) A warning at the Rip, naming the broken promise. (c) Raise
   `Postcondition.Still_Human` once the Rip is done; the Rip stands, as
   §3.1 reports a failed teardown. The Director asked that it "should
   raise a contract failure". Recommended: (c), checked only for a Rip
   that leaves a spin-off, so other Rips pay nothing.
4. **How `Outline` shows a missing Base.** `Tags` stays as it is: it
   lists leaves. For ann, which word or mark?

   ```text
   Person
     Student  (left)
       Graduate
   ```

5. **Your "requirement".** It cannot be a `@Requirement` as the kit
   stands: it refuses every fresh Agent (rule 4.2). (a) Write it as a
   guarded Postcondition (rule 4.1). Recommended. (b) Let the gate see
   the Bases its Form will apply. That changes §2.2 for every
   Precondition. Which? The Director has since proposed retiring
   `@Requirement` in favour of `@Pre` and `@Post` (STEP-SPEC-30). A
   `@Pre` naming the Base refuses every fresh Agent for the same reason,
   so under (a) the spelling is the guarded `@Post`.
6. **A spin-off in the safehouse's departments.** Should `Wizard[...]`
   list an Agent kept by Archmage that no longer holds Wizard (rule
   8.3)? Recommended: yes, the class tree, as now.

## Acceptance requirements

- `tests/test_topkit.py`: a `SpinOffTests` class, covering:
  - `del Base[agent]` under a Shape: not refused, teardowns run, the
    Shape stays, `Shape - Base` lists the Agent, nothing cascades;
  - what stays (Actions, Records, an `@Underlay` chain into the Base, the
    Shape's view) and what goes (the Base's view, Flag words, Pin
    publications, published members per question 1);
  - a guarded Postcondition naming the Base: passes at tagging; an
    Agent that leaves the Shape and then the Base stays sound; after the
    Rip of the Base alone,
    `except Postcondition.<name>` catches it and the Agent leaves an
    unrelated sound population; both repairs of rule 5.2;
  - a Requirement naming the Base refuses a fresh Agent (the guidance);
  - applying again per question 2; a Base over its Shape warns;
    deletion runs teardowns in reverse order of application;
  - `del Base` by name and a new declaration: the Shape applies its own
    Base; the contract fails by name; two Tags of one name are told
    apart in displays and warnings;
  - Pins; Scope; the Rip warning and the `Outline` mark (questions 3, 4).
- The old refusal test becomes a test that the Shape stays. On
  `step-19-sound-in`, the ScopeTests use a failing teardown instead.
- `tests/oracle_topkit.py`: `Rip_Refused` no longer refuses for a Shape;
  the model applies again per question 2; spin-offs in the walk.
- When STEP-SPEC-24 lands: `del Base[:]` leaves spin-offs.
- `tests/spec_examples.py`: the new §0.3 and §0.7 examples. The Guide: a
  pattern, "A training belt", when this STEP is Deployed.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
>
> *The Director chose the model on 2026-10-08, ahead of the whole STEP:*
> "So the best model is independent tags? Right? shapes just spin-off and
> you are right... we can impose a requirement for checking underlay's
> belonging. This way we can have "transitional tags", like a training or
> classification belt... it makes sense in real life systems. Also the
> requirement follows the maxima: "Explicit beats implicit" which is my
> last straw to decide this is the model we want. Yep. Decided. Let's go
> for it and start building it."
>
> *Decided by the Director on 2026-10-09:* applying a Shape the Agent
> already holds does nothing, a spin-off included ("if ari is a Wizard,
> this is idempotent, so it does nothing. that's the stablished rule");
> applying the Base again reinstates it ("it reinstates ari as Officer.
> explicit. good.").
>
> The Status stays Brief until the Director has read this text and
> answered the open questions.
