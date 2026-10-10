# STEP-ADA-1: Ada Ring 0 Profile

- **STEP:** ADA-1
- **Desk:** ada
- **Title:** Ada Ring 0 Profile
- **Author:** Julio Toboso (@JulTob); refresh proposed by Codex
- **Status:** Brief
- **Created:** 2026-09-13
- **Updated:** 2026-10-10
- **Issue:** [#5](https://github.com/JulTob/Tag_Oriented_Programming/issues/5)

> One STEP, one topic: identify the portable Ring 0 obligations and the
> Ada profile decisions needed to implement them. This refresh is a proposal,
> not a conformance claim or a decision on unresolved Python lifecycle work.

## Summary

An Ada implementation must preserve TOP's identity, membership, Field and
Form distinctions using Ada-native mechanisms. This STEP separates those
laws from Python mechanisms and identifies the remaining Ada profile choices.
The Director decides the profile; an experimental implementation may test an
independent law without making its package names the final language surface.

## Motivation

The original Brief in #5 predates the current Contribution tests and the
Director's Tagging decisions. Copying its whole-call rollback model would
port an obsolete design. Copying Python class surgery would mistake a host
mechanism for TOP. Conversely, claiming that any Ada access-value map is a
non-owning Field would overlook object destruction and address reuse.

## Sources and authority

- [Specification, Ring 0](../../spec/SPECIFICATION.md#ring-0--the-kernel).
- [Conformance](../../CONFORMANCE.md).
- [Python conformance seed](../../tests/test_topkit.py), supplemented by
  [Imprint failure](../../tests/test_nested_imprint.py),
  [Presence](../../tests/test_contribution_presence.py) and
  [Constant](../../tests/test_constants.py) tests where they touch the kernel.
- Director clarifications recorded in [#30](https://github.com/JulTob/Tag_Oriented_Programming/issues/30).

The Director's decisions control this proposal. A test is evidence of the
current Python implementation, not authority to reverse those decisions.
At the refresh baseline, `main` is `aff6f79` (2026-10-10). Some Specification
and test passages still describe whole-call restoration. This STEP records
that mismatch instead of silently adopting it as Ada law.

## Specification

### 1. Portable obligations

| Area | Obligation | Status at this refresh |
| --- | --- | --- |
| Identity (§0.1) | Tagging does not replace the Target; equal distinct Targets remain distinct; ordinary host behavior survives unless deliberately overlaid | Established |
| Vocabulary (§0.2) | Preserve Tag, Target, Agent, Field, Base, Shape, Form, Layer, Overlay and Underlay distinctions | Established |
| Membership (§0.3) | Distinguish active membership from has-been history; queries do not Tag; Fields are identity-indexed and non-owning | Established; Ada lifetime mechanism open |
| Form (§0.4) | Ordered Base-first closure, each Tag once; direct Bases retain declaration order; TOP Geometry is independent of a Target's Ada nominal inheritance | Established |
| Apply (§0.5) | Apply pending Tags Base-first; active reapplication does nothing; fresh reapplication after Rip repeats ordinary training | Established |
| Gate (§0.6) | Each pending Tag passes its own Gate when its turn arrives; completed earlier Taggings remain if a later Gate refuses | Director-approved; Python work tracked in #30 / PR #78 |
| After Gate (§0.6) | A failure after that Tag's Gate leaves it tagged, not refused; completed gains are not restored to a checkpoint; current Postconditions decide deficiency | Director-approved; exact Record failure flow remains open in #30 |
| Current state (§2.5) | Postconditions define requirements; missing declared gains alone and a past Imprint failure do not permanently mark deficiency | Director-approved; existing Imprint/current-state tests cover part of it |
| Rip (§0.7) | Rip ends active membership, not history; ordinary gains are sticky; reapplication is fresh; no implicit cascade | Established; several lifecycle extensions remain Brief |

The profile must not import an irreversible-ban feature: a programmer can
express a ban with a Report and Gate; no such TOP language feature has been
decided. Existing required-Base Rip refusal is a deployed Python rule, not
authority to settle the separate spin-off/arrest proposals.

### 2. Native Ada spellings: candidates, not decisions

Ada cannot overload `in` as arbitrary collection membership, and a function
call cannot stand alone as a Tagging statement. The original Brief's
`Agent in Wizard.Field` must therefore not be advertised as working Ada.

| Act | Candidate Ada direction | Choice still required |
| --- | --- | --- |
| Tagging | Package-level `Apply (Wizard, Agent)` | Carrier and input representation; final names |
| Active membership | Package-level query distinct from history | Query spelling and how Tag/Agent handles participate |
| Has-been | Separate history query | Must not collapse into active membership or Ada nominal type |
| Sound Field iteration | Iterable aspect and `for Agent of Population loop` | Population object and contract execution model |
| Whole Field | Distinct population value | Must include deficient Agents without judging soundness |
| Form | Package-level query yielding ordered Tag descriptors | Result type and identity representation |
| Rip | Package-level procedure | Failure model and supported lifecycle boundary |
| Agent-bound view | Generalized indexing is a possible later surface | Ring 1 design; not implemented by this STEP |

Package-level acts keep a Tag's programmer-owned Contribution namespace
available. Prefixed `Wizard.Apply (Agent)` is another possible profile, but
it reserves a name and requires a tagged descriptor; neither choice is
Cleared here. Ada iterable and indexing aspects are mechanisms, not substitutes
for deciding TOP's observable acts.

### 3. Identity and non-owning Fields

Standard Ada does not provide Python weak references for arbitrary access
values. A side map keyed only by an address cannot know that a Target was
deallocated, and may confuse a reused address with the previous Agent.

Two plausible first supported profiles are:

1. An opt-in limited carrier that host Targets explicitly extend. A private
   controlled lifetime component can perform internal cleanup independently
   of a host override of `Finalize`. Cleanup placed only in an inherited
   `Finalize` instead requires explicit host cooperation.
2. A caller-owned controlled companion attached to an existing aliased
   Target. The companion owns TOP state, not the host Target; the profile
   must guarantee its lifetime does not outlast or misidentify that Target.

Containment offers the stronger automatic-lifetime candidate but constrains
host types. A companion preserves more existing host structures, but requires
defined lifetime ordering, uniqueness and deallocation rules; checked
accessibility alone does not enforce these. The native evidence is recorded
in [STEP-ADA-3's issue #117](https://github.com/JulTob/Tag_Oriented_Programming/issues/117).
A raw address registry is useful only as a scoped experiment, not evidence
that the non-owning Field law has been met.

No carrier choice, copying rule, task-safety promise or ownership transfer
is decided by this STEP. Ada unsupported Targets must fail explicitly rather
than silently acquire shared or dangling state.

### 4. Law versus Python mechanism

Source methods below are in `tests/test_topkit.py`. Rows classify the
assertion, not the entire Python test as one indivisible law.

| Test / assertion | Portable law | Python mechanism or profile detail |
| --- | --- | --- |
| `test_tagging_preserves_identity_and_builds_base_membership` | Same Target; upward membership after Shape Tagging | `is`, `id`, runtime subclass checks |
| `test_runtime_type_keeps_the_host_name` | Host type name remains intact (§0.1) | Python runtime `type(...).__name__` |
| `test_direct_bases_apply_in_declaration_order_and_diamond_once` | Base-first ordered Form, diamond once | Class bases and Python declarations |
| `test_active_reapply_is_a_strict_noop` | No new membership, Records or Imprints | Python call spelling |
| `test_fields_are_non_owning_and_iterable_from_the_tag` | A Field does not own Targets; expired Targets vanish | `weakref`, `gc.collect`, Python iterator mechanics |
| `test_fields_index_by_identity_not_equality` | Equal distinct Targets count separately | Python equality and hashing hooks |
| `test_targets_that_cannot_carry_top_state_fail_explicitly` | Unsupported Targets fail explicitly | Python layout restrictions; Ada support set may differ |
| `test_membership_queries_do_not_actualize_an_untagged_target` | Queries do not perform Tagging | Python state dictionary and actualization |
| `test_isinstance_is_a_reliable_has_been_check` | History survives Rip and differs from is-now | `isinstance` is Python's history spelling |
| `test_runtime_types_are_shared_across_agents_and_shapes` | No specific cache law | Python runtime type sharing / performance profile |
| `test_host_special_methods_survive_tagging` | Existing host operations retain behavior | Python special-method lookup |
| `test_copying_an_agent_is_refused_explicitly` | Do not silently alias two Targets' TOP state | Python refuses copying; Ada's exact copy policy is open |
| `RipTests` membership/history assertions | Rip ends membership; sticky gains; fresh reapplication | `del Tag[agent]`, Python collection timing |

Tag member visibility, special-method Actions, Underlay, publication, Presence
and Constant belong to Ring 1 or later. Conditions and deficient populations
touch Ring 0's sequence but their complete model belongs to Ring 2. None can
be declared implemented merely because Geometry works.

## Implementation staging

1. Test Geometry/Form alone in an explicitly experimental namespace. This
   needs no Target carrier or unresolved failure protocol.
2. Decide the lifetime/identity profile, then test membership/history and
   non-owning Fields on supported host Targets.
3. Implement Tagging and Rip only after their relevant failure boundaries
   are precise; port assertions rather than Python internal mechanisms.

`Scope` is being retired by Director instruction (PR #60); it is not an Ada
requirement. Preconditions and Record builders are observational, with query
Actions allowed; enforcement remains #40. Whole-Field Rip (#35), failed-Rip
arrest/retry (#36), safehouse (#37), filters (#38), Links (#39) and deletion
continuation (#34) are separate designs. They are not silently added to ADA-1.

## Acceptance

Before Cleared, the Director must select the native surface and supported
Target/lifetime profile, accept the portable-law matrix, and resolve or explicitly
defer every lifecycle dependency affecting the claimed Ring 0 boundary.

Before an implementation claims Ring 0 conformance, it must run Ada law tests
for that boundary, document unsupported Targets and profile differences, and
demonstrate non-owning lifetime behavior. A compiling Geometry experiment is
not a conformant Ring 0 implementation. The steward grants the mark.

## Backwards compatibility and alternatives

This Brief refresh changes no Python runtime, normative Specification or
STEP status. It keeps the original portable-law goal while deferring final
Ada spellings. A single Rings 0–3 port would obscure independent decisions;
translating Python dunders or assuming an address map's lifetime safety would
not establish TOP conformance.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
