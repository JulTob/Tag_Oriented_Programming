# STEP-SPEC-36: Tagging Admission

- **STEP:** SPEC-36
- **Desk:** spec
- **Title:** Tagging Admission
- **Author:** Julio Toboso (@JulTob)
- **Status:** Cleared
- **Created:** 2026-10-12

## Summary

Tagging follows **Gate → Gainings → Imprints → FieldAdding → Posts**.
Unfinished training leaves actual Gains without membership; completed
training admits the Agent, and Posts determine its current soundness.
This supersedes the training and admission boundaries of STEP-SPEC-4.

## Motivation

A car is a car after assembly. A broken assembled car belongs to that
category; a wheel next to a frame is an unfinished attempt to produce one.
Likewise, membership follows completed training rather than preceding it.
An Agent with acquired Gains outside the Agency is Rogue, whether training
was partial or it previously entered and was Ripped.

## Specification

1. Missing Tags take independent turns in Base-first Form order. Each passes
   its own Gate against the Agent's current state. A refusal leaves this Tag
   unstarted and completed earlier Tags in place.
2. Actions, Records, condition definitions and deletions take effect in
   declaration order, top to bottom. Every acquired Gain or condition is
   visible to later declarations. All this Tag's own Preconditions have
   already been evaluated at the Gate. Record builders read and query to
   calculate their initial returned value; applying or Ripping Tags belongs
   to Imprints.
3. Imprints follow Gainings, in declaration order. The Agent can use acquired
   Actions and Records, but does not yet belong to this Tag. This Tag's
   published Reports and Operations and its Agent-bound view are unavailable
   through the Agent until admission.
4. After Imprints finish, FieldAdding establishes membership, history and
   Field entry together. An unfinished attempt establishes none of these.
5. Once the whole Form finishes, every visible Post checks the resulting
   Agent. Posts define requirements; a missing optional Gain or a historical
   exception does not independently define deficiency. Post failure preserves
   membership, and current Posts determine soundness.
6. Failed Gainings or Imprints retain actually acquired Gains and completed
   Taggings, without admitting the unfinished Tag. Python interruptions follow
   the same boundary and keep their original exception type.
   Acquired conditions also remain, including Posts and Constant Posts, just
   as established contracts remain after Rip. Ordinary Posts follow existing
   composition rules; Constant Posts keep their protection.
7. Calling `Tag(agent)` on this Rogue starts a fresh Gate, overlays ordinary
   Gains and restarts Imprints. It does not resume an interrupted instruction.
   Successfully established Constants remain protected; failed initialization
   does not establish a Constant Record binding.
8. Applying this same Tag to the same Agent while its Tagging is already
   underway is a no-op. An active reapplication also remains a no-op.
9. A failed never-member is outside `Tag[:]` and does not run Rip automatically.
   The program owns cleanup of unfinished training effects using ordinary
   Python error handling. Preconditions and Record builders are observational
   authoring rules, not a sandbox for arbitrary Python effects.

## Rationale

Gain acquisition and Agency membership are distinct facts. A Rogue can
satisfy its visible Posts without being admitted. An admitted Agent can be
deficient without ceasing to belong. Retrying through normal Tagging uses
TOP's existing Overlay and Imprint mechanisms rather than introducing a
resume protocol.

Posts remain once after the completed Form: a Base may promise what a later
Shape supplies. Existing conditions remain sticky after Rip; this STEP does
not change the author's responsibility for ending them.

A safety Post can precede the Action that needs it, so the contract is already
established when that Gain arrives. This does not automatically guard ordinary
Action calls; an Action can explicitly read its named safety condition before
effects. Acquired Posts also govern current validity and guards on
published services from active Tags.

## Backwards compatibility

Imprints can no longer assume their own Tag's membership, view or published
Agency services through the Agent. Failed training no longer admits this Tag,
and Record failure no longer restores completed independent Taggings.
Programs that caught training failures and then Ripped this Tag should handle
their unfinished resources directly instead. Post failures still preserve
membership and use the existing defective population `~Tag`.

## Alternatives considered

| Alternative | Decision |
| --- | --- |
| FieldAdding before Imprints | Superseded: an unfinished product is not yet a member |
| Require Posts before FieldAdding | Rejected: a broken completed product remains a member; Posts may inspect membership |
| Restore the whole Form after failed training | Rejected: Tags are independent, and actual completed work remains |
| Resume at the failed Imprint | Set aside: normal Tagging is a fresh attempt using the Agent's current state |

## Acceptance requirements

Verify ordered visibility of Gains; no membership or new history during
training; retained Gains and earlier Tags after failure; fresh retry and
Constant initialization boundaries; publication after admission; same-Tag
recursive application as a no-op; and Post failure preserving membership.
The independent oracle must model these outcomes, including Field join order.

---

### Decision

> Cleared on 2026-10-12 by the Director: **Gate → Gains/Imprints → Field → Posts**.
> Posts control a failure of completed training; unfinished training produces
> a Rogue with Gains outside the Agency. The Director also specified that
> Gains arrive in Tag declaration order, top to bottom, and are visible to
> subsequent Gains. Implementation is submitted in successive reviewable PRs.
