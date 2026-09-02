"""Deterministic state-machine stress runner for TagKit.

Run from the repository root with ``PYTHONPATH=.``. The defaults are a
short local probe; the full audited run uses 50 seeds, 1,200 steps, and a
population of 18.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import argparse
import gc
import random
import time
import weakref

from TagKit import (
        Action,
        Apply,
        Contract,
        Delete,
        Has,
        Imprint,
        ImprintingError,
        Operation,
        Post,
        Pre,
        Record,
        Report,
        Scope,
        Tag,
        TagPostconditionError,
        TagPreconditionError,
        TagResolutionError,
        Tags,
        Underlay,
        )


class Agent:
    def __init__(
            self,
            name: str,
            ) -> None:
        self.name = name
        self.ledger = {
                "events": [],
                "nested": [
                        {
                            "marks": [],
                            },
                        ],
                "flags": set(),
                "bytes": bytearray(
                        b"TOP"
                        ),
                }


@dataclass
class Model:
    active: list[type[Tag]]
    ever: set[type[Tag]]


def Direct_Bases(
        tag: type[Tag],
        ) -> tuple[type[Tag], ...]:
    return tuple(
            base
            for base in tag.__bases__
            if (
                    isinstance(
                            base,
                            type(Tag),
                            )
                    and base is not Tag
                    )
            )


def Form(
        tag: type[Tag],
        ) -> tuple[type[Tag], ...]:
    result: list[type[Tag]] = []

    def Visit(
            current: type[Tag],
            ) -> None:
        for base in Direct_Bases(current):
            Visit(base)

        if current not in result:
            result.append(current)

    Visit(tag)

    return tuple(result)


def Model_Apply(
        model: Model,
        tag: type[Tag],
        ) -> None:
    for current in Form(tag):
        if current not in model.active:
            model.active.append(current)
            model.ever.add(current)


def Model_Rip(
        model: Model,
        tag: type[Tag],
        ) -> None:
    model.active = [
            current
            for current in model.active
            if not issubclass(
                    current,
                    tag,
                    )
            ]


def Leaf_Tags(
        model: Model,
        ) -> tuple[type[Tag], ...]:
    leaves = [
            tag
            for tag in model.active
            if not any(
                    other is not tag
                    and issubclass(
                            other,
                            tag,
                            )
                    for other in model.active
                    )
            ]

    return tuple(
            reversed(leaves)
            )


def Family(
        prefix: str,
        ) -> tuple[type[Tag], ...]:
    root = type(
            prefix + "_Root",
            (Tag,),
            {},
            )
    left = type(
            prefix + "_Left",
            (root,),
            {},
            )
    right = type(
            prefix + "_Right",
            (root,),
            {},
            )
    bridge = type(
            prefix + "_Bridge",
            (
                    left,
                    right,
                    ),
            {},
            )
    left_leaf = type(
            prefix + "_Left_Leaf",
            (left,),
            {},
            )
    right_leaf = type(
            prefix + "_Right_Leaf",
            (right,),
            {},
            )
    independent = type(
            prefix + "_Independent",
            (Tag,),
            {},
            )
    composite = type(
            prefix + "_Composite",
            (
                    bridge,
                    independent,
                    ),
            {},
            )

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


def Assert_Target(
        target: object,
        model: Model,
        family: tuple[type[Tag], ...],
        *,
        seed: int,
        step: int,
        ) -> None:
    target_name = (
            target.__name__
            if isinstance(
                    target,
                    type,
                    )
            else target.name
            )
    context = (
            f"seed={seed} step={step}"
            f" target={target_name}"
            )

    assert Tags(target) == Leaf_Tags(model), (
            context,
            "Tags",
            Tags(target),
            Leaf_Tags(model),
            )

    for tag in family:
        expected = tag in model.active

        assert (target in tag) is expected, (
                context,
                "Field membership",
                tag.__name__,
                expected,
                )
        assert Has(
                target,
                tag,
                ) is expected, (
                context,
                "Has Tag",
                tag.__name__,
                expected,
                )

        if expected:
            assert Has(
                    target,
                    tag.__name__.swapcase(),
                    ), (
                    context,
                    "Has label",
                    tag.__name__,
                    )
            assert tag[target] is not None, (
                    context,
                    "view",
                    tag.__name__,
                    )
        else:
            try:
                tag[target]
            except TagResolutionError:
                pass
            else:
                raise AssertionError(
                        (
                                context,
                                "inactive view resolved",
                                tag.__name__,
                                )
                        )

        assert isinstance(
                target,
                tag,
                ) is (tag in model.ever), (
                context,
                "historical membership",
                tag.__name__,
                tag in model.ever,
                )
        assert tag[()] is tag.Field
        assert tag[...] is tag.Field


def Assert_Fields(
        targets: list[object],
        models: dict[object, Model],
        family: tuple[type[Tag], ...],
        *,
        seed: int,
        step: int,
        ) -> None:
    for tag in family:
        expected = {
                target
                for target in targets
                if tag in models[target].active
                }
        observed = set(tag.Field)

        assert observed == expected, (
                f"seed={seed} step={step}",
                "Field population",
                tag.__name__,
                len(observed),
                len(expected),
                )
        assert len(tag.Field) == len(expected)
        assert set(tag) == expected


def Snapshot_Mutables(
        target: Agent,
        ) -> tuple[dict[str, object], tuple[int, ...]]:
    ledger = target.ledger
    nested = ledger["nested"]
    first = nested[0]

    return (
            deepcopy(ledger),
            (
                    id(ledger),
                    id(ledger["events"]),
                    id(nested),
                    id(first),
                    id(first["marks"]),
                    id(ledger["flags"]),
                    id(ledger["bytes"]),
                    ),
            )


def Assert_Mutables(
        target: Agent,
        snapshot: tuple[dict[str, object], tuple[int, ...]],
        *,
        seed: int,
        step: int,
        ) -> None:
    expected, identities = snapshot
    observed, observed_identities = Snapshot_Mutables(target)

    assert observed == expected, (
            f"seed={seed} step={step}",
            "mutable values",
            observed,
            expected,
            )
    assert observed_identities == identities, (
            f"seed={seed} step={step}",
            "mutable identities",
            observed_identities,
            identities,
            )


def Transaction_Tags(
        prefix: str,
        ) -> tuple[
        type[Tag],
        type[Tag],
        type[Tag],
        type[Tag],
        ]:
    class Tx_Base(Tag):
        @Record
        def cache(
                target,
                ) -> dict[str, object]:
            return {
                    "history": [],
                    }

        @Imprint
        def Establish(
                target,
                ) -> None:
            target.ledger["events"].append(
                    "base"
                    )

    class Reject_Pre(Tx_Base):
        @Pre
        def Mutate_Then_Reject(
                target,
                ) -> bool:
            target.ledger["nested"][0]["marks"].append(
                    "pre"
                    )
            target.ledger["flags"].add(
                    "pre"
                    )
            target.ledger["bytes"].extend(
                    b"!"
                    )

            return False

    class Reject_Post(Tx_Base):
        @Imprint
        def Mutate(
                target,
                ) -> None:
            target.ledger["events"].append(
                    "post"
                    )
            target.ledger["nested"][0]["marks"].append(
                    "post"
                    )
            target.cache["history"].append(
                    "post"
                    )

        @Post
        def Reject(
                target,
                ) -> bool:
            return False

    class Reject_Imprint(Tx_Base):
        @Imprint
        def Mutate_Then_Raise(
                target,
                ) -> None:
            target.ledger["events"].append(
                    "imprint"
                    )
            target.ledger["nested"][0]["marks"].append(
                    "imprint"
                    )
            target.cache["history"].append(
                    "imprint"
                    )

            raise RuntimeError(
                    "deliberate"
                    )

    Tx_Base.__name__ = prefix + "_Tx_Base"
    Reject_Pre.__name__ = prefix + "_Reject_Pre"
    Reject_Post.__name__ = prefix + "_Reject_Post"
    Reject_Imprint.__name__ = prefix + "_Reject_Imprint"

    return (
            Tx_Base,
            Reject_Pre,
            Reject_Post,
            Reject_Imprint,
            )


def Exercise_Transactions(
        target: Agent,
        tx_tags: tuple[
        type[Tag],
        type[Tag],
        type[Tag],
        type[Tag],
        ],
        *,
        seed: int,
        step: int,
        ) -> None:
    base, reject_pre, reject_post, reject_imprint = tx_tags

    if target not in base:
        base(target)

    for tag, failure in (
            (
                    reject_pre,
                    TagPreconditionError,
                    ),
            ):
        before = Snapshot_Mutables(target)
        cache = target.cache
        cache_before = deepcopy(cache)

        try:
            tag(target)
        except failure:
            pass
        else:
            raise AssertionError(
                    (
                            f"seed={seed} step={step}",
                            "transaction unexpectedly committed",
                            tag.__name__,
                            )
                    )

        Assert_Mutables(
                target,
                before,
                seed=seed,
                step=step,
                )
        assert target.cache is cache
        assert target.cache == cache_before
        assert target not in tag
        assert not Has(
                target,
                tag,
                )

    try:
        reject_post(target)
    except TagPostconditionError:
        pass
    else:
        raise AssertionError(
                (
                        f"seed={seed} step={step}",
                        "postcondition unexpectedly succeeded",
                        reject_post.__name__,
                        )
                )

    assert target in reject_post
    assert Has(
            target,
            reject_post,
            )
    assert "post" in target.ledger["events"]
    reject_post.Rip(target)

    try:
        reject_imprint(target)
    except ImprintingError:
        pass
    else:
        raise AssertionError(
                (
                        f"seed={seed} step={step}",
                        "imprint unexpectedly succeeded",
                        reject_imprint.__name__,
                        )
                )

    assert target in reject_imprint
    assert Has(
            target,
            reject_imprint,
            )
    assert "imprint" in target.ledger["events"]
    reject_imprint.Rip(target)

    base.Rip(target)


def Feature_Probe(
        seed: int,
        ) -> None:
    class Base_Feature(Tag):
        shared = Report(
                5
                )

        @Operation
        def Population(
                tag,
                ) -> int:
            return len(
                    tag.Field
                    )

        @Pre
        def Named(
                target,
                ) -> bool:
            return bool(
                    target.name
                    )

        @Record
        def score(
                target,
                ) -> int:
            return 10

        @Action
        def Speak(
                target,
                ) -> str:
            return "base"

        @Post
        def Scored(
                target,
                ) -> bool:
            return target.score >= 0

    class Refined_Feature(Base_Feature):
        @Record
        @Underlay
        def score(
                target,
                previous,
                ) -> int:
            return (
                    previous()
                    + 7
                    )

        @Action
        @Underlay
        def Speak(
                target,
                previous,
                ) -> str:
            return (
                    previous()
                    + "+refined"
                    )

    target = Agent(
            f"feature-{seed}"
            )
    Refined_Feature(target)

    assert target.score == 17
    assert target.Speak() == "base+refined"
    assert Base_Feature.Population() == 1
    assert target.Refined_Feature.shared == 5
    assert Contract.Conditions(target)
    assert not Has(
            target,
            Base_Feature.Speak,
            )
    assert Has(
            target,
            Refined_Feature.Speak,
            )

    class Silenced(Tag):
        @Delete
        def Speak(
                target,
                ) -> None:
            pass

    silent_target = Agent(
            f"silent-{seed}"
            )
    Refined_Feature(silent_target)
    Silenced(silent_target)

    assert not hasattr(
            silent_target,
            "Speak",
            )

    class Catalogue(Tag):
        purpose = Report(
                "stress catalogue"
                )

        @Operation
        def Population(
                pin,
                ) -> int:
            return len(
                    pin.Field
                    )

        @Record
        def source(
                entry,
                source,
                ) -> str:
            return source

        @Action
        def Explain(
                entry,
                ) -> str:
            return entry.__name__

    class Entry(Tag):
        pass

    Catalogue(
            Entry,
            source=f"seed-{seed}",
            )

    assert Entry in Catalogue
    assert Catalogue.Population() == 1
    assert Entry.source == f"seed-{seed}"
    assert Entry.Explain() == "Entry"
    assert Entry.Tag(
            Catalogue
            ).purpose == "stress catalogue"

    Catalogue.Rip(Entry)

    assert Entry not in Catalogue
    assert Entry.source == f"seed-{seed}"
    assert Entry.Explain() == "Entry"
    assert target.Refined_Feature.score == 17
    assert target.Refined_Feature.Speak() == "base+refined"

    Refined_Feature.Rip(target)

    assert target not in Refined_Feature
    assert target in Base_Feature
    assert target.score == 17
    assert target.Speak() == "base+refined"
    assert Has(
            target,
            Refined_Feature.Speak,
            )


def Run_Seed(
        seed: int,
        *,
        steps: int,
        population: int,
        ) -> int:
    randomizer = random.Random(seed)
    agent_family = Family(
            f"S{seed}_Agent"
            )
    pin_family = Family(
            f"S{seed}_Pin"
            )
    agents = [
            Agent(
                    f"agent-{seed}-{index}"
                    )
            for index in range(population)
            ]
    entries = [
            type(
                    f"S{seed}_Entry_{index}",
                    (Tag,),
                    {},
                    )
            for index in range(
                    max(
                            2,
                            population // 3,
                            )
                    )
            ]
    agent_models = {
            target: Model(
                    active=[],
                    ever=set(),
                    )
            for target in agents
            }
    pin_models = {
            target: Model(
                    active=[],
                    ever=set(),
                    )
            for target in entries
            }
    tx_tags = Transaction_Tags(
            f"S{seed}"
            )
    operations = 0

    for step in range(steps):
        use_pins = randomizer.random() < 0.28
        targets = entries if use_pins else agents
        models = pin_models if use_pins else agent_models
        family = pin_family if use_pins else agent_family
        target = randomizer.choice(targets)
        model = models[target]
        choice = randomizer.randrange(10)

        if choice <= 2:
            tag = randomizer.choice(family)
            tag(target)
            Model_Apply(
                    model,
                    tag,
                    )
        elif choice == 3:
            first = randomizer.choice(family)
            second = randomizer.choice(family)
            Apply(
                    target,
                    first,
                    second,
                    )
            Model_Apply(
                    model,
                    first,
                    )
            Model_Apply(
                    model,
                    second,
                    )
        elif choice == 4:
            active = list(model.active)

            if active:
                tag = randomizer.choice(active)
                tag.Rip(target)
                Model_Rip(
                        model,
                        tag,
                        )
            else:
                tag = randomizer.choice(family)

                try:
                    tag.Rip(target)
                except TagResolutionError:
                    pass
                else:
                    raise AssertionError(
                            (
                                    f"seed={seed} step={step}",
                                    "inactive Rip succeeded",
                                    tag.__name__,
                                    )
                            )
        elif choice in {
                5,
                6,
                }:
            scoped_tags = tuple(
                    randomizer.choice(family)
                    for _ in range(
                            1 + randomizer.randrange(3)
                            )
                    )
            entry = Model(
                    active=list(model.active),
                    ever=set(model.ever),
                    )
            inside = Model(
                    active=list(model.active),
                    ever=set(model.ever),
                    )

            try:
                with Scope(
                        target,
                        *scoped_tags,
                        ):
                    for tag in scoped_tags:
                        Model_Apply(
                                inside,
                                tag,
                                )

                    Assert_Target(
                            target,
                            inside,
                            family,
                            seed=seed,
                            step=step,
                            )

                    if choice == 6:
                        raise LookupError(
                                "deliberate body failure"
                                )
            except LookupError:
                if choice != 6:
                    raise

            model.active = entry.active
            model.ever.update(inside.ever)
        elif choice == 7 and not use_pins:
            Exercise_Transactions(
                    target,
                    tx_tags,
                    seed=seed,
                    step=step,
                    )
        elif choice == 8:
            tag = randomizer.choice(family)
            before = list(model.active)
            returned = tag(target)
            assert returned is target
            Model_Apply(
                    model,
                    tag,
                    )

            tag(target)
            assert model.active != before or tag in before
        else:
            invalid = object()
            before = list(model.active)

            try:
                Apply(
                        target,
                        randomizer.choice(family),
                        invalid,
                        )
            except TypeError:
                pass
            else:
                raise AssertionError(
                        (
                                f"seed={seed} step={step}",
                                "invalid Apply succeeded",
                                )
                        )

            assert model.active == before

        Assert_Target(
                target,
                model,
                family,
                seed=seed,
                step=step,
                )

        if step % 23 == 0:
            Assert_Fields(
                    targets,
                    models,
                    family,
                    seed=seed,
                    step=step,
                    )

            for candidate in targets:
                Assert_Target(
                        candidate,
                        models[candidate],
                        family,
                        seed=seed,
                        step=step,
                        )

        operations += 1

    Assert_Fields(
            agents,
            agent_models,
            agent_family,
            seed=seed,
            step=steps,
            )
    Assert_Fields(
            entries,
            pin_models,
            pin_family,
            seed=seed,
            step=steps,
            )
    Feature_Probe(seed)

    return operations


def Weak_Field_Probe(
        count: int,
        ) -> None:
    class Ephemeral(Tag):
        pass

    agents = [
            Agent(
                    f"ephemeral-{index}"
                    )
            for index in range(count)
            ]

    for target in agents:
        Ephemeral(target)

    assert len(Ephemeral.Field) == count
    references = [
            weakref.ref(target)
            for target in agents
            ]

    agents.clear()
    del target
    gc.collect()

    assert len(Ephemeral.Field) == 0
    assert all(
            reference() is None
            for reference in references
            )


def Main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
            "--first-seed",
            type=int,
            default=1701,
            )
    parser.add_argument(
            "--seeds",
            type=int,
            default=25,
            )
    parser.add_argument(
            "--steps",
            type=int,
            default=600,
            )
    parser.add_argument(
            "--population",
            type=int,
            default=12,
            )
    arguments = parser.parse_args()
    started = time.perf_counter()
    operations = 0

    for seed in range(
            arguments.first_seed,
            arguments.first_seed + arguments.seeds,
            ):
        operations += Run_Seed(
                seed,
                steps=arguments.steps,
                population=arguments.population,
                )

    Weak_Field_Probe(
            max(
                    500,
                    arguments.population * 20,
                    )
            )
    duration = time.perf_counter() - started

    print(
            "PASS",
            f"seeds={arguments.first_seed}"
            f"..{arguments.first_seed + arguments.seeds - 1}",
            f"operations={operations}",
            f"seconds={duration:.3f}",
            )


if __name__ == "__main__":
    Main()
