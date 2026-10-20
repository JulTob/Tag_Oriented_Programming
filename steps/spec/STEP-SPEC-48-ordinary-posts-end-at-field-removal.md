# STEP-SPEC-48: Ordinary Posts End at Field Removal

- **STEP:** SPEC-48
- **Desk:** spec
- **Title:** Ordinary Posts End at Field Removal
- **Author:** Codex, recording the Director's 2026-10-20 ruling
- **Status:** Brief
- **Created:** 2026-10-20
- **Issue:** [#328](https://github.com/JulTob/Tag_Oriented_Programming/issues/328)
- **Related runtime draft:** [#339](https://github.com/JulTob/Tag_Oriented_Programming/pull/339) (a first Post Underlay receives the neutral `True`; it does not implement Rip layer removal)

> One STEP, one topic. This Brief changes the lifetime of an admitted
> Tagging's ordinary Posts. Constant Post composition, explicit condition
> deletion, and permanent Tag membership need their own decisions.

## Summary

An ordinary Post belongs to the application of the Tag that gained it. When
that application leaves its Field, its ordinary Post layer ends at Field
removal, before any `@Rip` protocol runs. Other Tag applications keep their
own Post layers. A lower same-name Post can then become visible again. A
`@Constant @Post` remains after Rip, as it does today. This Brief records a
new rule for review; current TopKit and the Specification still implement the
sticky ordinary-Post rule of [STEP-SPEC-12](STEP-SPEC-12-the-author-ends-a-condition.md).

## Motivation

Today STEP-SPEC-12 keeps every Post after Rip. A Tag can leave its Field while
its ordinary membership promise continues to judge the Agent, unless its
author added a guard or deleted the condition in `@Rip`. That also leaves a
later same-name Post with a bound Underlay that may still call a check from a
Tag application that has ended. The Director's newer rule is that an ordinary
Post lives at its Tag's layer: leaving that Field ends that application's
promise. When a Post must outlive membership, the author says so with
`@Constant`.

The Director stated: “The non-const Posts live ‘at Tag level’ so it makes
sense that field removal takes out the visibility. End at field removal.”
The change deliberately supersedes STEP-SPEC-12's Post lifetime while
preserving its historical decision and the separate behavior of Preconditions.

## Specification

1. **Application identity.** An admitted Tagging carries the ordinary Post
   layers it gained. TOP distinguishes that application from another
   application of the same Tag to the same Agent. A later Tagging or Pinning
   contributes its own layers; being a Shape does not copy a Base's Post
   application.
2. **End at Field removal.** When Rip removes an application from its Tag's
   Field, TOP ends that application's ordinary Post layers immediately.
   This happens before the first `@Rip` teardown and before any Safehouse
   retry. A failed teardown does not restore those ordinary Posts. Other
   applications' ordinary Posts stay, including those acquired by a fresh
   Tagging inside the old application's `@Rip`.
3. **Visible checks.** If the removed application supplied the visible Post
   at a name, the next surviving Post layer at that name becomes visible.
   If none survives, the name has no ordinary Post and contributes no broken
   promise. A surviving later Post remains its own check when an earlier
   Tag is Ripped; it must not keep invoking a removed check. If its
   `@Underlay @Post` has no surviving lower Post, its `prior()` is a callable
   returning the neutral `True`. Draft [#339](https://github.com/JulTob/Tag_Oriented_Programming/pull/339)
   implements that neutral value for a first Post Underlay, but does not yet
   rebuild a tower after Rip. The exact reconnection around a removed middle
   layer belongs to the separate Post composition design in
   [#328](https://github.com/JulTob/Tag_Oriented_Programming/issues/328).
4. **Constant and mixed conditions.** `@Constant @Post` keeps its existing
   lifetime after Rip. This STEP makes no decision about layering another
   same-name Post over that Constant check. A declaration marked with both
   `@Pre` and `@Post` has its ordinary Post side ended under this rule; its
   Precondition side keeps the current sticky lifetime. Actions and Records
   also keep their existing Rip behavior.
5. **Tags as Agents.** A Pin applies a Tag to another Tag. Ripping that Pin
   membership ends the Pin application's ordinary Posts by the same rule;
   it does not copy or end Posts that belong to other Tags.
6. **Unadmitted attempts.** A Post acquired before a Tagging attempt fails
   without Field entry has no Field removal event. This STEP does not
   silently erase that Rogue Post or decide its later recovery/deletion
   protocol. The law here concerns applications that entered a Field.

For example, if `Base` and then `Later` each apply a `Ready` Post to Ari,
Ripping `Later` reveals `Base`'s `Ready`. Ripping `Base` then ends its own
ordinary `Ready`; a `@Constant @Post Ready` from `Base` would instead remain.
If `Base` is Ripped while `Later` stays, `Later`'s check stays because the two
Tag applications are independent layers.

Under this proposal, the visible layer changes at each Rip:

```python
from TopKit import Post, Tag

class Host:
    pass

class Base(Tag):
    @Post
    def Ready(agent):
        return agent.ready

class Later(Tag):
    @Post
    def Ready(agent):
        return True

ari = Host()
ari.ready = True
Base(ari)
Later(ari)
ari.ready = False
del Later[ari]
assert not ari.Ready             # Base's check is visible again
del Base[ari]
assert not ("Ready" @ ari)       # no ordinary Ready layer remains
```

## Rationale

The Field is the explicit record that a Tag application has been admitted.
Ending that application's ordinary promise at Field removal makes the
contract follow that record without guessing from the Agent's current
Overlay. It also gives `@Constant @Post` a clear purpose: an author who
needs the promise to survive Rip declares permanence. Application identity
protects a deliberate reTag inside `@Rip`: ending old membership cannot
erase a newly trained application just because the Tag class has the same
name.

## Backwards compatibility

This reverses the ordinary-Post portion of Cleared
[STEP-SPEC-12](STEP-SPEC-12-the-author-ends-a-condition.md) and the current
Specification §0.7. That STEP stays on record; this Brief has no effect
until the Director Clears it and the implementation and current guides are
updated. Existing `@Rip` protocols that call
`Contract.Delete(agent, "Ready")` merely to end their own ordinary Post
will need review: their Post would already have ended when the teardown
starts, while another same-name layer may now be visible. The separate
condition-deletion work in #328 must implement the Director's chosen
Tag-specific spelling, `Contract.Delete(agent, Tag, "Ready")`, consistently
with this timing. Authors who intentionally require a promise to remain
after Rip can declare a Constant Post, subject to its own declaration rules.

## Alternatives considered

| Alternative | Reason set aside for this Brief |
| --- | --- |
| Keep all Posts sticky and require guards or `Contract.Delete` (STEP-SPEC-12) | A former Tag's ordinary promise remains in the Agent's contract unless every author remembers extra cleanup. The Director now locates ordinary Posts at the Tag layer. |
| End Preconditions and Contributions as well | Changes independent parts of the Overlay without a Director ruling; they keep their current lifetimes. |
| End the Post only after all `@Rip` teardowns succeed | An Agent may be out of the Field or in a Safehouse while an old ordinary membership promise still judges it. The Director chose Field removal as the boundary. |
| Remove every Post bearing the same Tag class name | A teardown may apply that Tag again. Class-name removal would erase the fresh application's Post. |

## Acceptance requirements

- A top ordinary Post ends at Field removal and reveals an earlier
  same-name Post; a middle Post can end without losing later applications.
  A surviving Post Underlay with no lower layer receives a callable `True`.
- A failing `@Rip` leaves the old ordinary Post ended, including when saved
  cleanup is retried. A fresh same-Tag application made during teardown
  keeps its own Post.
- A Constant Post survives Rip; a combined `@Pre @Post` keeps its Pre side
  while the ordinary Post side ends. A Pin Post follows the same application
  rule when its Target is a Tag.
- A Post gained by an unadmitted attempt is not accidentally treated as an
  admitted application's layer.
- Current Specification, conformance, guides, wiki, oracle, and existing
  sticky-Post tests are updated only after the Director's clearance. The
  historical STEP-SPEC-12 text remains intact with a clear cross-reference.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
