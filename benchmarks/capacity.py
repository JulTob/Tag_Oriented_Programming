"""Isolated probes for TopKit's Geometry scaling boundaries.

Run one probe in a fresh process so a deep Form does not contaminate a wide
composition's memory or timing::

    PYTHONPATH=. python3 benchmarks/capacity.py deep 500
    PYTHONPATH=. python3 benchmarks/capacity.py form 1500
    PYTHONPATH=. python3 benchmarks/capacity.py wide 2000
    PYTHONPATH=. python3 benchmarks/capacity.py diamond 512

These are capacity probes, not portable performance budgets.  They assert the
observable result and report wall-clock time; compare measurements only on a
controlled machine and interpreter.
"""

from __future__ import annotations

import argparse
import time
from collections.abc import Callable

from TopKit import Form
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
            }
    parser = argparse.ArgumentParser(
            description="Run one isolated TopKit Geometry capacity probe.",
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
