# STEP-SPEC-54: Best-Effort Imprints and Admission

- **STEP:** SPEC-54
- **Desk:** spec
- **Title:** Best-Effort Imprints and Admission
- **Author:** Codex, recording the Director's 2026-10-20 rulings
- **Status:** Brief
- **Created:** 2026-10-20
- **Issue:** [#368](https://github.com/JulTob/Tag_Oriented_Programming/issues/368)
- **Amends, if cleared:** [STEP-SPEC-39](STEP-SPEC-39-tagging-admission.md), rules 4, 6, 7 and 9; [STEP-SPEC-8](STEP-SPEC-8-named-failures.md), Imprint failure delivery

## Summary

An ordinary Imprint failure is a failed **training step**, not a failed
attempt to make an Agent a member. TOP continues later Imprints, admits the
Agent to this Tag's Field, and judges its current Posts. It warns separately
for each failed Imprint. Passing Posts leave a sound Agent and Tagging
returns it; failing Posts produce one final Tagging Failure that names every
failed Post. This Brief records the Director's new rule but changes no
runtime or current Specification by itself.

## Why this amends the existing rule

STEP-SPEC-39 currently says an Imprint that raises leaves a Rogue outside
the Field. The Director revised that distinction: a car leaving its factory
with a failed training step is still a car. It is in the Agency and its Posts
say whether it is sound. A structural failure to prepare a Target is a
different boundary, to be decided and implemented separately.

## Proposed behavior

1. Keep the Tag's ordered **Gate → Gainings → Imprints → Field → Posts**
   sequence. A refused Gate does not start this Tag. Gainings acquired before
   training remain visible to later Gainings. Earlier completed Tags remain
   independent.
2. If an Imprint raises an ordinary Python `Exception`, retain its effects,
   record the failure under that Imprint's declared name, and run each later
   Imprint in declaration order. Do not silently replay or roll back a
   completed training step.
3. After the Imprint sequence, admit the Agent to this Tag's Field even if
   one or more Imprints failed. Judge every currently visible Post. Posts
   that an Imprint deliberately ended are absent unless protected by
   `@Constant`; the declared list is not itself an automatic requirement.
4. Issue a named training warning for each failed Imprint, in declaration
   order, with its protocol name and failure type and message available for
   diagnosis. If the Posts hold, return the sound Agent. One ordinary false
   Post keeps its existing `Postcondition.Name` failure regardless of whether
   training also failed. Several false Posts produce one final Tagging Failure
   naming **all** failed Posts in evaluation order. The admitted Agent
   remains in the Field's broken population. A Tag with no Posts is sound by
   the ordinary vacuous contract rule.
5. A Python `BaseException` outside ordinary `Exception`, including
   `KeyboardInterrupt` and `SystemExit`, stops later training. If structural
   preparation succeeded, admission and Post inspection still occur, but
   neither a Post result nor a training diagnostic replaces the original
   interruption when it is re-raised.
6. The same per-Tag-turn Post timing applies to a Form: finish this Tag's
   admission and Post check before the next Shape's Gate. That timing is
   recorded separately in [STEP-SPEC-53's proposal](https://github.com/JulTob/Tag_Oriented_Programming/pull/370)
   and [#369](https://github.com/JulTob/Tag_Oriented_Programming/issues/369).

## Failure vocabulary

The Director chose a warning named by each failed training protocol and one
final error when several Posts fail. `TrainingWarning.Arm` and
`TaggingFailure` are proposed Python spellings, not exported APIs today.
STEP-SPEC-8 currently requires a failed `@Imprint Arm` to raise `Imprint.Arm`;
this Brief proposes changing that delivery during Tagging while retaining
the named single-Post failure. STEP-SPEC-8 also registers `Imprint.Arm` at
declaration time as an alias of a named error. Whether that historical error
alias stays available for explicit use or changes is unresolved; it must not
silently become a warning class. Diagnostics should not retain an Agent
solely through an exception traceback; exact cause storage is unresolved.

## Scope and open diagnostic detail

This STEP concerns ordinary **Imprint** exceptions only. Record initializer
failures need the same training treatment under a separate Record STEP, but
structural Record-space preflight and a proposed `TagTargetError` come first.
Refusing a new unrelated Tagging on an unsound Agent and `@Fix` recovery on
an existing Tag are separate changes. This STEP does not make any new Tag
silently repair another Tag's broken member.

If a Post returns a malformed verdict or violates its observational rule,
whether inspection continues to later Posts or stops immediately remains
open. Ordinary false Post verdicts are fully specified here. A warning
filter that converts a training warning into an exception also needs an
implementation rule so it cannot skip Field admission.

## Acceptance requirements

Test two failing Imprints followed by a successful one; warnings in declared
order with each name and failure type/message available; passing Posts
returning a sound admitted Agent; one false Post keeping its named failure;
several false Posts producing one final error while preserving broken Field
membership; a later
Shape not starting after that Post failure; and interruption preserving its
original Python type.
The independent Tagging oracle and public guide examples should change with
the runtime implementation, not with this Brief.

---

### Decision

> **Brief.** The Director revised failed-Imprint admission on 2026-10-20:
> continue later Imprints, admit the Agent, warn for each failed training
> step, then judge Posts. Formal clearance and runtime implementation remain
> separate review steps.
