"""The oracle: an independent model of the paradigm, checked against TopKit
after every transition.

The model knows the laws of the Specification and nothing of the kernel:
Base-first Forms, membership and history, Rip refused while a Shape
requires the Base, Scope as apply-then-rip, the call boundary (a refused
gate rolls back, a broken promise keeps the Tag and marks the Agent
defective, a failed Imprint keeps the Tag), sticky conditions ended by
the author, published members answering sound members only, condition
members read as booleans, Field algebra, and Pins with a Tag in the
Agent's seat.

A random walk applies, rips, scopes and breaks promises over a population
of Agents and of Tags; after each step the kit must agree with the model
on everything observable. A disagreement names the seed and the step, so
it can be replayed.

Run from the repository root:

    PYTHONPATH=. python3 tests/oracle_topkit.py
    PYTHONPATH=. python3 tests/oracle_topkit.py --seeds 50 --steps 1200 --population 18

The defaults are a short local probe. The unit test runs a shorter one.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
import argparse
import gc
import random
import time
import weakref

from TopKit import Apply
from TopKit import Contract
from TopKit import Imprint
from TopKit import Operation
from TopKit import Pin
from TopKit import Post
from TopKit import Pre
from TopKit import Public
from TopKit import Record
from TopKit import Report
from TopKit import Rip
from TopKit import Scope
from TopKit import Tag
from TopKit import TagCompositionError
from TopKit import TagImprintError
from TopKit import TagPostconditionError
from TopKit import TagPreconditionError
from TopKit import TagResolutionError
from TopKit import TagRogueAccessError
from TopKit import Tags


# ------------------------------------------------------------------
# The host, and the model
# ------------------------------------------------------------------


class Agent:
    def __init__(
            agent,
            name: str,
            ) -> None:
        agent.name = name
        agent.ok = True                     # what the promises read
        agent.events: list[str] = []


CLOCK = [0]                                 # ticks once per joining: Fields keep application order


@dataclass
class Model:
    """What the paradigm says about one Target."""

    active: list[type] = field(default_factory=list)
    ever: set[type] = field(default_factory=set)
    joined: dict[type, int] = field(default_factory=dict)   # when each active Tag was joined
    marked_ever: bool = False               # Marked's promise is sticky: once applied, always read
    gated_ever: bool = False                # Gated's gate is sticky too: it stays on the record
    ok: bool = True                         # the value every promise reads

    def Copy(
            model,
            ) -> "Model":
        return Model(
                list(model.active),
                set(model.ever),
                dict(model.joined),
                model.marked_ever,
                model.gated_ever,
                model.ok,
                )

    def Has_Promise(
            model,
            ) -> bool:
        return model.marked_ever or Promised in model.active

    def Sound(
            model,
            ) -> bool:
        return model.ok or not model.Has_Promise()


def Direct_Bases(
        tag: type,
        ) -> tuple[type, ...]:
    return tuple(
            base
            for base in tag.__bases__
            if isinstance(base, type(Tag)) and base is not Tag
            )


def Form(
        tag: type,
        ) -> tuple[type, ...]:
    """Base-first closure, each Tag once."""

    result: list[type] = []

    def Visit(
            current: type,
            ) -> None:
        for base in Direct_Bases(current):
            Visit(base)

        if current not in result:
            result.append(current)

    Visit(tag)

    return tuple(result)


def Leaves(
        active: list[type],
        ) -> tuple[type, ...]:
    return tuple(
            tag
            for tag in active
            if not any(
                    other is not tag and issubclass(other, tag)
                    for other in active
                    )
            )


def Model_Apply(
        model: Model,
        tag: type,
        ) -> None:
    for current in Form(tag):
        if current not in model.active:
            model.active.append(current)
            model.ever.add(current)
            CLOCK[0] += 1
            model.joined[current] = CLOCK[0]

    if tag is Marked:
        model.marked_ever = True

    if tag is Gated:
        model.gated_ever = True


def Rip_Refused(
        model: Model,
        tag: type,
        ) -> bool:
    """Rip is refused while a Shape requires the Base; it never cascades."""

    return any(
            other is not tag and issubclass(other, tag)
            for other in model.active
            )


def Model_Rip(
        model: Model,
        tag: type,
        ) -> None:
    model.active.remove(tag)
    del model.joined[tag]


# ------------------------------------------------------------------
# The Tags under test
# ------------------------------------------------------------------


def Family(
        prefix: str,
        pinned: bool = False,
        ) -> tuple[type, ...]:
    """A small Geometry: a diamond, two leaves, an independent Tag and a
    composite over both. As Pins when ``pinned``."""

    def Make(
            name: str,
            bases: tuple[type, ...],
            ) -> type:
        made = type(
                f"{prefix}_{name}",
                bases,
                {},
                )

        return Pin(made) if pinned and bases == (Tag,) else made

    root = Make("Root", (Tag,))
    left = Make("Left", (root,))
    right = Make("Right", (root,))
    bridge = Make("Bridge", (left, right))
    left_leaf = Make("Left_Leaf", (left,))
    right_leaf = Make("Right_Leaf", (right,))
    independent = Make("Independent", (Tag,))
    composite = Make("Composite", (bridge, independent))

    return (
            root,
            left,
            right,
            bridge,
            left_leaf,
            right_leaf,
            independent,
            composite,
            )


class Promised(Tag):
    """A promise that ends with the role: its @Rip deletes it."""

    @Post
    def Is_Ok(agent) -> bool:
        return agent.ok

    @Rip
    def Release(agent) -> None:
        Contract.Delete(agent, "Is_Ok")


class Marked(Tag):
    """A promise that outlives the role: sticky, as the law says."""

    @Post
    def Still_Ok(agent) -> bool:
        return agent.ok


class Guild(Tag):
    """Published members: answer sound members only."""

    @Public
    @Report
    def banner(tag) -> str:
        return "guild"

    @Public
    @Operation
    def Hail(tag, agent) -> str:
        return f"{tag.__name__} hails {agent.name}"

    def Own(agent) -> str:
        return "mine"


class Gated(Tag):
    """A gate that refuses when the Agent is not ok; the call rolls back."""

    @Pre
    def Ready(agent) -> bool:
        return agent.ok

    @Record
    def token(agent) -> str:
        return "prepared"

    @Imprint
    def Note(agent) -> None:
        agent.events.append("gated")


class Slipping(Tag):
    """An Imprint that fails after commit; the Tag stays."""

    @Imprint
    def Slip(agent) -> None:
        agent.events.append("slipped")
        raise RuntimeError("deliberate")


CONDITION_TAGS = (Promised, Marked)
FEATURE_TAGS = (Promised, Marked, Guild, Gated)


# ------------------------------------------------------------------
# Acting with the model's expectations
# ------------------------------------------------------------------


def Tag_It(
        target: object,
        tag: type,
        model: Model,
        context: str,
        **inputs: object,
        ) -> None:
    """Apply ``tag`` as the law predicts: refused at the gate, applied
    and reported defective, or applied clean."""

    if tag is Gated and not model.ok and Gated not in model.active:
        try:
            tag(target, **inputs)
        except TagPreconditionError:
            return

        raise AssertionError((context, "gate did not refuse", tag.__name__))

    pending = [member for member in Form(tag) if member not in model.active]
    Model_Apply(model, tag)
    defective_after = not model.Sound()

    try:
        tag(target, **inputs)
    except TagPostconditionError:
        if not defective_after or not pending:
            raise AssertionError((context, "promise reported where none should", tag.__name__, bool(pending)))
    else:
        if defective_after and pending:
            raise AssertionError((context, "defective tagging did not report", tag.__name__))
        # an active re-application is a no-op: nothing is re-checked (§0.7)


def Rip_It(
        target: object,
        tag: type,
        model: Model,
        context: str,
        ) -> None:
    if tag not in model.active:
        try:
            del tag[target]
        except TagResolutionError:
            return

        raise AssertionError((context, "inactive Rip succeeded", tag.__name__))

    if Rip_Refused(model, tag):
        try:
            del tag[target]
        except TagCompositionError:
            return

        raise AssertionError((context, "Rip of a required Base succeeded", tag.__name__))

    del tag[target]
    Model_Rip(model, tag)


# ------------------------------------------------------------------
# What must agree
# ------------------------------------------------------------------


def Assert_Target(
        target: object,
        model: Model,
        family: tuple[type, ...],
        context: str,
        ) -> None:
    observed = Tags(target)
    expected = Leaves(model.active)

    assert observed == expected, (context, "Tags", observed, expected)

    for tag in family + FEATURE_TAGS:
        active = tag in model.active

        assert (target in tag) is active, (context, "membership", tag.__name__, active)
        assert isinstance(target, tag) is (tag in model.ever), (context, "history", tag.__name__)

        if active:
            assert tag[target] is not None, (context, "view", tag.__name__)
        else:
            try:
                tag[target]
            except TagResolutionError:
                pass
            else:
                raise AssertionError((context, "inactive view resolved", tag.__name__))

    Assert_Contract(target, model, context)
    Assert_Published(target, model, context)


def Assert_Contract(
        target: object,
        model: Model,
        context: str,
        ) -> None:
    status = Contract.Status(target)
    expected: dict[str, bool] = {}

    if Promised in model.active:
        expected["Is_Ok"] = model.ok

    if model.marked_ever:
        expected["Still_Ok"] = model.ok

    if model.gated_ever:
        expected["Ready"] = model.ok                                  # sticky: Rip leaves the gate on the record

    assert status == expected, (context, "contract", status, expected)
    assert Contract.Holds(target) is model.Sound(), (context, "soundness", model.Sound())

    if not isinstance(target, type):
        assert bool(target) is model.Sound(), (context, "truth", model.Sound())

    for name, holds in expected.items():
        assert getattr(target, name) is holds, (context, "condition member", name, holds)

    for name in ("Is_Ok", "Still_Ok", "Ready"):
        if name not in expected:
            assert not hasattr(target, name), (context, "phantom condition member", name)


def Assert_Published(
        target: object,
        model: Model,
        context: str,
        ) -> None:
    if isinstance(target, type):
        return

    if Guild not in model.ever:
        assert not hasattr(target, "Hail"), (context, "published member before membership")
        return

    assert target.Own() == "mine", (context, "own Action")

    if Guild in model.active and model.Sound():
        assert target.Hail() == f"Guild hails {target.name}", (context, "published call")
        assert target.banner == "guild", (context, "published read")
        return

    failure = TagRogueAccessError if Guild not in model.active else TagPostconditionError

    for act in (
            lambda: target.Hail(),
            lambda: target.banner,
            ):
        try:
            act()
        except failure:
            continue

        raise AssertionError((context, "published member answered", failure.__name__))


def Assert_Fields(
        targets: list[object],
        models: dict[int, Model],
        family: tuple[type, ...],
        context: str,
        ) -> None:
    """Every Field over these targets agrees with the model, and so does
    the algebra. The feature Tags are checked with the Agents only: their
    Fields span the Agent population, never the Tags."""

    tags = family if isinstance(targets[0], type) else family + FEATURE_TAGS

    def Population(
            tag: type,
            ) -> list[object]:
        members = [t for t in targets if tag in models[id(t)].active]

        return sorted(members, key=lambda t: models[id(t)].joined[tag])   # application order

    def Sound(
            tag: type,
            ) -> list[object]:
        return [t for t in Population(tag) if models[id(t)].Sound()]

    for tag in tags:
        whole = Population(tag)
        sound = Sound(tag)
        defective = [t for t in whole if t not in sound]

        assert list(tag[:]) == whole, (context, "whole Field", tag.__name__, Names(tag[:]), Names(whole))
        assert list(tag) == sound, (context, "sound Field", tag.__name__)
        assert list(~tag) == defective, (context, "defective Field", tag.__name__)
        assert len(tag) == len(sound) and bool(tag) is bool(sound), (context, "Field size", tag.__name__)

    first, second = family[0], family[6]
    assert list(first | second) == Union(Sound(first), Sound(second)), (context, "sound union")
    assert list(first[:] | second[:]) == Union(Population(first), Population(second)), (context, "whole union")
    assert list(first & second) == [t for t in Sound(first) if t in Sound(second)], (context, "intersection")
    assert list(first - second) == [t for t in Sound(first) if t not in Sound(second)], (context, "difference")
    assert list(~first | second) == Union(
            [t for t in Population(first) if t not in Sound(first)],
            Sound(second),
            ), (context, "defective union")


def Names(
        population: object,
        ) -> list[str]:
    return [getattr(t, "__name__", None) or t.name for t in population]


def Union(
        left: list[object],
        right: list[object],
        ) -> list[object]:
    seen = {id(t) for t in left}

    return left + [t for t in right if id(t) not in seen]


# ------------------------------------------------------------------
# One seed
# ------------------------------------------------------------------


def Run_Seed(
        seed: int,
        steps: int,
        population: int,
        ) -> int:
    randomizer = random.Random(seed)
    agent_family = Family(f"S{seed}_A")
    pin_family = Family(f"S{seed}_P", pinned=True)
    agents = [Agent(f"agent-{seed}-{index}") for index in range(population)]
    entries = [type(f"S{seed}_Entry_{index}", (Tag,), {}) for index in range(max(2, population // 3))]
    agent_models = {id(target): Model() for target in agents}
    entry_models = {id(target): Model() for target in entries}
    transitions = 0

    for step in range(steps):
        use_pins = randomizer.random() < 0.25
        targets = entries if use_pins else agents
        models = entry_models if use_pins else agent_models
        family = pin_family if use_pins else agent_family
        target = randomizer.choice(targets)
        model = models[id(target)]
        context = f"seed={seed} step={step} target={getattr(target, '__name__', None) or target.name}"
        choice = randomizer.randrange(12)

        if choice <= 2:
            Tag_It(target, randomizer.choice(family), model, context)
        elif choice == 3:
            first, second = randomizer.choice(family), randomizer.choice(family)
            Tag_It(target, first, model, context)
            Tag_It(target, second, model, context)
        elif choice == 4:
            candidates = list(model.active) or list(family)
            Rip_It(target, randomizer.choice(candidates), model, context)
        elif choice in (5, 6):
            Exercise_Scope(target, model, family, randomizer, context, fail=choice == 6)
        elif choice == 7 and not use_pins:
            Tag_It(target, randomizer.choice(FEATURE_TAGS), model, context)
        elif choice == 8 and not use_pins:
            target.ok = not target.ok
            model.ok = target.ok
        elif choice == 9 and not use_pins:
            Exercise_Transactions(target, model, context)
        elif choice == 10:
            tag = randomizer.choice(family)
            Tag_It(target, tag, model, context)
            Tag_It(target, tag, model, context)                       # active re-application: a no-op
        else:
            first = randomizer.choice(family)
            before = model.Copy()

            try:
                Apply(target, first, object())
            except (TypeError, TagPostconditionError):
                pass
            else:
                raise AssertionError((context, "invalid Apply succeeded"))

            Model_Apply(model, first)                                 # Apply is a plain loop: the first landed

        Assert_Target(target, model, family, context)

        if step % 17 == 0:
            Assert_Fields(targets, models, family, context)

            for candidate in targets:
                Assert_Target(candidate, models[id(candidate)], family, context)

        transitions += 1

    Assert_Fields(agents, agent_models, agent_family, f"seed={seed} end")
    Assert_Fields(entries, entry_models, pin_family, f"seed={seed} end")

    return transitions


def Exercise_Scope(
        target: object,
        model: Model,
        family: tuple[type, ...],
        randomizer: random.Random,
        context: str,
        fail: bool,
        ) -> None:
    """Scope applies, runs the block, and rips what it applied in reverse
    on exit, even when the block raises. Bases a Shape brought in stay;
    a Rip refused for a required Base is swallowed and the Tag stays."""

    scoped = tuple(randomizer.choice(family) for _ in range(1 + randomizer.randrange(3)))
    entry = model.Copy()
    inside = model.Copy()
    joined_by_scope: list[type] = []

    for tag in scoped:
        if tag not in inside.active:
            Model_Apply(inside, tag)
            joined_by_scope.append(tag)

            if not inside.Sound():
                break                                                 # the first tagging on a defective Agent reports; the body never runs

    defective = bool(joined_by_scope) and not inside.Sound()      # only a tagging re-checks; a skipped Tag does not

    try:
        with Scope(target, *scoped):
            assert not defective, (context, "a defective tagging let the Scope body run")
            Assert_Target(target, inside, family, context + " inside")

            if fail:
                raise LookupError("deliberate")
    except LookupError:
        if not fail:
            raise
    except TagPostconditionError:
        if not defective:
            raise

    after = inside

    for tag in reversed(joined_by_scope):
        if tag in after.active and not Rip_Refused(after, tag):
            Model_Rip(after, tag)

    model.active = after.active
    model.ever = after.ever
    model.joined = after.joined
    model.marked_ever = after.marked_ever
    model.gated_ever = after.gated_ever


def Exercise_Transactions(
        target: object,
        model: Model,
        context: str,
        ) -> None:
    """The call boundary: a refused gate rolls the call back, a failed
    Imprint keeps the Tag."""

    if not model.Sound():
        return

    events_before = list(target.events)

    if Gated not in model.active:
        target.ok = False
        model.ok = False

        if not model.Sound():
            target.ok = True
            model.ok = True
        else:
            try:
                Gated(target)
            except TagPreconditionError:
                pass
            else:
                raise AssertionError((context, "gate accepted a not-ok Agent"))

            assert target not in Gated, (context, "gate rollback: membership")
            assert target.events == events_before, (context, "gate ran the Imprint")

            if not model.gated_ever:
                assert not hasattr(target, "token"), (context, "gate rollback: Record")      # sticky once ever applied
            target.ok = True
            model.ok = True

    if Slipping not in model.active:
        try:
            Slipping(target)
        except TagImprintError:
            pass
        else:
            raise AssertionError((context, "failed Imprint did not report"))

        Model_Apply(model, Slipping)
        assert target in Slipping and target.events[-1] == "slipped", (context, "Imprint failure kept the Tag")
        del Slipping[target]
        Model_Rip(model, Slipping)


def Weak_Field_Probe(
        count: int,
        ) -> None:
    class Ephemeral(Tag):
        pass

    agents = [Agent(f"ephemeral-{index}") for index in range(count)]

    for target in agents:
        Ephemeral(target)

    assert len(Ephemeral[:]) == count
    references = [weakref.ref(target) for target in agents]
    agents.clear()
    del target
    gc.collect()

    assert len(Ephemeral[:]) == 0, "a Field kept an Agent alive"
    assert all(reference() is None for reference in references)


def Main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--first-seed", type=int, default=1701)
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--steps", type=int, default=400)
    parser.add_argument("--population", type=int, default=9)
    arguments = parser.parse_args()
    started = time.perf_counter()
    transitions = 0

    for seed in range(arguments.first_seed, arguments.first_seed + arguments.seeds):
        transitions += Run_Seed(seed, arguments.steps, arguments.population)

    Weak_Field_Probe(max(200, arguments.population * 20))
    duration = time.perf_counter() - started

    print(
            "PASS",
            f"seeds={arguments.first_seed}..{arguments.first_seed + arguments.seeds - 1}",
            f"transitions={transitions}",
            f"seconds={duration:.3f}",
            )


if __name__ == "__main__":
    Main()
