"""Access: the hooks on the runtime type and the Agent-bound Tag views.

Three access forms, three meanings:

    agent.name          the current visible Overlay (Agent scope)
    agent.Wizard.name   the Overlay as it was right after Wizard applied
    Wizard.name         the Tag itself (Tag scope)
"""

from __future__ import annotations

from functools import partial
from inspect import getattr_static
from types import FunctionType
from types import MethodType
from typing import Any
from typing import Callable
from weakref import ref
import operator
import sys

from . import declarations
from . import state as state_module
from .arrest import _arrest_of
from .arrest import _require_available
from .arrest import _safehouse
from .lazy_guard import _guard_lazy_result
from .contracts import _condition_member
from .contracts import _holds
from .errors import TagCompositionError
from .errors import TagResolutionError
from .declarations import STATE
from .declarations import _MISSING
from .declarations import _is_flag
from .declarations import _words_of
from .lifecycle import _teardown_all
from .observations import _unobserved_cleanup
from .state import _Composing_Bound
from .state import _Pinned_Operation
from .state import _Secret_Bound
from .state import _Snapshot
from .state import _State
from .state import _is_composing
from .state import _context_action
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

        member = klass.__dict__.get(name)

        if member is not None:
            return member

    return None


def _arrest_read_hook(host_type: type, installed: Any = _MISSING) -> Callable[[object, str], Any]:
    """Keep the Host getter, while a Rip-trained Agent's reads stay gated."""

    original = object.__getattribute__ if installed is _MISSING else installed

    for owner in (() if installed is not _MISSING else type.__getattribute__(host_type, "__mro__")):
        member = type.__getattribute__(owner, "__dict__").get(
                "__getattribute__", _MISSING
                )
        if member is _MISSING:
            continue
        if (
                isinstance(member, FunctionType)
                and member.__dict__.get("_TOPKIT_ARREST_READ")
                ):
            continue
        original = member
        break

    native = (
            original is object.__getattribute__
            or original is type.__getattribute__
            or isinstance(original, FunctionType)
            )
    arrests = _safehouse
    lookup_entry = dict.get
    identity = id
    kind = type
    string_type = str
    plain_str = str.__str__
    lookup = getattr
    require = _require_available

    def Read(agent: object, name: str) -> Any:
        # Normalize a str subclass before the custody exception check; its
        # __eq__ or __ne__ cannot fake the Python identity seat.
        ordinary = plain_str(name) if kind(name) is not string_type else name
        arrest = lookup_entry(arrests, identity(agent))

        if arrest is not None and arrest.agent is agent and arrest.runs:
            if ordinary == "__class__":
                return kind(agent)  # actual runtime type, never the Host getter
            require(agent, f"read {ordinary!r}")

        if native:
            value = original(agent, name)
        else:
            getter = lookup(kind(original), "__get__", None)
            bound = getter(original, agent, kind(agent)) if getter else original
            value = bound(name)

        # A Host getter can catch its own failed Rip and return a value.
        # Recheck after it runs before that value escapes custody.
        arrest = lookup_entry(arrests, identity(agent))
        if arrest is not None and arrest.agent is agent and arrest.runs:
            if ordinary == "__class__":
                return kind(agent)
            require(agent, f"read {ordinary!r}")
        return value

    Read._TOPKIT_ARREST_READ = True
    return Read


def _arrest_write_hook(
        host_type: type,
        name: str,
        installed: Any = _MISSING,
        ) -> Callable[..., Any]:
    """Preserve the Host binding hook and gate it on saved Rip custody."""

    fallback = installed
    if fallback is _MISSING:
        for owner in type.__getattribute__(host_type, "__mro__"):
            members = type.__getattribute__(owner, "__dict__")
            if name in members:
                fallback = members[name]
                break

    native = (
            isinstance(fallback, FunctionType)
            or fallback is object.__setattr__
            or fallback is object.__delattr__
            or fallback is type.__setattr__
            or fallback is type.__delattr__
            )
    arrests = _safehouse
    lookup_entry = dict.get
    identity = id
    require = _require_available
    kind = type
    lookup = getattr

    def Write(agent: object, target: str, *values: Any) -> Any:
        arrest = lookup_entry(arrests, identity(agent))
        if arrest is not None and arrest.agent is agent and arrest.runs:
            require(agent, f"{name} binding")

        if native:
            result = fallback(agent, target, *values)
        else:
            getter = lookup(kind(fallback), "__get__", None)
            bound = getter(fallback, agent, kind(agent)) if getter else fallback
            result = bound(target, *values)

        arrest = lookup_entry(arrests, identity(agent))
        if arrest is not None and arrest.agent is agent and arrest.runs:
            require(agent, f"{name} binding")
        return result

    Write._TOPKIT_ARREST_WRITE = True
    return Write


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


def _refuse_host_truth(
        target: object,
        ) -> None:
    """Refuse custom host truth without evaluating it or changing the Target."""

    host = type(target)

    # Read Python's type data directly: custom metaclass lookup must not
    # hide a real protocol declaration or run while eligibility is checked.
    for klass in type.__dict__["__mro__"].__get__(host):
        namespace = type.__dict__["__dict__"].__get__(klass)

        if "__bool__" not in namespace:
            continue

        if (
                namespace.get("_TOPKIT_HOST_TYPE") is not None
                and namespace["__bool__"] is _agent_bool
                ):
            continue   # the kit's hook on a synthesized runtime layer

        raise TagCompositionError(
                f"{type.__dict__['__name__'].__get__(host)} defines __bool__;"
                " an Agent's truth is"
                " reserved for its visible Postconditions"
                )


def _hooks_for(
        host_type: type,
        has_flags: bool,
        ) -> dict[str, Any]:
    """The kit's special methods for one host.

    Ordinary object Agents use contract truth from the first Tagging.
    Their hosts may supply ``__len__``, but custom ``__bool__`` is refused
    before Tagging. Tags use their metaclass's own-contract truth.
    """

    hooks: dict[str, Any] = {
            "__getattr__": _agent_getattr,
            "__del__": _agent_del,
            "_TOPKIT_HOST_TYPE": host_type,
            "_TOPKIT_HOST_GETATTR": _host_member(host_type, "__getattr__"),
            }

    if not issubclass(host_type, type):
        hooks["__bool__"] = _agent_bool

    for name in ("__enter__", "__exit__", "__aenter__", "__aexit__"):
        original = _host_member(host_type, name)
        if original is None:
            continue
        def Call(agent, *args, _original=original, **kwargs):
            getter = getattr(type(_original), "__get__", None)
            method = getter(_original, agent, type(agent)) if getter else _original
            return method(*args, **kwargs)
        hooks[name] = _context_action(name, Call)

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
    """Miss path only: Tag views, then a Post verdict, then host fallback."""

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

        if state.postconditions:
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

    if not _is_composing(state):
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
    """Reserved Agent contract truth; a plain object
    constructed from an Agent's runtime type keeps ordinary host truth."""

    state = _state_of(agent)

    if state is None:
        return _host_truth(agent)

    if _safehouse and _arrest_of(agent) is not None:
        return False

    if not state.postconditions:
        return True   # nothing promised

    return _holds(agent, state)


def _host_truth(
        agent: object,
        ) -> bool:
    """An untagged runtime object keeps its host's native truth.

    The actual MRO already contains the underlying host classes. Skip the
    synthesized layers without moving an older host ahead of an override.
    """

    host = type(agent)

    for klass in type.__dict__["__mro__"].__get__(host):
        namespace = type.__dict__["__dict__"].__get__(klass)

        if namespace.get("_TOPKIT_HOST_TYPE") is not None:
            continue

        if "__len__" not in namespace:
            continue

        length = namespace["__len__"]

        # Python's descriptor slot reads __get__ from the real type data,
        # independently of a metaclass's attribute lookup or class equality.
        for descriptor_type in type.__dict__["__mro__"].__get__(type(length)):
            descriptor_namespace = type.__dict__["__dict__"].__get__(descriptor_type)

            if "__get__" in descriptor_namespace:
                call = descriptor_namespace["__get__"](length, agent, host)
                break

        else:
            call = length

        result = operator.index(call())

        if result < 0:
            raise ValueError("__len__() should return >= 0")

        if result > sys.maxsize:
            raise OverflowError("cannot fit 'int' into an index-sized integer")

        return result != 0

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
        cleanup_context: Callable[[], Any] = _unobserved_cleanup,
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

    with cleanup_context():
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


class _View_Call:
    """A captured callable follows its selected Tag's current application."""

    __slots__ = ("_view", "_name", "_secret")

    def __init__(call, view: "_Tag_View", name: str, secret: bool) -> None:
        call._view = view
        call._name = str.__str__(name)
        call._secret = secret

    def _authorize(call, agent: object, act: str) -> None:
        if _safehouse:
            _require_available(agent, act)
        _agent, snapshot = call._view._current()
        if call._name in snapshot.operations and call._name in snapshot.actions:
            origin = snapshot.operations[call._name][0]
            state_module._require_membership(agent, origin, call._name, "Operation")
        if (call._secret or call._name in snapshot.secrets) and not _is_composing(_state_of(agent)):
            raise AttributeError(
                    f"{call._name!r} was captured as a Secret member;"
                    " it is reachable only through composition"
                    )

    def __call__(call, *args: Any, **kwargs: Any) -> Any:
        agent, snapshot = call._view._current()
        call._authorize(agent, "Tag-view call")
        name = call._name
        if name in snapshot.secrets and not _is_composing(_state_of(agent)):
            raise AttributeError(f"{name!r} is a Secret member")
        if name in snapshot.operations:
            origin = snapshot.operations[name][0]
            if _safehouse:
                _require_available(origin, "Operation")
            operation = getattr(origin, name)
            if name in snapshot.actions:
                result = operation(agent, *args, **kwargs)
            else:
                result = operation(*args, **kwargs)
            result = _guard_lazy_result(result, origin, "Operation", _require_available)
        else:
            member = call._view._read(name, handles=False)
            result = member(*args, **kwargs)
        result = _guard_lazy_result(result, agent, "Tag-view call", call._authorize)
        call._authorize(agent, "Tag-view call")
        return result

    def __eq__(call, other: object) -> Any:
        if type(other) is not _View_Call:
            return NotImplemented
        return (call._view._tag is other._view._tag
                and call._view._identity is other._view._identity
                and call._name == other._name)

    def __hash__(call) -> int:
        return hash((id(call._view._tag), id(call._view._identity), call._name))

    def __repr__(call) -> str:
        tag = type.__dict__["__name__"].__get__(call._view._tag)
        return f"<Tag-view call {tag}.{call._name}>"

    def _binding(call) -> tuple[object, Any]:
        agent, snapshot = call._view._current()
        if call._name in snapshot.actions:
            return agent, snapshot.actions[call._name]
        if call._name in snapshot.operations:
            origin = snapshot.operations[call._name][0]
            current = getattr(origin, call._name)
            return current.__self__, current.__func__
        raise AttributeError(f"{call._name!r} is no longer a callable Contribution")

    @property
    def __self__(call) -> object:
        return call._binding()[0]

    @property
    def __func__(call) -> Any:
        return call._binding()[1]

    @property
    def __wrapped__(call) -> Any:
        receiver, function = call._binding()
        return MethodType(function, receiver)

    @property
    def __name__(call) -> str:
        try:
            return call.__func__.__name__
        except Exception:
            return call._name

    @property
    def __doc__(call) -> str | None:
        return getattr(call.__func__, "__doc__", None)


class _Tag_View:
    """A soft reference to the Overlay at this Tag's current application."""

    __slots__ = ("_reference", "_tag", "_identity")

    def __init__(view, agent: object, tag: type) -> None:
        state = _state_of(agent)
        if state.view_identity is None:
            state.view_identity = object()
        object.__setattr__(view, "_reference", ref(agent))
        object.__setattr__(view, "_tag", tag)
        object.__setattr__(view, "_identity", state.view_identity)

    def _current(view) -> tuple[object, _Snapshot]:
        agent = view._reference()
        if agent is None:
            raise ReferenceError("the Agent of this Tag view no longer exists")
        if _safehouse:
            _require_available(agent, "Tag-view access")
        state = _state_of(agent)
        if state is None or view._tag not in state.active:
            raise TagResolutionError(f"{view._tag.__name__} is not active on this Agent")
        return agent, state.snapshots[view._tag]

    def _read(view, name: str, *, handles: bool = True) -> Any:
        agent, snapshot = view._current()
        if name in snapshot.deleted:
            raise AttributeError(f"{view._tag.__name__} deleted {name!r}")
        if name in snapshot.secrets and not _is_composing(_state_of(agent)):
            raise AttributeError(f"{name!r} is a Secret member of {view._tag.__name__}")
        if name in snapshot.actions:
            if handles:
                result = _View_Call(view, name, name in snapshot.secrets)
            elif name in snapshot.secrets:
                result = _Secret_Bound(snapshot.actions[name], agent, name)
            else:
                result = _Composing_Bound(snapshot.actions[name], agent)
        elif name in snapshot.records:
            result = snapshot.records[name]
        elif name in snapshot.reports:
            origin = snapshot.reports[name][0]
            result = getattr(origin, name)
        elif name in snapshot.operations:
            result = _View_Call(view, name, name in snapshot.secrets)
        else:
            raise AttributeError(f"{view._tag.__name__} view has no member {name!r}")
        view._current()
        return result

    def __getattr__(view, name: str) -> Any:
        return view._read(name)

    def __setattr__(view, name: str, value: Any) -> None:
        raise AttributeError("a Tag view is read-only")

    def __rmatmul__(view, name: object) -> bool:
        if not issubclass(type(name), str):
            return NotImplemented
        agent, snapshot = view._current()
        name = str.__str__(name)
        if name in snapshot.deleted:
            result = False
        elif name in snapshot.secrets and not _is_composing(_state_of(agent)):
            result = False
        elif name in snapshot.reports:
            origin = snapshot.reports[name][0]
            result = getattr_static(origin, name, _MISSING) is not _MISSING
        elif name in snapshot.operations:
            origin = snapshot.operations[name][0]
            result = getattr_static(origin, name, _MISSING) is not _MISSING
        else:
            result = name in snapshot.actions or name in snapshot.records
        view._current()
        return result

    def __repr__(view) -> str:
        agent = view._reference()
        owner = _name_of(agent) if agent is not None else "<gone>"
        return f"<{view._tag.__name__} view of {owner}>"


def _view_of(
        agent: object,
        tag: type,
        state: _State | None = None,
        ) -> _Tag_View:
    if _safehouse:
        _require_available(agent, "Tag-view access")
    if state is None:
        state = _state_of(agent)

    if state is None or tag not in state.active:
        raise TagResolutionError(
                f"{tag.__name__} is not active on this Agent"
                )

    return _Tag_View(
            agent,
            tag,
            )
