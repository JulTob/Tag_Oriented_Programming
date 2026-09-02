# 🏷️ TOP Technical Specification 🔖

[Manifesto](MANIFESTO.md) → **Technical Specification** →
[TagKit Guide](../TagKit/GUIDE.md)

## 🏷️ Introduction

Tag-Oriented Programming (TOP) provides utility without changing identity.

By semantic increments, it provides new features without changing the essence of a target.

A hero is one character. Over a game she becomes a Human, a Wizard, a Sage, a Harper... and stays the same hero. TOP adds each meaning as a Tag; the object keeps its identity the whole way.

Traditional programming often asks, "what is this object?" TOP asks, "what is this object's use?", and lets the answer grow naturally.

You don't need object-oriented programming to use TOP. But if you know OOP, you will discover a complementary model that empowers your code with easy-to-use features and modular refactoring. Implementing TOP can make your codebases more structured, bringing forth Functional Programming and Contract Programming features without the headaches of refactoring your existing code. If you don't have a programming style yet, TOP provides an easy-to-follow model that has proven to be powerful and intuitive.

TOP governs the substrate over OOP with membership and contracts.

> **OOP owns inherent structure; TOP owns semantic context.**

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

```python
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
```

```txt
Charlie is a great hero.
Charlie is a human.
But Charlie is also a wizard.
```

An otherwise empty Tag is therefore meaningful. It can still define a
category and a Field of Agents.

The Target keeps its identity. Its semantic meaning expands through composition.

---



## ⚖️ TOP with OOP

Ordinary Object Oriented Programming mainly answers:

> What **is** this object?

TOP answers a different question:

> What does this object mean here?

TOP is external as a way of thinking: Tags are applied to an existing Target and compose visible semantic layers around it. OOP remains available for the Target's inherent structure, ordinary methods, and ordinary attributes.

TOP complements OOP. The same project may use both.


| OOP                     | TOP                            |
| ----------------------- | ------------------------------ |
| Inherent structure      | Semantic context               |
| Internal parts          | External layers                |
| Identity and invariants | Meaning and use                |
| Ordinary attributes     | Records contributed by context |
| Ordinary methods        | Actions contributed by context |
| Class inheritance       | Tag Geometry and Overlays      |


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
- composable before tangled
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


| Term        | Meaning                                                                                           |
| ----------- | ------------------------------------------------------------------------------------------------- |
| **Tag**     | A semantic category that can contribute meaning, behaviors, values, and constraints.              |
| **Target**  | A variable (value, dictionary, record, object...) before or during tagging.                       |
| **Tagging** | Applying a Tag to a Target, such as `Human(charlie)`, so the Target becomes an Agent of that Tag. |
| **Agent**   | A variable (value, dictionary, record, object...) when it belongs to a Tag.                       |
| **Field**   | The current committed population of Agents carrying a Tag.                                        |



| Term         | Meaning                                                                                       |
| ------------ | --------------------------------------------------------------------------------------------- |
| **Geometry** | The overall relationship structure established by Tags, Bases, and Shapes.                    |
| **Base**     | A broader Tag that a Shape specializes.                                                       |
| **Shape**    | A more specific Tag built over one or more Bases.                                             |
| **Form**     | The deterministic, duplicate-free, Base-first closure of one Tag, ending with the Tag itself. |
| **Layer**    | One Tag's semantic position in an Agent's composition.                                        |
| **Overlay**  | The currently visible result of all active Layers.                                            |
| **Underlay** | Explicit composition with the prior visible contribution sharing the same name.               |


TOP uses **Base** and **Shape** for specialization vocabulary. It does not
use OOP parent/child terminology, because those words describe a different
model.

A Tag may hold both roles: `Person` can be a Shape of `Being` and a Base of
`Wizard`.

The Geometry is the structure. A Form is one Tag's ordered route through
that Geometry.

```python
assert Wizard.Form() == (
        Being,
        Person,
        Wizard,
        )
```

A Tag has one Form at a time. An Agent may carry several active Forms; taken
together, they describe that Agent's current Geometry.

**Forming** follows that order downward, from general Bases toward the
specific Shape. **Deforming** moves upward in reverse dependency order,
removing specific Shapes before the Bases that support them.

---



# 🔩 Contributions

TOP distinguishes between contributions made on the Agent and contributions kept on the Tag Field.


Noun -> Tag (a category you are), adjective -> Record (a state you're in).

## 🪪 Agent-level contributions

- **Action**: behavior exposed on the Agent
- **Record**: state exposed on the Agent

A Tag usually corresponds to ***Nouns***, things you are (*ser*), while Records provide mutable states (*estar*), so they correspond to ***Adjectives***. Tags should not be used for circumstantial states, but to provide the Records that hold those states on the Agent.

## Imprinting and Ripping

- **Imprint**: application-time logic that shapes the Target when a Tag is applied
- **Rip**: extraction-time logic that shapes the Target when a Tag is rescinded.

Imprint shapes the Agent when active Field membership begins. Rip cleans up when active Field membership ends. They are duals: constructor/destructor, **enter**/**exit**. 

> ### **Tags are sticky.**
>
> Ripping does not revert the Agent back to a pre-Tagging state. Any Action, Record, or Condition applied to a Target remains after Ripping the Tag unless a Rip protocol explicitly changes it. Rogue Agents are dangerous... but useful!

- Imprint applies all missing Bases of a Tag by default.
- Ripping removes the Agent from the Tag's Field and, by default, from the Fields of Shapes that depend on that Tag.



## 📇 Field-level contributions

- **Report**: shared semantic data, stored on the Tag, across the Field.
- **Operation**: shared behavior on the Tag

Every public data value declared on a Tag is a Report. An implementation must
not invent application Reports: a Report name exists only when it is
declared, inherited through the Tag's Form, or contributed by Tagging the
Tag. Language runtime machinery is not a Report.

No Report name is reserved for display identity or documentation. A language
profile should use its language's native naming and documentation facilities
for those purposes.

In short:

- ◀️ Actions define behavior
- ⏺️ Records define state
- ⏸️ Imprints shape taggings
- ⏪️ Operations define shared behavior
- ⏹️ Reports define shared information

## This data/function structure avoids repetition, keeping structural behavior separate from individual object behavior.



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
> **Ripping** is the only explicit exception to monotonic membership: it removes the Agent from the Field. Ripping exists for utility, cleanup, or in-extremis domain resolution, as a safety feature. But it does not undo the fact that the Agent *is an instance* of the Tag.
> The Agent remains historically an instance of the Tag abstraction, even after leaving the active Field. Therefore, `isinstance` in Python should return true. Same for its equivalent in other languages.

```python
for agent in Mortal[:]:
    Observe( agent )

for agent in ~Mortal[:]:
    Review( agent )
```

Field iteration uses the **sound** population: Agents whose visible
Postconditions hold. Invert that view for the **defective** population —
members still in the Field whose Posts fail:

```python
~Mortal[:]
```

Sound and defective partition the Field. Their union is the U-set for that
Tag — every committed member, valid or not:

```python
agent in Mortal[:] or agent in ~Mortal[:]
Mortal[:] | ~Mortal[:]
```

```python
for wizard in Wizard[:]:
    play( wizard )

for broken in ~Wizard[:]:
    review( broken )
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

Preconditions inspect the **incoming materials**. Records still commit the
whole call or nothing. If a Precondition fails, missing Bases pulled in by
this call roll back with it. Tags committed by earlier calls survive
unchanged.

```text
Human(ari)
    Species would apply
    Human Precondition fails

ari in Human     == False
ari in Species   == False
```

An Imprint runs after that Tagging has applied. If it fails, the Tag stays.
The call raises an Imprinting Error: the machine failed while writing.

A Postcondition inspects the **finished product**. If it fails, the Tag stays
as a defective result. The call raises a Postcondition Error. You do not
unmake the Tag any more than a factory unmakes an unsafe toy; the error
protocol lets the caller throw it away.

For complex Taggings, incremental calls provide better control than one large Shape Tag, but TOP provides abstraction for hiding those complexities.

---



# Composition

Composition is order-sensitive for independent Tags. The last successful application of a Record or Action becomes the visible Overlay for that name. This is a core principle: TOP supports incremental design by letting later semantic layers refine, replace, or extend earlier ones. If the later Tag should preserve the previous behavior, it should use an Underlay. If a caller needs a specific historical layer, it should use Agent-bound Tag access.

---



# 🔩 Contributions

TOP distinguishes Agent-level and Tag-level contributions.


| Contribution      | Kind      | Scope           | Meaning                                    |
| ----------------- | --------- | --------------- | ------------------------------------------ |
| **Action**        | Callable  | Agent           | Behavior visible on an Agent.              |
| **Record**        | Data      | Agent           | State visible on an Agent.                 |
| **Imprint**       | Callable  | Tag application | Work performed automatically after the Tag has applied. |
| **Operation**     | Callable  | Tag             | Shared behavior belonging to the Tag.      |
| **Report**        | Data      | Tag             | Shared semantic data belonging to the Tag. |
| **Precondition**  | Predicate | Tag application | A guard evaluated before the Tag applies. |
| **Postcondition** | Predicate | Tag application | A guard evaluated after Imprints. |


An Agent acts through Actions and carries state through Records. It may
consult Reports and invoke Operations only through explicit Tag context.

Actions and Records actualize the Agent. They may replace ordinary OOP methods
and attributes as well as earlier TOP contributions.

Temporary state lives in Records:

```python
agent.asleep = True
agent.asleep = False
```

The `asleep` Record may remain part of the Agent's state while its value changes. Tag membership remains unchanged through that transition.

### Member coordinates

Every public member contribution has an overlay coordinate:

```text
(scope, name)
```

TOP defines two public member scopes:

| Scope | Contributions | Semantic receiver |
| --- | --- | --- |
| **Agent** | Action, Record | one Agent |
| **Tag** | Operation, Report | one Tag, possibly acting over its Field |

The semantic receiver determines the scope. The place where a contribution is
declared does not override these rules.

- An Action is Agent-scoped even when its single implementation is declared
  centrally inside a Tag.
- A Record is Agent-scoped because each Agent carries its own value.
- An Operation is Tag-scoped because the Tag is its receiver.
- A Report is Tag-scoped because the Tag owns the shared value.

Pinning is an explicit receiver change. When a Tag is applied to another Tag,
an Action may be adapted into an Operation and a Record may be materialized
as a Report. The resulting contributions occupy Tag scope because the Pinned
Tag is their receiver. This is an explicit Pin rule, not an implicit
projection onto every Agent.

### One slot per scope and name

Within one scope, a name identifies one public member slot. The visible
Overlay occupies that slot with one kind at a time.

- Same-kind Layers at the same coordinate follow the existing Overlay and
  Underlay rules.
- Independent Tags cannot place an Action and a Record at the same Agent
  coordinate, or an Operation and a Report at the same Tag coordinate.
  Those collisions fail atomically before membership, Imprints, Records,
  or other visible state commit.
- Within one Form, a later Layer may Overlay the slot with the other
  Agent kind. A Shape Record may fix a Base Action as data. A Shape
  Action may compute from a Base Record. The prior kind remains in the
  captured Base view; current access shows one kind.
- `@Underlay` remains same-kind. Changing kind is Overlay replacement,
  not mixed-kind extension.

Across scopes, equal names do not collide. They do not replace one another,
form an Underlay together, or change one another's history.

Kind alone is not the coordinate. Form Overlay may change which kind
currently occupies a slot; access never consults two live kinds for one
spelling in the same scope.

### Contract phases

Preconditions and Postconditions do not occupy Agent or Tag member slots.
They belong to distinct Tagging phases:

```text
(precondition, name)
(postcondition, name)
```

A Precondition and a Postcondition may share a name without colliding. Each
composes only with conditions in its own phase.

Preconditions are **incoming-material gates** for the layers applied in the
current call. Postconditions are **finished-product promises** on the Agent
— re-checked at each Tagging boundary and exposed for inspection on the
Agent in conforming profiles.

Imprints and Rip protocols remain ordered lifecycle protocols. They are not
ordinary public members and are not folded into the member coordinates above.

### Access follows scope

| Access | Scope consulted |
| --- | --- |
| `agent.name` | Agent |
| `Tag.name` | Tag |
| Agent-bound Tag view | captured Agent context, then captured Tag context |

Flat Agent access must not expose a Report or Operation. Direct Tag access
must not silently bind an Action to an unspecified Agent.

An Agent-bound Tag view is an explicit contextual view over both scopes. If
both captured scopes contain the same name, Agent scope is selected first.
The Tag-scoped contribution remains available through direct Tag access.
This access precedence is only a spelling rule: the two contributions do not
replace or Underlay one another.

### Central Actions and live authority

Declaring an Action on a Tag provides one central implementation bound to
each relevant Agent:

```python
class Agency( Tag ):

    @Operation
    def dispatch(
            agency,
            sender,
            message,
            ):
        if sender not in agency:
            raise PermissionError(
                    "Agency membership is inactive"
                    )

        return network.broadcast(
                sender,
                message,
                )

    @Action
    def broadcast(
            agent,
            message,
            ):
        return Agency.dispatch(
                agent,
                message,
                )
```

The public capability remains an Agent Action:

```python
Agency( agent )

send = agent.broadcast

send( message )
```

Ripping remains sticky. It does not erase the Action:

```python
Agency.Rip( agent )

send( message )  # PermissionError
```

The call fails because the guarded Operation checks active Field membership
at invocation time. Checking only when `send` is captured would allow a stale
handle to bypass revocation.

This rule does not make TOP a concurrency or transaction-security system.
Long-running or asynchronous work may need to check authority again before
an irreversible commit.

### No implicit Operation projection

An Operation is not automatically exposed as `agent.operation()`. Code that
wants an Agent-facing capability declares an Action explicitly. Such
projection would invent an Agent receiver for Tag behavior, permit
unannounced shadowing of inherent methods, complicate same-name resolution,
and make revocation dependent on hidden fallback rules.

---



# 💠 Layers and Overlays

Within each scope, the latest successfully applied Layer is the visible Overlay
for a contribution name at coordinate `(scope, name)`. This applies to Actions,
Records, Reports, Operations, Preconditions, and Postconditions.

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


| Tag - you became this                              | Record - this can change                                       |
| -------------------------------------------------- | -------------------------------------------------------------- |
| Human, Elf - species                               | asleep, poisoned - conditions                                  |
| Wizard, Paladin - class                            | hit points, gold - resources                                   |
| Sage, Soldier - background                         | location, morals                                               |
| Harpers - affiliation                              | friends? Enemies? Affinity? - current status                   |
| Spellcaster - learned capability                   | spell slots left                                               |
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



## Ripping Tags

Tags can be seen like a pass, a sticker, or a badge. Having one is nice, but they should have a function: a security pass should identify the user, a police badge needs the District and Agent's number, and a logistic's sticker needs a destination. Having a Tag without those Records makes for a dangerous state of uncertainty for the contract.

Ripping a Tag is an exceptional and violent act of Field expulsion. Like in 80s copaganda movies, to "return your badge" means the Agent is no longer an active member of the organization. But it creates a Rogue Agent: an element with the Actions and Records it had before Ripping the Tag, but without active access to the Tag's Field resources, Operations, or Reports. When an expulsion protocol is required ("Give me your badge and weapons. You can no longer go into the evidence room!"), the `@Rip` tag is used. A Rogue Agent can no longer be accessed by Field protocols.

```py
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
```

Imprint shapes the Agent when active Field membership begins. Rip cleans up when active Field membership ends. They are duals: constructor and destructor, **enter**/**exit**.

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

An Imprint writes into a Tag after that Tag has applied. A Tag may have zero
or more Imprints. Within one Tag, they run in declaration order. They are
the "write in a Tag" step: membership, Overlay, and Records are already
committed. Postconditions inspect that finished Tag after the Imprints.

An Imprint may apply further independent Tags to the same Target. Those
Taggings are ordinary later calls. A nested Precondition rolls back only
the nested Tag. The outer Tag stays. Use a Base when the extra meaning is
required and more general. Use an Imprint Tagging when the meaning is
optional, conditional, or should overlay the current Tag.

Preconditions, Record materializers, and Postconditions do not apply Tags.

Rip of the shape or its bases is forbidden while an Imprint of the shape is running.

Tagging may also establish Preconditions and Postconditions. Conditions are
TOP's tag-time quality control: they raise the alarms when a requisite is not met or when the output is defective, but
they do not wrap ordinary gameplay Action calls.

For one Tag application, TOP performs this logical sequence:

1. Construct the candidate Overlay.
2. Evaluate every Precondition visible in that candidate Overlay.
3. Materialize the new Tag's Records.
4. Commit the Tag's active Field membership and TOP-managed
   contributions.
5. Run the new Tag's Imprints. If an Imprint fails, the Tag stays and the
   call raises an Imprinting Error.
6. Evaluate every Postcondition visible in that Overlay. If a
   Postcondition fails, the Tag stays as a defective result and the call
   raises a Postcondition Error.

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

An Agent Action and an Agent Record occupy one name with one meaning. A
language profile may offer both a value spelling and a call spelling for that
same contribution. `agent.weapon` and `agent.weapon()` are not two slots.
They are two ways to read one Overlay. Calling a Record reads the stored
value; it does not run the materializer again. Reading a nullary Action
without `()` evaluates it. An Action that needs inputs remains a handle
until it is called, so capturing `send = agent.broadcast` stays valid.

Independent Tags still cannot give one Agent name two meanings, one as an
Action and one as a Record. A Shape may Overlay a Base contribution with the
other kind because that is still one name and one visible meaning.

### Polymorphic behaviour

A Shape inside a Form may turn a Base Action into stored data, or a Base
Record into a computed Action. With Uniform Access, the client asks what
`strike` is **for**, not whether it is stored or calculated:

```python
class Combatant(Tag):

    def strike(
            agent,
            ) -> int:
        return 1


class Fire(Combatant):

    @Record
    def strike(
            agent,
            ) -> int:
        return 4


Fire(ember)

assert ember.strike == 4
assert ember.strike() == 4
assert Combatant[ember].strike == 1
assert Combatant[ember].strike() == 1
```

The current Overlay is the Record. The Base view still holds the captured
Action. Both spellings work on each view. This is polymorphic behaviour in
TOP's sense: one name, one meaning per view, two readable spellings — not two
independent Tags sharing one Agent name.

### 🪪 Agent-bound Tag access

```python
agent.Paladin.Attack()
agent.Paladin.HONOR_CODE
```

This accesses the Overlay snapshot immediately after `Paladin` applied to
that Agent. It includes captured Agent-scoped contributions from that point,
then captured Tag-scoped contributions from the same moment. If both scopes
contain the same name, Agent scope is selected first. The Tag-scoped
contribution remains available through direct Tag access.

It does not change merely because a later Tag actualizes the same name on the
Agent.

Agent-bound Tag access requires active Field membership in the requested Tag.
Otherwise it fails with a Tag-resolution error. A Rogue Agent may keep sticky
Actions and Records, but it does not keep Agent-bound Tag access after Rip.

### 🪪 Direct Tag access

```python
Paladin.Field
Paladin.Report
Paladin.Operation()
```

This accesses Tag-scoped meaning on the Tag itself — not flat Agent access.
Operations and Reports are never projected onto `agent.name` without an
explicit Action adapter. A target-scoped Operation needs a Tag receiver;
an Agent-scoped Action needs an Agent receiver, which Agent-bound Tag access
provides when both scopes must be read together.

An implementation may choose a different syntactic form where direct dot
access collides with ordinary Agent attributes. It must preserve the scope
distinctions above.

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


| Failure                       | Meaning                                                                                         |
| ----------------------------- | ----------------------------------------------------------------------------------------------- |
| **Tag Resolution Failure**    | A required Underlay, Tag view, or contribution cannot be resolved.                              |
| **Tag Precondition Failure**  | A candidate Overlay's precondition does not hold.                                               |
| **Imprint Failure**           | An Imprint failed after the Tag had already applied.                                            |
| **Tag Postcondition Failure** | A Postcondition found a defective finished product. The Tag stays. |
| **Tag Composition Failure**   | Contributions cannot form the required Overlay.                                                 |
| **Tag Contract Failure**      | A condition returns a non-boolean (truthy/falsy) value instead of a strict True / False / None. |


Failure of a Precondition or Record stops the current Tagging. Dependencies
that were not applied earlier are not committed. An Imprint failure is a
machine error and does not un-apply the Tag. A Postcondition failure is a
defective result and does not un-apply the Tag either. Modular application
keeps earlier successful Taggings intact.

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



## 🧧 Purpose of This Specification

This specification has two jobs:

- explain the programming model
- specify the observable behavior a TOP implementation should provide

This specification explains the model first and the required semantics
second.

## Examples show intended meaning.
They do not freeze one permanent spelling.



## 🧯 TOP Commitments

A conforming TOP implementation must preserve the observable semantics
defined by this specification.

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

- `@Pre` — a Precondition. It guards *input*: what must be true *before* a Tag may apply.
- `@Post` — a Postcondition. It guards the *output*: what must be true *after* a Tag has applied.

Think of Tagging as a factory line. A Precondition inspects the **incoming
materials** — may this work enter the line at all? A Postcondition inspects
the **finished product** — did this Tagging produce something sound? The gate
and the quality check are different moments; TOP does not collapse them.

A condition is a function with the Agent as its first input. As with every TOP contribution, the first parameter is the Agent by discipline; its name is yours to choose, never a reserved word.

```python
class Wizard(Tag):

    @Pre
    def Level_Over_Zero(agent):
        return agent.level > 0          # you need a level to become a Wizard

    @Record
    def spellbook(agent):
        return "Tome"

    @Post
    def Has_Spellbook(agent):
        assert agent.spellbook          # a Wizard always ends up with a spellbook
```

A condition is **strictly boolean**: it holds on `True` (or on absent `return` for an assert-style body that fell through), fails on `False`, and is *rejected* on anything else. **True always means the clause holds.** TOP does not coerce truthy/falsy values, because they are not booleans, and prone to logic errors. A Record of `0` slots left is a real value, not a failure. So write the comparison you mean, `return agent.spell_slots > 0`, never the raw value `return agent.spell_slots` (which raises a contract error telling you to be explicit). 

The absence of a return statement defaults to True: a condition is a restriction, so saying nothing also permits. Legal until written into law.

---



## 🕰️ When conditions run

Conditions fire at tagging boundaries, never continuously during play. For one Tagging, TOP performs:

1. Build the candidate Overlay.
2. Evaluate the **Preconditions contributed by each layer applied in this
   call** — Bases pulled in by the Form walk, then the requested Tag. If one
   fails → *Precondition Failure*; nothing commits for that layer.
3. Establish Records.
4. Commit active Field membership and contributions.
5. Run the Imprints. If one fails → *Imprint Failure*; the Tag stays.
6. Evaluate every visible **Postcondition**. If one fails → *Postcondition
   Failure*; the Tag stays as a defective result.

Preconditions are **incoming-material gates**: they run at entry for the
layers being applied now, not as standing re-checks on every later Tagging.
Postconditions are **finished-product promises**: every visible Post is
re-checked at each Tagging boundary, so a later call can raise because an
earlier promise no longer holds — without unmaking the earlier Tag.
Conditions do not re-check themselves during gameplay; continuous, mutable
checks belong in Records, not in conditions.

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
>
> - The Layer's Lawyer

---



## ✅ Verifying an Agent: `if agent`

Preconditions are gates, checked once at entry for the layers applied in
that call. Postconditions are the standing promise, so TOP lets you re-check
them on the Agent itself — the same address as Actions and Records. The basic
obvious spellings are Uniform Access:

```python
if agent.Has_Spellbook:        # holds?
    proceed(agent)

if not agent.Has_Spellbook():  # same check, call spelling
    restore_spellbook(agent)
```

**True always means the clause holds.** Bare and `()` are two ways to read
one Condition, not two meanings.

Whole-Agent truthiness still runs every visible Post:

```python
if agent:                     # True exactly when every visible Post holds
    proceed(agent)

assert agent                  # raise if any Postcondition fails
```

An Agent is **truthy if and only if its Postconditions hold**. `if` is the
conditional and Post*conditions* **are** *conditions*. So `if agent` reads as
"if the agent's conditions hold.", or "is the agent ok? in good condition?".

> Python implementation notes: Truthiness on a plain object is vacuously True anyway, so this fills an empty seat rather than overriding a meaningful one.

If an agent's conditions assert to a failure, it controls the assertion so the
Agent returns a False boolean value.

Named failures carry the clause on the exception. Catch the named type, or
branch on `.condition`. Soft recovery uses the Agent condition itself — Python
cannot use `except agent.Has_Spellbook` because `except` needs an exception
*type*, not a live check:

```python
try:
    Wizard(agent)
except TagPostconditionError.Has_Spellbook:
    repair(agent)

# Same checks after a defective Tagging, or any time later:
if not agent.Has_Spellbook:
    repair(agent)
```

Print the contract without importing `Contract`:

```python
print(f"{agent:Contract}")
print(f"{agent:Display}")
print(f"{agent:Status}")
```

`:Contract` and `:Display` render the Pre/Post mini menu. `:Status` is the
flat OK/XX list. `Contract.Status` / `Contract.Display` remain for tools that
want the dict or an explicit call.

When you need to sweep every visible condition at once and raise, ask the
`Contract` diagnostic namespace:

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

A Precondition that does not hold stops the Tagging at entry, with nothing
committed. A Postcondition that does not hold raises after the Tag has
applied; the result is defective, and the Tag stays. A defective product may then be ammended, discarded, or ignored. 


| Failure                   | Meaning                                                                      |
| ------------------------- | ---------------------------------------------------------------------------- |
| **Precondition Failure**  | A visible Precondition did not hold before the Tag applied. The Tag does not apply. |
| **Postcondition Failure** | A visible Postcondition did not hold after Imprints. The Tag stays as a defective result. |


Preconditions keep the gate on incoming materials. Postconditions name a
defective finished product so the caller can throw it away. That is how TOP
keeps its word at every boundary without pretending a finished Tag was never
made.