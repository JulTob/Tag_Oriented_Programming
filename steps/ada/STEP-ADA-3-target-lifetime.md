# STEP-ADA-3: Ada Target lifetime

- **STEP:** ADA-3
- **Desk:** ada
- **Title:** Ada Target lifetime
- **Author:** Codex (proposal for @JulTob)
- **Status:** Brief
- **Created:** 2026-10-10

> One topic: how a supported Ada Target carries TOP state for its lifetime.
> No carrier, public syntax, or implementation has been selected.

## Summary

This Brief compares two lifetime arrangements for STEP-ADA-1
([#5](https://github.com/JulTob/Tag_Oriented_Programming/issues/5)):
state inside an opt-in limited host type, or a separate controlled companion
for an existing host. Native Ada probes expose the guarantees and obligations
of each. The Director still chooses the supported Target profile.

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
a companion reduces host intrusion but needs additional lifetime rules. That
trade-off requires the Director's decision, not an inferred choice from Ada's
accessibility checks.

## Alternatives to decide

### 1. Opt-in host with a private lifetime component

The supported host is declared over a limited carrier. TOP state lives inside
the same object, so its private lifetime component cannot end earlier than
that object. The host does not access or replace the component's finalizer.

A plain tagged limited carrier offers this without an outer controlled
finalizer. A controlled outer carrier containing the same private component
also lets the host override `Finalize` without owning the internal cleanup.
These are two native layouts, not a selected public API.

This is the stronger automatic-lifetime candidate from the probes, but it
requires host types to opt in before Tagging. Existing arbitrary types cannot
be retroactively extended in Ada. Cleanup placed only in an overridable
ancestor finalizer is another possible arrangement, with an explicit and
weaker cooperation requirement.

### 2. Separate controlled companion

An existing aliased host can retain its type while a limited companion carries
TOP state and a checked access discriminant refers to that same Target.

This supports more existing hosts, but a profile must additionally prevent or
define early companion destruction, multiple independent companions for one
Target, and deallocation of the Target while a companion survives. A checked
access discriminant is not an ownership or uniqueness guarantee. Programmer
discipline alone must not be described as an automatically enforced law.

### 3. Raw access-value side table

A non-owning side table alone cannot observe every arbitrary Target's end or
distinguish address reuse from the former Target. It still needs a lifetime
carrier or a stated cooperation mechanism. This is storage support, not a
third automatic-lifetime guarantee.

## Remaining decision boundaries

- Does the initial profile support only opt-in limited hosts, or also adapted
  existing hosts? No unsupported host should silently receive unsafe state.
- For unsupported Targets, is rejection at an Ada generic/type boundary the
  accepted profile diagnostic, or is a distinct named TOP runtime failure also
  required? Native compile errors alone have not been approved as the failure
  model's spelling.
- Must a Registry outlive all its Agents, with checked references and scope
  order enforcing ordinary uses, or does an Agent retain the required Tag
  storage? Opaque IDs alone cannot make a destroyed Registry safe to access.
- Which unsafe operations and companion lifetime duties are explicitly outside
  the supported profile? A contained token does not itself solve Registry
  lifetime or every alias held by other code.
- Is the initial task profile sequential, or does it coordinate shared Field
  access with Target destruction? Synchronizing Registry storage alone is not
  a complete answer.
- Does the initial runtime profile require controlled finalization? A pure
  SPARK or `No_Finalization` arrangement needs different support or a stated
  trusted boundary; none is selected by this Brief.
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
status, or experimental Geometry API. All alternatives remain open.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
