# Constant Contributions

`@Constant` fixes a Contribution's binding. A Record keeps its initialized
value; an Action or Operation keeps its implementation; a Post keeps its
promise. A Constant Report belongs to its declaring Tag. Applying a Shape
also applies that Base to the Agent; the Shape itself does not acquire the
Report as a direct Tag member.

Constant protects the binding, not everything inside the value. It also
does not change who may access the Contribution: `@Public` and `@Secret`
still set their own boundaries. The examples below run in order.

## A fixed Record can hold a mutable value

```python
from TopKit import (Action, Constant, Contract, Delete, Imprint, Operation,
                    Post, Record, Report, Tag, TagCompositionError,
                    TagDeclarationError)


class Host:
    def __init__(agent):
        agent.trainings = 0


class Issued(Tag):
    @Constant
    @Record
    def equipment(agent):
        return []

    @Record
    def scratch(agent):
        return []

    @Imprint
    def Train(agent):
        agent.trainings += 1


ari, bo = Host(), Host()
Issued(ari)
Issued(bo)
ari.equipment.append("compass")
assert ari.equipment == ["compass"]
assert bo.equipment == []
assert ari.equipment is not bo.equipment
```

The builder gives each Agent its own value. Adding to the list is allowed;
replacing or deleting its binding is refused:

```python
try:
    ari.equipment = []
except TagCompositionError:
    pass
else:
    raise AssertionError("a Constant binding was replaced")

try:
    del ari.equipment
except TagCompositionError:
    pass
else:
    raise AssertionError("a Constant binding was deleted")

assert ari.equipment == ["compass"]
```

`@Constant @Record` and `@Record @Constant` mean the same thing. The
modifier also stacks in either order with the other supported Contribution
declarations. It can mark a named Post; it cannot turn an anonymous
expression into a registered promise.

## One Constant Report on its declaring Tag

```python
initialized_for = []


class Network(Tag):
    @Report
    @Constant
    def directory(tag):
        initialized_for.append(tag)
        return {}

    @Constant
    @Operation
    def Name(tag):
        return tag.__name__


class East(Network):
    pass


class West(Network):
    pass


assert initialized_for == []
directory = Network.directory
assert initialized_for == [Network]     # the builder received its owner
assert directory is Network.directory
try:
    East.directory
except AttributeError:
    pass
else:
    raise AssertionError("a Shape acquired its Base's Report")
directory["dispatch"] = "ready"
assert Network.directory == {"dispatch": "ready"}
assert initialized_for == [Network]
assert Network.Name() == "Network"
try:
    West.Name()
except AttributeError:
    pass
else:
    raise AssertionError("a Shape acquired its Base's Operation")
```

A Constant Report initializes lazily on its declaring Tag, once. Its
contents can still change, as the shared dictionary shows. The Shape
cannot redeclare its name, and an Agent tagged with the Shape can read
the Base's value through its Base view or publication.

A Constant Operation keeps its implementation and receives its declaring
Tag when called directly. It is not a cached result. A Constant Action likewise
runs normally on its Agent; Constant does not make its work read-only.

## Keep a promise, and add other promises by their own names

```python
class Equipped(Tag):
    @Post
    @Constant
    def Has_Equipment(agent):
        return "equipment" @ agent

    @Action
    def Replace_Equipment(agent):
        agent.equipment = ["replacement"]


Equipped(ari)
assert ari
try:
    ari.Replace_Equipment()
except TagCompositionError:
    pass
else:
    raise AssertionError("an Action replaced a Constant binding")

del Equipped[ari]
assert ari.Has_Equipment
assert ari
```

The Post remains after Rip. An Action, Imprint or Rip protocol cannot
replace or delete it, and `Contract.Delete` cannot end it. A later Tag may
add independent Posts with different names; it cannot substitute its own
check for this one. The fixed check still evaluates current state whenever
TOP checks the contract. It is not an always-true result, and it does not
run continuously between those checks.

Use an explicit Boolean return for a check that must work under
`python -O`, `python -OO` or a nonzero `PYTHONOPTIMIZE` setting; Python
removes `assert` statements in those modes. Constant still locks the Post's
binding, but cannot restore the removed check.

## A later Layer cannot hide a Constant

```python
class Clear_Equipment(Tag):
    @Delete
    def equipment(agent): ...


try:
    Clear_Equipment(ari)
except TagCompositionError:
    pass
else:
    raise AssertionError("a Layer deleted a Constant binding")

assert ari.equipment == ["compass"]

try:
    class Other_Network(Network):
        directory = {}
except TagDeclarationError:
    pass
else:
    raise AssertionError("a Shape shadowed a Constant Report")
```

Replacing through another Contribution kind, `@Underlay`, a Pin, or a
direct write cannot bypass the protection. A Shape cannot redeclare a
Base's Constant name in its class body, even as an ordinary Python value.
The attempted change fails while the existing Constant stays intact.

## Reapplication keeps Constants and repeats the other work

```python
original = ari.equipment
ari.scratch.append("old training notes")
assert ari.trainings == 1
del Issued[ari]
Issued(ari)
assert ari.equipment is original
assert ari.equipment == ["compass"]
assert ari.scratch == []
assert ari.trainings == 2
```

Applying an already active Tag remains a no-op. After Rip, applying that
same Tag preserves its established Constants while rebuilding ordinary
Records and running Imprints again. It does not rerun Constant Record
builders or create a second Constant Report value.

These guarantees cover TOP composition and normal Python member writes
and deletions, including `object.__setattr__` on protected Agent bindings.
They do not make arbitrary Python code a security sandbox: editing private
runtime state or tampering directly with namespaces is outside the contract.

See [the Guide](GUIDE.md) for Contributions and
[Contracts](CONTRACTS.md) for when promises are checked.
