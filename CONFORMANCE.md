# Conformance

An implementation of TOP, in **any** language, is *conformant* when it
preserves the observable semantics of [`spec/SPECIFICATION.md`](spec/SPECIFICATION.md)
for every ring it claims, and passes the conformance suite for those rings.

## Rings

The Specification is written in rings. Conformance is claimed per ring,
from the inside out: a Ring 2 implementation also satisfies Rings 0 and 1.

| Ring | Laws, in short |
| --- | --- |
| **0 · Kernel** | stable identity and preserved host behaviour; Base-first Tagging with independent Field memberships and a has-been check established at FieldAdding; `agent in Tag` asks sound membership, `agent in Tag[:]` raw Field membership; non-owning identity-indexed Fields; Base-first Forms; each new Tag requires a valid source and preflights all Record spaces before Gains; declaration-ordered Gainings and Imprints precede FieldAdding, then current Posts judge that Tag before the next turn; ordinary Record initializer and Imprint failures warn individually and continue through admission, a failed Record retains its prior binding or absence, earlier completed Tags stay, and an active Tag call remains a no-op; structural failure that prevents admission discards provisional Posts; Rip ends one Field membership without cascade, leaves Actions and Records, ends that application's ordinary Posts before teardown, and preserves its admitted Constant Posts as lifetime Contract terms |
| **1 · Contributions** | two scopes, one slot per `(scope, name)`; latest-Layer Overlay with captured Underlays and stored-value Records; Tag members invisible on the Agent; `@Secret` and `Public` publication with a composition door, published members answering members only, and only sound ones (Rogue Access Failure for a Rogue Agent, the named promise for a defective one); Delete; three access forms; Pins: Tags as Targets, the receiver rule, patching Tag-scope declarations with collision control, publication onto the Field, Fields never mixed; Tools: a Record slot with a declared kind, a specific Tag (a Field member now) or a Python class (an instance) or both, checked when a value is successfully gained and at every write, allowing `None` only when declared, an initializer failure retaining the prior binding or absence and warning, never Tagging what it holds, its rule ending as any Record's declaration does |
| **2 · Contracts** | strict boolean conditions; each Tag gates when its turn arrives and active Tags are not re-asked; a Precondition is a transient Tagging Service that never becomes Agent state; Post definitions are prepared in declaration order and join the Contract bond only at Field admission; an ordinary Post is an Agent Gain bound to that admitted application, while an admitted Constant Post is a lifetime Contract term; best-effort Record initialization and Imprints before FieldAdding, with one named training warning per failed step; Python interruptions stop later training, attempt admission and Post inspection, and propagate unchanged; every current Post checked after each Tag's admission and re-checked later, one failed Post keeping its named error and several using `TaggingFailure`; Post failure preserves membership; explicit TOP acts refused in Pre/Post checks and Record calculations, direct Python writes remaining the author's responsibility; recursive Post edges neutral `True` without skipping other Posts, with query-local verdict reuse and protected-state invalidation; Forward-Post, Backward-Pre with weakening diagnosed; defective Agents, reserved Agent truth including a Tag's own Pin Posts, no Posts meaning true even with an empty Field, conflicting host/Contribution truth refused and host `len` intact, sound and free defective populations, arrested Agents in neither but retained in raw Fields and Safehouses, with an absorbing `~` (`~~Tag` is `~Tag`), populations combined with `|`, `&`, `-` at every level; a visible Post read on the Agent by its name as a plain bool, its name refused to other kinds; a failure names its check (`except Precondition.X`); `@Pre` and `@Post` stacked as two roles from one body, in either order |
| **3 · Lifecycle** | `@Rip` protocols after membership and that application's ordinary Posts end; explicit protocols run sequentially and stop at failure, saved work retries from the failed protocol, ordinary acts retry cleanup before access, and whole-Field Rip revokes all initial members before callbacks; guarded lazy TOP continuations and already-entered context exit cleanup follow the Python profile; the three deletion tiers (finalizer, `At_Exit`, and the program's own Rip in a `finally`); the Agent's `__del__` as Layers of its Overlay, after the teardowns, alone at interpreter exit |

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
