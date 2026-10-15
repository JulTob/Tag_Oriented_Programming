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
| **3 · Lifecycle** | teardown protocols, deletion |
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
- the accepted Target's own special methods (`__contains__`, `__len__`,
  operators, `__getattr__`) keep working, with one deliberate exception:
  an ordinary object Agent's `bool(agent)` is its visible Posts from
  first Tagging, even if the host defines `__len__`; `len(agent)` stays
  the host's (§2.5). A host with an explicit `__bool__` is refused as a
  Target before Tagging effects;
- the name of the object's type is unchanged.

What TOP does **not** promise is nominal type identity: a Python
implementation may swap the object's class for a runtime subclass of it.
`isinstance(agent, Host)` stays true; `type(agent) is Host` may not. See
Ring 4.

If preparation of that runtime representation fails, the Target keeps its
original identity, class and instance bindings, with no new Field entry
(STEP-SPEC-37). TopKit's Python host profile covers physical dictionary and
declared Python slot bindings; native extension fields and removed slot
declarations are outside its initial restoration profile. A custom host's
deliberate refusal is respected; ordinary frozen
dataclass field protection is not a refusal to prepare the representation.
This bounded restoration does not undo external effects or changes inside
mutable values, and does not prescribe rollback of later Gainings or
Imprints.

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
| **Pin** | A Tag marked `@Pin`, whose Targets are Tags (§1.9). |
| **Pinning** | Applying a Pin to a Tag: `Rare(Wizard)`. The pinned Tag is the Pin's Agent. |
| **Tool** | A Record whose value is an object of a declared kind, a specific Tag or a Python class (§1.3). Something you *have* (*tener*): what it is stays its own. |
| **Link** | A Tag one Agent holds under a Relation's name, `charlie.Knows`, made from a `@Link` Relation of a Tag it carries (§1.10). |
| **Contact** | A member of a Link's Field: whom the Link's Agent is related to (§1.10). |
| **Relation** | A Tag class marked `@Link` in a declaring Tag's body: the template of every Agent's Link, never a Tag in play (§1.10). |
| **Pair** | One Agent and one Contact, linked, `charlie.Knows[ruth]`: what the Relation declares for Agent scope lands here (§1.10). |

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

Tagging is **closed upward** through Bases: applying a Shape also applies
each missing Base in its Form, and the Agent enters each completed Tag's
Field. Afterwards each membership stands alone. Ripping a Base does not
remove the Agent from an active Shape's Field (§0.7).

```python
class Mortal(Tag): pass
class Human(Mortal): pass

Human(charlie)
assert charlie in Human
assert charlie in Mortal
```

Membership persists until Rip (§0.7), and Rip
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
assert f"{Arcane_Duelist:form}" == "Spellcaster → Duelist → Arcane_Duelist"
```

A Base reachable through several paths appears once. **Forming** follows
the Form downward, general to specific. The program may Rip memberships in
any order (§0.7). When TOP runs an Agent's teardowns at deletion or exit,
they run in reverse order of application (§3.2).

## 0.5 Applying a Tag

The canonical act is:

```python
Tag(target, **inputs)
```

If the requested Tag is not active, it applies every missing Tag in its
Form, Bases first, then returns the same Target. Keyword **inputs** are
handed by name to the Preconditions, Record builders and Imprints that
run during that call (§1.3, §2.2, §2.3).

```python
MI6(bond, code="007")      # every protocol that names `code` receives it
```

**Reapplying an active Tag does nothing.** It does not duplicate
membership, does not rerun Imprints, and does not rebuild Records. Rip ends
membership but leaves sticky Contributions. Applying the Tag after Rip is
fresh Tagging: that Tag's ordinary Record builders run again. Bases already
active are not reapplied. If a Shape remains active after its Base is Ripped,
calling the Shape again still does nothing; applying the Base explicitly
reinstates it through fresh Tagging. A builder without a second positional
seat replaces the current binding with its returned value;
a builder with that seat receives the current stored value and determines
how to evolve it. As in §1.3, an absent, deleted or Action binding supplies
`None`; `stored` is the example parameter name, not a required spelling.

## 0.6 The tagging sequence

Think of a factory line. For each missing Tag in the Form, in order:

1. **Gate.** That Tag's declarations are checked against the current
   Overlay, then its own Preconditions inspect the Agent and the inputs.
   A failed check or Precondition stops before that Tag begins; Tags whose
   turns have finished stay applied.

2. **Gainings.** That Tag's declarations are applied in order, top to bottom:
   Actions, Records, condition definitions and deletions take effect at their
   declared positions. Each acquired Gain or condition is visible to later
   declarations. A Record builder may read earlier Actions and Records as
   well as the value already stored under its own name. The Gate has already
   evaluated all of this Tag's own Preconditions before Gainings begin.
3. **Imprints.** That Tag's Imprints run, in declaration order, with the
   acquired Actions and Records available. The Agent is not yet in this Tag.
4. **FieldAdding.** After its Imprints finish, the Agent enters the Tag's
   Field. Membership and history are established together. The Tag's
   published Reports and Operations become accessible through the Agent,
   and its Agent-bound view is captured.

Then, once for the whole call:

5. **Posts.** Every visible Postcondition inspects the finished Agent.
   Checking once after the completed Form lets a Base promise what a later
   Shape supplies.

The **call boundary** decides what a failure means:

- A refusal in step 1 stops that Tag before its Gainings, Contributions, Field
  entry or Imprints. Earlier Tags completed during this call stay applied.
- A failure in steps 2 or 3 **raises and preserves acquired Gains**, but the
  Agent does not enter this Tag. It is a **Rogue Agent** with respect to this
  Tag: it acquired something without completing admission. Earlier completed
  Tags, including Tags applied by an Imprint, remain applied.
- A failure in step 5 **raises, but membership stays**. The product left the
  line. A defective product is flagged, repaired, or Ripped (§2.5).

| Outcome | Gains from this attempt | Membership in this Tag |
| --- | --- | --- |
| Gate refuses | none | absent |
| Gainings or Imprints fail | actually acquired Gains remain | absent; Rogue |
| Posts fail after admission | acquired Gains remain | present; defective while Posts fail |
| Posts hold after admission | acquired Gains remain | present; sound |

Calling `Tag(agent)` again after unfinished training starts a fresh attempt:
the Gate judges the Agent's current state, ordinary Gains overlay that state,
and Imprints start again. It does not resume at the failed instruction.
Successfully established Constants remain protected (§1.5); a Constant Record
whose builder never returned a value has no established binding to preserve.

Acquired conditions also remain after unfinished training, including Posts
and Constant Posts. As after Rip, being outside the Agency does not remove
the Agent's established contracts. Place a safety Post before the Action
that needs it, so the contract is present when that Action arrives. Ordinary
Posts follow TOP's existing composition rules; Constant Posts cannot be
replaced or deleted. Declaring a Post does not itself wrap ordinary Action
calls: an Action that must enforce it can read its named condition before
effects, such as `if not agent.Insulated: raise PermissionError(...)`.

The phase belongs to the call running the protocol. A nested refusal
inside an Imprint is that Imprint's failure, with the refusal as its cause;
a failure in a Record builder is a Gainings failure, not a Gate refusal.
Python interruptions follow the same boundary and propagate unchanged.
Before FieldAdding they leave acquired Gains without membership; after
FieldAdding they preserve membership. Failure to capture an admitted Tag's
view also preserves its membership.

An exceptional return does not itself make an Agent permanently defective.
Its current visible Postconditions determine soundness (§2.5), so a finished
Agent whose promises hold is sound. A Rogue may also satisfy its visible
Posts; soundness does not establish membership or complete unfinished
training.

```text
Citadel(ari)                      Form: Territory, Citadel
    Territory  Gate, Gainings, Imprints, FieldAdding
    Citadel    gate: Has_Charter FAILS
→ TagPreconditionError; ari in Territory == True, ari in Citadel == False

Broken_Wizard(ari)                Form: Person, Broken_Wizard
    Person     Gate, Gainings, Imprints, FieldAdding
    Wizard     Gate, Gainings, Imprints, FieldAdding
    check      Has_Spellbook FAILS
→ TagPostconditionError; ari in Person and ari in Wizard; bool(ari) == False
```

Preconditions judge by reading and querying. Record builders read and query
to calculate their initial returned values. Applying or Ripping Tags and
changing the world belong to Imprints, not Preconditions or Record builders.
These authoring rules are not a Python sandbox: automatic copies cannot undo
arbitrary Python or external effects.

Unfinished training does not trigger Rip: the Agent never entered that Tag.
It is outside `Tag[:]`, and `del Tag[agent]` cannot expel a nonmember. The
program owns cleanup of resources acquired during that attempt, using
ordinary Python error handling. TOP does not undo Imprint effects.

## 0.7 Rip

Tags can be seen like a pass, a sticker, a badge. Ripping one is an
exceptional, violent act of Field expulsion: *"Give me your badge and
weapon. You can no longer go into the evidence room."*

```python
del MI6[bond]
assert bond not in MI6
assert isinstance(bond, MI6)      # once an agent, always an agent
```

Rip is the only exit from a Field, and it obeys these laws:

- **Contributions are sticky.** Actions and Records stay on the Agent after
  Rip unless a `@Rip` protocol (§3.1) changes them. The result is a **Rogue
  Agent**: it has what it learned, but no active access to the Tag's Field,
  Operations, Reports or Agent-bound view. Rogue Agents are dangerous… but
  useful.
- **Each membership stands alone.** `del Beast[wolf]` ends Beast membership
  even while `Wolf` remains active. Beast's teardowns run; Wolf stays in its
  Field, with its acquired Actions and Records. Rip never cascades: TOP does
  not run other Tags' protocols behind your back. If Wolf needs continuing
  Beast membership, its author states that dependency in a Postcondition;
  the Rip then leaves Wolf defective while that Post fails (§2.5).
- **Conditions are sticky too** (STEP-SPEC-12). Rip does not touch a
  Tag's Preconditions or Postconditions: a promise that outlives its
  Tag fails loud, never silently. Rip does one thing, and it is the one
  act nothing can roll back, so it is not the place for a second rule.
  **The author ends a condition**, in one of two visible ways: a **guard
  in the condition** (`if agent not in Wizard: return True`), which can
  follow any membership at all, another Tag's, a keyword on a Tag, the
  Tag under an Underlay; or an **explicit deletion from the Tag's own
  `@Rip` protocol**, `Contract.Delete(agent, "Has_Book")`, one
  deliberate name at a time. A name that is not a condition on the Agent
  is a Resolution Failure. A Constant Post (§1.5) cannot be deleted;
  any membership guard must be part of its original check.
- **Reapplying a Ripped Tag is a fresh Tagging.** Imprints run again;
  that Tag's ordinary Record builders run again. A builder without a second
  positional seat replaces the current binding; one with that seat receives
  the current stored value, including a value left by the Tag's earlier
  application (§1.3).
  Established Constant bindings stay intact; their builders do not run
  again for the same declaration.

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
| carries a keyword? (Flags, §1.8) | `"Undead" in ghoul`, `Undead in ghoul`, `Keyword(ghoul, "Undead")`; a Flag's words the same, `"Wolf" in howler` |
| ever a member? | `isinstance(agent, Wizard)` |
| the sound population | `for w in Wizard`, `len(Wizard)`, `if len(Wizard) > 0:` |
| the defective population | `for w in ~Wizard`, `if ~Wizard:` |
| everyone in the Field | `Wizard[:]`, `if Wizard[:]:` |
| the Tag's own Posts hold | `bool(Wizard)`, `if Wizard:`; no Posts means true, even with an empty Field |
| populations combined (§2.5) | `Wizard \| Fighter`, `Wizard & Fighter`, `Wizard - Sworn`; the same on `Wizard[:]` and `~Wizard` |
| one condition, read on the Agent (§2.5) | `agent.Has_Book` |
| a named Contribution is present (§1.1) | `"Attack" @ agent`, `"Attack" @ Wizard[agent]` |
| keep a Contribution's binding fixed (§1.5) | `@Constant` with `@Record`, `@Action`, `@Post`, `@Report` or `@Operation` |
| a Tag of one's own, and its Contacts (§1.10) | `@Link` on a Tag in a Tag's body; `charlie.Knows(ruth)`, `ruth in charlie.Knows`, `charlie.Knows[ruth].since`, `del charlie.Knows[ruth]`, `del charlie.Knows[:]` |
| a Record whose value is an object of a kind (§1.3) | `@Tool(Weapon)` for a member of the Tag, now; `@Tool(Sword)` for an instance of the class; `@Tool(Sword, Weapon)` for both; `@Tool(Weapon \| None)` when the slot may be empty |
| the Agent-bound view | `Wizard[agent]` |
| leave the Field (Rip) | `del Wizard[agent]` |
| the Form, as Tags | `Form(Wizard)` |
| the Form, as text | `f"{Wizard:form}"` |
| an Agent's Tags, Outline, contract, as text | `f"{agent:tags}"`, `f"{agent:outline}"`, `f"{agent:contract}"` |
| catch one check's failure (§2.6) | `except Precondition.Is_A_Caster:`, `except Postcondition.Has_Book:`, `except Imprint.Arm:` |
| catch a Rogue Agent's access (§1.5) | `except TagRogueAccessError:` |
| end a condition explicitly (§0.7), from a `@Rip` protocol | `Contract.Delete(agent, "Has_Book")` |
| necessary to enter and to stay (§2.7) | `@Pre` + `@Post`, stacked on one function |
| pin a Tag (§1.9), and every act above with a Tag in the Agent's seat | `Rare(Wizard)`, `Wizard in Rare`, `for tag in Rare`, `Rare[Wizard]`, `del Rare[Wizard]` |
| a Tag carries a keyword? (Flag Pins, §1.9) | `"Deprecated" in Wizard`, `Keyword(Wizard, "Deprecated")` |
| a Tag's Pins and contract, as text | `f"{Wizard:pins}"`, `f"{Wizard:contract}"` |

Truth on a Tag checks its own visible Posts received through Pins (§1.9),
just as truth on any Agent checks its Posts. It does not check the Posts
the Tag declares for its members. A Tag with no Posts is true even with an
empty Field. Population questions use their cardinalities: `len(Wizard) > 0`
asks whether any sound Wizard exists, `while len(Enemy) > 0:` continues
while a sound enemy stands, and `if len(Boss) == 0:` can spawn one.
`len(Wizard[:])` counts everyone and `len(~Wizard)` counts defective members.
Population views keep collection truth: `if ~Wizard:` asks whether anyone
waits for repair, and `if Wizard[:]:` includes sound and defective members.

The Agent's own `in` is reserved for **keywords**: Tags marked `@Flag`
(§1.8). Ordinary Tags are asked from the Tag's side, `agent in Wizard`.

Format specs are the **display door**: a language's own string formatting
renders what a Tag or Agent is, without a method on either. On an Agent the
door follows the empty-seat rule: a host with its own formatting keeps it.

Queries that need a name are functions (`Form`, `Tags`, `Keyword`,
`Apply`, `Outline`, `Contract`), never members of the Tag or of the
Agent.
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

The receiver may itself be a Tag. When a Tag is applied to another Tag
(**pinning**, §1.9), the pinned Tag is the receiver, so the Pin's Records
land as Reports and its Actions as Operations of that Tag: Tag scope,
because a Tag is what receives them.

In Ada's terms, the Tag is the package specification and the Agent is the
body. The specification declares what is shared; the body is what acts.

A name identifies **one slot per scope**: `(scope, name)`. In Agent scope
that slot holds an Action or a Record, never both at once:

- **Independent** Tags (neither in the other's Form) cannot place an Action
  and a Record at the same Agent name. The current Tag fails at step 1 and
  never enters its Field; completed earlier turns stay applied.
- Within one Form, a Shape may **change the kind** of a Base slot: fix a
  Base Action as a Record, or compute a Base Record with an Action. The
  Base's view (§1.7) keeps the prior kind.
- Across scopes, equal names do not collide. `Fire.colour` (Tag) and
  `ember.colour` (Agent) are two slots with two histories.
- A **Link** (§1.10) is a third kind of Agent-scope contribution. Its
  slot is closed: no Action, Record, condition or `@Delete` arrives at a
  name that holds a Link, a Link never arrives where something is, and a
  Shape's change of kind never reaches it. On a Link, what the Relation
  declares for Agent scope lands on the Pair.

### Presence by name

Specified by [STEP-SPEC-33](../steps/spec/STEP-SPEC-33-contribution-presence.md).

`"name" @ agent` returns a boolean indicating whether the Agent currently
provides that name. Presence is independent of a Contribution's kind and
origin: a host attribute or method counts, and a name changing between
Action and Record does not change its presence. Stored `False`, `None`,
zero and empty values count as present. A declaration or leftover registry
entry without an actual binding does not.

The query does not execute Actions, Operations, host property getters,
lazy Report builders or Postconditions. A host property's binding counts
without evaluating its getter; names synthesized only by `__getattr__`
do not count. Presence guarantees neither successful value access,
callability nor successful behaviour. A Postcondition states which names
are required and any further conditions on their values or behaviour.

On the actual Agent, the query checks the current Overlay and host
bindings. Tag-scope names count there through publication. A published
Report requires its active publishing Tag; a lazy Report need not have
been read to be present. A published Operation's sticky Action can remain
present after Rip even though its use is refused (§1.5).
`"name" @ Wizard[agent]` instead checks that Agent-bound view's captured
contributions, including its captured shared contributions. Both forms
respect the receiver Agent's composition door for Secret names (§1.5).
Presence does not evaluate soundness.

Only a string left operand selects this TOP meaning. Other operands
retain the receiver's existing `@` behaviour. A pinned Tag is an Agent and
supports the query in that role; the operator introduces no presence API
on a bare, unpinned Tag.

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

An established Constant Action (§1.5) cannot be replaced or extended.

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
The Agent truth protocol `__bool__` is reserved for Posts (§2.5).

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

A Record is declared as a **builder**. The builder runs during Gainings,
step 2 of the tagging sequence; its value is stored on the Agent, fresh for
each Agent:

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

A Record signature has three seats: the Agent, the stored value, and the
application inputs, which bind **by name**. The second positional
parameter is always the stored seat; when there is nothing to read, a `*`
holds the seat empty and the inputs follow it by name:

```python
class MI6(Tag):

    @Record
    def code(agent, *, code):        # agent, nothing stored, code from the call
        return code

MI6(bond, code="007")
bond.code                            # "007"
```

A builder whose second positional parameter is named like a supplied input
is refused at tagging with a Declaration Failure that shows the spelling
above: the stored value must never be mistaken for the input in silence.
An input the caller did not supply keeps the parameter's default, or is
`None` when it has none.

After tagging, an ordinary Record can be read, assigned, or deleted with
the language's own `del agent.record`. A Constant Record (§1.5) can be read
but its binding cannot be replaced or deleted. Constant does not freeze
the value: a list can still receive items, and each Agent keeps its own
initialized list. Deleting ordinary Records is allowed but rarely good
design; frequent deletion means unclear state ownership.

Mutable Record values must be fresh per Agent unless sharing is the
explicit intent. Shared values belong in a Report.

### Tools

A **Tool** is a Record whose value is an object of a declared **kind**:
something the Agent *has* (*tener*), beside what it *is* (a Tag) and
what it is *currently* (a Record). The held object may be an Agent of
its own, with its own Tags, Field, contract, keywords and secrets;
nothing it is reaches its bearer, and nothing the bearer is reaches it.
The curse on the sword is the sword's.

`@Tool(K1, ..., Kn)` marks a Record builder and names the slot's kind.
Each `Ki` is a **specific Tag**, asked as membership now, or a **Python
class**, asked as the language's own instance test; all of them hold.
Inside one `Ki`, the language's own union names alternatives, any of
which admits the value, and `None` among them declares the empty hand.
`@Tool(...)` alone declares the Record; `@Record` may be written as well
and restates it. The mark stacks with `@Constant`, `@Secret` and
`@Public` in either order, and the builder keeps a Record's three seats:

```python
class Fighter(Tag):

    @Tool(Sword, Weapon)                # a Sword that is a Weapon, now
    def weapon(agent, *, weapon):
        return weapon                   # the forge Tagged it; the slot never does


Fighter(charlie, weapon=sword)
charlie.weapon in Weapon[:]             # True: the tool is a Weapon
charlie in Weapon[:]                    # False: the bearer is not
```

| Kind | Admits | Spelled |
| --- | --- | --- |
| a Tag | a member of the Tag now, sound or defective, a Shape's member included; never a Rogue of it | `@Tool(Weapon)` |
| a class | an instance of the class or a subclass, tagged or not, a Rogue included | `@Tool(Sword)` |
| several | a value every kind admits | `@Tool(Sword, Weapon)` |
| alternatives | a value any alternative admits | `@Tool(Sword \| Staff)`, `@Tool(Weapon \| Staff)` |
| the empty hand | `None`, besides the kind | `@Tool(Weapon \| None)` |

Three laws govern the slot:

1. **The slot has a kind, checked at admission.** Admission is asked when
   the slot is gained, on what the builder returns, and at every write
   to it, `object.__setattr__` included. A refusal is a Composition
   Failure: at the gaining it is a Record failure of §0.6; at a write
   nothing changes. Admission is a gate, never re-asked: a seated tool
   that later leaves its Tag stays in hand, a Rogue, and the bearer's
   own promise notices it (§2.4); a Tag kind refuses such a Rogue only
   if it is seated again, and a class kind admits it. Admission never
   evaluates the object's contract. Presence (`"weapon" @ agent`),
   current membership (`agent.weapon in Weapon[:]`) and soundness
   (`bool(agent.weapon)`, once it is known to be an Agent) stay three
   questions. An untagged value retains ordinary Python truth.
2. **The slot is never empty, unless its kind says so.** With a kind of
   Tags and classes alone, a builder that returns `None` and an
   assignment of `None` are Composition Failures. A kind written with
   `| None` admits `None` at the gaining and at the write: the empty hand
   is declared where readers see it. In both cases the drop is
   `del agent.weapon`, and `@Delete` at the name frees the slot (§1.6).
   A Constant slot refuses both (§1.5).
3. **The slot never Tags.** The kit applies no Tag to what the builder
   returns or to what is assigned. The forge Tags the object in plain
   sight, or the object arrives already Tagged. A tagging inside the
   builder is an ordinary call on another Target with its own §0.6
   boundary: its failure keeps its own name and refuses the bearer's
   gaining; a Tag it applied to a pre-existing object stays applied,
   since Rip is not restoration (§0.7).

The rule belongs to the effective Record declaration, as Overlay already
says (§1.2). A later Layer that redeclares the name as a Tool brings its
own kind and receives the held tool in its stored seat; a plain Record
or an Action at that name replaces the Contribution as it would any
Record, and the rule ends with it; `@Delete` frees the slot. Rip of the
bearer's Tag leaves the slot, its tool and its rule in hand, as
Contributions are sticky (§0.7); reapplication rebuilds an ordinary slot
through the builder and keeps a Constant one (§1.5). Two slots may hold
one tool, a tool may bear tools, a bearer may hold itself when it is of
the kind, and a tool is held strongly, as a Record holds its value.

The kind is a declaration-time fact. `@Tool()` without a kind, `None`
alone, a bare `@Tool` on the builder, the root `Tag`, `object`, a Pin
(§1.9: a Pin's Agents are Tags), a population (`Weapon | Blessed`,
`~Weapon`, `Weapon[:]`: §2.5's Field algebra, not a kind; the refusal
shows `@Tool(Weapon, Blessed)` for both and a common Base Tag for
either), an instance, a typing construct with no plain instance test,
`@Tool` over any other kind of declaration, or `@Tool` inside a `@Pin`
(a Pin's Records land as Reports, §1.9) is a Declaration Failure at
class use. A slot under a protocol name (`__rmatmul__`) keeps the
language's own hook: its ordinary writes are checked, and a kernel write
to it is a documented bypass, as writing the instance dictionary is.

## 1.4 Reports and Operations

A **Report** is shared data belonging to a Tag; an **Operation** is shared
behaviour. Both take the Tag as their first input, the way Agent members
take the Agent. The four kinds are one pattern, two scopes:

| | behaviour | data |
| --- | --- | --- |
| **Agent** | `@Action def f(agent, ...)` | `@Record def r(agent, stored)` |
| **Tag** | `@Operation def f(tag, ...)` | `@Report def r(tag, inherited)` |

```python
class Community(Tag):

    @Report
    def colour(tag) -> str:
        return "green"

    @Operation
    def Greet(tag, name) -> str:
        return f"{tag.__name__}:{name}"

Community.colour            # "green"
Community.Greet("Ari")      # "Community:Ari"
```

An ordinary Report builder runs once per Tag, on first read, and its value
is held on the Tag: one copy for the whole Field. Like a Record, it may declare a
second parameter, which receives the value the Tag's Bases give that name,
or `None`, so a Shape can extend a Base's Report rather than replace it.

A Constant Report initializes once on its **declaring Tag**, on first
read through that Tag or any Shape. The builder receives the declaring
Tag. Every Shape shares the exact same resulting value; no Shape runs a
separate initialization. Its binding cannot be replaced or deleted, but
the value's contents may mutate. A Constant Operation instead fixes the
implementation: it still runs on every call with the Tag through which
it was called as receiver.

Reports and Operations are **not visible on the Agent**. `ari.colour` does
not exist after `Community(ari)`, and neither does `ari.Greet`. Projecting
Tag members onto Agents would invent an Agent receiver for Tag behaviour,
silently shadow host methods, and confuse the two histories. The Agent
reaches them through its Tag-bound view (§1.7) or through publication.

A shared counter is a Report; the Imprint that changes it acts on the Tag:

```python
class Secret_Agent(Tag):

    @Report
    def active(tag) -> int:
        return 0

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
| Operation, Report | **internal** | `@Public` publishes it on the Agent |

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

`@Public` on a Report or Operation constructs the publishing member for
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

    @Public
    @Report
    def colour(tag) -> str:
        return "navy"

    @Public
    @Operation
    def dispatch(agency, sender, message):
        return network.broadcast(sender, message)   # a Rogue sender never gets here

Agency(agent)
agent.colour                     # "navy", read-only
agent.dispatch(message)          # Agency.dispatch(Agency, agent, message)
```

The published Action is a normal Action: it overlays and underlays at
`(Agent, name)` and stays on the Agent after Rip. Its **use** does not: a
published member **answers members only, and only sound ones**
(STEP-SPEC-10). At every use, an Operation's call or a Report's read, TOP
checks that the Agent still belongs to the publishing Tag and that every
promise on the Agent holds, whichever Tag made it: the same soundness
`if agent:` and the loop ask about. A Rogue Agent (it left or never completed
admission) gets a **Rogue Access Failure**, a Resolution Failure; a stale
`send = agent.dispatch` captured before Rip fails the same way. A
defective Agent (a promise broke) gets the **broken promise by name**,
`except Postcondition.Has_Homeland`, so it can repair what the failure
names and retry. Membership or repair opens the member again; nothing is
re-declared. The Agent's own Actions and Records are untouched: what it
became stays. A defective Agent reads the Tag's shared values through the
Tag directly, which asks nothing about the Agent. TOP is not a security
system; a long-running task may still re-check authority before an
irreversible step.

A Rogue Access Failure is a TOP failure and nothing else. It is not
dressed as a failure of the host language's attribute lookup: the
question *is this Agent a member?* belongs to TOP, and answering it in
the lower layer's words would let a lower-layer question (`hasattr`)
swallow it and report *no such name* for a name that plainly exists.

`@Secret` and `@Public` are **modifiers**: they stack with `@Action`,
`@Record`, `@Operation` and `@Report` in either order. A modifier that
restates the default (`@Public @Record`, `@Secret @Report`) is accepted;
both on one member is a contradiction and is rejected at declaration.

### Constant bindings

`@Constant` protects a named Record, Action, Post, Report or Operation
from replacement and deletion. It stacks with its declaration in either
order and is independent of `@Public` and `@Secret`. An unmarked method
may also be a Constant Action. A Constant modifier on an unsupported
declaration is a Declaration Failure.

Once established, a Constant binding survives normal Python assignments
and deletions, later Layers of any Contribution kind, `@Delete`,
Underlay-based replacement, and Pin patches. Such an attempt raises a
Composition Failure and leaves the Constant intact. A Shape declaration
that would hide a Base's Constant name, including with an ordinary Python
value, is a Declaration Failure. Direct reassignment or deletion on the
declaring Tag or a Shape is also refused.

A Constant Record is initialized per Agent and keeps its value on
reapplication of the same declaration. A Constant Action or Operation
keeps its implementation and ordinary call behavior. Constant does not
freeze mutable values or memoize behavior. Constant Reports have the
single declaring-Tag initialization described in §1.4.

A Constant Post keeps its check after Rip and cannot be replaced or
deleted through `Contract.Delete`, a protocol or another Layer. Other
Posts can be added under independent names; all applicable promises must
hold. Constant does not change when contracts are checked or require a
Post to return the same answer as the Agent changes. It locks the check's
binding, but cannot restore `assert` instructions removed by optimized
Python (§2.1).

Applying an active Tag remains a no-op. Reapplying after Rip preserves
the same declaration's Constants while rebuilding ordinary Records and
repeating Imprints. These rules do not change the tagging failure phases
in §0.6.

The Python guarantee includes normal member assignment and deletion,
including `object.__setattr__` on protected Agent bindings. It does not
provide a sandbox against deliberate manipulation of private runtime
state, direct namespace tampering or arbitrary Python execution.

## 1.6 Delete

`@Delete` on a name removes the visible contribution, or the host member,
of that name. It frees the slot: the next contribution may occupy it with
either Agent kind, and an Underlay-seeking contribution finds nothing.
Deleting a Constant Contribution is refused and leaves its binding intact.

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

## 1.8 Flags: Tags as keywords

Tabletop rules have **keywords**: Undead, Flying, Fey. A rule does not
import the creature's species; it asks whether the word is on the sheet. A
Tag marked `@Flag` is such a word. Its name becomes searchable from the
Agent's side, by name or by class:

```python
@Flag
class Undead(Tag):
    pass

Undead(ghoul)

assert "Undead" in ghoul             # by name
assert Undead in ghoul               # by class
assert Keyword(ghoul, "Undead")      # the function form, works on any object
assert ghoul in Undead               # membership, as for every Tag
```

This is what lets rules live as data. A table entry `"Undead-Flying"`
splits into words, and `Keyword(agent, *words)` decides; the rule ports to
any program whose Tags carry those names.

Flags are **opt-in** on purpose. Matching by name is global: two Tags that
share a name are one word to a string. Only Tags that ask to be words carry
that risk, and an ordinary Tag is never found by name. Names match
exactly.

**Words.** A keyword has variants and neighbours: to the rules that name
it so, a werewolf is also a *Wolf* and a *Lycanthrope*. `@Flag` takes the
words a Tag also answers to:

```python
@Flag("Wolf", "Lycanthrope")
class Werewolf(Tag):
    pass

Werewolf(howler)

assert "Wolf" in howler              # a word
assert "Werewolf" in howler          # the name always flags
assert Werewolf in howler            # the class form is unchanged
assert Keyword(howler, "Lycanthrope")
```

A word is only a word. It answers `in` and `Keyword`, never membership:
an Agent may carry the word *Beast* without being a `Beast`, the way a
secret identity carries a public name. A word that names another Tag is
accepted, and says nothing about that Tag's Field. Many Tags may share a
word; it answers while any of them is active. The words are the Tag's
own: a Shape's Agent answers its Base's words while that Base remains
active (§0.3), never by inheriting them. Rip the Base and those words
leave, even if the Shape stays. Bare `@Flag` is the name alone. Words are
non-empty strings and match exactly, like names.

A Flag needs the Agent's `in`, and one seat holds one meaning. Something
else may already answer it: the host, through its own `__contains__` or
`__iter__` (a container, a party that iterates its members), or a Tag's
Action of either name, a published Operation included. A Flag and any of
them collide, in either order. The later one fails with a Composition
Failure naming both sides, like a Record over a host property. Within one
Form, the collision is checked when that Tag's turn arrives: completed
Base Tags stay, while the colliding Tag never begins. A seat never changes
meaning in silence. A Flag that declares such an Action itself is a
Declaration Failure.

The host's seat is read as the language reads `in`. In Python, for
`__contains__` and then `__iter__`, the first class in the MRO that
defines the name decides. The value `None`, Python's "`in` is
unavailable", leaves the seat free. `__getitem__` alone is not a seat, and
a Flag takes it: on a keyed host its `in` fails or never ends; on an
index-style host (the old sequence protocol) its `in` worked, and stops
meaning membership once a Flag lands.
`Keyword(...)` answers for every object, tagged or not.

## 1.9 Pins: Tags as Targets

Categories have categories. A game marks Tags as *Rare* or *Homebrew*; a
rules engine keeps Tags by *School*; a program walks every Tag that is
*Deprecated*. A Tag marked `@Pin` applies to Tags, and the pinned Tag is
its Agent in every sense of Ring 0: membership, a Field to walk, a gate,
a promise, a view, a Rip.

```python
@Pin
class Rare(Tag):

    @Record
    def rarity(tag):                     # lands as Wizard.rarity: a Report
        return "rare"

    @Action
    def Describe(tag):                   # lands as Wizard.Describe: an Operation
        return f"{tag.__name__} is {tag.rarity}"


Rare(Wizard)

assert Wizard in Rare                    # active membership, from the Pin's side
assert list(Rare) == [Wizard]            # a Field of Tags
assert Wizard.rarity == "rare"           # one value, held on the Tag
assert Wizard.Describe() == "Wizard is rare"
assert not hasattr(charlie, "rarity")    # never on the Tag's Agents
```

**Who may be a Target.** A Pin applies to Tags only; on an object it
fails with a Composition Failure. An ordinary Tag applies to objects only;
on a class it is refused, as before. A Pin may not pin itself or any Tag
of its own Form. A Shape of a Pin is a Pin, and one Form is all Pins or
no Pins: mixing them is a Declaration Failure. Fields therefore never mix
Agents and Tags.

**The receiver rule** (§1.1). The first parameter of a Pin's Agent-scope
member is the pinned Tag; write it `tag`. A Pin's Record lands as a
Report of the pinned Tag: one value, held on the Tag, inherited by its
Shapes, and readable through the `inherited` seat of a Shape's own Report
(§1.4). A Pin's Action lands as an Operation: read from the pinned Tag or
any of its Shapes, it receives the Tag it was read from, as an Operation
does. Membership does not inherit: `War_Caster in Rare` is False until
`Rare(War_Caster)`. Nothing a Pin lands is ever projected onto the Tag's
Agents. A Pin's own Operations and Reports stay on the Pin.

**Patching, with collision control.** The pinned Tag's own Tag-scope
declarations are host members to a Pin, as a host method is to an
Action. A Pin Action over the Tag's own Operation replaces it silently
with the Operation as its Underlay, so `def Control(tag, underlay, ...)`
can call the engine it patches; every Agent that reaches the Operation
through the Tag is actualized at once, because an Operation is looked up
on the Tag at call time. A Pin Record over the Tag's own Report receives
the Report's value in the stored seat. A failed pinning rolls the
declaration back; a Ripped Pin leaves the patch, sticky, and a Pin's
`@Rip` teardown that declares a second seat receives the Tag's
**original declarations** under the patched names, so un-patching is one
line: `def Unpatch(tag, original): tag.Control = original.Control`. A Pin
member
named like something the Tag declares in **Agent scope** or as a
**protocol**, itself or in a Base, is refused at the gate: on a class the
scopes share one dictionary, and the write would silently remove the
declaration from every future Agent's contract. So is a name every Tag
answers through its metaclass. Names another Pin landed follow the
Overlay laws of §1.2 and §1.3.

Constant protection applies to Pin composition too. A Pin cannot replace
or hide an existing Constant Contribution of its Target or a Target's
Base; a failed patch leaves that Constant intact.

**Publication on a Tag.** `@Secret` on a Pin's Record or Action makes it
Pin-private state on the Tag: held in the Tag's state, resolved only
while the Tag's own protocols or pinned Operations run, an Attribute
failure from main, not inherited by Shapes. `@Public` publishes it onto
the pinned Tag's **Field**: every present Agent receives it at pinning
and every future Agent through the Tag, as the Tag's own published
Report or Operation (`def Control(tag, agent, ...)`, the Agent second),
under the membership rule of §1.5. The Field is checked on copies first;
a collision on any one Agent refuses the pinning and touches none. A
Pin's own Reports and Operations are not published, and `@Delete` and
special-method Actions on a Pin are Declaration Failures.

**Keywords on a Tag.** A Pin may be a Flag. A string can never be a
member, so on a Tag a string in the `in` seat asks for a keyword:
`"Deprecated" in Wizard` is True while the Flag Pin `Deprecated` is
active on it, and so is each word it lists; objects and classes in that
seat ask membership.
`Keyword(Wizard, "Deprecated")` and `Keyword(Wizard, Deprecated)` answer
the same. A word like *Deprecated* is a Pin and not a Report for the
reason `Undead` is a Tag and not `asleep = True`: a Report is a value,
and a value implies it may be flipped back; a Pin is membership, with a
Field, a gate, a promise, a Rip that is an act, and a history
`isinstance` remembers. A Tag says what something *is*; a Record says
what it *has* right now.

**The Tag's own contract.** `bool(Wizard)` checks its visible Pin Posts,
including those retained after Rip; no Posts means true. The Tag's Field
does not decide its truth. `len(Wizard) > 0` asks for a sound member (§0.8).
A pinned Tag's promises can also be read from the Pin's side,
`Wizard in ~Rare`, or inspected with `Contract.Display(Wizard)` and
`f"{Wizard:contract}"`.
`f"{Wizard:pins}"` names its Pins. `Wizard.Rare` is the Pin-bound view
by name, on the same miss-path rule as `charlie.Wizard`.

**Contracts, Imprints, Rip.** A Pin's Preconditions gate its own turn and
receive the Tag; a failed Gate leaves that Pin unapplied and its metaclass
unchanged, while completed Base Pins stay. Postconditions are checked once per pinning and
re-checked at later pinning boundaries of that Tag; a broken promise
leaves the Tag pinned and defective (§2.5). Imprints run before FieldAdding;
unfinished pinning leaves its acquired Gains without membership in the Pin.
`del Rare[Wizard]` runs the Pin's Rip protocols; landed values and
Operations stay, sticky, and `isinstance(Wizard, Rare)` stays True.
Pinning again after a Rip is a fresh pinning (§0.7).

A Pin does not alter the pinned Tag's own gate over its Agents. A Tag
that should refuse new members while Deprecated writes that as its own
Precondition, reading its Pins.

## 1.10 Links

Every Tag above is a one-place statement: *Ruth is a Wizard*. Many domains
need two-place ones: *Charlie knows Ruth*, *this drone follows that one*.
A two-place statement is a family of one-place statements, one for each
Agent in the first place, so TOP needs no new kind of membership, only a
way for each Agent to have a Tag of its own: a **Link**.

```python
class Social(Tag):

    @Link
    class Knows(Tag):                         # the Relation: a template

        @Pre
        def Not_Oneself(agent, contact):      # the Agent acts; the Contact is acted on
            return contact is not agent

        @Record
        def since(agent, contact, *, since=None):   # a fact about the Pair
            return since

        def Greet(agent, contact):            # an Action of the Pair
            return f"{agent.name} waves at {contact.name}"


Social(charlie)
Social(bob)
charlie.Knows(ruth, since=2010)               # Ruth is Charlie's Contact

ruth in charlie.Knows                         # True
ruth in bob.Knows                             # False: Bob's Link is another Tag
charlie.Knows[ruth].since                     # 2010: the Pair's Record
charlie.Knows[ruth].Greet()                   # "Charlie waves at Ruth"
del charlie.Knows[ruth]                       # Rip: Charlie forgets Ruth
```

| Term | Meaning |
| --- | --- |
| **Relation** | A Tag class marked `@Link` in a declaring Tag's body: the template every Agent's Link is made from. Never a Tag in play. |
| **Link** | The Tag one Agent holds under the Relation's name, `charlie.Knows`: a distinct Tag with its own Field. |
| **The Link's Agent** | The one who holds the Link and acts through it: Charlie. |
| **Contact** | A member of a Link's Field: Ruth. |
| **Pair** | One Agent and one Contact, linked: `charlie.Knows[ruth]`. It receives what the Relation declares for Agent scope. |

**Granting.** A Link is an Agent-scope contribution of the declaring Tag,
a third kind beside the Action and the Record. It is granted in declaration
order during Gainings (§0.6), visible to subsequent Gains and Imprints,
stored under the Relation's name, and **read-only**: assigning or
deleting `charlie.Knows` is a Composition Failure, `object.__setattr__`
included. Its slot is **closed**: nothing else arrives at that name, in
either order, and a Link never arrives where something is, a value the
Agent itself holds included. Links are sticky (§0.7): Rip of `Social`
leaves `charlie.Knows` with Charlie, and reapplying `Social` keeps the
same Link, its Field and its Pairs. A failure after the Link was gained
also keeps it; it does not establish membership in the unfinished Tag.

**A Link is its Agent's.** The Relation is only the declaration; the Tag
is each Agent's own, built when that Agent gains the declaration. So a Link is the
whole of `charlie.Knows`, and the name `Knows` alone is no Tag:
`bob in Social.Knows` has no answer and is refused (below), while
`bob in ruth.Knows` is a question Ruth's Link answers by itself, never
Charlie's. Two Agents' Links share a name and a template and nothing
else: two Fields, two Pairs for Bob, and `isinstance(bob, charlie.Knows)`
says nothing of `ruth.Knows`. Printed, they look alike, since nothing
public on a Link names its Agent (One direction, below).

**The seats.** Every function a Relation declares for the Pair takes the
Link's Agent and the Contact, in that order; after the two seats, each
kind reads its own (§1.2, §1.3, §2.2, §2.3): an Underlay, a stored value,
inputs by name. Fewer than two positional seats, or a Contact seat with a
default, is a Declaration Failure at class use; an input named like a
seat is refused at linking, nothing changed. Reports and Operations of a
Relation take the Link alone and belong to it, one Link per Agent:
`charlie.Knows.capacity`. So do its plain values and its other class and
static methods, as an ordinary Tag keeps them on the class. Across a
Relation and its extensions a name is a line (below) or a member of the
Link, never both, and a static method is never `@Secret`: Declaration
Failures at class use. Extensions declared side by side meet only on an
Agent, and a clash between them is a Composition Failure when the Agent
gains the second. A Pair Action, an Operation or another class method may
be a generator function or a coroutine function: its body runs later, when
iterated or awaited, and the kit takes each step behind the Link's doors
(below). An async generator function, a generator-based coroutine
(`@types.coroutine`), and a generator or coroutine function that is a
Record, a condition, an Imprint, a teardown or a Report builder are
Declaration Failures at class use: the event loop closes an async
generator itself, outside any wrapper, and the kit runs the others itself
and never iterates or awaits what they return.

**Linking** follows ordinary Tagging (§0.6), with the Pair receiving the
Relation's Agent-scope declarations. Each missing Base takes its turn
before its Shape: its Gate runs, its Gains arrive in declaration order,
its Imprints run, and only then does the Contact enter that Link's Field.
Posts judge completed admission; a broken Pair promise or Contact promise
raises without undoing membership.

A Gate refusal leaves that turn unapplied. A failed Gaining or Imprint
keeps the Pair's actually acquired Gains, including Posts, on a Rogue
Pair; the Contact does not enter the unfinished Link. Earlier completed
Base linkings and independent Taggings remain. Applying the Link again
retries the unfinished work with a fresh Gate, Gainings and Imprints;
already completed turns are no-ops. Applying the same Link to the same
Contact during its own training is also a no-op, so reciprocal Imprints
do not recurse forever. A Shape that needs an unfinished Base is refused,
as in ordinary Tagging.

A later failure in a call on either endpoint or another Agent does not
undo completed linkings or acquired Gains. The kit never restores and
replays Pair Layers to imitate a transaction. A Contact who was not an
Agent becomes one when admitted; she receives membership and published
lines, not the Pair's private Contributions. The kit never checks the
linking Agent's membership or soundness: a Gate that cares says so.

**The Pair** is reached through a Link while that Link admits its Contact:
`charlie.Knows[ruth]`, live, holding Records, Actions, conditions read by
name, and secrets that resolve only inside the Link's own functions.
The Link's own training and Rip can also read its Pair during their turn.
An unfinished attempt keeps partial Pair Gains privately for retry; a
Ripped Base Link has no fresh Pair view even when a Shape Link keeps the
shared Pair. On a Link this replaces the Agent-bound view of §1.7.
`bool(charlie.Knows[ruth])` is the Pair's own
contract. The Link's sound population, `for contact in charlie.Knows`,
holds the Contacts whose own contract holds and whose Pair holds;
`~charlie.Knows` the rest. A broken Pair never makes the Contact
defective anywhere else. A Link marked `@Flag` answers its words on the
Pair, never on the Contact. The Tags a Pair carries are the kit's own:
`Tags(pair)` lists none, and every Tag-level act on one is a Composition
Failure. A Pair held by a name after it ended, or after its Agent or
Contact is gone, keeps its stored Records as they were, and its functions
answer with a Resolution Failure. A Pair's members have ordinary names: a
Relation declares no special methods, and a Pair's teardown is a `@Rip`.
The view of the declaring Tag shows the Link it granted:
`Social[charlie].Knows is charlie.Knows`.

**Bases.** A Relation's Bases are Relations of the same declaring Tag or
of its Bases, resolved per Agent: with `class Trusts(Knows)`,
`charlie.Trusts` is a Shape of `charlie.Knows`, never of Bob's. Linking
through a Shape Link links through its Base Links first, and a Link and
its Base Links share **one Pair** for each Contact, its members overlaid
in the order its Layers reached it, as on any Agent (§1.2). A fresh Pair
receives all current Layers of a Base Link before the Shape Link's turn;
that later Shape Layer overlays them. An extension arriving after the
Shape's training instead overlays the Shape. The kit does not reorder or
replay existing Gains to erase these different histories. A successful
linking or extension gives the Pair every required Layer; a failed attempt
can leave partial Gains. Unlinking a Base Link leaves the Contact in any
Shape Link she holds, with the shared Pair retained while that Shape
holds her (§0.7). An ordinary Tag is never a Base of a Relation, and a
Relation or a Link is never a Base of an ordinary Tag: a Link that writes
a Tag on its Contact says so in an Imprint.

**Extending a held Link.** A Shape of the declaring Tag may extend its
Base's Relation by name, `@Link class Knows(Social.Knows)`, naming it as
its only Relation Base; a same-name Relation that does not, or that names
a Shape of it or a second Relation, is a Declaration Failure. When an
Agent gains the Shape, its Link gains the new Layer, keeping its
identity, its Field and its history, and the Layer applies to every Pair
it holds, one Pair at a time, during that Link's Gaining. Each Pair takes
its own Gate, ordered Gainings, Imprints, admission and Posts. If Ruth's
training completes and Bob's later Record fails, Ruth keeps her completed
training and Bob keeps his partial Gains. The declaring Shape has not
completed, but its acquired Link Layer remains; retrying the Shape finishes
the missing Pair training without repeating completed turns. Later linkings
also receive the Layer.

An extension requested during another linking follows the same rules as
ordinary Tagging. It may use completed Bases, but cannot train a Shape
over a Base that is still in training. That refusal leaves earlier
completed work and acquired Gains in place. There is no separate rollback
rule for an extension, and no replay of surviving Layers after failure.

**Seen by the Contact, or in-house.** A `@Public` Pair member is a line
onto the Contact: `ruth.Greet()` runs the Pair's `Greet(charlie, ruth)`,
and a `@Public` Pair Record reads live and read-only on her. A `@Public`
Report or Operation of the Link is published onto its Contacts as §1.5
says. A line is installed at the linking and sticky; when two Links
publish one name onto her, the latest linking is what she sees, with the
usual Overwrite Warning; once unlinked, a line raises a Rogue Access
Failure. A published Pair Record over her own Action is refused, as an
Action line over her Record is. A Pair condition or Imprint is never a
line: `@Public` on one is a Declaration Failure. Nothing unpublished of
the Link reaches her, her own views included. A `@Secret` member, of the Pair or of the
Link, belongs to the Link's Agent alone: it answers only inside the
Agent's own code, the Link's functions included.

**The doors.** A Link's functions run inside the composition door of the
Link's Agent and of the Pair, never the door of the Contact they are
about, on every path: a line she calls, a Pair function called from her
own code, a linking she asks for from her own Action, an Operation of the
Link called with her, by position or by name, and a teardown her own
deletion runs, included. The doors hold for as long as the Link's code
runs; what it hands back to run later, a closure or a generator made
elsewhere, runs under the doors of whoever runs it. A generator or a
coroutine the Relation itself declares takes every one of its steps behind
them (the Agent's and the Pair's open, every Contact's shut, her async
door too), and between two steps every door is as the caller left it; a
task its coroutine hands to the event loop is such a closure. A Link's Report is
built with every Contact's door shut, since its value is kept and served
to all. A Relation's static methods are plain functions the kit never
wraps. Otherwise doors follow the call, as §1.5 says for every Agent:
when a Contact's own Action calls into a Link about another Contact, her
door is open beneath that call, as it is for any code she calls.

**One direction.** A Link points from its Agent to its Contacts. Nothing
public on a Contact names an Agent who links her: her `Tags`, `Outline`,
format specs, contract and keywords never list a Link, and `ruth.Knows`
is her own Link or nothing. Nothing public on a Link or a Pair names its
Agent, and the kit holds that Agent weakly, so a Link never keeps it
alive. `isinstance(ruth, charlie.Knows)` answers, asked with the Link in
hand, and a Contact's history keeps a Link weakly: a living Contact never
keeps the Link of an Agent that is gone, save one. For each name a Link
published onto her, her record of that line keeps the last Link that
published it: at most one Link per name, never one per Agent. A Link that
should answer back says so in its own Imprint.

**Ending.** `del charlie.Knows[ruth]` ends her membership; the Link's
teardowns run with `(charlie, ruth)`; the Pair ends unless another Link
of the same Form still holds her, and then what the Ripped Link gave the
Pair stays, sticky. `del charlie.Knows[:]` unlinks every Contact in that
Link's Field; a Contact in a Shape Link remains there, with her Pair
retained. A Contact's deletion unlinks her,
the teardowns running with the live Agent; the Agent's deletion ends its
Links after its own teardowns, Shape Links first, with the dying Agent in
the first seat; `At_Exit` ends them at interpreter exit (§3.2). When the
Agent cannot be reached, the Pair ends silently. Each Pair's teardowns run
at most once, a self-link included. A Link held by a name after its Agent
is gone has an empty Field, linking through it is a Composition Failure,
and `k[ruth]` and `del k[ruth]` are Resolution Failures.

**The Relation itself** is a template with no Field, declared once: in
its declaring Tag's body, under its own name. Binding it again, in
another Tag or under another name (`Knows = Social.Trusts`), is a
Declaration Failure while that Tag lives; a Shape extends it by naming it
as its only Base.
Like any Tag, it answers its own Reports and Operations, with no Agent
behind them; `@Secret` binds on each Link, where an Agent exists. Every
Tag-level act
on it (apply, `in`, `isinstance`, walk, `len`, truth, `~`, `[:]`, `[x]`,
the population operators, `del`) is a Composition Failure that points to
a Link: "Knows is a Relation: link through an Agent". `Social.Knows |
None` keeps the language's own union. A Relation is no Tool kind, never a
Pin (in either decorator order), never a Pin's Target, and a `@Link`
inside a `@Pin`, or in a Tag marked a Pin later, is refused: Links between
Tags need their own receiver rule. One Agent's Link is never a Pin's
Target either.

Peers at the same level are not a Link: they are members of one ordinary
Tag whose gate keeps its Field at two, or Contacts of one Link held by the
Agent that stands for their pair.

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

**Python profile.** Assertion-style conditions require assertions enabled.
Python removes `assert` under `-O`, `-OO` or a nonzero `PYTHONOPTIMIZE`
setting; an assert-only condition then returns `None` and holds. For a
requirement that must also be checked in those modes, return a Boolean
explicitly, such as `return agent.spellbook is not None`.

TOP does not coerce truthy and falsy values: a Record of `0` spell slots is
a real value, not a failure. `return agent.spell_slots` raises a Contract
Failure telling you to write the comparison you mean. The absence of a
return is permission: a condition is a restriction, and saying nothing
permits. Legal until written into law.

> Contracts should be picky.
> The Layer's Lawyer

## 2.2 Preconditions: the gate

A Precondition inspects the **incoming materials**: may this Agent, with
these inputs, enter this Tag? It runs at step 1 when **that Tag's turn**
arrives. Missing Bases take their own turns first, so a later Shape's Gate
sees the Records, Actions, membership and Imprints of every Base that
completed. An active Tag's Gate is not re-asked; it already let its Agent
in.

A Shape cannot waive a missing Base's Gate: the Base must pass before the
Shape has a turn. A same-named Precondition declared by the Shape controls
the Shape's own Gate and the condition visible afterwards. `@Underlay`
deliberately calls the condition visible before the Shape as part of the
Shape's Gate.

Preconditions, like Record builders and Imprints, receive application
inputs by name:

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

Preconditions overlay **backward** within the current Tag's Gate. A Shape
may ask for less on its own turn, but it does not rewrite a Base's earlier
turn. Override freely; compose with `@Underlay` when the Shape should ask
the prior visible condition again:

```python
class Founder(Guild):
    @Pre
    def Dues_Paid(agent):
        return True                # the Founder's own Gate is open

class Apprentice(Wizard):
    @Pre
    @Underlay
    def Level_Over_Zero(agent, base):
        assert agent.mentor        # also needs a mentor
        return base()              # then the Base's gate
```

An unpaid fresh Agent still fails `Guild` before `Founder` has a turn. If
the Agent is already in `Guild`, applying `Founder` asks only Founder's
Gate; `Guild` is not re-asked.

This is also how **synergy** is expressed: a feat that requires two other
Tags gates on both.

```python
class War_Caster(Tag):
    @Pre
    def Is_A_Caster(agent):
        return agent in Wizard
```

## 2.3 Imprints: the writing

An Imprint performs the training work of tagging: it runs at step 3, after
Gainings and before FieldAdding, in declaration order, with application
inputs by name. Earlier Gains are available; this Tag's published Reports,
Operations and Agent-bound view are unavailable through the Agent until
admission. Previously active Tags retain their ordinary access rules.

```python
class MI6(Tag):
    @Imprint
    def SetUp(agent, code):
        agent.code = code
        agent.status = "Full"
```

An Imprint may apply further Tags to the same Agent; those are independent
Taggings. Applying the same Tag to this Agent while its training is already
underway is a no-op, rather than recursive training. If an Imprint fails,
the call raises its named Imprint Failure. Actual Gains and completed
Taggings stay, but the unfinished Tag is absent. Another `Tag(agent)` makes
a fresh attempt, including its Gate, Gainings and Imprints.

## 2.4 Postconditions: the promise

A Postcondition inspects the **finished product**. Every visible
Postcondition runs at step 5, **once per call, after the whole Form**, so a
Base may promise what its Shape delivers. Postconditions take no inputs:
they judge the Agent, not the materials.

Its definition is acquired at its declaration position during Gainings.
If a later Gain or Imprint fails, the acquired Post remains on the Rogue and
participates in current contract queries and published-member guards. This
does not establish membership in the unfinished Tag. A Constant Post retains
its protection there just as it does after Rip.

Every visible Postcondition is re-checked at each later tagging boundary,
so a later completed Tagging can report an earlier Tag's broken promise.
That is a Postcondition failure, not a Gate refusal. Conditions
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

A Constant Post is the explicit exception: its implementation cannot be
overridden, even with an Underlay, or deleted. Strengthen the contract by
adding an independently named Post; the original check remains applicable.

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

The plain loop is the working population, and `len(Wizard) > 0` asks whether
it contains a member. A broken Agent does not stop being a member (`in`), does not
leave `Wizard[:]`, and waits in `~Wizard` for repair or Rip. Membership and the loop deliberately disagree for it:
the loop is the line, and a defective product is off the line.

`~` reads "broken", never "not". Broken twice is still broken, so `~`
absorbs: `~~Wizard`, `~~~Wizard` and any longer run are `~Wizard`, the
same defective population (STEP-SPEC-38).

**Populations combine** (STEP-SPEC-13). `|` is either, `&` is both, `-`
is the left without the right, on any population: a whole Field, the
sound view, the defective view, or a combination. A Tag in an operator
seat is its sound population, as it is in the loop; `Wizard[:] |
Fighter[:]` is everyone who is either; the levels mix. The result is a
lazy view that reads its Fields when walked, keeps application order
within each side, answers `in`, `len`, truth and iteration, and takes no
`~`: `~(Wizard | Fighter)` is refused, and `~Wizard | ~Fighter` is the
defective population of either. A Tag with anything that is not a
population keeps the language's own class union (`Wizard | None`).

```python
for c in Wizard | Fighter:            # sound in either, each once
for b in Wizard & Fighter:            # sound in both
for u in (Wizard[:] | Fighter[:]) - Sworn:   # anyone with a role who has not sworn
```

**A population walk** (STEP-SPEC-35) checks current Field membership at
each member's turn. A member Ripped before its turn is skipped. If the
same Agent or Tag is tagged again before its turn, it belongs again and
must not be skipped merely because it was previously Ripped. TopKit's
saved-turn ordering and lazy operand timing are documented in its
[Field guide](../TopKit/FIELDS.md).

**A condition is read on the Agent by its name** (STEP-SPEC-14).
`agent.Has_Book` is `True` while the promise called `Has_Book` holds and
`False` when it does not: the language's boolean, computed on read, never
stored, never callable. A Postcondition answers before a Precondition of
the same name; a condition that raises reads `False`; a non-boolean is a
Contract Failure on read, as always. Because the name is read on the
Agent, a condition may not share its name with an Action, a Record, a
member the host defines or a value the Agent already holds: the tagging
is refused at the door with a Composition Failure, and so is an Action or
a Record laid over a condition's name. Nothing is silently shadowed. A
pinned Tag reads its own conditions the same way (`Wizard.Has_Members`).
A condition that outlived its Tag (§0.7) still reads by name until the
author ends it.

An ordinary object Agent with no visible Postcondition is truthy: it has
no broken promise. A host's `__len__` keeps answering `len(agent)`; its
length never answers the Agent's truth. Thus an empty Agent whose visible
promises hold is still truthy.

The Agent's `__bool__` protocol is reserved for that contract question.
A Tag cannot gain or delete it, including through a Record, Action or
published Report/Operation; a Declaration Failure refuses such a binding.
An ordinary Python host defining `__bool__` directly or by inheritance is
refused as a Target with a Composition Failure before Gates, Gainings or
Target mutation. Its truth is not evaluated or replaced by Tagging.
Objects held in Records retain their own truth. A Tag follows the same
contract rule: `bool(Tag)` checks its own visible Posts received through
Pins, independently of its members' Posts. No Posts means true even before
any Pin or with an empty Field. A Pin can explicitly require sound members
with a Post returning `len(tag) > 0`. Existing lengths and set algebra keep
their population meanings (§0.8).

## 2.6 Naming the culprit

A failed check raises a failure that **carries the check's name**, as a
subclass of the general failure: the Precondition declared as
`Is_A_Caster` refuses with `TagPreconditionError.Is_A_Caster`, an
Imprint called `Arm` fails with `TagImprintError.Arm`, a Postcondition
called `Has_Book` with `TagPostconditionError.Has_Book`. The marks are
the short spelling of the same classes, so a program catches a refusal in
its own words:

```python
try:
    War_Caster(bruk)
except Precondition.Is_A_Caster:      # this one refusal
    ...
except TagPreconditionError:          # any refusal
    ...
```

Rules:

1. The named failure **is** the general failure (`issubclass`), so a
   handler for the general one still catches everything. `error.name` is
   the check's name; the general failure's `name` is `None`.
2. A name exists from the moment its Tag class exists, not from its first
   tagging. A name that no Tag declared is an error at the `except` line
   (`AttributeError`), never a handler that silently fails to match.
3. Names are per kind, not per Tag: two Tags that each declare `Ready`
   share `Precondition.Ready`. A program that needs to tell them apart
   reads `f"{agent:contract}"` or names the checks differently.
4. A check that raises instead of returning `False` is named the same way.

`bool(agent)` is the verdict on a finished Agent. The `Contract` namespace
names the promise that broke:

```python
Contract.Postconditions(agent)   # promises hold, or raise naming one
Contract.Preconditions(agent)    # gates still hold, or raise
Contract.Conditions(agent)       # both, Pre then Post
Contract.Status(agent)           # {condition: holds?}, never raises
print(Contract.Display(agent))
# Hero[Wizard] contract:
#   Pre:
#     OK  Level_Over_Zero
#   Post:
#     XX  Has_Spellbook
```

## 2.7 Necessary to enter, necessary to stay

`@Pre` and `@Post` stacked on one function make it a **condition**:
checked at the door as a Precondition and kept as a Postcondition. It is
one body, named once, and it fails under both names:

```python
class Elf(Tag):

    @Pre
    @Post
    def Alive(agent):
        return agent.alive


Elf(dead)                     # refused: Precondition.Alive
Elf(ari)                      # in; and from now on Ari must stay alive
```

Being alive is necessary to become an Elf and necessary to remain a sound
one; it is not sufficient, since other living things are not Elves. A
condition says *necessary*; membership says *is*.

The order of the two marks changes nothing: `@Post` above `@Pre` is the
same condition. The two marks are its only spelling, so the page shows
that it is a gate and a promise.

The two failures keep their two names: `Precondition.Alive` at the
door, `Postcondition.Alive` afterwards. A program repairs the two
differently. One is an Agent that may not come in; the other is an Agent
already in and now broken.

## 2.8 Writing a check

A Post can require an Agent to *have* a named Contribution (§1.1).
Separate presence from its value:

- Is it there at all? `"spell_slots" @ agent` tests the name's presence.
  Stored `False`, `None` and `0` all count as present.
- Does it have a particular value? `agent.spell_slots > 0` tests its value.

A Post requiring the name can write `return "spell_slots" @ agent`, or `assert "spell_slots" @ agent`.
Presence guarantees neither successful value access, callability nor
successful behaviour; express those requirements separately.

---

# Ring 3 · Lifecycle

## 3.1 Rip protocols

An Imprint trains before admission; a `@Rip` Action runs when the Agent
leaves the Tag's Field. It is also an ordinary, callable Action. Unfinished
training never entered the Field and therefore does not run Rip
automatically (§0.6).

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
There are three tiers. The implementation provides the first and the
third; the program writes the second.

| Tier | Guarantee |
| --- | --- |
| **Finalizer** (`__del__`) | best effort: when the Agent is collected, its teardowns run, then its `__del__` Layers; at interpreter exit only the `__del__` Layers run; the language may not run finalizers at shutdown or inside reference cycles |
| **`del Tag[agent]` in a `finally`** | guaranteed: the language runs a `finally` whenever its block ends, by finishing or by raising |
| **`At_Exit(agent)`** | opt-in: teardowns also run at normal interpreter exit; registration is weak |

Every teardown runs at most once, whichever tier reaches it first. The
finalizer and `At_Exit` also end the Agent's Links (§1.10), after its
own teardowns, its exits from Links that hold it included.

**A block that holds a Tag** (STEP-SPEC-31) is a tagging and a Rip,
joined by the language's own `try` and `finally`. The rule: **tag before
`try`, Rip in `finally`.**

```python
Sentry(guard)              # the guard joins Sentry
try:
    guard.Patrol()
finally:
    del Sentry[guard]      # the guard leaves, even if Patrol raised
```

A Gate refusal raises before the `try`, so the block never runs and the
refused Tag is absent; earlier completed Base Tags stay. A Gaining or
Imprint failure also raises before the `try`: acquired Gains remain, but
the unfinished Tag has no membership to Rip. A broken Post is reported
after admission, so that Tag stays despite the failure (§0.6). The program
handles that failed Tagging separately if it needs cleanup; this `finally`
only covers the block entered after successful Tagging.
A Rip in a `finally` that fails raises, as every Rip does (§3.1).
If the block was raising too, the language keeps the block's error inside
the Rip's failure, as its context, and shows both.
TOP adds nothing to this. Each step is a line the program writes: a
block that should leave a Tag the Agent already carried checks first
(`was_sentry = guard in Sentry[:]`), and a block that should take away a
Base its Shape pulled in Rips the Base too.

TOP assigns `with` no automatic Tagging or Rip meaning. Ordinary Python
context protocols remain ordinary Contributions or host behavior: a host,
or an Agent with `__enter__` / `__exit__` (or their asynchronous forms),
may still follow `with` without changing membership unless its own code
does so explicitly.

**The Agent's own finalizer is a member in Layers** (STEP-SPEC-18). The
host's `__del__` is its first Layer, found as the language finds it. A
Tag's `__del__` replaces the Layers beneath it, or with `@Underlay`
extends them; `@Delete` removes them. With nothing stated, the host's own
`__del__` runs, as it would for the untagged object. The Layer beneath a
`__del__` is always callable, and where there is nothing it does nothing.
Deletion runs in that order: every teardown still due runs, then the
`__del__` runs as the Overlay shows it, top Layer first; both run inside
the composition door (§1.5). A `__del__` never stops a teardown:
replacing the Layers replaces only them, and an interrupted teardown
does not skip them. At interpreter exit only the Layers run; teardowns
at exit are `At_Exit`'s. An error raised by a `__del__` Layer is reported
as the language reports any finalizer's; the teardowns stay best effort
and silent. `@Rip` on a `__del__` is a Declaration Failure: a `__del__`
Layer already runs at deletion. The language calls `__del__`, not the
program: in Python, `agent.__del__` reads the kit's finalizer, and
calling it by hand runs the teardowns while the Agent is still a member.

```python
class Lantern:
    def __del__(self):
        log.append("wick out")             # the first Layer

class Carried(Tag):
    @Rip
    def Put_Down(agent):
        log.append("put down")             # a teardown: runs first

class Enchanted(Tag):
    @Underlay
    def __del__(agent, underlay):          # a Layer over the host's own
        log.append("spell fades")
        underlay()

lamp = Lantern()
Carried(lamp)
Enchanted(lamp)
del lamp
assert log == ["put down", "spell fades", "wick out"]
```

---

# Ring 4 · Edges

What TOP does not promise, stated so nobody has to discover it.

- **Nominal type.** `type(agent) is Host` may be false after tagging. The
  type's name is unchanged and `isinstance(agent, Host)` is true. Code that
  keys on exact type identity is outside the guarantee. A pinned Tag's
  metaclass may be wrapped the same way; its Shapes' is not.
- **Copying and pickling.** Cloning an Agent is domain work: build a new
  Target and apply its Tags again (`Tags(agent)` lists them). A Python
  implementation refuses `copy.copy` explicitly rather than aliasing state.
- **Threads.** One Agent, one thread. Fields are not synchronized.
- **Python optimization.** Assertion-style conditions need assertions
  enabled; §2.1 describes optimized execution and return-based checks.
- **Host descriptors.** A Record cannot share a name with a host property
  or slot; the Tagging fails with a Composition Failure.
- **Raw side effects.** A failure does not roll back completed Taggings,
  acquired Gains or Imprint effects (§0.6). The bounded restoration for
  failed mechanical host preparation preserves the host's bindings (§0.1);
  it cannot undo an in-place mutation of a pre-existing mutable value or
  effects elsewhere in the program. Preconditions and Record builders are
  observational authoring rules, not a sandbox for such effects.
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
| **Tag Composition Failure** | Contributions cannot form the Overlay: cross-kind collision, Record over a host descriptor, a Record builder or teardown that failed, a Target that cannot carry state. | before FieldAdding: current Tag absent, acquired Gains and earlier turns stay; after admission: membership stays; a teardown failure is reported after its Rip ends membership |
| **Tag Resolution Failure** | A required Underlay, view, or membership is unavailable. | use refused; during Tagging, follows the current phase boundary |
| **Tag Rogue Access Failure** | A Rogue Agent reached a published member of a Tag it has left or never entered. A Resolution Failure, and a TOP failure only: never dressed as a host-language attribute failure. | use refused |
| **Tag Precondition Failure** | A Gate refused the incoming Agent. | that Tag does not apply; earlier turns stay |
| **Tag Imprint Failure** | An Imprint failed before FieldAdding. | acquired Gains and completed Tags stay; unfinished Tag absent |
| **Tag Postcondition Failure** | The finished Agent breaks a promise. | Tags stay, Agent defective |
| **Tag Contract Failure** | A condition returned a non-boolean. | Gate: that Tag does not apply; quality check: Tags stay, Agent defective |
| **Overwrite Warning** | An independent Tag replaced a visible Action or Record without an Underlay. | diagnostic |
| **Contract Warning** | A Tag replaced another Tag’s visible Postcondition without an Underlay (Base, Shape, or independent Tag). | diagnostic |

---

# 🧰 Conformance obligations

A conforming implementation provides, ring by ring:

**Ring 0**
- stable object identity under tagging, and preserved host behaviour;
- membership (`agent in Tag`) gained Base-first and thereafter independent,
  with a has-been check that survives Rip;
- non-owning, identity-indexed, iterable Fields;
- Base-first Form application, each Base once, active reapply a no-op;
- the five-step tagging sequence: each missing Tag's Gate, Gainings,
  Imprints and FieldAdding, then Posts once after the completed Form;
  failed Gainings or Imprints leave acquired Gains without that Tag's
  membership or history; earlier completed Tags stay, retry starts fresh,
  and current Posts decide members' deficiency;
- Rip: one membership ends without cascade, while acquired contributions
  and conditions stay; the author ends a condition with a guard or
  `Contract.Delete` from the `@Rip` protocol;
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
- Flags: opt-in keyword Tags searchable from the Agent's side by name, by
  the words they list, and by class, a word never standing for
  membership, colliding in either order with a host or a Tag's Action
  that already answers `in`, never matched for ordinary Tags;
- Pins: opt-in Tags whose Targets are Tags, the pinned Tag as Agent under
  every Ring 0 act, the receiver rule (Records as Reports, Actions as
  Operations), Fields never mixed, the Tag's Tag-scope declarations as
  host members (Underlay, stored seat) with Agent-scope and protocol
  names refused, `@Secret` as Pin-private state, `@Public` as publication
  onto the Field, Flag Pins as keywords by string;
- published members answering members only, and only sound ones: a Rogue
  Access Failure on a Rogue Agent, the broken promise by name on a
  defective one, open again on membership or repair;
- `@Pre` and `@Post` stacked on one function as one condition, in
  either order;
- populations combined with `|`, `&` and `-` at every level, lazily, a
  Tag in an operator seat meaning its sound population;
- every condition read on the Agent by its name as a plain boolean, with
  a condition's name refused to Actions, Records and host members;
- Delete; the three access forms, with Agent-bound views as read-only
  snapshots requiring active membership;
- Links: a `@Link` Relation granting each Agent a distinct Tag held under
  its name, read-only and in a closed slot; two seats, the Agent then the
  Contact; linking as a tagging of the Contact with the Pair as receiver;
  one Pair per Contact across a Link's Form, sound on its own; Relation
  Bases resolved per Agent; extension of a held Link over every Pair;
  `@Public` lines onto the Contact and `@Secret` in-house; the doors of
  the Agent and the Pair, never the Contact's; nothing on a Contact, a
  Link or a Pair naming the Link's Agent; every act on a Relation refused.

**Ring 2**
- strict boolean conditions; each Tag gating when its turn arrives, with
  inputs; Imprints before FieldAdding, with inputs; Postconditions once per
  call after the whole Form, re-checked at every later boundary, without
  inputs;
- the contract direction, with weakened Postconditions diagnosed;
- defective Agents: contract truthiness; the plain loop as the sound
  population, `~Tag` the defective one, `Tag[:]` everyone, membership
  unchanged; a namespace that names the culprit.

**Ring 3**
- `@Rip` protocols run after membership ends, once, composed, failures
  reported; the three deletion tiers, the finalizer and `At_Exit` from
  the implementation, and the guaranteed one written by the program, a
  Rip in a `finally`; the Agent's `__del__` as Layers of its Overlay,
  run after the teardowns, and alone at interpreter exit;
- an Agent's deletion, and `At_Exit`, ending its Links after its own
  teardowns, the dying Agent in the first seat; a Contact's deletion
  unlinking her; each Pair's teardowns at most once.

**Everywhere**
- the failure types above, distinct and named.

An implementation may choose runtime type composition, generated wrappers,
proxies, trait machinery, or static code generation. Those are its business.
TopKit is the Python reference; any gap in TopKit is TopKit's to fix, not a
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
