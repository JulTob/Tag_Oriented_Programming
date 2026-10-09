"""Access: the hooks on the runtime type and the Agent-bound Tag views.

Three access forms, three meanings:

    agent.name          the current visible Overlay (Agent scope)
    agent.Wizard.name   the Overlay as it was right after Wizard applied
    Wizard.name         the Tag itself (Tag scope)
"""

from __future__ import annotations

from functools import partial
from typing import Any
from typing import Callable
import sys

from . import declarations
from .contracts import _condition_member
from .contracts import _holds
from .errors import TagCompositionError
from .errors import TagResolutionError
from .declarations import STATE
from .declarations import _MISSING
from .declarations import _is_flag
from .declarations import _words_of
from .lifecycle import _teardown_all
from .state import _Bound
from .state import _Pinned_Operation
from .state import _Snapshot
from .state import _State
from .state import _name_of
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

        if "_TOPKIT_HOST_TYPE" in klass.__dict__:
            continue   # a runtime type: its members are the kit's or a Tag's, not the host's

        member = klass.__dict__.get(name)

        if member is not None:
            return member

    return None


IN_SEAT = (
        "__contains__",
        "__iter__",
        )


def _host_in_seat(
        host_type: type,
        ) -> tuple[str, type] | None:
    """How the host answers `in`: the special method and the class that
    defines it, or None when the seat is free (STEP-SPEC-7).

    Resolved as Python resolves `in`: ``__contains__``, then ``__iter__``.
    For each, the first class in the MRO that defines the name decides. A
    method owns the seat; the value None says `in` is unavailable, Python
    tries nothing further, and the seat is free. ``__getitem__`` alone is
    not a seat a Flag respects: on a keyed host its `in` fails or never
    ends; on an index-style host it worked, and stops meaning membership
    once a Flag lands (the Director's call, STEP-SPEC-7)."""

    for name in IN_SEAT:
        for klass in host_type.__mro__:
            if klass is object:
                break

            if name in klass.__dict__:
                if klass.__dict__[name] is None:
                    return None

                return (
                        name,
                        klass,
                        )

    return None


def _hooks_for(
        host_type: type,
        has_flags: bool,
        ) -> dict[str, Any]:
    """The kit's special methods for one host. ``__bool__`` is on every
    Agent: its truth is its contract, even over the host's ``__len__``,
    which still answers ``len`` (§2.5). A host with its own ``__bool__``
    never gets here (§0.5), but a Tag does: it keeps its metaclass's
    truth, "anyone sound?"."""

    hooks: dict[str, Any] = {
            "__getattr__": _agent_getattr,
            "__del__": _agent_del,
            "_TOPKIT_HOST_TYPE": host_type,
            "_TOPKIT_HOST_GETATTR": _host_member(host_type, "__getattr__"),
            }

    if _host_member(host_type, "__bool__") is None:
        hooks["__bool__"] = _agent_bool

    if _host_member(host_type, "__format__") is None:
        hooks["__format__"] = _agent_format

    if has_flags and _host_in_seat(host_type) is None:
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
    """Miss path only: Tag views by name, then a condition by name as a
    plain bool (STEP-SPEC-14), then the host's own __getattr__."""

    state = _state_of(agent)

    if state is not None:
        if name in state.secrets and state.pinned is not None:
            return _secret_of_tag(
                    agent,
                    state,
                    name,
                    )

        for tag in reversed(state.active):
            if tag.__name__ == name:
                return _view_of(
                        agent,
                        tag,
                        state,
                        )

        if state.postconditions or state.preconditions:
            verdict = _condition_member(
                    agent,
                    state,
                    name,
                    )

            if verdict is not None:
                return verdict

    host_getattr = type(agent).__dict__.get("_TOPKIT_HOST_GETATTR")

    if host_getattr is not None:
        return host_getattr(
                agent,
                name,
                )

    raise AttributeError(
            f"{_name_of(agent)} has no member {name!r}"
            )


def _secret_of_tag(
        tag: type,
        state: _State,
        name: str,
        ) -> Any:
    """A Pin's @Secret member on a Tag: held in the state, resolved only
    while the Tag's own protocols or pinned Operations run."""

    if state.composing == 0:
        raise AttributeError(
                f"{name!r} is a secret member of {tag.__name__}; it is"
                " reachable only from its Pins' own Actions and protocols"
                )

    value = state.secret_values.get(
            name,
            _MISSING,
            )

    if value is _MISSING:
        raise AttributeError(
                f"{tag.__name__} has no visible member {name!r}"
                )

    if isinstance(value, _Pinned_Operation):
        return value.__get__(
                None,
                tag,
                )

    return value


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
    name, alias or class."""

    return _keyword(
            agent,
            probe,
            )


def _keyword(
        agent: object,
        probe: object,
        ) -> bool:
    state = _state_of(agent)

    if state is None:
        return False

    if isinstance(probe, str):
        if type(probe) is not str:
            probe = str.__str__(probe)   # its text: exact, and hashable

        words = state.words

        if words is None or words.flags_declared != declarations._flags_declared:
            # Read the count before gathering: a @Flag declared meanwhile then
            # marks these words stale, instead of letting them pass for new.
            words = state.words = _words_of(
                    state.active,
                    declarations._flags_declared,
                    )

        if probe in words.aliases:
            return True

        for tag in words.flags:
            if tag.__name__ == probe:
                return True

        return False

    return (
            probe in state.active
            and _is_flag(probe)
            )


def _agent_bool(
        agent: object,
        ) -> bool:
    """An Agent's truth is its contract (STEP-SPEC-28): true while every
    visible promise holds, and true with none. An object built from an
    Agent's runtime type but never tagged is a plain host object, and
    keeps its host's truth."""

    state = _state_of(agent)

    if state is None:
        return _host_truth(agent)

    if not state.postconditions:
        return True   # nothing promised

    return _holds(agent)


def _host_truth(
        agent: object,
        ) -> bool:
    """Python's own truth for a host with no ``__bool__``: its length when
    it has one, otherwise true."""

    if hasattr(
            type(agent),
            "__len__",
            ):
        return len(agent) != 0

    return True


def _host_finalizer(
        agent: object,
        kind: type = type,
        missing: type = AttributeError,
        ) -> None:
    """The host's own ``__del__``, found as Python finds it: through the
    object's type, past the kit's runtime types, the first class that
    defines one decides, ``None`` there means there is none, and a
    descriptor is bound first.

    It also runs late in interpreter exit, when this module's globals and
    even the builtins may be gone, so it needs neither: ``kind`` and
    ``missing`` are bound here."""

    for klass in kind(agent).__mro__:
        if "_TOPKIT_HOST_TYPE" in klass.__dict__:
            continue   # a runtime type: its __del__ is the kit's finalizer

        if "__del__" in klass.__dict__:
            finalizer = klass.__dict__["__del__"]
            break
    else:
        return

    if finalizer is None:
        return

    try:
        bind = kind(finalizer).__get__
    except missing:
        finalizer()   # not a descriptor: Python calls it as it is
        return

    bind(
            finalizer,
            agent,
            kind(agent),
            )()


def _agent_del(
        agent: object,
        finalizing: Callable[[], bool] = sys.is_finalizing,
        state_key: str = STATE,
        host_finalizer: Callable[[object], None] = _host_finalizer,
        read: Callable[[object, str], Any] = object.__getattribute__,
        ) -> None:
    """Deletion (§3.2, STEP-SPEC-18). The teardowns still due run, best
    effort; then the Agent's ``__del__`` runs as its Overlay shows it: the
    top Layer, which reaches the host's own through ``@Underlay``, or the
    host's own when no Tag declares one. At interpreter exit only the
    ``__del__`` Layers run: teardowns there are At_Exit's, and opt-in. A
    ``__del__`` Layer's own error is reported as Python reports any
    finalizer's.

    At exit this module's globals, and even the builtins, may already be
    gone. So the exit path uses neither: what it needs is bound here as a
    default, or found on the Agent. The Agent is read as Python reads it,
    never through the host's own ``__getattribute__``."""

    state = read(agent, "__dict__").get(state_key)

    if state is None:
        host_finalizer(agent)   # built from an Agent's runtime type, never tagged: a plain host
        return

    interrupted = None

    if not finalizing():
        try:
            _teardown_all(agent)
        except Exception:
            pass   # best effort (§3.2)
        except BaseException as error:
            interrupted = error   # Ctrl-C in a teardown: the __del__ Layers still run

    try:
        layer = state.actions.get("__del__")

        if layer is not None:
            state.composing += 1   # a Tag's Layer runs inside the composition door (§1.5)

            try:
                layer(agent)
            finally:
                state.composing -= 1
        elif "__del__" not in state.deleted:
            host_finalizer(agent)
    finally:
        if interrupted is not None:
            raise interrupted   # reported after the Layers, whatever they raised


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
        return f"<{view._tag.__name__} view of {_name_of(view._agent)}>"


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
