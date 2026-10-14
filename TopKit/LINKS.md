# The Links Guide

*Things that are true of two: roads, rails, ferries, bookings, lessons.*

The [Guide](GUIDE.md) shows how one Agent gets its Tags. A Tag says one
thing about **one** Agent: *Ruth is a Wizard*. But many facts are about
**two**: the road between two cities, a guest's booking at a hotel, a
teacher and a student. A **Link** is a Tag of an Agent's own that holds
those facts. This guide shows the main things you will use Links for,
one small section each. Every block below runs, in order, with nothing
installed but TopKit.

The [wiki page on Links](../wiki/1.5-TopKit-Links.md) teaches how they
work. This guide is about what they are good for.

Five words, so you never have to guess:

| Word | Meaning | In this guide |
| --- | --- | --- |
| **Relation** | The template you write inside a Tag, marked `@Link`. | `Geography.Road` |
| **Link** | The Tag each Agent builds from it: one per Agent. | `alicante.Road` |
| **Contact** | Someone an Agent is linked to. | `marbella`, in `alicante.Road` |
| **Pair** | One Agent and one Contact. The facts *between* them live here. | `alicante.Road[marbella]` |
| **Seats** | Every function in a Relation takes two: the Agent, then the Contact. | `def Describe(city, other)` |

The setting is a small country. A `City` is plain Python, and TOP never
asks you to change it.

```python
import gc

from TopKit import (
        Imprint, Link, Post, Pre, Public, Record, Report, Rip, Secret, Tag,
        TagPreconditionError, TagResolutionError,
        )


class City:
    """The host: ordinary Python."""

    def __init__(self, name):
        self.name = name
        self.sea_calm = True

    def __repr__(self):
        return self.name


class Geography(Tag):

    @Link
    class Road(Tag):                                  # a Relation: the template

        @Record
        def distance(city, other, *, distance=None):  # km
            return distance

        @Record
        def speed_limit(city, other, *, speed_limit=None):   # km/h
            return speed_limit

        @Record
        def travel_time(city, other, *, distance=None, speed_limit=None):
            return round(distance / speed_limit * 60)        # minutes

        def Describe(city, other):
            road = city.Road[other]
            return (f"{city.name} to {other.name}: {road.distance} km,"
                    f" limit {road.speed_limit}, about {road.travel_time} min")

    @Link
    class Motorway(Road):                             # a Road with one more fact

        @Record
        def toll(city, other, *, toll=0):
            return toll


alicante, marbella, murcia, valencia, madrid = (
        City("Alicante"), City("Marbella"), City("Murcia"),
        City("Valencia"), City("Madrid"),
        )

for city in (alicante, marbella, murcia, valencia, madrid):
    Geography(city)                                   # each city builds its own Road
```

---

## 1. Facts about the link itself

You have two cities and you want to say how long the road between them
takes. The time does not belong to Alicante, or to Marbella. It belongs
to **the road**. That is a Pair, and its Records are read like any other:

```python
alicante.Road(marbella, distance=480, speed_limit=120)

road = alicante.Road[marbella]

assert road.distance == 480
assert road.speed_limit == 120
assert road.travel_time == 240                  # worked out when the road was made
assert alicante.Road[marbella].travel_time == 240
```

Three things to know:

- **Write `alicante.Road[marbella]`, with the city object.** `Road` is
  each city's own: `alicante.Road` is Alicante's Link. The class
  `Geography.Road` is only the template, and asking it anything is
  refused.
- **Nothing is written on Marbella.** The facts are on the Pair.
  Marbella is a Contact, and she carries no record of the road at all.
- **A Record is a stored fact.** It is worked out once, when the road is
  made. You may change it later, and nothing else changes with it:

```python
road.travel_time = 255                          # traffic today: an estimate you update
assert road.travel_time == 255
assert road.distance == 480                     # the other facts did not move
```

For a value that must always follow the others, write a function. A
function on the Pair runs with the two cities in its two seats:

```python
assert road.Describe() == "Alicante to Marbella: 480 km, limit 120, about 255 min"
```

---

## 2. Asking who is connected to whom

A Link is a Tag, so everything you can ask a Tag you can ask a Link,
**of one city's Link at a time**:

```python
alicante.Road(murcia, distance=70, speed_limit=100)
alicante.Road(valencia, distance=170, speed_limit=120)
valencia.Road(madrid, distance=350, speed_limit=120)
murcia.Road(marbella, distance=390, speed_limit=120)

assert murcia in alicante.Road                  # is there a road from Alicante to Murcia?
assert madrid not in alicante.Road              # not directly
assert len(alicante.Road[:]) == 3               # how many roads leave Alicante
assert set(alicante.Road) == {marbella, murcia, valencia}   # walk them
```

Two points follow, and both surprise people at first.

**The question needs a city.** `murcia in Geography.Road` is not a
question. Only `murcia in alicante.Road` is, because every city has its
own roads. Ask about a city's Link, never about the name alone.

**A road has a direction.** `alicante.Road` holds the roads that *leave*
Alicante. Nothing public on Marbella says that a road reaches her. To
find the cities that have a road *to* Madrid, walk the cities you have
and ask each one:

```python
assert [c for c in Geography[:] if madrid in c.Road] == [valencia]
assert [c for c in Geography[:] if alicante in c.Road] == []   # no road leads back
```

---

## 3. Routes: a walk over links

The most common use of a graph is to find a way through it. A route is
a walk: from each city, follow the roads that leave it. Each step is one
line of ordinary Python:

```python
def roads_from(city):
    return list(city.Road)


def fewest_stops(start, goal):
    """The shortest list of cities from start to goal, or None."""
    seen = {start}
    paths = [[start]]
    while paths:
        path = paths.pop(0)
        here = path[-1]
        if here is goal:
            return path
        for next_city in roads_from(here):
            if next_city not in seen:
                seen.add(next_city)
                paths.append(path + [next_city])
    return None


def minutes(path):
    steps = zip(path, path[1:])
    return sum(a.Road[b].travel_time for a, b in steps)


route = fewest_stops(alicante, madrid)

assert route == [alicante, valencia, madrid]
assert minutes(route) == 85 + 175               # the facts on each road, added up
assert fewest_stops(madrid, alicante) is None   # the roads are one-way
```

The route function never mentions a Tag. It only asks each city's Link
who is next, and reads the time off each road. That is the whole use:
**the Link is the graph, and the Pair is the edge with its facts on it.**

Fewest stops is not the same as fastest. Alicante has a direct road to
Marbella, but the way through Murcia is quicker, and the facts to prove
it are already on the Pairs:

```python
direct = [alicante, marbella]
through_murcia = [alicante, murcia, marbella]

assert fewest_stops(alicante, marbella) == direct
assert minutes(direct) == 255                   # the estimate we updated in section 1
assert minutes(through_murcia) == 42 + 195      # 237: faster
```

To search by time instead of by stops, keep the same function and sort
the paths by `minutes`. The Links do not change.

---

## 4. Two-way links: say it once, in plain sight

A Link goes one way. A railway runs both ways, so make **two** Links, and
let the first one's training build the second. An `@Imprint` runs after
Gainings and before its Contact enters the Field. It links the other city
back, with the same facts:

```python
class Railway(Tag):

    @Link
    class Rail(Tag):

        @Record
        def minutes(city, other, *, minutes=None):
            return minutes

        @Imprint
        def Both_Ways(city, other):
            Railway(other)                              # the other city needs a Rail too
            other.Rail(city, minutes=city.Rail[other].minutes)


Railway(alicante)
alicante.Rail(murcia, minutes=55)

assert alicante.Rail[murcia].minutes == 55
assert murcia.Rail[alicante].minutes == 55              # the way back exists
assert alicante.Rail[murcia] is not murcia.Rail[alicante]   # two Pairs, two roads
```

Linking a city that is already linked, or repeating the same linking
while its training is underway, does nothing, so the echo stops after one
round. Because there are two Pairs, each direction may have its own facts.
Give the way back its own number if the facts differ.

A city can hold several Links at once. Alicante now has a `Road` and a
`Rail`, each with its own cities and its own facts. They do not mix.

---

## 5. Rules: who may link to whom

You do not want a road from a city to itself, or a port with ten
ferries on a pier built for two. A **gate** is a rule written as a
`@Pre`. When it says no, that Tag's training does not begin. A completed
Base linking stays. A **promise** is a rule written as a `@Post`: a link
that breaks its promise after admission stays, and it is marked defective
until it is repaired.

Linking follows ordinary Tagging: **Gate → Gainings → Imprints → Field →
Posts**. Gains arrive in declaration order. If a Record builder or Imprint
fails, the unfinished Link has no membership for that Contact, but the
Pair keeps its actual Gains and Posts. Linking again retries the unfinished
training. It does not undo a Base linking or independent Tagging that
already completed.

```python
class Sea(Tag):

    @Link
    class Ferry(Tag):

        @Report
        def capacity(link):                              # one fact about the Link, not the Pair
            return 2

        @Pre
        def Another_Port(city, other):
            return other is not city

        @Pre
        def Has_Room(city, other):
            return len(city.Ferry[:]) < city.Ferry.capacity

        @Post
        def Calm_Sea(city, other):
            return other.sea_calm

        @Record
        def hours(city, other, *, hours=None):
            return hours


ibiza, mallorca, menorca = City("Ibiza"), City("Mallorca"), City("Menorca")

Sea(alicante)
alicante.Ferry(ibiza, hours=4)
alicante.Ferry(mallorca, hours=7)

for refused in (alicante, menorca):                      # itself, and a third ferry
    try:
        alicante.Ferry(refused, hours=1)
    except TagPreconditionError:
        pass
    else:
        raise AssertionError("the gate must refuse")

assert len(alicante.Ferry[:]) == 2                       # a refusal changed nothing
assert menorca not in alicante.Ferry
```

Now the promise. When the sea is rough, the ferry to Mallorca is not
**removed**. It is **defective**, and it comes back by itself when the
sea calms:

```python
mallorca.sea_calm = False

assert mallorca in alicante.Ferry[:]                     # still linked
assert mallorca in ~alicante.Ferry                       # but in the broken ones
assert mallorca not in list(alicante.Ferry)              # and out of the sound ones
assert alicante.Ferry[mallorca].hours == 7               # its facts are still readable

mallorca.sea_calm = True

assert mallorca in list(alicante.Ferry)                  # repaired: nothing to redo
```

`list(link)` is the sound links. `~link` is the broken ones. `link[:]` is
all of them. A route finder that walks `list(city.Ferry)` avoids rough
seas for free.

---

## 6. Kinds of link: a Motorway is a Road

Some links are a kind of another. A motorway is a road with a toll. In
the setting at the top, `Motorway` is declared as a **Shape** of `Road`.
Linking through the Shape links through its Base first, and both share
**one Pair**:

```python
alicante.Motorway(valencia, distance=170, speed_limit=120, toll=12)

assert valencia in alicante.Motorway
assert alicante.Road[valencia] is alicante.Motorway[valencia]   # one Pair
assert alicante.Road[valencia].travel_time == 85                # the Road's facts
assert alicante.Motorway[valencia].toll == 12                   # and the Motorway's
```

Use a Shape when the new link **is** the old one, plus more. Everywhere
that asks for a Road finds the motorway too.

---

## 7. Using something up, and giving it back

A booking uses up a room. When the booking ends, the room must come
back. A link has a **teardown**, an `@Rip`, that runs when the link
ends, whichever way it ends, with both sides in hand:

```python
class Hotel:
    def __init__(self, name):
        self.name = name


class Guest:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


freed = []


class Hospitality(Tag):

    @Link
    class Booking(Tag):

        @Report
        def rooms(link):
            return 2

        @Pre
        def A_Room_Is_Free(hotel, guest):
            return len(hotel.Booking[:]) < hotel.Booking.rooms

        @Record
        def nights(hotel, guest, *, nights=None):
            return nights

        @Record
        def rate(hotel, guest, *, rate=None):
            return rate

        def Total(hotel, guest):
            booking = hotel.Booking[guest]
            return booking.nights * booking.rate

        @Rip
        def Free_The_Room(hotel, guest):
            freed.append((hotel.name, guest.name))        # a real program makes the room bookable again


sea_view = Hotel("Sea View")
ana, ben, cy = Guest("Ana"), Guest("Ben"), Guest("Cy")

Hospitality(sea_view)
sea_view.Booking(ana, nights=3, rate=90)
sea_view.Booking(ben, nights=2, rate=80)

assert sea_view.Booking[ana].Total() == 270

try:
    sea_view.Booking(cy, nights=1, rate=90)               # the hotel is full
except TagPreconditionError:
    pass
else:
    raise AssertionError("no room")

del sea_view.Booking[ana]                                 # Ana leaves

assert freed == [("Sea View", "Ana")]                     # the teardown ran with both of them
assert ana not in sea_view.Booking
sea_view.Booking(cy, nights=1, rate=90)                   # the room is free again
assert cy in sea_view.Booking
```

You do not have to remember to call anything. If the guest object
itself is deleted, the link ends on its own, and the same teardown runs:

```python
del ben
gc.collect()

assert freed == [("Sea View", "Ana"), ("Sea View", "Ben")]
```

---

## 8. What the other end sees

A link is one-way, so by default the Contact sees **nothing** of it.
`student.grade` is not a thing a student can read, and nothing on her
says who teaches her. A Relation can publish chosen members with
`@Public`, and they appear on the Contact, read-only. Everything else
stays on the Agent's side, and a published member says only what its
author wrote into it:

```python
class Staff_Room:
    def __init__(self, name):
        self.name = name


class Student:
    def __init__(self, name):
        self.name = name


class School(Tag):

    @Link
    class Teaches(Tag):

        @Public
        @Record
        def classroom(teacher, student, *, classroom=None):   # the student may read this
            return classroom

        @Record
        def grade(teacher, student, *, grade=None):           # only the teacher's side reads this
            return grade

        @Public
        def Homework(teacher, student):                       # the student may call this
            return f"{student.name}: read chapter 3, says {teacher.name}"   # the author chose to name the teacher


miss_ruiz = Staff_Room("Miss Ruiz")
eli = Student("Eli")

School(miss_ruiz)
miss_ruiz.Teaches(eli, classroom="B2", grade=8)

assert eli.classroom == "B2"                                    # published
assert eli.Homework() == "Eli: read chapter 3, says Miss Ruiz"
assert miss_ruiz.Teaches[eli].grade == 8                        # the teacher's side sees all

try:
    eli.grade
except AttributeError:
    pass
else:
    raise AssertionError("the grade is not published")
```

A published member is **live**: it follows the Pair. When the link ends,
the line is still on the student, but it answers no more:

```python
del miss_ruiz.Teaches[eli]

try:
    eli.Homework()
except Exception as error:
    assert type(error).__name__ == "TagRogueAccessError"
else:
    raise AssertionError("the lesson is over")
```

If two Agents link the same Contact and both publish `classroom`, the
Contact sees the latest. Publish a member only where one Agent is the
natural owner of that fact.

---

## 9. Link, Tag, Record, Tool, or Peers?

| You want to say | Use | Example |
| --- | --- | --- |
| One thing about one Agent, as a category | a **Tag** | `Wizard(ari)` |
| One value that belongs to one Agent | a **Record** | `ari.hp` |
| One thing the Agent *has*, held | a **Tool** | `ari.sword` |
| One thing true of **two** Agents, with facts of its own | a **Link** | `alicante.Road[marbella].travel_time` |
| A relation where neither holds the other: a duel, a marriage | **Peers**, one Tag whose gate keeps its Field at two | see the [wiki page](../wiki/1.5-TopKit-Links.md) |

A quick test: if you find yourself writing a dictionary keyed by a pair
of Agents, `facts[(alicante, marbella)]`, that dictionary is a Link
waiting to be written. A Link keeps it weakly, ends it when either side
goes, and checks its rules at every change.

---

## 10. The checklist

| Do | Don't |
| --- | --- |
| Put facts about the two on the Pair: `alicante.Road[marbella].travel_time`. | Put them on either city: `marbella.road_time`. |
| Ask a city's own Link: `murcia in alicante.Road`. | Ask the template: `murcia in Geography.Road`. It has no answer. |
| Make a second Link, written by an `@Imprint`, for a two-way relation. | Expect `alicante.Road[marbella]` to give you `marbella.Road[alicante]`. |
| Use a `@Pre` to refuse the current Tag before its Gainings begin. | Link first and clean up after a failure. |
| Use a `@Post` for what may stop being true: the link turns defective and recovers. | Remove and re-add links when the world changes. |
| Use `list(city.Road)` for sound links, `~city.Road` for broken ones, `city.Road[:]` for all. | Filter broken links by hand in every function that walks them. |
| Use a Shape for a link that **is** another plus more. | Copy a Relation to add one Record. |
| Put what must happen at the end in an `@Rip`. | Rely on the program remembering to clean up. |
| Publish with `@Public` only what the Contact may see. | Publish everything and hope it is fine. |
| Hold a Link through its Agent: `alicante.Road`. | Pass a printed Link around: two cities' Links print the same. |

---

## Where next

- [The wiki page on Links](../wiki/1.5-TopKit-Links.md): how Links work,
  with the rules of every example above.
- [The Guide](GUIDE.md): Tags, Records, Actions, and the patterns that
  Links are built on.
- [The Contracts Guide](CONTRACTS.md): gates, promises and repair in
  depth.
- [The Fields Guide](FIELDS.md): the population a Link holds is a Field,
  and everything there applies.
- [The Specification, section 1.10](../spec/SPECIFICATION.md): the laws.
