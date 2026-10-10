"""Isolated probes for TopKit's capacity boundaries.

Run one probe in a fresh process so one extreme does not contaminate another's
memory or timing::

    PYTHONPATH=. python3 benchmarks/capacity.py deep 500
    PYTHONPATH=. python3 benchmarks/capacity.py form 1500
    PYTHONPATH=. python3 benchmarks/capacity.py wide 2000
    PYTHONPATH=. python3 benchmarks/capacity.py diamond 512
    PYTHONPATH=. python3 benchmarks/capacity.py population 50000
    PYTHONPATH=. python3 benchmarks/capacity.py lifecycle 20000
    PYTHONPATH=. python3 benchmarks/capacity.py caches 5000

These are capacity probes, not portable performance budgets.  They assert the
observable result and report wall-clock time; compare measurements only on a
controlled machine and interpreter.
"""

from __future__ import annotations

import argparse
import gc
import time
import weakref
from collections.abc import Callable

from TopKit import At_Exit
from TopKit import Form
from TopKit import Rip
from TopKit import Tag
from TopKit import Tags


class Agent:
    pass


def _rip_form(
        agent: Agent,
        tag: type[Tag],
        ) -> None:
    """Deform one active Form from Shape to Bases, as Rip requires."""

    for member in reversed(Form(tag)):
        if agent in member:
            del member[agent]


def Deep(
        depth: int,
        ) -> None:
    """Build, apply and deform a single-inheritance Form."""

    started = time.perf_counter()
    chain: list[type[Tag]] = [
            type(
                    "Deep_0",
                    (Tag,),
                    {},
                    )
            ]

    for index in range(1, depth):
        chain.append(
                type(
                        f"Deep_{index}",
                        (chain[-1],),
                        {},
                        )
                )

    created = time.perf_counter()
    agent = Agent()
    chain[-1](agent)
    applied = time.perf_counter()

    assert Form(chain[-1]) == tuple(chain)
    assert Tags(agent) == (chain[-1],)
    assert all(agent in tag for tag in chain)

    _rip_form(
            agent,
            chain[-1],
            )
    ripped = time.perf_counter()

    assert Tags(agent) == ()
    assert not any(agent in tag for tag in chain)

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
    """Resolve a deep Form without applying it."""

    chain: list[type[Tag]] = [
            type(
                    "Form_0",
                    (Tag,),
                    {},
                    )
            ]

    for index in range(1, depth):
        chain.append(
                type(
                        f"Form_{index}",
                        (chain[-1],),
                        {},
                        )
                )

    started = time.perf_counter()
    form = Form(chain[-1])
    finished = time.perf_counter()

    assert form == tuple(chain)

    print(
            "FORM PASS",
            f"depth={depth}",
            f"seconds={finished - started:.6f}",
            )


def Wide(
        width: int,
        ) -> None:
    """Apply and Rip many independent Tags on one Agent."""

    tags = [
            type(
                    f"Wide_{index}",
                    (Tag,),
                    {},
                    )
            for index in range(width)
            ]
    agent = Agent()
    started = time.perf_counter()

    for tag in tags:
        tag(agent)

    applied = time.perf_counter()

    assert Tags(agent) == tuple(tags)
    assert all(agent in tag for tag in tags)

    for tag in reversed(tags):
        del tag[agent]

    ripped = time.perf_counter()

    assert Tags(agent) == ()
    assert not any(agent in tag for tag in tags)

    print(
            "WIDE PASS",
            f"width={width}",
            f"apply={applied - started:.6f}",
            f"rip={ripped - applied:.6f}",
            )


def Diamond(
        width: int,
        ) -> None:
    """Build and apply a wide diamond with one shared Base."""

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
    agent = Agent()
    leaf(agent)
    applied = time.perf_counter()

    assert Form(leaf) == (root, *branches, leaf)
    assert Tags(agent) == (leaf,)
    assert all(agent in tag for tag in (root, *branches, leaf))

    _rip_form(
            agent,
            leaf,
            )
    ripped = time.perf_counter()

    assert Tags(agent) == ()
    assert not any(agent in tag for tag in (root, *branches, leaf))

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
    """Fill one Field, release every Agent and check weak cleanup."""

    class Populated(Tag):
        pass

    agents = [
            Agent()
            for _ in range(count)
            ]
    started = time.perf_counter()

    for agent in agents:
        Populated(agent)

    applied = time.perf_counter()

    assert len(Populated[:]) == count

    references = [
            weakref.ref(agent)
            for agent in agents
            ]
    agents.clear()
    del agent
    gc.collect()
    collected = time.perf_counter()

    assert len(Populated[:]) == 0
    assert all(reference() is None for reference in references)

    print(
            "POPULATION PASS",
            f"count={count}",
            f"apply={applied - started:.6f}",
            f"collect={collected - applied:.6f}",
            )


def Lifecycle(
        count: int,
        ) -> None:
    """Collect registered Agents and check each teardown runs once."""

    closed: list[int] = []

    class Managed(Tag):
        @Rip
        def Close(
                agent,
                ) -> None:
            closed.append(agent.identity)

    agents = [
            Agent()
            for _ in range(count)
            ]

    for identity, agent in enumerate(agents):
        agent.identity = identity
        Managed(agent)
        At_Exit(agent)

    references = [
            weakref.ref(agent)
            for agent in agents
            ]
    started = time.perf_counter()

    agents.clear()
    del agent
    gc.collect()

    finished = time.perf_counter()

    assert len(closed) == count
    assert len(set(closed)) == count
    assert len(Managed[:]) == 0
    assert all(reference() is None for reference in references)

    print(
            "LIFECYCLE PASS",
            f"targets={count}",
            f"collect={finished - started:.6f}",
            )


def Cache_Churn(
        count: int,
        ) -> None:
    """Drop transient hosts, Tags, runtime types and Agents."""

    host_references: list[weakref.ReferenceType[type]] = []
    tag_references: list[weakref.ReferenceType[type]] = []
    runtime_references: list[weakref.ReferenceType[type]] = []
    agent_references: list[weakref.ReferenceType[object]] = []
    started = time.perf_counter()

    for index in range(count):
        host = type(
                f"Transient_Host_{index}",
                (),
                {},
                )
        tag = type(
                f"Transient_Tag_{index}",
                (Tag,),
                {},
                )
        agent = host()

        tag(agent)

        host_references.append(weakref.ref(host))
        tag_references.append(weakref.ref(tag))
        runtime_references.append(weakref.ref(type(agent)))
        agent_references.append(weakref.ref(agent))

    created = time.perf_counter()

    del host
    del tag
    del agent

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


def _positive(
        value: str,
        ) -> int:
    size = int(value)

    if size < 1:
        raise argparse.ArgumentTypeError("size must be at least 1")

    return size


def main() -> None:
    probes: dict[str, Callable[[int], None]] = {
            "deep": Deep,
            "form": Form_Only,
            "wide": Wide,
            "diamond": Diamond,
            "population": Population,
            "lifecycle": Lifecycle,
            "caches": Cache_Churn,
            }
    parser = argparse.ArgumentParser(
            description="Run one isolated TopKit capacity probe.",
            )
    parser.add_argument(
            "probe",
            choices=tuple(probes),
            )
    parser.add_argument(
            "size",
            type=_positive,
            )
    arguments = parser.parse_args()

    probes[arguments.probe](arguments.size)


if __name__ == "__main__":
    main()
