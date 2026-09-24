"""TopKit runtime budget.

Run:  PYTHONPATH=. python3 benchmarks/bench.py

Reads and Action calls are the hot path (Agents are built once and then
play for a long time); tagging may be slower.

Tagging is timed with nothing else running; peak memory is measured in a
separate pass, because tracemalloc slows every allocation it traces.
`benchmarks/compare.py` sets each cost beside its plain-OOP equivalent.
"""

from __future__ import annotations

import gc
import time
import tracemalloc

from TopKit import Post
from TopKit import Record
from TopKit import Tag


class Hero:
    def __init__(
            hero,
            name: str,
            ) -> None:
        hero.name = name
        hero.level = 1

    def Greet(
            hero,
            ) -> str:
        return "Hello"


class Person(Tag):
    def Attack(agent) -> str:
        return "Attack!"


class Wizard(Person):
    @Record
    def spell_slots(agent) -> int:
        return 2

    @Post
    def Has_Slots(agent) -> bool:
        return agent.spell_slots >= 0


def _per_call(
        function,
        repeat: int,
        ) -> float:
    start = time.perf_counter()

    for _ in range(repeat):
        function()

    return (time.perf_counter() - start) * 1e9 / repeat


def _tag_population(
        population: int,
        ) -> list[Hero]:
    keep = []

    for index in range(population):
        hero = Hero(str(index))
        Wizard(hero)
        keep.append(hero)

    return keep


def _release(
        keep: list[Hero],
        ) -> None:
    for hero in keep:
        del Wizard[hero]
        del Person[hero]

    keep.clear()


def _peak_memory(
        population: int,
        ) -> int:
    """Peak traced bytes while tagging ``population`` Agents, in a pass of
    its own so that tracing never slows the timed pass."""

    gc.collect()
    tracemalloc.start()
    keep = _tag_population(population)
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    _release(keep)

    return peak


def main() -> None:
    plain = Hero("plain")
    agent = Hero("agent")
    Wizard(agent)
    repeat = 300_000

    print("hot path (ns per operation)")
    print(f"  plain attribute read      {_per_call(lambda: plain.name, repeat):7.0f}")
    print(f"  Agent host attribute read {_per_call(lambda: agent.name, repeat):7.0f}")
    print(f"  Agent Record read         {_per_call(lambda: agent.spell_slots, repeat):7.0f}")
    print(f"  plain method call         {_per_call(lambda: plain.Greet(), repeat):7.0f}")
    print(f"  Agent Action call         {_per_call(lambda: agent.Attack(), repeat):7.0f}")
    print(f"  bool(agent) (1 Post)      {_per_call(lambda: bool(agent), repeat // 10):7.0f}")
    print(f"  agent in Wizard           {_per_call(lambda: agent in Wizard, repeat):7.0f}")

    for population in (1_000, 10_000):
        gc.collect()
        start = time.perf_counter()
        keep = _tag_population(population)
        elapsed = time.perf_counter() - start

        start = time.perf_counter()
        sound = sum(1 for _ in Wizard)
        iterate = time.perf_counter() - start

        runtime_types = len({type(h) for h in keep})
        _release(keep)
        peak = _peak_memory(population)

        print(f"population {population}")
        print(f"  tag Person+Wizard         {elapsed * 1e6 / population:7.1f} us per Agent")
        print(f"  iterate Wizard (sound)    {iterate * 1e3:7.1f} ms ({sound} sound)")
        print(f"  peak memory               {peak / population:7.0f} bytes per Agent")
        print(f"  runtime types             {runtime_types}")


if __name__ == "__main__":
    main()
