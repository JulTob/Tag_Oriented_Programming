# The Index Guide

*The Field as a mapping: keys, ranges, and one component per bracket.*

[The Fields Guide](FIELDS.md) shows a Field as a set: who is a member,
sound or defective, combined with other Fields. This guide is about the
Fields that are also maps. A signal has one sample at each time. A ledger
has one line at each number. A register has one citizen at each identity.
A Record marked `@Index` is a **component of the Tag's key**, and the key
makes the Field an ordered mapping from key to Agent. Every block below
runs, in order, and the test suite runs them.

```python
from TopKit import Imprint, Index, Post, Pre, Precondition, Record, Report, Tag
from TopKit import TagCompositionError, TagDeclarationError, TagResolutionError


class Sample:
    """The host: a value read off a sensor."""

    def __init__(self, value):
        self.value = value


class Signal(Tag):

    @Index
    def t(agent, *, t):                     # the key, given by the caller
        return t

    @Post
    def In_Range(agent):
        return -100 <= agent.value <= 100


x0, x2, x5 = Sample(0.0), Sample(0.7), Sample(0.3)
Signal(x0, t=0)
Signal(x2, t=2)
Signal(x5, t=5)
```

---

## 1. A key on the Field

An Index is a Record. It is built at tagging, from the inputs by name,
and it lives on the Agent like any Record. Three laws make it a key.

**Constant.** Writes and deletes are refused. Another key means Rip, then
apply again.

```python
assert x2.t == 2                            # a Record, on the Agent

try:
    x2.t = 3
except AttributeError:
    pass                                    # constant while the Agent carries it
```

**Unique as a whole.** The key is checked when it is built, before
anything is published, so a duplicate rolls the call back and the
newcomer is not a member.

```python
late = Sample(0.9)

try:
    Signal(late, t=2)
except TagCompositionError:
    pass

assert late not in Signal[:]
assert not hasattr(late, "t")
```

**One Index per Form, declared in one Tag.** A Shape inherits the key
and may not add to it. The reason is the kernel's: membership is closed
upward, so every member of the Shape is also in the Base's Field, where
the Base's key already decides uniqueness. A component that can never
separate two members is a trap, so it is refused where it is written.

```python
try:
    class Widened(Signal):
        @Index
        def channel(agent, *, channel):
            return channel
except TagDeclarationError:
    pass
```

---

## 2. The handle: values, and the seat

Read on the Tag, an Index component is a **handle**. It is the same name
in two scopes, which the Specification already allows: `x2.t` is the
value on the Agent, `Signal.t` is the map on the Tag.

The handle is the set of that component's values, the way a dictionary's
keys are. Iterate it, count it, ask `in`, take the smallest and the
largest.

```python
assert list(Signal.t) == [0, 2, 5]
assert len(Signal.t) == 3
assert 2 in Signal.t
assert 3 not in Signal.t
assert min(Signal.t) == 0 and max(Signal.t) == 5
```

Its brackets are the seat for that one component. A value names the
member at that key. A slice names a range of values, half-open as the
language's own, in key order. The step is the direction.

```python
assert Signal.t[2] is x2                    # the member at that key
assert list(Signal.t[:]) == [x0, x2, x5]    # everyone, in key order
assert list(Signal.t[::-1]) == [x5, x2, x0] # descending
assert list(Signal.t[1:5]) == [x2]          # 1 <= t < 5
assert list(Signal.t[2:]) == [x2, x5]       # either bound may be omitted
```

A miss on the key fails, in TOP's words. Presence is a question, and a
question never fails.

```python
try:
    Signal.t[3]
except TagResolutionError:
    pass

if 3 in Signal.t:
    raise AssertionError("nothing at three")
```

Keys are values, not positions. Sample two is the sample whose key is
two, not the second one tagged. That is why the plain `Signal[0:2]` is
refused and the keyed `Signal.t[0:2]` is not.

---

## 3. Two components, one key

Two events can happen at one time. One component cannot separate them,
so the key takes a second: a counted sequence number. Components are
declared in one Tag, in the order that orders the Field: by `t`, then by
`seq`.

```python
class Event(Tag):

    @Report
    def next(tag):                          # the counter, shared by the Field
        return 0

    @Index
    def t(agent, *, t):
        return t

    @Index
    def seq(agent):                         # counted: read here, bumped after commit
        return Event.next

    @Imprint
    def Count(agent):
        Event.next += 1


e1, e2, e3 = Sample(1), Sample(2), Sample(3)
Event(e1, t=1)
Event(e2, t=1)                              # the same time, a different seq
Event(e3, t=0)

assert (e1.seq, e2.seq, e3.seq) == (0, 1, 2)
assert list(Event.t[:]) == [e3, e1, e2]     # by t, then by seq
```

Each bracket constrains one component, by name, so nothing is positional.
Part of the key names a population. The whole key names one Agent, as
`d[1]` is a dictionary and `d[1][2]` is the value.

```python
assert list(Event.t[1]) == [e1, e2]         # a population
assert Event.t[1].seq[1] is e2              # the one member
assert Event.seq[1].t[1] is e2              # the order of steps is free
assert 1 in Event.t[1].seq                  # is there an event at t one, seq one
assert 9 not in Event.t[1].seq
```

A chain is nothing new: it is the intersection the Fields Guide already
gives, then the one member.

```python
assert list(Event.t[1].seq[0:2]) == list(Event.t[1] & Event.seq[0:2])
```

The same component twice, or a name that is not a component, is refused.
So is any assignment: membership comes from tagging, and Rip is
`del Event[agent]`.

```python
try:
    Event.t[1].t
except AttributeError:
    pass

try:
    Event.t[1].value
except AttributeError:
    pass

try:
    Event.t[9] = e1
except TypeError:
    pass
```

---

## 4. Shapes share the key

A Shape's handle is the Shape's own Field, read through the Base's key.

```python
class Alarm(Signal):
    pass


loud = Sample(90.0)
Alarm(loud, t=7)

assert Alarm.t[7] is loud
assert Signal.t[7] is loud                  # in the Base's Field too
assert list(Alarm.t[:]) == [loud]
assert list(Signal.t[5:]) == [x5, loud]

try:
    Alarm.t[5]                              # a Signal, not an Alarm
except TagResolutionError:
    pass
```

---

## 5. Windows, and the algebra

A range through a handle is a population like any other: it is alive,
and it combines with `|`, `&` and `-`. A handle walks **everyone**, as
`Signal[:]` does, so a defective member is still found by its key.
Sound only is `if sample:` in the loop.

```python
class Acknowledged(Tag):
    pass


Acknowledged(x2)
window = Signal.t[0:6]                      # made once

assert list(window - Acknowledged) == [x0, x5]

x5.value = 500.0                            # x5 breaks In_Range: defective
assert Signal.t[5] is x5                    # still found by key
assert [s for s in window if s] == [x0, x2] # the sound ones, by truth

x5.value = 0.3                              # repaired

x1 = Sample(0.1)
Signal(x1, t=1)                             # joins after the window was made
assert list(window) == [x0, x1, x2, x5]
```

---

## 6. Keys of your own type

A key's type carries its own order and its own hash, as it does for the
language's sorting and dictionaries. When the natural order is wrong, or
the key has parts, make a type. A frozen, ordered dataclass gives both in
one line. A slice bound is then a value of that type.

```python
from dataclasses import dataclass


@dataclass(order=True, frozen=True)
class DNI:
    number: int
    letter: str


class Citizen(Tag):

    @Index
    def dni(agent, *, dni):
        return dni


ana, bo, cy = Sample(1), Sample(2), Sample(3)
Citizen(ana, dni=DNI(30_000_000, "X"))
Citizen(bo, dni=DNI(12_345_678, "Z"))
Citizen(cy, dni=DNI(99_999_999, "R"))

assert list(Citizen.dni[:]) == [bo, ana, cy]
assert Citizen.dni[DNI(12_345_678, "Z")] is bo
assert list(Citizen.dni[DNI(20_000_000, "A"):DNI(90_000_000, "A")]) == [ana]
assert max(Citizen.dni).number == 99_999_999
```

A component that is computed from another adds nothing: the check letter
of a DNI can never separate two citizens the number did not. Keep such
values as plain Records, and keep the key to what separates.

---

## 7. Rip, gaps, coordinates

A Rip releases the key from the Field. The Rogue keeps its value, sticky
and still constant, and a later member may take the key. Uniqueness is a
law of the Field: two objects may carry one value once one of them is
outside.

```python
del Signal[x1]

assert 1 not in Signal.t
assert x1.t == 1                            # sticky

try:
    x1.t = 4
except AttributeError:
    pass                                    # and still constant

x1b = Sample(0.2)
Signal(x1b, t=1)                            # the key is free again
assert Signal.t[1] is x1b

Signal(x1, t=4)                             # a fresh tagging gives the Rogue a fresh key
assert x1.t == 4
```

A gap is not a mess. A key is a **coordinate**, not a position, and a
coordinate does not move because a neighbour left. In a signal a gap is a
dropout, which is information. In a counted sequence a gap says an event
was removed, and renumbering would break every stored reference. When
positions are wanted, the language gives them on read.

```python
del Event[e1]

assert list(Event.t[1].seq) == [1]          # the gap stays
assert [n for n, _event in enumerate(Event.t[:])] == [0, 1]
```

---

## 8. Three numerations

- **Given.** `def t(agent, *, t): return t`. The caller says where.
- **Derived.** `def key(agent): return agent.serial`. The Agent already
  knows where.
- **Counted.** The builder reads a Report and an Imprint bumps it after
  commit, as `Event.seq` does above. A refused gate consumes no number,
  because the Imprint never runs; a Rip leaves a gap.

```python
class Ticket(Tag):

    @Report
    def issued(tag):
        return 0

    @Index
    def number(agent):
        return Ticket.issued

    @Imprint
    def Issue(agent):
        Ticket.issued += 1

    @Pre
    def Paid(agent):
        return agent.value > 0


paid = [Sample(5), Sample(5)]              # a Field never keeps an Agent alive: hold them

for ticket in paid:
    Ticket(ticket)

try:
    Ticket(Sample(0))
except Precondition.Paid:
    pass

assert Ticket.issued == 2                   # the refused ticket took no number
assert list(Ticket.number) == [0, 1]
```

---

## 9. What is refused

| Spelling | Why |
| --- | --- |
| `x.t = 3`, `del x.t` | constant: an attribute failure, as on a published Report |
| `Signal(y, t=2)` when two is taken | the whole key is unique: a Composition Failure, rolled back |
| `Signal(y, t="two")` among numbers | one component, one order: a Composition Failure, rolled back |
| a second `@Index` in a Shape or a second Base | one Index per Form: a Declaration Failure |
| `@Index def t(agent, stored)`, `@Secret @Index` | a key is a coordinate, not a pile, and never hidden: a Declaration Failure |
| a Record, an Action, a condition or `@Delete` named `t` from another Tag | the name stays taken: a Composition Failure |
| `Signal.t[3]` with nothing there | a Resolution Failure; ask `3 in Signal.t` |
| `Signal.t[1].t`, `Signal.t[1].value` | each component once, and only components |
| `Signal.t[::2]` | the step is a direction |
| `Signal.t[9] = y`, `del Signal.t[9]` | membership comes from tagging; Rip is `del Signal[y]` |
| `@Index` on a Pin | a Pin's Field is a population of Tags; a later STEP |

## 10. The checklist

- **Mark the Records that locate a member** `@Index`, in one Tag, in the
  order that should order the Field. Keep derived values as plain
  Records.
- **Read the handle on the Tag.** `Signal.t` is the values; `Signal.t[v]`
  the member; `Signal.t[a:b]` the window; `Signal.t[:]` everyone in
  order.
- **One component per bracket.** Chain by name, never by position.
- **Ask presence with `in`**, on the last handle. Look up with brackets
  when the member must be there.
- **Expect gaps after a Rip**, and read positions with `enumerate` when
  you need them.
