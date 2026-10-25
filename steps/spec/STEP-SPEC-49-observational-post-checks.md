# STEP-SPEC-49: Postconditions Are Observational Checks

- **STEP:** SPEC-49
- **Desk:** spec
- **Title:** Postconditions Are Observational Checks
- **Author:** Codex, recording the Director's read-only Post ruling
- **Status:** Brief
- **Created:** 2026-10-20
- **Issue:** [#344](https://github.com/JulTob/Tag_Oriented_Programming/issues/344)

> One STEP, one topic. This Brief records a design direction, not a deployed
> read-only guarantee or a decision about when Posts are evaluated.

## Summary

A Postcondition judges an Agent or Tag by reading it. It may calculate, read
Records and Reports, and call observational Actions, but it must not change
the Agent, another Agent, a Tag, a Field, a contract, or the outside world.
The Director ruled: **“Posts are read-only checks.”** This STEP proposes how
TopKit should guard explicit TOP acts during a Post. Direct Python writes,
including writes to Agent Gains, remain violations of the authoring rule
without a general runtime write hook.

## Motivation

TOP asks Posts while deciding Agent truth, Tag truth, named conditions,
diagnostics, and sound or defective populations. If one of those checks
Rips a member, changes a Record, or ends another Post, the act of asking a
question changes the answer and can even invalidate a contract walk. A new
Tagging can also inspect the existing contract before its Gate; a mutating
Post could change the source before that Gate refuses it. A condition is a
promise to be judged, not an Imprint or Rip protocol.

Current TopKit marks an executing Post for same-Agent soundness recursion,
but that marker does not guard TOP mutations. Existing Precondition/Record
observation work already distinguishes explicit TOP acts from ordinary
Python assignments. A general Agent write hook was tried: it was costly
and could still be bypassed. The Director chose an explicit TOP-act guard
plus the authoring rule for direct assignments instead.

## Proposed specification

1. **Observation.** Every Post evaluation is read-only. Local calculation
   and retrieval are allowed. Calling an Action to retrieve or calculate is
   allowed only while the entire call remains observational. A Post is not a
   place for Tagging, Rip, Imprint, contract deletion, Field changes, late
   declaration changes, or writes to an Agent's Gains.
2. **One rule at every read.** The rule applies to ordinary Agent Posts,
   Posts gained by a Pin on a Tag, and any future native Tag Posts. It applies
   whenever a Post runs: after Tagging, through `bool(agent)` or `bool(Tag)`,
   a named condition read, `Contract` diagnostics, publication guards, and
   sound or defective population queries. This STEP does not choose the
   scheduling of those reads or change population membership algebra.
3. **TOP-bound effects.** TopKit should refuse its own mutating acts before
   they take effect during a Post, including application/Rip, `Contract.Delete`,
   and late TOP declaration changes and marks. Calling through an Action or
   an Underlay does not evade this guard when that call attempts an explicit
   TOP act. An attempted forbidden act must not make the enclosing Post
   appear to pass merely because the Post catches the immediate exception.
   The exact guard and error representation remain implementation choices.
4. **Python boundary.** Direct assignment or deletion, including
   `agent.wheels = 2` and `del agent.Start`, violates the same read-only
   authoring rule, but TopKit does not install a general hook to intercept
   those Python operations. The author must also keep host methods and
   other values it calls observational. TopKit cannot generally stop
   mutation of arbitrary Python objects, I/O, or external calls. It does
   not promise a copy of the world or rollback of arbitrary Python effects.
   The mechanically enforced boundary is explicit TOP acts; the remaining
   boundary is the author's responsibility.
5. **Reentrancy.** Recursive validity checks have their own rule: the
   Director chose neutral `True` at a revisited Post check, including sound
   population queries, Agent truth, and Contract diagnostics. That rule
   supersedes the current same-Agent Contract Failure and needs its own
   focused STEP and runtime change (#291, #295 and #33). `Tag[:]` remains a
   raw Field-membership question. This STEP concerns observation: a blocked
   TOP mutation cannot become a passing Post merely because a recursive
   check returns neutral `True`.
6. **Failure reporting.** A detected mutation attempt should make that Post
   fail under the existing named Post diagnostic, so a detailed check names
   the offending Post while boolean and population reads do not report a
   false soundness verdict. Preserve the underlying refusal as diagnostic
   cause. Python interruptions such as `KeyboardInterrupt` and `SystemExit`
   retain their own interruption semantics. Whether the public API needs a
   dedicated observation error, and how caught attempts are tracked across
   nested checks, remain open implementation details.

## Rationale

Post truth is useful only when reading it does not itself carry out a TOP
act. The existing observation pattern for Preconditions and Record
calculations is a starting point, but Posts are reached by more paths.
Guarding explicit TOP acts at those paths gives a practical mechanical
boundary while allowing ordinary calculations and read-only Actions.
Direct Python writes remain prohibited by the authoring rule even though
that guard cannot detect them.

This rule does not freeze the world between checks. A later read may give a
different verdict because an Imprint, Rip, repair, or host event changed
state in between. The restriction concerns effects **during** the Post's
own evaluation.

## Backwards compatibility

Programs whose Posts deliberately Tag, Rip, delete conditions, or write
Gains while answering a truth query must move those effects to an Imprint,
Rip, repair, or explicit Action and leave the Post as a check. Existing
population tests that Rip or re-Tag from inside a Post are examples to
replace with mutation between walk turns. STEP-SPEC-35's implementation
note about state-changing conditions then needs a compatibility annotation;
its cleared membership-at-each-turn rule remains intact.

This Brief does not amend the Post lifetime proposal in STEP-SPEC-48, the
truth meaning of STEP-SPEC-40, or the condition-name semantics of
STEP-SPEC-14. Their checks would simply execute under the observational
rule once implemented. The historical STEP-SPEC-12 and current
Specification/GUIDE wording require a focused amendment when this rule is
cleared and deployed.

## Alternatives considered

| Alternative | Assessment |
| --- | --- |
| Copy the Agent for every Post | Copies cannot faithfully isolate arbitrary Python objects, Tags, Fields or I/O; a verdict on a copy might not describe the real Agent. |
| Intercept every Python write through an Agent hook | Tried and set aside by the Director: the measured cost was high and a host can still bypass the hook. Direct writes remain authoring violations. |
| Disallow every Action call in a Post | Forbids useful retrieval and calculation even when no state changes. Guard the effect, including nested calls, instead. |
| Trust authors even for explicit TOP acts | Gives no protection against an accidental Tagging, Rip or contract deletion during a Post. |

## Dependencies and acceptance for implementation

- Coordinate with the observation work in [#305](https://github.com/JulTob/Tag_Oriented_Programming/issues/305) and [#310](https://github.com/JulTob/Tag_Oriented_Programming/issues/310), the source-sound check in [#333](https://github.com/JulTob/Tag_Oriented_Programming/issues/333), and the contract-walk mutation failure in [#101](https://github.com/JulTob/Tag_Oriented_Programming/issues/101).
- Test each Post entry path above with explicit TOP acts, including an act
  called through an Action or Underlay. A caught refusal must not let the
  Post report success. Observational Actions and Underlays must still work.
- Test same-Agent recursive soundness, raw `Tag[:]` membership, nested Posts,
  normal Post exceptions, and Python interruptions without raw dictionary
  iteration errors or silent success.
- Update the Specification, guides, STEP-SPEC-35 implementation note, and
  population tests together with the runtime change. Do not change the
  cleared per-turn membership law to preserve a mutating-Post test.
- State plainly in user guidance that direct Agent Gain assignments and
  deletions are prohibited in Posts by the authoring rule but are not caught
  by a general runtime write hook, as are arbitrary host mutations and I/O.

### Decision *(filled by the Director)*

Status remains **Brief**. The Director's 2026-10-20 ruling establishes that
Posts are read-only checks and settles the enforcement boundary: mechanically
guard explicit TOP acts, while direct Python assignments, including Agent
Gain writes/deletes, remain authoring violations without a general write
hook. The detailed diagnostic and reentrancy rules still require review.
