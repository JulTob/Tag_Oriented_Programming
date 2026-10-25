# STEP-SPEC-56: Record Initializers as Training

- **STEP:** SPEC-56
- **Desk:** spec
- **Title:** Record Initializers as Training
- **Author:** Codex, recording the Director's 2026-10-20 rulings
- **Status:** Brief
- **Created:** 2026-10-20
- **Issue:** [#375](https://github.com/JulTob/Tag_Oriented_Programming/issues/375)
- **Historical bundled draft:** [#324](https://github.com/JulTob/Tag_Oriented_Programming/pull/324)
- **Amends, if cleared:** [STEP-SPEC-39](STEP-SPEC-39-tagging-admission.md), the Record failure boundary; [STEP-SPEC-36](STEP-SPEC-36-tools.md), the *initial* Tool-value failure boundary

## Summary

A declared `@Record` calculates its initial value at its place among the
Tag's Gainings. If that calculation or application fails ordinarily, this
Record has not been gained. TOP warns under its declared name and continues
later Gainings and Imprints. Once structural preparation has succeeded, that
training failure does not prevent Field admission: the Agent's current Posts
judge it. This Brief extracts the Record-value ruling from draft #324; it
does not change current law or runtime by itself.

## Motivation

The current [STEP-SPEC-39](STEP-SPEC-39-tagging-admission.md) puts failed
Record Gainings outside the Field as Rogue attempts. The Director has since
distinguished the ability to hold a Record's **space** from the calculation
of its **initial value**. A Target without the required space cannot start
this Tagging. A failed calculation is one failed training step: later
training can still produce an admitted Agent whose Posts say whether it is
sound. Structural preparation is the separate proposal in
[#374](https://github.com/JulTob/Tag_Oriented_Programming/issues/374).

## Proposed behavior

1. After the Gate and successful structural Record-space preparation, run
   Gainings in their declared top-to-bottom order. A `@Record` initializer
   reads current values and may call query Actions to calculate its initial
   value. Successful earlier Actions and Records are visible to each later
   Gaining. The prior stored value passed to an extending Record still follows
   [STEP-SPEC-5](STEP-SPEC-5-stored-records.md).
2. An ordinary Python `Exception` while calculating, validating, or applying
   a Record value fails **that Record's training step**. It establishes no
   new Record value, Record layer, `@Constant` binding, or `@Tool` binding.
   The previously available value or Contribution at that name stays at its
   earlier layer; if none existed, the failed Record is absent. A returned
   `None` is a value, not an exception, subject to any declared Tool rule.
   For an `@Tool` Record, validating the initializer's returned kind belongs
   to this training step. An invalid initial kind leaves the earlier binding
   in place, warns under this Record's name, and allows later training.
   Assignment to an already gained Tool retains STEP-SPEC-36's existing
   Composition Failure rule. Malformed declarations retain their Declaration
   Failure rule; this proposal does not turn every TOP error into a warning.
3. Keep successful earlier Gains. Continue the later Gainings in declaration
   order and then the Imprints. Later declarations see all successful earlier
   Gains and do not see the failed Record's unestablished value. No failed
   initializer is silently retried during this Tagging.
4. Report each failed Record with its own **named training warning**, in
   failure order with other failed training steps. The diagnostic identifies
   the `Record` kind, its declared name, and the failure's type and message.
   Reporting must not prevent later training, Field admission, or Post
   judgment. The diagnostic need not retain the traceback frames, which can
   keep the Agent alive. The concrete warning class and delivery rule are
   shared with the best-effort Imprint proposal
   [#368](https://github.com/JulTob/Tag_Oriented_Programming/issues/368).
5. With structural preparation complete, Field admission follows the
   training attempts even if a Record initializer failed. Judge the Agent's
   **current visible Posts**. Passing Posts allow Tagging to return a sound
   Agent; failed Posts leave an admitted broken member. One ordinary false
   Post keeps its existing named failure; the proposed aggregate for several
   false Posts belongs to [#368](https://github.com/JulTob/Tag_Oriented_Programming/issues/368).
6. A Python interruption outside ordinary `Exception`, including
   `KeyboardInterrupt` and `SystemExit`, stops later training. If structural
   preparation succeeded, admit the Agent and inspect its Posts, then
   propagate the original interruption without replacing its type. The
   interruption does not establish the unfinished Record.

Record initializers remain observational authoring protocols: they may
calculate from reads and query Actions, but Tagging and Rip are Imprint work.
TOP does not promise to undo arbitrary effects that author-supplied Python
code caused while calculating a value. This proposal protects TOP's own
Record binding and the earlier layer from a failed initialization.

## Boundary and dependencies

[#374](https://github.com/JulTob/Tag_Oriented_Programming/issues/374)
separately proposes checking **all required Record spaces before any Gain**
and using `TagTargetError` for structural refusal. It is not a Record
initializer warning. That boundary must be settled before this behavior can
be deployed. The Imprint continuation and warning delivery are separately
proposed in [#368](https://github.com/JulTob/Tag_Oriented_Programming/issues/368).
STEP-SPEC-36 currently calls an invalid initial Tool value a Composition
Failure and leaves the Tag outside its Field. This Brief proposes changing
that *initial* check to a training warning while leaving subsequent Tool
assignment refusal intact; STEP-SPEC-36 must be amended if this is cleared.
Checking Posts at each admitted Tag turn before the next Shape's Gate is the
separate [#369](https://github.com/JulTob/Tag_Oriented_Programming/issues/369)
decision, not a new timing rule in this STEP.
This STEP neither decides failures of non-Record Gainings nor introduces
`@Fix`, changes the Gate, or lets a new unrelated Tag silently repair an
unsound Agent.

## Backwards compatibility

An ordinary Record initializer error would no longer necessarily raise a
Composition Failure and leave this Tag unapplied. Code that catches that
error must inspect the named training warning and the admitted Agent's
current Post verdict. A failed Record remains absent or leaves the earlier
layer visible, so an author can make its presence a requirement with a Post.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Treat every Record failure as structural Target refusal | Rejected: a calculation can fail although the Target can hold the Record |
| Stop later Gainings at the first failed initializer | Rejected: a Record is one training step; later independent training can still succeed |
| Install a failed Record as `None` | Rejected: `None` is a real value and must remain distinct from absence |
| Re-run the failed initializer automatically before admission | Rejected: it could repeat calculations and effects; recovery is a separate design |

## Acceptance requirements

Cover earlier Action and Record visibility, prior value preservation,
continuation through later Gainings and Imprints, named warnings in training
order, and Field admission followed by Post judgment. Cover failed
`@Constant @Record` and `@Tool` initializers, an invalid initial Tool kind
versus a later Tool assignment, a value write that raises after
a provisional binding, nested Taggings, interruption identity, and an
independent Tagging oracle. A diagnostic captured by a warning handler must
not keep an otherwise collectible Agent alive solely through traceback
frames. Keep structural refusal and ordinary value failure distinct.

---

### Decision

> **Brief.** The Director distinguished structural Record-space preparation
> from a declared Record's value calculation on 2026-10-20. A failed value
> calculation is training: leave that Record unestablished, continue later
> training, admit after successful structural preparation, and judge Posts.
> Formal clearance and runtime implementation require separate review.
