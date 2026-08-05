# 🏷️ The TOP Manifesto 🔖

> **OOP owns inherent structure; TOP owns semantic context.**

Tag-Oriented Programming provides utility without changing identity.

By semantic increments, it gives an existing Target new meanings without
replacing its essence. A hero may become Human, Wizard, Sage, Merchant, or
Champion while remaining the same hero.

TOP is a programming paradigm for composing semantic layers on one stable
object identity.

---

## One identity, many meanings

Traditional programming often asks:

> What is this object?

TOP asks:

> What does this object mean here?

The first question remains important. It belongs to the Target and its
inherent structure. The second may change with the world around that Target:
its role, species, affiliation, capability, permission, background, or use.

TOP lets those meanings grow without forcing every combination into one class
tree.

```python
charlie = Character( "Charlie" )

Human( charlie )
Wizard( charlie )

assert charlie in Human
assert charlie in Wizard
```

There is still one Charlie.

---

## Structure and context

OOP and TOP are complementary views.

| OOP | TOP |
| --- | --- |
| Inherent structure | Semantic context |
| Internal parts | External layers |
| Identity and invariants | Meaning and use |
| Ordinary attributes | Records contributed by context |
| Ordinary methods | Actions contributed by context |
| Class inheritance | Tag Geometry and Overlays |

TOP does not ask an object to stop being an object. It gives the object a
clear way to participate in meanings that do not belong inside its permanent
structure.

---

## Tags are meaning, not mutable values

A Tag answers:

> Which semantic context applies to this Target?

A Record answers:

> What value does this Agent currently hold?

An Action answers:

> What can this Agent do in this context?

Therefore:

- `Clearance` is a Tag;
- a current authorization status is a Record;
- an authorized operation is an Action;
- changing HP, charges, cooldowns, or frame statistics changes Records, not
  Tags; and
- ordinary procedural code may process those Records as efficiently as the
  application requires.

Tags may be applied and Ripped because context can begin and end. They should
not become disguised scalar variables.

---

## An empty Tag is complete

Membership is the primary contribution of a Tag.

An empty Tag still defines a semantic category and its Field of Agents:

```python
class Wizard( Tag ):
    pass
```

Actions, Records, Conditions, Reports, Operations, and Imprints may enrich
that meaning. None of them is required to justify it.

A Tag primitive should not invent application data. Language profiles should
use their language's native name and documentation facilities. `COLOR`,
`SOURCE`, `ABSTRACT`, or any other Report exists only when the program gives
that information to the Tag.

---

## Composition should remain visible

TOP favors small semantic contributions that compose:

- Bases provide general meaning;
- Shapes form more specific meaning;
- independent Tags cross ordinary hierarchies;
- Underlays preserve and extend compatible contributions;
- Overlays show the meaning currently visible; and
- Fields reveal the current population of a Tag.

The relationships should be readable from the program. TOP is not hidden
global mutation and does not require a framework to reinterpret ordinary
code.

---

## Multiparadigm by design

TOP does not claim every responsibility.

Use object-oriented design for inherent structure and invariants. Use
procedural or functional code for transformations, loops, and pipelines. Use
contracts for obligations. Use TOP where semantic context must compose across
those boundaries.

The paradigms cooperate because each owns a different question.

---

## Commitments

TOP is guided by these commitments:

1. A Target keeps one stable identity.
2. Tags add semantic context rather than replacing inherent structure.
3. Membership is meaningful even when a Tag contributes nothing else.
4. Mutable Agent state belongs in Records.
5. Shared Tag data belongs in Reports.
6. Composition is explicit, ordered, and inspectable.
7. Application failure must not publish a partial Tagging.
8. Rip ends active membership without pretending history never happened.
9. Language profiles should feel native to their host language.
10. Implementations serve the paradigm; the paradigm does not serve one
    application.

---

## How to read TOP

This Manifesto governs the intent and thought model of TOP.

The [Technical Specification](SPECIFICATION.md) defines its normative,
observable semantics. Focused guides teach concrete language profiles and
facilities. Implementations document their own engineering decisions
separately.

The layers of documentation follow TOP itself: general meaning first, then
technical structure, then specific use.
