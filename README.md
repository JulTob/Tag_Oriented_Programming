# Tag-Oriented Programming (TOP)™

> Compose semantic layers on one stable object identity.

> **OOP owns inherent structure; TOP owns semantic context.**

**TOP** is a programming paradigm: a Target keeps its identity while Tags
add meaning — species, roles, backgrounds, capabilities — that cut across
ordinary class hierarchies. Where traditional code asks *"what is this
object?"*, TOP asks *"what does this object mean here?"*, and lets the
answer grow.

```python
charlie = Hero( "Charlie" )
Human( charlie )
Wizard( charlie )

assert charlie in Wizard           # active membership
assert isinstance(
        charlie,
        Human,
        )                          # "ever an instance, always an instance"
charlie.attack()                   # composed behavior
```

The Python profile also exposes a procedural facade for functional and
multi-paradigm code:

```python
from TagKit import Apply
from TagKit import Has
from TagKit import Tags


charlie = Apply(
        Hero( "Charlie" ),
        Human,
        Wizard,
        )

assert Has(
        charlie,
        Human,
        Wizard,
        )
assert Wizard in Tags( charlie )

party = [
        Hero( "Ari" ),
        Hero( "Bea" ),
        ]
party = list(
        map(
                Wizard,
                party,
                )
        )
```

`Tag( target )` remains the smallest identity-preserving transformer.
`Apply( target, *tags )` composes several Tags without claiming method names
from the Target; `Tags( target )` and `Has( target, ... )` are read-only
queries.
Optional object-style conveniences yield to methods and protocols already
defined by the host object. Python actualization still uses a synthesized
runtime subclass, so exact-type-sensitive libraries should review the
[documented profile boundary](TagKit/IMPLEMENTATION_NOTES.md#decisions--edge-cases-judgment-calls).

## Install TagKit

TagKit currently ships as an alpha reference implementation. From a checked
out repository:

```bash
python -m pip install .
```

Use an editable installation while developing TagKit itself:

```bash
python -m pip install --editable .
```

Application code imports only from the stable public package:

```python
from TagKit import Has
from TagKit import Tag
from TagKit import Tags
```

Applications should pin an immutable release or commit. Do not depend on
TagKit's internal modules or on a mutable development branch.

## Read TOP in this order

1. [The TOP Manifesto](spec/MANIFESTO.md) explains the paradigm's intent and
   thought model.
2. [The Technical Specification](spec/SPECIFICATION.md) defines normative,
   observable semantics.
3. [The TagKit Guide](TagKit/GUIDE.md) teaches the Python profile.
4. [The Python Profile](TagKit/PYTHON_PROFILE.md) lists TagKit utilities that
   sit beside the Specification — queries, Fields, Checkpoints, Scope, and
   similar conveniences.
5. Focused guides such as the [Pin Guide](TagKit/PIN_GUIDE.md) explain one
   facility in depth.
6. [Implementation Notes](TagKit/IMPLEMENTATION_NOTES.md) document internal
   engineering decisions.

## This repository

| Path | What | License |
|---|---|---|
| [`spec/MANIFESTO.md`](spec/MANIFESTO.md) | **Manifesto** — TOP's intent, ethos, and mental model. | CC-BY-4.0 |
| [`spec/SPECIFICATION.md`](spec/SPECIFICATION.md) | **Technical Specification** — normative observable semantics. | CC-BY-4.0 |
| [`TagKit/`](TagKit/) | **TagKit** — the Python reference implementation. | Apache-2.0 |
| [`TagKit/GUIDE.md`](TagKit/GUIDE.md) | **TagKit Guide** — the user-facing Python API. | Apache-2.0 |
| [`TagKit/PYTHON_PROFILE.md`](TagKit/PYTHON_PROFILE.md) | **Python Profile** — TagKit utilities beside the Specification. | Apache-2.0 |
| [`TagKit/PIN_GUIDE.md`](TagKit/PIN_GUIDE.md) | **Pin Guide** — organize Tags by Tagging Tags. | Apache-2.0 |
| [`TagKit/IMPLEMENTATION_NOTES.md`](TagKit/IMPLEMENTATION_NOTES.md) | **Implementation Notes** — non-normative TagKit internals. | Apache-2.0 |
| [`CHANGELOG.md`](CHANGELOG.md) | **Changelog** — versioned behavior and migration notes. | Apache-2.0 |
| [`tests/`](tests/) | Seed of the language-agnostic conformance suite. | Apache-2.0 |
| [`tests/STRESS_TESTING.md`](tests/STRESS_TESTING.md) | Reproducible state-machine and capacity stress profiles. | Apache-2.0 |
| [`steps/`](steps/) | **STEP**s — Standard TOP Enhancement Proposals. | CC-BY-4.0 |

The **Manifesto governs intent. The Specification governs conformance.**
Guides teach a language profile; implementations must follow the
Specification. Any gap in TagKit is TagKit's to fix, not a change to TOP.

## Conformance

An implementation in any language is welcome. "TOP-conformant" means it
preserves the observable semantics in the Specification and passes the
conformance suite — see [`CONFORMANCE.md`](CONFORMANCE.md). The
**TOP Verified** mark is granted by the steward, so the standard stays
meaningful.

## Governance & contributing

TOP is led by a **Director**, with a path to shared governance — see [`GOVERNANCE.md`](GOVERNANCE.md). Propose changes through the **STEP** process ([`CONTRIBUTING.md`](CONTRIBUTING.md)); every decision is recorded, in the open, with its reason.

## License & trademark

Code is **Apache-2.0**; the Manifesto, Specification, and STEPs are
**CC-BY-4.0**. "Tag-Oriented Programming", "TOP", and "TagKit" are
trademarks — see [`TRADEMARK.md`](TRADEMARK.md). You may implement the
paradigm freely; the marks identify the official specification and conformant
implementations.

© 2026 Julio Toboso.
