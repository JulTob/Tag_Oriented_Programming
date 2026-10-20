# STEP-SPEC-45: The Live Base Report Link

- **STEP:** SPEC-45
- **Desk:** spec
- **Title:** The Live Base Report Link
- **Author:** Codex, recording the Director's 2026-10-15 ruling
- **Status:** Brief
- **Created:** 2026-10-15

## Summary

A Shape may declare its own two-parameter `@Report` to link explicitly to
the current value of a same-named Base Report. An ordinary linked Report
recalculates on every read. A `@Constant @Report` keeps its first calculated
value; a one-parameter Report keeps its ordinary once-per-Tag calculation.

## Motivation

Today a two-parameter Report calculates only on its first read of each Tag.
If the Base Report later changes, the Shape's calculated value stays stale.
When a Pin has supplied the Base Report, the calculation can even receive
the Pin's descriptor instead of its value. Both results defeat an explicit
link to the Base's current information. This STEP concerns the Shape's own
Report, within the Tag scope settled separately in #230.

## Specification

1. A Shape that declares `@Report def name(tag, base_value)` owns `name`.
   Its second input is a **Base Report link**: the current value of the
   eligible same-named Base binding found in TOP's existing Base search
   order. An eligible binding is a Base's current Report, including a Pin
   Record or an ordinary value written over that Report. A same-named
   Action or Operation is not a Report: if it replaces the nearer Base's
   Report, the link searches for the next eligible Base Report. It never
   passes the Action or Operation object to the builder. The declaration
   does not place a Report on another Tag. A Shape with no own `name` has
   no direct `Shape.name` Report merely because a Base declares one.
2. On each permitted read of an ordinary linked Report, TOP resolves the
   current Base binding, reads its value, and calls the Shape's builder
   again. Rebinding the Base Report and mutating an object held by it are
   both visible to the next Shape read. A Pin-supplied Report contributes
   its current value, never its Python descriptor object.
3. If the chosen Base binding is deleted, the next eligible current Base
   binding in that same search order supplies the value. Deletion and
   Pinning do not reorder the Agent's Tagging Overlay.
4. A Shape-owned `@Constant @Report` with a Base Report link calculates
   once, on its first permitted read, and keeps that resulting binding
   fixed when the Base later changes. As with other Constant values,
   mutating the held Python object remains possible; Constant does not
   deep-freeze it (STEP-SPEC-34).
5. A one-parameter `@Report def name(tag)` still calculates once per Tag
   on first read. `@Public` still controls whether an Agent can read the
   Report directly. This STEP does not change Agent Overlay order, Report
   deletion, or which Tag owns a Pin-supplied Report.

```python
class Inventory(Tag):
    @Report
    def supplies(tag):
        return []

class Packed(Inventory):
    @Report
    def supplies(tag, base_value):
        return len(base_value or [])

class FixedCount(Inventory):
    @Constant
    @Report
    def supplies(tag, base_value):
        return len(base_value or [])

assert Packed.supplies == 0
assert FixedCount.supplies == 0
Inventory.supplies.append("rope")
assert Packed.supplies == 1       # the Base Report link recalculates
assert FixedCount.supplies == 0   # Constant keeps its first result
```

If a nearer Base's `signal` Report is replaced by an Operation named
`signal`, a Shape's explicit `signal` link reads a deeper Base's current
`signal` Report, when one exists. It must not receive the Operation object.

## Open question

If no eligible Base Report remains, should the builder receive `None`, as
today's calculation does, or should the read fail? A real Report may itself
hold `None`, so the answer cannot be inferred from that value. This Brief
does not settle the missing-link behavior.

## Rationale

The second builder input is an explicit link to a Base's current Report,
so recalculation makes its meaning consistent with the value the Base
answers now. It also lets a Shape derive a different value without copying
the Base's declaration or making all Reports eager. Constant provides an
explicit fixed result when that is the author's intent.

## Backwards compatibility

An ordinary two-parameter Report may now call its builder more than once
and may return a different value after a Base change. Builders that need a
fixed result can use `@Constant` if the protected binding is appropriate.
Existing one-parameter Report calculations and Constant binding rules do
not change. The runtime and guide still describe the earlier calculation
until #231 is implemented; this Brief records the proposed rule only.

## Alternatives considered

- Keep the first calculated value for every linked Report: leaves a Base
  change invisible through an explicit link.
- Recalculate every Report: changes ordinary one-parameter builders with
  no Base link and loses their once-per-Tag behavior.
- Make Constant linked Reports follow Base changes: conflicts with the
  fixed Report binding chosen in STEP-SPEC-34.
- Copy Base Reports into Shapes: gives the Shape a member it did not
  declare and obscures which Tag supplies the value.

### Decision

On 2026-10-15 the Director ruled that ordinary Shape-owned Base Report
links recalculate on every read, including after Base rebinding or in-place
mutation, and that `@Constant` keeps the first calculated value. This
Brief records that direction. STEP clearance and implementation remain
separate review steps.
