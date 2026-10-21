# STEP-SPEC-58: Agent Feature Deletion and Service Grants

- **STEP:** SPEC-58
- **Desk:** spec
- **Title:** Agent Feature Deletion and Service Grants
- **Author:** Codex, recording the Director's 2026-10-20 ruling
- **Status:** Brief
- **Created:** 2026-10-20
- **Issue:** [#385](https://github.com/JulTob/Tag_Oriented_Programming/issues/385)
- **Amends, if cleared:** [STEP-SPEC-1](STEP-SPEC-1-contribution-scope.md), [STEP-SPEC-3](STEP-SPEC-3-member-publication.md), [STEP-SPEC-5](STEP-SPEC-5-stored-records.md), [STEP-SPEC-10](STEP-SPEC-10-published-members-answer-members.md), [STEP-SPEC-12](STEP-SPEC-12-the-author-ends-a-condition.md), [STEP-SPEC-14](STEP-SPEC-14-condition-members.md), [STEP-SPEC-33](STEP-SPEC-33-contribution-presence.md), [STEP-SPEC-34](STEP-SPEC-34-constant-contributions.md), [STEP-SPEC-36](STEP-SPEC-36-tools.md), [STEP-SPEC-39](STEP-SPEC-39-tagging-admission.md), and [STEP-SPEC-40](STEP-SPEC-40-agent-contract-truth.md)
- **Depends on:** [STEP-SPEC-32](STEP-SPEC-32-the-arrest.md), the live-view design in [PR #228](https://github.com/JulTob/Tag_Oriented_Programming/pull/228), and the later Constant-tower design (not yet assigned a STEP)

## Summary

TOP calls a named thing exposed by an Agent or Agency a **Feature**. A Tag
gives one Agent a **Gain**. An Agency owns a **Service**. Publication gives a
member a **Grant** to that Service. A **Contribution** is the declaration
layer by which a Tag builds or composes a Feature.

The Director's core deletion ruling is equally direct: `del ari.name` ends
Ari's Gain at that name, or revokes Ari's Grant when the visible Feature is a
published Service. It never deletes the Agency's Service. This Brief records
that language and evaluates the Overlay mechanics needed to make it honest;
it changes no runtime by itself.

## Vocabulary

| Word | Meaning |
| --- | --- |
| **Feature** | User-facing umbrella for a named capability, value, check, or shared facility exposed by TOP. |
| **Contribution** | A declaration/layer that supplies, replaces, deletes, or composes a Feature. Existing Overlay specifications keep this technical word. |
| **Gain** | An Agent-owned Feature given by a Tag: an Action, Record, Tool-marked Record value, or Agent Contract check. |
| **Service** | A Tag/Agency-owned Feature: a Report or Operation. It lives at Tag scope rather than being copied per Agent. |
| **Grant** | One Agent's publication authorization and route to a Service, subject to membership, Contract and arrest gates. Publication may come from `@Public` or another explicit TOP rule such as a Pin. A blocked Grant still exists; revocation ends it. |
| **Contract** | The visible Overlay of Post checks used for Agent validity. Every visible Post holding, including no Posts, is a **Valid Contract**; one or more failures make it a **Void Contract**. |

A free Agent with a Valid Contract is a **Valid Agent**. A free Agent with a
Void Contract is a **Broken Agent**. An arrested Agent is a separate Safehouse
status and is neither Valid nor Broken, regardless of whether its Posts would
otherwise hold; Agent truth remains false until its saved Rip work succeeds.
These are the user-facing terms for the sound/defective population states and
the separately proposed arrested state.

Calling a Post a Gain is an ownership statement, not a coordinate change.
Actions and Records still occupy Agent member coordinates. Preconditions and
Postconditions keep the separate phase coordinates defined by STEP-SPEC-1.
A Precondition is a Gate protocol, not a Feature given to its Target.

The public `Contract` namespace may retain Precondition diagnostics for API
compatibility even though the validity Contract itself means the Post
Overlay.

## Settled language rule

### 1. One Agent-scope deletion

For an actualized Agent, `del agent.name` is the public spelling for ending
the visible, non-Constant Agent Feature at that name.

- If the visible Feature is an Action or Record Gain, it ends that Gain.
- If it is a Tool-marked Record, deletion removes the current value and
  presence while retaining the Tool kind rule that governs a later value.
- If it is an Agent Post, deletion ends that Contract contribution under the
  condition rule selected before this STEP is cleared.
- If it is a published Report or Operation, deletion revokes only this
  Agent's Grant. The Service remains on the Tag and other Agents keep their
  own Grants.
- If it is a Host-only attribute that TOP does not manage, ordinary Python
  deletion remains the Host's act.

Deletion does not Rip a Tag or change Field membership. Remaining Posts judge
the result. An author who requires a Gain or Grant states that requirement in
a Post; an uncrushable requirement uses `@Constant @Post`.

### 2. Scope stays visible

This distinction is observable:

```python
class Dispatch(Tag):
    @Public
    @Operation
    def Send(tag, agent, message):
        ...


Dispatch(ari)
Dispatch(bob)

del ari.Send

ari.Send("status")       # Ari's Grant is gone
bob.Send("status")       # Bob's Grant is unchanged
Dispatch.Send             # the Service still belongs to Dispatch
```

An Agent-bound Tag view uses that Agent's live credentials, so
`Dispatch[ari].Send` cannot bypass Ari's revocation. Direct Tag scope does not
become Agent scope merely because an Agent Grant ended.

An already-read Report is an ordinary Python value and cannot be revoked:

```python
colour = ari.colour
del ari.colour
use(colour)               # the value was already delivered
```

A saved Operation handle rechecks its live Grant at invocation. Capturing the
handle is not a permanent credential; after revocation it raises the same
strict Resolution Failure as a fresh Agent access.

## Recommended Overlay model

The following mechanics make the settled surface rule coherent, but they are
recommendations pending the Director's answers.

### 3. A deletion boundary, not a lower reveal

Deleting a removable Feature records an Agent-and-name boundary. It ends the
visible removable tower at that coordinate instead of revealing an older
same-name Gain or Grant. A later real Gain or Grant begins a new tower above
the boundary. If that later Feature ends, the coordinate returns to the
boundary rather than resurrecting a Feature already deleted by the Agent.

The boundary stores origin and kind metadata even while no binding is
present. For a Tool this is also where its admission rule survives. The word
**undeclared** in this Brief therefore means “no current TOP binding or
presence,” not “TOP has forgotten every declaration or rule.” A separate
choice below decides whether an underlying Host binding then becomes visible.

A Constant is the exception. STEP-SPEC-34 already refuses deletion,
replacement, or hiding of an established Constant. The Director's newer
Jenga-tower ruling would allow removable pieces to compose above a Constant
while keeping the Constant visible when those pieces leave; that amendment is
a dependency of this proposed boundary. Whether a Constant public Service
also makes every member's Grant unrevokable remains open.

This direct Agent deletion is distinct from a Tag-specific kernel operation
that removes one removable Contract layer while leaving the rest of its
tower. The Tag-specific operation identifies the origin; `del agent.name`
does not.

### 4. Mixed Gain and Grant towers

One Agent member name can change kind and origin over time. A public
Operation appears through an Agent-facing Action path, and a public Report
may occupy a name later used by a Record. Therefore deletion cannot infer
ownership from “callable” or “data” alone. It must inspect the visible
Contribution's semantic scope and source:

- an Agent-scoped Contribution means end a Gain, even though it was declared
  inside a Tag;
- a publication adapter from a Tag-scoped Service means revoke a Grant;
- a Host binding follows the Host rule when it is itself visible.

The recommended boundary covers all removable layers at the direct Agent
coordinate. Explicit `Base[ari].name` does not tunnel under it to a lower
same-name Service, because that view still uses Ari's credentials. This is a
security-relevant choice and must be cleared explicitly.

### 5. Capture and liveness

Ordinary captured Action callables retain Python capture behavior. Deleting
the coordinate prevents new resolution; it cannot erase an arbitrary
callable already handed to user code.

A captured public Operation handle is different because it represents a live
Grant. The recommended handle rechecks the Grant when called:

```python
send = ari.Send
del ari.Send
send("report")            # rechecks; strict Resolution Failure
```

Fresh Agent access and a saved `Tag[agent]` view both resolve live state. This
depends on the separately proposed soft-view rule: a saved view is a shortcut
for performing the Tag view resolution now, not a snapshot object.

### 6. Access boundaries

- A Broken Agent may delete one of its own Gains as an explicit repair act.
- Secret deletion requires the composition door and reveals nothing when the
  door is closed.
- An ordinary deletion requested on an arrested Agent first retries its saved
  Rip work. If every retry succeeds, the Agent is released and deletion may
  proceed; if retry fails, Arrested Access Failure occurs before deletion.
  Owning Fix and explicit Rip retain their special recovery paths.
- Losing membership or becoming Broken does not itself count as deliberate
  Grant revocation. Until deliberately revoked, ordinary attempts to use that
  blocked Grant keep the existing Rogue/Broken failure. Whether revocation
  itself is permitted is choice 10 below.
- Constant deletion is refused before mutation.

Python protocol seats need their own implementation boundary. Conceptually a
dunder Action is a Gain, but `del agent.__len__` or `del agent.__enter__`
cannot be implemented as ordinary instance deletion because Python finds
those methods on the runtime type. `__del__` also carries TOP finalization.
Clearance must either define safe runtime-type rebuilding for each supported
protocol or defer dunder Feature deletion to a later STEP.

## Presence and failure

`"name" @ agent` remains the presence query for an Agent **member** Feature.
It becomes false when an Action, Record, Tool value, or Grant has no current
binding. It does not silently expand to Preconditions or Postconditions;
their phase visibility remains a Contract diagnostic unless STEP-SPEC-33 is
separately amended.

Using an ended Gain or revoked Grant is strict. A TOP-managed absent Feature
raises its appropriate missing or named `TagResolutionError`; it does not warn
and substitute `None`, `True`, or a null Action. A name TOP never managed keeps
ordinary Python `AttributeError`. Secret, Rogue, Broken, and Safehouse failures
retain their more specific meanings. Optional use must ask presence first:

```python
if "Fireball" @ wizard:
    wizard.Fireball()
```

An already-read Report value remains ordinary Python data, as described
above. A captured public Operation is still an authority-bearing handle and
therefore rechecks its Grant before use.

## Rationale

Python's `del` is the linguistic act the Director wanted: this Agent no
longer has this Feature here. The present runtime only partially delivers
that meaning. Some bindings disappear while Overlay metadata remains,
conditions require `Contract.Delete`, a Tool keeps a rule that ordinary
attribute language cannot see, and a later Underlay can expose apparently
deleted history. A kernel boundary makes the surface truthful.

Service and Grant preserve TOP's scope law. A Report belongs to its Tag;
deleting one Agent's route cannot delete shared Agency state. `Grant` is the
short access word that pairs naturally with Gain:

> A Tag gives an Agent a Gain. An Agency owns a Service. Publication gives a
> member a Grant to that Service.

## Backwards compatibility

Current `del agent.action` and `del agent.record` can remove a Python binding
without consistently ending the corresponding Overlay history. Conditions
use `Contract.Delete`; published Reports are read-only; published Operation
deletion does not define a persistent per-Agent Grant. These paths change
only after this Brief is cleared and implemented.

The proposal preserves raw Python values already read from Reports and
ordinary callables captured from Actions. Saved public Operation handles fail
closed because they represent live Grants rather than ordinary captured Gains.

## Alternatives considered

| Alternative | Assessment |
| --- | --- |
| Keep `Contract.Delete` as the only condition spelling | Less linguistic and inconsistent with the Director's one Agent Feature deletion, but its Pre/Post behavior must be resolved before replacement. |
| Reveal the lower removable layer | Rejected in the recommended model: direct Agent deletion should not resurrect history the Agent ended. |
| Delete the Tag Service | Rejected: `del agent.name` has Agent scope. `del Tag.report` is the separate Tag-scope act. |
| Call the Tag-owned Feature an Authorization | Rejected: the Service and one Agent's authorization are different things. Service and Grant name them separately. |
| Revoke already-read Report values | Impossible in ordinary Python; revocation can govern later reads only. |
| Treat every callable as a Gain | Rejected: a public Operation's Agent path is a Grant despite looking callable. Semantic origin controls ownership. |

## Open Director decisions

1. **Conditions:** should `del agent.Ready` end only the visible Post Gain, as
   recommended, or both same-name Pre and Post like today's
   `Contract.Delete`? If only a Pre exists, does deletion refuse because the
   Agent owns no Post? If both exist, Post-only deletion leaves the same-name
   Pre visible through condition APIs rather than making the spelling vanish.
   Should the compatibility API change with it?
2. **Boundary scope:** confirm that direct Agent deletion tombstones all
   removable earlier Gain/Grant layers at that name, while any Constant layer
   remains visible.
3. **Repeated deletion:** should deleting an already ended known Feature be
   idempotent? The recommendation is yes; a never-managed Host name keeps the
   Host's normal failure.
4. **Grant restoration:** which acts start a new Grant tower: a fresh Tagging,
   reTag after Rip, a newly published independent Service, late Pin
   publication, or Service delete/redeclare? Calling an already-active Tag is
   currently a no-op and should not restore access accidentally.
5. **Explicit Tag view:** confirm that `Base[ari].name` honors Ari's direct
   deletion boundary rather than reaching a lower same-name Service.
6. **Constant Service:** may an Agent revoke its Grant to a Constant public
   Service, or does Constant make that Grant unrevokable?
7. **Dunders:** include safe runtime-type rebuilding here, or defer direct
   deletion of protocol-seat Actions to a focused STEP?
8. **Soft views:** clear the live-view dependency so a saved `Tag[agent]` view
   follows current state rather than retaining a deleted binding.
9. **Host beneath TOP:** when a Gain above a Host method, property, slot, or
    stored value ends, should the Host Feature become visible again, as
    recommended, or should the Agent-and-name boundary hide it too?
10. **Blocked Grant revocation:** may a Broken or Rogue Agent deliberately
    revoke its own Grant even though it cannot currently use the Service? The
    recommendation is yes because revocation reduces authority; it must not
    evaluate or disclose the Service.

## Acceptance requirements after clearance

- Cover Action, Record, Tool-marked Record, Post, Report Grant and Operation
  Grant deletion with exact presence and failure behavior.
- Cover same-name Pre/Post, conditions excluded from member presence, mixed
  Gain/Grant towers in both orders, independent same-name Services, and a
  Constant below removable layers.
- Prove per-Agent Grant isolation and unchanged direct Tag Service state.
- Distinguish saved Operation handles, already-read Report values, ordinary
  Action handles, fresh access, and a saved live Tag view.
- Cover Broken own-Gain repair, Rogue/Broken published access, Secret doors,
  Safehouse arrest, Pins, Underlays, Rip/reTag, late publication, Host custom
  `__delattr__`, a Host method/property/slot/value below a TOP Gain, repeated
  deletion, and the chosen dunder boundary.
- Preserve Tool admission rules after value deletion and on later assignment.
- Run the full suite, strict failure checks, Overlay fuzzing, leak checks, and all
  performance budgets.

---

### Decision

> **Brief.** The Director settled Feature/Gain/Service/Grant, and that
> `del agent.name` ends an Agent Gain or revokes only that Agent's access to a
> Tag Service. The Director also chose strict use-after-deletion and live Grant
> rechecking for saved Operations on 2026-10-21. The ten mechanics listed above
> remain proposed review points; this STEP does not present them as cleared law.
