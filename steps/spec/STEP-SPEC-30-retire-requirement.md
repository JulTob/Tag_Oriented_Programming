# STEP-SPEC-30: Retire `@Requirement`

- **STEP:** SPEC-30
- **Desk:** spec
- **Title:** Retire `@Requirement`
- **Author:** Codex, recording the Director's approved design
- **Status:** Cleared
- **Created:** 2026-10-09

## Summary

`TopKit.Requirement` is removed. A condition that is necessary both to
enter a Tag and to remain sound is declared with `@Pre` and `@Post`
stacked on the same function. Either decorator order has the same meaning.

```python
class Crew_Member(Tag):

    @Pre
    @Post
    def Alive(agent):
        return agent.alive
```

## Specification

1. `Requirement` is absent from `TopKit`, `TopKit.__all__` and the
   declaration API. It is removed at once, without a warning release.
2. `@Pre` and `@Post` may be stacked in either order on one condition.
   This is the sole spelling for a claim that must hold at the door and
   afterwards.
3. The two moments keep their distinct failure names. A refusal at the
   door raises `Precondition.Name`; a later failed promise raises
   `Postcondition.Name`. There is no third Requirement failure.
4. No contract semantics change. Stacking the existing marks already
   produced one condition in both the Precondition and Postcondition
   protocols.

## Rationale

The two marks expose both parts of the contract on the page. A separate
word added no behavior and obscured whether a condition gates Tagging,
judges later soundness, or both.

## Backwards compatibility

`from TopKit import Requirement` now raises `ImportError`. Replace every
`@Requirement` with `@Pre` and `@Post` on the same function. Code that
catches `Precondition.Name` or `Postcondition.Name` is unchanged.

## Validation

The tests exercise both decorator orders, the two distinct named failures,
explicit condition deletion, condition-member reads and removal from the
public API. The example, oracle and differential fuzz program use only the
stacked spelling.

### Decision

The Director said: “@Requirement is not maquing it for me as a special
word. I think we could go back to just using @Pre and @Post simultaneously,”
then decided: “remove @Requirement at once.” This STEP records that accepted
design as **Cleared**; it adds no separate decision.
