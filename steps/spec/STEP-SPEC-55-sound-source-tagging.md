# STEP-SPEC-55: Sound Source for a New Tagging

- **STEP:** SPEC-55
- **Desk:** spec
- **Title:** Sound Source for a New Tagging
- **Author:** Codex, recording the Director's 2026-10-20 ruling
- **Status:** Brief
- **Created:** 2026-10-20
- **Issue:** [#376](https://github.com/JulTob/Tag_Oriented_Programming/issues/376)
- **Design dependencies:** [STEP-SPEC-39](STEP-SPEC-39-tagging-admission.md), [STEP-SPEC-53](https://github.com/JulTob/Tag_Oriented_Programming/pull/370), and the observational Post proposal [#348](https://github.com/JulTob/Tag_Oriented_Programming/pull/348)

## Summary

An Agent must be **sound now** before it starts a new Tag turn. TOP checks
the Agent's current visible Posts before that Tag's Gate, Gainings, Imprints
or Field entry. A broken Agent cannot acquire an unrelated Tag in the hope
that the later Tag will repair an earlier promise. This Brief changes no
runtime code or current Specification while it awaits review.

## Motivation

Tags are independent layers with independent Fields. A new Tag should
receive a valid Agent; it should not quietly become the repair step for a
broken member of another Tag. A Base and its Shape follow the same rule:
applying a Shape does not skip an already active Base's newly failed Post.
The programmer may repair the existing Agent through its available Actions,
Records or the owning Tag's proposed Fix protocol, then start the new
Tagging deliberately.

## Proposed rule

1. Before each **missing** Tag in a Form starts its own Gate, inspect every
   currently visible Post on the Target. A false Post refuses that new turn
   before any of its Gate, Gains, Imprints or Field entry runs. Report the
   existing contract failure; this is not a refusal by the new Tag's Pre.
   No completed earlier Tag turn is rolled back.
2. A Host never actualized by TOP has no TOP Posts to fail. Its ordinary
   Python `bool()` is not a substitute for this check. An actualized Agent
   with no failing visible Posts may start the new Tag turn, even if it has
   left every ordinary Field.
3. Check at the boundary again even if a Base in the Form is already active.
   Its Posts may have changed since admission. Thus a broken active Base
   blocks a new Shape before the Shape's Gate. When a newly applied Base
   enters its Field, its Posts are checked at that turn before the Shape
   under the separate per-Tag timing proposal, STEP-SPEC-53.
4. A Post gained during a failed earlier attempt still participates while
   visible. A retained false `@Constant @Post` after Rip therefore blocks
   a **new** Tagging, including reapplying the Ripped Tag, until the Agent
   repairs its current contract. Soundness is read from current Posts, not
   from a permanent failed-training marker.
5. Calling a Tag already active on the Agent is not a new Tag turn. A sound
   active call keeps today's no-op behavior. The proposed `Car(car)` Fix
   path for a broken member, or an Agent held for Car's saved Rip, belongs
   to [STEP-SPEC-47](https://github.com/JulTob/Tag_Oriented_Programming/pull/326).
   An active Tag's Fix must not be invoked implicitly by a different Tag's
   call. Calling the same Tag while its original Tagging is underway stays
   a no-op under STEP-SPEC-39.
6. Safehouse arrest has its own Rip-retry and access rules under
   [STEP-SPEC-32](STEP-SPEC-32-the-arrest.md). This rule grants no path for
   a new Tagging around arrest. Posts used for this source check follow the
   observational Post rule: TOP acts inside a Post are refused; ordinary
   Python writes remain the author's responsibility.

## Example of the proposed boundary

This example expresses the proposed rule; current TopKit does not yet
perform the source check:

```python
class Host:
    pass


class Body(Tag):
    @Post
    def Ready(agent):
        return agent.ready


class Vehicle(Body):
    @Pre
    def May_Enter(agent):
        print("Vehicle Gate")
        return True


car = Host()
car.ready = True
Body(car)
car.ready = False
Vehicle(car)  # Body's failing Ready refuses before Vehicle's Gate
```

Body remains in `Body[:]`; Vehicle never enters its own Field. Repairing
`car.ready` and calling `Vehicle(car)` again starts Vehicle's new turn.
There is no implicit Body re-training in that call.

## Scope and diagnostic boundary

This STEP chooses **when and whose Posts** guard a new Tagging. It does not
define Record-space preparation ([#374](https://github.com/JulTob/Tag_Oriented_Programming/issues/374)),
Record initializer failures ([#375](https://github.com/JulTob/Tag_Oriented_Programming/issues/375)),
ordinary Imprint warnings ([#368](https://github.com/JulTob/Tag_Oriented_Programming/issues/368)),
or Fix selection. A single failing Post can use its existing named Post
failure. The diagnostic for several simultaneously false Posts follows the
separate aggregate-failure decision; this Brief does not invent another
failure class. A malformed Post verdict or observational violation remains
a Contract Failure under its own rule.

## Acceptance requirements

Verify a broken member and a Rogue with a failing acquired Post cannot
start an unrelated Tag; the refused Tag's Gate and Gains do not run and its
Field stays untouched. Verify an already active Base that has since become
broken blocks a new Shape. Verify sound Agents, untouched Hosts, and Agents
with no failing Posts can start new Tags. Verify a retained false Constant
Post after Rip blocks a new Tagging. Existing completed Tags and Gains remain
in place after a refusal. Test Tag Targets receiving Pins under the same
contract rule, without treating a Tag's Field size as its truth.

---

### Decision

> **Brief.** The Director ruled on 2026-10-20 that a new Tagging needs a
> currently sound Agent. The owning Tag's Fix and Safehouse retry paths are
> separate. Formal clearance and implementation remain later review steps.
