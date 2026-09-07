"""Lifecycle: Rip, teardown, Scope, and exit protocols.

Rip ends active membership. Contributions are sticky: Actions and Records
stay on the Agent (a Rogue Agent) unless the Tag's @Rip teardowns change
them. Ripping a Base is refused while an active Shape still requires it.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any
from typing import Iterator
import atexit
import weakref

from .declarations import _parameters_of
from .declarations import _takes_underlay
from .errors import TagCompositionError
from .errors import TagError
from .errors import TagResolutionError
from .geometry import _requiring_shapes
from .state import _Originals
from .state import _State
from .state import _state_of


def _rip(
        agent: object,
        tag: type,
        ) -> object:
    state = _state_of(agent)

    if state is None or tag not in state.active:
        raise TagResolutionError(
                f"{tag.__name__} is not active on this Agent"
                )

    blocking = _requiring_shapes(
            tag,
            state.active,
            )

    if blocking:
        names = ", ".join(
                shape.__name__
                for shape in blocking
                )

        raise TagCompositionError(
                f"{tag.__name__} is required by active Shape(s): {names}"
                )

    state.active.remove(tag)
    tag._topkit_field.Remove(agent)

    _teardown(
            agent,
            state,
            tag,
            )

    return agent


def _teardown(
        agent: object,
        state: _State,
        tag: type,
        ) -> None:
    """Run every @Rip teardown of ``tag`` once, then report failures."""

    teardowns = state.rips.pop(tag, ())
    failures: list[tuple[str, Exception]] = []
    state.composing += 1

    try:
        for teardown in teardowns:
            try:
                _call_teardown(
                        teardown,
                        agent,
                        state,
                        )
            except Exception as error:
                failures.append(
                        (
                            teardown.__name__,
                            error,
                            )
                        )
    finally:
        state.composing -= 1

    if failures:
        names = ", ".join(
                name
                for name, _error in failures
                )

        raise TagCompositionError(
                f"{tag.__name__} teardown failed in: {names}"
                ) from failures[0][1]


def _teardown_all(
        agent: object,
        ) -> None:
    """Best-effort teardown of every still-active Tag (finalizer, exit)."""

    state = _state_of(agent)

    if state is None:
        return

    for tag in reversed(list(state.active)):
        for teardown in state.rips.pop(tag, ()):
            try:
                _call_teardown(
                        teardown,
                        agent,
                        state,
                        )
            except Exception:
                pass


def _call_teardown(
        teardown: Any,
        agent: object,
        state: _State,
        ) -> None:
    """Run one @Rip teardown. On a pinned Tag, a teardown that declares a
    seat after the receiver (and after its Underlay, if it takes one)
    receives the Tag's original declarations, so un-patching is
    ``tag.Control = original.Control``."""

    if state.pinned is None:
        teardown(agent)
        return

    declared = getattr(
            teardown,
            "__wrapped__",
            teardown,
            )
    seats = _parameters_of(declared).positional
    receiver_seats = 2 if _takes_underlay(declared) else 1

    if seats > receiver_seats:
        teardown(
                agent,
                _Originals(state.originals),
                )
    else:
        teardown(agent)


@contextmanager
def Scope(
        agent: object,
        *tags: type,
        **inputs: Any,
        ) -> Iterator[object]:
    """Apply Tags for a block and Rip them, in reverse, on exit, even if
    the block raises. The guaranteed teardown path."""

    applied: list[type] = []

    try:
        for tag in tags:
            tag(
                    agent,
                    **inputs,
                    )
            applied.append(tag)

        yield agent
    finally:
        for tag in reversed(applied):
            try:
                _rip(
                        agent,
                        tag,
                        )
            except TagError:
                pass


_exit_registry: list[weakref.ReferenceType[object]] = []


def At_Exit(
        agent: object,
        ) -> object:
    """Also run the Agent's teardowns at normal interpreter exit.

    Registration is weak: it never keeps the Agent alive.
    """

    _exit_registry[:] = [
            reference
            for reference in _exit_registry
            if reference() is not None
            ]
    _exit_registry.append(
            weakref.ref(agent)
            )

    return agent


def _run_exit_protocols() -> None:
    for reference in _exit_registry:
        agent = reference()

        if agent is not None:
            _teardown_all(agent)


atexit.register(_run_exit_protocols)
