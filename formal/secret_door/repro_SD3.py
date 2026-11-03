"""SD-3: lazy/dunder bodies read their OWN Agent's Secret -> DENIED on current code.

Spec: 'Inside composition means: while an Action ... bound to this Agent is
running' (spec/SPECIFICATION.md:782-784). The sync door wraps only coroutine
creation (_Composing_Bound.__call__); _guard_lazy_result opens no door;
_guard_dunder opens no door. Classification: violates a spec promise (the
doc calls lazy execution a separate concern, #94).
"""
import asyncio
import sys

sys.path.insert(0, "/home/io2007/Documents/Tag_Oriented_Programming")
from TopKit import Action, Record, Secret, Tag  # noqa: E402
from TopKit.state import _state_of  # noqa: E402


class Host:
    pass


class Lazy(Tag):
    @Secret
    @Record
    def code(agent):
        return "private"

    @Action
    def gen(agent):
        yield 1
        yield agent.code

    @Action
    async def aro(agent):
        return agent.code

    @Action
    async def agen(agent):
        yield agent.code


class Dunder(Tag):
    @Secret
    @Record
    def code(agent):
        return "private"

    @Action
    def __eq__(agent, other):
        return agent.code == "private"


def main():
    h = Host()
    Lazy(h)
    rows = []
    g = h.gen()
    first = next(g)
    try:
        rows.append(("generator-resume", next(g)))
    except AttributeError as e:
        rows.append(("generator-resume", f"DENIED: {e}"))
    g.close()
    try:
        rows.append(("coroutine", asyncio.run(h.aro())))
    except AttributeError as e:
        rows.append(("coroutine", f"DENIED: {e}"))

    async def drain():
        try:
            return [v async for v in h.agen()]
        except AttributeError as e:
            return f"DENIED: {e}"

    rows.append(("async-generator", asyncio.run(drain())))
    d = Host()
    Dunder(d)
    try:
        rows.append(("dunder-eq", d == d))
    except AttributeError as e:
        rows.append(("dunder-eq", f"DENIED: {e}"))
    for name, got in rows:
        print(f"{name}: observed={got!r} expected='private' (own Secret resolves)")
    print("composing after:", _state_of(h).composing, "(expected 0)")


if __name__ == "__main__":
    main()
