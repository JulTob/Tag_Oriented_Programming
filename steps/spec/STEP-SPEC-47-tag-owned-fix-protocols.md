# STEP-SPEC-47: Tag-Owned Fix Protocols

- **STEP:** SPEC-47
- **Desk:** spec
- **Title:** Tag-Owned Fix Protocols
- **Author:** Codex, recording the Director's recovery proposal
- **Status:** Brief
- **Created:** 2026-10-20
- **Depends on:** [STEP-SPEC-39](STEP-SPEC-39-tagging-admission.md) and the saved Rip work of [STEP-SPEC-32](STEP-SPEC-32-the-arrest.md)

## Summary

Propose `@Fix` as an explicit way for a Tag to repair an Agent it already
holds, or whose unfinished Rip it owes. The Director approved both a
re-runable `@Fix @Imprint` and a standalone `@Fix` protocol, including a Fix
owned by the Tag that holds an arrested Agent. This Brief records those
directions and the remaining execution choices. It changes no runtime code.

## Motivation

A failed training step can leave a Car in its Field with a broken promise.
Its programmer needs a named way to complete the training without laying an
unrelated Tag over a broken Agent. A failed Rip can also leave an Agent in
the owning Tag's Safehouse: repairing a condition needed by that saved Rip
may require access to its Actions and Records before retry can succeed.

Normal `Tag(agent)` on an active member is a no-op; it does not re-run the
Imprint. Another new Tag is not an implicit repair of this Tag. An ordinary
Action can already repair a free Agent, but arrested Agent access is reserved
for its saved Rip work. `@Fix` would name an intentional, auditable recovery
entry in that Tag.

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

`Calibrate` runs at its normal Imprint turn during first Tagging. It can also
be invoked later as a Fix for this Car. `Replace_Fuse` runs only when called
as a Fix; it is a Tag-owned protocol, not a gained Agent Action. Neither form
reapplies Car, repeats other Imprints or Record initializers, enters or leaves
the Field, or removes any saved Rip work.

### Receiver and permission

The proposed explicit call is `Car.Replace_Fuse(car)` or
`Car.Calibrate(car)`. The first argument is the existing Agent. The Fix
belongs to **the Tag that declares it**, even when that Tag is a Base in a
Shape's Form. `Base.Repair(agent)` names Base's protocol;
`Shape.Repair(agent)` would not silently take ownership of it.

Permission is checked when the call runs, including for a handle captured
earlier:

1. A free Agent may run a Fix of a Tag whose raw Field currently contains
   it. The check is raw membership, not soundness: a repair need not first
   execute the Posts it is trying to restore.
2. While an Agent is arrested, only a Tag with **its own pending saved Rip
   application** may run its Fix on that Agent. Mere membership in another
   Tag does not open recovery during someone else's arrest.
3. An Agent that neither belongs to this Tag nor owes it saved Rip work is
   refused. A structural Target refusal before Field admission creates no
   recovery claim; the programmer can repair the Target and retry Tagging.

The recommended implementation is a revocable, Agent-specific recovery
door, separate from the saved Rip door. It permits the Fix body to read and
change that Agent and call its Actions while the door is open. It closes on
normal return, failure, or Python interruption; a copied execution context
or captured callable cannot keep it open. The Fix body has the ordinary
composition access of a Tag protocol, including its Agent's Secret
Contributions. The call must finish synchronously: a returned coroutine,
generator or async generator cannot carry the recovery door beyond the call.

### Result and continued custody

A Fix changes current state; it does not certify a permanent result. Current
Posts determine whether a free Agent is now sound. A Fix on an arrested
Agent does **not** release it: its original saved Rip run remains owed, and
ordinary access still retries or refuses that Rip under STEP-SPEC-32. A Fix
also grants no exception to the rule that a new, unrelated Tagging starts
from a sound Agent. The programmer repairs the existing Tag explicitly,
then applies another Tag when the Agent is sound.

As with Imprints and Actions, effects already performed by a failing Fix
remain; there is no general rollback of Python effects. `@Fix` does not
make Record builders or Preconditions performative.

## Why a Tag-owned protocol

`@Fix` identifies which Tag is responsible for recovery. A plain gained
Action is available through the Agent's Overlay and can be replaced by later
Tags. A Fix remains named on its declaring Tag and can be reached even when
that Tag has revoked Field membership but still owes a saved Rip. This keeps
the Safehouse exception narrow: an unrelated Tag cannot use its own Fix to
obtain general access to someone else's arrested Agent.

The ordinary Overlay remains available for free-Agent repair Actions. A
program may deliberately make such an Action its public repair interface;
`@Fix` is the protocol entry for the cases that need Tag ownership or the
arrested-Agent recovery door.

## Open decisions for the Director

1. **Call spelling.** Is `Car.Repair(car)` the right Tag-owned syntax? A
   `Car[car]` view normally needs current Field membership, so it cannot
   address a member arrested after Car's Rip without changing what views
   mean. This Brief recommends the direct Tag spelling.
2. **Completion check.** Should a Fix merely perform its named work and
   leave current Posts to `bool(agent)` / ordinary contract reads, or
   immediately check them and report any still broken promise? The first
   permits several partial repairs; this Brief recommends it.
3. **Failure name.** Should a failed recovery call raise a new named
   `TagFixError.Name` with its original cause? During initial Tagging,
   `@Fix @Imprint` would use the ordinary Imprint diagnostic, not a Fix
   diagnostic. This Brief recommends the separate recovery failure name.
4. **Other marks and Pins.** The first implementation could accept `@Fix`
   alone or with `@Imprint`, in either order, and refuse other combinations
   until defined. Should the same protocol also repair a Tag that is an
   Agent of a Pin? The ownership and saved Rip rule can apply there, but
   its call boundary needs an explicit probe.

## Backwards compatibility

`@Fix` is new and would not alter existing declarations by itself. The
related admission and sound-source changes belong to STEP-SPEC-39, not to
this STEP. Programs using ordinary Actions to repair free Agents can keep
them. A declaration named `Fix` without the proposed decorator remains an
ordinary Action under today's scan.

## Alternatives considered

| Alternative | Assessment |
| --- | --- |
| Reapply an active Tag to retry training | Existing Tagging makes this a no-op; changing it would make repeated calls silently repeat effects. |
| Automatically apply a different Tag to repair a broken Agent | Crosses the independent Tag boundary and makes the other Tag responsible for this Tag's contract. |
| Let every Tag's Fix run during any arrest | Gives unrelated Tags an access door to an Agent held by another Tag's unfinished Rip. |
| Use only Agent Actions | Useful for free Agents, but does not identify the Tag that owns saved Rip work or grant a narrow recovery door. |

---

### Decision *(to be filled by the Director)*

> Status remains **Brief**. The Director has approved the two declaration
> forms and an owning Tag's Fix during its arrest. Call spelling, automatic
> completion checks, recovery failure naming, mark combinations and Pin
> parity remain open for review.
