"""Access: the hooks on the runtime type and the Agent-bound Tag views.

Three access forms, three meanings:

    agent.name          the current visible Overlay (Agent scope)
    agent.Wizard.name   the Overlay as it was right after Wizard applied
    Wizard.name         the Tag itself (Tag scope)
"""

from __future__ import annotations

from functools import partial
from typing import Any

from .errors import TagCompositionError
from .errors import TagResolutionError
from .state import _Bound
from .state import _Snapshot
from .state import _State
from .state import _state_of


# ------------------------------------------------------------------
# Hooks placed on every runtime type
# ------------------------------------------------------------------


def _host_member(
        host_type: type,
        name: str,
        ) -> Any:
    """A special method the host itself defines, or None."""

    for klass in host_type.__mro__:
        if klass is object:
            break

        member = klass.__dict__.get(name)

        if member is not None:
            return member

    return None


def _hooks_for(
        host_type: type,
        has_posts: bool,
        has_flags: bool,
        ) -> dict[str, Any]:
    hooks: dict[str, Any] = {
            "__getattr__": _agent_getattr,
            "__del__": _agent_del,
            "_TAGKIT_HOST_TYPE": host_type,
            "_TAGKIT_HOST_GETATTR": _host_member(host_type, "__getattr__"),
            "_TAGKIT_HOST_DEL": _host_member(host_type, "__del__"),
            }

    if has_posts:
        hooks["__bool__"] = _agent_bool

    if _host_member(host_type, "__format__") is None:
        hooks["__format__"] = _agent_format

    if has_flags:
        hooks["__contains__"] = _agent_contains

    if _host_member(host_type, "__copy__") is None:
        hooks["__copy__"] = _agent_copy

    if _host_member(host_type, "__deepcopy__") is None:
        hooks["__deepcopy__"] = _agent_deepcopy

    return hooks


def _agent_getattr(
        agent: object,
        name: str,
        ) -> Any:
    """Miss path only: Tag views by name, then the host's own __getattr__."""

    state = _state_of(agent)

    if state is not None:
        for tag in reversed(state.active):
            if tag.__name__ == name:
                return _view_of(
                        agent,
                        tag,
                        state,
                        )

    host_getattr = type(agent).__dict__.get("_TAGKIT_HOST_GETATTR")

    if host_getattr is not None:
        return host_getattr(
                agent,
                name,
                )

    raise AttributeError(
            f"{type(agent).__name__} has no member {name!r}"
            )


def _agent_format(
        agent: object,
        spec: str,
        ) -> str:
    """``f"{agent:tags}"``, ``f"{agent:outline}"``, ``f"{agent:contract}"``."""

    if spec == "":
        return str(agent)

    if spec == "tags":
        from .queries import Tags

        return ", ".join(
                tag.__name__
                for tag in Tags(agent)
                )

    if spec == "outline":
        from .queries import Outline

        return Outline(agent)

    if spec == "contract":
        from .contracts import Contract

        return Contract.Display(agent)

    raise ValueError(
            f"unknown format spec {spec!r} for an Agent; use 'tags',"
            " 'outline', or 'contract'"
            )


def _agent_contains(
        agent: object,
        probe: object,
        ) -> bool:
    """``"Undead" in ghoul`` and ``Undead in ghoul``: an active Flag, by
    name or by class."""

    return _keyword(
            agent,
            probe,
            )


def _keyword(
        agent: object,
        probe: object,
        ) -> bool:
    from .declarations import _is_flag

    state = _state_of(agent)

    if state is None:
        return False

    if isinstance(probe, str):
        return any(
                _is_flag(tag) and tag.__name__ == probe
                for tag in state.active
                )

    return (
            probe in state.active
            and _is_flag(probe)
            )


def _agent_bool(
        agent: object,
        ) -> bool:
    from .contracts import _holds

    return _holds(agent)


def _agent_del(
        agent: object,
        ) -> None:
    # Best effort: run remaining teardowns, then the host's finalizer.
    # Python does not promise finalizers at shutdown or inside cycles;
    # Scope() is the guaranteed path.
    try:
        from .lifecycle import _teardown_all

        _teardown_all(agent)

        host_del = type(agent).__dict__.get("_TAGKIT_HOST_DEL")

        if host_del is not None:
            host_del(agent)
    except Exception:
        pass


def _agent_copy(
        agent: object,
        ) -> object:
    raise TagCompositionError(
            "copying an Agent is domain work: build a new Target and apply"
            " its Tags again (Tags(agent) lists them)"
            )


def _agent_deepcopy(
        agent: object,
        memo: dict[int, Any],
        ) -> object:
    return _agent_copy(agent)


# ------------------------------------------------------------------
# Agent-bound Tag views
# ------------------------------------------------------------------


class _Tag_View:
    """The Overlay snapshot captured right after one Tag applied."""

    __slots__ = (
            "_agent",
            "_tag",
            "_snapshot",
            )

    def __init__(
            view,
            agent: object,
            tag: type,
            snapshot: _Snapshot,
            ) -> None:
        object.__setattr__(view, "_agent", agent)
        object.__setattr__(view, "_tag", tag)
        object.__setattr__(view, "_snapshot", snapshot)

    def __getattr__(
            view,
            name: str,
            ) -> Any:
        snapshot: _Snapshot = view._snapshot
        agent = view._agent

        if name in snapshot.deleted:
            raise AttributeError(
                    f"{view._tag.__name__} deleted {name!r}"
                    )

        if name in snapshot.secrets and _state_of(agent).composing == 0:
            raise AttributeError(
                    f"{name!r} is a secret member of {view._tag.__name__}"
                    )

        if name in snapshot.actions:
            return _Bound(
                    snapshot.actions[name],
                    agent,
                    )

        if name in snapshot.records:
            return snapshot.records[name]

        if name in snapshot.reports:
            return snapshot.reports[name][1]

        if name in snapshot.operations:
            origin, operation = snapshot.operations[name]

            return partial(
                    operation,
                    origin,
                    )

        raise AttributeError(
                f"{view._tag.__name__} view has no member {name!r}"
                )

    def __setattr__(
            view,
            name: str,
            value: Any,
            ) -> None:
        raise AttributeError("a Tag view is a snapshot; it is read-only")

    def __repr__(
            view,
            ) -> str:
        return f"<{view._tag.__name__} view of {type(view._agent).__name__}>"


def _view_of(
        agent: object,
        tag: type,
        state: _State | None = None,
        ) -> _Tag_View:
    if state is None:
        state = _state_of(agent)

    if state is None or tag not in state.active:
        raise TagResolutionError(
                f"{tag.__name__} is not active on this Agent"
                )

    return _Tag_View(
            agent,
            tag,
            state.snapshots[tag],
            )
