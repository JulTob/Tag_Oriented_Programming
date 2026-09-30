# STEP-SPEC-6: Kernel Corrections

- **STEP:** SPEC-6
- **Desk:** spec
- **Title:** Kernel Corrections
- **Author:** Julio Toboso (@JulTob)
- **Status:** Deployed
- **Created:** 2026-09-04
- **Deployed:** 2026-09-05

> One STEP, one topic: resolve the contradictions the review of 2026-09-04
> found between the Specification and its implementations, with no new
> feature.

## Summary

Five clarifications, each choosing between two things the project already
said or did:

1. **Rip never cascades.** The Specification said Rip removes the Agent
   from dependent Shapes' Fields by default; both implementations refused.
   The refusal is the law: a Base cannot be Ripped while an active Shape
   requires it.
2. **Deletion has three tiers.** "Deletion always Rips the Agent" is
   replaced by finalizer (best effort), `Scope` (guaranteed; it Rips the
   Tags it applied, and only those), `At_Exit` (opt-in).
3. **Identity is object identity.** `is`, `id`, hash, equality and host
   behaviour are preserved; nominal type may be a runtime subclass with the
   same name.
4. **Preconditions gate only the current call.** An earlier Tag's gate is
   not re-asked when an unrelated Tag arrives; with inputs it would fail on
   `None`.
5. **Host behaviour is preserved.** A host's special methods keep working
   after tagging, with `bool` the one documented exception once a
   Postcondition is visible. Tag members never leak onto the Agent.

Also editorial: duplicated sections merged, examples corrected, "crunch"
replaced by "override", implementation-specific names removed from the
normative text.

## Rationale

Each choice picks the option that keeps TOP explicit: no hidden protocols
running on Rip, no promise the language cannot keep, no re-asking a gate
with materials that are no longer there.

## Backwards compatibility

No program that ran against TopKit 0.1 changes behaviour under 1, 2 or 4
as first decided. The Amendment of 2026-09-29 to item 2 changes two
kinds of program, listed there.
Under 5, programs that accidentally relied on `agent.Label()`,
`agent.Greet()` or a Report object appearing on the Agent must use the Tag
or the Agent-bound view.

---

## Amendment, 2026-09-29

Found by the oracle in PR #17 (2026-09-21); §0.7 of the Specification
carried the rule from then, and this records it where the tiers were
decided, beside `Scope` in §3.2. Item 2 above carries the amended text.
Under the original rule a Scope Ripped every Tag it named whose tagging
returned without error: a Tag the Agent carried before the block lost it
on exit, and a Tag that broke its promise at the door was left on the
Agent. One gap stayed after PR #17: a Tag whose Imprint failed at the
door stayed applied (§0.6) and was not Ripped.

| Question | The Director's decision |
| --- | --- |
| A Tag the Agent already carries | The Scope adds nothing and takes nothing away. The Director asked: "if hero is in Wizard then the with is skipped. makes sense? with is for trial runs or temporary." *Drafted for the Director's confirmation:* what is skipped is the Scope's tagging and its Rip, and the block still runs, because a `with` cannot skip its body without raising |
| A Tag that applied and then failed at the door (its Postcondition, or its Imprint) | Ripped as the failure leaves the Scope, with the Tags applied before it: the Scope applied it; the block does not run |
| A Base the Scope pulled in with a Shape | Stays: the Scope Rips the Tags it names that it applied, and only those. The words were fixed, not the kit. A Base the Scope names after its Shape is already carried when the Scope reaches it, so it stays too |
| A Tag the Scope applied that a Shape still requires on the way out (the block applied the Shape) | *Drafted for the Director's confirmation:* the Rip is refused, as any Rip of a required Base is (item 1); the Scope catches the refusal, the Tag stays on the Agent, and the Scope goes on Ripping the rest. The kit has done this since 0.1 |
| A teardown that fails as the Scope Rips its Tag | *Open for the Director:* the Tag is Ripped, its membership has ended, and the failure is dropped, where a Rip reports it (§3.1, Ring 3: "failures reported"). The kit has done this since 0.1. The choice: keep dropping it, and say so; or have the Scope raise the Composition Failure after every Rip is done, when the block ended without an exception, and let the block's own exception leave when it raised |
| When, and the spelling | "Rule now, spelling this release, but add Wizard[h, **inputs] to the rule if possible". The spelling `with Wizard[h]:` goes to STEP-SPEC-21, with the inputs as `with Wizard[h](code="007"):`, the spelling the Director chose on 2026-09-30, since the language takes no keywords inside `[...]` |

**Backwards compatibility.** Two programs change. One that relied on a
Scope to Rip a Tag the Agent already carried now keeps the Tag after the
block. One that caught an Imprint or Postcondition failure from a Scope
and expected the Tag to stay now finds it Ripped.

**Alternatives considered.**

| Alternative | Verdict |
| --- | --- |
| Skip the block when the Agent already carries a named Tag | Not possible without raising: a `with` body cannot be skipped. Drafted for the Director's confirmation, with row 1 |
| Rip every Tag named, as before | Rejected: it takes away a Tag the Scope did not give |
| Rip the Bases a Shape pulled in | Rejected: the Scope Rips the Tags it names, and only those |

Covered by `tests/test_topkit.py::ScopeTests` and the oracle
(`tests/oracle_topkit.py`, `Exercise_Scope`).

---

### Decision *(filled by the Director)*

> Status set to **Deployed** on 2026-09-05, because the Director approved
> the whole review in PR #3 ("all changes approved"), the rule is
> reflected in `spec/SPECIFICATION.md`, and TopKit 0.2.0a2 covers it in
> `tests/test_topkit.py`. Cleared on 2026-09-05.
>
> Amended on 2026-09-29 (the Amendment above), per the Director: "Rule
> now, spelling this release, but add Wizard[h, **inputs] to the rule if
> possible".
>
> *Drafted for the Director's confirmation:* that a Tag the Agent already
> carries leaves the block running, and that a Rip the Scope cannot make
> leaves its Tag, are this draft's reading. Whether a Scope reports a
> teardown that fails is open.
