# 🏷️ Tag-Oriented Programming: The Specification 🔖

> **OOP owns inherent structure; TOP owns semantic context.**

Tag-Oriented Programming (TOP) provides utility without changing identity.

A hero is one character. Over a game she becomes a Human, a Wizard, a Sage,
a Harper, and stays the same hero. TOP adds each meaning as a **Tag**; the
object keeps its identity the whole way. Traditional programming asks
*"what is this object?"* TOP asks *"what is this object for, here?"*, and
lets the answer grow.

TOP was born from tabletop character creation: species, class, background
and feats are independent choices, and the character sheet is what they
compose. A spell list is written by all of them. TOP gives that idea a
precise algebra: one identity, many layers, clear rules for how the layers
meet.

This document is the source of truth. It is written in **rings**, from the
kernel outward. Everything in an inner ring holds without the outer rings.
A conforming implementation must preserve the observable semantics of every
ring it claims. Examples are in Python; the laws are language-neutral.

| Ring | Contents |
| --- | --- |
| **0 · Kernel** | identity, membership, Geometry, the tagging sequence, Rip |
| **1 · Contributions** | Actions, Records, Operations, Reports, Overlay and Underlay, publication, access |
| **2 · Contracts** | Preconditions, Imprints, Postconditions, defective Agents |
| **3 · Lifecycle** | teardown protocols, Scope, deletion |
| **4 · Edges** | what TOP does not promise, and why |

The last sections give the failure model, the conformance obligations, and
where TOP stands among paradigms.

---

# Ring 0 · The Kernel

## 0.1 Identity

A **Target** is any object a program already has. Tagging a Target never
replaces it: before and after, it is the same object. Precisely:

- object identity is preserved (`tagged is original`, same `id`, same hash,
  same equality);
- every attribute and method the Target had keeps working the way it did,
  unless a Tag deliberately contributes a member of that name;
- the Target's own special methods (`__contains__`, `__len__`, `__bool__`,
  operators, `__getattr__`) keep working, with one deliberate exception:
  `bool(agent)` gains contract meaning once a Postcondition is visible
  (§2.5);
- the name of the object's type is unchanged.

What TOP does **not** promise is nominal type identity: a Python
implementation may swap the object's class for a runtime subclass of it.
`isinstance(agent, Host)` stays true; `type(agent) is Host` may not. See
Ring 4.

## 0.2 Vocabulary

| Term | Meaning |
| --- | --- |
| **Tag** | A semantic category that can contribute meaning, behaviour, values and constraints. A noun: something you *are* (*ser*). |
| **Target** | An object before or during tagging. |
| **Tagging** | Applying a Tag to a Target: `Human(charlie)`. |
| **Agent** | A Target that belongs to at least one Tag. |
| **Field** | The population of Agents currently carrying a Tag. |
| **Base** | A broader Tag that a Shape specializes. |
| **Shape** | A more specific Tag built over one or more Bases. |
| **Form** | The ordered, duplicate-free, Base-first closure of one Tag, ending with the Tag itself. |
| **Geometry** | The whole relationship structure of Tags, Bases and Shapes. |
| **Layer** | One Tag's position in an Agent's composition. |
| **Overlay** | The currently visible result of all active Layers. |
| **Underlay** | The prior visible contribution of a name, captured for a later Layer to extend. |

TOP uses **Base** and **Shape**, never *parent* and *child*: the words
describe a different model. A Tag may be both: `Person` is a Shape of
`Being` and a Base of `Wizard`.

## 0.3 Membership

The primary result of a Tagging is **membership**. An otherwise empty Tag
is complete: it still defines a category and a Field.

```python
class Wizard(Tag):
    pass

Wizard(charlie)

assert charlie in Wizard            # active membership
for wizard in Wizard:               # the Field (its sound members, §2.5)
    Observe(wizard)
```

Membership is **closed upward** through Bases: an Agent of a Shape is an
Agent of every Base in the Shape's Form, and appears in each of those
Fields.

```python
class Mortal(Tag): pass
class Human(Mortal): pass

Human(charlie)
assert charlie in Human
assert charlie in Mortal
```

Membership is **monotonic by design**. Only Rip (§0.7) ends it, and Rip
does not erase history: an Agent that has ever been a member of a Tag
remains *an instance* of that Tag. In Python, `isinstance(agent, Tag)` is
that has-been check and stays true after Rip. `agent in Tag` is the is-now
check.

A Field **never keeps an Agent alive**. When an Agent ceases to exist it
vanishes from every Field. Fields are indexed by identity: two equal but
distinct Agents are two members.

## 0.4 Geometry

Bases and Shapes form a directed graph, the Geometry. Each Tag has one
**Form**: its Bases, deepest first, in declaration order, each once, then
the Tag.

```python
class Spellcaster(Tag): pass
class Duelist(Tag): pass

class Arcane_Duelist(Spellcaster, Duelist):
    pass

assert Form(Arcane_Duelist) == (Spellcaster, Duelist, Arcane_Duelist)
```

A Base reachable through several paths appears once. **Forming** follows
the Form downward, general to specific. **Deforming** (Rip) goes the other
way: a Shape leaves before the Bases that support it.

## 0.5 Applying a Tag

The canonical act is:

```python
Tag(target, **inputs)
```

It applies every Tag in the Form that is not yet active, Bases first, then
returns the same Target. Keyword **inputs** are handed by name to the
Preconditions and Imprints run during that call (§2.2, §2.3).

```python
MI6(bond, code="007")      # every Imprint that declares `code` receives it
```

**Reapplying an active Tag does nothing.** It does not duplicate
membership, does not rerun Imprints, does not reset Records. Resetting is a
deliberate act: Rip, then apply again.

## 0.6 The tagging sequence

Think of a factory line. Once, for the whole call:

1. **Gate.** The Preconditions visible in the Form this call will produce
   inspect the incoming Agent and the inputs. A Shape's Precondition
   overrides its Base's, so a Shape can relax the gate. A failed gate stops
   the call before anything changes.

Then for each Tag in the Form, in order:

2. **Parts.** That Tag's Records are built, each allowed to read the value
   already stored under its name.
3. **Commit.** The Agent enters the Tag's Field; the Overlay and the
   Agent-bound view are set.
4. **Write.** That Tag's Imprints run, in declaration order.

Then, once for the whole call:

5. **Quality check.** Every visible Postcondition inspects the finished
   Agent.

The **call boundary** decides what a failure means:

- A failure in steps 1 or 2, for any Tag in the Form, **rolls the whole
  call back**. The Agent is exactly as it was at the call, including Bases
  pulled in by this call. Tags committed by earlier calls are untouched.
  Nothing partial is ever published.
- A failure in steps 4 or 5 **raises, but the Tags stay**. The product left
  the line. A defective product is not melted back to materials: it is
  flagged, repaired, or Ripped (§2.5).

```text
Citadel(ari)                      Form: Territory, Citadel
    gate       Has_Charter FAILS
→ TagPreconditionError; ari in Territory == False, ari in Citadel == False

Broken_Wizard(ari)                Form: Person, Broken_Wizard
    gate       ok
    Person     parts, commit, write
    Wizard     parts, commit, write
    check      Has_Spellbook FAILS
→ TagPostconditionError; ari in Person and ari in Wizard; bool(ari) == False
```

Tagging is otherwise side-effect free: TOP-managed state is restored on
rollback. An Imprint's in-place mutation of a pre-existing mutable value
(`events.append(...)`) is outside what TOP can undo; keep such effects for
step 4, where they are never rolled back, or hold them in Records.

## 0.7 Rip

Tags can be seen like a pass, a sticker, a badge. Ripping one is an
exceptional, violent act of Field expulsion: *"Give me your badge and
weapon. You can no longer go into the evidence room."*

```python
del MI6[bond]
assert bond not in MI6
assert isinstance(bond, MI6)      # once an agent, always an agent
```

Rip is the only exit from a Field, and it obeys three laws:

- **Contributions are sticky.** Actions and Records stay on the Agent after
  Rip unless a `@Rip` protocol (§3.1) changes them. The result is a **Rogue
  Agent**: it has what it learned, but no active access to the Tag's Field,
  Operations, Reports or Agent-bound view. Rogue Agents are dangerous… but
  useful.
- **Rip is refused while a Shape needs the Base.** `del Beast[wolf]` fails
  while `Wolf` is active. Deform the Shape first. Rip never cascades: TOP
  does not run other Tags' protocols behind your back.
- **Reapplying a Ripped Tag is a fresh Tagging.** Imprints run again;
  Records are rebuilt.

## 0.8 Spellings

TOP borrows the language's own syntax for every Tag-level act and leaves
the Tag's dotted namespace, `Wizard.something`, to the program. A Report
called `Field`, `Form` or `Rip` must be possible. Structure without
stepping on the programmer's choices: TOP should feel like part of the
language, not a library's naming.

| Act | Python spelling |
| --- | --- |
| apply | `Wizard(agent, **inputs)` |
| active member? | `agent in Wizard` |
| ever a member? | `isinstance(agent, Wizard)` |
| the sound population | `for w in Wizard`, `len(Wizard)` |
| the defective population | `for w in ~Wizard` |
| everyone in the Field | `Wizard[:]` |
| the Agent-bound view | `Wizard[agent]` |
| leave the Field (Rip) | `del Wizard[agent]` |
| the Form | `Form(Wizard)` |

Queries that need a name are functions (`Form`, `Tags`, `Has`, `Apply`,
`Outline`, `Contract`, `Scope`), never members of the Tag or of the Agent.
Another language profile chooses its own native spellings; the acts and
their distinctions are what must survive.

---

# Ring 1 · Contributions

## 1.1 Two scopes

Every contribution has a **receiver**, and the receiver decides its scope.

| Scope | Contributions | Receiver | Meaning |
| --- | --- | --- | --- |
| **Agent** | Action, Record | one Agent | what *this* Agent does and holds |
| **Tag** | Operation, Report | the Tag | what the whole Field shares |

Where a contribution is *declared* does not change its scope. An Action
written inside a Tag class is still an Agent contribution: the Tag stores
it once, every Agent is its receiver.

In Ada's terms, the Tag is the package specification and the Agent is the
body. The specification declares what is shared; the body is what acts.

A name identifies **one slot per scope**: `(scope, name)`. In Agent scope
that slot holds an Action or a Record, never both at once:

- **Independent** Tags (neither in the other's Form) cannot place an Action
  and a Record at the same Agent name. The Tagging fails at step 1, atomic.
- Within one Form, a Shape may **change the kind** of a Base slot: fix a
  Base Action as a Record, or compute a Base Record with an Action. The
  Base's view (§1.7) keeps the prior kind.
- Across scopes, equal names do not collide. `Fire.colour` (Tag) and
  `ember.colour` (Agent) are two slots with two histories.

## 1.2 Actions

An Action is Agent behaviour. Declared as a plain method on the Tag or with
`@Action`; the first parameter is the Agent, by discipline, under any name.

```python
class Person(Tag):
    def Attack(agent) -> str:
        return "Attack!"
```

The latest applied Layer is the visible Overlay for a name. An Action
declared without an Underlay **replaces**; with `@Underlay` it **extends**:

```python
class Elf(Person):
    @Action
    @Underlay
    def Attack(agent, underlay) -> str:
        return "With elven grace " + underlay()
```

The Underlay is **captured when the Tag applies**: it is the complete Action
visible immediately before this Layer. It forms a backward chain of
callables and never resolves again later. Calling it with no arguments
forwards the current call's arguments; calling it with arguments passes
those instead. If no prior Action exists, a Tag asking for an Underlay
cannot apply (Tag Resolution Failure).

An Action that calls another Action **through the Agent** uses the current
Overlay at play time:

```python
class Combatant(Tag):
    def Combat(agent) -> str:
        return agent.Attack()          # whatever Attack is visible now
```

Replacing an Action of an **independent** Tag without an Underlay is
allowed but **diagnosed** (a warning): something was overwritten that
another meaning still relies on.

The same rules bind special methods: a Tag may contribute `__add__`,
`__eq__` and the like, and they actualize the Agent.

## 1.3 Records

A Record is Agent state contributed by a Tag. A Tag is something you
*are*; a Record is something you are *currently* (*estar*): an adjective.

| Tag, you became this | Record, this can change |
| --- | --- |
| Human, Elf: species | asleep, poisoned: conditions |
| Wizard, Paladin: class | hit points, gold: resources |
| Sage, Soldier: background | location, morals |
| Harpers: affiliation | affinity, standing: current status |
| Spellcaster: learned capability | spell slots left |
| Access Pass: recognized by the system | clearance: the specific level |

A Record is declared as a **builder**. The builder runs at step 2 of the
tagging sequence; its value is stored on the Agent, fresh for each Agent:

```python
class Inventory(Tag):
    @Record
    def items(agent) -> list[str]:
        return []
```

A builder may declare a **second parameter**: it receives the value already
stored under that name, or `None` when there is none. This is how
independent Tags **pile up** on one Record, in application order, and how a
Tag extends an ordinary attribute the host already had:

```python
class Elf(Species):
    @Record
    def spells(agent, stored) -> list[str]:
        return (stored or []) + ["Light"]

class Wizard(Class):
    @Record
    def spells(agent, stored) -> list[str]:
        return (stored or []) + ["Magic Missile", "Shield"]

class Sage(Tag):
    @Record
    def spells(agent, stored) -> list[str]:
        return (stored or []) + ["Identify"]

Elf(ari); Wizard(ari); Sage(ari)
assert ari.spells == ["Light", "Magic Missile", "Shield", "Identify"]
```

The author writes the merge. `stored + new`, `max(stored, new)`,
`stored | new`: whatever the domain means. A builder without the second
parameter **replaces**; replacing the Record of an independent Tag is
diagnosed, like an Action.

After tagging, a Record is an ordinary attribute: read it, assign it,
delete it with the language's own `del agent.record`. Deleting is allowed
but rarely good design; frequent deletion means unclear state ownership.

Mutable Record values must be fresh per Agent unless sharing is the
explicit intent. Shared values belong in a Report.

## 1.4 Reports and Operations

A **Report** is shared data belonging to a Tag; an **Operation** is shared
behaviour whose first input is the Tag.

```python
class Community(Tag):
    colour = Report("green")

    @Operation
    def Greet(tag, name) -> str:
        return f"{tag.__name__}:{name}"

Community.colour            # "green"
Community.Greet("Ari")      # "Community:Ari"
```

Reports and Operations are **not visible on the Agent**. `ari.colour` does
not exist after `Community(ari)`, and neither does `ari.Greet`. Projecting
Tag members onto Agents would invent an Agent receiver for Tag behaviour,
silently shadow host methods, and confuse the two histories. The Agent
reaches them through its Tag-bound view (§1.7) or through publication.

A shared counter is a Report; the Imprint that changes it acts on the Tag:

```python
class Secret_Agent(Tag):
    active = Report(0)

    @Imprint
    def Activate(agent):
        Secret_Agent.active += 1
```

## 1.5 Publication

Scope says *who owns* a member. **Publication** says *who may reach it from
outside*. The defaults follow the Agency/Agent picture: what the Agent does
is public; what the Agency keeps is internal.

| Contribution | Default | Mark |
| --- | --- | --- |
| Action, Record | **external** | `@Secret` makes it internal |
| Operation, Report | **internal** | `Public(...)` publishes it on the Agent |

**Composition** is the door. Inside it, everything of the relevant scopes
resolves; outside it, only external members and the control plane (apply,
Rip, membership, Fields, views of carried meaning). *Inside composition*
means: while an Action, Imprint, Record builder, condition, or Rip protocol
bound to **this Agent** is running.

`@Secret` on an Action or Record:

```python
class Fire(Tag):
    @Secret
    @Record
    def ember_heat(agent) -> int:
        return 3

    @Secret
    @Action
    def ignite(agent) -> int:
        return agent.ember_heat * 2

    @Action
    def strike(agent) -> int:
        return agent.ignite() + 1     # inside composition: resolves

ember.strike()        # 7
ember.ignite()        # AttributeError: secret member
ember.ember_heat      # AttributeError: secret member
```

A secret handle captured inside and called outside **fails closed**. A
secret still occupies its `(Agent, name)` slot; it is not a third kind.

`Public(...)` on a Report or Operation constructs the publishing member for
you, so field economy (one value, one body on the Tag) needs no hand-written
adapter:

- A **published Report** appears on the Agent as a **read-only name** that
  reads the Tag's current value. One copy lives on the Tag; the Agent does
  not carry it.
- A **published Operation** appears on the Agent as an **Action** that
  forwards to the Operation with **the Agent as its second input**, after
  the Tag.

```python
class Agency(Tag):
    colour = Public(Report("navy"))

    @Public
    @Operation
    def dispatch(agency, sender, message):
        if sender not in agency:
            raise PermissionError("inactive")
        return network.broadcast(sender, message)

Agency(agent)
agent.colour                     # "navy", read-only
agent.dispatch(message)          # Agency.dispatch(Agency, agent, message)
```

The published Action is a normal Action: it overlays and underlays at
`(Agent, name)` and is sticky after Rip. That is why the guarded Operation
checks membership **at invocation**: a stale `send = agent.dispatch`
captured before Rip fails closed after it. TOP is not a security system; a
long-running task may need to re-check authority before an irreversible
step.

Illegal marks are rejected at declaration: `@Secret` on Tag members,
`Public` on Agent members, or both on one member.

## 1.6 Delete

`@Delete` on a name removes the visible contribution, or the host member,
of that name. It frees the slot: the next contribution may occupy it with
either Agent kind, and an Underlay-seeking contribution finds nothing.

```python
class Pacifist(Tag):
    @Delete
    def Attack(agent): ...
```

## 1.7 Access model

Three forms, three meanings. An implementation may spell them differently
but must keep them distinct.

**Current Agent access**: the visible Overlay now.

```python
agent.Attack()
agent.weapon
```

**Agent-bound Tag access**: the Overlay **as it was immediately after that
Tag applied** to this Agent, including prior independent Tags. It does not
change when a later Tag actualizes the same name. It is a snapshot: read
only. Two spellings:

```python
agent.Paladin.Attack()       # by name: the last active Tag called Paladin
Paladin[agent].Attack()      # by class: exact, even when names collide
```

Agent-bound access requires **active** membership; a Rogue Agent keeps its
sticky members but loses the view. Secret members obey the same door in a
view.

**Direct Tag access**: the Tag itself.

```python
Paladin.HONOUR_CODE
Paladin.Operation(...)
Paladin[:]                    # its Field
```

Worked example:

```python
class Character:
    def Attack(agent) -> str:
        return "Faulty OOP attack."

class Person(Tag):
    def Attack(agent) -> str:
        return "Attack!"

class Elf(Person):
    @Action
    @Underlay
    def Attack(agent, underlay) -> str:
        return "With elven grace " + underlay()

class Paladin(Person):
    @Action
    @Underlay
    def Attack(agent, underlay) -> str:
        return underlay() + " For your holy oath!"

ari = Character()
Paladin(ari)
Elf(ari)

ari.Attack()             # "With elven grace Attack! For your holy oath!"
ari.Paladin.Attack()     # "Attack! For your holy oath!"
```

`Person` applies before `Paladin` and stays active when `Elf` arrives. Elf
captures the complete Attack Overlay (Person, then Paladin). The later Tag
replaces `ari.Attack()` without changing what `ari.Paladin.Attack()` means.

---

# Ring 2 · Contracts

Conditions are TOP's quality control. They run at tagging boundaries, never
continuously during play, and they never wrap an ordinary Action call.

## 2.1 A condition is strictly boolean

A condition is a function whose first input is the Agent. It **holds** on
`True` or on falling through without a `return` (an assert-style body),
**fails** on `False`, and is **rejected** on anything else.

```python
class Wizard(Tag):
    @Pre
    def Level_Over_Zero(agent):
        return agent.level > 0

    @Post
    def Has_Spellbook(agent):
        assert agent.spellbook is not None
```

TOP does not coerce truthy and falsy values: a Record of `0` spell slots is
a real value, not a failure. `return agent.spell_slots` raises a Contract
Failure telling you to write the comparison you mean. The absence of a
return is permission: a condition is a restriction, and saying nothing
permits. Legal until written into law.

> Contracts should be picky.
> The Layer's Lawyer

## 2.2 Preconditions: the gate

A Precondition inspects the **incoming materials**: may this Agent, with
these inputs, enter the line? It runs at step 1, once per call, for **the
Tags applied in the current call only**, as they will be composed: a
Shape's gate replaces its Base's. An earlier Tag's gate is not re-asked
when a later, unrelated Tag arrives; it already let its Agent in. Because
the gate runs before any Base applies, a Precondition sees the Agent as it
arrives, never what a Base's Imprint is about to write.

Preconditions receive application inputs by name:

```python
class Coded(Tag):
    @Pre
    def Has_Code(agent, code):
        return code is not None

Coded(bond)              # TagPreconditionError
Coded(bond, code="007")  # applies
```

A parameter the caller did not supply keeps its declared default, or is
`None` when it has none.

Preconditions **relax backward**. A Shape may ask for less than its Base,
never more, so a Shape can stand in wherever its Base is expected. Override
freely; compose with `@Underlay` when you want the Base's gate too:

```python
class Founder(Guild):
    @Pre
    def Dues_Paid(agent):
        return True                # founders skip the dues gate

class Apprentice(Wizard):
    @Pre
    @Underlay
    def Level_Over_Zero(agent, base):
        assert agent.mentor        # also needs a mentor
        return base()              # then the Base's gate
```

This is also how **synergy** is expressed: a feat that requires two other
Tags gates on both.

```python
class War_Caster(Tag):
    @Pre
    def Is_A_Caster(agent):
        return agent in Wizard
```

## 2.3 Imprints: the writing

An Imprint performs the work of tagging: it runs at step 4, after the Tag
has committed, in declaration order, with the application inputs by name.

```python
class MI6(Tag):
    @Imprint
    def SetUp(agent, code):
        agent.code = code
        agent.status = "Full"
```

An Imprint may apply further Tags to the same Agent; those are ordinary
later calls. If an Imprint fails, the Tag **stays** and the call raises an
Imprint Failure: the machine broke while writing, and the product is on the
line for inspection.

## 2.4 Postconditions: the promise

A Postcondition inspects the **finished product**. Every visible
Postcondition runs at step 5, **once per call, after the whole Form**, so a
Base may promise what its Shape delivers. Postconditions take no inputs:
they judge the Agent, not the materials.

Every visible Postcondition is re-checked at each later tagging boundary,
so a later Tagging can be refused by an earlier Tag's promise. Conditions
do not check themselves during play; what must be watched continuously is
a Record.

Postconditions **strengthen forward**. A Shape promises at least what its
Base promised: compose with `@Underlay` and `and`.

```python
class Knight(Soldier):
    @Post
    @Underlay
    def Is_Equipped(agent, base):
        return base() and agent.oath
```

Sometimes a specific case really is looser than the rule: "no Strength
above 20", except Barbarians. Overriding a Base Postcondition **without**
its Underlay is a **weakened** promise. TOP allows it, because forbidding it
would break the refactoring that is the point of TOP, but it is **never
silent**: a Contract Warning is raised at tagging. If the relaxation is
intended, the warning is your receipt; if it was a slip, it is your alarm.

The discipline in three lines:

- **Strengthen a Post** → `@Post @Underlay`, `return base() and …`. Silent.
- **Relax a Pre** → override freely. Silent.
- **Weaken a Post** → override without the Underlay. Allowed, diagnosed.

## 2.5 Defective Agents

A Tag whose Postcondition failed is **applied and defective**. The Agent is
a member; its promise is broken; it must be repaired or Ripped.

An Agent is **truthy exactly when every visible Postcondition holds**.
`if` is the conditional and Post*conditions* are conditions:

```python
if agent:               # every promise holds
    proceed(agent)

assert agent            # or raise
```

Fields partition accordingly:

```python
for wizard in Wizard:        # the sound population: the ones fit to play
for broken in ~Wizard:       # the defective population: repair them
for anyone in Wizard[:]:     # everyone, sound or defective
assert broken in Wizard      # a defective Agent is still a member
```

The plain loop is the working population. A broken Agent does not stop
being a member (`in`), does not leave `Wizard[:]`, and waits in `~Wizard`
for repair or Rip. Membership and the loop deliberately disagree for it:
the loop is the line, and a defective product is off the line.

Truthiness on a plain object is vacuously true, so this fills an empty
seat. A host that defines its own `__bool__` or `__len__` keeps it until a
Postcondition becomes visible on that Agent.

## 2.6 Naming the culprit

`bool(agent)` is the verdict. The `Contract` namespace names the promise
that broke:

```python
Contract.Postconditions(agent)   # promises hold, or raise naming one
Contract.Preconditions(agent)    # gates still hold, or raise
Contract.Conditions(agent)       # both, Pre then Post
Contract.Holds(agent)            # the boolean form, spelled out
Contract.Status(agent)           # {condition: holds?}, never raises
print(Contract.Display(agent))
# Hero[Wizard] contract:
#   Pre:
#     OK  Level_Over_Zero
#   Post:
#     XX  Has_Spellbook
```

## 2.7 Writing a check

A condition usually asks whether an Agent *has* something. `assert
agent.spellbook` reads well, but asks two questions at once: *defined* and
*truthy*. That is fine for a spellbook object; it is a trap for a
`spell_slots` of `0`. Separate having a contribution from its value:

- Is it there at all? `assert agent.spell_slots is not None`, or
  `assert hasattr(agent, "spell_slots")` when `None` is itself valid.
- Does it have a particular value? `assert agent.spell_slots > 0`.

---

# Ring 3 · Lifecycle

## 3.1 Rip protocols

Imprint and Rip are duals: constructor and destructor, `__enter__` and
`__exit__`. A `@Rip` Action runs when the Agent leaves the Tag's Field. It
is also an ordinary, callable Action.

```python
class MI6(Tag):
    @Imprint
    def SetUp(agent, code):
        agent.code = code
        agent.status = "Full"

    @Rip
    def SetDown(agent):
        del agent.code
        agent.status = "Former MI6 Agent"

MI6(bond, code="007")
del MI6[bond]
bond.status          # "Former MI6 Agent"
```

Teardowns run **after** membership has ended, in declaration order, every
one of them; failures are collected and reported once as a Composition
Failure. A `@Rip` Action with an `@Underlay` runs composed, like any Action.

Ripping a Tag may apply another Tag, even itself. That is outside good TOP
use: it could keep an Agent from ever leaving a Field.

## 3.2 Deleting an Agent

Deletion of an Agent Rips it from its active Tags, so exit protocols run.
An implementation provides three tiers and says which is which:

| Tier | Guarantee |
| --- | --- |
| **Finalizer** (`__del__`) | best effort: teardowns run when the Agent is collected; the language may not run finalizers at shutdown or inside reference cycles |
| **`Scope(agent, *tags)`** | guaranteed: Tags apply on entry and Rip, in reverse, on exit, even if the block raises |
| **`At_Exit(agent)`** | opt-in: teardowns also run at normal interpreter exit; registration is weak |

Every teardown runs at most once, whichever tier reaches it first.

```python
with Scope(agent, Sentry):
    guard_the_gate(agent)
# Sentry's teardown has run here, exception or not
```

---

# Ring 4 · Edges

What TOP does not promise, stated so nobody has to discover it.

- **Nominal type.** `type(agent) is Host` may be false after tagging. The
  type's name is unchanged and `isinstance(agent, Host)` is true. Code that
  keys on exact type identity is outside the guarantee.
- **Copying and pickling.** Cloning an Agent is domain work: build a new
  Target and apply its Tags again (`Tags(agent)` lists them). A Python
  implementation refuses `copy.copy` explicitly rather than aliasing state.
- **Threads.** One Agent, one thread. Fields are not synchronized.
- **Host descriptors.** A Record cannot share a name with a host property
  or slot; the Tagging fails with a Composition Failure.
- **Raw side effects.** Rollback restores TOP-managed state and the Agent's
  attributes at call entry. It cannot undo an in-place mutation of a
  pre-existing mutable value.
- **Operations and the door.** An Operation called directly on the Tag is
  outside composition unless it was reached from an Action, Imprint,
  condition or Rip of the Agent whose secrets it reads.

---

# 🚨 Failure model

Every failure names the law it violates. A language profile may use its own
types but must keep these distinct.

| Failure | Meaning | Effect |
| --- | --- | --- |
| **Tag Declaration Failure** | A Tag is written wrong: illegal mark combination, `@Underlay` without a parameter to receive it. | at class use |
| **Tag Composition Failure** | Contributions cannot form the Overlay: cross-kind collision, Record over a host descriptor, a Record builder or teardown that failed, a Target that cannot carry state, a Base still required. | call rolled back (or Rip refused) |
| **Tag Resolution Failure** | A required Underlay, view, or membership is unavailable. | call rolled back |
| **Tag Precondition Failure** | A gate refused the incoming Agent. | call rolled back |
| **Tag Imprint Failure** | An Imprint failed after commit. | Tags stay |
| **Tag Postcondition Failure** | The finished Agent breaks a promise. | Tags stay, Agent defective |
| **Tag Contract Failure** | A condition returned a non-boolean. | call rolled back |
| **Overwrite Warning** | An independent Tag replaced a visible Action or Record without an Underlay. | diagnostic |
| **Contract Warning** | A Shape weakened a Base Postcondition. | diagnostic |

---

# 🧰 Conformance obligations

A conforming implementation provides, ring by ring:

**Ring 0**
- stable object identity under tagging, and preserved host behaviour;
- membership and Base membership (`agent in Tag`), closed upward, with a
  has-been check that survives Rip;
- non-owning, identity-indexed, iterable Fields;
- Base-first Form application, each Base once, active reapply a no-op;
- the five-step tagging sequence with the call boundary: rollback on gate
  and Record failure, Tags stay on Imprint and Postcondition failure;
- Rip: sticky contributions, refusal while a Shape requires the Base, no
  cascade;
- native spellings for every Tag-level act, leaving the Tag's dotted
  namespace to the program.

**Ring 1**
- Agent and Tag scopes, `(scope, name)` slots, cross-kind collision rules;
- latest-Layer Overlay; captured, callable Underlays for Actions and
  conditions; the stored value for Records;
- Reports and Operations invisible on the Agent;
- publication: `@Secret` with a composition door that fails closed; `Public`
  Reports as read-only live names and `Public` Operations as Actions with
  the Agent as second input; illegal marks rejected at declaration;
- Delete; the three access forms, with Agent-bound views as read-only
  snapshots requiring active membership.

**Ring 2**
- strict boolean conditions; Preconditions gating only the current call,
  with inputs; Imprints after commit, with inputs; Postconditions once per
  call after the whole Form, re-checked at every later boundary, without
  inputs;
- the contract direction, with weakened Postconditions diagnosed;
- defective Agents: contract truthiness; the plain loop as the sound
  population, `~Tag` the defective one, `Tag[:]` everyone, membership
  unchanged; a namespace that names the culprit.

**Ring 3**
- `@Rip` protocols run after membership ends, once, composed, failures
  reported; the three deletion tiers.

**Everywhere**
- the failure types above, distinct and named.

An implementation may choose runtime type composition, generated wrappers,
proxies, trait machinery, or static code generation. Those are its business.
TagKit is the Python reference; any gap in TagKit is TagKit's to fix, not a
change to TOP.

---

# 🧭 TOP among paradigms

TOP was arrived at independently, from storage systems, organizational
models, and character creation. Several established ideas share pieces of
it:

- **Mixins and traits** compose behaviour per class, resolved once. TOP
  composes per instance, at runtime, and freezes each Layer as an Underlay.
- **The Role Object pattern** adds roles to a live identity but treats
  removal as ordinary. TOP treats removal as exceptional: a role is
  something you became; only active membership can be rescinded; changing
  state lives in Records.
- **Entity-Component systems** attach data to an identity. TOP keeps
  behaviour with the category and adds membership: "every Wizard".
- **Aspect-oriented programming** layers behaviour across a hierarchy. TOP's
  Imprints and conditions are a tag-time form of the same idea, scoped to
  one semantic act.
- **Design by Contract** (Meyer, Eiffel; Ada 2012 aspects) gives TOP its
  contract direction and its refusal to coerce booleans.
- **Ada packages** give TOP its specification/body picture: the Tag declares
  what is shared, the Agent is what acts.

TOP goes beyond these to one vocabulary: sticky runtime contributions,
active Field membership, captured Overlays, tag-time contracts, two scopes
with publication, and one stable identity.

More importantly, it is a thinking system: a simple idea with analogies to
the real world, strong enough to make complex systems intuitive. TOP is not
just a library; it is a way to think.

---

# 🧯 Commitments

1. A Target keeps one stable identity.
2. Tags add semantic context; they never replace inherent structure.
3. Membership is meaningful even when a Tag contributes nothing else.
4. Mutable Agent state belongs in Records; shared Tag data in Reports.
5. Composition is explicit, ordered, and inspectable.
6. A failed gate publishes nothing; a failed promise is never silent.
7. Rip ends active membership without pretending history never happened.
8. What the Agent does is public; what the Agency keeps is internal.
9. Language profiles feel native to their language.
10. Implementations serve the paradigm; the paradigm serves no single
    application.

Surface spellings may evolve. Implementation strategies may evolve. The
semantic laws stay.
