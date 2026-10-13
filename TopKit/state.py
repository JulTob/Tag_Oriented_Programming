"""Agent state and the runtime type.

An Agent keeps one ``_TOPKIT_STATE`` in its instance dictionary. Actions
live in that dictionary as bound callables, Records as plain values, so
ordinary attribute access costs what it costs on a plain object. The
runtime type is neutral (host first, then the ``Tagged`` marker) and only
carries what Python requires on a type: special-method Actions and the
descriptors that gate deleted, secret, published, computed-condition,
and Constant names.
"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from dataclasses import field
from dataclasses import FrozenInstanceError
from functools import wraps
from inspect import signature
from types import FunctionType
from types import GetSetDescriptorType
from types import MemberDescriptorType
from types import MethodType
from typing import Any
from typing import Callable
from typing import Iterator
from weakref import WeakValueDictionary
import weakref

from .declarations import STATE
from .declarations import _MISSING
from .declarations import _Words
from .declarations import _is_dunder
from .declarations import _is_flag
from .errors import TagCompositionError
from .memo import _namespace_snapshot

Function = Callable[..., Any]
Check = Callable[..., Any]


# ------------------------------------------------------------------
# State
# ------------------------------------------------------------------


@dataclass(slots=True)
class _Snapshot:
    actions: dict[str, Function]
    records: dict[str, Any]
    reports: dict[str, tuple[type, Any]]
    operations: dict[str, tuple[type, Function]]
    deleted: frozenset[str]
    secrets: frozenset[str]


@dataclass(slots=True)
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
    restored: frozenset[str] = frozenset()   # deleted, then stored again; shared until used
    snapshots: dict[type, _Snapshot] = field(default_factory=dict)
    rips: dict[type, tuple[tuple[str, Function], ...]] = field(default_factory=dict)
    secret_values: dict[str, Any] = field(default_factory=dict)   # a pinned Tag's @Secret members
    originals: dict[str, Any] = field(default_factory=dict)       # what a Pin patched, as declared
    constants: dict[str, tuple[type, str, Any]] = field(default_factory=dict)  # origin, kind, declaration
    tools: dict[str, tuple[type, Any]] = field(default_factory=dict)   # origin, kind: a Tool slot admits only its kind
    composing: int = 0
    checking: bool = False
    words: _Words | None = None   # what its Flags answer to; None after its Tags change

    def Restore(
            state,
            entry: "_State",
            ) -> None:
        """Take back everything ``entry`` held, in place. The counters of
        open doors and checks stay: whoever opened them before the call
        that is rolled back closes them on this same object."""

        for name in state.__slots__:
            if name not in ("composing", "checking"):
                setattr(
                        state,
                        name,
                        getattr(entry, name),
                        )

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
                restored=state.restored,
                snapshots=dict(state.snapshots),
                rips=dict(state.rips),
                secret_values=dict(state.secret_values),
                originals=dict(state.originals),
                constants=dict(state.constants),
                tools=dict(state.tools),
                composing=state.composing,
                checking=state.checking,
                words=state.words,
                )


class _Async_Door:
    """One async Action's execution-local authority to read Secrets."""

    __slots__ = (
            "active",
            "state",
            )

    def __init__(
            door,
            state: _State,
            ) -> None:
        door.active = True
        door.state = state

    def Close(
            door,
            ) -> None:
        door.active = False
        door.state = None


_async_doors: ContextVar[tuple[_Async_Door, ...]] = ContextVar(
        "TopKit_async_composition_doors",
        default=(),
        )


def _is_composing(
        state: _State,
        ) -> bool:
    """Whether this execution, rather than merely this Agent, has a door."""

    if state.composing:
        return True

    doors = _async_doors.get()

    if not doors:
        return False

    return any(
            door.active
            and door.state is state
            for door in reversed(doors)
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
        type.__setattr__(
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

        type.__delattr__(
                namespace._owner,
                name,
                )

        return value

    def keys(
            namespace,
            ) -> Any:
        return namespace.copy().keys()

    def items(
            namespace,
            ) -> Any:
        return namespace.copy().items()

    def copy(namespace) -> dict[str, Any]:
        return _namespace_snapshot(namespace._owner)

    def __iter__(
            namespace,
            ) -> Iterator[str]:
        return iter(namespace.copy())

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

    if issubclass(type(namespace), dict):
        return namespace

    if issubclass(type(agent), type):
        return _Class_Namespace(agent)

    return None


def _real_namespace_of(
        agent: object,
        ) -> Any:
    """The physical instance dictionary, bypassing a shadowing property."""

    if issubclass(type(agent), type):
        return type.__dict__["__dict__"].__get__(agent)

    for owner in type.__getattribute__(type(agent), "__mro__"):
        member = type.__getattribute__(owner, "__dict__").get("__dict__")

        if issubclass(type(member), GetSetDescriptorType):
            return member.__get__(agent, type(agent))

    return None


@dataclass(slots=True)
class _Host_Bindings:
    """Physical Python bindings at initial preparation; never copies values."""

    host_type: type
    dictionary: Any
    namespace: dict[str, Any] | None
    contents: dict[str, Any]
    slots: tuple[tuple[Any, bool, Any], ...]


def _host_bindings_of(agent: object) -> _Host_Bindings:
    """Read native storage without invoking user properties or write hooks."""

    host_type = type(agent)
    dictionary = None
    namespace = None
    slots = []
    seen = set()

    if not issubclass(host_type, type):
        for owner in type.__getattribute__(host_type, "__mro__"):
            members = dict(type.__getattribute__(owner, "__dict__"))
            for name, member in members.items():
                if (
                        name == "__dict__"
                        and type(member) is GetSetDescriptorType
                        and dictionary is None
                        ):
                    dictionary = member
                    namespace = member.__get__(agent, host_type)
                elif (
                        # Python's declared slots, not arbitrary native
                        # extension fields that may be read-only.
                        "__slots__" in members
                        and type(member) is MemberDescriptorType
                        and member.__objclass__ is owner
                        and id(member) not in seen
                        ):
                    seen.add(id(member))
                    try:
                        value = member.__get__(agent, host_type)
                    except AttributeError:
                        slots.append((member, False, None))
                    else:
                        slots.append((member, True, value))

    return _Host_Bindings(
            host_type, dictionary, namespace,
            dict(namespace) if namespace is not None else {},
            tuple(slots),
            )


def _restore_host_bindings(agent: object, entry: _Host_Bindings) -> None:
    """Restore the class first, then dictionary identity and slot bindings."""

    if type(agent) is not entry.host_type:
        _set_runtime_type(agent, entry.host_type)

    if entry.namespace is not None:
        entry.dictionary.__set__(agent, entry.namespace)
        entry.namespace.clear()
        entry.namespace.update(entry.contents)

    for member, present, value in entry.slots:
        if present:
            member.__set__(agent, value)
        else:
            try:
                member.__delete__(agent)
            except AttributeError:
                pass


def _restore_namespace(
        agent: object,
        entry: dict[str, Any],
        ) -> None:
    """Put the namespace back exactly as it was at entry."""

    namespace = _namespace_of(agent)

    if namespace is None:
        return

    if issubclass(type(namespace), dict):
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

    if issubclass(type(agent), type):
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

    if not issubclass(type(agent), type) and namespace is not _real_namespace_of(agent):
        raise TagCompositionError(
                f"{type(agent).__name__} cannot carry TOP state"
                " (its __dict__ is not its instance storage)"
                )

    state = namespace.get(STATE)

    if state is None:
        host_type = type(agent)
        host_of_runtime = host_type.__dict__.get("_TOPKIT_HOST_TYPE")

        if host_of_runtime is not None and not issubclass(type(agent), type):
            # Built from an Agent's runtime type (dataclasses.replace,
            # type(self)(...)): until tagged, it is a plain host object.
            # Removing an inherited internal representation is a kernel
            # change. The host decides on its later first actualization,
            # after the Gate, rather than being asked twice.
            try:
                _set_runtime_type(agent, host_of_runtime)
            except Exception as error:
                raise TagCompositionError(
                        f"{host_type.__name__} cannot restore its host runtime type"
                        ) from error
            host_type = host_of_runtime

        state = _State(
                host_type=host_type,
                pinned=agent if issubclass(type(agent), type) else None,
                )
        namespace[STATE] = state

        retained = _namespace_of(agent)

        if retained is None or retained.get(STATE) is not state:
            namespace.pop(STATE, None)
            raise TagCompositionError(
                    f"{host_type.__name__} cannot retain TOP state"
                    )

    return state


def _set_state(
        agent: object,
        state: _State,
        ) -> None:
    _namespace_of(agent)[STATE] = state


def _actualize_runtime_type(
        agent: object,
        runtime_type: type,
        state: _State,
        ) -> None:
    """Let a host accept its first Agent type, then verify the result."""

    host_type = type(agent)

    try:
        frozen_type = None
        for owner in host_type.__mro__:
            setter = owner.__dict__.get("__setattr__", _MISSING)
            if setter is _MISSING:
                continue
            if not _frozen_dataclass_setter(owner, setter):
                break
            frozen_type = owner

        if frozen_type is not None:
            # The generated wrappers protect host bindings, but reject
            # every write on the exact dataclass, including our internal
            # class change. Skip only those wrappers: a base's real host
            # write hook still decides whether to accept actualization.
            super(frozen_type, agent).__setattr__("__class__", runtime_type)
        else:
            agent.__class__ = runtime_type
    except Exception as error:
        raise TagCompositionError(
                f"{host_type.__name__} cannot be actualized in place"
                ) from error

    if type(agent) is not runtime_type:
        raise TagCompositionError(
                f"{host_type.__name__} did not accept the Agent runtime type"
                )

    if _state_of(agent) is not state:
        raise TagCompositionError(
                f"{host_type.__name__} did not retain TOP state during actualization"
                )


def _frozen_dataclass_setter(
        host_type: type,
        setter: Any,
        ) -> bool:
    """Recognize the standard frozen-dataclass wrapper conservatively."""

    parameters = host_type.__dict__.get("__dataclass_params__")

    if (
            parameters is None
            or not parameters.frozen
            or type(setter) is not FunctionType
            or setter.__code__.co_filename != "<string>"
            or setter.__code__.co_freevars not in (
                    ("FrozenInstanceError", "cls"),
                    ("FrozenInstanceError", "__class__"),
                    )
            ):
        return False

    frozen_error, declared_type = (
            cell.cell_contents
            for cell in setter.__closure__
            )
    if frozen_error is not FrozenInstanceError:
        return False

    if declared_type is host_type:
        return True

    # Before Python 3.14, slots=True recreates the dataclass while the
    # generated frozen setter still captures its original class. Both
    # classes retain the exact same declaration and dataclass metadata.
    if not issubclass(type(declared_type), type):
        return False

    original = type.__getattribute__(declared_type, "__dict__")
    current = type.__getattribute__(host_type, "__dict__")
    return (
            "__slots__" in current
            and "__slots__" not in original
            and original.get("__setattr__") is setter
            and original.get("__dataclass_params__") is parameters
            and original.get("__dataclass_fields__") is current.get("__dataclass_fields__")
            and declared_type.__name__ == host_type.__name__
            and declared_type.__qualname__ == host_type.__qualname__
            and declared_type.__bases__ == host_type.__bases__
            )


def _set_runtime_type(agent: object, runtime_type: type) -> None:
    """Install an internal type without routing through host write hooks."""

    if issubclass(type(agent), type):
        type.__setattr__(agent, "__class__", runtime_type)
    else:
        object.__setattr__(agent, "__class__", runtime_type)

    if type(agent) is not runtime_type:
        raise TagCompositionError("the host did not accept the Agent runtime type")


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


class _Originals:
    """The pinned Tag's declarations as they were before its Pins patched
    them, handed to a Pin's @Rip teardown as its second seat, so
    un-patching is one deliberate line: ``tag.Control = original.Control``.
    """

    __slots__ = ("_declared",)

    def __init__(
            original,
            declared: dict[str, Any],
            ) -> None:
        object.__setattr__(original, "_declared", dict(declared))

    def __getattr__(
            original,
            name: str,
            ) -> Any:
        try:
            return original._declared[name]
        except KeyError:
            raise AttributeError(
                    f"no original declaration named {name!r} was patched"
                    ) from None

    def __setattr__(
            original,
            name: str,
            value: Any,
            ) -> None:
        raise AttributeError("the originals are a record; they are read-only")

    def __contains__(
            original,
            name: object,
            ) -> bool:
        return name in original._declared

    def __iter__(
            original,
            ) -> Iterator[str]:
        return iter(original._declared)

    def __repr__(
            original,
            ) -> str:
        return f"<originals of {', '.join(original._declared) or 'nothing'}>"


class _Pinned_Bound:
    """A public Operation handle with its original callable and receiver.

    Signature inspection is deferred until requested: optional callable
    introspection must not prevent reading or calling an Operation.
    """

    __slots__ = ("_function", "_owner", "_state", "_name", "_doc")

    def __init__(
            bound,
            function: Function,
            owner: type,
            state: "_State",
            name: str,
            doc: str | None,
            ) -> None:
        bound._function = function
        bound._owner = owner
        bound._state = state
        bound._name = name
        bound._doc = doc

    def __call__(bound, *args: Any, **kwargs: Any) -> Any:
        state = bound._state
        state.composing += 1

        try:
            return bound._function(bound._owner, *args, **kwargs)
        finally:
            state.composing -= 1

    def __eq__(bound, other: object) -> Any:
        # Use Python's function equality and receiver identity without
        # consulting the receiving Tag's equality or hash hooks.
        if isinstance(other, _Pinned_Bound):
            other = MethodType(other._function, other._owner)

        return MethodType(bound._function, bound._owner).__eq__(other)

    def __hash__(bound) -> int:
        return hash(MethodType(bound._function, bound._owner))

    def __repr__(bound) -> str:
        return f"<pinned Operation {bound._name} of {_name_of(bound._owner)}>"

    @property
    def __self__(bound) -> type:
        return bound._owner

    @property
    def __func__(bound) -> Function:
        return bound._function

    @property
    def __signature__(bound) -> Any:
        return signature(MethodType(bound._function, bound._owner))

    @property
    def __name__(bound) -> str:
        return bound._name

    @property
    def __doc__(bound) -> str | None:
        return bound._doc


class _Composing_Pinned_Operation(_Pinned_Operation):
    """A pinned Operation that opens the pinned Tag's composition door
    while it runs, so the Pin's @Secret members resolve inside it."""

    __slots__ = ("_state", "_name")

    def __init__(
            operation,
            function: Function,
            state: "_State",
            name: str,
            ) -> None:
        super().__init__(function)
        operation._state = state
        operation._name = name

    def __get__(
            operation,
            instance: object,
            owner: type | None = None,
            ) -> Any:
        if owner is None:
            owner = type(instance)

        function = operation._function
        try:
            name = function.__name__
            if not issubclass(type(name), str):
                name = operation._name
        except Exception:
            name = operation._name

        try:
            doc = function.__doc__
        except Exception:
            doc = None

        return _Pinned_Bound(function, owner, operation._state, name, doc)


class _Secret_Pinned_Operation(_Composing_Pinned_Operation):
    """A captured Pin-private Operation cannot open its own access door."""

    __slots__ = ()

    def __get__(
            operation,
            instance: object,
            owner: type | None = None,
            ) -> Any:
        composing = super().__get__(instance, owner)
        state = operation._state
        name = operation._name

        def Secret(
                *args: Any,
                **kwargs: Any,
                ) -> Any:
            if not _is_composing(state):
                raise AttributeError(
                        f"{name!r} is a secret pinned Operation; it is"
                        " reachable only from its Tag's composition"
                        )

            return composing(*args, **kwargs)

        Secret.__name__ = composing.__name__
        Secret.__doc__ = composing.__doc__

        return Secret


class _Composing_Bound(_Bound):
    """A bound Action that opens the composition door while it runs, so
    @Secret members resolve inside it."""

    __slots__ = ()
    __doc__ = _Bound.__dict__["__doc__"]   # keep the bound Action's metadata

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


class _Secret_Bound(_Composing_Bound):
    """A bound Secret Action needs an open door before it can open its own.

    Capturing the callable from inside composition grants no later access.
    Its captured Secret boundary stays even if a newer Layer is public.
    """

    __slots__ = ("_name",)
    __doc__ = _Bound.__dict__["__doc__"]

    def __init__(
            bound,
            function: Function,
            agent: object,
            name: str,
            ) -> None:
        super().__init__(function, agent)
        bound._name = name

    def __call__(
            bound,
            *args: Any,
            **kwargs: Any,
            ) -> Any:
        agent = bound._reference()

        if agent is None:
            raise ReferenceError("the Agent of this Action no longer exists")

        state = _state_of(agent)

        if state is None or not _is_composing(state):
            raise AttributeError(
                    f"{bound._name!r} is a secret Action; it is reachable"
                    " only from its Agent's composition"
                    )

        return super().__call__(*args, **kwargs)


def _bind_to(
        agent: object,
        state: _State,
        name: str,
        ) -> None:
    """Store the Agent's visible Action ``name`` in its dictionary."""

    function = state.actions[name]

    if state.pinned is not None:
        _bind_pinned(
                agent,
                state,
                name,
                function,
                )
        return

    if name in state.secrets:
        bound: _Bound = _Secret_Bound(function, agent, name)
    else:
        bound = _Composing_Bound(function, agent)

    _namespace_of(agent)[name] = bound


def _bind_pinned(
        tag: type,
        state: _State,
        name: str,
        function: Function,
        ) -> None:
    """A Pin's Action on a Tag: a secret one lives in the state and is
    read through the door; the rest live in the class dictionary."""

    if name in state.secrets:
        bound: _Pinned_Operation = _Secret_Pinned_Operation(function, state, name)
    else:
        bound = _Composing_Pinned_Operation(function, state, name)

    if name in state.secrets:
        _namespace_of(tag).pop(name, None)
        state.secret_values[name] = bound
    else:
        _namespace_of(tag)[name] = bound


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

        if not _is_composing(namespace[STATE]):
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


_require_membership: Callable[..., None] | None = None
# overlay's membership check for published members. overlay imports this
# module, so it hands the check over when it loads (see overlay.py).


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
        _require_membership(
                agent,
                origin,
                gate.name,
                "Report",
                )

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
    """Special-method Actions that live on the runtime type. ``__del__`` is
    not one of them: the finalizer runs the Agent's ``__del__`` Layers after
    its teardowns (STEP-SPEC-18)."""

    return {
            name: function
            for name, function in state.actions.items()
            if _is_dunder(name) and name != "__del__"
            }


_CONTEXT_ACTIONS = frozenset((
        "__enter__",
        "__exit__",
        "__aenter__",
        "__aexit__",
        ))
_ASYNC_CONTEXT_ACTIONS = frozenset((
        "__aenter__",
        "__aexit__",
        ))


def _context_action(
        name: str,
        function: Function,
        ) -> Function:
    """Run an Agent-authored context hook through its composition door.

    Async hooks keep the door open while their result is awaited.  The
    wrapper is made only after the runtime-type cache lookup, so the cache
    continues to identify a composition by the selected Action itself.
    """

    if name in _ASYNC_CONTEXT_ACTIONS:
        @wraps(function)
        async def Async_Context(
                agent: object,
                *args: Any,
                **kwargs: Any,
                ) -> Any:
            state = _state_of(agent)
            door = _Async_Door(state)
            _async_doors.set(
                    tuple(
                            active
                            for active in _async_doors.get()
                            if active.active
                            ) + (door,),
                    )

            try:
                return await function(
                        agent,
                        *args,
                        **kwargs,
                        )
            finally:
                door.Close()
                # A suspended coroutine can be closed in another Context,
                # or before another hook opened after it. Revoke its shared
                # capability first, then keep the current Context's other
                # live doors; a token reset assumes the original Context
                # and stack order. Captured contexts retain only an inert
                # door with no Agent state, pruned at their next entry.
                _async_doors.set(tuple(
                        active
                        for active in _async_doors.get()
                        if active.active
                        ))

        return Async_Context

    @wraps(function)
    def Context(
            agent: object,
            *args: Any,
            **kwargs: Any,
            ) -> Any:
        state = _state_of(agent)
        state.composing += 1

        try:
            return function(
                    agent,
                    *args,
                    **kwargs,
                    )
        finally:
            state.composing -= 1

    return Context


def _runtime_dunder_actions(
        selected: dict[str, Function],
        ) -> dict[str, Function]:
    """Prepare selected special Actions for one shared runtime type."""

    return {
            name: (
                    _context_action(name, function)
                    if name in _CONTEXT_ACTIONS
                    else function
                    )
            for name, function in selected.items()
            }


def _type_key_of(
        state: _State,
        ) -> tuple:
    return (
            state.host_type,
            frozenset((state.deleted | state.restored) - {"__del__"}),   # a restored name keeps its gate; __del__ has none
            frozenset(state.secrets),
            frozenset(state.published),
            frozenset(state.preconditions | state.postconditions),
            bool(state.postconditions),
            any(_is_flag(tag) for tag in state.active),
            tuple(
                    sorted(
                            (name, id(function))
                            for name, function in _dunder_actions(state).items()
                            )
                    ),
            frozenset(state.constants),
            frozenset(state.tools),
            )


def _runtime_type_for(
        state: _State,
        ) -> type:
    """The runtime type for a composition, shared across Agents that need
    the same type-level behaviour."""

    key = _type_key_of(state)
    shared = _type_cache.get(key)

    if shared is not None:
        return shared

    from .access import _hooks_for   # access imports this module
    from .contracts import _Condition_Gate
    from .presence import _presence_hook
    from .constants import _binding_write_hooks
    from .constants import _Constant_Gate

    host_type = state.host_type
    selected_dunders = _dunder_actions(state)
    dunders = _runtime_dunder_actions(
            selected_dunders,
            )
    deleted = key[1]
    secrets = key[2]
    published = key[3]
    conditions = key[4]
    has_posts = key[5]
    has_flags = key[6]

    hooks = _hooks_for(
            host_type,
            has_posts,
            has_flags,
            )
    namespace: dict[str, Any] = dict(hooks)
    namespace.update(dunders)

    if not issubclass(host_type, type):
        # A Tag's gates are answered on its miss path, never by a data
        # descriptor on its metaclass (which would also intercept the
        # class-attribute writes the kernel makes).
        for name in deleted:
            namespace[name] = _Deleted(name)

        for name in secrets:
            namespace[name] = _Secret_Gate(name)

        for name in published:
            namespace[name] = _Published(name)

        for name in conditions:
            namespace[name] = _Condition_Gate(
                    name,
                    namespace.get(name, _MISSING),
                    )

        if "__contains__" in hooks:
            namespace["__contains__"] = hooks["__contains__"]   # the Flag holds the seat

    namespace["__del__"] = hooks["__del__"]   # the finalizer, whatever gate names __del__
    _presence_hook(namespace, host_type)

    if not issubclass(host_type, type):
        for name in state.constants:
            namespace[name] = _Constant_Gate(name, namespace.get(name, _MISSING))

        from .tools import _Tool_Gate   # tools imports this module

        for name in state.tools:
            if _is_dunder(name):
                continue   # a protocol name keeps the language's own hook; the write hook guards it

            namespace[name] = _Tool_Gate(name, namespace.get(name, _MISSING))   # over a Constant or Secret gate, when both

    ungated_tools = any(_is_dunder(name) for name in state.tools)

    if conditions or state.constants or state.tools or issubclass(host_type, type):
        _binding_write_hooks(namespace, host_type, force=ungated_tools)

    if issubclass(host_type, Tagged):
        bases: tuple[type, ...] = (host_type,)
    else:
        bases = (
                host_type,
                Tagged,
                )

    requested_namespace = dict(namespace)

    try:
        runtime_type = type(
                host_type.__name__,
                bases,
                dict(requested_namespace),
                )
    except Exception as error:
        raise TagCompositionError(
                f"{host_type.__name__} cannot be actualized as an Agent"
                ) from error

    valid_runtime_type = False

    if issubclass(type(runtime_type), type):
        runtime_bases = type.__getattribute__(runtime_type, "__bases__")
        runtime_mro = type.__getattribute__(runtime_type, "__mro__")
        runtime_namespace = type.__getattribute__(runtime_type, "__dict__")
        valid_runtime_type = (
                runtime_type is not host_type
                and type.__getattribute__(runtime_type, "__name__") == host_type.__name__
                and len(runtime_bases) == len(bases)
                and all(
                        actual is requested
                        for actual, requested in zip(runtime_bases, bases)
                        )
                and any(ancestor is host_type for ancestor in runtime_mro)
                and any(ancestor is Tagged for ancestor in runtime_mro)
                and all(
                        runtime_namespace.get(name, _MISSING) is value
                        for name, value in requested_namespace.items()
                        )
                )

    if not valid_runtime_type:
        raise TagCompositionError(
                f"{host_type.__name__}'s metaclass did not construct"
                " TOP's requested Agent runtime type"
                )

    try:
        type.__setattr__(runtime_type, "__qualname__", host_type.__qualname__)
        type.__setattr__(runtime_type, "__module__", host_type.__module__)
    except Exception as error:
        raise TagCompositionError(
                f"{host_type.__name__} cannot be actualized as an Agent"
                ) from error

    _type_cache[key] = runtime_type

    return runtime_type
