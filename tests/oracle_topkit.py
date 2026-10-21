"""The oracle: an independent model of the paradigm, checked against TopKit
after every transition.

The model knows the laws of the Specification and nothing of the kernel:
Base-first Forms, independent membership after admission, Rip of one Tag
without cascading into its Shapes, a block that holds Tags (tag before
try, Rip in finally), the call boundary (each Tag gates at its own turn, acquired
Gains precede admission, ordinary training failures warn and continue,
completed training enters the Field, and Posts judge each Tag before the
next turn), membership-bound ordinary Posts, published members answering
sound members only, condition
members read as booleans, Field algebra, Pins with a Tag in the
Agent's seat, and keywords: a Flag answers to its name and its words,
through the Form, and a word is never membership.

A random walk applies, rips, holds Tags for a block and breaks promises
over a population of Agents and of Tags; after each step the kit must agree with the model
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
import warnings

from TopKit import Apply
from TopKit import Contract
from TopKit import Flag
from TopKit import Imprint
from TopKit import Keyword
from TopKit import Operation
from TopKit import Pin
from TopKit import Post
from TopKit import Pre
from TopKit import Public
from TopKit import Record
from TopKit import Report
from TopKit import Rip
from TopKit import Tag
from TopKit import TagCompositionError
from TopKit import TagPostconditionError
from TopKit import TagPreconditionError
from TopKit import TagResolutionError
from TopKit import TagRogueAccessError
from TopKit import TagTrainingWarning
from TopKit import Tags
from TopKit import Tool


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
        agent.slipping_allowed = True
        agent.slipping_fails = True


CLOCK = [0]                                 # ticks once per joining: Fields keep application order
WORDS: dict[type, frozenset[str]] = {}      # what the model knows each Flag answers to


@dataclass
class Model:
    """What the paradigm says about one Target."""

    active: list[type] = field(default_factory=list)
    ever: set[type] = field(default_factory=set)
    joined: dict[type, int] = field(default_factory=dict)   # when each active Tag was joined
    ok: bool = True                         # the value every promise reads
    gained: set[type] = field(default_factory=set)   # independent of Field entry and history
    slipping_round: int = 0                 # sticky Record rebuilt on each training attempt
    slipping_allowed: bool = True          # the retryable Tag's Gate
    slipping_fails: bool = True            # Record and Imprint calculations fail together
    slipping_optional: bool = False        # successfully initialized value remains sticky

    def Copy(
            model,
            ) -> "Model":
        return Model(
                list(model.active),
                set(model.ever),
                dict(model.joined),
                model.ok,
                set(model.gained),
                model.slipping_round,
                model.slipping_allowed,
                model.slipping_fails,
                model.slipping_optional,
                )

    def Has_Promise(
            model,
            ) -> bool:
        return any(
                tag in model.active
                for tag in (Promised, Marked, Slipping)
                )

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


def Model_Gain(
        model: Model,
        tag: type,
        ) -> None:
    """The actual Gains persist even if the following training fails."""

    model.gained.add(tag)
    if tag is Slipping:
        model.slipping_round += 1
        if not model.slipping_fails:
            model.slipping_optional = True


def Model_Apply(
        model: Model,
        tag: type,
        ) -> None:
    if tag in model.active:
        return

    for current in Form(tag):
        if current not in model.active:
            Model_Gain(model, current)
            model.active.append(current)
            model.ever.add(current)
            CLOCK[0] += 1
            model.joined[current] = CLOCK[0]


def Model_Tagging(
        model: Model,
        tag: type,
        ) -> type[Exception] | None:
    """Each missing Tag needs a sound source, its own Gate and its own
    Post inspection. A failed ordinary training step still admits that
    Tag; a failed Post stops the Form there. Active reapplication is a no-op.
    """

    if tag in model.active:
        return None

    for current in Form(tag):
        if current in model.active:
            continue
        if not model.Sound():
            return TagCompositionError
        if (current is Gated and not model.ok) or (
                current is Slipping and not model.slipping_allowed):
            return TagPreconditionError
        Model_Gain(model, current)
        model.active.append(current)
        model.ever.add(current)
        CLOCK[0] += 1
        model.joined[current] = CLOCK[0]
        if not model.Sound():
            return TagPostconditionError
    return None


def Rip_Failure(
        model: Model,
        tag: type,
        ) -> type[Exception] | None:
    """The failure a Rip of ``tag`` raises, or None when it Rips."""

    if tag not in model.active:
        return TagResolutionError

    return None


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

    def Words(
            tag: type,
            *aliases: str,
            ) -> None:
        WORDS[tag] = frozenset({tag.__name__, *aliases})
        Flag(*aliases)(tag) if aliases else Flag(tag)

    root = Make("Root", (Tag,))
    left = Make("Left", (root,))
    right = Make("Right", (root,))
    bridge = Make("Bridge", (left, right))
    left_leaf = Make("Left_Leaf", (left,))
    right_leaf = Make("Right_Leaf", (right,))
    independent = Make("Independent", (Tag,))
    composite = Make("Composite", (bridge, independent))

    Words(root, f"{prefix}_Kin")                                   # every Shape below says it, through the Base
    Words(right)                                                    # the name alone
    Words(left_leaf, f"{prefix}_Kin", f"{prefix}_Right")            # a shared word, and another Flag's name
    Words(independent, f"{prefix}_Loner", f"{prefix}_Kin")
    Words(composite)

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
    """An ordinary promise: it lives exactly while this membership does."""

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
    """A Gate that refuses when the Agent is not ok."""

    @Pre
    def Ready(agent) -> bool:
        return agent.ok

    @Record
    def token(agent) -> str:
        return "prepared"

    @Imprint
    def Note(agent) -> None:
        agent.events.append("gated")


class Gear(Tag):
    """What a tool IS: the kind an Armed Agent's slot admits."""


class Armed(Tag):
    """A Tool slot (STEP-SPEC-36): the forge Tags the gear in plain
    sight; the slot admits only a Gear, never None, never the bearer."""

    @Tool(Gear)
    def gear(agent, *, gear) -> object:
        return gear


class Carrying(Tag):
    """A Tool slot kinded by a class (STEP-SPEC-36): any Agent-hosted
    object, tagged or not; the bearer itself included."""

    @Tool(Agent)
    def pack(agent) -> object:
        return Agent(f"{agent.name}'s pack")


class Slipping(Guild):
    """Best-effort training: failed steps warn, later steps still run."""

    @Pre
    def Can_Slip(agent) -> bool:
        return agent.slipping_allowed

    @Record
    def slipping_optional(agent) -> str:
        if agent.slipping_fails:
            raise RuntimeError("deliberate Record failure")
        return "prepared"

    @Record
    def slipping_round(agent, stored) -> int:
        return (stored or 0) + 1

    def Read_Slip(agent) -> int:
        return agent.slipping_round

    @Post
    def Slip_Ready(agent) -> bool:
        return agent.ok

    @Imprint
    def Slip(agent) -> None:
        agent.events.append("slipped")
        if agent.slipping_fails:
            raise RuntimeError("deliberate")

    @Imprint
    def Continue(agent) -> None:
        agent.events.append("continued")


SOURCE_GATES: list[int] = []
SHAPE_GATES: list[int] = []


class Promised_Shape(Promised):
    """The Base's completed Post inspection precedes this Shape's Gate."""

    @Pre
    def Inspect(agent) -> bool:
        SHAPE_GATES.append(id(agent))
        return True


class Source_Probe(Tag):
    """Instrumentation: a broken source must never reach this Gate."""

    @Pre
    def Enter(agent) -> bool:
        SOURCE_GATES.append(id(agent))
        return True

    @Record
    def source_payload(agent) -> str:
        agent.events.append("source Record")
        return "prepared"

    @Imprint
    def Train(agent) -> None:
        agent.events.append("source Imprint")


class Refused_Guild(Guild):
    """Its Base completes, then this Shape refuses at its own Gate."""

    @Pre
    def Never(agent) -> bool:
        return False

    @Record
    def refused_record(agent) -> str:
        return "must not be built"


CONDITION_TAGS = (Promised, Marked)
FEATURE_TAGS = (Promised, Marked, Guild, Gated)
OBSERVED_TAGS = FEATURE_TAGS + (Slipping, Source_Probe, Promised_Shape)


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

    failure = Model_Tagging(model, tag)

    try:
        tag(target, **inputs)
    except (TagCompositionError, TagPreconditionError, TagPostconditionError) as error:
        if failure is None or not isinstance(error, failure):
            raise AssertionError((context, "unexpected Tagging failure", tag.__name__, type(error).__name__, failure)) from error
    else:
        if failure is not None:
            raise AssertionError((context, "Tagging did not refuse or report", tag.__name__, failure))


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

    for tag in family + OBSERVED_TAGS:
        active = tag in model.active

        assert (target in tag[:]) is active, (context, "membership", tag.__name__, active)
        assert (target in tag) is (active and model.Sound()), (
                context, "sound membership", tag.__name__, active, model.Sound()
                )
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
    Assert_Keywords(target, model, family, context)


def Assert_Keywords(
        target: object,
        model: Model,
        family: tuple[type, ...],
        context: str,
        ) -> None:
    """A word answers while an active Tag of the Form is a Flag that says
    it; a class answers only for an active Flag itself. The Agent's `in`
    is defined while a Flag is active; on a Tag, `in` always takes a
    string as a word."""

    vocabulary = sorted(
            {word for tag in family for word in WORDS.get(tag, ())}
            | {tag.__name__ for tag in family}
            | {"Stranger", family[0].__name__.lower()}
            )
    seated = isinstance(target, type) or any(tag in WORDS for tag in model.active)

    for word in vocabulary:
        expected = any(word in WORDS.get(tag, ()) for tag in model.active)

        assert Keyword(target, word) is expected, (context, "keyword", word, expected)

        if seated:
            assert (word in target) is expected, (context, "word in", word, expected)

    for tag in family:
        expected = tag in model.active and tag in WORDS

        assert Keyword(target, tag) is expected, (context, "keyword class", tag.__name__, expected)

        if seated and not isinstance(target, type):
            assert (tag in target) is expected, (context, "class in", tag.__name__, expected)


def Assert_Contract(
        target: object,
        model: Model,
        context: str,
        ) -> None:
    status = Contract.Status(target)
    expected: dict[str, bool] = {}

    if Promised in model.active:
        expected["Is_Ok"] = model.ok

    if Marked in model.active:
        expected["Still_Ok"] = model.ok

    if Slipping in model.active:
        expected["Slip_Ready"] = model.ok

    if Slipping in model.gained:
        assert "slipping_round" @ target, (context, "missing acquired Record")
        assert "Read_Slip" @ target, (context, "missing acquired Action")
        assert target.slipping_round == model.slipping_round, (context, "retry Record")
        assert target.Read_Slip() == model.slipping_round, (context, "Rogue Action")
        assert ("slipping_optional" @ target) is model.slipping_optional, (context, "failed Record initialization")
        if model.slipping_optional:
            assert target.slipping_optional == "prepared", (context, "initialized Record")

    assert status == expected, (context, "contract", status, expected)
    assert bool(target) is model.Sound(), (context, "truth", model.Sound())

    for name, holds in expected.items():
        assert getattr(target, name) is holds, (context, "condition member", name, holds)

    for name in ("Is_Ok", "Still_Ok", "Ready", "Can_Slip", "Slip_Ready"):
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

    tags = family if isinstance(targets[0], type) else family + OBSERVED_TAGS

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
        assert list(~~tag) == defective, (context, "~ absorbs", tag.__name__)
        assert len(tag) == len(sound), (context, "sound Field size", tag.__name__)
        assert len(tag[:]) == len(whole), (context, "whole Field size", tag.__name__)
        assert len(~tag) == len(defective), (context, "defective Field size", tag.__name__)

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
        choice = randomizer.randrange(13)

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
            Exercise_Block(target, model, family, randomizer, context, fail=choice == 6)
        elif choice == 7 and not use_pins:
            Tag_It(target, randomizer.choice(FEATURE_TAGS), model, context)
        elif choice == 8 and not use_pins:
            target.ok = not target.ok
            model.ok = target.ok
        elif choice == 9 and not use_pins:
            Exercise_Transactions(target, model, context)
            Exercise_Tools(target, model, context)
        elif choice == 10:
            tag = randomizer.choice(family)
            Tag_It(target, tag, model, context)
            Tag_It(target, tag, model, context)                       # active re-application: a no-op
        elif choice == 12 and not use_pins:
            Exercise_Refused_Source(target, model, context)
        else:
            first = randomizer.choice(family)
            expected = Model_Tagging(model, first)

            try:
                Apply(target, first, object())
            except (TypeError, TagPostconditionError, TagCompositionError) as error:
                assert (isinstance(error, TypeError) if expected is None else isinstance(error, expected)), (
                        context, "Apply failed at the wrong turn", type(error).__name__, expected,
                        )
            else:
                raise AssertionError((context, "invalid Apply succeeded"))

        Assert_Target(target, model, family, context)

        if step % 17 == 0:
            Assert_Fields(targets, models, family, context)

            for candidate in targets:
                Assert_Target(candidate, models[id(candidate)], family, context)

        transitions += 1

    Assert_Fields(agents, agent_models, agent_family, f"seed={seed} end")
    Assert_Fields(entries, entry_models, pin_family, f"seed={seed} end")

    return transitions


def Exercise_Block(
        target: object,
        model: Model,
        family: tuple[type, ...],
        randomizer: random.Random,
        context: str,
        fail: bool,
        ) -> None:
    """A block that holds Tags, written as a program writes it (STEP-SPEC-31,
    form 3): every Tag is tagged before the ``try``, and Ripped in reverse
    in the ``finally``. A Post failure raises before the ``try``: the block
    never runs, nothing is Ripped, and completed Tags stay.
    A Rip in the ``finally`` raises as any Rip does, and the Rips after it
    do not run; if the block was raising, its error is the Rip's context."""

    held = tuple(randomizer.choice(family) for _ in range(1 + randomizer.randrange(3)))
    inside = model.Copy()
    door: type | None = None
    door_failure: type[Exception] | None = None

    for tag in held:
        door_failure = Model_Tagging(inside, tag)
        if door_failure is not None:
            door = tag                                                # reports at the door: the try never starts
            break

    after = inside.Copy()
    refusal: type[Exception] | None = None

    if door is None:
        for tag in reversed(held):
            refusal = Rip_Failure(after, tag)

            if refusal is not None:
                break                                                 # its error leaves at once: the Rips after it do not run

            Model_Rip(after, tag)

    ran: list[bool] = []

    def Hold() -> None:
        for tag in held:
            tag(target)                                               # tag before the try

        try:
            ran.append(True)
            Assert_Target(target, inside, family, context + " inside")

            if fail:
                raise LookupError("deliberate")                       # a new one each time: a kept error would keep its frames
        finally:
            for tag in reversed(held):
                del tag[target]                                       # Rip in the finally

    try:
        Hold()
    except TagPostconditionError:
        assert door is not None and door_failure is TagPostconditionError, (context, "a door failure the model does not predict")
        assert not ran, (context, "the block ran after a door failure")
    except (TagResolutionError, TagCompositionError) as error:
        if door is not None:
            assert isinstance(error, door_failure), (context, "wrong Tagging refusal before block", type(error).__name__)
            assert not ran, (context, "the block ran after a source refusal")
        else:
            assert type(error) is refusal, (context, "a Rip the model does not refuse failed", type(error).__name__)
            assert Is_Block_Error(error.__context__) is fail, (context, "the Rip's context is not the block's error")
            assert fail or error.__context__ is None, (context, "a Rip's failure carries a context of its own")
    except LookupError as error:
        assert Is_Block_Error(error) and refusal is None, (context, "the block's error reached the caller past a failed Rip")
    else:
        assert door is None and refusal is None and not fail, (context, "the block ended where the model raises")

    final = inside if door is not None else after
    model.active = final.active
    model.ever = final.ever
    model.joined = final.joined
    model.gained = final.gained
    model.slipping_round = final.slipping_round
    model.slipping_allowed = final.slipping_allowed
    model.slipping_fails = final.slipping_fails
    model.slipping_optional = final.slipping_optional


def Is_Block_Error(
        error: BaseException | None,
        ) -> bool:
    """Whether ``error`` is the one a failing block raises."""

    return type(error) is LookupError and error.args == ("deliberate",)


def Exercise_Refused_Source(target: object, model: Model, context: str) -> None:
    """A fresh orthogonal Tag cannot inspect or train a broken source."""

    if model.Sound() and not model.ok and Promised not in model.active:
        # A valid Agent without this obligation can start the Base. Its
        # failed Post then stops the Form before the later Shape's Gate.
        shapes = len(SHAPE_GATES)
        Tag_It(target, Promised_Shape, model, context + " Base Post boundary")
        assert target in Promised[:], (context, "failed Base Post lost membership")
        assert target not in Promised_Shape[:], (context, "Shape entered after failed Base Post")
        assert len(SHAPE_GATES) == shapes, (context, "later Shape Gate preceded Base Posts")
    if model.Sound():
        return
    events = list(target.events)
    gates = len(SOURCE_GATES)
    active = Tags(target)
    try:
        Source_Probe(target)
    except TagCompositionError:
        pass
    else:
        raise AssertionError((context, "a broken source accepted fresh Tagging"))
    assert Tags(target) == active, (context, "source refusal changed existing Tags")
    assert len(SOURCE_GATES) == gates, (context, "broken source reached Gate")
    assert target.events == events, (context, "broken source began training")
    assert not ("source_payload" @ target), (context, "source refusal acquired a Record")
    assert target not in Source_Probe[:], (context, "source refusal entered Field")
    assert not isinstance(target, Source_Probe), (context, "source refusal acquired history")


def Exercise_Transactions(
        target: object,
        model: Model,
        context: str,
        ) -> None:
    """Failed training admits, active reTag is a no-op, Rip permits retraining."""

    if not model.Sound():
        return

    events_before = list(target.events)

    if Guild not in model.active:
        try:
            Refused_Guild(target)
        except TagPreconditionError.Never:
            pass
        else:
            raise AssertionError((context, "later Gate accepted the Agent"))

        Model_Apply(model, Guild)
        assert target in Guild, (context, "later Gate removed its completed Base")
        assert target not in Refused_Guild, (context, "refused Shape entered its Field")
        assert not hasattr(target, "refused_record"), (context, "refused Shape built a Record")

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

            assert target not in Gated, (context, "Gate refusal: membership")
            assert target.events == events_before, (context, "gate ran the Imprint")

            if Gated not in model.gained:
                assert not hasattr(target, "token"), (context, "Gate refusal: Record")      # sticky once ever applied
            target.ok = True
            model.ok = True

    if Slipping not in model.active:
        target.slipping_fails = True
        model.slipping_fails = True
        target.slipping_allowed = True
        model.slipping_allowed = True
        clock_before = CLOCK[0]
        had_guild = Guild in model.active
        with warnings.catch_warnings(record=True) as notices:
            warnings.simplefilter("always", TagTrainingWarning)
            Tag_It(target, Slipping, model, context + " failed training")
        training = [notice.message for notice in notices if isinstance(notice.message, TagTrainingWarning)]
        assert [notice.name for notice in training] == ["slipping_optional", "Slip"], (
                context, "failed steps must each warn", [str(notice) for notice in training],
                )
        assert target in Slipping[:], (context, "completed best-effort training did not enter Field")
        assert (target in Slipping) is model.Sound(), (context, "Posts did not judge failed training")
        assert isinstance(target, Slipping), (context, "admission did not record history")
        assert Slipping[target].Read_Slip() == model.slipping_round, (context, "admitted training has no view")
        assert target.events[-2:] == ["slipped", "continued"], (context, "a failed Imprint stopped later Imprints")
        assert CLOCK[0] == clock_before + (not had_guild) + 1, (context, "training admission join order")
        Assert_Contract(target, model, context + " failed training")

        # An active Tagging does not restart training or recheck its Gate.
        target.slipping_allowed = False
        model.slipping_allowed = False
        round_before = model.slipping_round
        events_before_retry = list(target.events)
        Slipping(target)
        assert target.slipping_round == round_before, (context, "active retag rebuilt Gains")
        assert target.events == events_before_retry, (context, "active retag retrained")
        del Slipping[target]
        Model_Rip(model, Slipping)

        # After Rip, a refused Gate preserves the completed earlier training.
        try:
            Slipping(target)
        except TagPreconditionError.Can_Slip:
            pass
        else:
            raise AssertionError((context, "retry Gate accepted"))
        assert target.slipping_round == round_before, (context, "refusal erased or rebuilt Gains")
        assert target.events == events_before_retry, (context, "refusal retrained")
        Assert_Contract(target, model, context + " refused retry")

        # Fresh Tagging restarts training against the current Agent.
        target.slipping_allowed = True
        model.slipping_allowed = True
        target.slipping_fails = False
        model.slipping_fails = False
        Tag_It(target, Slipping, model, context + " retry")
        assert target in Slipping[:], (context, "successful retry did not enter")
        assert (target in Slipping) is model.Sound(), (context, "retry sound membership")
        assert (target in list(Slipping)) is model.Sound(), (context, "retry sound Field")
        assert (target in ~Slipping) is (not model.Sound()), (context, "retry deficient Field")
        assert Slipping[target].Read_Slip() == model.slipping_round, (context, "retry view")
        del Slipping[target]
        Model_Rip(model, Slipping)


def Exercise_Tools(
        target: object,
        model: Model,
        context: str,
        ) -> None:
    """The three laws of a Tool slot (STEP-SPEC-36): the slot holds a
    member of its kind and never the bearer, admission is asked at the
    gaining and at every write, the slot is never empty, and the slot
    never Tags. The bearer's membership follows the model as any Tag's."""

    if not model.Sound() or Armed in model.active:
        return

    prepared = Agent(f"{target.name}'s gear")
    Gear(prepared)
    Armed(target, gear=prepared)
    Model_Apply(model, Armed)
    gear = target.gear

    assert gear in Gear[:] and target not in Gear[:], (context, "the forge Tags the gear, never the bearer")
    assert "gear" @ target, (context, "the slot is present")

    for misfit in (Agent("a stick"), None, target):
        try:
            target.gear = misfit
        except TagCompositionError:
            pass
        else:
            raise AssertionError((context, "the slot admitted", misfit))

        assert target.gear is gear, (context, "a refused write changed the slot")

    stick = Agent("a stick")
    assert stick not in Gear[:], (context, "the slot Tagged what it refused")

    Gear(stick)
    target.gear = stick                                               # a member is admitted
    assert target.gear is stick, (context, "an admitted write did not land")

    del Gear[stick]                                                   # a Rogue in hand stays in hand
    assert target.gear is stick and "gear" @ target, (context, "a Rogue in hand was dropped")

    del Armed[target]
    Model_Rip(model, Armed)
    assert "gear" @ target, (context, "Rip of the bearer dropped the slot")
    del target.gear                                                   # the drop, so the next exercise starts clean

    if Carrying in model.active:
        return

    Carrying(target)
    Model_Apply(model, Carrying)
    pack = target.pack
    assert type(pack) is Agent and "pack" @ target, (context, "a class kind did not build its value")

    for misfit in (object(), None, "a stick"):
        try:
            target.pack = misfit
        except TagCompositionError:
            pass
        else:
            raise AssertionError((context, "a class kind admitted", misfit))

        assert target.pack is pack, (context, "a refused write changed the slot")

    target.pack = target                                              # self-reference: the bearer is an Agent instance
    assert target.pack is target, (context, "self-reference by class was refused")
    target.pack = stick                                               # a Rogue Gear is still an Agent instance
    assert target.pack is stick, (context, "a class kind refused a Rogue of some Tag")

    del Carrying[target]
    Model_Rip(model, Carrying)
    del target.pack


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
