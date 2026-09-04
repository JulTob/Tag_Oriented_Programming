# The TagKit Guide

*Tag-Oriented Programming for people. Read this before the Specification.*

This guide teaches TOP by building one thing: a character sheet the way a
tabletop game builds it. Species, class, background and feats are separate
choices, and the sheet is what they compose. Every code block runs, in
order, on Python 3.10 or later, with nothing installed but TagKit.

If you want the laws, read [the Specification](../spec/SPECIFICATION.md).
If you want to see the whole thing at once, run
[`examples/dnd_character.py`](../examples/dnd_character.py). This document
is for learning, one pattern at a time.

---

## The one idea

A hero is one character. Over a game she becomes a Human, a Wizard, a Fighter,
a Harper. She stays the same hero. In TOP you write each of those meanings
as a **Tag**, and you **apply** Tags to an object you already have. The
object keeps its identity. Its meaning grows.

Two words from Spanish say the whole model. A Tag is something you *are*
(*ser*): a noun, durable. A **Record** is how you are *right now* (*estar*):
an adjective, changeable. Wizard is a Tag. Hit points are a Record.

```python
from TagKit import (
        Action, Contract, Delete, Flag, Form, Imprint, Keyword, Operation,
        Outline, Post, Pre, Public, Record, Report, Rip, Scope, Secret, Tag,
        Tags, Underlay,
        TagCompositionError, TagPostconditionError, TagPreconditionError,
        )


class Character:
    """The host: ordinary Python. TOP never asks you to change it."""

    def __init__(self, name, level=1):
        self.name = name
        self.level = level
```

---

## Ten minutes

### A Tag is a category. Applying it is membership.

```python
class Wizard(Tag):
    pass


ari = Character("Ari", level=3)
Wizard(ari)

assert ari in Wizard                 # Ari is a Wizard now
assert list(Wizard) == [ari]         # the Field: everyone who is one
assert Wizard                        # "is anyone a Wizard?" (yes)
```

An empty Tag is already useful. It defines a category and a population, and
that is the primary thing a Tag does. Everything else is extra.

### Tags give the Agent things: Records and Actions

```python
class Wizard(Tag):

    @Record
    def spell_slots(agent):
        return 2                          # built once per Agent, stored on it

    def Attack(agent):                    # a plain method is an Action
        return f"{agent.name} casts a spell"


ari = Character("Ari", level=3)
Wizard(ari)

assert ari.spell_slots == 2
assert ari.Attack() == "Ari casts a spell"

ari.spell_slots -= 1                      # a Record is an ordinary attribute
assert ari.spell_slots == 1
```

Notice the first parameter is `agent`, not `self`. A Tag's methods act on
*someone else's* object. The name is your choice; the position is the rule.

### Tags compose. The last one applied is what you see.

```python
class Fighter(Tag):

    def Attack(agent):
        return f"{agent.name} "


Fighter(ari)

assert ari.Attack() == "Ari cuts with a blade."       # Fighter came last
assert ari.Wizard.Attack() == "Ari casts a spell"   # the view after Wizard
```

`ari.Wizard` is a **view**: the sheet as it was right after Wizard applied.
It never changes, whatever comes later. `Wizard[ari]` is the same view by
class, exact even if two Tags share a name.

### A Tag can be taken away. What it gave stays.

```python
del Fighter[ari]                          # Rip: leave the Field

assert ari not in Fighter
assert isinstance(ari, Fighter)           # ever a Fighter, always a Fighter
assert ari.Attack() == "Ari cuts with a blade."   # sticky: the Action stays
```

That last line surprises people. TOP calls this a **Rogue Agent**: it has
what it learned, but no active membership. If a Tag must clean up after
itself, it says so with `@Rip` (pattern 9).

That is the whole kernel. The rest of this guide is patterns.

---

## Patterns

Each pattern has the same shape: **when you want** something, **write**
this, and **watch out** for that.

### Pattern 1 · A category with no code

**When you want** to say what something *is*, so other code can ask.

```python
class Undead(Tag):
    pass


ghoul = Character("Ghoul")
Undead(ghoul)

for creature in Undead:                 # every sound member
    creature.level += 1

if not Undead:                          # nobody is Undead: nothing to do
    pass
```

**Watch out.** `for creature in Undead` walks the *sound* population: the
members whose promises hold (pattern 6). `Undead[:]` is everyone.

### Pattern 2 · State that belongs to the role

**When you want** each Agent to carry its own value, fresh, set by the Tag.

```python
class Wizard(Tag):

    @Record
    def spell_slots(agent):
        return 2

    @Record
    def spellbook(agent):
        return []                       # a new list for every Agent


a = Character("A")
b = Character("B")
Wizard(a)
Wizard(b)

a.spellbook.append("Light")

assert b.spellbook == []                # not shared
```

**Watch out.** A Record builder runs once, when the Tag applies. It is not a
property; it does not recompute. Reapplying an active Tag does nothing, so
a Record is never silently reset. To reset, Rip and apply again.

### Pattern 3 · Pile things up from several Tags

**When you want** a value that several independent Tags contribute to: a
spell list from species, class and background; hit points from class and a
feat.

Declare a second parameter on the builder. It receives what is already
stored under that name, or `None` the first time.

```python
class Elf(Tag):

    @Record
    def spells(agent, stored):
        return (stored or []) + ["Light"]


class Wizard(Tag):

    @Record
    def spells(agent, stored):
        return (stored or []) + ["Magic Missile", "Shield"]

    @Record
    def hit_points(agent, stored):
        return (stored or 0) + 6 * agent.level


class Tough(Tag):

    @Record
    def hit_points(agent, stored):
        return (stored or 0) + 2 * agent.level


ari = Character("Ari", level=3)
Elf(ari)
Wizard(ari)
Tough(ari)

assert ari.spells == ["Light", "Magic Missile", "Shield"]
assert ari.hit_points == 18 + 6
```

You write the merge. `stored + new`, `max(stored, new)`, `stored | new`:
whatever the domain means. There is nothing to configure.

**Watch out.** A builder *without* the second parameter replaces. If it
replaces a Record that an unrelated Tag put there, TagKit warns, because
something another meaning relied on was overwritten.

### Pattern 4 · Extend behaviour instead of replacing it

**When you want** a later Tag to add to an Action, not overwrite it.

```python
class Person(Tag):

    def Attack(agent):
        return "Attack!"


class Elf(Person):                      # Elf is a Shape of Person

    @Action
    @Underlay
    def Attack(agent, underlay):
        return "With elven grace, " + underlay()


class Paladin(Person):

    @Action
    @Underlay
    def Attack(agent, underlay):
        return underlay() + " For the oath!"


ari = Character("Ari")
Elf(ari)
Paladin(ari)

assert ari.Attack() == "With elven grace, Attack! For the oath!"
assert ari.Elf.Attack() == "With elven grace, Attack!"
```

`@Underlay` hands you the Action as it was just before yours. It is captured
when the Tag applies and never changes, so every view stays true.

`class Elf(Person)` makes Person a **Base** of Elf: applying Elf applies
Person first. `Form(Elf)` lists that order; `f"{Elf:form}"` prints it.

**Watch out.** An Action that calls *another* Action through the Agent
(`agent.Attack()` inside `Combat`) uses whatever is visible *now*, not what
was captured. Underlay is for the same name; the Agent is for the current
sheet.

### Pattern 5 · Gate the door

**When you want** a Tag that not everyone may take. Preconditions inspect
the incoming Agent before anything changes.

```python
class Wizard(Tag):

    @Pre
    def Can_Study(agent):
        return agent.level >= 1


class War_Caster(Tag):

    @Pre
    def Is_A_Caster(agent):             # synergy: needs another Tag
        return agent in Wizard


bruk = Character("Bruk", level=2)

try:
    War_Caster(bruk)
except TagPreconditionError:
    pass                                # Bruk is no caster: nothing changed

assert bruk not in War_Caster

Wizard(bruk)
War_Caster(bruk)                        # now it takes
```

Inputs can travel with the tagging. `MI6(bond, code="007")` hands `code`,
by name, to every Precondition, Record builder and Imprint of that call
that has a parameter called `code`. The usual use is a Record that simply
keeps the input:

```python
class MI6(Tag):

    @Pre
    def Has_A_Code(agent, code):
        return code is not None

    @Record
    def code(agent, *, code):           # keyword-only: "this comes from the call"
        return code


bond = Character("Bond")
MI6(bond, code="007")

assert bond.code == "007"
```

Read the `*` as a blank space. A Record's signature has three places:
the Agent, what was stored (pattern 3), and what the call brings. When
there is nothing stored to read, the star holds the empty seat, so
`def code(agent, *, code)` says "agent, nothing stored, then `code` from
the call". Writing `def code(agent, code)` would put `code` in the stored
seat; TagKit refuses that at tagging and shows the spelling above.
Preconditions and Imprints have no stored seat, so there
`def Has_A_Code(agent, code)` is enough.

**Watch out.** A condition must return `True`, `False`, or nothing. A
count of `0` is not `False`; write `return agent.slots > 0`. TagKit refuses
raw values so a real zero is never mistaken for a failure. A Shape may
*relax* its Base's gate by overriding it (founders skip the dues); that is
the Liskov direction and it is silent.

### Pattern 6 · Promise, then repair

**When you want** a Tag to guarantee something about the finished Agent.
Postconditions inspect the product after everything applied.

```python
class Wizard(Tag):

    @Post
    def Has_Spellbook(agent):
        assert agent.spellbook is not None


newt = Character("Newt")
newt.spellbook = None

try:
    Wizard(newt)
except TagPostconditionError:
    pass                                # the Tag stays; Newt is defective

assert newt in Wizard                   # a member
assert not newt                         # whose promise is broken
assert newt in ~Wizard                  # waiting in the repair queue

for broken in ~Wizard:                  # the repair loop
    broken.spellbook = []

assert newt                             # sound again
assert newt in list(Wizard)             # back in the working population
```

This is the factory rule: a bad product is not melted back to materials. It
is flagged, repaired, or thrown away (`del Wizard[newt]`).

`if agent:` reads "are this agent's promises holding". When you need the
name of the broken one, `Contract.Display(agent)` or `f"{agent:contract}"`
prints them.

**Watch out.** A Shape should promise *at least* what its Base promised.
Use `@Post @Underlay` and `return base() and ...`. Overriding a Base's
promise without it weakens the contract; TagKit allows it and warns.

### Pattern 7 · Keywords for rules written as data

**When you want** rules that live in tables or files and check words, not
classes. Mark the Tags that are words with `@Flag`.

```python
@Flag
class Undead(Tag):
    pass


@Flag
class Flying(Tag):
    pass


ghoul = Character("Ghoul")
Undead(ghoul)

assert "Undead" in ghoul                # by name
assert Undead in ghoul                  # by class
assert "Flying" not in ghoul

TURNABLE = ["Undead", "Fiend"]          # a rule as data
assert any(word in ghoul for word in TURNABLE)

assert Keyword(ghoul, "Undead")         # the function form: any object
assert not Keyword(Character("x"), "Undead")
```

**Watch out.** Only Flags answer by name; an ordinary Tag never does, so
`"Wizard" in agent` is `False` unless Wizard is a Flag. A Flag cannot be
applied to an object that already has its own `in` (a list-like host);
TagKit refuses rather than take the seat. `Keyword(...)` works everywhere.

### Pattern 8 · Shared things, and who may reach them

**When you want** one value or one behaviour for the whole Field, and a
clean line between what the Agent shows and what the Tag keeps.

```python
class Agency(Tag):

    @Public
    @Report
    def colour(tag):
        return "navy"                   # one copy, published on the Agent

    @Report
    def HQ(tag):
        return "London"                 # one copy, Tag-side only

    @Public
    @Operation
    def dispatch(agency, sender, mesFighter):
        if sender not in agency:        # live authority: checked each call
            raise PermissionError("inactive")
        return f"{sender.name}: {mesFighter}"

    @Secret
    @Record
    def clearance(agent):
        return "top"

    @Action
    def status(agent):
        return agent.clearance          # inside: the secret resolves


bond = Character("Bond")
Agency(bond)

assert bond.colour == "navy"            # published Report, read-only
assert bond.dispatch("hello") == "Bond: hello"
assert bond.status() == "top"
assert not hasattr(bond, "HQ")          # Tag-side stays Tag-side
assert not hasattr(bond, "clearance")   # secret from outside

send = bond.dispatch                    # a captured handle
del Agency[bond]

try:
    send("late")
except PermissionError:
    pass                                # the Operation checks membership
```

The rule in one line: what the Agent does is public, what the Agency keeps
is internal. `@Secret` hides an Agent member; `@Public` shows a Tag member.
Both are modifiers: they stack on `@Record`, `@Action`, `@Report` or
`@Operation` in either order.

Notice the symmetry. A Report is written exactly like a Record, with the
Tag instead of the Agent as its first input; it runs once per Tag and its
value is shared by the whole Field. `def hit_die(tag, inherited)` extends
the Base's value, as `def spells(agent, stored)` extends what is stored.

**Watch out.** A secret resolves only while one of the Agent's own Actions
or protocols is running. A handle to a secret Action captured inside and
called outside fails, on purpose.

### Pattern 9 · Roles that end

**When you want** a Tag to clean up when it leaves, or a role that lasts for
a block of code.

```python
class Sentry(Tag):

    @Imprint
    def post(agent):
        agent.on_duty = True

    @Rip
    def stand_down(agent):
        agent.on_duty = False


guard = Character("Guard")

with Scope(guard, Sentry):              # applies on entry
    assert guard.on_duty

assert not guard.on_duty                # Ripped on exit, even on error
assert guard not in Sentry
```

`@Imprint` runs after the Tag applies; `@Rip` runs after it leaves. They
are constructor and destructor, `__enter__` and `__exit__`.

**Watch out.** Python does not promise to run finalizers at shutdown, so
`del agent` is best-effort. `Scope` is the guaranteed path.

### Pattern 10 · Build the sheet from pieces

Put it together. This is the D&D example in miniature.

```python
class Species(Tag):

    @Record
    def speed(agent):
        return 30


class Elf(Species):

    @Record
    def spells(agent, stored):
        return (stored or []) + ["Light"]


class Class(Tag):

    @Report
    def hit_die(tag):
        return 8


class Wizard(Class):

    @Report
    def hit_die(tag):
        return 6

    @Pre
    def Can_Study(agent):
        return agent.level >= 1

    @Record
    def spells(agent, stored):
        return (stored or []) + ["Magic Missile"]

    @Record
    def hit_points(agent, stored):
        return (stored or 0) + agent.level * Wizard.hit_die

    @Post
    def Knows_Spells(agent):
        return len(agent.spells) > 0

    def Attack(agent):
        return f"{agent.name} casts {agent.spells[-1]}"


class Fighter(Tag):

    @Record
    def spells(agent, stored):
        return (stored or []) + ["Identify"]


class War_Caster(Tag):

    @Pre
    def Is_A_Caster(agent):
        return agent in Wizard

    @Action
    @Underlay
    def Attack(agent, underlay):
        return underlay() + " behind a shield"


ari = Character("Ari", level=3)

for choice in (Elf, Wizard, Fighter, War_Caster):
    choice(ari)

assert ari.spells == ["Light", "Magic Missile", "Identify"]
assert ari.hit_points == 18
assert ari.Attack() == "Ari casts Identify behind a shield"
assert ari                                      # every promise holds
assert f"{ari:tags}" == "Elf, Wizard, Fighter, War_Caster"

print(Outline(ari))
# Character
#   Species
#     Elf
#   Class
#     Wizard
#   Fighter
#   War_Caster
```

---

## Reading an Agent

| Question | Spelling |
| --- | --- |
| Is it a Wizard now? | `agent in Wizard` |
| Was it ever? | `isinstance(agent, Wizard)` |
| Does it carry the keyword? | `"Undead" in agent`, `Keyword(agent, "Undead")` |
| Which Tags, in order? | `Tags(agent)`, `f"{agent:tags}"` |
| The whole shape? | `Outline(agent)`, `f"{agent:outline}"` |
| Are its promises holding? | `if agent:`, `Contract.Status(agent)`, `f"{agent:contract}"` |
| What did it look like right after Wizard? | `agent.Wizard`, `Wizard[agent]` |

## Reading a Tag

| Question | Spelling |
| --- | --- |
| Who is one, and sound? | `for a in Wizard`, `len(Wizard)`, `if Wizard:` |
| Who is one, and broken? | `for a in ~Wizard`, `if ~Wizard:` |
| Everyone? | `Wizard[:]` |
| What applies with it? | `Form(Wizard)`, `f"{Wizard:form}"` |
| Take it away | `del Wizard[agent]` |

Nothing TOP-level lives at `Wizard.something`. That namespace is yours: put
your Reports and Operations there.

---

## Do and don't

| Do | Don't |
| --- | --- |
| Make a Tag for what something *is*: species, class, role, clearance. | Make a Tag for a passing state. `Asleep` is a Record, `asleep = True`. |
| Let independent Tags pile up on one Record with `stored`. | Chain Tags by inheritance just to share a list. |
| Extend an Action with `@Underlay`. | Call `agent.Attack()` from inside `Attack` (that recurses). |
| Gate with `@Pre`; promise with `@Post`; repair through `~Tag`. | Roll your own validation after the fact. |
| Mark word-like Tags `@Flag` and write rules as data. | Match every Tag by name. Only Flags are words. |
| Clean up with `@Rip`, guarantee it with `Scope`. | Rely on `del agent` for anything that matters. |
| Reset by Rip and apply again. | Reapply an active Tag hoping it resets (it does nothing). |
| Keep shared data in a `Report`, one copy. | Copy shared data into every Agent's Record. |
| Ask `agent in Wizard`. | Ask `type(agent) is Character`; the type is wrapped. |

---

## Where next

- [The Specification](../spec/SPECIFICATION.md): the laws, ring by ring.
- [`examples/dnd_character.py`](../examples/dnd_character.py) and
  [`examples/biome.py`](../examples/biome.py): the long form.
- [`benchmarks/bench.py`](../benchmarks/bench.py): what it costs.
- [`IMPLEMENTATION_NOTES.md`](IMPLEMENTATION_NOTES.md): how TagKit does it.
