# STEP-SPEC-44: The Null Action Underlay

- **STEP:** SPEC-44
- **Desk:** spec
- **Title:** The Null Action Underlay
- **Author:** Codex, recording the Director's Action Underlay ruling
- **Status:** Cleared
- **Created:** 2026-10-15

> **Pin declaration migration — 2026-10-21.** The example below preserves
> its original Pin declaration. Under the approved API, replace
> `@Pin class Patch(Tag)` with `class Patch(Pin)`; `Patch(Shape)` and the
> null Action Underlay rule are unchanged. See the amendment to
> [STEP-SPEC-9](STEP-SPEC-9-tags-as-targets.md).

## Summary

An `@Underlay` Action can be the first Action of its name. Its prior Action
is a callable null Action: calling it does nothing and returns `None`.

## Specification

1. When an Action asks for an Underlay and no earlier Action exists in
   that Agent's current Overlay, it receives a callable null Action. The
   callable accepts forwarded or explicit positional and keyword arguments,
   performs no work, and returns `None`.
2. The null Action is captured when that Layer applies, like an ordinary
   Underlay. A later Overlay does not change what the Layer calls.
3. This rule covers ordinary Action Gainings, Pin Actions on Tag Targets,
   Actions marked `@Rip`, and special-method Actions. It applies after an
   earlier Action was removed by `@Delete` as well as when none was ever
   present. A Pin over a Shape with no Action of that name can therefore
   extend the null Action. Which Tag-scope declaration a Pin sees as an
   earlier Action follows the separate Tag-scope rule; this STEP does not
   define Python class inheritance as TOP layering.
4. The Action's own return is whatever its author returns. The null Action
   does not give `None` to a Record builder or a condition. Records already
   receive a stored value or `None` under STEP-SPEC-5. A Precondition or
   Postcondition with `@Underlay` still requires an existing condition;
   this STEP does not weaken that contract rule.

```python
class Visitor(Tag):
    @Underlay
    def Greet(agent, prior, name):
        previous = prior(name)  # None on the first Greet layer
        return f"Hello, {name}" if previous is None else f"{previous}; hello again"

class Base(Tag):
    pass

class Shape(Base):
    pass

@Pin
class Patch(Tag):
    @Underlay
    def Inspect(tag, prior):
        return prior()  # None when Shape has no earlier Inspect Action

Patch(Shape)
```

## Rationale

An Overlay can extend nothing without pretending that a missing Action
exists. The author decides whether the null result is useful, as with a
Record's `None` stored value. TOP does not need an automatic refusal at
Tagging merely because the author wrote an Action that accepts `prior`.

## Compatibility

This supersedes STEP-SPEC-5 item 5 and Specification §1.2's former
Tag Resolution Failure for a missing Action Underlay. Such a Tag now
applies. If its Action assumes a non-`None` result, that Action may fail
when called; the author can handle the null result explicitly. Other
Action collision, Constant, warning and declaration rules stay in force.
STEP-SPEC-18's historical comparison with other Actions predates this
rule; its `__del__` null floor remains valid.

### Decision

On 2026-10-15 the Director selected a callable null Action for a first
`@Underlay` Action **everywhere for Actions**, including ordinary Tag and
Pin Gainings. This decision does not change condition Underlays.
