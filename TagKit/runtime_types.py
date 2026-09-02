from __future__ import annotations

"""Agent state, Tag metaclass, views, and runtime actualization."""

from contextvars import ContextVar
from dataclasses import dataclass
from functools import partial
from functools import wraps
from inspect import cleandoc
from typing import Any
from typing import ClassVar
from typing import Iterator
from weakref import WeakValueDictionary

from .declarations import Action_Body
from .declarations import Operation_Body
from .declarations import Predicate
from .declarations import Record_Builder
from .declarations import Report
from .declarations import _MISSING
from .declarations import _declarations_cache
from .declarations import _dunder
from .declarations import _require_synchronous_result
from .errors import TagCompositionError
from .errors import TagPostconditionError
from .errors import TagResolutionError
from .access import _assigned
from .access import _bound_action
from .access import _bound_condition
from .access import _bound_record
from .fields import _Field
from .fields import _Valid_Field
from .geometry import _direct_bases_for
from .geometry import _form_for
from .geometry import _leaf_tags_for


_PIN_STATE = "__tagkit_pin_state__"
_PIN_PROTECTED_MEMBERS = frozenset(
        {
            "Checkpoint",
            "Field",
            "Form",
            "Rip",
            "Tag",
            }
        )
_RUNTIME_PROTECTED_DUNDERS = frozenset(
        {
            "__bool__",
            "__class__",
            "__contains__",
            "__del__",
            "__delattr__",
            "__dict__",
            "__getattr__",
            "__getattribute__",
            "__ior__",
            "__or__",
            "__setattr__",
            }
        )
_TAGGED_COMPATIBILITY_MEMBERS = frozenset(
        {
            "AppliedTags",
            "ApplyTags",
            "As",
            "FORM_ROOTS",
            "Forms",
            "Geometry",
            "Has",
            "HostType",
            "Outline",
            "Tag",
            "Tags",
            "With",
            }
        )

_runtime_type_cache = WeakValueDictionary()
_committed_queries = ContextVar(
        "tagkit_committed_queries",
        default=(),
        )


def _apply_pin_transaction(
        *args: Any,
        **kwargs: Any,
        ) -> Any:
    from .pins import _apply_pin_transaction as apply_pin_transaction

    return apply_pin_transaction(
            *args,
            **kwargs,
            )


def _apply_transaction(
        *args: Any,
        **kwargs: Any,
        ) -> Any:
    from .transactions import _apply_transaction as apply_transaction

    return apply_transaction(
            *args,
            **kwargs,
            )


def _check_conditions(
        *args: Any,
        **kwargs: Any,
        ) -> Any:
    from .contracts import _check_conditions as check_conditions

    return check_conditions(
            *args,
            **kwargs,
            )


def _checkpoint(
        *args: Any,
        **kwargs: Any,
        ) -> Any:
    from .transactions import _checkpoint as checkpoint

    return checkpoint(
            *args,
            **kwargs,
            )


def _contribution_matches(
        *args: Any,
        **kwargs: Any,
        ) -> Any:
    from .queries import _contribution_matches as contribution_matches

    return contribution_matches(
            *args,
            **kwargs,
            )


def _host_finalizer(
        *args: Any,
        **kwargs: Any,
        ) -> Any:
    from .lifecycle import _host_finalizer as host_finalizer

    return host_finalizer(
            *args,
            **kwargs,
            )


def _record_value_for(
        *args: Any,
        **kwargs: Any,
        ) -> Any:
    from .records import _record_value_for as record_value_for

    return record_value_for(
            *args,
            **kwargs,
            )


def _rip_one(
        *args: Any,
        **kwargs: Any,
        ) -> Any:
    from .transactions import _rip_one as rip_one

    return rip_one(
            *args,
            **kwargs,
            )


def _same_bound_member(
        *args: Any,
        **kwargs: Any,
        ) -> Any:
    from .overlays import _same_bound_member as same_bound_member

    return same_bound_member(
            *args,
            **kwargs,
            )


def Apply(
        *args: Any,
        **kwargs: Any,
        ) -> Any:
    from .api import Apply as apply

    return apply(
            *args,
            **kwargs,
            )


def Has(
        *args: Any,
        **kwargs: Any,
        ) -> Any:
    from .queries import Has as has

    return has(
            *args,
            **kwargs,
            )


def Tags(
        *args: Any,
        **kwargs: Any,
        ) -> Any:
    from .queries import Tags as tags

    return tags(
            *args,
            **kwargs,
            )


@dataclass(
        slots=True,
        )
class _Tag_Snapshot:
    actions: dict[str, Action_Body]
    records: dict[str, Any]
    reports: dict[str, tuple[type["Tag"], Any]]
    operations: dict[str, tuple[type["Tag"], Operation_Body]]
    preconditions: dict[str, Predicate]
    postconditions: dict[str, Predicate]
    deleted: frozenset[str]


@dataclass(
        frozen=True,
        slots=True,
        )
class _Mutable_Snapshot:
    value: object
    snapshot: object


@dataclass(
        frozen=True,
        slots=True,
        )
class _Tag_Namespace_Snapshot:
    namespace: dict[str, Any]
    mutable_values: tuple[_Mutable_Snapshot, ...]
    name: str
    qualname: str
    bases: tuple[type, ...]


@dataclass(
        frozen=True,
        slots=True,
        )
class _Slot_Snapshot:
    descriptor: Any
    was_present: bool
    value: Any


@dataclass(
        frozen=True,
        slots=True,
        )
class _Instance_Snapshot:
    namespace: dict[str, Any] | None
    slots: tuple[_Slot_Snapshot, ...]
    mutable_values: tuple[_Mutable_Snapshot, ...]


@dataclass(
        slots=True,
        )
class _Agent_State:
    host_type: type
    active_tags: list[type["Tag"]]
    actions: dict[str, Action_Body]
    action_origins: dict[str, type["Tag"] | type]
    record_builders: dict[str, Record_Builder]
    record_origins: dict[str, type["Tag"] | type]
    record_values: dict[str, Any]
    preconditions: dict[str, Predicate]
    postconditions: dict[str, Predicate]
    reports: dict[str, Any]
    operations: dict[str, tuple[type["Tag"], Operation_Body]]
    field_reports: dict[type["Tag"], dict[str, Any]]
    field_operations: dict[type["Tag"], dict[str, Operation_Body]]
    field_deletions: dict[type["Tag"], set[str]]
    deleted: set[str]
    snapshots: dict[type["Tag"], _Tag_Snapshot]
    rip_actions: dict[
            type["Tag"],
            tuple[tuple[str, Action_Body], ...],
            ]
    ever_tags: set[type["Tag"]]
    ripped: bool = False

    def Copy(
            state,
            ) -> "_Agent_State":
        return _Agent_State(
                host_type=state.host_type,
                active_tags=list(state.active_tags),
                actions=dict(state.actions),
                action_origins=dict(state.action_origins),
                record_builders=dict(state.record_builders),
                record_origins=dict(state.record_origins),
                record_values=dict(state.record_values),
                preconditions=dict(state.preconditions),
                postconditions=dict(state.postconditions),
                reports=dict(state.reports),
                operations=dict(state.operations),
                field_reports=dict(state.field_reports),
                field_operations=dict(state.field_operations),
                field_deletions=dict(state.field_deletions),
                deleted=set(state.deleted),
                snapshots=dict(state.snapshots),
                rip_actions=dict(state.rip_actions),
                ever_tags=set(state.ever_tags),
                ripped=state.ripped,
                )


@dataclass(
        slots=True,
        )
class _Committed_Query:
    target: object
    state: _Agent_State | None
    record_names: frozenset[str]
    active: bool = True


@dataclass(
        slots=True,
        )
class _Tagging_Transaction:
    identity: int
    active: bool = True


def _deleted_action(
        name: str,
        ) -> Action_Body:
    def Deleted(
            agent: object,
            *args: Any,
            **kwargs: Any,
            ) -> Any:
        raise AttributeError(
                f"{type(agent).__name__} has no visible Action {name!r}"
                )

    return Deleted


def _new_runtime_type(
        host_type: type,
        leaves: tuple[type["Tag"], ...],
        host_bases: tuple[type, ...],
        namespace: dict[str, Any],
        ) -> type:
    class_name = "__".join(
            [
                host_type.__name__,
                *(tag.__name__ for tag in leaves),
                ]
            )

    try:
        runtime_type = type(
                class_name,
                host_bases,
                namespace,
                )
        runtime_bases = type.__getattribute__(
                runtime_type,
                "__bases__",
                )
        runtime_mro = type.__getattribute__(
                runtime_type,
                "__mro__",
                )
        runtime_namespace = type.__getattribute__(
                runtime_type,
                "__dict__",
                )
        valid_runtime_type = (
                isinstance(
                        runtime_type,
                        type,
                        )
                and runtime_type is not host_type
                and len(runtime_bases) == len(host_bases)
                and all(
                        actual is requested
                        for actual, requested in zip(
                                runtime_bases,
                                host_bases,
                                )
                        )
                and any(
                        ancestor is Tagged
                        for ancestor in runtime_mro
                        )
                and any(
                        ancestor is host_type
                        for ancestor in runtime_mro
                        )
                and all(
                        runtime_namespace.get(
                                name,
                                _MISSING,
                                )
                        is value
                        for name, value in namespace.items()
                        )
                )
    except Exception as error:
        raise TagCompositionError(
                "Tags cannot form a Python runtime type with the Target"
                ) from error

    if not valid_runtime_type:
        raise TagCompositionError(
                "Target metaclass did not construct TOP's requested"
                " runtime type"
                )

    return runtime_type


def _actualize_runtime_type(
        agent: object,
        runtime_type: type,
        ) -> None:
    host_name = type(agent).__name__

    try:
        agent.__class__ = runtime_type
    except Exception as error:
        raise TagCompositionError(
                f"{host_name} cannot be actualized in place"
                ) from error

    if type(agent) is not runtime_type:
        raise TagCompositionError(
                f"{host_name} ignored TOP's runtime type actualization"
                )


def _restore_runtime_type(
        agent: object,
        runtime_type: type,
        ) -> None:
    """Restore an internal runtime class without a host veto."""

    try:
        object.__setattr__(
                agent,
                "__class__",
                runtime_type,
                )
    except Exception as error:
        raise TagCompositionError(
                "Target runtime type could not be restored atomically"
                ) from error

    if type(agent) is not runtime_type:
        raise TagCompositionError(
                "Target ignored atomic runtime type restoration"
                )


def _runtime_type_for(
        state: _Agent_State,
        ) -> type:
    protected = {
            name
            for name in _RUNTIME_PROTECTED_DUNDERS
            if (
                name in state.deleted
                or (
                    name in state.actions
                    and isinstance(
                            state.action_origins.get(name),
                            _Tag_Type,
                            )
                    )
                or (
                    name in state.record_builders
                    and isinstance(
                            state.record_origins.get(name),
                            _Tag_Type,
                            )
                    )
                )
            }

    if protected:
        names = ", ".join(
                repr(name)
                for name in sorted(protected)
                )

        raise TagCompositionError(
                "Tags cannot replace TOP-managed runtime"
                f" protocol(s): {names}"
                )

    leaves = _leaf_tags_for(state.active_tags)
    host_type = state.host_type

    if issubclass(host_type, Tagged):
        host_bases = (host_type,)
    else:
        host_bases = (
                Tagged,
                host_type,
                )

    dunder_actions = {
            name: action
            for name, action in state.actions.items()
            if _dunder(name)
            }
    deleted_dunders = [
            name
            for name in state.deleted
            if _dunder(name)
            ]

    # Ordinary (non-dunder) Actions resolve through Tagged.__getattribute__
    # from the Agent state, so they never need to live on the runtime type.
    # When a composition contributes no special-method behaviour the type is
    # a neutral host adapter keyed by (host, leaves); it is shared across
    # every Agent of that shape instead of rebuilt per application.
    if not dunder_actions and not deleted_dunders:
        canonical = tuple(
                sorted(
                        leaves,
                        key=lambda tag: (
                                tag.__module__,
                                tag.__qualname__,
                                ),
                        )
                )
        key = (host_type, canonical)
        shared = _runtime_type_cache.get(key)

        if shared is not None:
            return shared

        active: list[type] = []

        for leaf in canonical:
            for ancestor in _form_for(leaf):
                if ancestor not in active:
                    active.append(ancestor)

        shared = _new_runtime_type(
                host_type,
                canonical,
                host_bases,
                {
                    "_TAGKIT_HOST_TYPE": host_type,
                    "_TAGKIT_ACTIVE_TAGS": tuple(active),
                    },
                )
        _runtime_type_cache[key] = shared

        return shared

    namespace: dict[str, Any] = {
            "_TAGKIT_HOST_TYPE": host_type,
            "_TAGKIT_ACTIVE_TAGS": tuple(state.active_tags),
            }
    namespace.update(dunder_actions)

    for name in deleted_dunders:
        namespace[name] = _deleted_action(name)

    return _new_runtime_type(
            host_type,
            leaves,
            host_bases,
            namespace,
            )


def _is_tag(
        target: object,
        ) -> bool:
    return isinstance(
            target,
            _Tag_Type,
            )


def _new_state_for(
        agent: object,
        ) -> _Agent_State:
    return _Agent_State(
            host_type=type(agent),
            active_tags=[],
            actions={},
            action_origins={},
            record_builders={},
            record_origins={},
            record_values={},
            preconditions={},
            postconditions={},
            reports={},
            operations={},
            field_reports={},
            field_operations={},
            field_deletions={},
            deleted=set(),
            snapshots={},
            rip_actions={},
            ever_tags=set(),
            )


def _direct_pin_state(
        target: type["Tag"],
        ) -> _Agent_State | None:
    namespace = type.__getattribute__(
            target,
            "__dict__",
            )

    return namespace.get(_PIN_STATE)


def _validate_agent_state_slot(
        agent: object,
        ) -> None:
    if _is_tag(agent):
        return

    try:
        state = object.__getattribute__(
                agent,
                "_TAGKIT_STATE",
                )
    except AttributeError:
        return

    if not isinstance(
            state,
            _Agent_State,
            ):
        raise TagCompositionError(
                "Target attribute '_TAGKIT_STATE' conflicts with"
                " TagKit's private runtime state"
                )


def _state_for(
        agent: object,
        ) -> _Agent_State:
    if _is_tag(agent):
        state = _direct_pin_state(agent)

        if state is None:
            state = _new_state_for(agent)
            type.__setattr__(
                    agent,
                    _PIN_STATE,
                    state,
                    )

        return state

    try:
        state = object.__getattribute__(
                agent,
                "_TAGKIT_STATE",
                )
    except AttributeError:
        state = _new_state_for(agent)

        try:
            object.__setattr__(
                    agent,
                    "_TAGKIT_STATE",
                    state,
                    )
        except AttributeError as error:
            raise TagCompositionError(
                    "Tagged Agents must allow TOP state to be attached"
                    ) from error

    if not isinstance(
            state,
            _Agent_State,
            ):
        raise TagCompositionError(
                "Target attribute '_TAGKIT_STATE' conflicts with"
                " TagKit's private runtime state"
                )

    return state


def _existing_state_for(
        agent: object,
        ) -> _Agent_State | None:
    if _is_tag(agent):
        return _direct_pin_state(agent)

    try:
        state = object.__getattribute__(
                agent,
                "_TAGKIT_STATE",
                )
    except AttributeError:
        return None

    if not isinstance(
            state,
            _Agent_State,
            ):
        return None

    return state


def _query_state_for(
        target: object,
        ) -> _Agent_State | None:
    for query in reversed(
            _committed_queries.get()
            ):
        if (
                query.active
                and query.target is target
                ):
            return query.state

    return _existing_state_for(target)


def _record_names_for(
        target: object,
        state: _Agent_State | None,
        ) -> frozenset[str]:
    if state is None:
        return frozenset()

    if _is_tag(target):
        return frozenset(
                state.record_values.keys()
                - state.deleted
                )

    return frozenset(
            name
            for name in state.record_builders
            if (
                name not in state.deleted
                and _record_value_for(
                        target,
                        name,
                        )
                is not _MISSING
                )
            )


def _query_record_names_for(
        target: object,
        state: _Agent_State | None,
        ) -> frozenset[str]:
    for query in reversed(
            _committed_queries.get()
            ):
        if (
                query.active
                and query.target is target
                ):
            return query.record_names

    return _record_names_for(
            target,
            state,
            )


def _set_state(
        agent: object,
        state: _Agent_State,
        ) -> None:
    if _is_tag(agent):
        type.__setattr__(
                agent,
                _PIN_STATE,
                state,
                )

        return

    object.__setattr__(
            agent,
            "_TAGKIT_STATE",
            state,
            )


def _delete_state(
        agent: object,
        ) -> None:
    if _is_tag(agent):
        try:
            type.__delattr__(
                    agent,
                    _PIN_STATE,
                    )
        except AttributeError:
            pass

        return

    try:
        object.__delattr__(
                agent,
                "_TAGKIT_STATE",
                )
    except AttributeError:
        pass


def _host_declaration_for(
        host_type: type,
        name: str,
        ) -> Any:
    for provider in host_type.__mro__:
        if provider is Tagged:
            continue

        if name in provider.__dict__:
            return provider.__dict__[name]

    return _MISSING


def _host_action_for(
        host_type: type,
        name: str,
        target: object | None = None,
        ) -> Action_Body | None:
    attribute = _host_declaration_for(
            host_type,
            name,
            )

    if (
            not callable(attribute)
            and getattr(
                    attribute,
                    "__get__",
                    None,
                    )
            is None
            ):
        return None

    if target is not None:
        candidate = _bind_host_declaration(
                target,
                attribute,
                )

        if not callable(candidate):
            return None

    def Host_Action(
            agent: object,
            *args: Any,
            **kwargs: Any,
            ) -> Any:
        member = _bind_host_declaration(
                agent,
                attribute,
                )

        return member(
                *args,
                **kwargs,
                )

    source = (
            attribute.__func__
            if isinstance(
                    attribute,
                    (
                        classmethod,
                        staticmethod,
                        ),
                    )
            else attribute
            )

    if callable(source):
        Host_Action = wraps(source)(
                Host_Action
                )

    return Host_Action


def _bind_host_declaration(
        agent: object,
        attribute: Any,
        ) -> Any:
    descriptor = getattr(
            attribute,
            "__get__",
            None,
            )

    if descriptor is None:
        return attribute

    return descriptor(
            agent,
            type(agent),
            )


def _host_member_for(
        agent: object,
        host_type: type,
        name: str,
        ) -> Any:
    attribute = _host_declaration_for(
            host_type,
            name,
            )

    if attribute is _MISSING:
        return _MISSING

    return _bind_host_declaration(
            agent,
            attribute,
            )


def _host_namespace_member_for(
        agent: object,
        host_type: type,
        name: str,
        ) -> Any:
    declaration = _host_declaration_for(
            host_type,
            name,
            )

    if declaration is not _MISSING:
        is_data_descriptor = (
                getattr(
                        declaration,
                        "__set__",
                        None,
                        )
                is not None
                or getattr(
                        declaration,
                        "__delete__",
                        None,
                        )
                is not None
                )

        if is_data_descriptor:
            return _bind_host_declaration(
                    agent,
                    declaration,
                    )

    try:
        namespace = object.__getattribute__(
                agent,
                "__dict__",
                )
    except AttributeError:
        namespace = {}

    if name in namespace:
        return namespace[name]

    if declaration is _MISSING:
        return _MISSING

    return _bind_host_declaration(
            agent,
            declaration,
            )


class _Tag_View:
    def __init__(
            view,
            agent: object,
            tag: type["Tag"],
            snapshot: _Tag_Snapshot,
            ) -> None:
        view._agent = agent
        view._tag = tag
        view._snapshot = snapshot

    def __getattr__(
            view,
            name: str,
            ) -> Any:
        view._require_active(
                view._tag,
                name,
                )

        if name in view._snapshot.deleted:
            raise AttributeError(
                    f"{view._tag.__name__} deleted {name!r}"
                    )

        if name in view._snapshot.actions:
            return _bound_action(
                    view._agent,
                    name,
                    view._snapshot.actions[name],
                    )

        if name in view._snapshot.records:
            return _bound_record(
                    view._agent,
                    name,
                    frozen=view._snapshot.records[name],
                    )

        if name in view._snapshot.postconditions:
            return _bound_condition(
                    view._agent,
                    name,
                    view._snapshot.postconditions[name],
                    )

        if name in view._snapshot.preconditions:
            return _bound_condition(
                    view._agent,
                    name,
                    view._snapshot.preconditions[name],
                    )

        if name in view._snapshot.reports:
            origin, value = view._snapshot.reports[name]
            view._require_active(
                    origin,
                    name,
                    )

            return value

        if name in view._snapshot.operations:
            origin, operation = view._snapshot.operations[name]
            view._require_active(
                    origin,
                    name,
                    )

            return partial(
                    operation,
                    origin,
                    )

        raise AttributeError(
                f"{view._tag.__name__} has no visible member {name!r}"
                )

    def _require_active(
            view,
            origin: type["Tag"],
            name: str,
            ) -> None:
        if view._agent in origin._tagkit_field:
            return

        raise TagResolutionError(
                f"{origin.__name__}.{name} is unavailable because"
                f" {origin.__name__} is no longer active"
                )


class _Tag_Type(type):
    """Internal metaclass supporting durable semantic Tag categories."""

    def __new__(
            meta,
            name: str,
            bases: tuple[type, ...],
            namespace: dict[str, Any],
            **kwargs: Any,
            ) -> "_Tag_Type":
        namespace.setdefault(
                "_tagkit_field",
                _Field(),
                )

        return super().__new__(
                meta,
                name,
                bases,
                namespace,
                **kwargs,
                )

    def __str__(
            tag,
            ) -> str:
        return type.__getattribute__(
                tag,
                "__name__",
                )

    def __repr__(
            tag,
            ) -> str:
        name = str( tag )
        description = type.__getattribute__(
                tag,
                "__doc__",
                )

        if not isinstance(
                description,
                str,
                ):
            return name

        description = cleandoc( description )

        if not description:
            return name

        return (
                name
                + "\n"
                + description
                )

    def __getattribute__(
            tag,
            name: str,
            ) -> Any:
        if name == _PIN_STATE:
            raise AttributeError(name)

        if name == "Field":
            return type.__getattribute__(
                    tag,
                    "_tagkit_field",
                    )

        state = _existing_state_for(tag)

        if state is not None:
            if name in state.deleted:
                raise AttributeError(
                        f"{tag.__name__} has no visible Tag member {name!r}"
                        )

            if name in state.actions:
                return _bound_action(
                        tag,
                        name,
                        state.actions[name],
                        )

            if name in state.record_builders:
                if name in state.record_values:
                    return _bound_record(
                            tag,
                            name,
                            frozen=state.record_values[name],
                            )

                raise AttributeError(
                        f"{tag.__name__} has no visible Tag member {name!r}"
                        )

            if name in state.postconditions:
                return _bound_condition(
                        tag,
                        name,
                        state.postconditions[name],
                        )

            if name in state.preconditions:
                return _bound_condition(
                        tag,
                        name,
                        state.preconditions[name],
                        )

        value = super().__getattribute__(name)

        if isinstance(value, Report):
            return value.value

        return value

    def __getattr__(
            tag,
            name: str,
            ) -> _Tag_View:
        state = _existing_state_for(tag)

        if state is not None:
            for pin in reversed(state.active_tags):
                if pin.__name__ != name:
                    continue

                snapshot = state.snapshots.get(pin)

                if (
                        snapshot is not None
                        and tag in pin._tagkit_field
                        ):
                    return _Tag_View(
                            tag,
                            pin,
                            snapshot,
                            )

                break

        raise AttributeError(
                f"{tag.__name__} has no Tag view {name!r}"
                )

    def __getitem__(
            tag,
            target: object,
            ) -> _Field | _Valid_Field | _Tag_View:
        if target is ...:
            return tag.Field

        if (
                isinstance(
                        target,
                        tuple,
                        )
                and not target
                ):
            return tag.Field

        if isinstance(
                target,
                slice,
                ):
            if (
                    target.start is None
                    and target.stop is None
                    and target.step is None
                    ):
                return _Valid_Field(
                        tag._tagkit_field,
                        )

            raise TypeError(
                    f"{tag.__name__} accepts only [:]"
                    " for sound Field members"
                    )

        state = _existing_state_for(target)
        snapshot = (
                state.snapshots.get(tag)
                if state is not None
                else None
                )

        if (
                target not in tag._tagkit_field
                or snapshot is None
                ):
            target_name = (
                    target.__name__
                    if _is_tag(target)
                    else type(target).__name__
                    )

            raise TagResolutionError(
                    f"{tag.__name__} is not active on"
                    f" {target_name}"
                    )

        return _Tag_View(
                target,
                tag,
                snapshot,
                )

    def __setattr__(
            tag,
            name: str,
            value: Any,
            ) -> None:
        if name == _PIN_STATE:
            raise TagCompositionError(
                    "Pinned Tag state is managed internally"
                    )

        state = _existing_state_for(tag)

        if state is not None:
            if name in state.deleted:
                raise TagCompositionError(
                        f"Tag member {name!r}"
                        " is masked by a Delete from an active Pin"
                        )

            if name in state.actions:
                raise TagCompositionError(
                        f"Tag-scope Operation {name!r}"
                        " cannot be assigned directly"
                        )

            if name in state.record_builders:
                state.record_values[name] = _assigned(value)

                return

        type.__setattr__(
                tag,
                name,
                value,
                )
        _declarations_cache.pop(
                tag,
                None,
                )

    def __delattr__(
            tag,
            name: str,
            ) -> None:
        if name == _PIN_STATE:
            raise TagCompositionError(
                    "Pinned Tag state is managed internally"
                    )

        state = _existing_state_for(tag)

        if state is not None:
            if name in state.deleted:
                raise TagCompositionError(
                        f"Tag member {name!r}"
                        " is masked by a Delete from an active Pin"
                        )

            if name in state.actions:
                raise TagCompositionError(
                        f"Tag-scope Operation {name!r}"
                        " cannot be deleted directly"
                        )

            if name in state.record_builders:
                if name not in state.record_values:
                    raise AttributeError(name)

                del state.record_values[name]

                return

        type.__delattr__(
                tag,
                name,
                )
        _declarations_cache.pop(
                tag,
                None,
                )

    def __bool__(
            tag,
            ) -> bool:
        return _check_conditions(
                tag,
                "postconditions",
                TagPostconditionError,
                "Postcondition",
                False,
                )

    def Tag(
            tag,
            pin: type["Tag"],
            ) -> _Tag_View:
        state = _existing_state_for(tag)
        snapshot = (
                state.snapshots.get(pin)
                if state is not None
                else None
                )

        if (
                tag not in pin._tagkit_field
                or snapshot is None
                ):
            raise TagResolutionError(
                    f"{pin.__name__} is not an active Pin on"
                    f" {tag.__name__}"
                    )

        return _Tag_View(
                tag,
                pin,
                snapshot,
                )

    def __contains__(
            tag,
            candidate: object,
            ) -> bool:
        return candidate in tag._tagkit_field

    def __iter__(
            tag,
            ) -> Iterator[object]:
        return iter(
                _Valid_Field(
                        tag._tagkit_field,
                        )
                )

    def __instancecheck__(
            tag,
            candidate: object,
            ) -> bool:
        # isinstance is the HAS-BEEN check: True once an Agent has ever been a
        # member of this Tag, and it stays True after Rip and through later
        # re-composition ("ever an X, always an X"). ``agent in Tag`` is the
        # IS check -- current Field membership. Non-Agents and never-members
        # fall back to ordinary isinstance.
        state = _existing_state_for(candidate)

        if state is not None and tag in state.ever_tags:
            return True

        return super().__instancecheck__(candidate)

    def Rip(
            tag,
            agent: object,
            ) -> object:
        """Extract an Agent from this Tag's Field (the only sanctioned exit).

        After ``Tag.Rip(agent)``: ``agent in Tag`` is False and the Agent no
        longer appears in the Field. By default its Actions and Records
        remain (a Rogue Agent); any ``@Rip`` teardown Actions of this Tag run
        after extraction. Ripping a Base first Rips its dependent Shapes in
        reverse application order; unrelated Bases remain active.

        Tags are ripped; Records are removed with ``del agent.record``.
        """

        return _rip_one(
                agent,
                tag,
                )

    def Checkpoint(
            tag,
            target: object,
            ) -> Any:
        """Open recoverable, provisional Tagging for one Target.

        The returned control object lives outside the Target. Finish it with
        ``Commit()`` or ``Restore()``, or use it as a context manager.
        """

        return _checkpoint( target )

    def __call__(
            tag,
            *args: object,
            **kwargs: object,
            ) -> object:
        if (
                len(args) == 1
                and _is_tag(args[0])
                ):
            return _apply_pin_transaction(
                    args[0],
                    tag,
                    dict(kwargs),
                    )

        if (
                len(args) == 1
                and not isinstance(args[0], type)
                ):
            return _apply_transaction(
                    args[0],
                    tag,
                    dict(kwargs),
                    )

        return super().__call__(
                *args,
                **kwargs,
                )


class Tag(metaclass=_Tag_Type):
    """Base class for TOP semantic categories."""

    @classmethod
    def Form(
            tag,
            *,
            roots: tuple[type["Tag"], ...] = (),
            ) -> tuple[type["Tag"], ...]:
        """Return the Base-first Form of this Tag, ending with the Tag."""

        form = _form_for(tag)

        if not roots:
            return form

        for index, candidate in enumerate(form):
            if candidate in roots:
                return form[index:]

        return form


class Tagged:
    """Mixin supplied to an Agent after its first successful Tagging."""

    FORM_ROOTS: ClassVar[tuple[type[Tag], ...]] = ()

    def __getattribute__(
            agent,
            name: str,
            ) -> Any:
        if name == "_TAGKIT_STATE":
            return object.__getattribute__(
                    agent,
                    name,
                    )

        try:
            state = object.__getattribute__(
                    agent,
                    "_TAGKIT_STATE",
                    )
        except AttributeError:
            state = None

        if state is not None:
            if name in state.deleted:
                raise AttributeError(
                        f"{type(agent).__name__} has no visible member {name!r}"
                        )

            if name in state.actions:
                return _bound_action(
                        agent,
                        name,
                        state.actions[name],
                        )

            if name in state.record_builders:
                # A Record lives only as an Agent instance value. Resolve to
                # that value, or raise; the Tag keeps its builder declaration.
                value = _record_value_for(
                        agent,
                        name,
                        )

                if value is not _MISSING:
                    return _bound_record(
                            agent,
                            name,
                            frozen=value,
                            )

                raise AttributeError(
                        f"{type(agent).__name__} has no visible member {name!r}"
                        )

            if name in state.postconditions:
                return _bound_condition(
                        agent,
                        name,
                        state.postconditions[name],
                        )

            if name in state.preconditions:
                return _bound_condition(
                        agent,
                        name,
                        state.preconditions[name],
                        )

            if name in _TAGGED_COMPATIBILITY_MEMBERS:
                getattribute_declaration = _host_declaration_for(
                        state.host_type,
                        "__getattribute__",
                        )

                if getattribute_declaration is not object.__getattribute__:
                    custom_getattribute = _bind_host_declaration(
                            agent,
                            getattribute_declaration,
                            )
                    custom_value = custom_getattribute(name)
                    default_value = object.__getattribute__(
                            agent,
                            name,
                            )

                    if not _same_bound_member(
                            custom_value,
                            default_value,
                            ):
                        return custom_value

                host_member = _host_namespace_member_for(
                        agent,
                        state.host_type,
                        name,
                        )

                if host_member is not _MISSING:
                    return host_member

                return object.__getattribute__(
                        agent,
                        name,
                        )

            host_getattribute = _host_member_for(
                    agent,
                    state.host_type,
                    "__getattribute__",
                    )

            if host_getattribute is not _MISSING:
                return host_getattribute(
                        name,
                        )

        return object.__getattribute__(
                agent,
                name,
                )

    def __setattr__(
            agent,
            name: str,
            value: Any,
            ) -> None:
        if name == "_TAGKIT_STATE":
            object.__setattr__(
                    agent,
                    name,
                    value,
                    )
            return

        value = _assigned(value)

        try:
            state = object.__getattribute__(
                    agent,
                    "_TAGKIT_STATE",
                    )
        except AttributeError:
            object.__setattr__(
                    agent,
                    name,
                    value,
                    )
            return

        host_setattr = _host_member_for(
                agent,
                state.host_type,
                "__setattr__",
                )

        if host_setattr is not _MISSING:
            host_setattr(
                    name,
                    value,
                    )
            return

        object.__setattr__(
                agent,
                name,
                value,
                )

    def __getattr__(
            agent,
            name: str,
            ) -> _Tag_View:
        state = _state_for(agent)

        for tag in reversed(state.active_tags):
            if tag.__name__ != name:
                continue

            snapshot = state.snapshots.get(tag)

            if (
                    snapshot is None
                    or agent not in tag._tagkit_field
                    ):
                break

            return _Tag_View(
                    agent,
                    tag,
                    snapshot,
                    )

        host_getattr = _host_member_for(
                agent,
                state.host_type,
                "__getattr__",
                )

        if host_getattr is not _MISSING:
            return host_getattr(
                    name,
                    )

        raise AttributeError(
                f"{type(agent).__name__} has no Tag view {name!r}"
                )

    def __bool__(
            agent,
            ) -> bool:
        state = _existing_state_for(agent)

        if state is not None and state.postconditions:
            return _check_conditions(
                    agent,
                    "postconditions",
                    TagPostconditionError,
                    "Postcondition",
                    False,
                    )

        if state is not None:
            host_bool = _host_member_for(
                    agent,
                    state.host_type,
                    "__bool__",
                    )

            if host_bool is not _MISSING:
                return host_bool()

            has_length = (
                    "__len__" in state.actions
                    or (
                        "__len__" not in state.deleted
                        and _host_declaration_for(
                                state.host_type,
                                "__len__",
                                )
                        is not _MISSING
                        )
                    )

            if has_length:
                return len(agent) != 0

        return True

    def __format__(
            agent,
            specification: str,
            ) -> str:
        key = specification.strip().casefold()

        if key in {
                "contract",
                "display",
                "status",
                }:
            from .contracts import Contract

            return Contract.Format(
                    agent,
                    specification,
                    )

        state = _existing_state_for(agent)

        if state is not None:
            host_format = _host_member_for(
                    agent,
                    state.host_type,
                    "__format__",
                    )

            if host_format is not _MISSING:
                return host_format(specification)

        if not specification:
            return str(agent)

        return format(
                str(agent),
                specification,
                )

    def __del__(
            agent,
            ) -> None:
        # Best-effort exit protocol: run @Rip teardown for still-active
        # Tags when the Agent is collected. Python does not promise __del__
        # at interpreter shutdown or inside reference cycles -- use Scope()
        # or an explicit Rip for guaranteed teardown. The whole body is
        # guarded so a dying Agent never raises from a finalizer, even when
        # module globals are already being torn down at shutdown.
        try:
            try:
                state = object.__getattribute__(
                        agent,
                        "_TAGKIT_STATE",
                        )
            except AttributeError:
                state = None

            if state is not None and not state.ripped:
                state.ripped = True

                for tag in reversed(state.active_tags):
                    for name, rip in state.rip_actions.get(tag, ()):
                        try:
                            _require_synchronous_result(
                                    rip(agent),
                                    (
                                        "Finalizer Rip protocol"
                                        f" {tag.__qualname__}.{name}"
                                        ),
                                    )
                        except Exception:
                            pass

            finalizer = _host_finalizer(agent)

            if finalizer is not None:
                finalizer(agent)
        except Exception:
            pass

    @classmethod
    def HostType(
            base_type,
            ) -> type:
        return getattr(
                base_type,
                "_TAGKIT_HOST_TYPE",
                base_type,
                )

    @classmethod
    def AppliedTags(
            base_type,
            ) -> tuple[type[Tag], ...]:
        return tuple(
                getattr(
                        base_type,
                        "_TAGKIT_ACTIVE_TAGS",
                        (),
                        )
                )

    def ApplyTags(
            agent,
            *tags: type[Tag],
            ) -> "Tagged":
        return Apply(
                agent,
                *tags,
                )

    def With(
            agent,
            *tags: type[Tag],
            ) -> "Tagged":
        return Apply(
                agent,
                *tags,
                )

    def As(
            agent,
            *tags: type[Tag],
            ) -> "Tagged":
        return Apply(
                agent,
                *tags,
                )

    def __or__(
            agent,
            value: object,
            ) -> Any:
        if isinstance(
                value,
                _Tag_Type,
                ):
            return Apply(
                    agent,
                    value,
                    )

        state = _existing_state_for(agent)
        host_or = (
                _host_member_for(
                        agent,
                        state.host_type,
                        "__or__",
                        )
                if state is not None
                else _MISSING
                )

        if host_or is _MISSING:
            return NotImplemented

        return host_or(
                value,
                )

    def __ior__(
            agent,
            value: object,
            ) -> Any:
        if isinstance(
                value,
                _Tag_Type,
                ):
            return Apply(
                    agent,
                    value,
                    )

        state = _existing_state_for(agent)

        if state is None:
            return NotImplemented

        host_ior = _host_member_for(
                agent,
                state.host_type,
                "__ior__",
                )

        if host_ior is not _MISSING:
            return host_ior(
                    value,
                    )

        return NotImplemented

    def Tag(
            agent,
            tag: type[Tag],
            ) -> _Tag_View:
        state = _state_for(agent)
        snapshot = state.snapshots.get(tag)

        if (
                agent not in tag._tagkit_field
                or snapshot is None
                ):
            raise TagResolutionError(
                    f"{tag.__name__} is not active on this Agent"
                    )

        return _Tag_View(
                agent,
                tag,
                snapshot,
                )

    def Tags(
            agent,
            ) -> tuple[type[Tag], ...]:
        return Tags(agent)

    def Forms(
            agent,
            ) -> tuple[tuple[type[Tag], ...], ...]:
        state = _state_for(agent)
        roots = getattr(
                state.host_type,
                "FORM_ROOTS",
                (),
                )

        return tuple(
                tag.Form(
                        roots=roots,
                        )
                for tag in _leaf_tags_for(state.active_tags)
                )

    def Geometry(
            agent,
            ) -> dict[type[Tag], tuple[type[Tag], ...]]:
        ordered_tags: list[type[Tag]] = []

        for form in Tagged.Forms(agent):
            for tag in form:
                if tag not in ordered_tags:
                    ordered_tags.append(tag)

        return {
                base: tuple(
                        shape
                        for shape in ordered_tags
                        if base in _direct_bases_for(shape)
                        )
                for base in ordered_tags
                }

    def Outline(
            agent,
            *,
            indent: str = "  ",
            ) -> str:
        state = _state_for(agent)
        lines = [state.host_type.__name__]
        geometry = Tagged.Geometry(agent)
        shapes = {
                shape
                for direct_shapes in geometry.values()
                for shape in direct_shapes
                }
        roots = tuple(
                tag
                for tag in geometry
                if tag not in shapes
                )

        def Visit(
                tag: type[Tag],
                depth: int,
                path: frozenset[type[Tag]],
                ) -> None:
            lines.append(
                    f"{indent * depth}{str( tag )}"
                    )

            if tag in path:
                return

            next_path = (
                    path
                    | {
                        tag,
                        }
                    )

            for shape in geometry[tag]:
                Visit(
                        shape,
                        depth + 1,
                        next_path,
                        )

        for root in roots:
            Visit(
                    root,
                    1,
                    frozenset(),
                    )

        return "\n".join(lines)

    def Has(
            agent,
            *probes: object,
            ) -> bool:
        return Has(
                agent,
                *probes,
                )

    def __contains__(
            agent,
            probe: object,
            ) -> bool:
        state = _existing_state_for(agent)
        query_state = _query_state_for(agent)

        if isinstance(
                probe,
                _Tag_Type,
                ):
            return Has(
                    agent,
                    probe,
                    )

        if (
                query_state is not None
                and _contribution_matches(
                        query_state,
                        probe,
                        )
                ):
            return Has(
                    agent,
                    probe,
                    )

        if state is not None:
            host_contains = _host_declaration_for(
                    state.host_type,
                    "__contains__",
                    )

            if (
                    "__contains__" not in state.deleted
                    and host_contains is not _MISSING
                    ):
                member = _host_member_for(
                        agent,
                        state.host_type,
                        "__contains__",
                        )

                return member(
                    probe,
                    )

            has_native_iteration = any(
                    (
                        name in state.actions
                        or (
                            name not in state.deleted
                            and _host_declaration_for(
                                    state.host_type,
                                    name,
                                    )
                            is not _MISSING
                            )
                        )
                    for name in (
                            "__iter__",
                            "__getitem__",
                            )
                    )

            if has_native_iteration:
                for candidate in agent:
                    if (
                            candidate is probe
                            or candidate == probe
                            ):
                        return True

                return False

        return Has(
                agent,
                probe,
                )
