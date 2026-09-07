# The Contracts Guide

*Gates, promises, privileges, and what to do when they fail.*

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
        Action, Contract, Operation, Pin, Post, Postcondition, Pre,
        Precondition, Public, Record, Report, Rip, Tag,
        TagPrivilegeError,
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
| "You will stay like this" | `@Post` | at the door, then at every tagging and every use of a privilege | the Tag stays; the Agent is **defective** |
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
privilege. When it breaks, TOP does not undo anything. The product left
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

**Soundness is holistic.** The privilege refused because *a* promise on
the ship was broken, not because Engineering's own promises were. A ship
with a working helm and a failing core is not cleared to engage. If a
Shape needs to relax a Base's promise, it deletes it in its Overlay; a
promise is never quietly ignored.

---

## 5. Privileges: relieved of duty

What the Agent does is its own. What the Agency shares is a privilege.
When a crew member leaves the Bridge, she keeps everything she became,
and loses what the Bridge lent her.

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
assert not hasattr(worf, "alert")                # the Agency's: gone

try:
    worf.Fire("asteroid")
except TagPrivilegeError:
    pass                                # a Rogue Agent, refused

try:
    fire("asteroid")                    # the stale handle fails the same way
except TagPrivilegeError:
    pass

Bridge(worf)                            # reinstated: privileges return
assert worf.Fire("asteroid") == "Worf fires at asteroid"
```

Two failures, two meanings. `TagPrivilegeError` says *you left*.
`Postcondition.Something` says *you are broken*. A program that catches
them separately reacts correctly to each without reading a word of text.

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

## 8. Reading a contract

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

## 9. Contracts on Tags themselves

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

## 10. The checklist

- **Gate what must be true to enter** with `@Pre`. A refused Agent is
  untouched.
- **Promise what must stay true** with `@Post`. A broken promise flags,
  never undoes.
- **Stack both** when a claim is a necessity in both directions.
- **Catch the name**, `except Precondition.X`, `except Postcondition.X`,
  and repair what it names. Never one handler for everything.
- **Expect two failures on a privilege**: `TagPrivilegeError` means the
  Agent left; a named promise means it is broken. React to each.
- **Repair from the outside** with `for broken in ~Tag`, or **at the point
  of use** with autofix. Both are ordinary Python.
- **Read the contract** with `Contract.Status`, `Contract.Display`, or
  `f"{agent:contract}"` when you need the whole picture.
- **Return `True`, `False`, or nothing** from a condition. A count of `0`
  is refused as a raw value, so a real zero is never mistaken for a
  failure.
