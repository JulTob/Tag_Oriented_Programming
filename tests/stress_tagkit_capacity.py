"""Parameterized capacity probes for TagKit's principal scaling axes.

Each probe is intentionally separate so a slow or memory-heavy dimension can
run in its own fresh process.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
import argparse
import gc
import time
import tracemalloc
import weakref

from TagKit import (
        Action,
        At_Exit,
        Imprint,
        Post,
        Record,
        Rip,
        Scope,
        Tag,
        TagPostconditionError,
        Tags,
        Underlay,
        )


class Agent:
    pass


def Deep(
        depth: int,
        ) -> None:
    started = time.perf_counter()
    chain: list[type[Tag]] = [
            type(
                    "Deep_0",
                    (Tag,),
                    {},
                    )
            ]

    for index in range(
            1,
            depth,
            ):
        chain.append(
                type(
                        f"Deep_{index}",
                        (chain[-1],),
                        {},
                        )
                )

    created = time.perf_counter()
    target = Agent()
    chain[-1](target)
    applied = time.perf_counter()

    assert len(
            [
                    tag
                    for tag in chain
                    if target in tag
                    ]
            ) == depth
    assert Tags(target) == (
            chain[-1],
            )

    chain[0].Rip(target)
    ripped = time.perf_counter()

    assert not any(
            target in tag
            for tag in chain
            )

    print(
            "DEEP PASS",
            f"depth={depth}",
            f"create={created - started:.6f}",
            f"apply={applied - created:.6f}",
            f"rip={ripped - applied:.6f}",
            )


def Form_Only(
        depth: int,
        ) -> None:
    current = type(
            "Form_0",
            (Tag,),
            {},
            )

    for index in range(
            1,
            depth,
            ):
        current = type(
                f"Form_{index}",
                (current,),
                {},
                )

    started = time.perf_counter()
    form = current.Form()
    finished = time.perf_counter()

    assert len(form) == depth

    print(
            "FORM PASS",
            f"depth={depth}",
            f"seconds={finished - started:.6f}",
            )


def Wide(
        width: int,
        ) -> None:
    tags = [
            type(
                    f"Wide_{index}",
                    (Tag,),
                    {},
                    )
            for index in range(width)
            ]
    target = Agent()
    started = time.perf_counter()

    for tag in tags:
        tag(target)

    applied = time.perf_counter()

    assert len(Tags(target)) == width
    assert all(
            target in tag
            for tag in tags
            )

    for tag in reversed(tags):
        tag.Rip(target)

    ripped = time.perf_counter()

    assert Tags(target) == ()

    print(
            "WIDE PASS",
            f"width={width}",
            f"apply={applied - started:.6f}",
            f"rip={ripped - applied:.6f}",
            )


def Diamond(
        width: int,
        ) -> None:
    root = type(
            "Diamond_Root",
            (Tag,),
            {},
            )
    branches = tuple(
            type(
                    f"Diamond_Branch_{index}",
                    (root,),
                    {},
                    )
            for index in range(width)
            )
    started = time.perf_counter()
    leaf = type(
            "Diamond_Leaf",
            branches,
            {},
            )
    created = time.perf_counter()
    target = Agent()
    leaf(target)
    applied = time.perf_counter()

    assert target in root
    assert target in leaf
    assert all(
            target in branch
            for branch in branches
            )
    assert Tags(target) == (
            leaf,
            )

    root.Rip(target)
    ripped = time.perf_counter()

    assert target not in root
    assert target not in leaf

    print(
            "DIAMOND PASS",
            f"width={width}",
            f"leaf-class={created - started:.6f}",
            f"apply={applied - created:.6f}",
            f"rip={ripped - applied:.6f}",
            )


def Population(
        count: int,
        ) -> None:
    class Populated(Tag):
        pass

    targets = [
            Agent()
            for _ in range(count)
            ]
    started = time.perf_counter()

    for target in targets:
        Populated(target)

    applied = time.perf_counter()

    assert len(Populated.Field) == count

    references = [
            weakref.ref(target)
            for target in targets
            ]
    targets.clear()
    del target
    gc.collect()
    collected = time.perf_counter()

    assert len(Populated.Field) == 0
    assert all(
            reference() is None
            for reference in references
            )

    print(
            "POPULATION PASS",
            f"count={count}",
            f"apply={applied - started:.6f}",
            f"collect={collected - applied:.6f}",
            )


def Nested_Scopes(
        depth: int,
        ) -> None:
    tags = [
            type(
                    f"Scoped_{index}",
                    (Tag,),
                    {},
                    )
            for index in range(depth)
            ]
    target = Agent()
    started = time.perf_counter()

    with ExitStack() as stack:
        for tag in tags:
            stack.enter_context(
                    Scope(
                            target,
                            tag,
                            )
                    )

        assert len(Tags(target)) == depth

    finished = time.perf_counter()

    assert Tags(target) == ()

    print(
            "SCOPES PASS",
            f"depth={depth}",
            f"total={finished - started:.6f}",
            )


def Mutable_Rollback(
        count: int,
        ) -> None:
    class Rejected(Tag):
        @Imprint
        def Mutate(
                target,
                ) -> None:
            target.values.reverse()
            target.values.append(
                    -1
                    )
            target.mapping["values"].pop()
            target.members.add(
                    -1
                    )
            target.payload.extend(
                    b"!"
                    )

        @Post
        def Reject(
                target,
                ) -> bool:
            return False

    target = Agent()
    target.values = list(
            range(count)
            )
    target.mapping = {
            "values": target.values,
            }
    target.members = set(
            range(count)
            )
    target.payload = bytearray(
            b"x" * count
            )
    values = target.values
    mapping = target.mapping
    members = target.members
    payload = target.payload
    expected = list(
            range(count)
            )

    tracemalloc.start()
    started = time.perf_counter()

    try:
        Rejected(target)
    except TagPostconditionError:
        pass
    else:
        raise AssertionError(
                "Rejected Tag committed"
                )

    finished = time.perf_counter()
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    assert target.values is values
    assert target.mapping is mapping
    assert target.mapping["values"] is values
    assert target.members is members
    assert target.payload is payload
    assert target.values == expected
    assert target.members == set(expected)
    assert target.payload == bytearray(
            b"x" * count
            )

    print(
            "ROLLBACK PASS",
            f"items={count}",
            f"seconds={finished - started:.6f}",
            f"peak-bytes={peak}",
            )


def Distinct_Target_Threads(
        count: int,
        ) -> None:
    class Base(Tag):
        @Record
        def values(
                target,
                ) -> list[int]:
            return []

        @Action
        def Add(
                target,
                value: int,
                ) -> int:
            target.values.append(value)

            return len(target.values)

    class Refined(Base):
        @Action
        @Underlay
        def Add(
                target,
                prior,
                value: int,
                ) -> int:
            return prior(
                    value * 2
                    )

    def Exercise(
            index: int,
            ) -> bool:
        target = Agent()

        Refined(target)

        assert target.Add(index) == 1
        assert target.values == [
                index * 2,
                ]
        assert target in Base
        assert target in Refined

        Base.Rip(target)

        return (
                target not in Base
                and target not in Refined
                and isinstance(
                        target,
                        Refined,
                        )
                )

    started = time.perf_counter()

    with ThreadPoolExecutor(
            max_workers=16,
            ) as workers:
        results = list(
                workers.map(
                        Exercise,
                        range(count),
                        )
                )

    finished = time.perf_counter()

    assert all(results)
    assert len(Base.Field) == 0
    assert len(Refined.Field) == 0

    print(
            "THREADS PASS",
            f"targets={count}",
            f"seconds={finished - started:.6f}",
            )


def Lifecycle(
        count: int,
        ) -> None:
    closed: list[int] = []

    class Managed(Tag):
        @Rip
        def Close(
                target,
                ) -> None:
            closed.append(
                    target.identity
                    )

    targets = [
            Agent()
            for _index in range(count)
            ]

    for identity, target in enumerate(targets):
        target.identity = identity
        Managed(target)
        At_Exit(target)

    references = [
            weakref.ref(target)
            for target in targets
            ]
    started = time.perf_counter()

    targets.clear()
    del target
    gc.collect()

    finished = time.perf_counter()

    assert len(closed) == count
    assert len(set(closed)) == count
    assert len(Managed.Field) == 0
    assert all(
            reference() is None
            for reference in references
            )

    print(
            "LIFECYCLE PASS",
            f"targets={count}",
            f"collect={finished - started:.6f}",
            )


def Cache_Churn(
        count: int,
        ) -> None:
    host_references: list[
            weakref.ReferenceType[type]
            ] = []
    tag_references: list[
            weakref.ReferenceType[type]
            ] = []
    runtime_references: list[
            weakref.ReferenceType[type]
            ] = []
    agent_references: list[
            weakref.ReferenceType[object]
            ] = []
    started = time.perf_counter()

    for index in range(count):
        host = type(
                f"Transient_Host_{index}",
                (),
                {},
                )
        shape = type(
                f"Transient_Tag_{index}",
                (Tag,),
                {},
                )
        target = host()

        shape(target)

        host_references.append(
                weakref.ref(host)
                )
        tag_references.append(
                weakref.ref(shape)
                )
        runtime_references.append(
                weakref.ref(
                        type(target)
                        )
                )
        agent_references.append(
                weakref.ref(target)
                )

    created = time.perf_counter()

    del host
    del shape
    del target

    gc.collect()
    gc.collect()

    collected = time.perf_counter()

    groups = (
            host_references,
            tag_references,
            runtime_references,
            agent_references,
            )

    assert all(
            reference() is None
            for group in groups
            for reference in group
            )

    print(
            "CACHES PASS",
            f"compositions={count}",
            f"create={created - started:.6f}",
            f"collect={collected - created:.6f}",
            )


def Pin_Cycles(
        count: int,
        ) -> None:
    class First(Tag):
        pass

    class Second(Tag):
        pass

    started = time.perf_counter()

    for _index in range(count):
        First(First)

        assert First in First

        First.Rip(First)
        First(Second)
        Second(First)

        assert Second in First
        assert First in Second

        First.Rip(Second)
        Second.Rip(First)

    finished = time.perf_counter()

    assert Tags(First) == ()
    assert Tags(Second) == ()
    assert isinstance(
            First,
            First,
            )
    assert isinstance(
            Second,
            First,
            )

    print(
            "PIN-CYCLES PASS",
            f"cycles={count}",
            f"seconds={finished - started:.6f}",
            )


def Main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
            "probe",
            choices=(
                    "deep",
                    "form",
                    "wide",
                    "diamond",
                    "population",
                    "scopes",
                    "rollback",
                    "threads",
                    "lifecycle",
                    "caches",
                    "pin-cycles",
                    ),
            )
    parser.add_argument(
            "size",
            type=int,
            )
    arguments = parser.parse_args()

    probes = {
            "deep": Deep,
            "form": Form_Only,
            "wide": Wide,
            "diamond": Diamond,
            "population": Population,
            "scopes": Nested_Scopes,
            "rollback": Mutable_Rollback,
            "threads": Distinct_Target_Threads,
            "lifecycle": Lifecycle,
            "caches": Cache_Churn,
            "pin-cycles": Pin_Cycles,
            }

    probes[arguments.probe](
            arguments.size
            )


if __name__ == "__main__":
    Main()
