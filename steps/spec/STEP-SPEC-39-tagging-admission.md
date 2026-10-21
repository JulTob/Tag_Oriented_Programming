# STEP-SPEC-39: Tagging Admission

- **STEP:** SPEC-39
- **Desk:** spec
- **Title:** Tagging Admission
- **Author:** Julio Toboso (@JulTob)
- **Status:** Cleared
- **Created:** 2026-10-12

## Summary

Tagging follows **Gate → Gainings → Imprints → FieldAdding → Posts**.
Unfinished training leaves actual Gains without membership; completed
training admits the Agent, and Posts determine its current soundness.
This supersedes the training and admission boundaries of STEP-SPEC-4.

> **Condition-lifetime amendment, 2026-10-20:**
> [STEP-SPEC-61](STEP-SPEC-61-condition-lifetimes.md) replaces this STEP's
> condition-retention statements. Actions and Records actually acquired by an
> unfinished attempt keep the Rogue behavior below, but every provisional
> Post from that attempt is discarded. Pres are transient Gate Services.

> **Later Director amendment, recorded 2026-10-21:** The final section below
> records the Director's subsequent decisions about source validity,
> structural preparation, best-effort training and per-Tag Post inspection.
> It takes precedence over the older failure and whole-Form timing statements
> retained here. The original 2026-10-12 Decision remains dated history;
> the STEP remains **Cleared**.

## Motivation

A car is a car after assembly. A broken assembled car belongs to that
category; a wheel next to a frame is an unfinished attempt to produce one.
Likewise, membership follows completed training rather than preceding it.
An Agent with acquired Gains outside the Agency is Rogue, whether training
was partial or it previously entered and was Ripped.

## Specification

1. Missing Tags take independent turns in Base-first Form order. Each passes
   its own Gate against the Agent's current state. A refusal leaves this Tag
   unstarted and completed earlier Tags in place.
2. Actions, Records, condition definitions and deletions take effect in
   declaration order, top to bottom. Every acquired Gain or condition is
   visible to later declarations. All this Tag's own Preconditions have
   already been evaluated at the Gate. Record builders read and query to
   calculate their initial returned value; applying or Ripping Tags belongs
   to Imprints.
3. Imprints follow Gainings, in declaration order. The Agent can use acquired
   Actions and Records, but does not yet belong to this Tag. This Tag's
   published Reports and Operations and its Agent-bound view are unavailable
   through the Agent until admission.
4. After Imprints finish, FieldAdding establishes membership, history and
   Field entry together. An unfinished attempt establishes none of these.
5. Once the whole Form finishes, every visible Post checks the resulting
   Agent. Posts define requirements; a missing optional Gain or a historical
   exception does not independently define deficiency. Post failure preserves
   membership, and current Posts determine soundness.
6. Failed Gainings or Imprints retain actually acquired Gains and completed
   Taggings, without admitting the unfinished Tag. Python interruptions follow
   the same boundary and keep their original exception type.
   Acquired conditions also remain, including Posts and Constant Posts, just
   as established contracts remain after Rip. Ordinary Posts follow existing
   composition rules; Constant Posts keep their protection.
7. Calling `Tag(agent)` on this Rogue starts a fresh Gate, overlays ordinary
   Gains and restarts Imprints. It does not resume an interrupted instruction.
   Successfully established Constants remain protected; failed initialization
   does not establish a Constant Record binding.
8. Applying this same Tag to the same Agent while its Tagging is already
   underway is a no-op. An active reapplication also remains a no-op.
9. A failed never-member is outside `Tag[:]` and does not run Rip automatically.
   The program owns cleanup of unfinished training effects using ordinary
   Python error handling. Preconditions and Record builders are observational
   authoring rules, not a sandbox for arbitrary Python effects.

## Rationale

Gain acquisition and Agency membership are distinct facts. A Rogue can
satisfy its visible Posts without being admitted. An admitted Agent can be
deficient without ceasing to belong. Retrying through normal Tagging uses
TOP's existing Overlay and Imprint mechanisms rather than introducing a
resume protocol.

Posts remain once after the completed Form: a Base may promise what a later
Shape supplies. Existing conditions remain sticky after Rip; this STEP does
not change the author's responsibility for ending them.

A safety Post can precede the Action that needs it, so the contract is already
established when that Gain arrives. This does not automatically guard ordinary
Action calls; an Action can explicitly read its named safety condition before
effects. Acquired Posts also govern current validity and guards on
published services from active Tags.

## Backwards compatibility

Imprints can no longer assume their own Tag's membership, view or published
Agency services through the Agent. Failed training no longer admits this Tag,
and Record failure no longer restores completed independent Taggings.
Programs that caught training failures and then Ripped this Tag should handle
their unfinished resources directly instead. Post failures still preserve
membership and use the existing defective population `~Tag`.

## Alternatives considered

| Alternative | Decision |
| --- | --- |
| FieldAdding before Imprints | Superseded: an unfinished product is not yet a member |
| Require Posts before FieldAdding | Rejected: a broken completed product remains a member; Posts may inspect membership |
| Restore the whole Form after failed training | Rejected: Tags are independent, and actual completed work remains |
| Resume at the failed Imprint | Set aside: normal Tagging is a fresh attempt using the Agent's current state |

## Acceptance requirements

Verify ordered visibility of Gains; no membership or new history during
training; retained Gains and earlier Tags after failure; fresh retry and
Constant initialization boundaries; publication after admission; same-Tag
recursive application as a no-op; and Post failure preserving membership.
The independent oracle must model these outcomes, including Field join order.

---

### Decision

> Cleared on 2026-10-12 by the Director: **Gate → Gains/Imprints → Field → Posts**.
> Posts control a failure of completed training; unfinished training produces
> a Rogue with Gains outside the Agency. The Director also specified that
> Gains arrive in Tag declaration order, top to bottom, and are visible to
> subsequent Gains. Implementation is submitted in successive reviewable PRs.

### Later Director amendment — recorded 2026-10-21

This records subsequent rulings already given by the Director in the project
work session. The date above is the date of this record, not a claim that
every answer was given on that date. It amends this STEP's training and
admission boundary; it does not Clear a separate Brief or introduce recovery
syntax.

The Director's answers establish the following source of authority:

- **Independent Tag turns:** “On each tagging. A form just indicates
  layering, they are not inherited so inheritance should not be assumed as
  the wanted behaviour.” Each Tag's Post inspection precedes the next Tag's
  Gate.
- **Valid source:** “But every tagging for a new tag must be in a valid
  agent.” Repair before fresh Tagging was also explicitly approved, including
  when a retained Constant Post is false after Rip.
- **Record preparation versus training:** “the initialization of a Record is
  an imprint labeled @Record” and “the failure on building a record should
  not initialize it.” The Director approved preflighting all Record spaces
  before Gains and a public `TagTargetError` subtype. This describes the
  Record initializer's training role; it does not require an additional
  `@Imprint` decorator on a Record.
- **Best-effort training:** the Director approved Field entry after failed
  ordinary training and then said “continue later imprints.” The selected
  diagnostic rule was “Warnings per step, one final Post error,” with named
  training warnings and every failed Post named in evaluation order.
- **Current Contract:** “Judge current Posts; @Constant protects required
  ones” was approved. Ordinary Posts follow Field membership; admitted
  Constant Posts last for life under STEP-SPEC-61.
- **Python interruptions:** “Stop and preserve interruption” was approved
  for a Record initializer or Imprint raising `KeyboardInterrupt`,
  `SystemExit` or another `BaseException` outside ordinary `Exception`.

Drafts [#324](https://github.com/JulTob/Tag_Oriented_Programming/pull/324) and
[#370](https://github.com/JulTob/Tag_Oriented_Programming/pull/370) preserve
earlier proposal work. Their text or draft status supplies no additional
clearance. The rulings recorded above are the basis of this amendment.

#### Amended rules

1. **Each missing Tag takes a complete independent turn.** Source validity,
   structural preparation and its Pre Services precede its Gains. After its
   training attempt, it enters its own Field and all current visible Posts
   are inspected before the next Tag's turn. A Form orders these Taggings;
   it does not defer a Base's promise until a later Shape supplies a repair.
   Earlier admitted Tags remain when a later turn refuses or fails.
2. **Fresh Tagging requires a valid source.** An existing Agent's current
   Posts must hold before a missing Tag's Gate can run. A broken source is
   refused without evaluating that Tag's Pres, running its initializers or
   Imprints, acquiring its Gains, or entering its Field. A retained false
   Constant Post also blocks reapplying a previously Ripped Tag. Existing
   explicit repairs must restore validity first.
3. **Structural preparation is the zero step.** Check every Record space
   required by this Tag before installing any of its Gains or running any
   initializer. If the Target cannot carry those spaces or its initial Agent
   representation, refuse it with `TagTargetError`, a `TagCompositionError`
   subtype. This Tag gains nothing and stays outside its Field; failed
   provisional Host preparation is restored. Earlier completed Tags remain.
   This restoration is about TOP's preparation, not arbitrary Python effects.
4. **Gainings retain declaration order.** Actions, Record initializers, Post
   definitions and deletions take their positions top to bottom. Successfully
   acquired Gains are visible to later declarations. A Record initializer
   calculates its initial value from the information available at that point;
   it follows the ordinary training-failure rule below, not structural
   refusal merely because its calculation raises.
5. **Ordinary training failure does not stop later training.** An ordinary
   `Exception` while calculating or applying a Record's initial value emits
   its own named `TrainingWarning.<RecordName>` and leaves the previous
   binding, or absence, unchanged. It establishes no new Constant Record
   binding. Later Gainings continue. An ordinary failed Imprint likewise
   emits `TrainingWarning.<ImprintName>` and later Imprints continue in their
   declared order. `TrainingWarning` is also exported as
   `TagTrainingWarning`; each warning identifies its Tag and training kind.
6. **Admission follows the training attempt.** Ordinary initializer or
   Imprint exceptions do not by themselves prevent FieldAdding. Membership
   and has-been history are established together. During training, this Tag's
   Field membership, published Reports and Operations, and Agent-bound view
   remain unavailable through the Agent. They become available at admission.
   Structural failure that prevents admission is a distinct boundary: it can
   leave actually acquired non-Post Gains on a Rogue, while provisional Posts
   are discarded under STEP-SPEC-61.
7. **Current Posts determine the admitted Agent's validity.** Inspect every
   current visible Post and report every failed name in evaluation order.
   Report each ordinary training failure separately. If Posts pass, return
   the sound Agent despite those training warnings. If Posts fail, retain
   membership and raise one final Postcondition Failure: the existing named
   exception for one failed Post, or `TaggingFailure` for several. A
   non-boolean condition result remains a Contract Failure. Training warnings
   are reported after admission and Post inspection; promoting warnings to
   exceptions does not undo membership.
8. **Declaration is not an implicit requirement.** A missing optional Record
   or Action and a historical training exception do not independently make
   the Agent invalid. Posts express requirements. An Imprint may deliberately
   end an ordinary Post; the final inspection judges the Posts currently
   visible, rather than requiring every declared Post to remain. An admitted
   Constant Post retains its separately defined protection and lifetime.
9. **Interruption stops training and keeps its identity.** A Python
   interruption from a Record initializer or Imprint stops later training
   immediately. After successful structural preparation, TOP still attempts
   admission and inspects the Posts actually acquired, then propagates the
   original interruption. Post failures or later diagnostics must not replace
   it. Declarations never reached before the interruption are not invented.
10. **A new training attempt is explicit.** Calling the same Tag during its
    current training or while it is already active remains a no-op, including
    for a defective member. It does not silently run recovery or retrain.
    Rip followed by a later Tagging starts a new attempt if the remaining
    Contract is valid; successfully established Constants remain protected.
    Proposed `@Fix` protocols and recovery-call syntax remain separate design
    work.

#### Effect on the retained text

The original Specification items 5–7 and 9, their whole-Form rationale,
failure compatibility statements and corresponding acceptance wording are
superseded where they contradict these amended rules. In particular, an
ordinary failed initializer or Imprint is no longer evidence of an unfinished
Rogue, and a Tag's Posts no longer wait for the whole Form. The original
declaration-order visibility and same-Tag no-op rulings remain in force.
STEP-SPEC-61 continues to govern condition lifetimes; this amendment does not
make Pres into Gains or provisional Posts into lifetime obligations.

The matching Specification update belongs with the implementation. Its
affected sections are
[§0.6, The tagging sequence](../../spec/SPECIFICATION.md#06-the-tagging-sequence),
[§1.3, Records](../../spec/SPECIFICATION.md#13-records),
[§2.3, Imprints](../../spec/SPECIFICATION.md#23-imprints-the-writing),
[§2.4, Postconditions](../../spec/SPECIFICATION.md#24-postconditions-the-promise)
and [§2.6, Naming the culprit](../../spec/SPECIFICATION.md#26-naming-the-culprit).
The **Contract** remains the bond between Agent and Agency: Pres are transient
Tagging Services, ordinary Posts are membership-bound Agent Gains, and
admitted Constant Posts are lifetime Contract terms.

#### Amended acceptance requirements

- A missing Tag on a broken source refuses before its Pre Services or Gains;
  an already active same-Tag call remains a no-op.
- A Base's failed Posts stop the Form before the next Shape's Gate while
  preserving that admitted Base and earlier completed Tags.
- An unsuitable later Record space prevents every Gain of this Tag and
  restores provisional Host preparation, with `TagTargetError` identifying
  structural refusal.
- Each failed ordinary Record initializer or Imprint gets its own named
  warning; later training still runs, successful Gains remain visible, and
  failed Record initialization preserves its old binding or absence.
- Field admission and history follow the attempt; current passing Posts
  permit return with warnings, and failed Posts retain membership while the
  final error names every failure.
- Interruptions stop subsequent training, still attempt admission and Post
  inspection, and propagate unchanged. A failure preventing admission
  discards provisional Posts under STEP-SPEC-61.
- The independent oracle, focused runtime tests, Specification and guides
  describe the same rules, including explicit Rip before fresh training.
