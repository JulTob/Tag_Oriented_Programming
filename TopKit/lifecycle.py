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

from .declarations import _parameters_of
from .declarations import _ACTION_CHAIN
from .declarations import _discard_lazy_result
from .declarations import _Lazy_Rip_Guard
from .declarations import _lazy_rip_guard
from .declarations import _takes_underlay
from .errors import TagCompositionError
from .errors import TagError
from .errors import TagPostconditionError
from .errors import TagResolutionError
from .fields import _Member
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
    state.words = None
    state.snapshots.pop(tag, None)   # a view needs membership: never read again
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

    state.composing += 1   # teardowns run inside the composition door, as on a Rip

    try:
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
    finally:
        state.composing -= 1


def _call_teardown(
        teardown: Any,
        agent: object,
        state: _State,
        ) -> None:
    """Run one @Rip teardown. On a pinned Tag, a teardown that declares a
    seat after the receiver (and after its Underlay, if it takes one)
    receives the Tag's original declarations, so un-patching is
    ``tag.Control = original.Control``."""

    guard = _Lazy_Rip_Guard(
            getattr(
                teardown,
                _ACTION_CHAIN,
                None,
                )
            )
    token = _lazy_rip_guard.set(guard)

    try:
        if state.pinned is None:
            result = teardown(agent)
        else:
            declared = getattr(
                    teardown,
                    "__wrapped__",
                    teardown,
                    )
            seats = _parameters_of(declared).positional
            receiver_seats = 2 if _takes_underlay(declared) else 1

            if seats > receiver_seats:
                result = teardown(
                        agent,
                        _Originals(state.originals),
                        )
            else:
                result = teardown(agent)
    finally:
        guard.active = False
        _lazy_rip_guard.reset(token)

    lazy = _discard_lazy_result(result)

    if guard.failures:
        raise guard.failures[0]

    if lazy is not None:
        article = "an" if lazy == "async generator" else "a"

        raise TagCompositionError(
                f"Rip protocol {teardown.__qualname__} returned {article}"
                f" {lazy}; a Rip protocol must complete synchronously."
                " TOP does not await or iterate teardown protocols."
                )


@contextmanager
def Scope(
        agent: object,
        *tags: type,
        **inputs: Any,
        ) -> Iterator[object]:
    """Apply Tags for a block and Rip them, in reverse, on exit, even if
    the block raises. The guaranteed teardown path.

    Only what the Scope itself applied is Ripped: a Tag the Agent already
    carried at entry is left as it was. A Tag that applied and then
    reported a broken promise at the door did apply, so it is Ripped on
    the way out like any other.
    """

    applied: list[type] = []

    try:
        for tag in tags:
            if agent in tag:
                continue                    # already the Agent's: not the Scope's to take away

            try:
                tag(
                        agent,
                        **inputs,
                        )
            except TagPostconditionError:
                applied.append(tag)         # applied, and defective: still the Scope's to Rip
                raise

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


_exit_registry: dict[int, _Member] = {}   # by registration number; an entry leaves when its Agent dies
_exit_count = 0   # registrations so far; each one's number is its key


def _forget_exit(
        expired: _Member,
        ) -> None:
    _exit_registry.pop(expired.key, None)


def At_Exit(
        agent: object,
        ) -> object:
    """Also run the Agent's teardowns at normal interpreter exit.

    Registration is weak: it never keeps the Agent alive, and it leaves
    the registry when the Agent dies.
    """

    global _exit_count

    reference = _Member(
            agent,
            _forget_exit,
            )
    reference.key = _exit_count
    _exit_registry[reference.key] = reference
    _exit_count += 1

    return agent


def _run_exit_protocols() -> None:
    number = 0

    while number < _exit_count:   # registrations made during the pass are reached too
        reference = _exit_registry.get(number)
        number += 1

        if reference is not None:
            agent = reference()

            if agent is not None:
                _teardown_all(agent)


atexit.register(_run_exit_protocols)
