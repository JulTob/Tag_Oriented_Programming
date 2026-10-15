"""Lifecycle: Rip, teardown, and exit protocols.

Rip ends active membership. Contributions are sticky: Actions and Records
stay on the Agent (a Rogue Agent) unless the Tag's @Rip teardowns change
them. Each Rip removes only the named Tag, even if a Shape stays active.

Of the three deletion tiers (§3.2), the kit gives the finalizer's
teardowns and At_Exit. The guaranteed tier is the program's own: it tags
before ``try`` and Rips in ``finally`` (STEP-SPEC-31).
"""

from __future__ import annotations

from typing import Any
import atexit

from .arrest import _arrest_of
from .declarations import _parameters_of
from .declarations import _action_chain
from .declarations import _discard_lazy_result
from .declarations import _Lazy_Rip_Guard
from .declarations import _lazy_rip_guard
from .declarations import _takes_underlay
from .errors import TagCompositionError
from .errors import TagResolutionError
from .fields import _Member
from .fields import _field_of
from .rip_runs import _RipRun
from .rip_runs import _pending_run
from .rip_runs import _retry_arrested as _retry_saved_runs
from .rip_runs import _run_saved
from .rip_runs import _save_run
from .state import _Originals
from .state import _State
from .state import _state_of


def _rip(
        agent: object,
        tag: type,
        ) -> object:
    """End this Tag's application, then finish older arrested work.

    If an old application of the same Tag still owes Rip, retry that
    application first. A new Tagging of the same Tag stays in its Field.
    """

    state = _state_of(agent)

    arrest = _arrest_of(agent)
    pending = _pending_run(agent, tag) if arrest is not None else None

    if pending is not None:
        _run_one(agent, state, pending)
        if _arrest_of(agent) is not None:
            _retry_arrested(agent)
        return agent

    if state is None or tag not in state.active:
        raise TagResolutionError(
                f"{tag.__name__} is not active on this Agent"
                )

    teardowns = state.rips.get(tag, ())

    if teardowns:
        run = _RipRun(tag, tuple(teardowns))
        # Publish the original work before the Agent leaves the Field.
        # A failing callback can then never strand an unrecorded suffix.
        _save_run(agent, run)
        _run_one(agent, state, run)
    else:
        # No callback can fail or remain unfinished. Keep ordinary Rip's
        # short path, including its one Field removal and sticky Gains.
        state.active.remove(tag)
        state.words = None
        state.snapshots.pop(tag, None)
        _field_of(tag)._Remove(agent)

    # An explicit other-Tag Rip runs its own protocol first. After it
    # succeeds, any older arrested work must clear before the Agent is free.
    if (teardowns or arrest is not None) and _arrest_of(agent) is not None:
        _retry_arrested(agent)

    return agent


def _retry_arrested(
        agent: object,
        ) -> object:
    """Retry live saved Rip work in original order from root Tag[...]."""

    state = _state_of(agent)

    if state is None:
        raise TagResolutionError("this Agent has no TOP state for saved Rip work")

    state.composing += 1

    try:
        return _retry_saved_runs(
                agent,
                lambda run: _revoke(agent, state, run),
                lambda run, name, teardown: _call_teardown(
                        name, teardown, agent, state,
                        ),
                )
    finally:
        state.composing -= 1


def _run_one(agent: object, state: _State, run: _RipRun) -> None:
    """Run a chosen Rip before older custody, retaining its failure seat."""

    state.composing += 1

    try:
        _run_saved(
                agent,
                run,
                lambda current: _revoke(agent, state, current),
                lambda current, name, teardown: _call_teardown(
                        name, teardown, agent, state,
                        ),
                )
    finally:
        state.composing -= 1


def _revoke(agent: object, state: _State, run: _RipRun) -> None:
    """Remove one saved application before its teardown starts.

    Repeating a partly interrupted revocation is safe. A new Tagging may
    happen during the later Rip callbacks, after this boundary is marked.
    """

    if run.revoked:
        return

    for index, active in enumerate(state.active):
        if active is run.tag:
            state.active.pop(index)
            break

    words = state.words
    snapshot = state.snapshots.get(run.tag)
    state.words = None
    state.snapshots.pop(run.tag, None)
    _field_of(run.tag)._Remove(agent)
    state.rips.pop(run.tag, None)
    _ = (words, snapshot)


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
