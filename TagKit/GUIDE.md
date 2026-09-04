# 🎮 TagKit Guide

[Manifesto](../spec/MANIFESTO.md) →
[Technical Specification](../spec/SPECIFICATION.md) →
**TagKit Guide** → [Python Profile](PYTHON_PROFILE.md) → [Pin Guide](PIN_GUIDE.md)

## Build from meaning, with no class jungle.

TagKit is the Python implementation of Tag-Oriented Programming.

It is useful when one game object can accumulate several independent
meanings:

- a monster has a Species;
- it carries one or more elemental Types;
- it evolves through new Forms;
- it learns capabilities;
- it joins an encounter as a Boss, Minion, Merchant, or Companion; and
- each meaning may contribute data and behavior.

Traditional inheritance asks you to predict those combinations:

```text
ElectricFireFlyingArmoredBossMonster
```
or to carry attributes as long as a shopping list.
```text
monster.type = Electric
monster.secondary_type = Fire
monster.flying = True
monster.armored = True
monster.boss = True
monster.swimming = False
monster.biome = "Placeholder"
```
Most of these are not necessarily applicable to all creatures, but a few extraordinary cases impose the design pattern on all the generic blueprints.

TOP keeps one creature and composes the meanings around it:

```python
Fire( monster )
Electric( monster )
Flying( monster )
Boss( monster )
```

The Target remains the same object. Its usable context grows.

> Note:
> The [Manifesto](../spec/MANIFESTO.md) explains TOP's intent. The
> [Technical Specification](../spec/SPECIFICATION.md) defines the normative
> semantics. This guide teaches the TagKit Python API through examples aimed
> at game and generator developers. TOP can also support databases,
> simulations, processing systems, and control systems.

---

# Quick start

## Your first Elemental Monster

Begin with the smallest object your game actually owns. What data does it hold for all cases? The minimal expression, kernel of your system.

We will call this essential element a Creature in our example. But first, we must import the tools we will use: TagKit. Our library for Tag Oriented Programming.
```python
from dataclasses import dataclass

# We recommend using a namespace for actual production code.
## The standard import for TagKit is "tag"
import TagKit as tag

# We will be using some features directly
from TagKit import Action
from TagKit import Imprint
from TagKit import Tag


@dataclass
class Creature:
    name: str
```

The host class carries inherent identity. Everything else can arrive through
Tags.

```python
class Fire( Tag ):

    @Imprint
    def set_fire_records(
            target,
            max_hp,
            fire_resistance,
            ) -> None:
        target.max_hp = max_hp
        target.hp = max_hp
        target.resistances = {
                "fire": fire_resistance,
                }

    @Action
    def fire_attack(
            target,
            ) -> dict[str, int]:
        return {
                "fire": 6,
                }
```

Apply the Tag:

```python
ember = Creature( "Embercub" )
identity_before = id( ember )

Fire(
        ember,
        max_hp=30,
        fire_resistance=0.5,
        )
```

The same creature now belongs to the `Fire` Field, but the identity of the creature is unchanged:

```python
assert ember in Fire
assert ember in Fire[:]
assert id( ember ) == identity_before
```

The Imprint established ordinary object data gained from Tags:

```python
assert ember.max_hp == 30
assert ember.hp == 30
assert ember.resistances == {
        "fire": 0.5,
        }
```

Those values are Records. They are normal mutable attributes gained from Tag Imprints:

```python
ember.hp -= 8
ember.resistances[ "fire" ] = 0.75

print(ember.hp) #--> 22
print(ember.resistances[ "fire" ]) #--> 0.75
# Both records changed here.
# Generally speaking Records keep data that changes, but they also can store constant values.
```

The Action is normal behavior:

```python
assert ember.fire_attack() == {
        "fire": 6,
        }
```

That is the smallest complete TagKit loop:

| TOP idea | Game example |
| --- | --- |
| Target | `ember` before or during Tagging |
| Tag | `Fire` |
| Tagging | `Fire( ember, ... )` |
| Agent | `ember` as a Fire creature |
| Field | `Fire[:]` sound · `~Fire[:]` defective · `Fire[:] \| ~Fire[:]` U-set |
| Record | `ember.hp`, `ember.resistances` |
| Action | `ember.fire_attack()` |

---

# Part I — A scalable elemental system

We are going to explore a scalable system: a game with elemental monsters. These will show how easy it can be to design oriented on syntax and use instead of oriented towards identities.

## The stable host

For a clean TOP architecture, you should keep the creature model focused on the core identity your application always needs.

Here we will use a dataclass (an object that stores data consistently), but we could have used a dictionary, a standard object, or any target.

```python
from dataclasses import dataclass


@dataclass
class Creature:
    name: str
    level: int = 1
```

The host does not need to know every future type, move, evolution, biome, or
content pack.

---

## General combat and elemental Bases

First, we will make our Elemntal Tags. We will start by making a Base tag for every element. We will then shape each element (water, fire, electric...) into specific expressions of this Base Element.
- We stablish that Elemental Creatures will have resistances. We don't need to worry about them now, but we stablish they will exist as a dictionary or set.

We also will add tags that express the functionalities of the game. For example, some game items may be Combatants, and they require basic combat actions and combat records they will use for this purpose specifically.

```python
from TagKit import Action
from TagKit import Imprint
from TagKit import Operation
from TagKit import Tag
from TagKit import Underlay


class Element( Tag ):

    @Imprint
    def set_element_records(
            target,
            ) -> None:
        target.resistances = {}


class Combatant( Tag ):

    @Imprint
    def set_combat_records(
            target,
            max_hp,
            ) -> None:
        target.max_hp = max_hp
        target.hp = max_hp
        target.statuses = set()

    @Action
    def take_damage(
            target,
            amount: int,
            ) -> int:
        target.hp = max(
                0,
                target.hp - amount,
                )

        return target.hp

    @Action
    def attack(
            target,
            enemy: Creature,
            ) -> dict[str, int]:
        return {
                "physical": 5,
                }
```

`Element` owns elemental Records.

`Combatant` owns combat Records and the basic attack.

They are independent Bases. A creature can be a Combatant without an
element, and another system could reuse `Element` without the combat model.

---

## Fire
We'll start building our Elemental shapes: we creat the Fire Tag. As being a FIre creature will affect the combat stats of the creature, we base the Fire tag on Combatant too.

```python
class Fire(
        Element,
        Combatant,
        ):
    """Fire elemental creature with combat skills."""

        #-- Note: Fire Tag will apply the Element Tag and the Combatant Tag before applying itself.

    color = "#ef5b35"

    @Imprint
    def set_fire_records(
            target,
            fire_resistance,
            ) -> None:
        target.resistances[ "fire" ] = fire_resistance

    @Action
    @Underlay
    def attack(
            target,
            prior,
            enemy: Creature,
            ) -> dict[str, int]:
        damage = prior( enemy )

        return {
                **damage,
                "fire": damage.get(
                        "fire",
                        0,
                        )
                + 4,
                }

    @Action
    def fire_burst(
            target,
            enemy: Creature,
            ) -> dict[str, int]:
        return {
                "fire": 8,
                }

    @Operation
    def roster(
            tag,
            ) -> tuple[str, ...]:
        return tuple(
                creature.name
                for creature in tag[:]
                )
```

Python already gives the Tag its name and documentation:

```python
assert str( Fire ) == "Fire"
assert Fire.__name__ == "Fire"
assert Fire.__doc__ == "Fire elemental creature with combat skills."
assert repr( Fire ) == (
        "Fire\n"
        "Fire elemental creature with combat skills."
        )
```

`color` is a Report because it is public data declared on the `Fire` Tag:

```python
assert Fire.color == "#ef5b35"
```

TagKit does not prebuild name or description Reports. The explicit
`Report( value )` wrapper remains available for compatibility and for unusual
values, such as a callable that must be treated as data rather than an
Action.

`Fire` is a Shape over two Bases:

```python
assert Fire.Form() == (
        Element,
        Combatant,
        Fire,
        )
```

Applying it forms the missing Bases first:

```python
ember = Creature(
        name="Embercub",
        level=12,
        )

Fire(
        ember,
        max_hp=30,
        fire_resistance=0.5,
        )
```

```python
assert ember in Element
assert ember in Combatant
assert ember in Fire

assert ember.hp == 30
assert ember.resistances[ "fire" ] == 0.5
```

The Fire attack extends the Combatant attack:

```python
training_dummy = Creature( "Training Dummy" )

assert ember.attack( training_dummy ) == {
        "physical": 5,
        "fire": 4,
        }
```

The unique Fire Action also exists:

```python
assert ember.fire_burst( training_dummy ) == {
        "fire": 8,
        }
```

---

## Dual typing

Add another type without editing `Creature`, `Combatant`, or `Fire`:

```python
class Electric(
        Element,
        Combatant,
        ):
    """Electric-aligned combatant."""

    color = "#f5cf3d"

    @Imprint
    def set_electric_records(
            target,
            electric_resistance,
            ) -> None:
        target.resistances[ "electric" ] = electric_resistance

    @Action
    @Underlay
    def attack(
            target,
            prior,
            enemy: Creature,
            ) -> dict[str, int]:
        damage = prior( enemy )

        return {
                **damage,
                "electric": damage.get(
                        "electric",
                        0,
                        )
                + 3,
                }

    @Action
    def shock(
            target,
            enemy: Creature,
            ) -> dict[str, int]:
        return {
                "electric": 7,
                }
```

```python
Electric(
        ember,
        electric_resistance=0.75,
        )
```

There is still one Embercub:

```python
assert ember in Fire
assert ember in Electric
assert ember in Element

assert ember.resistances == {
        "fire": 0.5,
        "electric": 0.75,
        }
```

The later Type extends the attack that was already visible:

```python
assert ember.attack( training_dummy ) == {
        "physical": 5,
        "fire": 4,
        "electric": 3,
        }
```

No combined `FireElectricCreature` class was required.

---

## Add Water independently

```python
class Water(
        Element,
        Combatant,
        ):
    """Water-aligned combatant."""

    color = "#3698db"

    @Imprint
    def set_water_records(
            target,
            water_resistance,
            ) -> None:
        target.resistances[ "water" ] = water_resistance

    @Action
    @Underlay
    def attack(
            target,
            prior,
            enemy: Creature,
            ) -> dict[str, int]:
        damage = prior( enemy )

        return {
                **damage,
                "water": damage.get(
                        "water",
                        0,
                        )
                + 4,
                }

    @Action
    def water_jet(
            target,
            enemy: Creature,
            ) -> dict[str, int]:
        return {
                "water": 8,
                }
```

```python
rivlet = Creature(
        name="Rivlet",
        level=7,
        )

Water(
        rivlet,
        max_hp=36,
        water_resistance=0.6,
        )
```

The Fields are already useful registries:

```python
assert tuple( Fire[:] ) == ( ember, )
assert tuple( Electric[:] ) == ( ember, )
assert tuple( Water[:] ) == ( rivlet, )
```

Nothing prevents a later Water/Electric creature. That combination is data
chosen at runtime, not a class you must create in advance.

---

# Part II — Records are ordinary game state

## Imprints establish Records

A Record is data carried by one Agent:

```python
class Armored( Tag ):

    @Imprint
    def set_armor_records(
            target,
            armor,
            ) -> None:
        target.armor = armor

    @Action
    def absorb_damage(
            target,
            amount: int,
            ) -> int:
        absorbed = min(
                target.armor,
                amount,
                )

        target.armor -= absorbed

        return amount - absorbed
```

```python
Armored(
        ember,
        armor=10,
        )

assert ember.armor == 10

remaining = ember.absorb_damage( 6 )

assert remaining == 0
assert ember.armor == 4
```

`armor` is not a property that recalculates itself. It is a normal mutable
attribute established during Tagging.

The same is true for:

- HP;
- resistances;
- movement speed;
- spell slots;
- status collections;
- inventory;
- remaining uses; and
- generated names or titles.

---

## Imprints may apply later Tags

A Base is required and more general. It always applies *before* the Shape.

That is the wrong tool for an optional or later layer. `class MyTag(PreTag,
AdditionalTag1)` makes `AdditionalTag1` required and puts it *under* `MyTag`.

Apply the later Tag from the Imprint instead. The written construction stays
PreTag, then MyTag, then AdditionalTag1. MyTag has already applied before
that Imprint runs. If AdditionalTag1's Precondition fails, only
AdditionalTag1 rolls back:

```python
class MyTag(
        PreTag,
        ):

    @Imprint
    def maybe_extra(
            target,
            extra=None,
            ) -> None:
        if extra:
            AdditionalTag1(
                    target
                    )
```

```python
MyTag(
        ember,
        extra=True,
        )

assert ember in PreTag
assert ember in MyTag
assert ember in AdditionalTag1
```

Preconditions, Record materializers, and Postconditions still cannot apply
Tags. Rip is forbidden while an Imprint is running.

---

## Named Record materializers

An Imprint is convenient when one coherent setup step establishes several
related values. TagKit also offers `@Record` when each value deserves its own
named declaration:

```python
from TagKit import Record


class Battle_Ready( Tag ):

    @Imprint
    def begin_combat_log(
            target,
            hp,
            ) -> None:
        target.combat_log = [
                f"Entered battle with {hp} HP.",
                ]

    @Record
    def max_hp(
            target,
            hp,
            ) -> int:
        return hp

    @Record
    def hp(
            target,
            hp,
            ) -> int:
        return hp

    @Record
    def resistances(
            target,
            ) -> dict[str, float]:
        return {}
```

Apply it with one set of named inputs:

```python
sparkit = Creature(
        name="Sparkit",
        level=3,
        )

Battle_Ready(
        sparkit,
        hp=24,
        )
```

The `hp` input is written once. TagKit offers it to every Imprint and Record
materializer whose signature asks for `hp`:

```python
assert sparkit.max_hp == 24
assert sparkit.hp == 24
assert sparkit.combat_log == [
        "Entered battle with 24 HP.",
        ]
```

The decorated class member's name becomes the Record name. Its returned value
is materialized once during Tagging and assigned to the Agent.

It is not a dynamic property:

```python
sparkit.hp -= 5
sparkit.resistances[ "electric" ] = 0.5

assert sparkit.hp == 19
assert sparkit.resistances == {
        "electric": 0.5,
        }

assert Battle_Ready[ sparkit ].hp == 24
```

The Agent carries the current mutable value. The Tag-bound view remembers the
value captured when `Battle_Ready` applied. Neither access recalculates the
Record.

This gives you two clean authoring styles:

| Need | Prefer |
| --- | --- |
| Establish several related values as one procedure | `@Imprint` |
| Mutate existing state or perform ordered setup | `@Imprint` |
| Declare one Record with a clear name | `@Record` |
| Produce a fresh list, set, or dictionary for each Agent | `@Record` |
| Extend a previous same-name Record with `@Underlay` | `@Record` |

They can coexist in one Tag, as `Battle_Ready` demonstrates. Avoid assigning
the same attribute through both routes unless replacement is intentional:
Imprints run after Records, so an Imprint write becomes the visible value.

---

## Tag or Record?

Use a Tag for a durable semantic category:

```text
Fire
Electric
Dragon
Boss
Flying
Merchant
```

Use a Record for mutable state:

```text
hp
armor
burn_turns
resistances
inventory
remaining_charges
```

A temporary burn is usually not a new identity:

```python
ember.statuses.add( "burning" )
ember.statuses.remove( "burning" )
```

The creature remains Fire, Electric, Armored, or whatever else it has become.

---

## Reapplying an active Tag does not reset Records

```python
ember.armor = 2

Armored(
        ember,
        armor=99,
        )

assert ember.armor == 2
```

Active reapplication is a strict no-op:

- Imprints do not run again;
- Records do not reset; and
- Field membership is not duplicated.

If your game needs healing, recharging, or resetting, model that as an Action
or an explicit system operation.

---

## Reports are shared Tag data

Every public data value declared on a Tag is a Report. It remains ordinary
Python data on that Tag and also participates in Tag-bound views, Overlays,
Underlays, Pins, and Delete.

Records belong to one creature:

```python
ember.hp
rivlet.hp
```

Reports belong to the whole Tag:

```python
Fire.color
Water.color
Electric.color
```

Reports suit:

- presentation colors;
- damage categories;
- source books;
- ruleset versions;
- default assets;
- schemas; and
- other shared semantic information.

Prefer immutable Report values unless shared mutation is intentional.

---

# Part III — Actions compose abilities

## Actions belong to Agents

An Action becomes callable on every current Agent of its Tag:

```python
ember.take_damage( 5 )

assert ember.hp == 25
```

```python
ember.shock( training_dummy )
rivlet.water_jet( training_dummy )
```

A bare Tag method is also treated as an Action. `@Action` is the explicit
form and is particularly useful when decorators are stacked.

---

## One name, two spellings

An Action and a Record are still two kinds. What they share is the Agent
address: one visible name, one meaning, readable with or without `()`.

```python
assert ember.hp == 30
assert ember.hp() == 30

assert ember.motto == "onward"
assert ember.motto() == "onward"

send = ember.strike
send( training_dummy )
```

`ember.hp()` does not rematerialize the Record. It returns the stored value.
`ember.motto` without `()` evaluates that nullary Action. `ember.strike`
without `()` is still the handle, so a later `send( dummy )` works after Rip
the same way a bound method would.

This is Uniform Access, not a third contribution. Independent Tags still
cannot share one Agent name as both an Action and a Record. A Shape may
still Overlay a Base Action with a Record, or the reverse. That is
**polymorphic behaviour** in TOP: one name, one meaning per view, readable
with or without `()`:

```python
assert ember.strike == 4
assert ember.strike() == 4
assert Combatant[ ember ].strike == 1
assert Combatant[ ember ].strike() == 1
```

Use `ember.hp()` when Python needs the raw object (`isinstance`, `is None`,
JSON). Equality, arithmetic, and `ember.hp -= 8` use the stored value.

---

## Underlays extend the visible Action

`Combatant.attack` introduced physical damage.

`Fire.attack` extended it:

```python
assert Fire[ ember ].attack( training_dummy ) == {
        "physical": 5,
        "fire": 4,
        }
```

`Electric.attack` then extended the complete visible result:

```python
assert Electric[ ember ].attack( training_dummy ) == {
        "physical": 5,
        "fire": 4,
        "electric": 3,
        }
```

The current Overlay is available directly:

```python
assert ember.attack( training_dummy ) == {
        "physical": 5,
        "fire": 4,
        "electric": 3,
        }
```

The second input of an `@Underlay` contribution receives the captured
contribution beneath it:

```python
@Action
@Underlay
def attack(
        target,
        prior,
        enemy,
        ):
    damage = prior( enemy )
    ...
```

This supports:

- elemental damage layers;
- equipment bonuses;
- class features;
- difficulty modifiers;
- AI behavior refinements;
- animation decorators; and
- content-pack extensions.

If no compatible contribution exists underneath, applying the extending Tag
fails rather than silently inventing behavior.

---

## Polymorphic behaviour: a Shape may fix an Action as a Record

Specialization may turn a computed Action into stored data. That is Overlay
inside a Form, not a name collision between independent Tags. The client asks
what `strike` is **for**, not whether it is stored or calculated — the same
Ada-style uniform access, adapted to TOP's Overlay model:

```python
class Combatant(Tag):

    def strike(
            target,
            ) -> int:
        return 1


class Fire(Combatant):

    @Record
    def strike(
            target,
            ) -> int:
        return 4


Fire(ember)

assert ember.strike == 4
assert ember.strike() == 4
assert Combatant[ember].strike() == 1
assert Combatant[ember].strike == 1
```

The current Overlay is the Record. The Base view still holds the Action.
Both spellings work on each view. The reverse Overlay is the same law: a
Shape Action may compute from a Base Record. `@Underlay` still requires the
prior visible contribution to have the same kind. Independent Tags still
cannot share one Agent name as both an Action and a Record.

---

## Current access and Tag-bound access

```python
ember.attack( training_dummy )
```

uses the latest visible Overlay.

```python
Fire[ ember ].attack( training_dummy )
```

uses the Overlay captured when `Fire` applied.

```python
Electric[ ember ].attack( training_dummy )
```

uses the Overlay captured when `Electric` applied.

That distinction is valuable for:

- combat logs;
- debugging generated builds;
- comparing pre-evolution and post-evolution behavior;
- inspecting which content pack contributed a feature; and
- rendering a character sheet by source.

Tag subscription has two related forms:

```python
Fire[:]             # every sound Fire creature
~Fire[:]            # defective Fire members (Posts fail)
Fire[:] | ~Fire[:]  # U-set: the whole Field
Fire[ ember ]       # Embercub through its Fire card
```

If your game has knights, `Knight[:]` naturally means “all sound Knights.”
`~Knight[:]` is the repair queue.
The syntax works even when nobody at the table gets the joke.

---

## Delete a visible contribution

`@Delete` masks a contribution by name:

```python
from TagKit import Delete


class Pacifist( Tag ):

    @Delete
    def attack(
            target,
            enemy,
            ) -> None:
        pass
```

```python
peaceful = Creature( "Mossfriend" )

Fire(
        peaceful,
        max_hp=24,
        fire_resistance=0.4,
        )
Pacifist( peaceful )

assert not hasattr(
        peaceful,
        "attack",
        )
```

Earlier Tag-bound views remain available while their Tags are active:

```python
assert Fire[ peaceful ].attack( training_dummy ) == {
        "physical": 5,
        "fire": 4,
        }
```

Delete changes the visible Overlay. It does not remove Field membership.

---

# Part IV — Species and evolution

## A Form grows from general to specific

Elemental Type and Species are different semantic routes:

```python
class Species( Tag ):
    pass


class Emberling( Species ):

    @Action
    def species_cry(
            target,
            ) -> str:
        return f"{target.name} crackles."


class Pyroclaw( Emberling ):

    @Imprint
    def set_evolution_records(
            target,
            hp_bonus,
            ) -> None:
        target.max_hp += hp_bonus
        target.hp += hp_bonus

    @Action
    def claw_swipe(
            target,
            enemy: Creature,
            ) -> dict[str, int]:
        return {
                "physical": 9,
                }
```

Apply the initial Species:

```python
Emberling( ember )

assert ember in Species
assert ember in Emberling
```

Later, evolve the same creature:

```python
Pyroclaw(
        ember,
        hp_bonus=12,
        )

assert ember in Pyroclaw
assert ember in Emberling
assert ember.max_hp == 42
assert ember.hp == 37
```

The Form is the ordered Base ancestry:

```python
assert Pyroclaw.Form() == (
        Species,
        Emberling,
        Pyroclaw,
        )
```

The Target never became a new Python object.

---

## One creature can carry several Forms

```python
forms = ember.Forms()

assert (
        Element,
        Combatant,
        Fire,
        ) in forms

assert (
        Element,
        Combatant,
        Electric,
        ) in forms

assert (
        Species,
        Emberling,
        Pyroclaw,
        ) in forms
```

Together those Forms make the current Geometry:

```python
geometry = ember.Geometry()

assert geometry[ Element ] == (
        Fire,
        Electric,
        )
assert geometry[ Species ] == (
        Emberling,
        )
```

`Outline()` gives tooling and debug UIs a ready-made view:

```python
print( ember.Outline() )
```

```text
Creature
  Element
    Fire
    Electric
  Combatant
    Fire
    Electric
  Armored
  Species
    Emberling
      Pyroclaw
```

This is useful for:

- build inspectors;
- generated-character previews;
- save debugging;
- content validation; and
- editor tooling.

---

# Part V — Fields, queries, and catalogs

## Fields are live registries

```python
for wizard in Wizard[:]:
    play( wizard )

for broken in ~Wizard[:]:
    review( broken )
```

`Tag[:]` iterates **sound** Field members — Agents whose visible
Postconditions currently hold. `~Tag[:]` is the defective complement —
still in the Field, Posts fail. Together they are the U-set for that Tag:

```python
assert creature in Fire[:] or creature in ~Fire[:]
assert ( Fire[:] | ~Fire[:] ) is Fire.Field
```

```python
for creature in Fire[:]:
    render_fire_aura( creature )

for broken in ~Fire[:]:
    repair( broken )
```

Fields:

- contain committed current Agents;
- include Agents of active Shapes;
- preserve application order;
- are read-only; and
- do not keep otherwise unused objects alive.

There is no parallel `all_fire_creatures` list to synchronize.

Use `Tag[:]` for gameplay rosters. Use `~Tag[:]` for repair and review
queues. Use `Tag[:] | ~Tag[:]` when you need every member.

---

## Current membership versus history

Use `in` for current Field membership:

```python
assert ember in Fire
```

TagKit uses `isinstance` for committed history:

```python
assert isinstance(
        ember,
        Fire,
        )
```

After Rip:

```python
Fire.Rip( peaceful )

assert peaceful not in Fire
assert isinstance(
        peaceful,
        Fire,
        )
```

The creature is no longer an active Fire Agent, but it did successfully carry
that meaning before.

Use current membership for normal gameplay. Ask about history only when the
history matters.

---

## `Tags` returns active leaves

```python
from TagKit import Tags


active_leaves = Tags( ember )
```

```python
assert Fire in active_leaves
assert Electric in active_leaves
assert Pyroclaw in active_leaves

assert Element not in active_leaves
assert Species not in active_leaves
```

The Bases remain active:

```python
assert ember in Element
assert ember in Species
```

Use each leaf's Form when you need its supporting Bases.

---

## `Has` asks semantic questions

```python
from TagKit import Has


assert Has(
        ember,
        Fire,
        Electric,
        Pyroclaw,
        )
```

Tag-name queries are case-insensitive:

```python
assert Has(
        ember,
        "fire",
        "electric",
        )
```

It can also ask whether a contribution is currently visible:

```python
assert Has(
        ember,
        Electric.attack,
        )
```

An Action hidden beneath a later same-name contribution is not the current
visible Action. Use a Tag-bound view to inspect that earlier Layer.

---

## Tag-level Reports and Operations

```python
assert Fire.color == "#ef5b35"
assert Electric.color == "#f5cf3d"
assert Water.color == "#3698db"
```

The Fire Operation uses its Field:

```python
assert Fire.roster() == (
        "Embercub",
        )
```

Operations suit:

- spawn-table construction;
- validation;
- shared calculations;
- catalog exports;
- encounter summaries; and
- editor integrations.

Actions are performed by one Agent. Operations belong to the Tag.

---

# Part VI — Contracts protect generated builds

Tagging is a factory line. Preconditions inspect the **incoming materials**:
may this Target receive this Tag? Postconditions inspect the **finished
product**: did the Tagging produce something sound? `@Pre` runs at the door
for the layers applied in this call only. If it fails, that layer never
applies. `@Post` runs after Imprints and re-checks every visible promise. If
it fails, the Tag stays as a defective result — inspectable, repairable, or
discardable by the caller.

---

## A Boss Tag with real requirements

```python
from TagKit import Post
from TagKit import Pre


class Boss( Tag ):

    @Pre
    def meets_level_requirement(
            target,
            minimum_level,
            ) -> bool:
        return target.level >= minimum_level

    @Imprint
    def set_boss_records(
            target,
            enrage_at,
            ) -> None:
        target.boss_phase = 1
        target.enrage_at = enrage_at

    @Post
    def has_valid_enrage_threshold(
            target,
            ) -> bool:
        return (
                target.enrage_at > 0
                and target.enrage_at < target.max_hp
                )
```

Embercub is eligible:

```python
Boss(
        ember,
        minimum_level=10,
        enrage_at=12,
        )

assert ember in Boss
assert ember.boss_phase == 1
assert ember.enrage_at == 12
```

A low-level creature fails before the Imprint:

```python
from TagKit import TagPreconditionError


newt = Creature(
        name="Newt",
        level=2,
        )

try:
    Boss(
            newt,
            minimum_level=10,
            enrage_at=5,
            )
except TagPreconditionError:
    pass
else:
    raise AssertionError(
            "A low-level creature became a Boss."
            )

assert newt not in Boss
assert not hasattr(
        newt,
        "boss_phase",
        )
```

A failed Tagging does not enter the Field and restores supported in-memory
Target changes.

External effects cannot be generically rolled back. Keep file writes, network
requests, achievements, and analytics after a successful boundary or give
them an explicit compensation path.

---

## Conditions are strict

**True always means the clause holds.** A condition returns:

- `True` — holds;
- `False` — fails; or
- `None` after successful assertions — also holds.

Return the comparison:

```python
def is_alive(
        target,
        ) -> bool:
    return target.hp > 0
```

Do not return arbitrary truthy or falsy state:

```python
def is_alive(
        target,
        ):
    return target.hp
```

Zero HP is meaningful data. Conditions should say exactly what it means.

---

## Inspect contracts

Visible Preconditions and Postconditions are Agent contributions. The basic
obvious checks are Uniform Access — bare or call; **True always means holds:**

```python
if ember.has_valid_enrage_threshold:
    ...

if not ember.has_valid_enrage_threshold():
    ember.enrage_at = ember.max_hp // 2

assert ember.meets_level_requirement
assert ember.has_valid_enrage_threshold()
```

Print the contract as a mini menu — no `Contract` import required:

```python
print(f"{ember:Contract}")
print(f"{ember:Display}")
```

`:Contract` and `:Display` show Pre and Post with OK / XX marks. `:Status`
is the flat list. Prefer these over `Contract.Display` in ordinary code.

When a Tagging fails a Post, catch the named clause. Python's `except` needs
an exception *type*, so use the named error — not `except ember.Has_…`:

```python
from TagKit import TagPostconditionError

try:
    Boss(
            newt,
            minimum_level=10,
            enrage_at=5,
            )
except TagPostconditionError.has_valid_enrage_threshold:
    repair(newt)
except TagPostconditionError as error:
    assert error.condition == "has_valid_enrage_threshold"
```

`Contract` remains available for explicit sweeps and editors:

```python
from TagKit import Contract


assert Contract.Preconditions( ember )
assert Contract.Postconditions( ember )
assert Contract.Conditions( ember )

status = Contract.Status( ember )
display = Contract.Display( ember )
```

`Status` returns one verdict per visible condition.

`Display` gives the same mini menu as `f"{ember:Display}"`.

When visible Postconditions exist, `bool( ember )` reports whether those
promises currently hold. Without visible Postconditions, TagKit preserves the
host object's native truth behavior.

Preconditions gate only the layers applied in the current call. Visible
Postconditions are re-checked at every later Tagging boundary, so a generated
build cannot quietly accept another Tag while breaking an existing promise.

---

# Part VII — Pins organize game content

## Classify Tags without side lists

Suppose a game wants discoverable starter Types:

```python
class Starter( Tag ):
    pass


class Rare( Tag ):
    pass
```

Pin the content cards:

```python
Starter( Fire )
Starter( Water )

Rare( Electric )
```

The Pin Fields become catalogs:

```python
assert tuple( Starter[:] ) == (
        Fire,
        Water,
        )

assert tuple( Rare[:] ) == (
        Electric,
        )
```

One Tag card can carry several independent Pins:

```python
Starter( Electric )

assert Electric in Starter
assert Electric in Rare
```

The Pin marks the `Electric` Tag. It does not automatically put every
Electric creature into the `Starter` Field.

Pins work well for:

- starter choices;
- rarity;
- biomes;
- expansion packs;
- game modes;
- platform availability;
- procedural-generation pools; and
- editor categories.

The [Pin Guide](PIN_GUIDE.md) covers overlapping Pins, Pin resources,
composition, and Rip in detail.

---

# Part VIII — Evolution of the codebase

## Add a new Type without editing old Types

An expansion can introduce Ice:

```python
class Ice(
        Element,
        Combatant,
        ):
    """Ice-aligned combatant."""

    color = "#9edff2"

    @Imprint
    def set_ice_records(
            target,
            ice_resistance,
            ) -> None:
        target.resistances[ "ice" ] = ice_resistance

    @Action
    @Underlay
    def attack(
            target,
            prior,
            enemy: Creature,
            ) -> dict[str, int]:
        damage = prior( enemy )

        return {
                **damage,
                "ice": damage.get(
                        "ice",
                        0,
                        )
                + 4,
                }

    @Action
    def frost_bite(
            target,
            enemy: Creature,
            ) -> dict[str, int]:
        return {
                "ice": 8,
                }
```

Register it through Pins:

```python
Starter( Ice )
```

Use it immediately:

```python
frostel = Creature(
        name="Frostel",
        level=5,
        )

Ice(
        frostel,
        max_hp=28,
        ice_resistance=0.65,
        )

assert frostel in Ice
assert frostel in Combatant
assert frostel.frost_bite( training_dummy ) == {
        "ice": 8,
        }
```

No central Type enum, Creature switch, combined subclass, or global registry
needed editing.

---

## Compose capabilities independently

```python
class Flying( Tag ):

    @Imprint
    def set_flight_records(
            target,
            flight_speed,
            ) -> None:
        target.flight_speed = flight_speed

    @Action
    def fly(
            target,
            destination: str,
            ) -> str:
        return f"{target.name} flies to {destination}."
```

```python
parrot = Creature( "Parrot" )

Water(
        parrot,
        max_hp=18,
        water_resistance=0.2,
        )
Flying(
        parrot,
        flight_speed=12,
        )

assert parrot in Water
assert parrot in Flying
assert parrot.flight_speed == 12
```

`Flying` does not need to know whether the Target is a monster, mount,
familiar, vehicle, or parrot. The capability composes where its contract
makes sense.

---

## Unify player and non-player actors

```python
class Actor( Tag ):
    pass


class Player( Actor ):
    pass


class Non_Player( Actor ):
    pass


class Merchant( Tag ):

    @Imprint
    def set_merchant_records(
            target,
            wares,
            ) -> None:
        target.wares = list( wares )

    @Action
    def list_wares(
            target,
            ) -> tuple[str, ...]:
        return tuple( target.wares )
```

```python
shopkeeper = Creature( "Mira" )

Non_Player( shopkeeper )
Merchant(
        shopkeeper,
        wares=(
                "Potion",
                "Capture Orb",
                ),
        )

assert shopkeeper in Actor
assert shopkeeper in Non_Player
assert shopkeeper in Merchant
```

Player and non-player characters can share Species, professions,
backgrounds, names, titles, dialogue, inventory, and narrative features.
Only genuinely different behavior needs a separate Tag.

---

# Part IX — Functional and multiparadigm use

## Apply several Tags

```python
from TagKit import Apply


voltwing = Apply(
        Creature(
                name="Voltwing",
                level=9,
                ),
        Electric,
        Flying,
        max_hp=34,
        electric_resistance=0.7,
        flight_speed=16,
        )
```

`Apply`:

- validates every requested Tag first;
- applies them in order;
- offers keyword inputs to matching protocols; and
- returns the same Target.

```python
assert voltwing in Electric
assert voltwing in Flying
assert voltwing.max_hp == 34
assert voltwing.flight_speed == 16
```

Tag classes are unary transformations when they need no additional inputs:

```python
actors = list(
        map(
                Non_Player,
                actors,
                )
        )
```

---

## Checkpoint a design phase

A generated build is often a design before it becomes durable meaning. Select
the Tags with ordinary Python data, then apply them in their intended order:

```python
selected_tags = (
        randomizer.choice( SPECIES_TAGS ),
        randomizer.choice( BACKGROUND_TAGS ),
        randomizer.choice( CLASS_TAGS ),
        )
```

When partial success is useful, apply the Tags normally. Each successful call
commits independently:

```python
for selected_tag in selected_tags:
    selected_tag( creature )
```

When the whole design must be recoverable, create a Checkpoint from `Tag`.
The control object stays outside the Target, so it does not claim a useful
Target member name:

```python
checkpoint = Tag.Checkpoint( creature )

try:
    for selected_tag in selected_tags:
        selected_tag( creature )

    if not archetype_is_approved( creature ):
        raise Invalid_Archetype(
                "The selected Tags do not form an approved archetype."
                )

except Exception:
    checkpoint.Restore()

    raise

else:
    checkpoint.Commit()
```

The Tags still run one at a time and in written order. Preconditions
and Records still commit that call or roll it back. An Imprint failure
is a machine error and leaves the Tag applied. A Postcondition failure
is a defective result and leaves the Tag applied too. The Checkpoint
adds one outer publication and recovery boundary:

- Imprints and later Tags can use the provisional Records and Actions;
- `Commit()` publishes every newly applied membership together;
- `Restore()` recovers the entry type, Tag state, attributes, slots, and
  supported mutable containers;
- previously committed Tags remain committed; and
- the Target keeps the same identity throughout.

Field membership, `Tags`, `Has`, Tag-bound views, and historical `isinstance`
continue to report the committed entry state until `Commit()`. This prevents a
half-designed Agent from appearing in registries.

A context manager provides the same control flow when normal exit means
approval and an exception means rejection:

```python
with Tag.Checkpoint( creature ) as candidate:
    for selected_tag in selected_tags:
        selected_tag( candidate )

    if not archetype_is_approved( candidate ):
        raise Invalid_Archetype(
                "The design was rejected."
                )
```

Use an explicit test and exception for production approval. Python may remove
`assert` statements under optimization, so assertions are best reserved for
development diagnostics.

A Checkpoint is not Rip and does not erase committed history. Rip is forbidden
while a Checkpoint is provisional. The rollback journal also cannot undo
external I/O, mutations hidden inside opaque custom objects, or changes to
another object graph. Keep those effects after `Commit()`, or compensate for
them explicitly.

The same mechanism works when the Target is a Tag during Pin design.
Every explicitly created Checkpoint must finish with `Commit()` or `Restore()`;
prefer the context-manager form when no later decision needs the control
object.

`Commit()` publishes the decision; it does not invent an approval rule.
Evaluate the domain condition, or call the relevant `Contract` checks, before
committing.

---

## OOP coexistence

```python
assert isinstance(
        ember,
        Creature,
        )
```

The host's ordinary methods, descriptors, slots, and attributes remain
available. TOP contributions join the visible interface by name.

Use module-level `Apply`, `Tags`, and `Has` when an existing host already owns
methods with those names.

TagKit can sit beside:

- ordinary OOP;
- dataclasses;
- functional pipelines;
- data-driven factories;
- ECS-style subsystems;
- plugin architectures; and
- editor tooling.

TOP supplies semantic context. It does not demand ownership of the whole
architecture.

---

## Async Actions and Operations

Actions and Operations may be asynchronous:

```python
class Network_Visible( Tag ):

    @Action
    async def serialize_for_client(
            target,
            ) -> dict[str, object]:
        return {
                "name": target.name,
                "hp": target.hp,
                }
```

Tagging protocols remain synchronous:

- Preconditions;
- Imprints;
- Postconditions; and
- Rip protocols.

One Tagging boundary should complete before the game exposes the resulting
Agent.

---

# Part X — Rip and bounded roles

## Rip ends active membership

```python
Armored.Rip( ember )

assert ember not in Armored
assert isinstance(
        ember,
        Armored,
        )
```

History remains committed. Records and Actions are sticky unless an explicit
Rip protocol changes them.

Rip is exceptional. Mutable gameplay state normally belongs in Records.

---

## Cleanup through a Rip protocol

```python
from TagKit import Rip


class Arena_Participant( Tag ):

    @Imprint
    def set_arena_records(
            target,
            ) -> None:
        target.turn_energy = 1

    @Action
    def spend_turn_energy(
            target,
            ) -> None:
        target.turn_energy = 0

    @Action
    @Rip
    def leave_arena(
            target,
            ) -> None:
        target.turn_energy = 0
```

---

## Scope owns temporary membership

```python
from TagKit import Scope


with Scope(
        rivlet,
        Arena_Participant,
        ):
    assert rivlet in Arena_Participant
    assert rivlet.turn_energy == 1

assert rivlet not in Arena_Participant
assert rivlet.turn_energy == 0
```

`Scope` Rips exactly the memberships it added, even if the block raises.

Memberships active before entry are borrowed and remain active afterward.

Use `At_Exit( agent )` only for best-effort interpreter-exit cleanup.
Explicit Rip and `Scope` are deterministic.

---

# Part XI — Design choices that scale

## Host, Tag, Record, or Report?

| Question | Put it in |
| --- | --- |
| Is it inherent structure owned by the application? | Host |
| Is it a durable semantic category? | Tag |
| Is it mutable state for one Agent? | Record established during Tagging |
| Is it shared information about one Tag? | Report |

Example:

| Game concept | Model |
| --- | --- |
| stable save identifier | Host |
| Fire Type | Tag |
| current HP | Record |
| Fire UI color | Report |

---

## Base, independent Tag, or Pin?

| Question | Model |
| --- | --- |
| Should every Shape Agent carry the broader meaning? | Base |
| Should this one object gain another separate meaning? | Independent Tag |
| Should this Tag card appear in a content category? | Pin |

Examples:

- `Fire` is a Shape of `Element`;
- Embercub independently carries both `Fire` and `Electric`; and
- the `Fire` card is Pinned `Starter`.

---

## Common mistakes

- **Declaring an optional later layer as a Base.** A Base is required and
  applies before the Shape. Apply a later or conditional Tag from the Imprint.
- **Making every status a Tag.** Mutable and temporary conditions normally
  belong in Records.
- **Creating combined subclasses.** Compose independent Tags at runtime.
- **Using a Report for per-creature state.** Reports are shared.
- **Expecting reapplication to reset data.** Active reapplication is a no-op.
- **Expecting Rip to undo history.** It ends active membership.
- **Mutating a Field directly.** Tagging and Rip own membership.
- **Assuming `Tags( creature )` returns every Base.** It returns active leaves.
- **Returning truthy values from Conditions.** Return explicit booleans.
- **Doing irreversible I/O inside provisional Tagging.** It cannot be
  generically rolled back.
- **Demanding exact runtime classes.** Prefer `isinstance`.
- **Using `is` on a Record or Action.** TagKit hands out a bound member so
  both `name` and `name()` work. Compare with `==`, or call `()` for the raw
  Python object.

---

# Part XII — Python profile boundaries

## Suitable Targets

TagKit works best with ordinary user-defined Python objects.

A Target must support:

- weak references;
- compatible runtime class composition; and
- writable state when Tagging establishes Records.

Strings, integers, tuples, and most built-in containers cannot carry TagKit
state directly. Wrap the value in a small domain object and Tag that object.

Object identity remains stable:

```python
before = id( ember )

Boss(
        ember,
        minimum_level=10,
        enrage_at=12,
        )

assert id( ember ) == before
```

The Python profile actualizes the Agent through a compatible runtime subclass.
`isinstance( ember, Creature )` remains true, but exact
`type( ember ) is Creature` checks can observe the runtime adapter.

Concurrent Tagging of the same Target is unsupported. Finish one Tagging or
Rip before starting another on that Target.

---

## Record materializers are not dynamic properties

`@Record` calls the decorated function once during Tagging and writes the
returned value into the Target. Later reads, including `agent.stamina()`,
return that stored value. They do not run the materializer again.

The resulting attribute remains mutable Agent state:

```python
@Record
def stamina(
        target,
        stamina,
        ):
    return stamina
```

The decorator gives TagKit enough information to track the Record's origin,
capture its Tag-bound value, compose it through an Underlay, and restore the
previous value if Tagging fails. It does not turn the attribute into a
descriptor that recalculates on access.

Use an Imprint when procedural setup reads more clearly. Use `@Record` when
one named materializer communicates the Record more clearly.

---

## Failure types

| Error | Meaning |
| --- | --- |
| `TagResolutionError` | a Tag view or required Underlay cannot resolve |
| `TagPreconditionError` | a Precondition refused Tagging |
| `ImprintingError` | an Imprint failed after the Tag applied (`TagImprintError` is the same error) |
| `TagPostconditionError` | a Postcondition found a defective applied Tag |
| `TagCompositionError` | contributions cannot form a valid Overlay |
| `TagContractError` | a Condition returned an invalid verdict |
| `TagDeletionError` | a requested deletion cannot apply |

All derive from `TagError`.

`TagOverwriteWarning` and `TagContractWarning` identify allowed composition
decisions that deserve attention.

---

# API pocket reference

## Core operations

| Intention | Python |
| --- | --- |
| Define a Tag | `class Fire( Tag ): ...` |
| Apply one Tag | `Fire( creature, ... )` |
| Apply several Tags | `Apply( creature, Fire, Flying, ... )` |
| Open recoverable Tagging | `checkpoint = Tag.Checkpoint( creature )` |
| Publish a Checkpoint | `checkpoint.Commit()` |
| Recover a Checkpoint | `checkpoint.Restore()` |
| Check current membership | `creature in Fire` |
| Check committed history | `isinstance( creature, Fire )` |
| Iterate sound Field members | `for wizard in Wizard[:]: play( wizard )` |
| Iterate defective Field members | `for broken in ~Wizard[:]: review( broken )` |
| Whole Field (U-set) | `Wizard[:] \| ~Wizard[:]` |
| Open one Tag-bound view | `Fire[ creature ]` |
| List active leaf Tags | `Tags( creature )` |
| Query Tags or Tag names | `Has( creature, Fire, "flying" )` |
| Read a Form | `Fire.Form()` |
| Read Agent Forms | `creature.Forms()` |
| Read Agent Geometry | `creature.Geometry()` |
| Render the Geometry | `creature.Outline()` |
| End active membership | `Fire.Rip( creature )` |
| Own bounded membership | `with Scope( creature, Arena ): ...` |
| Register best-effort exit cleanup | `At_Exit( creature )` |
| Verify contracts | `Contract.Conditions( creature )` |
| Print the contract mini menu | `f"{creature:Contract}"` / `f"{creature:Display}"` |
| Read a Record as data or as a call | `creature.hp` / `creature.hp()` |
| Read a nullary Action as data or as a call | `creature.motto` / `creature.motto()` |
| Read a Condition | `creature.Has_Spellbook` / `creature.Has_Spellbook()` |

---

## Contributions

| Contribution | Scope | Purpose |
| --- | --- | --- |
| Tag | Field | durable semantic category |
| Action | Agent | behavior |
| Record | Agent | mutable state established during Tagging |
| Imprint | Tagging | establish Records and application-time context |
| Precondition | Tagging / Agent | incoming-material gate; binary Agent check |
| Postcondition | Tagging / Agent | finished-product promise; binary Agent check |
| Underlay | Layer | extend the compatible contribution beneath |
| Delete | Overlay | mask a named contribution |
| Rip | Exit | explicit teardown |
| Report | Tag | shared information |
| Operation | Tag | shared behavior |

---

# Start building

A practical monster generator can begin this small:

```python
creature = Creature(
        name=generated_name,
        level=generated_level,
        )

selected_type(
        creature,
        **generated_records,
        )

if creature in selected_type:
    encounter.add( creature )
```

From there, Species, evolutions, roles, backgrounds, abilities, Pins, and
content packs can grow independently around the same creature.

That is the value TagKit offers an indie game:

> Add a new meaning without rebuilding the object that carries it.
