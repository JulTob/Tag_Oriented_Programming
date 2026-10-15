"""Lifecycle: Rip, teardown, and exit protocols.

Rip ends active membership. Contributions are sticky: Actions and Records
stay on the Agent (a Rogue Agent) unless the Tag's @Rip teardowns change
them. Each Rip removes only the named Tag, even if a Shape stays active.

Of the three deletion tiers (§3.2), the kit gives the finalizer's
teardowns and At_Exit. The guaranteed tier is the program's own: it tags
before ``try`` and Rips in ``finally`` (STEP-SPEC-31).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from types import MappingProxyType
import atexit

from .declarations import _parameters_of
from .declarations import _action_chain
from .declarations import _discard_lazy_result
from .declarations import STATE
from .declarations import _Lazy_Rip_Guard
from .declarations import _lazy_rip_guard
from .declarations import _takes_underlay
from .errors import TagCompositionError
from .errors import TagResolutionError
from .fields import _Member
from .fields import _field_of
from .state import _Originals
from .state import _State
from .state import _real_namespace_of
from .state import _state_of


@dataclass(frozen=True, slots=True)
class _RipRun:
    """The teardown work saved when one Tag application leaves its Field."""

    tag: type
    teardowns: tuple[tuple[str, Any], ...]


def _rip(
        agent: object,
        tag: type,
        ) -> object:
    state, run = _revoke_membership(agent, tag)

    _teardown(
            agent,
            state,
            run,
            )

    return agent


def _revoke_membership(
        agent: object,
        tag: type,
        ) -> tuple[_State, _RipRun]:
    """End one membership and save its Rip chain before callbacks run."""

    state = _state_of(agent)

    if state is None or tag not in state.active:
        raise TagResolutionError(
                f"{tag.__name__} is not active on this Agent"
                )

    state.active.remove(tag)
    state.words = None
    state.snapshots.pop(tag, None)   # a view needs membership: never read again
    _field_of(tag)._Remove(agent)

    return state, _RipRun(tag, state.rips.pop(tag, ()))


def _rip_field(
        tag: type,
        ) -> None:
    """Rip the Field as it stood at entry: revoke all, then clean up FIFO."""

    field = _field_of(tag)
    pending = []

    for agent in list(field):
        # Read the real state without asking a host's __dict__ property.
        namespace = _real_namespace_of(agent)
        if namespace is None:
            state = None
        elif issubclass(type(namespace), dict):
            # A host may use a dict subclass with a user-defined get().
            state = dict.get(namespace, STATE)
        else:
            # A Pin's native namespace is a mappingproxy.
            state = MappingProxyType.get(namespace, STATE)

        if state is None:
            raise TagResolutionError(
                    f"{tag.__name__} is not active on this Agent"
                    )

        for index, active in enumerate(state.active):
            if active is tag:
                break
        else:
            raise TagResolutionError(
                    f"{tag.__name__} is not active on this Agent"
                    )

        state.active.pop(index)
        words = state.words   # do not release a possible last Tag reference yet
        state.words = None
        snapshot = state.snapshots.pop(tag, None)
        field._Remove(agent)
        run = _RipRun(tag, state.rips.pop(tag, ()))
        pending.append((agent, state, run, words, snapshot))

    # Arrest and ordered retry belong to STEP-SPEC-32. Until that protocol
    # is decided, use the existing per-Agent teardown behavior and finish
    # attempting cleanup for every member before reporting failures.
    failures: list[Exception] = []

    for agent, state, run, _words, _snapshot in pending:
        try:
            _teardown(agent, state, run)
        except Exception as error:
            failures.append(error)

    pending.clear()   # release saved views only after every cleanup attempt

    if failures:
        raise TagCompositionError(
                f"{tag.__name__} Field teardown failed for"
                f" {len(failures)} member(s)"
                ) from failures[0]


def _teardown(
        agent: object,
        state: _State,
        run: _RipRun,
        ) -> None:
    """Run every saved @Rip teardown once, then report failures."""

    failures: list[tuple[str, Exception]] = []
    state.composing += 1

    try:
        for name, teardown in run.teardowns:
            try:
                _call_teardown(
                        name,
                        teardown,
                        agent,
                        state,
                        )
            except Exception as error:
                failures.append(
                        (
                            name,
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
                f"{run.tag.__name__} teardown failed in: {names}"
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
            for name, teardown in state.rips.pop(tag, ()):
                try:
                    _call_teardown(
                            name,
                            teardown,
                            agent,
                            state,
                            )
                except Exception:
                    pass
    finally:
        state.composing -= 1


def _call_teardown(
        name: str,
        teardown: Any,
        agent: object,
        state: _State,
        ) -> None:
    """Run one @Rip teardown. On a pinned Tag, a teardown that declares a
    seat after the receiver (and after its Underlay, if it takes one)
    receives the Tag's original declarations, so un-patching is
    ``tag.Control = original.Control``."""

    guard = _Lazy_Rip_Guard(
            name,
            _action_chain(teardown)
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
            receiver_seats = 2 if _takes_underlay(declared, name) else 1

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
                f"Rip protocol {str.__str__(name)!r} returned {article}"
                f" {lazy}; a Rip protocol must complete synchronously."
                " TOP does not await or iterate teardown protocols."
                )


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
