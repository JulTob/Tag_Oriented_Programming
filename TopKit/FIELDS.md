# The Fields Guide

*Populations, partitions, and the algebra between them.*

[The Guide](GUIDE.md) shows how one Agent gets its Tags. This guide is
about the other direction: every Tag keeps the population of Agents that
carry it, and a program can ask that population questions, walk it,
partition it, and combine it with others. Everything here is one line
long and runs; the blocks below are run by the test suite in order.

```python
from TopKit import Post, Public, Record, Report, Tag


class Crew:
    """The host: a name and a pulse."""

    def __init__(self, name):
        self.name = name
        self.alive = True


class Officer(Tag):

    @Post
    def Alive(agent):
        return agent.alive


class Wizard(Officer):

    @Record
    def spells(agent):
        return ["Light"]


class Fighter(Officer):

    @Record
    def weapon(agent):
        return "sword"


class Sworn(Tag):
    pass


ari, bo, cal, dee = Crew("Ari"), Crew("Bo"), Crew("Cal"), Crew("Dee")
Wizard(ari)
Wizard(bo)
Fighter(bo)
Fighter(cal)
Sworn(ari)
Sworn(cal)
```

---

## 1. Three views of one Field

A Field is the population of a Tag, in the order they joined, weakly
held: it never keeps an Agent alive. It comes in three views.

```python
assert list(Wizard[:]) == [ari, bo]         # everyone: the whole Field
assert list(Wizard) == [ari, bo]            # the sound ones: every promise holds
assert list(~Wizard) == []                  # the defective ones: a promise is broken

cal.alive = False                           # Cal breaks Officer's promise
assert list(Fighter) == [bo]                # off the line
assert list(~Fighter) == [cal]              # waiting for repair
assert cal in Fighter                       # still a member
assert cal in Fighter[:]                    # still in the Field
```

The plain loop, `for f in Fighter`, is the working population. `~Fighter`
is the repair queue. `Fighter[:]` is the roster. `if Fighter:` asks
whether anyone is fit; `len(Fighter[:])` counts everyone.

---

## 2. The algebra: either, both, without

Populations combine with three operators. `|` is either, `&` is both,
`-` is the left without the right. **A Tag in an operator seat means its
sound population**, exactly as it does in `for w in Wizard`.

```python
assert list(Wizard | Fighter) == [ari, bo]          # sound Wizards, then sound Fighters, each once
assert list(Wizard & Fighter) == [bo]               # sound in both
assert list(Wizard - Sworn) == [bo]                 # sound Wizards who have not sworn
assert list(Fighter | Wizard) == [bo, ari]          # order follows the left side first
```

The whole Field and the defective view combine the same way, and the
levels mix: a population is a population.

```python
assert list(Wizard[:] | Fighter[:]) == [ari, bo, cal]     # everyone who is either, Cal included
assert list(Fighter[:] - Wizard) == [cal]                  # every Fighter who is not a sound Wizard
assert list(~Fighter | ~Wizard) == [cal]                   # the whole repair queue of both
assert list(Sworn[:] & Fighter[:]) == [cal]                # sworn, and a Fighter, of any condition
assert list(Sworn & Fighter[:]) == []                      # Cal is defective, so he is not a *sound* Sworn
```

That last line is worth a pause. Soundness is holistic: Cal broke
Officer's promise, so he is off every sound line, `Sworn`'s included,
even though `Sworn` promised nothing itself. Ask the whole Field,
`Sworn[:]`, when condition does not matter.

---

## 3. A combined view is alive

The result of an operator is not a list. It holds its two sides and reads
them when it is walked, so it is never stale: an Agent who joins later is
in it, and one who is repaired moves from one side to the other.

```python
combatants = Wizard | Fighter               # made once
assert list(combatants) == [ari, bo]

Fighter(dee)                                # Dee joins after the view was made
assert dee in combatants

cal.alive = True                            # Cal is repaired
assert cal in combatants
assert len(combatants) == 4
assert combatants                           # truth: anyone at all?
```

Keep a combined view around like you would keep a Tag around. Do not
copy it into a list unless you want the moment frozen.

---

## 4. Patterns

**The battle loop.** Every combatant regardless of class, fit to fight:

```python
for fighter in Wizard | Fighter:
    assert fighter.alive
```

**The roster of the missing.** Who has a role but not the role that
should go with it:

```python
unsworn = (Wizard[:] | Fighter[:]) - Sworn
assert list(unsworn) == [bo, dee]           # Bo and Dee never swore
```

**The repair queue across roles.** One loop over every defective Agent
of several Tags, whichever promise broke:

```python
bo.alive = False
for broken in ~Wizard | ~Fighter:
    broken.alive = True                     # sickbay
assert not list(~Wizard | ~Fighter)
```

**A gate that reads a population.** A condition may ask a combined view a
question, since it answers `in`:

```python
from TopKit import Pre, Precondition


class Champion(Tag):

    @Pre
    def Is_A_Fighting_Wizard(agent):
        return agent in (Wizard & Fighter)


Champion(bo)                                # Bo is both
try:
    Champion(ari)
except Precondition.Is_A_Fighting_Wizard:
    pass                                    # Ari is only a Wizard
```

**Pins combine too.** A Pin's Field is a population of Tags, so the same
algebra sorts Tags:

```python
from TopKit import Flag, Pin


@Pin
class Combat(Tag):
    pass


@Flag
@Pin
class Deprecated(Tag):
    pass


Combat(Wizard)
Combat(Fighter)
Deprecated(Fighter)

assert list(Combat - Deprecated) == [Wizard]        # combat Tags still in use
```

---

## 5. What the algebra does not do

- **No complement of a union.** `~(Wizard | Fighter)` has no universe to
  complement, so it is not defined. `~Wizard | ~Fighter` is what you mean.
- **No order across sides.** `|` walks the left side first, then the
  right; it does not interleave by join time.
- **No copies.** A view reads the Fields it was made from. If you need a
  frozen moment, say so: `list(Wizard | Fighter)`.
- **Type unions still work.** `Wizard | None` is the language's own class
  union, untouched; only a Tag or a population on the other side makes
  the operator a Field operator.

## 6. The checklist

- **Walk a Tag** for the sound population, `~Tag` for the repair queue,
  `Tag[:]` for everyone.
- **Combine with `|`, `&`, `-`.** A Tag in an operator seat is its sound
  population; `Tag[:]` and `~Tag` say the other levels.
- **Keep views, not lists.** A view is alive; a list is a moment.
- **Read a view in a condition** with `in`, and the gate follows the
  population.
