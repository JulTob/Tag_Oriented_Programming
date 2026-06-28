# Tag-Oriented Programming (TOP)™

> Compose semantic layers on one stable object identity.

**TOP** is a programming paradigm: a Target keeps its identity while Tags add meaning — species, roles, backgrounds, capabilities — that cut across ordinary class hierarchies. Where traditional code asks *"what is this object?"*, TOP asks *"what is this object for?"*, and lets the answer grow.

```python
charlie = Hero("Charlie")
Human(charlie)
Wizard(charlie)

assert charlie in Wizard           # active membership
assert isinstance(charlie, Human)  # "ever an instance, always an instance"
charlie.Attack()                   # composed behaviour
```

## This repository

| Path | What | License |
|---|---|---|
| [`spec/SPECIFICATION.md`](spec/SPECIFICATION.md) | **The Guide** — the authoritative paradigm. The source of truth. | CC-BY-4.0 |
| [`TagKit/`](TagKit/) | **TagKit** — the Python reference implementation. | Apache-2.0 |
| [`tests/`](tests/) | Seed of the language-agnostic conformance suite. | Apache-2.0 |
| [`steps/`](steps/) | **STEP**s — Standard TOP Enhancement Proposals. | CC-BY-4.0 |

The **Specification is the source of truth.** TagKit demonstrates it and must perform as the Guide describes; any gap in TagKit is TagKit's to fix, not a change to TOP.

## Conformance

An implementation in any language is welcome. "TOP-conformant" means it preserves the observable semantics in the Guide and passes the conformance suite — see [`CONFORMANCE.md`](CONFORMANCE.md). The **TOP Verified** mark is granted by the steward, so the standard stays meaningful.

## Governance & contributing

TOP is led by a **Director**, with a path to shared governance — see [`GOVERNANCE.md`](GOVERNANCE.md). Propose changes through the **STEP** process ([`CONTRIBUTING.md`](CONTRIBUTING.md)); every decision is recorded, in the open, with its reason.

## License & trademark

Code is **Apache-2.0**; the Specification and STEPs are **CC-BY-4.0**. "Tag-Oriented Programming", "TOP", and "TagKit" are trademarks — see [`TRADEMARK.md`](TRADEMARK.md). You may implement the paradigm freely; the marks identify the official spec and conformant implementations.

© 2026 Julio Toboso.
