"""Identity-held Agents whose saved Rip work remains unfinished."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any
from typing import Iterator

from .errors import TagArrestedAccessError

class _Arrest:
    __slots__ = ("agent", "runs", "lazy")

    def __init__(self, agent: object) -> None:
        self.agent = agent
        self.runs: list[Any] = []
        self.lazy: list[Any] = []   # denied lazy Actions must not finalize while arrested


# Never invoke a host's hash or equality just to keep its unfinished Rip.
_safehouse: dict[int, _Arrest] = {}


def _arrest_of(
        agent: object,
        _entries: dict[int, _Arrest] = _safehouse,
        _identify = id,
        ) -> _Arrest | None:
    # These defaults also keep late generator finalization independent of
    # module globals that Python may clear while the interpreter exits.
    arrest = dict.get(_entries, _identify(agent))
    return arrest if arrest is not None and arrest.agent is agent and arrest.runs else None


def _hold_lazy_result(
        agent: object,
        source: object,
        _lookup = _arrest_of,
        ) -> None:
    """Keep a denied lazy source from finalizing before Rip completes.

    The Safehouse already retains the Agent. It also retains a suspended
    result whose caller abandons it after a denied resume: otherwise its
    ``finally`` could run outside the only permitted Rip door during GC.
    """

    arrest = _lookup(agent)
    if arrest is not None:
        for held in arrest.lazy:
            if held is source:
                return
        arrest.lazy.append(source)


class _Rip_Door:
    """Permission to act on one Agent during its saved Rip callback only.

    A copied Context may outlive the callback. Closing this shared door
    revokes even those copies, as with the asynchronous Secret door.
    """

    __slots__ = ("active", "agent")

    def __init__(self, agent: object) -> None:
        self.active = True
        self.agent: object | None = agent

    def Close(self) -> None:
        self.active = False
        self.agent = None


_rip_doors: ContextVar[tuple[_Rip_Door, ...]] = ContextVar(
        "topkit_rip_doors",
        default=(),
        )


@contextmanager
def _rip_door(agent: object) -> Iterator[None]:
    door = _Rip_Door(agent)
    _rip_doors.set(tuple(
            active for active in _rip_doors.get() if active.active
            ) + (door,))

    try:
        yield
    finally:
        door.Close()
        # An async exit may be closed from a different Context after it
        # suspended. A ContextVar token belongs only to its origin Context;
        # pruning this Context and revoking the shared door works in both.
        _rip_doors.set(tuple(
                active for active in _rip_doors.get() if active.active
                ))


def _may_act(agent: object) -> bool:
    if _arrest_of(agent) is None:
        return True

    return any(
            door.active and door.agent is agent
            for door in reversed(_rip_doors.get())
            )


def _require_available(agent: object, act: str) -> None:
    """Refuse a TOP act while this Agent has unfinished Rip work.

    Public Rip activation will first retry that work, then use this same
    boundary to decide whether the requested act may proceed.
    """

    if not _may_act(agent):
        raise TagArrestedAccessError(
                f"{act} is unavailable: this Agent has unfinished Rip work"
                )
