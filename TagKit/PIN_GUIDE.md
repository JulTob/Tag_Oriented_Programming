# 📌 Pin Guide

[Manifesto](../spec/MANIFESTO.md) →
[Technical Specification](../spec/SPECIFICATION.md) →
[TagKit Guide](GUIDE.md) → **Pin Guide**

## Let the cards organize the cards

A Tag can itself be Tagged.

When a Tag is applied to another Tag, this guide calls the mark a **Pin**:

```text
character  -- tagged by -->  Wizard
Wizard     -- pinned by -->  Mage
```

`Wizard` gives meaning to a character.

`Mage` gives an additional meaning to the `Wizard` card: this character
class belongs among the magic-using classes.

Imagine each Tag as a card:

- Bases and Shapes show how the card grows from broader cards;
- a Pin places a small note on that chosen card; and
- `Pin[:]` gathers every card carrying the same note.

A Pin is not a new kind of object. It is an ordinary Tag used with another
Tag as its Target.

The [Manifesto](../spec/MANIFESTO.md) explains TOP's intent. The
[Technical Specification](../spec/SPECIFICATION.md) defines its normative
semantics. The [TagKit Guide](GUIDE.md) teaches the general Python API. This
page focuses on the Tag-on-Tag pattern.

> **A Pin points; it does not own.**
>
> Its Field is weak and non-owning, like every TagKit Field.

---

## 1. The smallest Pin

Ordinary Tagging:

```python
Wizard( character )
```

The character becomes a `Wizard` Agent.

Pinning:

```python
Mage( Wizard )
```

The `Wizard` Tag becomes a `Mage` Agent.

That one relation is already useful:

```python
assert Wizard in Mage
assert Wizard in Mage[:]
```

The Field is the classification. There is no parallel flag or registry to
keep synchronized.

---

## 2. A simple classification

Suppose a project defines these character classes:

```python
from TagKit import Tag


class Character_Class( Tag ):
    pass


class Druid( Character_Class ):
    pass


class Wizard( Character_Class ):
    pass


class Warlock( Character_Class ):
    pass


class Fighter( Character_Class ):
    pass


class Barbarian( Character_Class ):
    pass


class Rogue( Character_Class ):
    pass


class Ranger( Character_Class ):
    pass
```

Now make two Tags that answer useful questions about those cards:

```python
class Mage( Tag ):
    pass


class Martial( Tag ):
    pass
```

Pin the matching classes:

```python
Mage( Druid )
Mage( Wizard )
Mage( Warlock )

Martial( Fighter )
Martial( Barbarian )
Martial( Rogue )

Mage( Ranger )
Martial( Ranger )
```

`Ranger` may carry both Pins:

```python
assert Ranger in Mage
assert Ranger in Martial
```

That overlap is ordinary. The Pins answer two different questions about the
same card.

Their Fields remain immediately useful:

```python
mage_classes = tuple( Mage[:] )
martial_classes = tuple( Martial[:] )
```

`Ranger` appears in both collections without leaving its
`Character_Class` Form.

---

## 3. Grow a card or mark a card?

Use Base/Shape when one meaning grows from another.

Use a Pin when an existing Tag needs an external classification.

| Question | Model |
| --- | --- |
| Is `Wizard` a kind of `Character_Class`? | Base/Shape |
| Should every Wizard Agent also be a `Spellcaster`? | Base/Shape |
| Should the `Wizard` card appear in the `Mage` Field? | Pin |
| Should `Ranger` appear in both `Mage` and `Martial`? | Two Pins |
| Should every future Shape inherit the relation? | Base/Shape |
| Should only this chosen card carry the mark? | Pin |

A Pin sticks to the card you pinned.

It does not automatically appear:

- on future Shapes of that card; or
- on ordinary Agents later tagged by that card.

```python
Mage( Wizard )
Wizard( charlie )

assert Wizard in Mage
assert charlie not in Mage
```

If every Wizard Agent should also be a Mage, then `Mage` belongs in the
Wizard's Form as a Base, or the Agent should receive both Tags.

---

## 4. Pin vocabulary

- **Pin** — an ordinary Tag applied to another Tag.
- **Pinned Tag** — the Target Tag receiving the Pin.
- **Pinning** — the call `Pin( Target_Tag )`.
- **Pin Field** — the current Pinned Tags, opened with `Pin[:]`.

The words describe the relation, not new Python machinery.

The same class may be an ordinary Tag in one expression and a Pin in another.
What matters is the Target of this particular Tagging.

---

## 5. Contributions follow the Target

Ask one question:

> What is the Target of this Tagging?

If the Target is a character:

- an Action is behavior on that character; and
- a Record is state on that character.

If the Target is itself a Tag:

- the Action naturally becomes an Operation on that Tag; and
- the Record naturally becomes a Report on that Tag.

| Declared on the Pin | Meaning on the Pinned Tag |
| --- | --- |
| Action | Operation |
| Record | Report |
| Precondition | Guard before Pinning |
| Imprint | Work during Pinning |
| Postcondition | Promise checked before commit |
| Operation | Shared behavior of the Pin Field |
| Report | Shared information of the Pin Field |

The contribution keeps its purpose. Its scope follows the Target.

---

## 6. Pin Records become Reports

A classifier can provide structured information to every Pinned Tag:

```python
from TagKit import Record


class Available( Tag ):

    @Record
    def ability_choices(
            background,
            abilities,
            ) -> tuple[str, ...]:
        return tuple( abilities )


class Merchant( Tag ):
    pass


Available(
        Merchant,
        abilities=(
                "Charisma",
                "Dexterity",
                ),
        )
```

`ability_choices` is now shared information on the `Merchant` card:

```python
assert Merchant.ability_choices == (
        "Charisma",
        "Dexterity",
        )
```

There is no external `BACKGROUND_ABILITY_CHOICES` lookup. The relation and
its Report travel together through one Pinning.

Prefer immutable values for Pin-provided Reports unless shared mutation is a
deliberate part of the model.

---

## 7. Pin Actions become Operations

A Pin may also teach each Pinned Tag a shared behavior:

```python
from TagKit import Action


class Available( Tag ):

    @Action
    def describe_availability(
            background,
            ) -> str:
        return f"{str( background )} is available."
```

```python
Available( Merchant )

assert (
        Merchant.describe_availability()
        == "Merchant is available."
        )
```

The function was written as an Action because `Available` describes its
Agents. When one of those Agents is the `Merchant` Tag, that behavior sits
naturally at Tag scope as an Operation.

---

## 8. Resources of the Pin itself

A Pin may have its own Report and Operation. Those remain resources of the
Pin Field rather than contributions copied onto each Pinned Tag:

```python
from TagKit import Operation


class Available( Tag ):
    purpose = "Selectable backgrounds"

    @Operation
    def count(
            pin,
            ) -> int:
        return len( pin[:] )
```

`purpose` is a Report because it is public data declared on the `Available`
Tag. TagKit does not invent Reports that the program did not declare.

Open one Pinned Tag through the Pin to reach the captured Pin resources:

```python
Available( Merchant )

assert Available[ Merchant ].purpose == "Selectable backgrounds"
assert Available[ Merchant ].count() == 1
```

The distinction is simple:

- `Merchant.ability_choices` came from a Pin Record and belongs on the
  `Merchant` card; while
- `Available[ Merchant ].purpose` is information about the `Available`
  Field.

---

## 9. Reading Pin Fields and cards

The ordinary TagKit access forms keep their meanings:

```python
Available( Merchant )
```

Apply the Pin.

```python
Merchant in Available
```

Check current Pin membership.

```python
Available[:]
```

Open the whole Pin Field.

```python
Available[ Merchant ]
```

Open the `Merchant` card through its active `Available` Pin.

```python
Available.Rip( Merchant )
```

End active Pin membership.

Pinning preserves the Pinned Tag's:

- object identity;
- Form and place in the Geometry;
- ability to Tag ordinary Targets; and
- other active Pins.

After a Pinning has committed, `isinstance( Merchant, Available )` records
that history even if active membership is later Ripped.

---

## 10. Composition between Pins

Pins are Tags, so ordinary composition rules apply:

- Pin Bases apply before Pin Shapes;
- reapplying an active Pin is a strict no-op;
- later same-name contributions become visible;
- `@Underlay` extends the compatible contribution beneath it;
- `@Delete` masks a named contribution; and
- failed Pinning does not enter the Pin Field.

For example, two Pins may build one Report in layers:

```python
from TagKit import Underlay


class Categorized( Tag ):

    @Record
    def labels(
            target_tag,
            ) -> tuple[str, ...]:
        return ( "categorized", )


class Playable( Categorized ):

    @Record
    @Underlay
    def labels(
            target_tag,
            prior,
            ) -> tuple[str, ...]:
        return prior() + ( "playable", )
```

```python
Playable( Wizard )

assert Wizard.labels == (
        "categorized",
        "playable",
        )
```

Use Pin Bases when the classification itself has a true general-to-specific
Form. Use independent Pins when the questions are independent.

---

## 11. Conditions and Imprints on a Pin

Conditions can validate whether a Tag is eligible for a Pin:

```python
from TagKit import Pre


class Documented( Tag ):

    @Pre
    def has_description(
            target_tag,
            ) -> bool:
        return bool( target_tag.__doc__ )
```

An Imprint may perform application-time work on the Pinned Tag. Use it
sparingly. Most classification needs only membership and Reports.

Keep external I/O outside provisional Pinning whenever possible. If a
Precondition, Imprint, Record, or Postcondition fails, the Pin must not enter
the Field, but Python cannot reverse a message already sent or a file already
written.

---

## 12. Rip and history

Ripping a Pin ends the active relation:

```python
Available.Rip( Merchant )

assert Merchant not in Available
assert Merchant not in Available[:]
```

It also ends access through `Available[ Merchant ]`.

Committed history remains:

```python
assert isinstance(
        Merchant,
        Available,
        )
```

As in ordinary TOP, contributions made as Actions and Records are sticky
unless an explicit Rip protocol changes them. Native Reports and Operations
of the Pin are Field resources and disappear from that Pin-bound view when
membership ends.

Rip is exceptional. Do not use it as an everyday substitute for a mutable
Record or a better classification.

---

## 13. Useful Pin patterns

A Pin should answer a question that code can say aloud:

> Is this class a `Mage`?

> Is this background `Available`?

> Is this rule `Official`?

> Is this feature `NPC_Ready`?

Common patterns include:

- discoverable groups without side registries;
- availability filters;
- official, optional, or homebrew source marks;
- feature families;
- serialization or presentation categories;
- plugin capabilities; and
- ruleset compatibility.

A good Pin remains useful even when it contributes no Actions, Records,
Operations, or Reports. Membership and the Field are already a complete
semantic relation.

---

## 14. Designing a clear Pin

Before making a Pin, ask:

1. What note am I putting on the card?
2. Which exact Tags should carry it?
3. Should future Shapes inherit it?
4. Does the Field answer a useful question?
5. Should information live as a Report on each Pinned Tag?
6. Should behavior live as an Operation on each Pinned Tag?

If future Shapes must inherit the relation, use a Base.

If only one Tag needs one value, a native Report may be enough.

Keep Pins easy to read:

- choose a name that answers its question;
- let the Field be the registry;
- prefer immutable Reports;
- give every contribution one purpose;
- keep outside effects away from Pinning; and
- use the public `Tag` API.

The whole model fits in three lines:

```python
Available( Merchant )

assert Merchant in Available
assert Merchant in Available[:]
```

Pin a note to the card. Open the Field when you need the marked cards.
