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
   replaced by finalizer (best effort), `Scope` (guaranteed), `At_Exit`
   (opt-in).
3. **Identity is object identity.** `is`, `id`, hash, equality and host
   behaviour are preserved; nominal type may be a runtime subclass with the
   same name.
4. **Preconditions gate only the current call.** An earlier Tag's gate is
   not re-asked when an unrelated Tag arrives; with inputs it would fail on
   `None`.
5. **Accepted host behaviour is preserved.** A host's special methods
   keep working after tagging, with one documented exception: a host's
   `__len__` keeps answering `len(agent)`, but never supplies an Agent's
   contract truth. An explicit host `__bool__` is refused before Tagging;
   the truth protocol is reserved for Posts (STEP-SPEC-40). Tag members
   never leak onto the Agent.

Also editorial: duplicated sections merged, examples corrected, "crunch"
replaced by "override", implementation-specific names removed from the
normative text.

> **Later spelling:** STEP-SPEC-31 retires `Scope`. The three-tier law
> remains, but the guaranteed tier is now written directly by the program:
> tag before `try`, then Rip in `finally`.

> **Later Director ruling on rule 1:** The automatic refusal to Rip a Base
> while an active Shape remains is superseded. Applying a Shape still adds
> its missing Bases first, but each completed membership then stands alone.
> Ripping a Base leaves the Shape active and does not cascade; a Shape that
> needs continuing Base membership states that need in a Postcondition.
> Applying an already active Shape stays a no-op, while explicitly applying
> the Ripped Base starts fresh Tagging. See Specification §§0.3, 0.5, 0.7
> and [STEP-SPEC-26](STEP-SPEC-26-a-shape-keeps-no-base-hostage.md)
> ([issue #184](https://github.com/JulTob/Tag_Oriented_Programming/issues/184)).
> This note changes only the later law; the 2026-09-05 decision below is
> retained as history.

## Rationale

Each choice picks the option that keeps TOP explicit: no hidden protocols
running on Rip, no promise the language cannot keep, no re-asking a gate
with materials that are no longer there.

## Backwards compatibility

No program that ran against TopKit 0.1 changes behaviour under 1, 2 or 4.
Under 5, programs that accidentally relied on `agent.Label()`,
`agent.Greet()` or a Report object appearing on the Agent must use the Tag
or the Agent-bound view.

---

### Decision *(filled by the Director)*

> Status set to **Deployed** on 2026-09-05, because the Director approved
> the whole review in PR #3 ("all changes approved"), the rule is
> reflected in `spec/SPECIFICATION.md`, and TopKit 0.2.0a2 covers it in
> `tests/test_topkit.py`. Cleared on 2026-09-05.
