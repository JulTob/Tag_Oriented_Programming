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
from TopKit import Tag, Record, Action, Underlay, Pre

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

Read [`TopKit/GUIDE.md`](https://github.com/JulTob/Tag_Oriented_Programming/blob/main/TopKit/GUIDE.md) for the patterns, and run
`examples/dnd_character.py` and `examples/biome.py` for the long form;
`examples/fleet_patching.py` and `examples/crew_access.py` for the design
patterns Pins and published members give you.

## Installing

```
pip install topkit
```

TopKit is in alpha. While no final release exists, a plain
`pip install topkit` installs the newest alpha. Once a final release is
out, it installs that, and `pip install --pre topkit` asks for the newest
alpha.

## This repository

| Path | What | License |
| --- | --- | --- |
| [`spec/SPECIFICATION.md`](https://github.com/JulTob/Tag_Oriented_Programming/blob/main/spec/SPECIFICATION.md) | **The Specification**, written in rings from the kernel outward. The source of truth. | CC-BY-4.0 |
| [`TopKit/GUIDE.md`](https://github.com/JulTob/Tag_Oriented_Programming/blob/main/TopKit/GUIDE.md) | **The Guide**: TOP for people, pattern by pattern. Start here. | Apache-2.0 |
| [`TopKit/`](https://github.com/JulTob/Tag_Oriented_Programming/tree/main/TopKit) | **TopKit**, the Python reference implementation (the T is the Tag in T.O.P.). | Apache-2.0 |
| [`TopKit/CONTRACTS.md`](https://github.com/JulTob/Tag_Oriented_Programming/blob/main/TopKit/CONTRACTS.md) | **The Contracts Guide**: gates, promises, membership and error control, aboard a starship. | Apache-2.0 |
| [`TopKit/FIELDS.md`](https://github.com/JulTob/Tag_Oriented_Programming/blob/main/TopKit/FIELDS.md) | **The Fields Guide**: populations, partitions and the algebra between them. | Apache-2.0 |
| [`tests/`](https://github.com/JulTob/Tag_Oriented_Programming/tree/main/tests) | The conformance suite, the examples and every document block, the oracle (an independent model of the paradigm checked against the kit on a random walk), and the differential fuzzer (the same random programs on two versions of the kit, transcripts compared). | Apache-2.0 |
| [`examples/`](https://github.com/JulTob/Tag_Oriented_Programming/tree/main/examples) | A D&D character sheet, a mix-and-match biome, a drone fleet patched through Pins, a starship crew under published members. Each is a set of design patterns. | Apache-2.0 |
| [`benchmarks/`](https://github.com/JulTob/Tag_Oriented_Programming/tree/main/benchmarks) | The runtime budget: reads, calls, tagging, memory. | Apache-2.0 |
| [`steps/`](https://github.com/JulTob/Tag_Oriented_Programming/tree/main/steps) | **STEP**s, Standard TOP Enhancement Proposals. | CC-BY-4.0 |
| [`RELEASING.md`](https://github.com/JulTob/Tag_Oriented_Programming/blob/main/RELEASING.md) | How TopKit reaches PyPI, and what to check first. | Apache-2.0 |

The **Specification is the source of truth.** TopKit demonstrates it and
must perform as the Specification describes; any gap in TopKit is TopKit's
to fix, not a change to TOP.

## Using TopKit from a checkout

From a checkout of this repository:

```
pip install .                         # or: PYTHONPATH=. python3 ...
PYTHONPATH=. python3 -m unittest discover -s tests -t .
PYTHONPATH=. python3 benchmarks/bench.py
```

Python 3.12 or later, no dependencies. TopKit is built so that an Agent's
attribute reads and Action calls cost what they cost on a plain object;
tagging is the slower, rarer act.

## Conformance

An implementation in any language is welcome. "TOP-conformant" means it
preserves the observable semantics in the Specification, ring by ring, and
passes the conformance suite. See [`CONFORMANCE.md`](https://github.com/JulTob/Tag_Oriented_Programming/blob/main/CONFORMANCE.md). The
**TOP Verified** mark is granted by the steward, so the standard stays
meaningful.

## Governance & contributing

TOP is led by a **Director**, with a path to shared governance; see
[`GOVERNANCE.md`](https://github.com/JulTob/Tag_Oriented_Programming/blob/main/GOVERNANCE.md). Propose changes through the **STEP**
process ([`CONTRIBUTING.md`](https://github.com/JulTob/Tag_Oriented_Programming/blob/main/CONTRIBUTING.md)); every decision is recorded,
in the open, with its reason.

## License & trademark

Code is **Apache-2.0**; the Specification and STEPs are **CC-BY-4.0**.
"Tag-Oriented Programming", "TOP", and "TopKit" are trademarks; see
[`TRADEMARK.md`](https://github.com/JulTob/Tag_Oriented_Programming/blob/main/TRADEMARK.md). You may implement the paradigm freely; the
marks identify the official spec and conformant implementations.

© 2026 Julio Toboso.
