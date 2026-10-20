# STEP-SPEC-55: Prepare Record Spaces Before Gainings

- **STEP:** SPEC-55
- **Desk:** spec
- **Title:** Prepare Record Spaces Before Gainings
- **Author:** Codex, recording the Director's 2026-10-20 ruling
- **Status:** Brief
- **Created:** 2026-10-20
- **Issue:** [#374](https://github.com/JulTob/Tag_Oriented_Programming/issues/374)
- **Related draft:** [#324](https://github.com/JulTob/Tag_Oriented_Programming/pull/324) bundled this boundary with other Tagging changes; this STEP extracts the Record-space decision only.
- **Amends, if cleared:** [STEP-SPEC-39](STEP-SPEC-39-tagging-admission.md), the preparation boundary before Gainings; respects [STEP-SPEC-37](STEP-SPEC-37-host-actualization.md)'s bounded Host restoration.

## Summary

After a Tag's Gate passes, TOP checks that the Target can physically hold
every Record space this Tagging needs **before it acquires any of this Tag's
Gainings**. This is a zero step: it does not calculate or store Record values.
If the space cannot be prepared, TOP restores this attempt's provisional
Target representation and bindings, leaves the Tag unadmitted, and raises
`TagTargetError`, a public kind of `TagCompositionError`. Earlier completed
Tags remain in place. This Brief does not change the runtime by itself.

## Motivation

A Record builder calculates a value during training. A Target that cannot
hold the Record at all is a different failure: it cannot start this Tagging.
Finding that out only after an earlier Action or Post has stuck creates
partial training for an unsuitable Target. Conversely, running a builder as
a test of space may perform calculations or read changing inputs and would
confuse a failed calculation with a structural refusal.

## Proposed specification

1. For each Tag turn, run its Gate first. Before that Tag's first Gaining or
   Imprint, check the physical storage needed for **all Record bindings this
   application must establish**, without calling their builders or assigning
   their calculated values. This check does not change the declaration order
   in which actual Gainings later become visible.
2. If a needed Record space cannot be provided, this Tag acquires no Gains,
   runs no Record initializer or Imprint, and enters no Field. Restore the
   Target's provisional runtime type, instance dictionary and supported
   slot bindings to their state before this Tag's preparation. Earlier
   completed independent Taggings and their bindings stay in place.
3. Report this structural refusal as public `TagTargetError`, a subtype of
   `TagCompositionError`. Name the Tag and Record space that cannot be
   prepared. Preserve an underlying Host refusal as the cause when one was
   raised. A later Record *value* calculation or application failure is a
   training failure, not this target error; its handling belongs to the
   separate [Record initializer issue #375](https://github.com/JulTob/Tag_Oriented_Programming/issues/375).
4. The restoration boundary is the bounded one in STEP-SPEC-37: physical
   representation and bindings, not a deep copy of mutable values or a
   reversal of external Python effects. A generated frozen dataclass remains
   eligible where TOP can provide the Record space through its supported
   kernel path. Frozen status by itself is not a structural refusal.

General Host actualization failures remain STEP-SPEC-37 Composition Failures.
Whether they should also use `TagTargetError` is outside this Record-space
proposal.

For example, if `Car` declares `@Action Start` before `@Record wheels`, and
the Target's Host reserves `wheels` in a protected slot, `Car(target)` must
fail before `Start` sticks. If `Base(target)` completed first, Base remains
applied. If the Target can hold `wheels` but its builder raises while
calculating a value, this STEP's structural refusal does not apply.

## Open Gate ordering detail

This Brief proposes a successful Gate before the zero step. Current TopKit
checks ordinary Record conflicts during `_gate` before it evaluates that
Tag's `@Pre`. If both a Precondition would refuse and a Record space is
missing, the choice changes which failure the caller sees; neither order
would acquire a Gain. The Director still needs to settle that diagnostic
priority before this STEP is Cleared.

## Rationale

Space and value are separate questions. The zero step makes a physically
unsuitable Target an early, bounded refusal while preserving the ordinary
top-to-bottom visibility of real Gainings. Keeping `TagTargetError` under
`TagCompositionError` lets existing composition handlers catch it and gives
the caller a more precise reason.

## Backwards compatibility

Main already refuses a Record over a Host property or slot during the Gate,
before Gainings. The new subtype makes that refusal more precise, and the
zero-step rule extends the early check to every Record space the application
needs. A structural refusal discovered later on some other path would now
occur before any Gain of this Tag. Callers catching `TagCompositionError`
continue to catch the new subtype. This STEP does not make every frozen Host
invalid and does not turn a builder's own exception into `TagTargetError`.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Discover missing space while applying Records in declaration order | Rejected: an earlier Gain may already have stuck before structural refusal |
| Call Record builders during preparation | Rejected: calculation is training, and the test could itself cause effects or fail for a nonstructural reason |
| Roll back all Python effects after refusal | Rejected: STEP-SPEC-37 limits restoration to physical representation and bindings |
| Treat every frozen Host as unsuitable | Rejected: TOP already supports compatible frozen dataclasses |

## Acceptance requirements

Check every required Record space before the first Gain or Imprint. Cover a
protected Host slot, a compatible frozen dataclass, and a later failing Tag
in a Form whose earlier Tags remain. Verify restoration of provisional
runtime type and bindings, zero builder calls on structural refusal, the
public `TagTargetError` subtype and cause, and existing Host actualization
and performance budgets.

---

### Decision

> **Brief.** The Director distinguished Record-space preparation from
> Record-value training on 2026-10-20. Formal clearance and runtime
> implementation remain separate review steps.
