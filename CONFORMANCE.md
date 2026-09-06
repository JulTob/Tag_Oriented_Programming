# Conformance

An implementation of TOP, in **any** language, is *conformant* when it
preserves the observable semantics of [`spec/SPECIFICATION.md`](spec/SPECIFICATION.md)
for every ring it claims, and passes the conformance suite for those rings.

## Rings

The Specification is written in rings. Conformance is claimed per ring,
from the inside out: a Ring 2 implementation also satisfies Rings 0 and 1.

| Ring | Laws, in short |
| --- | --- |
| **0 · Kernel** | stable identity and preserved host behaviour; upward-closed membership with a has-been check; non-owning identity-indexed Fields; Base-first Forms; the five-step tagging sequence with rollback on gate and Record failure; Rip sticky, refused while required, never cascading |
| **1 · Contributions** | two scopes, one slot per `(scope, name)`; latest-Layer Overlay with captured Underlays and stored-value Records; Tag members invisible on the Agent; `@Secret` and `Public` publication with a composition door; Delete; three access forms; Pins: Tags as Targets, the receiver rule, Fields never mixed |
| **2 · Contracts** | strict boolean conditions; Preconditions gate only the current call; Imprints after commit; Postconditions once per call and re-checked later; Forward-Post, Backward-Pre with weakening diagnosed; defective Agents, truthiness, sound and defective partitions; a failure names its check (`except Precondition.X`) |
| **3 · Lifecycle** | `@Rip` protocols after membership ends; the three deletion tiers |

Surface spellings may differ between languages. The **semantic laws** may
not. Every failure in the failure model must stay distinct and named.

## The conformance suite

`tests/test_tagkit.py` is organized by ring and is the seed of the
language-agnostic suite. Test classes named for a ring assert laws; a port
in another language satisfies the behaviours those tests assert, in its
own spelling. Tests that exercise Python-only mechanics (garbage
collection, weak references, warnings) are profile tests, not laws.

## The "TOP Verified" mark

Implementing TOP is free and open. **Claiming conformance under the "TOP
Verified" / "TOP-conformant" designation** is what the steward authorizes,
per implementation and per ring, so the mark continues to mean something.
Request review by opening an issue.
