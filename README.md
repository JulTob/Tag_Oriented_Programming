# Tag-Oriented Programming (TOP)™

> Compose semantic layers on one stable object identity.

**TOP** is a programming paradigm: a Target keeps its identity while Tags
add meaning, species, roles, backgrounds, capabilities, that cut across
ordinary class hierarchies. Where traditional code asks *"what is this
object?"*, TOP asks *"what is this object for, here?"*, and lets the answer
grow. The inspiration is tabletop character creation: species, class,
background and feats are independent choices, and the character sheet is
what they compose.

```python
from TagKit import Tag, Record, Action, Underlay, Pre

class Character:
    def __init__(self, name, level):
        self.name, self.level = name, level

class Elf(Tag):
    @Record
    def spells(agent, stored):                 # piles up with other Tags
        return (stored or []) + ["Light"]

class Wizard(Tag):
    @Pre
    def Can_Study(agent):
        return agent.level >= 1

    @Record
    def spells(agent, stored):
        return (stored or []) + ["Magic Missile"]

    def Attack(agent):
        return f"{agent.name} casts {agent.spells[-1]}"

class War_Caster(Tag):
    @Pre
    def Is_A_Caster(agent):                    # synergy: needs Wizard
        return agent in Wizard

    @Action
    @Underlay
    def Attack(agent, underlay):
        return underlay() + " while holding a shield"

ari = Character("Ari", level=3)
Elf(ari); Wizard(ari); War_Caster(ari)

assert ari in Wizard                           # active membership
assert ari.spells == ["Light", "Magic Missile"]
assert ari.Attack() == "Ari casts Magic Missile while holding a shield"
assert ari.Wizard.Attack() == "Ari casts Magic Missile"   # the view after Wizard
```

Run `examples/dnd_character.py` and `examples/biome.py` for the long form.

## This repository

| Path | What | License |
| --- | --- | --- |
| [`spec/SPECIFICATION.md`](spec/SPECIFICATION.md) | **The Specification**, written in rings from the kernel outward. The source of truth. | CC-BY-4.0 |
| [`TagKit/`](TagKit/) | **TagKit**, the Python reference implementation. | Apache-2.0 |
| [`tests/`](tests/) | The conformance suite, organized by ring. | Apache-2.0 |
| [`examples/`](examples/) | A D&D character sheet and a mix-and-match biome. | Apache-2.0 |
| [`benchmarks/`](benchmarks/) | The runtime budget: reads, calls, tagging, memory. | Apache-2.0 |
| [`steps/`](steps/) | **STEP**s, Standard TOP Enhancement Proposals. | CC-BY-4.0 |

The **Specification is the source of truth.** TagKit demonstrates it and
must perform as the Specification describes; any gap in TagKit is TagKit's
to fix, not a change to TOP.

## Using TagKit

```
pip install .                         # or: PYTHONPATH=. python3 ...
PYTHONPATH=. python3 -m unittest tests.test_tagkit
PYTHONPATH=. python3 benchmarks/bench.py
```

Python 3.10 or later, no dependencies. TagKit is built so that an Agent's
attribute reads and Action calls cost what they cost on a plain object;
tagging is the slower, rarer act.

## Conformance

An implementation in any language is welcome. "TOP-conformant" means it
preserves the observable semantics in the Specification, ring by ring, and
passes the conformance suite. See [`CONFORMANCE.md`](CONFORMANCE.md). The
**TOP Verified** mark is granted by the steward, so the standard stays
meaningful.

## Governance & contributing

TOP is led by a **Director**, with a path to shared governance; see
[`GOVERNANCE.md`](GOVERNANCE.md). Propose changes through the **STEP**
process ([`CONTRIBUTING.md`](CONTRIBUTING.md)); every decision is recorded,
in the open, with its reason.

## License & trademark

Code is **Apache-2.0**; the Specification and STEPs are **CC-BY-4.0**.
"Tag-Oriented Programming", "TOP", and "TagKit" are trademarks; see
[`TRADEMARK.md`](TRADEMARK.md). You may implement the paradigm freely; the
marks identify the official spec and conformant implementations.

© 2026 Julio Toboso.
