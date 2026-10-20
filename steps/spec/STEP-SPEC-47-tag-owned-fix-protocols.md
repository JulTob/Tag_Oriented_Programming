# STEP-SPEC-47: Tag-Owned Fix Protocols

- **STEP:** SPEC-47
- **Desk:** spec
- **Title:** Tag-Owned Fix Protocols
- **Author:** Codex, recording the Director's recovery proposal
- **Status:** Brief
- **Created:** 2026-10-20
- **Depends on:** [STEP-SPEC-39](STEP-SPEC-39-tagging-admission.md) and the saved Rip work of [STEP-SPEC-32](STEP-SPEC-32-the-arrest.md)

## Summary

Propose `@Fix` as a Tag-owned recovery protocol. The Director approved both
a re-runable `@Fix @Imprint` and a standalone `@Fix`, including recovery by
the Tag that owes an arrested Agent's unfinished Rip. The proposed recovery
entry is the Tagging spelling itself, `Car(car)`: on a broken member it would
run Car's Fix protocol rather than repeat ordinary Tagging. This Brief
records that direction and the remaining execution choices. It changes no
runtime code.

## Motivation

A failed training step can leave a Car in its Field with a broken promise.
Its programmer needs a named way to complete the training without laying an
unrelated Tag over a broken Agent. A failed Rip can also leave an Agent in
the owning Tag's Safehouse: repairing a condition needed by that saved Rip
may require access to its Actions and Records before retry can succeed.

Today `Car(car)` is a no-op when Car already holds the Agent. The Director
prefers giving that same Tagging expression a recovery meaning when repair
is needed, without repeating Car's Gate, Gainings and ordinary Imprints.
Another new Tag is not an implicit repair of Car. An ordinary Action can
already repair a free Agent, but arrested Agent access is reserved for its
saved Rip work. `@Fix` would name the intentional recovery work within Car.

## Proposed language

Both decorator orders below would have the same meaning:

```python
class Car(Tag):
    @Post
    def Ignites(car):
        return car.engine_ready

    @Fix
    @Imprint
    def Calibrate(car):
        car.engine_ready = car.fuse_ok

    @Fix
    def Replace_Fuse(car):
        car.fuse_ok = True
        car.engine_ready = True

# Also proposed: @Imprint @Fix def Calibrate(car): ...
```

`Calibrate` runs at its normal Imprint turn during first Tagging. It could
also run in Car's later recovery. `Replace_Fuse` runs only during recovery;
it is a Tag-owned protocol, not a gained Agent Action. The intended recovery
expression is `Car(car)`. It would run selected Fix protocols without
repeating the Gate, Gainings, ordinary Imprints or Record initializers,
changing Field membership, or removing saved Rip work. Which Fixes it
selects is still open below.

### Receiver and permission

The proposed call is `Car(car)`, with the existing Agent as Target. If Car
already holds a sound Agent and owes no Rip, the call remains a no-op. If
Car holds a broken Agent, the call may enter Car's recovery protocol. If
Car owes that Agent a saved Rip, the call may enter Car's recovery protocol
without granting it fresh Field membership. The Fix belongs to **the Tag
that declares it**, even when that Tag is a Base in a Shape's Form:
`Shape(agent)` does not silently run Base's Fix.

Permission is checked when the Tagging expression runs:

1. A free Agent may enter a Fix of a Tag whose raw Field currently contains
   it. This uses raw membership rather than requiring soundness first: a
   repair need not satisfy the Posts it is trying to restore.
2. While an Agent is arrested, only a Tag with **its own pending saved Rip
   application** may run its Fix on that Agent. Mere membership in another
   Tag does not open recovery during someone else's arrest.
3. An Agent that neither belongs to this Tag nor owes it saved Rip work is
   refused. A structural Target refusal before Field admission creates no
   recovery claim; the programmer can repair the Target and retry Tagging.

An arrested Agent needs a narrow recovery door so the owning Fix can read
and change it and call its Actions without releasing the saved Rip. The
exact door and its interaction with automatic Rip retry remain open. It
must close on normal return, failure, or Python interruption; a copied
execution context or captured callable must not keep it open. A Fix must
finish synchronously: a returned coroutine, generator or async generator
cannot carry the recovery door beyond the call.

### Result and continued custody

A Fix changes current state; it does not certify a permanent result or
automatically check Posts after each Fix. The program may ask `bool(agent)`
or read a named condition to check repair. A Fix on an arrested Agent does
**not** release it: its original saved Rip run remains owed, and ordinary
access still retries or refuses that Rip under STEP-SPEC-32. A Fix grants
no exception to the rule that a new, unrelated Tagging starts from a sound
Agent. The programmer repairs the existing Agent explicitly, then applies
another Tag when it is sound.

An explicit recovery failure should raise `TagFixError.Name`, naming the
failed Fix and preserving its original cause. During initial Tagging,
`@Fix @Imprint` still follows the Imprint diagnostic rule. Whether one
failed Fix stops other selected Fixes remains open.

As with Imprints and Actions, effects already performed by a failing Fix
remain; there is no general rollback of Python effects. `@Fix` does not
make Record builders or Preconditions performative.

## Why a Tag-owned protocol

`@Fix` identifies which Tag is responsible for recovery. A plain gained
Action is available through the Agent's Overlay and can be replaced by later
Tags. A Fix belongs to its declaring Tag's recovery protocol even after
that Tag has revoked Field membership but still owes a saved Rip. This keeps
the Safehouse exception narrow: an unrelated Tag cannot use its own Fix to
obtain general access to someone else's arrested Agent.

The ordinary Overlay remains available for free-Agent repair Actions. A
program may deliberately make such an Action its public repair interface;
`@Fix` is the protocol entry for the cases that need Tag ownership or the
arrested-Agent recovery door.

## Open decisions for the Director

1. **Selection and Post ownership.** When `Car(car)` finds a broken Agent,
   should it run every Fix declared by Car, only Fixes explicitly tied to
   a failed Post owned by Car, or let each Fix decide whether it applies?
   Does a failure of another Tag's Post trigger Car's recovery at all?
   A Post tie needs a declaration spelling and a rule for an overlaid Post.
2. **Failure sequence.** If two selected Fixes raise, should recovery stop
   at the first named `TagFixError.Name`, or continue other Fixes and report
   both? Effects already performed remain in either case.
3. **Arrest door.** How does `Car(car)` enter Car's Fix while its saved Rip
   would ordinarily retry on access, and how does the door close without
   releasing that saved Rip? A fresh Tagging of an unrelated Tag must not
   use this door.
4. **No Fix and input routing.** If Car has no selected Fix, should calling
   `Car(car)` on its broken member remain a no-op or report that recovery is
   unavailable? If Fix protocols accept inputs, should `Car(car, part=...)`
   route those inputs to each selected Fix?
5. **Other marks and Pins.** The first implementation could accept `@Fix`
   alone or with `@Imprint`, in either order, and refuse other combinations
   until defined. Should the same protocol also repair a Tag that is an
   Agent of a Pin? The ownership and saved Rip rule can apply there, but
   its call boundary needs an explicit probe.

## Backwards compatibility

`@Fix` is new. The proposed recovery meaning would change an active,
broken member's `Car(car)` from a no-op to a deliberate Fix run. Active,
sound reapplication and in-progress same-Tag calls would remain no-ops.
The related admission and sound-source changes belong to STEP-SPEC-39,
not to this STEP. Programs using ordinary Actions to repair free Agents
can keep them. A declaration named `Fix` without the proposed decorator
remains an ordinary Action under today's scan.

## Alternatives considered

| Alternative | Assessment |
| --- | --- |
| Reapply an active Tag's full training | Would repeat its Gate, Gains and every Imprint; the proposed `Car(car)` recovery runs only selected Fix protocols. |
| Call `Car.Repair(car)` | Names a Tag member as a function, can collide with a Report, and departs from the Tagging expression already used for that Agent. |
| Automatically apply a different Tag to repair a broken Agent | Crosses the independent Tag boundary and makes the other Tag responsible for this Tag's contract. |
| Let every Tag's Fix run during any arrest | Gives unrelated Tags an access door to an Agent held by another Tag's unfinished Rip. |
| Use only Agent Actions | Useful for free Agents, but does not identify the Tag that owns saved Rip work or grant a narrow recovery door. |

---

### Decision *(to be filled by the Director)*

> Status remains **Brief**. The Director has approved the two declaration
> forms and an owning Tag's Fix during its arrest. The preferred recovery
> entry is `Car(car)`, with no automatic Post check after each Fix and a
> named `TagFixError.Name` for an explicit recovery failure. Fix selection,
> Post ties, failure sequence, Safehouse permission and Pin parity remain
> open for review.
