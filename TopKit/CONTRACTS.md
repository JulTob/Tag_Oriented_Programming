# The Contracts Guide

*Gates, promises, membership, and what to do when they fail.*

The [Guide](GUIDE.md) teaches Tag-Oriented Programming one pattern at a
time. This guide goes deeper into one ring of it: **contracts**, and the
error control they give you. Contract programming is not widespread and
error control is often an afterthought, so this guide is a little more
serious, with the same rule: every code block below runs, in order, on
Python 3.10 or later, with nothing installed but TopKit.

The setting is a starship. Accidents happen to the ship, access is
controlled among the crew, and sickbay has protocols. Every one of those
is a contract.

```python
from TopKit import (
        Action, Contract, Flag, Operation, Pin, Post, Postcondition, Pre,
        Precondition, Public, Record, Report, Requirement, Rip, Tag,
        TagRogueAccessError, Underlay,
        )


class Crew:
    """The host: ordinary Python. TOP never asks you to change it."""

    def __init__(self, name, rank=1):
        self.name = name
        self.rank = rank
        self.alive = True
        self.infected = False


class Ship:
    def __init__(self, name):
        self.name = name
        self.core_temperature = 900
        self.shields = 0
```

---

## 1. Three ways a contract fails

A Tag can make three kinds of claim, and each fails in its own way and
at its own time.

| Claim | Mark | Checked | When it fails |
| --- | --- | --- | --- |
| "You may enter" | `@Pre` | at the door, once | nothing changes: refused |
| "You will stay like this" | `@Post` | at the door, then at every tagging and every use of a published member | the Tag stays; the Agent is **defective** |
| "You may use what we share" | `@Public` | at every use | refused until membership and soundness return |

The first two are conditions the Tag declares. The third is not declared
at all: it is what publication *means*.

---

## 2. The gate: nothing changes

A Precondition inspects the incoming Agent. When it says no, the tagging
stops before anything is written, and the failure carries the name you
wrote.

```python
class Officer(Tag):

    @Pre
    def Commissioned(agent):
        return agent.rank >= 2


ensign = Crew("Wesley", rank=1)

try:
    Officer(ensign)
except Precondition.Commissioned:
    pass                                # refused; Wesley is exactly as he was

assert ensign not in Officer
assert not isinstance(ensign, Officer)  # never was one

ensign.rank = 2
Officer(ensign)                         # now it takes
```

`except Precondition.Commissioned` catches that one refusal. A name you
never declared is an error at the `except` line, so a handler cannot sit
silently and never fire.

---

## 3. The promise: the Tag stays, the Agent is defective

A Postcondition is a promise about the finished Agent. It is checked when
the Tag applies, and again at every later tagging and every use of a
published member. When it breaks, TOP does not undo anything. The product left
the line; it is flagged.

```python
class Warp_Core(Tag):

    @Post
    def Core_Within_Tolerance(agent):
        return agent.core_temperature < 1000

    def Vent(agent):
        agent.core_temperature -= 300


enterprise = Ship("Enterprise")
Warp_Core(enterprise)

assert enterprise                       # every promise holds

enterprise.core_temperature = 1400      # an accident, during play

assert not enterprise                   # a promise is broken
assert enterprise in Warp_Core          # still a Warp_Core ship
assert enterprise in ~Warp_Core         # waiting in the repair queue
```

This is the factory rule: a bad product is not melted back to materials.
It is flagged, repaired, or thrown away.

---

## 4. The repair loop, and autofix

Two ways to repair. The **repair loop** walks every defective member and
fixes them from the outside:

```python
for ship in ~Warp_Core:                 # every broken one
    ship.Vent()
    ship.Vent()

assert enterprise                       # sound again
assert list(Warp_Core) == [enterprise]  # back in the working population
```

**Autofix** repairs at the point of use. A published member refuses a
defective Agent, and the refusal names the promise that broke, so the
handler knows exactly what to fix and can try again:

```python
class Engineering(Tag):

    @Public
    @Operation
    def Engage(engineering, ship, factor):
        return f"{ship.name} at warp {factor}"


Engineering(enterprise)
enterprise.core_temperature = 1400      # another accident

try:
    enterprise.Engage(9)
except Postcondition.Core_Within_Tolerance:
    enterprise.Vent()
    enterprise.Vent()
    assert enterprise.Engage(9) == "Enterprise at warp 9"
```

Notice that the handler did not read a message or inspect the ship. The
failure said which promise, the handler fixed that promise, and the
retry went through. That is error control that reads as the program's
own words.

**Soundness is holistic.** The published member refused because *a*
promise on the ship was broken, not because Engineering's own promises were. A ship
with a working helm and a failing core is not cleared to engage. If a
Shape needs to relax a Base's promise, it deletes it in its Overlay; a
promise is never quietly ignored.

---

## 5. Published members: relieved of duty

What the Agent does is its own. What the Tag publishes stays the Tag's,
lent for as long as the Agent is a sound member. When a crew member
leaves the Bridge, she keeps everything she became, and loses what the
Bridge lent her.

```python
class Bridge(Tag):

    @Public
    @Report
    def alert(bridge):
        return "green"

    @Public
    @Operation
    def Fire(bridge, agent, target):
        return f"{agent.name} fires at {target}"

    @Record
    def station(agent):
        return "tactical"

    def Report_In(agent):
        return f"{agent.name} at {agent.station}"


worf = Crew("Worf", rank=3)
Officer(worf)
Bridge(worf)

assert worf.alert == "green"            # published Report, read-only
assert worf.Fire("asteroid") == "Worf fires at asteroid"
assert worf.Report_In() == "Worf at tactical"

fire = worf.Fire                        # a handle captured on the bridge
del Bridge[worf]                        # relieved of duty

assert worf.Report_In() == "Worf at tactical"   # his own: he keeps it
assert isinstance(worf, Bridge)                  # ever bridge crew, always
try:
    worf.alert                          # the Bridge's: closed
except TagRogueAccessError:
    pass

try:
    worf.Fire("asteroid")
except TagRogueAccessError:
    pass                                # a Rogue Agent, refused

try:
    fire("asteroid")                    # the stale handle fails the same way
except TagRogueAccessError:
    pass

Bridge(worf)                            # reinstated: the Bridge answers again
assert worf.Fire("asteroid") == "Worf fires at asteroid"
```

Two failures, two meanings. `TagRogueAccessError` says *you left*.
`Postcondition.Something` says *you are broken*. A program that catches
them separately reacts correctly to each without reading a word of text.

Notice what the refusal is **not**. Worf's `alert` still exists; Worf is
simply no longer the one who may read it. So TOP raises a TOP failure and
says so, rather than answering in the host language's words that there is
no such name. A question about membership is answered by the layer that
owns membership.

---

## 6. Necessary to enter, necessary to stay

Some claims are both a gate and a promise. Stack the two marks on one
function and it fails under both names.

```python
class Crew_Member(Tag):

    @Pre
    @Post
    def Alive(agent):
        return agent.alive


casualty = Crew("Redshirt")
casualty.alive = False

try:
    Crew_Member(casualty)
except Precondition.Alive:
    pass                                # cannot join

Crew_Member(worf)
worf.alive = False                      # a crew member who died is a broken crew member
assert worf in ~Crew_Member
worf.alive = True                       # sickbay did its work
assert worf in list(Crew_Member)
```

Being alive is necessary to be crew, not sufficient: other living things
are not crew. A condition says *necessary*; membership says *is*.

`@Requirement` is the same mark in one word, for a claim that reads as a
necessity rather than as a pair of checks:

```python
class Crew_Member(Tag):

    @Requirement
    def Alive(agent):
        return agent.alive
```

A Requirement still fails under two names, and that is the point: at the
door it is `Precondition.Alive`, someone who may not come aboard;
afterwards it is `Postcondition.Alive`, someone aboard who needs sickbay.
Two repairs, two names. Asking `Requirement.Alive` for a failure of its
own is a mistake, and the refusal tells you which of the two you meant.

---

## 7. Quarantine: a gate that reads another Tag's defect

Conditions can ask about other Tags, including whether an Agent is
defective under them. Sickbay quarantines exactly the crew who are
infected, which is a broken promise of `Healthy`.

```python
class Healthy(Tag):

    @Post
    def Not_Infected(agent):
        return not agent.infected


class Quarantined(Tag):

    @Pre
    def Is_A_Case(agent):
        return agent in ~Healthy         # defective under Healthy

    @Record
    def bay(agent):
        return "isolation ward 2"

    @Rip
    def Discharge(agent):
        agent.bay = None


Healthy(worf)

try:
    Quarantined(worf)
except Precondition.Is_A_Case:
    pass                                # healthy crew are not quarantined

worf.infected = True                    # exposure, during play
assert worf in ~Healthy

try:
    Quarantined(worf)                   # the gate opens exactly now
except Postcondition.Not_Infected:
    pass                                # applied; and the tagging reports the standing defect

assert worf in Quarantined
assert worf.bay == "isolation ward 2"

worf.infected = False                   # treated
assert worf in list(Healthy)
del Quarantined[worf]                   # discharged: the Rip protocol runs
assert worf.bay is None
```

Notice the `except` around the quarantine. Every tagging re-checks every
promise on the Agent, so tagging a defective Agent applies the Tag and
then reports the defect that is still standing. Quarantine went through;
the ship's medical record still says infected. That is the point.

---

## 8. The author writes the guard

A condition is a function, and the question *does this promise still
apply to this Agent* is one line inside it. Write it in your own words
and it can follow any membership you like: another Tag's, a keyword on a
Tag, or the Tag underneath an Underlay. No law has to guess which one
you meant, and the guard is right there for the next reader.

**A promise that follows another Tag.** The weapons lock matters only
while the officer stands on the Bridge. Off the Bridge, the promise
holds, because you said so.

```python
class Armed(Tag):

    @Post
    def Weapons_Locked(agent):
        if agent not in Bridge:         # not on duty: nothing to lock
            return True
        return agent.safety_on


worf.safety_on = True
Armed(worf)
worf.safety_on = False                  # during play
assert worf in ~Armed                   # on the Bridge: the lock matters

del Bridge[worf]
assert worf in list(Armed)              # off the Bridge: it does not

worf.safety_on = True                   # a tagging re-checks every promise
Bridge(worf)
```

**A promise that follows a keyword on a Tag.** The ship's state is a
keyword on the Bridge itself, a Flag Pin. The protocol bites only while
that keyword is there.

```python
@Flag
@Pin
class Red_Alert(Tag):
    """The ship's state, not the crew's."""


class Alert_Protocol(Tag):

    @Post
    def At_Station(agent):
        if "Red_Alert" not in Bridge:   # peacetime: the protocol sleeps
            return True
        return agent.station == "tactical"


Alert_Protocol(worf)
worf.station = "mess hall"
assert worf in list(Alert_Protocol)     # nobody minds

Red_Alert(Bridge)
assert worf in ~Alert_Protocol          # to your station

worf.station = "tactical"
del Red_Alert[Bridge]
```

**An Underlay that knows whose promise the underneath is.** A Veteran's
`Alive` is laid over the crew's. If the crew role is gone, the Veteran
holds only his own clause, and the chain never calls a check of a Tag
the Agent has left.

```python
class Veteran(Tag):

    @Post
    @Underlay
    def Alive(agent, base):
        underneath = base() if agent in Crew_Member else True
        return underneath and agent.decorated


kurn = Crew("Kurn")
kurn.decorated = True
Crew_Member(kurn)
Veteran(kurn)

del Crew_Member[kurn]                   # the underneath leaves
kurn.alive = False                      # its promise no longer counts
assert kurn in list(Veteran)            # only the Veteran's own clause

kurn.decorated = False
assert kurn in ~Veteran
```

**Or end it explicitly, when the role leaves.** A condition is sticky:
Rip does not remove it, so a promise that outlives its Tag fails loud
rather than vanishing. When a promise should end with the role, the
role's own `@Rip` protocol ends it, one deliberate name at a time.

```python
class Sworn_Officer(Tag):

    @Post
    def Has_Oath(agent):
        return agent.oath is not None

    @Rip
    def Release(agent):
        Contract.Delete(agent, "Has_Oath")  # visibly, here, and nowhere else


kurn.decorated = True                   # a tagging re-checks every promise
kurn.oath = "to the Empire"
Sworn_Officer(kurn)
del Sworn_Officer[kurn]                 # released from the oath
kurn.oath = None
assert kurn in list(Veteran)            # no promise left to break
```

Both are flow control, nothing more. The guard costs one `in`; the
deletion costs one name. Each reads as the rule it is, where the rule
lives. There is no automatic law: a condition stays until you end it.

---

## 9. Reading a contract

When something is refused and you want the whole picture, ask the
contract namespace. It never guesses; it runs the checks and tells you.

```python
enterprise.core_temperature = 1400

status = Contract.Status(enterprise)
assert status == {"Core_Within_Tolerance": False}

print(f"{enterprise:contract}")
# Ship[Warp_Core, Engineering] contract:
#   Post:
#     XX  Core_Within_Tolerance

enterprise.Vent()
enterprise.Vent()
assert Contract.Holds(enterprise)
```

---

## 10. Contracts on Tags themselves

A Pin (Guide, pattern 11) puts a Tag in the Agent's seat, so everything
above applies to Tags too. Fleet command can require that a protocol Tag
has at least one trained crew member before it counts as *Certified*.

```python
@Pin
class Certified(Tag):

    @Pre
    def Has_Trained_Crew(tag):
        return bool(tag[:])


try:
    Certified(Quarantined)
except Precondition.Has_Trained_Crew:
    pass                                # nobody is quarantined right now

Certified(Bridge)                       # Worf is on the bridge
assert Bridge in Certified
```

---

## 11. The checklist

- **Gate what must be true to enter** with `@Pre`. A refused Agent is
  untouched.
- **Promise what must stay true** with `@Post`. A broken promise flags,
  never undoes.
- **Stack both**, or write `@Requirement`, when a claim is a necessity in
  both directions.
- **Catch the name**, `except Precondition.X`, `except Postcondition.X`,
  and repair what it names. Never one handler for everything.
- **Expect two failures on a published member**: `TagRogueAccessError`
  means the Agent left; a named promise means it is broken. React to each.
- **Repair from the outside** with `for broken in ~Tag`, or **at the point
  of use** with autofix. Both are ordinary Python.
- **End a condition yourself.** Rip never does. A guard in the promise,
  `if agent not in Bridge: return True`, lets it follow any membership;
  `Contract.Delete(agent, "Has_Oath")` in the role's `@Rip` protocol
  ends it when the role leaves. One visible line beats a law that
  guesses.
- **Read the contract** with `Contract.Status`, `Contract.Display`, or
  `f"{agent:contract}"` when you need the whole picture.
- **Return `True`, `False`, or nothing** from a condition. A count of `0`
  is refused as a raw value, so a real zero is never mistaken for a
  failure.
