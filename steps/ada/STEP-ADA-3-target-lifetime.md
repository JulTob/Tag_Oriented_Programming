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
| Its host finalizer raises | Component still finalized; GNAT reported `Program_Error` | This probe's cleanup survived the host's exception |
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

The local probes provide scouting evidence, not a deployed implementation or
a complete portable conformance suite. Their final arrangement belongs in a
separate, small implementation PR after the profile decision.

## Backwards compatibility

None: this Brief changes no Python behaviour, Specification, existing STEP
status, or experimental Geometry API. All alternatives remain open.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
