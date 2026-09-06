"""Agent state and the runtime type.

An Agent keeps one ``_TAGKIT_STATE`` in its instance dictionary. Actions
live in that dictionary as bound callables, Records as plain values, so
ordinary attribute access costs what it costs on a plain object. The
runtime type is neutral (host first, then the ``Tagged`` marker) and only
carries what Python requires on a type: special-method Actions and the
descriptors that gate deleted, secret, and published names.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from types import MethodType
from typing import Any
from typing import Callable
from typing import Iterator
from weakref import WeakValueDictionary
import weakref

from .declarations import STATE
from .declarations import _MISSING
from .declarations import _is_dunder
from .declarations import _is_flag
from .errors import TagCompositionError

Function = Callable[..., Any]
Check = Callable[..., Any]


# ------------------------------------------------------------------
# State
# ------------------------------------------------------------------


@dataclass
class _Snapshot:
    actions: dict[str, Function]
    records: dict[str, Any]
    reports: dict[str, tuple[type, Any]]
    operations: dict[str, tuple[type, Function]]
    deleted: frozenset[str]
    secrets: frozenset[str]


@dataclass
class _State:
    host_type: type
    pinned: type | None = None   # the Tag itself, when the Agent is a Tag
    active: list[type] = field(default_factory=list)
    ever: set[type] = field(default_factory=set)
    actions: dict[str, Function] = field(default_factory=dict)
    action_origins: dict[str, type] = field(default_factory=dict)
    records: dict[str, type] = field(default_factory=dict)
    preconditions: dict[str, Check] = field(default_factory=dict)
    postconditions: dict[str, Check] = field(default_factory=dict)
    reports: dict[str, tuple[type, Any]] = field(default_factory=dict)
    operations: dict[str, tuple[type, Function]] = field(default_factory=dict)
    published: set[str] = field(default_factory=set)
    secrets: set[str] = field(default_factory=set)
    deleted: set[str] = field(default_factory=set)
    snapshots: dict[type, _Snapshot] = field(default_factory=dict)
    rips: dict[type, tuple[Function, ...]] = field(default_factory=dict)
    composing: int = 0
    checking: bool = False

    def Copy(
            state,
            ) -> "_State":
        return _State(
                host_type=state.host_type,
                pinned=state.pinned,
                active=list(state.active),
                ever=set(state.ever),
                actions=dict(state.actions),
                action_origins=dict(state.action_origins),
                records=dict(state.records),
                preconditions=dict(state.preconditions),
                postconditions=dict(state.postconditions),
                reports=dict(state.reports),
                operations=dict(state.operations),
                published=set(state.published),
                secrets=set(state.secrets),
                deleted=set(state.deleted),
                snapshots=dict(state.snapshots),
                rips=dict(state.rips),
                composing=state.composing,
                checking=state.checking,
                )


class _Class_Namespace:
    """The namespace of a Tag used as a Target (a pinned Tag).

    A class dictionary is read through a proxy and written through the
    class. This adapter gives the kernel the few dictionary operations it
    uses, so the tagging sequence is one code path for objects and Tags.
    """

    __slots__ = ("_owner",)

    def __init__(
            namespace,
            owner: type,
            ) -> None:
        namespace._owner = owner

    def get(
            namespace,
            name: str,
            default: Any = None,
            ) -> Any:
        return namespace._owner.__dict__.get(
                name,
                default,
                )

    def __getitem__(
            namespace,
            name: str,
            ) -> Any:
        return namespace._owner.__dict__[name]

    def __setitem__(
            namespace,
            name: str,
            value: Any,
            ) -> None:
        setattr(
                namespace._owner,
                name,
                value,
                )

    def __contains__(
            namespace,
            name: object,
            ) -> bool:
        return name in namespace._owner.__dict__

    def pop(
            namespace,
            name: str,
            default: Any = _MISSING,
            ) -> Any:
        value = namespace._owner.__dict__.get(
                name,
                _MISSING,
                )

        if value is _MISSING:
            if default is _MISSING:
                raise KeyError(name)

            return default

        delattr(
                namespace._owner,
                name,
                )

        return value

    def keys(
            namespace,
            ) -> Any:
        return namespace._owner.__dict__.keys()

    def items(
            namespace,
            ) -> Any:
        return namespace._owner.__dict__.items()

    def __iter__(
            namespace,
            ) -> Iterator[str]:
        return iter(namespace._owner.__dict__)

    def __len__(
            namespace,
            ) -> int:
        return len(namespace._owner.__dict__)


def _namespace_of(
        agent: object,
        ) -> Any:
    """The Agent's writable namespace: its dictionary, or the adapter over
    a Tag's class dictionary; None when it has neither."""

    try:
        namespace = object.__getattribute__(
                agent,
                "__dict__",
                )
    except AttributeError:
        return None

    if isinstance(namespace, dict):
        return namespace

    if isinstance(agent, type):
        return _Class_Namespace(agent)

    return None


def _restore_namespace(
        agent: object,
        entry: dict[str, Any],
        ) -> None:
    """Put the namespace back exactly as it was at entry."""

    namespace = _namespace_of(agent)

    if namespace is None:
        return

    if isinstance(namespace, dict):
        namespace.clear()
        namespace.update(entry)
        return

    for name in list(namespace.keys()):
        if name not in entry:
            namespace.pop(name, None)

    for name, value in entry.items():
        if namespace.get(name, _MISSING) is not value:
            namespace[name] = value


def _name_of(
        agent: object,
        ) -> str:
    """How an Agent is called in messages: a Tag by its own name, an
    object by its type's."""

    if isinstance(agent, type):
        return agent.__name__

    return type(agent).__name__


def _state_of(
        agent: object,
        ) -> _State | None:
    """The Agent's state, or None. Read straight from the dictionary (or a
    Tag's dictionary proxy): this is on the path of ``agent in Tag``."""

    try:
        return object.__getattribute__(
                agent,
                "__dict__",
                ).get(STATE)
    except AttributeError:
        return None


def _state_for(
        agent: object,
        ) -> _State:
    """The Agent's state, attached on first use."""

    namespace = _namespace_of(agent)

    if namespace is None:
        raise TagCompositionError(
                f"{type(agent).__name__} cannot carry TOP state"
                " (no instance dictionary)"
                )

    state = namespace.get(STATE)

    if state is None:
        state = _State(
                host_type=type(agent),
                pinned=agent if isinstance(agent, type) else None,
                )
        namespace[STATE] = state

    return state


def _set_state(
        agent: object,
        state: _State,
        ) -> None:
    _namespace_of(agent)[STATE] = state


# ------------------------------------------------------------------
# Bound Actions
# ------------------------------------------------------------------


class _Bound:
    """An Action bound to one Agent, stored in the Agent's dictionary.

    Holds the Agent weakly so the Field's weak references stay honest.
    """

    __slots__ = (
            "_function",
            "_reference",
            )

    def __init__(
            bound,
            function: Function,
            agent: object,
            ) -> None:
        bound._function = function
        bound._reference = weakref.ref(agent)

    def __call__(
            bound,
            *args: Any,
            **kwargs: Any,
            ) -> Any:
        agent = bound._reference()

        if agent is None:
            raise ReferenceError("the Agent of this Action no longer exists")

        return bound._function(
                agent,
                *args,
                **kwargs,
                )

    @property
    def __name__(
            bound,
            ) -> str:
        return bound._function.__name__

    @property
    def __doc__(
            bound,
            ) -> str | None:
        return bound._function.__doc__

    @property
    def __func__(
            bound,
            ) -> Function:
        return bound._function

    def __repr__(
            bound,
            ) -> str:
        agent = bound._reference()
        owner = _name_of(agent) if agent is not None else "<gone>"

        return f"<Action {bound._function.__name__} of {owner}>"


class _Pinned_Operation:
    """An Action a Pin landed on a Tag: an Operation of that Tag.

    Read from the pinned Tag or from any of its Shapes, it binds to the
    Tag it was read from, as a classmethod does, so a Shape inherits it
    the way it inherits every Tag-scope member.
    """

    __slots__ = ("_function",)

    def __init__(
            operation,
            function: Function,
            ) -> None:
        operation._function = function

    def __get__(
            operation,
            instance: object,
            owner: type | None = None,
            ) -> Any:
        if owner is None:
            owner = type(instance)

        return MethodType(
                operation._function,
                owner,
                )

    @property
    def __func__(
            operation,
            ) -> Function:
        return operation._function

    def __repr__(
            operation,
            ) -> str:
        return f"<pinned Operation {operation._function.__name__}>"


class _Composing_Bound(_Bound):
    """A bound Action that opens the composition door while it runs, so
    @Secret members resolve inside it."""

    __slots__ = ()

    def __call__(
            bound,
            *args: Any,
            **kwargs: Any,
            ) -> Any:
        agent = bound._reference()

        if agent is None:
            raise ReferenceError("the Agent of this Action no longer exists")

        state = _state_of(agent)
        state.composing += 1

        try:
            return bound._function(
                    agent,
                    *args,
                    **kwargs,
                    )
        finally:
            state.composing -= 1


def _bind_to(
        agent: object,
        state: _State,
        name: str,
        ) -> None:
    """Store the Agent's visible Action ``name`` in its dictionary."""

    function = state.actions[name]

    if state.pinned is not None:
        bound: Any = _Pinned_Operation(function)
    elif state.secrets:
        bound = _Composing_Bound(function, agent)
    else:
        bound = _Bound(function, agent)

    _namespace_of(agent)[name] = bound


def _rebind_all(
        agent: object,
        state: _State,
        ) -> None:
    for name in state.actions:
        if not _is_dunder(name):
            _bind_to(
                    agent,
                    state,
                    name,
                    )


# ------------------------------------------------------------------
# Descriptors installed on the runtime type
# ------------------------------------------------------------------


class _Deleted:
    """A name a Tag deleted. Reads fail until something stores it again."""

    __slots__ = ("name",)

    def __init__(
            gate,
            name: str,
            ) -> None:
        gate.name = name

    def __get__(
            gate,
            agent: object,
            owner: type | None = None,
            ) -> Any:
        if agent is None:
            return gate

        value = _namespace_of(agent).get(
                gate.name,
                _MISSING,
                )

        if value is _MISSING:
            raise AttributeError(
                    f"{type(agent).__name__} has no visible member"
                    f" {gate.name!r} (deleted by a Tag)"
                    )

        return value

    def __set__(
            gate,
            agent: object,
            value: Any,
            ) -> None:
        _namespace_of(agent)[gate.name] = value

    def __delete__(
            gate,
            agent: object,
            ) -> None:
        _namespace_of(agent).pop(
                gate.name,
                None,
                )


class _Secret_Gate:
    """A @Secret name. Resolves only while the Agent is composing."""

    __slots__ = ("name",)

    def __init__(
            gate,
            name: str,
            ) -> None:
        gate.name = name

    def _open(
            gate,
            agent: object,
            ) -> dict[str, Any]:
        namespace = _namespace_of(agent)

        if namespace[STATE].composing == 0:
            raise AttributeError(
                    f"{gate.name!r} is a secret member of"
                    f" {type(agent).__name__}; it is reachable only from"
                    " its Tags' own Actions and protocols"
                    )

        return namespace

    def __get__(
            gate,
            agent: object,
            owner: type | None = None,
            ) -> Any:
        if agent is None:
            return gate

        namespace = gate._open(agent)
        value = namespace.get(
                gate.name,
                _MISSING,
                )

        if value is _MISSING:
            raise AttributeError(
                    f"{type(agent).__name__} has no visible member"
                    f" {gate.name!r}"
                    )

        return value

    def __set__(
            gate,
            agent: object,
            value: Any,
            ) -> None:
        gate._open(agent)[gate.name] = value

    def __delete__(
            gate,
            agent: object,
            ) -> None:
        gate._open(agent).pop(
                gate.name,
                None,
                )


class _Published:
    """A published Report: reads the Tag-scope value, read-only on the Agent."""

    __slots__ = ("name",)

    def __init__(
            gate,
            name: str,
            ) -> None:
        gate.name = name

    def __get__(
            gate,
            agent: object,
            owner: type | None = None,
            ) -> Any:
        if agent is None:
            return gate

        state = _namespace_of(agent)[STATE]
        origin, _declared = state.reports[gate.name]

        return getattr(
                origin,
                gate.name,
                )

    def __set__(
            gate,
            agent: object,
            value: Any,
            ) -> None:
        raise AttributeError(
                f"{gate.name!r} is a published Report; it is read-only on"
                " the Agent and lives on the Tag"
                )


# ------------------------------------------------------------------
# Runtime types
# ------------------------------------------------------------------


class Tagged:
    """Marker base every Agent runtime type ends with."""

    __slots__ = ()


_type_cache: "WeakValueDictionary[tuple, type]" = WeakValueDictionary()


def _dunder_actions(
        state: _State,
        ) -> dict[str, Function]:
    return {
            name: function
            for name, function in state.actions.items()
            if _is_dunder(name)
            }


def _type_key_of(
        state: _State,
        ) -> tuple:
    return (
            state.host_type,
            frozenset(state.deleted),
            frozenset(state.secrets),
            frozenset(state.published),
            bool(state.postconditions),
            any(_is_flag(tag) for tag in state.active),
            tuple(
                    sorted(
                            (name, id(function))
                            for name, function in _dunder_actions(state).items()
                            )
                    ),
            )


def _runtime_type_for(
        state: _State,
        ) -> type:
    """The runtime type for a composition, shared across Agents that need
    the same type-level behaviour."""

    from .access import _hooks_for

    key = _type_key_of(state)
    shared = _type_cache.get(key)

    if shared is not None:
        return shared

    host_type = state.host_type
    dunders = _dunder_actions(state)
    deleted = key[1]
    secrets = key[2]
    published = key[3]
    has_posts = key[4]
    has_flags = key[5]

    namespace: dict[str, Any] = _hooks_for(
            host_type,
            has_posts,
            has_flags,
            )
    namespace.update(dunders)

    for name in deleted:
        namespace[name] = _Deleted(name)

    for name in secrets:
        namespace[name] = _Secret_Gate(name)

    for name in published:
        namespace[name] = _Published(name)

    if issubclass(host_type, Tagged):
        bases: tuple[type, ...] = (host_type,)
    else:
        bases = (
                host_type,
                Tagged,
                )

    try:
        runtime_type = type(
                host_type.__name__,
                bases,
                namespace,
                )
    except TypeError as error:
        raise TagCompositionError(
                f"{host_type.__name__} cannot be actualized as an Agent"
                ) from error

    runtime_type.__qualname__ = host_type.__qualname__
    runtime_type.__module__ = host_type.__module__
    _type_cache[key] = runtime_type

    return runtime_type
