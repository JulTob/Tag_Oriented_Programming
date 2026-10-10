# STEP-SPEC-34: Constant Contributions

- **STEP:** SPEC-34
- **Desk:** spec
- **Title:** Constant Contributions
- **Author:** Codex, recording the Director's approved design
- **Status:** Cleared
- **Created:** 2026-10-09

## Summary

`@Constant` fixes a named Contribution's binding once it is established.
Records, Actions, Posts, Reports and Operations can be Constant. The
protection survives later Layers and Rip while preserving each
Contribution kind's ordinary scope and call behavior.

## Motivation

Some Agent capabilities and promises form a lasting contract. Ordinary
Overlay permits a later Layer to replace, extend or delete them, and Rip
normally removes a Tag's Contributions. Hiding a protected Contribution
behind a different kind or through a Shape would make the guarantee
illusory. TOP needs one explicit declaration that says the binding cannot
be crushed while leaving mutable values and executable behavior useful.

## Specification

1. `@Constant` may mark a named Record, Action, Post, Report or Operation.
   It stacks with that declaration's modifiers in either order. An
   unqualified method remains an Action. `@Public` and `@Secret` retain
   their independent meanings. A Precondition alone, an Imprint, a Rip or
   a Delete cannot be Constant.
2. Constant fixes the **binding**, not the object held by the binding. A
   Constant Record is initialized separately for each Agent. Its value may
   be mutable, but the Agent cannot assign another value to that name or
   delete it. A Constant Action or Operation keeps its implementation and
   continues to perform work normally.
3. A Constant Report belongs to its declaring Tag. Its builder runs lazily
   once for that Tag, even when the first read comes through a Shape. The
   declaring Tag and every Shape read the same value and object. A Constant
   Operation still receives the Tag through which it is called.
4. A Constant Post keeps its original check. It cannot be replaced,
   extended with an Underlay, deleted by a Layer or ended through
   `Contract.Delete`. Other Posts may be added under other names, and all
   applicable checks continue to judge current Agent state. When a
   condition is both a Precondition and Postcondition, Constant protects
   the Postcondition; a Precondition alone is not a lasting binding.
5. Protection is independent of Contribution kind. Direct assignment and
   deletion, a later Overlay, `@Delete`, `@Underlay`, Pin publication and
   Pin patching cannot replace or hide a Constant name. A failed attempt
   raises the applicable Declaration or Composition Failure and leaves the
   protected binding and Fields unchanged.
6. A Shape cannot redeclare or mask a Base's Constant. Multiple inheritance
   and late changes to a Base or Pin must also preserve the effective
   Constant seen by every existing Shape. A diamond that reaches the same
   Constant declaration through both arms is valid.
7. Rip ends the Tag's Field membership and ordinary Contributions as usual,
   but established Constant Agent bindings and Constant Posts remain.
   Reapplying the same declaration retains those Constants without running
   their builders again; ordinary Records rebuild and Imprints run again.
8. The guarantee covers TOP composition and normal Python member writes,
   including `object.__setattr__` on an Agent. It is not a sandbox against
   deliberate mutation of TOP's private runtime state or direct namespace
   tampering.

## Rationale

The modifier names a semantic property of the Contribution rather than a
new Contribution kind. This lets an Action later become a Record without
changing how the protection is expressed. Fixing the binding keeps the
useful Python distinction between a stable reference and immutable data.

Reports follow their declaration because a Shape-specific value would let
inheritance manufacture multiple supposedly fixed bindings. Posts persist
after Rip because their purpose is to hold the Agent to a lasting contract;
programmers can express any intended release inside the original check.

## Backwards compatibility

Existing unmarked Contributions keep their current Overlay and Rip
behavior. Programs opt into the new restriction with `@Constant`.
Composition that previously replaced a newly marked name now raises a
Failure and must instead use a different name or leave the declaration
non-Constant.

## Alternatives considered

- A `constant def` statement was set aside because it would require a new
  Python grammar rather than compose with TOP's declaration modifiers.
- Deeply freezing Record and Report values was rejected; arbitrary Python
  objects do not share one useful definition of deep immutability.
- One Constant Report value per Shape was rejected. All Shapes read the
  declaring Tag's single fixed value.
- Anonymous or merely lambda-based permanence was set aside. Permanence is
  explicit through `@Constant`, while a named Post remains inspectable.

## Validation

The implementation has 33 focused regressions covering every supported
kind and modifier order, mutable values, Rip and reapplication, direct and
host-defined writes, Pins, publication, Secret access, presence queries,
multiple inheritance and late Shape masking. The full suite passes on
Python 3.12 and 3.13, along with 60,000 randomized oracle transitions and
the relevant tagging, Rip and Record-write performance budgets.

### Decision

The Director specified that a Constant binding is uncrushable: it cannot
be overwritten, redefined or deleted from the Agent from that point on,
while a stored mutable value may still mutate. The Director further chose
`@Constant`, required protection for Records, Actions, Posts, Reports and
Operations, and clarified that a Constant Report is completely fixed:
both a Base and its Shapes read the Base's one value. On 2026-10-09 the
Director approved the reviewed and tested implementation for push. This
records that accepted design as **Cleared**; it adds no separate decision.
