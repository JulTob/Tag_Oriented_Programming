# Conformance

An implementation of TOP, in **any** language, is *conformant* when it
preserves the observable semantics of [`spec/SPECIFICATION.md`](spec/SPECIFICATION.md)
for every ring it claims, and passes the conformance suite for those rings.

## Rings

The Specification is written in rings. Conformance is claimed per ring,
from the inside out: a Ring 2 implementation also satisfies Rings 0 and 1.

| Ring | Laws, in short |
| --- | --- |
| **0 · Kernel** | stable identity and preserved host behaviour; upward-closed membership with a has-been check established at FieldAdding; non-owning identity-indexed Fields; Base-first Forms; each Tag's Gate, declaration-ordered Gainings, Imprints and FieldAdding, then Posts once after the completed Form; unfinished training retains actual Gains without admission, earlier completed Tags stay, retry starts fresh; Rip sticky for contributions and for conditions (the author ends a condition: a guard, or `Contract.Delete` from the `@Rip` protocol), refused while required, never cascading |
| **1 · Contributions** | two scopes, one slot per `(scope, name)`; latest-Layer Overlay with captured Underlays and stored-value Records; Tag members invisible on the Agent; `@Secret` and `Public` publication with a composition door, published members answering members only, and only sound ones (Rogue Access Failure for a Rogue Agent, the named promise for a defective one); Delete; three access forms; Pins: Tags as Targets, the receiver rule, patching Tag-scope declarations with collision control, publication onto the Field, Fields never mixed; Tools: a Record slot with a declared kind, a specific Tag (a member now) or a Python class (an instance) or both, checked at the gaining and at every write, never empty unless declared, never Tagging what it holds, its rule ending as any Record's declaration does; Links: a `@Link` Relation granting each Agent a Tag of its own, read-only in a closed slot, two seats (the Agent, then the Contact), linking as a tagging of the Contact with the Pair as receiver, one Pair per Contact across a Link's Form, extension of a held Link over every Pair, `@Public` lines onto the Contact and `@Secret` in-house, the doors of the Agent and the Pair never the Contact's, nothing naming the Link's Agent, every act on a Relation refused |
| **2 · Contracts** | strict boolean conditions; each Tag gates when its turn arrives and active Tags are not re-asked; condition definitions acquired in declaration order and retained after unfinished training, including Constant Posts; Imprints before FieldAdding; Postconditions once after the completed Form and re-checked later; Post failure preserves membership and current Posts determine soundness; Forward-Post, Backward-Pre with weakening diagnosed; defective Agents, reserved Agent truth including a Tag's own Pin Posts, no Posts meaning true even with an empty Field, conflicting host/Contribution truth refused and host `len` intact, sound and defective partitions with an absorbing `~` (`~~Tag` is `~Tag`), populations combined with `|`, `&`, `-` at every level; a condition read on the Agent by its name as a plain bool, its name refused to other kinds; a failure names its check (`except Precondition.X`); `@Pre` and `@Post` stacked as one condition, in either order |
| **3 · Lifecycle** | `@Rip` protocols after membership ends; the three deletion tiers (finalizer, `At_Exit`, and the program's own Rip in a `finally`); the Agent's `__del__` as Layers of its Overlay, after the teardowns, alone at interpreter exit; an Agent's deletion and `At_Exit` ending its Links after its own teardowns, a Contact's deletion unlinking her, each Pair's teardowns at most once |

Surface spellings may differ between languages. The **semantic laws** may
not. Every failure in the failure model must stay distinct and named.

## The conformance suite

[`tests/test_topkit/`](tests/test_topkit/) groups the conformance seed by
behavior, with one TestCase class per file and shared hosts and Tags in
`_fixtures.py`. Test classes assert laws; a port in another language
satisfies the behaviours those tests assert, in its
own spelling. Tests that exercise Python-only mechanics (garbage
collection, weak references, warnings) are profile tests, not laws.

Run all of it with `PYTHONPATH=. python3 -m unittest tests.test_topkit`, or
choose a file such as `tests.test_topkit.test_record`. Existing class targets
such as `tests.test_topkit.RecordTests` still work. Normal test discovery
includes the package once; its `__init__.py` delegates to `unittest`.
`PYTHONPATH=. python3 -m tests.test_topkit` remains an equivalent entry point.
Historical STEP references to `tests/test_topkit.py` refer to these same
test classes, now in the package.

## The "TOP Verified" mark

Implementing TOP is free and open. **Claiming conformance under the "TOP
Verified" / "TOP-conformant" designation** is what the steward authorizes,
per implementation and per ring, so the mark continues to mean something.
Request review by opening an issue.
