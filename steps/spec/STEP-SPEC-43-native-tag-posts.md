# STEP-SPEC-43: Native Tag Posts

- **STEP:** SPEC-43
- **Desk:** spec
- **Title:** Native Tag Posts
- **Author:** Codex, recording the Director's feature request and alternatives
- **Status:** Brief
- **Created:** 2026-10-14
- **Issue:** [#181](https://github.com/JulTob/Tag_Oriented_Programming/issues/181)
- **Design dependency:** STEP-SPEC-40's unified Agent/Tag truth, proposed in [#160](https://github.com/JulTob/Tag_Oriented_Programming/pull/160), with the public API cleanup in [#180](https://github.com/JulTob/Tag_Oriented_Programming/pull/180)

## Summary

Allow a Tag to declare a Post about itself without first receiving a Pin.
The Director requested evaluation of `@Post` with `@Operation` against
`@Post` with a proposed `@Private`. Recommend **Post-Operation**: Operation
identifies the Tag as receiver, and Post identifies a condition contributing
to that receiver's validity. This Brief proposes semantics for review; it
changes no runtime code or current Specification.

## Motivation

STEP-SPEC-40 makes `bool(Tag)` answer the Tag's own visible Posts. At present
those Posts come through Pins. A Pin is useful when another Tag supplies a
contract, membership and lifecycle. Requiring one just to let an Agency
state its own promise adds a declaration and a Tagging to express something
local to that Agency.

A plain `@Post` must retain its existing meaning: a promise about the
Agents receiving the Tag. A distinct supported combination must identify
the Tag as the subject of the new promise.

## Existing vocabulary and behavior

The [Specification](../../spec/SPECIFICATION.md) separates two questions:

- **Receiver scope**, §1.4 and [STEP-SPEC-1](STEP-SPEC-1-contribution-scope.md):
  Actions receive an Agent; Operations receive a Tag.
- **Publication**, §1.5: Secret/Public control how Contributions are reached;
  they do not change who receives them. Tag-scope Contributions are already
  internal by default, while remaining directly accessible on the Tag.
- **Conditions**, §2.5 and [STEP-SPEC-14](STEP-SPEC-14-condition-members.md):
  a condition's name reads as a computed plain boolean, not a callable or a
  proxy pretending to be both.

There is no exported `@Private` modifier. `@Secret` already expresses
restricted visibility. A new Private mark could be given a scope-changing
definition, but that definition would diverge from the existing separation.

Neither order of `@Post` and `@Operation` currently implements this feature.
On #160 head `c37c0b35e19be49ba23df53f10372762dbc8282f`, both scan as an
ordinary Operation with zero Posts: its call can return False while the
Tag's truth remains True. The single-kind marker and classmethod scan lose
the intended combination. Acceptance of the syntax is not implementation.

## Comparison

| Criterion | `@Post` + `@Operation` | `@Post` + proposed `@Private` |
| --- | --- | --- |
| Identifies the Tag receiver | Uses Operation's existing receiver | Needs a new meaning for Private |
| Separates scope from visibility | Keeps the two questions separate | Uses a visibility word to choose scope |
| Reuses the modifier vocabulary | Adds a supported combination of existing marks | Adds a new mark beside Secret/Public |
| Invoking the check by name | Execute the Post body on named access, with the Tag as receiver | Could also execute on named access, but receiver selection would depend on the new privacy rule |
| Describes the desired locality | Says which object is checked | Suggests a locally held promise, but could also suggest a hidden Agent Post |

**Recommendation:** Post-Operation. This is a supported combined declaration,
not a claim that every Operation is a condition. A normal Operation remains
callable. The cost to acknowledge is that Post-Operation must follow one
clear access rule; restoring the old callable/boolean condition proxy would
conflict with the current condition model.

## Director's clarifications, 2026-10-14

On the named check, the Director specified **“callable just by name without
\"()\", not just read”**. Evaluating `Tag.Ready` must execute the Post body
immediately and yield its current verdict. It retrieves neither a stored
verdict nor a handle waiting to be called. This clarification concerns the
Post-Operation; it does not introduce a general change to Action invocation.

On Shapes, the Director specified **“they don't need a copy, as the base is
tagged before a shape is”**. Record the no-copy constraint. The receiver of
the shared declaration remains to be clarified: applying a Base before a
Shape to a member Agent does not itself apply that Base to the Shape class.
Reusing one declaration does not require copying its body in any of the
receiver choices described below.

## Proposed semantics — remaining decisions

The following records execution by name as clarified above; other choices
remain recommendations unless explicitly confirmed.

### Declaration, receiver and reads

1. Both decorator orders declare the same Tag-level Post. Its body receives
   the Tag, takes no Tagging inputs, and follows existing Post verdict,
   assertion, synchronous-result and recursion rules. This does not make
   arbitrary decorator combinations valid.
2. `Tag.Ready` invokes the check immediately, without `()`, and returns its
   current boolean verdict under the existing condition rules. Each ordinary
   access evaluates current state; it is not a saved result. Existing nested
   check guards still apply. The proposal returns the plain verdict, with no
   additional callable/boolean proxy. Operation chooses the receiver in this
   combination; Post chooses the condition behavior.
3. The declaration contributes to the same visible contract used by
   `bool(Tag)`, `Contract.Postconditions(Tag)`, `Contract.Status(Tag)` and
   the existing diagnostic views. Named failures use the existing Post
   failure conventions. There is no second truth API or implicit Pin.
4. A plain `@Post` in the same class still promises something about its
   member Agents. Neither kind is silently copied into the other's contract.
   No Pin membership, Pin Field entry or fabricated self-Tagging is created.
5. `len(Tag)`, `len(Tag[:])`, `len(~Tag)`, iteration and algebra keep their
   existing populations. A Tag's broken promise does not by itself make
   every member Agent defective. A Tag used as a member of a Pin, however,
   is judged by its full own contract for that Pin's sound/broken partitions.

### Example of the recommended spelling

This is **proposed syntax**, not a runnable example of the current release:

```python
class Fleet(Tag):
    @Report
    def capacity(tag):
        return 10

    @Post
    @Operation
    def Within_Capacity(tag):
        return len(tag[:]) <= tag.capacity

    @Post
    def Charged(agent):
        return agent.charge > 0


if Fleet.Within_Capacity:    # execute the Tag's named check now, without ()
    pass

if Fleet:                  # all of the Tag's own visible Posts
    pass

if len(Fleet) > 0:         # there is a sound member Agent
    pass
```

`Within_Capacity` counts the whole Field deliberately, including broken
members. `Charged` contributes to each receiving Agent's contract. A Pin
could supply further Posts about Fleet without being needed to establish
`Within_Capacity` in the first place.

### Shapes, Overlay and protection

No copy of the Base's Post body is needed. The earlier recommendation was
to reuse it with **the Shape** as receiver, as inherited Operations do.
The Director's Base-first answer does not yet settle that receiver; keep
this choice open rather than treating no-copy as either acceptance or
rejection of Shape-bound evaluation.

Concrete decision: Crew declares a Post-Operation requiring two members.
Pilots is a Shape of Crew. There are ten Crew members, but only one Pilot.
Tagging that Pilot already applied Crew first, as the Director describes.
Does Pilots nevertheless need two Pilots to be valid, or does the Post
govern Crew as a whole? This is about which Agency the requirement judges,
not whether its declaration is copied. If it governs Crew only, separately
settle whether Crew's failure contributes to Pilots' truth.

The Director requested a simpler explanation of this question; no answer
about the receiver or applicability has yet been recorded.
Existing Posts gained through a Pin remain specific to the Tag actually
pinned under the current rules; Pin membership does not inherit. Revisit
the example and the dependent Overlay/deletion recommendations below once
the native Post receiver is settled.

Recommend one visible Post per name, using existing Post Overlay, Underlay,
Contract Warning and Constant protection. A Shape or a Pin should not create
two simultaneously enforced promises named Ready while `Tag.Ready` reports
only one of them. Same-name Record/Action/Report/ordinary Operation collisions
must follow an explicit condition collision rule, not silently hide a Post.

Native/Pin Overlay is a real design extension: current Pin rules distinguish
patchable Tag-scope Contributions from protected protocol declarations.
Before implementation, settle exactly how native Posts enter that distinction,
how same-name Pin Posts overlay them, and how late Base/Shape edits interact
with a receiving Tag's retained Pin history.

Recommend computed-condition write protection: `Tag.Ready = True` and
`del Tag.Ready` cannot bypass its calculation. Deliberate removal uses
`Contract.Delete(Tag, "Ready")` for a non-Constant condition. For an inherited
native Post, this must affect that receiving Tag only, not erase its Base's
declaration or sibling Shapes' contracts. The deletion's persistence across
later Shape edits or Pin reapplication needs an explicit decision and tests;
it must not silently resurrect a deleted promise.

`@Constant` would protect the binding and implementation, not freeze the
condition's verdict: a fixed check still answers current state. Rip of a Pin
must not erase an independently declared native Post. Existing retained
Pin Post behavior remains applicable to Posts actually gained from that Pin.
If a Pin Post has overlaid a native Post, Rip keeps that visible Pin Post
under ordinary sticky-contract rules; it does not automatically restore
the native one.

### When the condition is checked

Recommend the normal truth, named-read and diagnostic paths, together with
existing contract checks when that Tag receives a Pin. A false native Post
at class creation is allowed. A promise such as `len(tag) > 0` must be able
to begin false and become true when the Agency gains a sound member.

Do not infer an automatic Gate over the Tag's members, a check after every
member Tagging/Rip, or an automatic guard on ordinary Operations. Existing
§1.9 makes a Tag's admission policy explicit even when a Pin supplies its
contract. Preserve that pattern here: a programmer may read Tag truth in
an appropriate Pre or Action/Operation guard. Repair Operations must remain
possible. Any additional automatic checkpoint needs its own defined failure
boundary, including which memberships and Gains survive.

Bodies may calculate and read information using existing Post conventions.
This proposal introduces no read-only sandbox or general side-effect policy.

## Boundaries and implementation outline

This is one feature: direct Tag-level Posts. Publication of those conditions
onto member Agents and a Tag-level Pre with an as-yet unspecified event to
gate are outside the first implementation. Contradictory or unspecified
combinations must be rejected explicitly, never accepted while losing a mark.

After the design is Cleared, the implementation must:

- represent the supported combined declaration without dropping Post or
  depending on decorator order;
- compose native and gained Tag Posts into one visible contract used by
  truth, diagnostics, named reads and Pin population checks;
- preserve plain Agent Posts, normal callable Operations, Fields, access
  rules, and Tagging/Pin lifecycle behavior;
- implement the agreed Shape, collision, Overlay, deletion, Constant and
  cache-invalidation rules together with their failure paths;
- amend Specification §§1.4, 1.5, 1.9 and 2.5–2.6, relevant STEP guidance,
  executable guides and the wiki when the implementation is ready.

## Acceptance for the eventual implementation

- Both decorator orders evaluate an initially false Tag Post without a Pin;
  a state repair makes truth true. No-Post Tags remain true under STEP-SPEC-40.
- Named reads, truth and diagnostics agree, including errors, non-boolean
  verdicts, assertion fall-through, recursive checks and lazy results.
- Access by name invokes the body immediately without `()`; a later access
  observes changed state rather than returning a cached verdict or handle.
- Native Posts and ordinary member Posts stay separate; none is implicitly
  published and no implicit membership appears.
- A Pin's sound/broken partition reflects a receiving Tag's native failure;
  the receiving Tag's own member cardinalities and algebra remain unchanged.
- Cover the agreed Shape receiver and non-inherited Pin contract behavior,
  ordered multiple Bases, Post Underlay, warnings and same-name collisions.
- Cover native/Pin coexistence and Overlay, Constant refusal, Pin Rip and
  reapplication, explicit deletion on one Shape and subsequent declaration
  edits, including cache refresh.
- Ordinary Operations remain callable and available for repair; a false
  Tag Post alone does not become a member Gate or add hidden checkpoints.
- Unsupported combinations and condition dunder names fail explicitly.
- Run regression tests on the pre-change runtime, then the full supported
  suites, executable docs and the contract oracle on the implementation.

## Compatibility and dependencies

The Brief is based on current `main`; its implementation is designed for
STEP-SPEC-40 as revised in #160 and the removal of `Contract.Holds` in #180.
Those changes are still unmerged at drafting. This STEP extends the sources
of a Tag's Posts; it does not reopen their unified truth or population rules.

Code already stacking Post and Operation may rely accidentally on getting
an ordinary callable Operation. Supporting the combination changes that
behavior and must be documented. Existing callable checks can remain normal
Operations; an actual contract check uses the supported combined declaration.

Keeping Pins as the only source of Tag Posts needs no new runtime behavior
but does not meet the requested direct declaration. Giving Private a new
scope meaning is possible, but less consistent with TOP's current vocabulary.

## Decisions to settle

1. Confirm the combined declaration spelling; execution by name without
   `()` is clarified above.
2. Resolve the Base/Shape receiver and applicability example above, while
   reusing the declaration without copying it.
3. Confirm native/Pin Post Overlay and explicit per-Tag deletion, including
   later declaration changes and Constant protection.
4. Confirm explicit validity checks and existing Pin boundaries, without
   automatic member admission or Operation blocking.

### Decision *(filled by the Director)*

Status remains **Brief**. The feature request and clarifications authorize
this proposal and record execution by name and the no-copy constraint;
they do not settle the remaining choices above or Clear the STEP.
