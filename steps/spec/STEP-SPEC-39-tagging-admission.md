# STEP-SPEC-39: Tagging Admission

- **STEP:** SPEC-39
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

### Amendment proposed for review — Target validation and best-effort training (2026-10-20)

The Director distinguished a Target's ability to hold Records from the
calculation of their initial values. The original Gate → Gainings → Imprints
→ FieldAdding → Posts sequence remains, but the boundary for failed
`@Record` and `@Imprint` protocols changes as follows. This amendment
depends on the separately cleared per-Tag Post timing in #318: each newly
admitted Tag is judged before the next Tag's Gate. It is **not yet Deployed**.

1. Before applying an unrelated new Tag, the Agent's current visible
   Posts must hold. This applies to independent Tags as well as to a
   Shape's next turn; layering does not implicitly repair another Tag's
   contract. An untouched Host has no TOP Posts to fail. Applying an
   already active Tag remains a no-op. Whether this soundness gate also
   bars reapplying a previously Ripped Tag while its old Post remains
   sticky is open pending the separate Post-after-Rip decision.
2. Before any Gain of this Tag, TOP validates **all Record spaces** the
   Target needs. This is retractable, zero-step structural preparation,
   not an `@Record` value calculation. If it fails, TOP restores this
   attempt's provisional Target representation and bindings, raises public
   `TagTargetError` (a subtype of `TagCompositionError`), and acquires no
   Gains or Field membership for this Tag. Earlier completed Taggings stay.
   `TagTargetError` also names structural Host Target refusals: inability
   to carry TOP state or the requested runtime representation. Overlay
   collisions keep their existing failure classes. Other Host
   actualization rules remain under STEP-SPEC-37.
3. Gainings still take effect in declaration order, top to bottom. An
   `@Record` initializer calculates a value at its own declaration
   position. If that calculation fails, it acquires no new value, Constant
   binding or Tool binding for that declaration. Any prior value remains
   available at its existing layer. Later Gainings continue and see every
   successful earlier Gain; Imprints then run in their declaration order.
4. If an Imprint fails ordinarily, later Imprints still run. Each ordinary
   `@Record` or `@Imprint` failure is reported by its own **named training
   warning**, in declaration order: `TrainingWarning.Name`, where `Name`
   is that protocol's declared name.
   Reporting must not stop the remaining training or prevent Field
   admission. A failed protocol does not erase earlier Gains or by itself
   mark the Agent permanently broken.
5. After these training attempts, FieldAdding admits the Agent, including
   when one or more declared calculations or Imprints failed. Its gained
   Posts stay recorded in the current contract; Tag publications become
   available through the admitted Agent. The Agent is then judged by its
   **current visible Posts**. A non-Constant Post may have been deliberately
   ended; `@Constant` is the way to protect a required Post from replacement
   or deletion. There is no separate requirement that every declaration
   still be present.
6. If the current Posts all hold, Tagging returns the sound Agent after any
   warnings. If exactly one visible Post fails, the existing named
   `TagPostconditionError.Name` (also `Postcondition.Name`) remains the
   final error. If several visible Posts fail, Tagging raises **one final
   aggregate `TaggingFailure`** naming all of them in Post evaluation order.
   `TaggingFailure` is a subtype of `TagPostconditionError`, so general
   Postcondition failure handlers still catch it. A non-boolean Post verdict
   remains a separate Contract Failure, not an aggregate of failed Posts.
   In either case the Agent stays in the Field as broken. The verdict is
   taken after all ordinary training attempts; past protocol errors alone
   do not determine membership or soundness.
7. `KeyboardInterrupt` and `SystemExit` during an `@Record` initializer or
   Imprint stop later training. TOP still performs Field admission and Post
   inspection, then preserves and propagates the original interruption;
   a Post failure does not replace it.

This amendment would supersede rule 4's successful-Imprint requirement,
rule 6's failure boundary for declared calculations and Imprints, rule 7's
fresh retry after those failures, rule 9's never-member conclusion for them,
and related compatibility and acceptance text above. A structural Target
failure is different: it is zero-step and does not admit this Tag. The
historical cleared decision remains above for traceability. STEP-SPEC-22's
Link Pair and Contact admission, the Specification, guides, tests and oracle
need coordinated updates. A Pair cannot be admitted while its Contact is
silently left outside that Link.

STEP-SPEC-8's named `TagImprintError.Name` exception on the Tagging call is
superseded for ordinary Imprint failures: the call continues and reports
named training warnings. STEP-SPEC-8's named Precondition failures and its
single named Postcondition failure remain. Several failed Posts are one
aggregate outcome rather than several named exceptions.

Recovery of a broken or arrested Agent is Tag-owned, but the proposed
`@Fix` declaration, call route and Safehouse permissions belong to a
separate STEP. This amendment does not authorize an unrelated Tag to repair
another Tag implicitly, or release an Agent whose saved Rip is unfinished.
It also does not decide whether non-Record Gaining failures continue through
later declarations; structural Target refusal and declared `@Record` failure
are the two boundaries decided here.
