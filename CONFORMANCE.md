# Conformance

An implementation of TOP, in **any** language, is *conformant* when it
preserves the observable semantics of [`spec/SPECIFICATION.md`](spec/SPECIFICATION.md)
for every ring it claims, and passes the conformance suite for those rings.

## Rings

The Specification is written in rings. Conformance is claimed per ring,
from the inside out: a Ring 2 implementation also satisfies Rings 0 and 1.

| Ring | Laws, in short |
| --- | --- |
| **0 · Kernel** | stable identity and preserved host behaviour; upward-closed membership with a has-been check; non-owning identity-indexed Fields; Base-first Forms; the five-step tagging sequence with rollback on gate and Record failure; Rip sticky for contributions and for conditions (the author ends a condition: a guard, or `Contract.Delete` from the `@Rip` protocol), refused while required, never cascading |
| **1 · Contributions** | two scopes, one slot per `(scope, name)`; latest-Layer Overlay with captured Underlays and stored-value Records; Tag members invisible on the Agent; `@Secret` and `Public` publication with a composition door, published members answering members only, and only sound ones (Rogue Access Failure for a Rogue Agent, the named promise for a defective one); Delete; three access forms; Flags: opt-in keywords by name, by their words and by class, marked where the Tag is declared, one seat for `in`; Pins: Tags as Targets, the receiver rule, patching Tag-scope declarations with collision control, publication onto the Field, Fields never mixed |
| **2 · Contracts** | strict boolean conditions; Preconditions gate only the current call; Imprints after commit; Postconditions once per call and re-checked later; Forward-Post, Backward-Pre with weakening diagnosed; defective Agents, truthiness, sound and defective partitions, populations combined with `|`, `&`, `-` at every level; a condition read on the Agent by its name as a plain bool, a non-boolean raising the Contract Failure and a gate read without the tagging's inputs, its name refused to other kinds; a failure names its check (`except Precondition.X`); `@Pre` and `@Post` stacked as one condition, spelled `@Requirement` in one word |
| **3 · Lifecycle** | `@Rip` protocols after membership ends on a Rip, and while the Agent is still a member at deletion and in the `At_Exit` pass; a failed teardown on an explicit Rip refuses the Rip and rolls it back (a Composition Failure); in the `At_Exit` pass it rolls that Agent back and is reported, as a finalizer's error; at deletion it is reported and blocks the deletion, the Agent rolled back and kept in the safehouse, `Tag[...]`, a population over each Tag's tree of Shapes, left by an explicit Rip; triage, `del Tag[...]`, letting the kept Agents go without their teardowns, one Triage Warning each; the three deletion tiers, a Scope Ripping the Tags it applied and only those, leaving one a Shape still requires, and reporting a Rip it cannot make; the Agent's `__del__` as Layers of its Overlay, after the teardowns, alone once the interpreter is finalizing at exit; the Agent's own Actions answering its teardowns and Layers at deletion |

Surface spellings may differ between languages. The **semantic laws** may
not. Every failure in the failure model must stay distinct and named.

## The conformance suite

`tests/test_topkit.py` is organized by ring and is the seed of the
language-agnostic suite. Test classes named for a ring assert laws; a port
in another language satisfies the behaviours those tests assert, in its
own spelling. Tests that exercise Python-only mechanics (garbage
collection, weak references, warnings) are profile tests, not laws.

## The "TOP Verified" mark

Implementing TOP is free and open. **Claiming conformance under the "TOP
Verified" / "TOP-conformant" designation** is what the steward authorizes,
per implementation and per ring, so the mark continues to mean something.
Request review by opening an issue.
