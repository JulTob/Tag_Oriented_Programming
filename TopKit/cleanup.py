"""Permit the matching exit of a Python context entered before arrest.

An entered context owns one cleanup call. Its exit may read the Agent to
release resources even if a Rip failed after entry. This permission never
escapes the exit hook and cannot suppress the Rip error from the with body.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any
from typing import Callable
import weakref

from .arrest import _arrest_of
from .arrest import _require_available
from .arrest import _rip_door
from .lazy_guard import _guard_lazy_result


class _Entry:
    __slots__ = ("agent", "kind", "active")

    def __init__(self, agent: object, kind: str) -> None:
        self.agent = weakref.ref(agent)
        self.kind = kind
        self.active = True


_entries: ContextVar[tuple[_Entry, ...]] = ContextVar(
        "topkit_entered_contexts",
        default=(),
        )


def _enter(agent: object, kind: str, invoke: Callable[[], Any]) -> Any:
    _require_available(agent, f"context {kind} entry")
    result = invoke()
    # A hook may catch its own failed Rip. Do not enter the with body while
    # that work is still pending.
    _require_available(agent, f"context {kind} entry")
    _entries.set(_entries.get() + (_Entry(agent, kind),))
    return result


async def _aenter(agent: object, invoke: Callable[[], Any]) -> Any:
    _require_available(agent, "async context entry")
    result = await invoke()
    _require_available(agent, "async context entry")
    _entries.set(_entries.get() + (_Entry(agent, "async"),))
    return result


def _take_entry(agent: object, kind: str) -> bool:
    entries = _entries.get()

    for index in range(len(entries) - 1, -1, -1):
        entry = entries[index]
        if entry.active and entry.agent() is agent and entry.kind == kind:
            entry.active = False
            _entries.set(entries[:index] + entries[index + 1:])
            return True

    return False


def _exit(
        agent: object,
        kind: str,
        failure: BaseException | None,
        invoke: Callable[[], Any],
        ) -> Any:
    if not _take_entry(agent, kind):
        _require_available(agent, f"context {kind} exit")
        result = invoke()
        _require_available(agent, f"context {kind} exit")
        return result

    was_arrested = _arrest_of(agent) is not None

    # Keep the cleanup door open throughout an entered exit, including a
    # Rip that arrests the Agent after the exit hook itself has begun.
    with _rip_door(agent):
        try:
            result = invoke()
        except BaseException:
            # A failure already held by the with body wins over a failed
            # cleanup of an *existing* arrest. If this exit caused the first
            # arrest, its new Rip failure must be visible instead.
            if failure is not None and was_arrested:
                raise failure
            raise

    # An exit may have caught a failed Rip and returned True. When there is
    # no body Rip error to preserve, check outside the cleanup door so the
    # saved work is retried before this context returns to ordinary code.
    if (
            _arrest_of(agent) is not None
            and (failure is None or not was_arrested)
            ):
        _require_available(agent, f"context {kind} exit")

    if failure is not None and was_arrested:
        return False

    return result


async def _aexit(
        agent: object,
        failure: BaseException | None,
        invoke: Callable[[], Any],
        ) -> Any:
    if not _take_entry(agent, "async"):
        _require_available(agent, "async context exit")

        async def Await_Exit() -> Any:
            return await invoke()

        # Guard the outer coroutine, including custom Awaitable results
        # whose own continuations the native-result helper cannot inspect.
        result = await _guard_lazy_result(
                Await_Exit(), agent, "async context exit", _require_available,
                )
        _require_available(agent, "async context exit")
        return result

    was_arrested = _arrest_of(agent) is not None
    with _rip_door(agent):
        try:
            result = await invoke()
        except BaseException:
            if failure is not None and was_arrested:
                raise failure
            raise

    if (
            _arrest_of(agent) is not None
            and (failure is None or not was_arrested)
            ):
        _require_available(agent, "async context exit")

    if failure is not None and was_arrested:
        return False

    return result
