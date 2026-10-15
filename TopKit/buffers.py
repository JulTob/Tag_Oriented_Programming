"""Permit the matching release of a Host buffer acquired before arrest."""

from __future__ import annotations

from threading import RLock
from typing import Any
from typing import Callable
import weakref

from .arrest import _require_available
from .arrest import _rip_door


class _Acquired_Buffer:
    __slots__ = ("agent", "view")

    def __init__(self, agent: object, view: memoryview) -> None:
        self.agent = weakref.ref(agent)
        self.view = weakref.ref(view)


# __release_buffer__ receives the view returned by __buffer__, rather than
# the outer memoryview made for the caller. One Host may export the very same
# view more than once, so each acquisition gets one release ticket.
_buffers: dict[int, list[_Acquired_Buffer]] = {}
_buffer_lock = RLock()


def _live_view(value: object) -> bool:
    if not isinstance(value, memoryview):
        return False
    try:
        value.nbytes
    except ValueError:
        # Python rejects a pre-released view without calling the Host's
        # release hook. It must not leave an acquired release ticket.
        return False
    return True


def _remember(agent: object, view: memoryview) -> None:
    key = id(view)
    entry = _Acquired_Buffer(agent, view)
    entries_by_id = _buffers
    lock = _buffer_lock

    def Expire(_reference: weakref.ReferenceType[memoryview]) -> None:
        # A view may expire during interpreter shutdown, after this module's
        # globals have been cleared. Keep only these ledger references alive.
        with lock:
            entries = entries_by_id.get(key)
            if entries is None:
                return
            try:
                entries.remove(entry)
            except ValueError:
                return
            if not entries:
                entries_by_id.pop(key, None)

    entry.view = weakref.ref(view, Expire)
    with _buffer_lock:
        _buffers.setdefault(key, []).append(entry)


def _take(agent: object, view: object) -> bool:
    key = id(view)
    with _buffer_lock:
        entries = _buffers.get(key)
        if entries is None:
            return False
        for index in range(len(entries) - 1, -1, -1):
            entry = entries[index]
            if entry.agent() is agent and entry.view() is view:
                entries.pop(index)
                if not entries:
                    _buffers.pop(key, None)
                return True
    return False


def _acquire_buffer(
        agent: object,
        invoke: Callable[[], Any],
        release: Callable[[memoryview], Any] | None,
        ) -> Any:
    _require_available(agent, "buffer acquisition")
    view = invoke()
    try:
        # A Host can catch its own failing Rip and still return a view.
        _require_available(agent, "buffer acquisition")
    except BaseException as denial:
        if _live_view(view) and release is not None:
            # Python never received this acquisition and will not call the
            # matching release hook. Run it once, without losing the Rip
            # failure if cleanup itself also fails.
            try:
                with _rip_door(agent):
                    release(view)
            except BaseException as cleanup_error:
                try:
                    denial.add_note(
                            "buffer cleanup also failed:"
                            f" {type(cleanup_error).__name__}"
                            )
                except BaseException:
                    pass
        raise

    if _live_view(view) and release is not None:
        _remember(agent, view)
    return view


def _release_buffer(
        agent: object,
        view: object,
        invoke: Callable[[], Any],
        ) -> Any:
    if _take(agent, view):
        with _rip_door(agent):
            return invoke()

    _require_available(agent, "buffer release")
    result = invoke()
    _require_available(agent, "buffer release")
    return result
