# STEP-ADA-3: Ada Target lifetime

- **STEP:** ADA-3
- **Desk:** ada
- **Title:** Ada Target lifetime
- **Author:** Codex (proposal for @JulTob)
- **Status:** Brief
- **Created:** 2026-10-10

> One topic: how a supported Ada Target carries TOP state for its lifetime.
> The Director selected opt-in limited hosts and sequential use for the first
> implementation, with retained Tag storage and automatic host hooks. The
> concrete storage mechanism and public syntax remain open; this STEP is
> still Brief.

## Summary

This Brief compares two lifetime arrangements for STEP-ADA-1
([#5](https://github.com/JulTob/Tag_Oriented_Programming/issues/5)):
state inside an opt-in limited host type, or a separate controlled companion
for an existing host. Native Ada probes expose the guarantees and obligations
of each. The Director selected the initial host and task scope below; the
remaining Target profile decisions still need resolution.

## Motivation

An Ada Field can hold a non-owning reference without keeping a Target alive,
but that reference must not become a dangling access value when the Target
ends. TOP must preserve the same Target, distinguish its identity from value
equality, and remove a ceased Target from its Fields
([Specification, Ring 0](../../spec/SPECIFICATION.md)).

The carrier is implementation support, not a TOP Base. Ada type ancestry
must not encode independent Tag membership or the Geometry. The experimental
Geometry in [#108](https://github.com/JulTob/Tag_Oriented_Programming/pull/108)
does not yet carry Targets and does not settle this question.

## Specification — proposed profile obligations

Any selected arrangement must explain these obligations before an Ada
implementation claims conformance:

1. Tagging preserves the existing supported Target; a companion must not
   replace it with a different returned object.
2. Field references do not own Targets. When a supported Target ends normally,
   later Field queries cannot follow its expired storage.
3. Ordinary host finalization must not silently omit TOP's internal lifetime
   cleanup. The profile must state any required host cooperation.
4. A live Target must not silently lose membership merely because a separate
   companion ends early. Accessibility alone does not enforce this.
5. Every cleanup reference to Tag/Field storage remains valid. In particular,
   the Registry must not disappear first unless the design safely retains the
   required storage and meaning.
6. Ordinary copying must not silently alias TOP state between distinct Targets.
   Unsupported Target/copy cases need explicit profile diagnostics.
7. Internal eviction must not require a still-usable host during finalization.
   Removing a registered identity must not dispatch back to host Actions or
   inspect extension components that may already have ended.
8. The profile must prevent premature internal eviction, or explicitly state
   any cooperation boundary for visible finalizers. Explicit host `Finalize`
   calls, and cleanup following an earlier Rip, need stated boundaries.
9. The profile must state whether Fields may be used by several tasks and how
   a reader's access remains valid during Target destruction. A Registry lock
   alone does not keep a returned non-owning access value valid.

This does not decide whether Target destruction runs Rip protocols, what a
failed teardown does, or how Tagging failures behave. Those are separate
lifecycle and contract decisions. Internal lifetime cleanup alone is not a
new spelling for Rip of a living Agent.

## Native Ada evidence

Isolated scouting probes ran with GNAT 14.2.0, Ada 2022 and assertions enabled
on 2026-10-10. Carrier probes also passed with all warnings enabled and treated
as errors. No probe implemented TOP membership or claimed conformance.

| Probe | Observed result | Consequence |
| --- | --- | --- |
| Cleanup only in a `Limited_Controlled` carrier's `Finalize`; host overrides without calling it | Host finalizer ran; carrier cleanup did not | An inherited finalizer alone requires cooperation |
| Same host explicitly calls the carrier finalizer | Carrier cleanup ran | Cooperation can work, but is not automatic |
| Plain tagged limited carrier contains a private `Limited_Controlled` component | Component finalized; an ordinary host procedure named `Finalize` was not called automatically | The component's cleanup is independent of that name |
| Declare `overriding Finalize` on that plain host | Compilation rejected: `subprogram "Finalize" is not overriding` | A plain tagged carrier does not provide the controlled host hook |
| Controlled outer carrier also contains the private component; host overrides and omits the ancestor call | Host and component finalized; ancestor finalizer did not run | Containment protects cleanup while allowing the host hook |
| Explicitly deallocate the latter host | Component finalized | Normal deallocation also finalizes the contained component |
| Its host finalizer raises while its master ends normally | Component still finalized; `Program_Error` raised after leaving the master | This bounded-error context requires the other finalizations and then `Program_Error`; it is not evidence for every finalization-exception context |
| Assign a limited carrier or companion | Compilation rejected: `left hand of assignment must not be limited type` | Limited objects prohibit ordinary assignment-copying |
| Checked companion points to an aliased Target in the same scope | Companion finalized while Target was alive, then Target finalized | Normal declaration order can provide valid cleanup access |
| Companion occupies a shorter nested scope | Legal; companion finalized while Target remained alive | Coextensive lifetime is not enforced |
| Companion with a local Target escapes via an allocator | Static rejection, or `Program_Error` accessibility failure through an access parameter | Checked accessibility prevents this ordinary scope escape |
| Heap Target is explicitly freed while its companion survives | Legal; Target ended first | Accessibility does not prevent explicit early deallocation |

The last probe never dereferenced the freed Target. These results concern
ordinary Ada finalization and checked references, not process termination,
unchecked memory manipulation, or a finalizer that never returns. Ada RM
§§7.6–7.6.1 describe controlled finalization; §3.10.2 covers accessibility;
§13.11.2 covers unchecked deallocation.

### Finalization order and the host callback boundary

[Ada RM 7.6.1](https://www.ada-auth.org/standards/22rm/html/RM-7-6-1.html)
paragraphs 7/3 and 9/3 first call the outer controlled object's `Finalize`,
then finalize its components. Component order is generally **arbitrary**,
not a general rule that the parent part follows the extension. Components
with access discriminants constrained by per-object expressions finalize
before ordinary components; several such components finalize in reverse
declaration order. The annotated paragraph 9.b/4 includes the object's actual
extension components in this rule.

This matters for the proposed self-reference, the Rosen layout:

```ada
Token : Lifetime (Carrier'Access);
```

That constraint can change the token's order relative to extension
components. The original carrier probes' token has no self-reference and does
not test this layout. Evaluate separate native identity and order probes. Even
with the special ordering, the outer controlled host's `Finalize` has already
run, and another dependent extension component can precede the parent token.
A host callback cannot assume all host resources remain usable.

Self-reference is useful to investigate registration and stable identity, but
Field **removal** need not dereference the Target. A token can retain an opaque
registered identity and the required Registry handle, and evict that identity
without consulting the host. A cached address alone does not establish identity
across storage reuse. Native counter/event traces are evidence about Ada
mechanics, not an implemented Field or a guarantee of safe host callbacks.

The raising-finalizer probe has a narrower rule: RM 7.6.1(17.2/1) requires
other finalizations associated with the ending master and then `Program_Error`
after leaving that master. Its handler must not accept the original host
exception or a silently swallowed exception. Explicit procedure calls,
abort and termination are different contexts.

### Explicit finalizer calls

A visible `Finalize` is an ordinary callable procedure. Calling a host's
procedure explicitly runs its body; it does not automatically finalize its
contained components. A private token can therefore separate automatic
internal eviction from public host hooks, but an inherited public finalizer
that performs eviction directly can detach a live Agent early.

A later carrier must test explicit host and ancestor calls while the Target
is live, ordinary external inaccessibility of the private token's cleanup,
and normal automatic cleanup afterwards. Internal eviction must tolerate an
already absent entry after an earlier Rip; idempotence does not make premature
eviction correct. Host code can still end its own resources explicitly, and
unchecked operations can bypass ordinary Ada privacy. The supported usage
boundary must say so.

### Task and runtime profile boundaries

All current probes are **sequential scouting**. They exercise no shared Field,
Registry synchronization or concurrent Target destruction, and select no
task profile. Supporting shared Fields would require both synchronized
storage and a rule coordinating Target access with destruction. Returning an
access value or snapshot under a lock and dereferencing it after releasing
that lock can still race with destruction. Registry storage must outlive
every token that uses it; callbacks or Posts must not run under an internal
cleanup lock without a separately justified reentrancy design.

Every arrangement compared here requires automatic controlled finalization,
including the carrier whose outer type is plain tagged limited. These are
finalization-capable Ada runtime candidates, not support for every Ada runtime.
GNAT's implementation-defined
[`No_Finalization` restriction](https://github.com/gcc-mirror/gcc/blob/releases/gcc-14.2.0/gcc/ada/doc/gnat_rm/standard_and_implementation_defined_restrictions.rst)
disables the automatic initialization/finalization machinery they require;
a restricted runtime or build cannot support these arrangements unchanged.
Do not infer a portable type-availability rule from one compiler diagnostic.

[SPARK LRM 7.6](https://github.com/AdaCore/spark2014/blob/16089e43221032b88b1c6ecbd0c1b23bb78e2257/docs/lrm/source/packages.rst)
does not permit controlled types. These controlled carrier implementations
are therefore outside a pure SPARK implementation. A trusted Ada boundary
usable by SPARK callers, or another lifetime arrangement without controlled
types, remains a separate option requiring an explicit verification boundary.
No SPARK proof or `No_Finalization` support is claimed by the native probes.

## Rationale

TOP needs the state lifetime of the same Target, not merely a pointer that is
valid at construction. The probes favour containment for automatic cleanup;
a companion reduces host intrusion but needs additional lifetime rules. The
Director chose containment for the first implementation; the remaining
storage and public-surface choices do not follow from accessibility checks.

## Initial implementation scope confirmed by the Director

On 2026-10-12, the Director chose:

- **Opt-in limited hosts first**, containing private lifetime support.
  Adapting arbitrary existing hosts through separate companions is deferred.
- **Sequential implementation first**. Shared-task Field access and Target
  destruction coordination require a later design and separate evidence.
- **Retain Tag state while Agents carry it**. Ending the Ada scope of a public
  Tag handle must not silently end membership or invalidate the internal
  storage still needed by a live Agent. Fields must never keep Targets alive.
- **Preserve automatic host hooks** through a controlled limited carrier,
  with TOP cleanup in a separate private component. Host initialization and
  finalization remain automatic; a host override cannot omit token cleanup.

These answers choose the first development direction, not the entire profile.
They do not Clear this STEP, choose public package names, or claim Ring 0
conformance. Controlled containment still requires a finalization-capable
Ada runtime and remains outside a pure SPARK implementation.

### Proposed first implementation slices

1. **Target identity and private lifetime support.** Preserve the same host
   object and give distinct Targets distinct opaque identities. Test limited
   assignment refusal, build-in-place construction, explicit host-finalizer
   calls, host initialization/finalization failures and normal deallocation.
   The selected controlled outer carrier preserves automatic host hooks;
   a plain outer carrier is a deferred alternative.
2. **Internal non-owning membership storage.** Connect the token to retained
   Tag storage that never owns its Target. Eviction
   removes the registered identity without dereferencing the host or running
   Actions, Posts or Rip. Repeated internal removal must be harmless, and
   finalization cleanup must not allocate. This internal eviction does not
   decide any separate destruction/Rip protocol. Field mutation remains internal
   to the kernel, rather than a public bypass of Tagging and Rip.
3. **Field selection and walking.** Design how a walk obtains and uses a live
   Target after the storage proof. An identity-only membership table does not
   prove safe Target access. Sequential callbacks can still end a Target or
   change membership during a walk. Rechecking saved entries before use is
   necessary but insufficient if a callback destroys the Target it is using.
   The later design must preserve access for the whole use or explicitly
   refuse unsupported destruction before selecting a borrowing API.

These are separate reviewable proposals. No Gate, Contribution, Imprint,
Postcondition, Geometry integration or public Tagging/Rip implementation is
introduced by this scope record.

### Selected storage-lifetime direction

An Agent may outlive the Ada scope of a public Tag handle. The Director selected
the first arrangement; the second remains a considered alternative:

- **Retain private Tag/Registry storage while Agents require it.** A public
  handle can end without silently expelling its live Agents. Retained storage
  must be reclaimed when no required reference remains, and its Field entries
  must not keep Targets alive. This follows the existing Python Agent-to-Tag
  retention pattern, but requires a private storage-lifetime mechanism.
- **Require Tags/Fields to outlive their Agents in the first Ada profile.**
  Checked access discriminants can enforce ordinary scope accessibility.
  This imposes a visible construction/lifetime restriction and still does
  not make explicit early deallocation of referenced storage safe.

Retained metadata does not retain the host object. The implementation must
test that a Tag handle can end before its Agent, that the Agent can end before
the last Tag handle, and that the retained storage is eventually reclaimed.
Retaining metadata does not itself justify following a saved Target access
value. It also cannot extend the lifetime/accessibility of local objects,
host types or nested callbacks referenced by future Contributions. Geometry,
persistent Posts and has-been history may require metadata after Rip; leaving
a Field must not silently discard those references. No application-wide
Registry or unsafe access conversion is implied by the contained-host choice.

## Lifetime arrangements considered

### 1. Opt-in host with a private lifetime component

The supported host is declared over a limited carrier. TOP state lives inside
the same object, so its private lifetime component cannot end earlier than
that object. The host does not access or replace the component's finalizer.

A plain tagged limited carrier offers this without an outer controlled
finalizer. A controlled outer carrier containing the same private component
also lets the host override `Finalize` without owning the internal cleanup.
These are two native layouts. The Director selected the controlled outer
carrier containing the private component for the first implementation so
automatic host hooks remain available. Public package names are still open.

This is the stronger automatic-lifetime candidate from the probes, but it
requires host types to opt in before Tagging. Existing arbitrary types cannot
be retroactively extended in Ada. Cleanup placed only in an overridable
ancestor finalizer is another possible arrangement, with an explicit and
weaker cooperation requirement.

### 2. Separate controlled companion

An existing aliased host can retain its type while a limited companion carries
TOP state and a checked access discriminant refers to that same Target.

This deferred alternative supports more existing hosts, but a profile must
additionally prevent or define early companion destruction, multiple
independent companions for one
Target, and deallocation of the Target while a companion survives. A checked
access discriminant is not an ownership or uniqueness guarantee. Programmer
discipline alone must not be described as an automatically enforced law.

### 3. Raw access-value side table

A non-owning side table alone cannot observe every arbitrary Target's end or
distinguish address reuse from the former Target. It still needs a lifetime
carrier or a stated cooperation mechanism. This is storage support, not a
third automatic-lifetime guarantee.

## Remaining decision boundaries

- The initial direction is opt-in limited hosts; companion adaptation is
  deferred. No unsupported host should silently receive unsafe state.
- For unsupported Targets, is rejection at an Ada generic/type boundary the
  accepted profile diagnostic, or is a distinct named TOP runtime failure also
  required? Native compile errors alone have not been approved as the failure
  model's spelling.
- Agents retain the required Tag storage. Its concrete retention/reclamation
  mechanism must be tested; opaque IDs alone cannot make destroyed storage
  safe to access.
- The carrier preserves automatic host hooks with a controlled outer type
  and private contained cleanup; the concrete experimental surface remains
  to be reviewed.
- Which unsafe operations and companion lifetime duties are explicitly outside
  the supported profile? A contained token does not itself solve Registry
  lifetime or every alias held by other code.
- The initial implementation is sequential. A later shared-task profile must
  coordinate Field access with Target destruction; synchronizing Registry
  storage alone is not a complete answer.
- The selected controlled carrier requires finalization-capable Ada. A pure
  SPARK or `No_Finalization` arrangement is deferred and would need different
  support or a stated trusted boundary.
- Is the private token self-referential, and how is its registration identity
  retained without host callbacks during eviction? Public host finalizers must
  not be mistaken for private cleanup entry points.

Limited types forbid ordinary assignment, not creation of a fresh Target by
build-in-place initialization. No clone, nominal Tag type, contribution, or
replacement-object protocol is proposed here.

## Acceptance for a later implementation

After the Director chooses the profile, publish its carrier tests before
claiming conformance: stable Target identity; equal-but-distinct Targets;
non-owning Field removal on normal Target destruction; host finalizer override
and exception cases; supported deallocation; rejected copying; and the
Registry/Target lifetime boundary. Any companion option also needs tests for
early end, duplicate companions, and static/dynamic accessibility failure.

For a contained token, additionally demonstrate the proposed Rosen layout
if used: checked self-reference to the same live Target, distinct identities,
supported build-in-place construction and deallocation, ordinary versus
dependent extension-component order, and cleanup by registered identity
without dereferencing or dispatching to the host. Test explicit visible
finalizer calls before normal end and access refusal for private cleanup.

State the actual compiler/runtime and SPARK boundary. If shared task use is
selected, demonstrate removal racing with lookup/iteration and the rule
preventing expired Target dereference, including Registry shutdown. If only
sequential use is selected, say so rather than treating sequential counters
as concurrent Field evidence.

The local probes provide scouting evidence, not a deployed implementation or
a complete portable conformance suite. Their final arrangement belongs in a
separate, small implementation PR after the profile decision.

## Backwards compatibility

None: this Brief changes no Python behaviour, Specification, existing STEP
status, or experimental Geometry API. It records the confirmed initial host
and task scope while leaving the remaining profile choices open.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
