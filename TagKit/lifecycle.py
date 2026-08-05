from __future__ import annotations

"""Best-effort exit integration for active Rip protocols."""

from typing import Callable
import atexit
import weakref

from .declarations import Target
from .declarations import _require_synchronous_result
from .errors import TagCompositionError
from .runtime_types import _existing_state_for
from .runtime_types import _host_action_for


_exit_registry = {}


def _host_finalizer(
        agent: object,
        ) -> Callable[[object], None] | None:
    """Find a host ``__del__`` shadowed by ``Tagged.__del__``, if any."""

    runtime_type = type(agent)
    host_type = runtime_type.__dict__.get(
            "_TAGKIT_HOST_TYPE",
            runtime_type,
            )

    return _host_action_for(
            host_type,
            "__del__",
            agent,
            )


def At_Exit(
        agent: Target,
        ) -> Target:
    """Register an Agent's @Rip teardown to also run at interpreter exit.

    The registration is weak and never keeps the Agent alive. At a normal
    exit, any still-active @Rip teardown runs once (best-effort). This
    complements ``__del__``, which Python does not guarantee at shutdown.
    """

    identity = id(agent)
    current = _exit_registry.get(identity)

    if (
            current is not None
            and current() is agent
            ):
        return agent

    def Forget(
            expired: weakref.ReferenceType[object],
            ) -> None:
        if _exit_registry.get(identity) is expired:
            _exit_registry.pop(
                    identity,
                    None,
                    )

    try:
        reference = weakref.ref(
                agent,
                Forget,
                )
    except TypeError as error:
        raise TagCompositionError(
                "At_Exit Agents must support weak references"
                ) from error

    _exit_registry[identity] = reference

    return agent


def _run_exit_protocols() -> None:
    for reference in tuple(
            _exit_registry.values()
            ):
        agent = reference()

        if agent is None:
            continue

        state = _existing_state_for(agent)

        if state is None or state.ripped:
            continue

        state.ripped = True

        for tag in reversed(state.active_tags):
            for name, rip in state.rip_actions.get(tag, ()):
                try:
                    _require_synchronous_result(
                            rip(agent),
                            (
                                "At-exit Rip protocol"
                                f" {tag.__qualname__}.{name}"
                                ),
                            )
                except Exception:
                    pass


atexit.register(
        _run_exit_protocols
        )
