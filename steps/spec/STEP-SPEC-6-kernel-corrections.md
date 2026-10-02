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
| A Base the Scope pulled in with a Shape | *Open for the Director.* The Director, 2026-10-01: "If Dire is a shape of wolf... then wolf applies first automatically when applying dire, and then when applying a second time it is idempotent. This was a basic top rule." That says how a Scope applies a Shape and its Base: the Base applies first, with the Shape, and applying it a second time adds nothing, so a Base the Scope names after its Shape is already carried when the Scope reaches it. Whether the Scope then Rips the Base it pulled in stays a question for the Director. The kit leaves it on the Agent, since the Scope Rips the Tags it names that it applied, and only those. The sharpest case: when the Base's Imprint fails at the door, the Shape never lands, the Scope raises before the block runs, and the Base stays on the Agent after the `with`, a Tag the Agent did not have and the Scope never named |
| A Tag the Scope applied that a Shape still requires on the way out (the block applied the Shape) | The Director, 2026-10-02: "deletion should be blocked, yeah, and an error raised the good contract thing to do, because deleting to uncertain states can be problematic". *Drafted for the Director's confirmation:* the Rip is refused, as any Rip of a required Base is (item 1), and the Tag stays on the Agent. The Scope goes on Ripping the rest, then reports the refusal as `del Tag[agent]` does: when the block ended without an exception, the Composition Failure leaves the `with`; when the block raised, its own exception leaves, with the refusal as a note. From 0.1 to 0.2.0a4 the Scope dropped the refusal |
| A teardown that fails as the Scope Rips its Tag | *Drafted for the Director's confirmation, with row 4:* the Tag is Ripped, its membership has ended, and the Scope reports the failure as a Rip does (§3.1, Ring 3: "failures reported"), in the same way as a refused Rip: raised once every Rip is done, or a note on the block's exception. From 0.1 to 0.2.0a4 the Scope dropped it. *Open for the Director:* the Director, 2026-10-02: "I was gonna suggest to just ammend the rule to a failed rip blocks an agent's expulsion". That would leave the Agent in the Tag when a teardown fails, as a Rip refused for a required Base already does (the row above). A teardown runs after membership has ended (§3.1), so this amends every Rip, `del Tag[agent]` too, not only the Scope's. The kit is unchanged on this until the Director rules |
| When, and the spelling | "Rule now, spelling this release, but add Wizard[h, **inputs] to the rule if possible". The spelling `with Wizard[h]:` goes to STEP-SPEC-21, with the inputs as `with Wizard[h](code="007"):`, the spelling the Director chose on 2026-09-30, since the language takes no keywords inside `[...]` |

**Backwards compatibility.** Two programs change. One that relied on a
Scope to Rip a Tag the Agent already carried now keeps the Tag after the
block. One that caught an Imprint or Postcondition failure from a Scope
and expected the Tag to stay now finds it Ripped. Rows 4 and 5, as
drafted on 2026-10-02, change a third: a Scope whose Rip is refused, or
whose teardown fails, now raises the Composition Failure after the
block, or notes it on the block's exception, where 0.2.0a4 said
nothing. The Agent is left as 0.2.0a4 left it.

**Alternatives considered.**

| Alternative | Verdict |
| --- | --- |
| Skip the block when the Agent already carries a named Tag | Not possible without raising: a `with` body cannot be skipped. Drafted for the Director's confirmation, with row 1 |
| Rip every Tag named, as before | Rejected: it takes away a Tag the Scope did not give |
| Rip the Bases a Shape pulled in | Open for the Director, with row 3: the Scope did not name them, but its Shape brought them. That includes a Base whose Imprint failed at the door, which stays though its Shape never landed |
| Drop a Rip the Scope cannot make, as 0.1 to 0.2.0a4 did | Drafted to be replaced, with rows 4 and 5: the Agent would leave the Scope in a state the Scope did not report, where `del Tag[agent]` raises |
| A failed Rip blocks the Agent's expulsion: the Tag stays when a teardown fails | Suggested by the Director on 2026-10-02; open, with row 5. It changes §3.1 for every Rip |

Covered by `tests/test_topkit.py::ScopeTests` and the oracle
(`tests/oracle_topkit.py`, `Exercise_Scope`).

---

### Decision *(filled by the Director)*

> Status set to **Deployed** on 2026-09-05, because the Director approved
> the whole review in PR #3 ("all changes approved"), the rule is
> reflected in `spec/SPECIFICATION.md`, and TopKit 0.2.0a2 covers it in
> `tests/test_topkit.py`. Cleared on 2026-09-05.
>
> *Drafted for the Director's confirmation:* amended on 2026-09-29 (the
> Amendment above), per the Director: "Rule now, spelling this release,
> but add Wizard[h, **inputs] to the rule if possible".
>
> *Drafted for the Director's confirmation:* that a Tag the Agent already
> carries leaves the block running, and that a Rip the Scope cannot make
> leaves its Tag, are this draft's reading.
>
> *Added 2026-10-02, drafted for the Director's confirmation:* the
> Director, on a Rip the Scope cannot make: "deletion should be blocked,
> yeah, and an error raised the good contract thing to do, because
> deleting to uncertain states can be problematic". Recorded in row 4:
> the refused Rip leaves its Tag, and the Scope reports it once every
> Rip is done. This draft reads the words as covering row 5 too, so a
> teardown that fails in a Scope is reported the same way. On a
> teardown that fails, the Director also suggested: "I was gonna suggest
> to just ammend the rule to a failed rip blocks an agent's expulsion".
> Recorded in row 5 as a choice still open; it would change §3.1 for
> every Rip, and the kit is unchanged on it until the Director rules.
>
> *Added 2026-10-02, drafted for the Director's confirmation:* the
> Director, 2026-10-01, on a Base the Scope
> pulls in with a Shape: "If Dire is a shape of wolf... then wolf
> applies first automatically when applying dire, and then when applying
> a second time it is idempotent. This was a basic top rule." Recorded
> in row 3 of the Amendment. It says how the Scope applies the Shape and
> its Base; whether the Scope Rips that Base on the way out stays open.
