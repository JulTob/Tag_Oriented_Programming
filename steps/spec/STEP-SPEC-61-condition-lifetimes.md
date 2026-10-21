# STEP-SPEC-61: Condition Lifetimes

- **STEP:** SPEC-61
- **Desk:** spec
- **Title:** Condition Lifetimes
- **Author:** Codex, recording the Director's 2026-10-20 ruling
- **Status:** Deployed
- **Created:** 2026-10-20
- **Deployed:** 2026-10-20

> One STEP, one topic. This STEP defines when each kind of condition exists.
> It does not change Post-check timing, failed-Imprint admission, recursive
> verdicts, or same-name layering above a Constant Post.

## Summary

TOP has three condition lifetimes:

- a **Pre** is a transient Tagging Service. It exists only while its Tag's
  Gate judges one Tagging attempt;
- an ordinary **Post** is a membership-bound Agent Gain. It belongs to the
  Tag application that admitted the Agent and ends when that application
  leaves its Field; and
- a **Constant Post** becomes a lifetime Contract term after admission. It
  continues to bind the Agent after Rip, like an NDA after employment ends.

The **Contract** is the bond between the Agent and its Agencies. A Pre decides
whether that bond may begin; it is not itself a term carried by the Agent.

## Motivation

The previous model stored both Pres and Posts on the Agent and kept them after
Rip. That mixed three different ideas:

- a Gate question asked before an Agency relationship exists;
- a promise owed while an Agent belongs to an Agency; and
- a deliberately permanent promise that outlives that relationship.

It also left a refused Gate visible as an Agent member, let an unfinished
Tagging impose a Contract for an Agency the Rogue never joined, and required
ordinary membership promises to delete themselves during Rip. The Director's
three-part lifetime model gives each concept one structural home.

## Specification

1. **Pre is a Service of the Gate.** A Pre is bound and evaluated only for
   the current Tag's turn. It may take application inputs and may use
   `@Underlay` to call a prior Pre Service in that Tag's ordered Form. Pres
   from unrelated earlier Taggings are not Agent history and cannot become
   that Underlay.
2. **Pre leaves no Agent feature.** A Pre is not installed in Agent state,
   does not reserve its name on the Agent, does not appear in presence or
   Contract queries, and is not something Rip or condition deletion ends.
   A fresh Tagging evaluates it again from its declaration.
3. **Posts are provisional during Gainings.** A Post declaration takes its
   declaration-order position so later Gainings in that attempt can read it.
   Until Field admission it is provisional, not an established Contract
   term. If the attempt fails before admission, all of that attempt's Posts
   are discarded, including Constant Posts. Actually acquired Actions and
   Records keep their separately defined Rogue behavior.
4. **Admission owns the Post application.** FieldAdding associates every
   admitted Post layer with that specific Tag application. Application
   identity, not merely the Tag class or Post name, distinguishes an old
   application from a fresh reTagging of the same Agent.
5. **Ordinary Posts follow membership.** Removing that application from its
   Field ends its ordinary Post layers before any `@Rip` teardown runs. A
   teardown failure does not restore them. A fresh same-Tag application made
   by an old teardown keeps its own layers.
6. **Surviving Post towers remain coherent.** Ending a top layer reveals the
   next surviving layer. Ending a middle layer reconnects later Underlays to
   the nearest survivor. If no lower Post survives, the missing Post Underlay
   contributes the neutral verdict `True`.
7. **Constant Posts begin at admission and last for life.** A provisional
   Constant Post is discarded with any other unadmitted Post. Once admitted,
   it survives Rip and continues to participate in Agent truth and named
   Contract checks for the Agent's lifetime. Its existing Constant binding
   protection remains in force.
8. **One body may declare two roles.** Stacking `@Pre` and `@Post` keeps one
   calculation and two named failure roles, but not one stored condition. Its
   Pre role is transient; its ordinary Post role follows membership. Adding
   `@Constant` protects and extends only the admitted Post role.
9. **Pins obey the same lifetimes.** When a Tag is itself an Agent, its Pre is
   still transient, its ordinary Post follows the Pin membership, and its
   admitted Constant Post survives that Rip.
10. **Contract diagnostics are Post diagnostics.** `bool(agent)`,
    `Contract.Postconditions`, `Contract.Status`, `Contract.Display`, and a
    named condition read inspect current Posts. There is no stored Pre history
    for `Contract.Preconditions` or `Contract.Conditions` to query, so those
    two legacy APIs end.

## Rationale

Field membership is the explicit evidence that an Agent--Agency bond was
formed. It is therefore the natural lifetime boundary for an ordinary Post.
Using an opaque application identity preserves TOP's independent layers: an
old Rip cannot erase a new application merely because both use the same Tag.

Constant gives permanence a visible spelling. Starting that permanence only
at admission prevents a failed production attempt from imposing a lifelong
obligation. Ending ordinary Posts before teardown means teardown code observes
the same fact as the Field: the old Agency relationship has already ended.

Keeping Pres outside Agent state is both simpler and more faithful to their
meaning. A Service answers the Gate that calls it; it is not a Gain, a
promise, or a tombstone carried afterwards.

## Backwards compatibility

This supersedes the lifetime rules of
[STEP-SPEC-12](STEP-SPEC-12-the-author-ends-a-condition.md), the stored-Pre
part of [STEP-SPEC-14](STEP-SPEC-14-condition-members.md), and the
unadmitted-condition rule in
[STEP-SPEC-39](STEP-SPEC-39-tagging-admission.md).

Programs that read a Pre from an Agent must perform a new Tagging or express
the lasting fact as a Record or Post. Programs that used an ordinary Post
after Rip must declare it Constant when the obligation truly lasts for life.
Old Rip protocols may still call `Contract.Delete` after automatic removal;
ending an already absent removable Post is idempotent.

The following settled changes remain separate work and are not hidden inside
this STEP: allowing stricter same-name Posts above a Constant while enforcing
both, the public `del agent.PostName` neutral reset, per-Tag-turn Post checks,
and neutral recursive Post evaluation.

## Alternatives considered

| Alternative | Reason set aside |
| --- | --- |
| Keep every condition sticky | A transient Gate becomes Agent history, and ordinary membership promises outlive the membership they govern. |
| Keep Posts from failed Taggings | It imposes a Contract without admission into the Agency. |
| End ordinary Posts after teardown | A failed teardown leaves a former membership promise judging an Agent already outside the Field. |
| Make every Post permanent | It erases the semantic reason for `@Constant`. |
| Remove by Tag class instead of application | A teardown that deliberately reTags could erase the fresh application. |

## Acceptance requirements

- A successful or refused Pre leaves no Agent member or Contract entry and is
  evaluated again on a fresh Tagging.
- Pre Underlay uses only the current ordered Form.
- A pre-admission failure discards ordinary and Constant Posts while keeping
  separately acquired Actions and Records.
- Rip ends ordinary Posts before teardown, even when teardown fails; top and
  middle removal rebuild same-name Post towers correctly.
- ReTagging inside an old Rip preserves the fresh Post application.
- An admitted Constant Post survives Rip and still controls Agent truth.
- Pins and stacked `@Pre @Post` declarations follow the same rules.
- Current Specification, guides, wiki, oracle, optimized checks, and runtime
  tests describe and exercise the same lifetime model.

---

### Decision

> **Deployed on 2026-10-20.** The Director ordered Pres to be “transient to
> tagging,” ordinary Posts to be “Field membership dependent,” and Constant
> Posts to be “for life,” using an NDA that remains relevant after leaving a
> company as the model. The dependent implementation, current Specification,
> guides, oracle, and focused regressions deploy the ruling.
