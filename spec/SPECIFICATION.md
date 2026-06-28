# 🏷️ Guide to Tag-Oriented Programming 🔖

## 🏷️ Introduction

Tag-Oriented Programming (TOP) provides utility without changing identity.

By semantic increments, it provides new features without changing the essence of a target.

A hero is one character. Over a game she becomes a Human, a Wizard, a Sage, a Harper... and stays the same hero. TOP adds each meaning as a Tag; the object keeps its identity the whole way.

Traditional programming often asks, "what is this object?" TOP asks, "what is this object's use?", and lets the answer grow naturally.

You don't need object-oriented programming to use TOP. But if you know OOP, you will discover a complementary model that empowers your code with easy-to-use features and modular refactoring. Implementing TOP can make your codebases more structured, bringing forth Functional Programming and Contract Programming features without the headaches of refactoring your existing code. If you don't have a programming style yet, TOP provides an easy-to-follow model that has proven to be powerful and intuitive.

TOP governs the substrate over OOP with membership and contracts.

> **TOP is a programming paradigm for composing semantic layers on one stable object identity.**

TOP lets a Target take on semantic meanings that cut across ordinary class hierarchies.


Instead of forcing every semantic distinction into one class tree, TOP lets
Tags compose independently on one Target.

The Target keeps its identity.
Its semantic meaning expands through composition.

When a Tag is successfully applied, the Target becomes an Agent of that Tag: a concrete, acting expression of that abstraction.

Initially inspired by tabletop RPG systems (like D&D), Tags behave like roles, jobs, backgrounds... They may bring forth specifications for the Agent, determine mutable states with Records, bestow Actions, and establish Tag-level functionality.

A Target may be Human, Wizard, Sage, or any other semantic role while
remaining that same Character.

---

## 🔰 TOP's Mental model

TOP works with one identity and many semantic layers.

If an element is tagged as `Human`, then later tagged as `Wizard`, there is still one character. The element is not replaced conceptually. Its semantic role expands.

TOP therefore combines two truths:

- the Target remains the same entity; and
- its visible semantic relation changes as Tags are composed.

If `Human` exists on top of `Species`, then tagging with `Human` also implies membership in `Species`.

When a Tag is successfully applied to a Target, that Target becomes an Agent of the Tag. A concrete, acting expression of that abstraction.

```python
Human( charlie )

assert charlie in Human
```

The primary result is membership in a semantic category. 

A Tag may also contribute Actions, Records, Conditions, and an Imprint, but none of those contributions defines membership.

````python
class Hero():
    def __init__(self, name):
        self.name = name

class Species(Tag):
    pass

class Human(Species):
    pass

class Wizard(Tag):
    pass


charlie = Hero("Charlie")
Human(charlie)
Wizard(charlie)

assert isinstance(charlie, Character)
# charlie is still a Character Object 

print(f"{charlie.name} is a great hero.")

if charlie in Species: 
    if charlie in Human:
        print(f"{charlie.name} is a human.")
    else:
        print(f"{charlie.name} is of a non-human species.")


if charlie in Wizard:
    print(f"But {charlie.name} is also a Wizard.")
````
````txt
Charlie is a great hero.
Charlie is a human.
But Charlie is also a wizard.
````

An otherwise empty Tag is therefore meaningful. It can still define a
category and a Field of Agents.

The Target keeps its identity. Its semantic meaning expands through composition.

---

## ⚖️ TOP with OOP

Ordinary Object Oriented Programming mainly answers:

> What **is** this object?

TOP answers a different question:

> What's the use for this object?

TOP is external as a way of thinking: Tags are applied to an existing Target and compose visible semantic layers around it. OOP remains available for the Target's inherent structure, ordinary methods, and ordinary attributes.

TOP complements OOP. The same project may use both.

| OOP | TOP |
| --- | --- |
| Internal | External |
| Parts | Layers |
| Structures | Semantics |
| What it is | What it does |
| Definition | Use |
| Inheritance | Overlay |

TOP does not eliminate OOP, but complements it. The same structure may exist with or without TOP, in the same way it may or may not exist with OOP.

TOP is appropriate for durable meanings such as:

- species;
- roles;
- backgrounds;
- affiliations;
- skill trees;
- jobs;
- classifications;
- gameplay development; and
- permissions whose membership is intentionally durable.


---

## 💡 Design Patterns

TOP should be:

- clear before clever
- readable before dense
- explicit before magical
- semantically strong before syntactically fancy
- orthogonal before tangled
- contract-aware where obligations are real
- practical

TOP should not become:

- a bag of decorators without a model
- a disguised form of class-centric design
- a syntax trick without stable semantic laws
- a system where Target scope and Tag scope blur together




---

# 🧰 Core vocabulary

## 🛠️ Core entities

| Term    | Meaning |
|---------|---------|
| **Tag** | A semantic category that can contribute meaning, behaviors, values, and constraints. |
| **Target** |  A variable (value, dictionary, record, object...) before or during tagging. |
| **Tagging** | Applying a Tag to a Target, such as `Human(charlie)`, so the Target becomes an Agent of that Tag. |
| **Agent** | A variable (value, dictionary, record, object...) when it belongs to a Tag. |
| **Field** | The population of Agents belonging to a Tag. |


| Term | Meaning |
| --- | --- |
| **Base** | A broader Tag that a Shape specializes. |
| **Shape** | A more specific Tag built over one or more Bases. |
| **Layer** | One Tag's semantic position in an Agent's composition. |
| **Overlay** | The currently visible result of all active Layers. |
| **Underlay** | The visible contribution captured immediately before a new contribution is applied. |

TOP uses **Base**/**Supertag** and **Shape**/**Subtag** for specialization vocabulary. It does not use OOP parent/child
terminology to avoid conflicts with OOP.


---
# 🔩 Contributions

TOP distinguishes between contributions made on the Agent and contributions kept on the Tag Field.


Noun -> Tag (a category you are), adjective -> Record (a state you're in).
## 🪪 Agent-level contributions

- **Action**: behavior exposed on the Agent
- **Record**: state exposed on the Agent


A Tag usually corresponds to __*Nouns*__, things you are (_ser_), while Records provide mutable states (_estar_), so they correspond to __*Adjectives*__. Tags should not be used for circumstantial states, but to provide the Records that hold those states on the Agent.

## Imprinting and Ripping

- **Imprint**: application-time logic that shapes the Target when a Tag is applied
- **Rip**: extraction-time logic that shapes the Target when a Tag is rescinded.

Imprint shapes the Agent when active Field membership begins. Rip cleans up when active Field membership ends. They are duals: constructor/destructor, __enter__/__exit__. 

> ### __Tags are sticky.__ 
> Ripping does not revert the Agent back to a pre-Tagging state. Any Action, Record, or Condition applied to a Target remains after Ripping the Tag unless a Rip protocol explicitly changes it. Rogue Agents are dangerous... but useful!

- Imprint applies all missing Bases of a Tag by default.
- Ripping removes the Agent from the Tag's Field and, by default, from the Fields of Shapes that depend on that Tag.



## 📇 Field-level contributions

- **Report**: shared semantic data, stored on the Tag, across the Field.
- **Operation**: shared behavior on the Tag

In short:

- ◀️ Actions define behavior
- ⏺️ Records define state
- ⏸️ Imprints shape taggings
- ⏪️ Operations define shared behavior
- ⏹️ Reports define shared information

This data/function structure avoids repetition, keeping structural behavior separate from individual object behavior.
---

## 🪢 Membership and Fields

Membership is closed upward through Bases.

```python
class Mortal(Tag):
    pass


class Human(Mortal):
    pass


Human( charlie )

assert charlie in Human
assert charlie in Mortal
```

If an Agent belongs to a Shape, it belongs to every active Base required
by that Shape. The Agent appears in the Field of each of those Tags.

> In TOP, Field Membership Checks (`agent in Tag`) means active Field membership. It does not mean that the Agent's history or identity is erased when Field membership ends.
> **Ripping** is the only explicit exception to monotonic membership: it removes the Agent from the Field. Ripping exists for utility, cleanup, or in-extremis domain resolution, as a safety feature. But it does not undo the fact that the Agent _is an instance_ of the Tag.
> The Agent remains historically an instance of the Tag abstraction, even after leaving the active Field. Therefore, `isinstance` in Python should return true. Same for its equivalent in other languages.

```python
for agent in Mortal:
    Observe( agent )
```

A Tag must not keep an Agent alive. Once an
Agent no longer exists, it must no longer appear in any Field. A Python
implementation will normally use weak references to satisfy this law.

Reapplying an active Tag does nothing. It neither duplicates membership nor runs its Imprint again.

---

# 🏳️ Applying Tags

The canonical semantic act is:

```python
Tag( target )
```

An implementation may provide readable sugar, but sugar must preserve the same semantics.

### 🧋 Hidden Layering

Applying a Tag follows this order:

1. Apply each missing direct Base.
2. When a Tag has several direct Bases, apply them in declaration order.
3. Apply the requested Tag after its required Bases.

Each Base follows the same rule recursively. A Base required through
more than one path applies only once.

```python
class Arcane_Duelist(
        Spellcaster,
        Duelist,
        ):
    pass
```

Applying `Arcane_Duelist` first applies the missing `Spellcaster` branch,
then the missing `Duelist` branch, then `Arcane_Duelist` itself.

### 🧯 Expectations On Failed Taggings

Tagging has no side effects. If an imprint fails to stick the Shape Tag, it does not apply new dependency Tags either. The Overlay will stay as before the Tagging call. Tags committed by earlier calls survive unchanged.


```text
Human(ari)
    Species succeeds
    Human fails

ari in Human     == False
ari in Species   == False

```

For complex Taggings, incremental calls provide better control than one large Shape Tag, but TOP provides abstraction for hiding those complexities.


---
# Composition

Composition is order-sensitive for independent Tags. The last successful application of a Record or Action becomes the visible Overlay for that name. This is a core principle: TOP supports incremental design by letting later semantic layers refine, replace, or extend earlier ones. If the later Tag should preserve the previous behavior, it should use an Underlay. If a caller needs a specific historical layer, it should use Agent-bound Tag access.

---

# 🔩 Contributions

TOP distinguishes Agent-level and Tag-level contributions.

| Contribution | Kind | Scope | Meaning |
| --- | --- | --- | --- |
| **Action** | Callable | Agent | Behavior visible on an Agent. |
| **Record** | Data | Agent | State visible on an Agent. |
| **Imprint** | Callable | Tag application | Work performed while the Tag is applied. |
| **Operation** | Callable | Tag | Shared behavior belonging to the Tag. |
| **Report** | Data | Tag | Shared semantic data belonging to the Tag. |
| **Precondition** | Predicate | Tag application | A guard evaluated before Imprints. |
| **Postcondition** | Predicate | Tag application | A guard evaluated after Imprints. |

An Agent acts through Actions, remembers through Records, coordinates through Operations, and gains context by Reports.

Actions and Records actualize the Agent. They may replace ordinary OOP methods
and attributes as well as earlier TOP contributions.

Reports and Operations remain Tag-scoped, but they participate in the
Agent's Tag-contextual Overlay.

Temporary state lives in Records:

```python
agent.asleep = True
agent.asleep = False
```

The `asleep` Record may remain part of the Agent's state while its value changes. Tag membership remains unchanged through that transition.

---

# 💠 Layers and Overlays

The latest successfully applied Layer is the visible Overlay for a
contribution name. This applies to Actions, Records, Reports, Operations,
Preconditions, and Postconditions.

An ordinary Tag Action declaration has two semantic forms.

```python
class Person(Tag):

    def Attack(
            agent,
            ) -> str:
        return "Attack!"
```

An Action with no Underlay input introduces or replaces the visible
Action of that name. Replacing a contribution from an independent Tag is
allowed, but a conforming implementation should emit a diagnostic.

```python
class Elf(Person):

    @Action
    @Underlay
    def Attack(
            agent,
            underlay,
            ) -> str:
        return (
            "With elven grace "
            + underlay()
            )
```

An Action with an Underlay input extends the visible Action. `@Underlay` is the decorator that indicates an Action needs an underlay. It makes the second input, whatever its name, the call to the underlay Action with the same name. If no Action is available as an underlay, the Tagging raises an error.

The Underlay is captured when the Tag applies. It is the complete Action
visible immediately before that Tag's contribution. It does not dynamically
resolve again later.

```text
Paladin Underlay
    -> Elf visible Action
        -> Person visible Action
```

This is callable composition, not source-code copying. The captured callable
forms a backward chain and does not capture the Agent itself.

If no visible contribution exists, an Action that requires an Underlay
cannot apply successfully.

### 🥊 Dynamic Action calls

An Action that calls another Action through the Agent uses the current Overlay
at gameplay time.

```python
class Combatant(Tag):

    def Combat(
            agent,
            ) -> str:
        return agent.Attack()
```

If a later Tag actualizes `Attack`, `Combat` uses that later visible `Attack`.
Inside an `Attack` Action itself, calling `agent.Attack()` recurses into the
current Action. An extending Action uses its captured Underlay instead.

---

# 🪪 Records

A Record is Agent state contributed by a Tag. It becomes visible when its Tag applies successfully.

Records may:

- introduce a new name;
- replace an existing TOP Record;
- replace an ordinary Agent attribute;
- derive a value from the Underlay when the implementation exposes that
  form; or
- be removed at runtime with `del agent.record`.

Mutable Record values must be fresh for each Agent unless shared state is the explicit intent. A shared value belongs in a Report, not a Record.

A Tag is something a Target became and remains in its history: a durable semantic category. A noun is usually a Tag.

A Record is something a Target currently is: a value that can change. An adjective is usually a Record.

| Tag - you became this | Record - this can change |
| --- | --- |
| Human, Elf - species | asleep, poisoned - conditions |
| Wizard, Paladin - class | hit points, gold - resources |
| Sage, Soldier - background | location, morals |
| Harpers - affiliation | friends? Enemies? Affinity? - current status |
| Spellcaster - learned capability | spell slots left |
| Access Pass - an Agent is recognized by the system | Permission - the specific security clearance of the individual |


The same idea often splits across both. "Harper" is a Tag — you joined, and the joining is permanent history. "Affinity" is a Record: it changes. Tagging records that the membership happened; the Record tracks what's true now.

Records may be deleted altogether, but good design can often avoid this. Frequent Record deletion may indicate unclear state ownership. To delete a Record you may use `del agent.myRecord`. This may be useful in Ripping to optimize memory management and avoid overloading a Target.

```py
class Person:
    def __init__(self, name):
        self.name = name

class SafetyClearance(Tag):
    @Imprint
    def Protocol_Up(agent):
        agent.safety_clearance = "visitor"

class Worker(Tag):
    @Imprint
    def Protocol_Up(agent):
        agent.safety_clearance = "worker"

    @Rip
    def Protocol_Down(agent):
        agent.safety_clearance = "visitor"

```
---
##  Ripping Tags

Tags can be seen like a pass, a sticker, or a badge. Having one is nice, but they should have a function: a security pass should identify the user, a police badge needs the District and Agent's number, and a logistic's sticker needs a destination. Having a Tag without those Records makes for a dangerous state of uncertainty for the contract.

Ripping a Tag is an exceptional and violent act of Field expulsion. Like in 80s copaganda movies, to "return your badge" means the Agent is no longer an active member of the organization. But it creates a Rogue Agent: an element with the Actions and Records it had before Ripping the Tag, but without active access to the Tag's Field resources, Operations, or Reports. When an expulsion protocol is required ("Give me your badge and weapons. You can no longer go into the evidence room!"), the `@Rip` tag is used. A Rogue Agent can no longer be accessed by Field protocols.

````py
class Person:                       # a plain host class
    def __init__(self, name):
        self.name = name

class MI6(Tag):                     # MI6 is a Tag applied to a Person

    @Imprint
    def SetUp(agent, code):
        agent.code = code
        agent.status = "Full"

    @Rip
    def SetDown(agent):
        del agent.code
        agent.status = "Former MI6 Agent"

bond = Person("Bond James Bond")    # bond is a Person (the host object)

MI6(bond, code="007")               # tag bond as MI6
print(bond.code)                    # 007

MI6.Rip(bond)
print(bond.status)                  # Former MI6 Agent

assert bond not in MI6
````

Imprint shapes the Agent when active Field membership begins. Rip cleans up when active Field membership ends. They are duals: constructor and destructor, __enter__/__exit__.

> Note: Ripping a Tag may apply another Tag. Technically, it may even apply itself. That would be outside good TOP use, but it could prevent an Agent from ever leaving the Field.


---

# 🗑️ Deleting an Agent

Deletion of an Agent means it is also Ripped from its active Tags. To launch a deletion protocol, the `@Rip` modifier must define the actions to take on leaving.

```python
class Secret_Agent(Tag):
    active_agents = 0

    @Imprint
    def Activate(agent):
        agent.status = "Active"
        Secret_Agent.active_agents += 1

    @Rip
    def Deactivate(agent):
        agent.status = "Not Active"
        Secret_Agent.active_agents -= 1
```

Deletion always Rips the Agent. Any exit protocol will run on deletion of the hosting object.

---

# ⏸️ Imprints

An Imprint performs the action of tagging itself. A Tag may have zero or more Imprints. Within one Tag, they run in declaration order.

Tagging may also establish Preconditions and Postconditions. Conditions are TOP's tag-time guardrails: they decide whether the Tagging may commit, but they do not wrap ordinary gameplay Action calls.

For one Tag application, TOP performs this logical sequence:

1. Construct the candidate Overlay.
2. Evaluate every Precondition visible in that candidate Overlay.
3. Run the new Tag's Imprints.
4. Evaluate every Postcondition visible in that candidate Overlay.
5. Commit the Tag's active Field membership and TOP-managed
   contributions.

The detailed condition model is described in the Conditions section.

```python
class Wizard(Tag):

    @Post
    def Has_Spellbook(
            agent,
            ) -> bool:
        return hasattr(
                agent,
                "spellbook",
                )
    @Pre
    def LevelOverZero(agent):
        """ 
        A 0 level character can't gain the Wizard Role!
        """
        return (agent.level > 0)
```


---

# 🎫 Access model

TOP has three distinct access forms.

### 🪪 Current Agent access

```python
agent.Attack()
agent.weapon
```

This uses the current visible Overlay at the moment of access.

### 🪪 Agent-bound Tag access

```python
agent.Paladin.Attack()
agent.Paladin.HONOR_CODE
```

This accesses the Overlay snapshot immediately after `Paladin` applied to
that Agent. It includes all visible contributions that existed at that point,
including prior independent Tags. It does not change merely because a later
Tag actualizes the same name.

Agent-bound Tag access requires active Field membership in the requested Tag.
Otherwise it fails with a Tag-resolution error. A Rogue Agent may keep sticky
Actions and Records, but it does not keep Agent-bound Tag access after Rip.

### 🪪 Direct Tag access

```python
Paladin.Field
Paladin.Report
Paladin.Operation()
```

This accesses Tag-level meaning, not an Agent-bound Action. A target-scoped
Action needs an Agent context, which Agent-bound Tag access provides.

An implementation may choose a different syntactic form where direct dot
access collides with ordinary Agent attributes. It must preserve the three
semantic distinctions.

---

# 🖼️ Example: stable identity and captured Underlay

```python
class Character:

    def Attack(
            agent,
            ) -> str:
        return "Faulty OOP attack."


class Person(Tag):

    @Action
    def Attack(
            agent,
            ) -> str:
        return "Attack!"


class Elf(Person):

    @Action
    @Underlay
    def Attack(
            agent,
            underlay,
            ) -> str:
        return (
            "With elven grace "
            + underlay()
            )


class Paladin(Person):

    @Action
    @Underlay
    def Attack(
            agent,
            underlay,
            ) -> str:
        return (
            underlay()
            + " For your holy oath!"
            )


ari = Character()

Paladin( ari )
Elf( ari )

assert ari in Person
assert ari in Elf
assert ari in Paladin

print(ari.Attack())
# With elven grace Attack! For your holy oath!
print(ari.Paladin.Attack())
# Attack! For your holy oath!

```

The `Person` Base applies before `Paladin`. It remains active when `Elf` applies. Elf captures the complete current Attack Overlay: Person followed by Paladin. The later Tag replaces `ari.Attack()` without changing what `ari.Paladin.Attack()` means.

---

# 🚨 Failure model

TOP failures must identify the violated semantic rule. A language profile may use its own exception or result types, but it must distinguish at least:

| Failure | Meaning |
| --- | --- |
| **Tag Resolution Failure** | A required Underlay, Tag view, or contribution cannot be resolved. |
| **Tag Precondition Failure** | A candidate Overlay's precondition does not hold. |
| **Imprint Failure** | Tag application logic fails before the Tag becomes active. |
| **Tag Postcondition Failure** | A candidate Overlay's postcondition does not hold. |
| **Tag Composition Failure** | Contributions cannot form the required Overlay. |
| **Tag Contract Failure** | A condition returns a non-boolean (truthy/falsy) value instead of a strict True / False / None. |

Failure stops the current Tagging, preventing Dependencies that were not applied earlier from being committed. Modular and atomic application provides isolation from failure, keeping side effects contained. Dependency Tags committed earlier remain; the Agent does not lose previous successful taggings.

---

# 🧰 Implementation obligations

A conforming implementation must provide:

- stable Target identity under tagging;
- observable membership and Base membership;
- non-owning iterable Fields;
- ordered Base then Shape application;
- sticky Tag contributions;
- Active Field membership ends only by explicit Rip;
- the latest visible Overlay by contribution name;
- captured Underlays for extending contributions;
- Agent-bound Tag views that preserve historical overlay snapshots;
- tag-time Preconditions, Imprints, and Postconditions; and
- defined diagnostics and failure reporting.

An implementation may choose runtime type composition, generated wrappers,
proxies, trait machinery, static code generation, or another mechanism. Those
are implementation details.

TagKit is a Python implementation target for these obligations. Any gap in
TagKit is TagKit work, not a change to TOP.

---

## 🧧 Purpose of This Guide

This guide has two jobs:

- explain the programming model
- specify the observable behavior a TOP implementation should provide

This guide explains the model first and the current TagKit surface second.

Examples show intended meaning.
They do not freeze one permanent spelling.
---
## 🧯 TOP Commitments

A conforming TOP implementation must preserve the observable semantics defined by this guide.

Surface spellings may evolve.
Internal implementation strategies may evolve.
But the semantic laws must remain stable.

---
# TOP as a Paradigm
TOP was arrived at independently, from storage systems, organizational models, and D&D character creation. Several established ideas share pieces of it:

- Overlaying gives durable contributions, but fixed at tagging time. TOP keeps incremental change and moves acquisition to runtime, per object.
- Membership is monotonic by design principle. Rip is the explicit in-extremis exception: it removes active Field membership without reverting the Agent's identity, history, or sticky contributions.
- Mixins / traits compose behavior, but per class, resolved once. TOP composes per instance and freezes each layer as an Underlay.
- The Role Object pattern adds roles to a live identity, but treats removal as ordinary. TOP treats removal as exceptional: a role is something you became, while active Field membership is something that can be rescinded. States live in Records instead.
- Aspect-oriented programming layers behavior across a hierarchy. TOP's Imprints and conditions are a tag-time form of the same idea, scoped to a single semantic act.
- Entity-Component systems attach data to an identity. TOP keeps behavior with the category and adds membership ("every Wizard").
- TOP brings forth Design by Contract (Meyer/Eiffel) and Ada 2012 contracts.

TOP goes beyond these ideas to build a complete paradigm: sticky runtime contributions, active Field membership, captured overlays, tag-time contracts, and one scope x kind contribution model on a single stable identity, in one vocabulary.

More importantly to me, it provides a thinking system: a simple idea, with analogies to the real world, but powerful enough to simplify complex systems into an intuitive syntax. TOP is not just a library, not just a tool, but a new way to think about complex topics.



---
# ⚖️ Conditions

Conditions are TOP's contracts. They are tag-time guardrails: boolean checks that decide whether a Tagging is allowed to commit. A condition guards the *act of tagging*, not ordinary gameplay — an Action is never wrapped by a condition.

TOP has two conditions:

- **`@Pre`** — a Precondition. It guards *entry*: what must be true *before* a Tag may apply.
- **`@Post`** — a Postcondition. It guards the *promise*: what must be true *after* a Tag has applied.

A condition is a function with the Agent as its first input. As with every TOP contribution, the first parameter is the Agent by discipline; its name is yours to choose, never a reserved word.

```python
class Wizard(Tag):

    @Pre
    def Level_Over_Zero(agent):
        return agent.level > 0          # you need a level to become a Wizard

    @Post
    def Has_Spellbook(agent):
        assert agent.spellbook          # a Wizard always ends up with a spellbook
```

A condition is **strictly boolean**: it holds on `True` (or on absent `return` for an assert-style body that fell through), fails on `False`, and is *rejected* on anything else. TOP does not coerce truthy/falsy values, because they are not booleans, and prone to logic errors. A Record of `0` slots left is a real value, not a failure. So write the comparison you mean, `return agent.spell_slots > 0`, never the raw value `return agent.spell_slots` (which raises a contract error telling you to be explicit). 

The absence of a return statement defaults to True: a condition is a restriction, so saying nothing also permits. Legal until written into law.

---

## 🕰️ When conditions run

Conditions fire at tagging boundaries, never continuously during play. For one Tagging, TOP performs:

1. Build the candidate Overlay.
2. Evaluate every visible **Precondition**. If one fails → *Precondition Failure*; nothing commits.
3. Run the Imprints.
4. Evaluate every visible **Postcondition**. If one fails → *Postcondition Failure*; nothing commits.
5. Commit active Field membership and contributions.

Every *visible* condition runs, not only the ones the newest Shape declared. So a later Tagging can be refused because an earlier Tag's condition no longer holds — the contract is re-checked at each boundary. Conditions do not re-check themselves during gameplay; continuous, mutable checks belong in Records, not in conditions.

---

## 🧅 Conditions Layer, like every contribution

A condition is a Layer. When a Shape declares a condition with the same name as a Base's, the Shape's becomes the visible Overlay and the Base's becomes its Underlay — the very law that governs Actions and Records. Conditions are not special, and TOP keeps no separate deletion verb for them: to relax or replace a condition you **override** it, crunching a new Layer on top.

```python
class Apprentice(Wizard):

    @Pre
    @Underlay
    def Level_Over_Zero(agent, base):
        assert agent.mentor   # also needs a mentor
        return base()         # then defer to the Base's level gate
```

An `@Underlay` condition receives the Base's check and composes with it. Without `@Underlay`, the Shape's condition simply replaces the Base's.

---

## 🧭 The contract direction: **Forward-Post, Backward-Pre**

Conditions carry a direction, and it is the rule of substitutability (Liskov; Design by Contract):

> **Forward-Post, Backward-Pre.**
> As Tags specialize, Postconditions accumulate *forward* — a Shape promises at least as much as its Base, and more. Preconditions relax *backward* — a Shape may ask for less than its Base, never more.

This is what lets a Shape stand in safely wherever its Base is expected. A more specific Tag may open easier doors in, but it must not quietly revoke what the Base guaranteed.

**Relaxing a Precondition is ordinary.** A `Founder` joins a `Guild` without paying dues — the relaxed gate is just a Shape overriding it:

```python
class Founder(Guild):

    @Pre
    def Dues_Paid(agent):
        return True                      # founders skip the dues gate
```

`agent in Guild` still means "is a Guild member," and code iterating `Guild.Field` is unaffected, because the Guild's *promises* are untouched. Easier entry, same guarantees.

**Strengthening a Postcondition is ordinary too** — `@Underlay` and `and`:

```python
class Knight(Soldier):

    @Post
    @Underlay
    def Is_Equipped(agent, base):
        return base() and agent.oath    # keeps the Soldier promise, adds an oath
```

---

## 🪓 Relaxing a promise: the deliberate exception

Sometimes a specific case really is looser than the rule. A rule says "no Strength above 20"; Barbarians break it.

```python
class Character(Tag):

    @Post
    def Strength_Capped(agent):
        return agent.strength <= 20

class Barbarian(Character):

    @Post
    def Strength_Capped(agent):
        return agent.strength <= 24       # Barbarians widen the cap -- a plain crunch
```

*(Strictly a cap like this belongs in a Record, but it shows the shape of the feature.)* Here the Barbarian's Postcondition does **not** preserve the Base promise — it widens it. That is a *weakened* Postcondition, against Forward-Post.

TOP allows it, because forbidding it outright would break the easy refactoring that is the point of TOP. But it is never silent: **overriding a Base Postcondition without preserving its Underlay raises a contract diagnostic.** A relaxed promise is therefore always a visible, deliberate decision, never an accident. If the relaxation is intended, the diagnostic is your receipt; if it was a slip, it is your warning.

The whole discipline in three lines:

- **Strengthen a Post** → `@Post @Underlay`, `return base() and ...`. Silent and correct.
- **Relax a Pre** → override freely. Silent and correct.
- **Weaken a Post** → override without the Underlay. Allowed, but diagnosed.

---

## 🔎 Writing a check

A condition usually asks whether an Agent *has* something. The natural spelling is `assert`:

```python
class Wizard(Tag):
    @Post
    def Has_Spellbook(agent):
        assert agent.spellbook
```

`assert agent.spellbook` reads as a contract clause and fails with an `AssertionError` that names the line. But it asks **two questions at once**: it passes only if the contribution is *defined* **and** *truthy*. That is fine when a Record holds a truthy value whenever it is present (a spellbook object, a weapon). It is a trap when a Record can legitimately be falsy — a `spell_slots` of `0` is a real, defined value, yet `assert agent.spell_slots` would reject it as if it were missing.

So separate **having a contribution** from **its value**:

- **Is the contribution there at all?** (defined, with any value, even `0` or `False`):
  - `assert agent.spell_slots is not None`  ·  or `assert hasattr(agent, "spell_slots")` when `None` is itself a valid value
- **Does it have a particular value?**:
  - `assert agent.spell_slots > 0`  ·  `assert agent.spell_slots != 0`

`assert agent.rec` is the shorthand for "defined **and** truthy" — reach for it only when that is exactly what you mean. The same strictness that rejects a bare `return agent.spell_slots` is the discipline asking you, in `assert` too, to separate a contribution *being there* from a contribution *being falsy*.

> Contracts should be picky.
> - The Layer's Lawyer 

---

## ✅ Verifying an Agent: `if agent`

Preconditions are gates, checked once at entry. Postconditions are the standing promise, the active conditions, so TOP lets you re-check them on demand, with the most natural spelling in the language:

```python
if agent:         # True exactly when every visible Postcondition holds
    proceed(agent)

assert agent      # raise if any Postcondition fails
```

An Agent is **truthy if and only if its Postconditions hold**. `if` is the conditional and Post*conditions* **are** *conditions*. So `if agent` reads as "if the agent's conditions hold.", or "is the agent ok? in good condition?". 

> Python implementation notes: Truthiness on a plain object is vacuously True anyway, so this fills an empty seat rather than overriding a meaningful one. 

If an agent's conditions assert to a failure, it controls the assertion so the Agent returns a False boolean value.

When you need to know *which* promise broke, ask the `Contract` namespace, whose method names say exactly what they check:

```python
Contract.Postconditions(agent)   
    # the promises hold, or raise naming the one that failed
Contract.Preconditions(agent)    
    # the entry gates still hold, or raise
Contract.Conditions(agent)       
    # both, Pre then Post
```

For the whole picture rather than a single verdict, `Contract.Status(agent)` returns `{condition: holds?}` for every visible condition, Preconditions then Postconditions (it never raises; a broken condition maps to `False`), and `Contract.Display(agent)` renders that with Pre and Post in separate sections: a quick diagnostic while debugging:

```python
print(Contract.Display(charlie))
# Hero__Wizard contract:
#   Pre:
#     OK  Level_Over_Zero
#   Post:
#     XX  Has_Spellbook
```

The dict is the primitive; the display is one view built from it.

---

## 🚨 Failure

A condition that does not hold stops the Tagging at its boundary, with nothing committed:

| Failure | Meaning |
| --- | --- |
| **Precondition Failure** | A visible Precondition did not hold before Imprints. The Tag does not apply. |
| **Postcondition Failure** | A visible Postcondition did not hold after Imprints. The Tag does not apply. |

Because Tagging is atomic, a failed condition leaves the Agent exactly as it was before the call. Conditions are how TOP keeps its word at every boundary: the contract layer that lets you refactor by Tag without fear.

