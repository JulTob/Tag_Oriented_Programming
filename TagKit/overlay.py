"""Overlay: installing one Tag's declarations into a candidate state.

The latest applied Layer is the visible Overlay for a name. Within one
scope a name is one slot: an Action or a Record, never both at once.
"""

from __future__ import annotations

from functools import wraps
from typing import Any
from typing import Callable
import warnings

from .contracts import _bind_condition
from .declarations import _Declarations
from .declarations import _is_flag
from .declarations import _parameters_of
from .declarations import _protocol_inputs
from .declarations import _takes_stored
from .declarations import _takes_underlay
from .errors import TagCompositionError
from .errors import TagDeclarationError
from .errors import TagError
from .errors import TagOverwriteWarning
from .errors import TagContractWarning
from .errors import TagResolutionError
from .declarations import STATE
from .declarations import Report
from .declarations import _declarations_of
from .geometry import _related
from .declarations import _MISSING
from .state import _Bound
from .state import _Pinned_Operation
from .state import _State
from .state import _namespace_of
from .state import _state_of


Function = Callable[..., Any]


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _is_tag_type(
        candidate: object,
        ) -> bool:
    from .tags import MetaTag

    return isinstance(candidate, MetaTag)


def _independent(
        tag: type,
        origin: type,
        ) -> bool:
    """True when ``origin`` is a Tag unrelated to ``tag`` (not in its Form)."""

    return (
            _is_tag_type(origin)
            and not _related(tag, origin)
            )


def _host_function(
        host_type: type,
        name: str,
        ) -> Function | None:
    """A plain callable the host class defines under ``name``, wrapped so it
    can serve as an Underlay."""

    for klass in host_type.__mro__:
        attribute = klass.__dict__.get(name)

        if attribute is None:
            continue

        if isinstance(attribute, (classmethod, staticmethod)):
            return None

        if not callable(attribute):
            return None

        @wraps(attribute)
        def Host_Action(
                agent: object,
                *args: Any,
                **kwargs: Any,
                ) -> Any:
            return attribute(
                    agent,
                    *args,
                    **kwargs,
                    )

        return Host_Action

    return None


def _host_data_descriptor(
        host_type: type,
        name: str,
        ) -> bool:
    for klass in host_type.__mro__:
        attribute = klass.__dict__.get(name)

        if attribute is not None:
            return hasattr(
                    type(attribute),
                    "__set__",
                    )

    return False


def _compose(
        function: Function,
        underlay: Function | None,
        ) -> Function:
    """Bind an Action to its Underlay (when it asks for one)."""

    uses_underlay = _takes_underlay(function)

    if not uses_underlay:
        return function

    if underlay is None:
        raise TagResolutionError(
                f"{function.__qualname__} requires a visible Underlay"
                )

    @wraps(function)
    def Call(
            agent: object,
            *args: Any,
            **kwargs: Any,
            ) -> Any:
        def prior(
                *next_args: Any,
                **next_kwargs: Any,
                ) -> Any:
            if next_args or next_kwargs:
                return underlay(
                        agent,
                        *next_args,
                        **next_kwargs,
                        )

            return underlay(
                    agent,
                    *args,
                    **kwargs,
                    )

        return function(
                agent,
                prior,
                *args,
                **kwargs,
                )

    return Call


def _adapter(
        tag: type,
        name: str,
        operation: Function,
        ) -> Function:
    """The Action a Public Operation publishes: the Agent is passed to the
    Operation as its second input. A published member is an Agency
    privilege: it requires active membership, so a Rogue Agent's call
    fails closed (STEP-SPEC-10)."""

    def Published(
            agent: object,
            *args: Any,
            **kwargs: Any,
            ) -> Any:
        _require_membership(
                agent,
                tag,
                name,
                "Operation",
                )

        return operation(
                tag,
                agent,
                *args,
                **kwargs,
                )

    Published.__name__ = name
    Published.__qualname__ = f"{tag.__qualname__}.{name}"
    Published.__doc__ = operation.__doc__

    return Published


def _require_membership(
        agent: object,
        tag: type,
        name: str,
        kind: str,
        ) -> None:
    from .state import _name_of
    from .state import _state_of

    state = _state_of(agent)

    if state is None or tag not in state.active:
        raise TagResolutionError(
                f"{name!r} is a published {kind} of {tag.__name__};"
                f" {_name_of(agent)} is no longer a member, and a published"
                " member is a privilege of membership"
                )


# ------------------------------------------------------------------
# Installing
# ------------------------------------------------------------------


def _install(
        state: _State,
        tag: type,
        declarations: _Declarations,
        ) -> None:
    """Lay ``tag`` over ``state`` (a candidate copy). Order matters: deletions
    free names first; conditions, Tag members, Actions, Records follow."""

    if _is_flag(tag):
        _refuse_container_host(
                state,
                tag,
                )

    for name in declarations.deletions:
        _delete(state, name)

    for name, function in declarations.preconditions:
        state.preconditions[name] = _bind_condition(
                function,
                state.preconditions.get(name),
                True,
                )

    for name, function in declarations.postconditions:
        prior = state.postconditions.get(name)

        if (
                prior is not None
                and not _takes_underlay(function)
                and _origin_of(prior) is not tag
                ):
            warnings.warn(
                    f"{tag.__name__}.{name} overrides a Base Postcondition"
                    " without @Underlay (weakens a promise; see Forward-Post)",
                    TagContractWarning,
                    stacklevel=6,
                    )

        state.postconditions[name] = _stamp(
                _bind_condition(
                        function,
                        prior,
                        False,
                        ),
                tag,
                )

    for name, report, public in declarations.reports:
        state.reports[name] = (tag, report)

        if public:
            state.published.add(name)

    for name, operation, public in declarations.operations:
        state.operations[name] = (tag, operation)

        if public:
            _install_action(
                    state,
                    tag,
                    name,
                    _adapter(tag, name, operation),
                    )

    for name, function in declarations.actions:
        _install_action(
                state,
                tag,
                name,
                function,
                )

    for name, builder in declarations.records:
        _install_record(
                state,
                tag,
                name,
                builder,
                )

    state.secrets.update(declarations.secrets)

    if state.pinned is not None:
        state.published.update(declarations.published)

    if declarations.rips:
        state.rips[tag] = tuple(
                state.actions[name]
                for name in declarations.rips
                )


def _refuse_stored_input_collision(
        builder: Function,
        inputs: dict[str, Any],
        ) -> None:
    """A Record's second positional parameter is the stored value. If it is
    named like a supplied input, the author almost certainly meant the
    input; say so rather than hand over the stored value in silence."""

    second = _parameters_of(builder).named[1][0]

    if second in inputs:
        raise TagDeclarationError(
                f"{builder.__qualname__}: its second parameter {second!r} is"
                f" the stored value, but an input named {second!r} was"
                " supplied. Take the input by name after a `*`:"
                f" `def {builder.__name__}(agent, *, {second})`, or rename"
                " the stored parameter."
                )


def _refuse_container_host(
        state: _State,
        tag: type,
        ) -> None:
    from .access import _host_member

    if state.pinned is not None:
        return   # on a Tag, TOP owns `in`: a string in it asks for a keyword

    if _host_member(state.host_type, "__contains__") is not None:
        raise TagCompositionError(
                f"{tag.__name__} is a Flag, but the host"
                f" {state.host_type.__name__} defines its own `in`; a"
                " keyword needs that seat empty"
                )


def _stamp(
        check: Function,
        tag: type,
        ) -> Function:
    """Remember which Tag bound a condition, so a Tag re-applied after a
    Rip replaces its own promise silently: a fresh Tagging, not a Shape
    weakening a Base."""

    check.__tagkit_origin__ = tag   # type: ignore[attr-defined]

    return check


def _origin_of(
        check: Function,
        ) -> type | None:
    return getattr(
            check,
            "__tagkit_origin__",
            None,
            )


def _own_declaration(
        pinned: type,
        name: str,
        ) -> tuple[type, str, Any] | None:
    """Where the pinned Tag itself declares ``name``, as what, and the
    declared object: ("operation" | "report" | "value" | "agent" |
    "protocol"). None when the name is absent or TOP-managed (landed by a
    Pin), in which case the Overlay laws decide."""

    for klass in pinned.__mro__:
        if name not in klass.__dict__:
            continue

        managed = klass.__dict__.get(STATE)

        if managed is not None and (
                name in managed.actions
                or name in managed.records
                ):
            return None

        declared = klass.__dict__[name]

        if not hasattr(klass, "_tagkit_field"):
            return (klass, "protocol", declared)

        declarations = _declarations_of(klass)

        if any(name == n for n, _f, _p in declarations.operations):
            return (klass, "operation", declared)

        if any(name == n for n, _r, _p in declarations.reports):
            return (klass, "report", declared)

        if any(name == n for n, _f in declarations.actions) or any(
                name == n for n, _f in declarations.records
                ):
            return (klass, "agent", declared)

        if (
                any(name == n for n, _f in declarations.preconditions)
                or any(name == n for n, _f in declarations.postconditions)
                or any(name == n for n, _f in declarations.imprints)
                or name in declarations.deletions
                ):
            return (klass, "protocol", declared)

        return (klass, "value", declared)

    return None


def _refuse_tag_member(
        state: _State,
        tag: type,
        name: str,
        ) -> None:
    """Collision control for a Pin (STEP-SPEC-9 §4). A Pin's members are
    Tag scope, so they may overlay what the Tag declares in Tag scope (an
    Operation, a Report, a plain value) as a host member: silently, with
    the declaration as Underlay or stored value. They may never take a
    name the Tag declares in Agent scope or as a protocol: on a class the
    two scopes share one dictionary, and the write would silently remove
    the declaration from every future Agent's contract. Nor a name every
    Tag answers through its metaclass."""

    pinned = state.pinned

    if hasattr(type(pinned), name):
        raise TagCompositionError(
                f"{tag.__name__}.{name}: a Pin may not name what every Tag"
                f" already answers ({name!r} belongs to the Tag's metaclass)"
                )

    found = _own_declaration(
            pinned,
            name,
            )

    if found is None:
        return

    klass, kind, declared = found

    if kind in ("operation", "report", "value"):
        state.originals.setdefault(
                name,
                declared,
                )   # the first patch remembers the declaration
        return

    where = (
            "itself"
            if klass is pinned
            else f"in its Base {klass.__name__}"
            )
    what = (
            "an Agent-scope member"
            if kind == "agent"
            else "a protocol"
            )

    raise TagCompositionError(
            f"{tag.__name__}.{name}: {pinned.__name__} declares {name!r}"
            f" {where} as {what}; a Pin overlays a Tag's Operations and"
            " Reports, never its Agent members or protocols (STEP-SPEC-9 §4)"
            )


def _pinned_host_function(
        pinned: type,
        name: str,
        ) -> Function | None:
    """The pinned Tag's own Operation under ``name``, as the Underlay of a
    Pin Action: the patch can call the engine it replaces."""

    found = _own_declaration(
            pinned,
            name,
            )

    if found is None or found[1] != "operation":
        return None

    operation = found[2].__func__

    @wraps(operation)
    def Host_Operation(
            tag: type,
            *args: Any,
            **kwargs: Any,
            ) -> Any:
        return operation(
                tag,
                *args,
                **kwargs,
                )

    return Host_Operation


def _pinned_stored(
        pinned: type,
        name: str,
        ) -> Any:
    """What the pinned Tag currently holds under ``name``, for a Pin
    Record's stored seat: its own Report's value, a plain value, or what an
    earlier Pin landed (own or inherited). Behaviour is never a stored
    value."""

    for klass in pinned.__mro__:
        if name not in klass.__dict__:
            continue

        declared = klass.__dict__[name]

        if isinstance(declared, Report):
            return declared.__get__(
                    None,
                    pinned,
                    )

        if isinstance(
                declared,
                (
                    _Bound,
                    _Pinned_Operation,
                    classmethod,
                    staticmethod,
                ),
                ) or callable(declared):
            return None

        return declared

    return None


def _delete(
        state: _State,
        name: str,
        ) -> None:
    state.actions.pop(name, None)
    state.action_origins.pop(name, None)
    state.records.pop(name, None)
    state.preconditions.pop(name, None)
    state.postconditions.pop(name, None)
    state.reports.pop(name, None)
    state.operations.pop(name, None)
    state.published.discard(name)
    state.secrets.discard(name)
    state.deleted.add(name)


def _install_action(
        state: _State,
        tag: type,
        name: str,
        function: Function,
        ) -> None:
    if state.pinned is not None:
        _refuse_tag_member(
                state,
                tag,
                name,
                )

    record_origin = state.records.get(name)

    if record_origin is not None:
        if _independent(tag, record_origin):
            raise TagCompositionError(
                    f"{tag.__name__}.{name} is an Action but"
                    f" {record_origin.__name__} already contributes a Record"
                    " of that name; independent Tags cannot share one Agent"
                    " name across kinds"
                    )

        state.records.pop(name)

    underlay = state.actions.get(name)
    origin = state.action_origins.get(name, state.host_type)

    if underlay is None and name not in state.deleted:
        if state.pinned is not None:
            underlay = _pinned_host_function(
                    state.pinned,
                    name,
                    )
        else:
            underlay = _host_function(
                    state.host_type,
                    name,
                    )

    if (
            underlay is not None
            and not _takes_underlay(function)
            and _independent(tag, origin)
            ):
        warnings.warn(
                f"{tag.__name__}.{name} replaces the Action of independent"
                f" Tag {origin.__name__}",
                TagOverwriteWarning,
                stacklevel=6,
                )

    state.actions[name] = _compose(
            function,
            underlay,
            )
    state.action_origins[name] = tag
    state.deleted.discard(name)
    state.published.discard(name)


def _install_record(
        state: _State,
        tag: type,
        name: str,
        builder: Function,
        ) -> None:
    if state.pinned is not None:
        _refuse_tag_member(
                state,
                tag,
                name,
                )

    if _host_data_descriptor(state.host_type, name):
        raise TagCompositionError(
                f"{tag.__name__}.{name} is a Record but the host"
                f" {state.host_type.__name__} defines {name!r} as a property"
                " or slot; Records need an ordinary attribute"
                )

    action_origin = state.action_origins.get(name)

    if action_origin is not None:
        if _independent(tag, action_origin):
            raise TagCompositionError(
                    f"{tag.__name__}.{name} is a Record but"
                    f" {action_origin.__name__} already contributes an"
                    " Action of that name; independent Tags cannot share"
                    " one Agent name across kinds"
                    )

        state.actions.pop(name)
        state.action_origins.pop(name)

    prior = state.records.get(name)

    if (
            prior is not None
            and not _takes_stored(builder)
            and _independent(tag, prior)
            ):
        warnings.warn(
                f"{tag.__name__}.{name} replaces the Record of independent"
                f" Tag {prior.__name__}",
                TagOverwriteWarning,
                stacklevel=6,
                )

    state.records[name] = tag
    state.deleted.discard(name)
    state.published.discard(name)


# ------------------------------------------------------------------
# Materializing Records
# ------------------------------------------------------------------


def _materialize(
        agent: object,
        declarations: _Declarations,
        deleted_before: set[str],
        inputs: dict[str, Any],
        ) -> None:
    """Run the Tag's Record builders and store their values on the Agent.

    The builder's optional second positional input is the value already
    stored under that name, or None when there is none (or the name was
    deleted). Application inputs bind by name to the parameters after
    that, so ``def code(agent, *, code)`` stores the input directly.
    """

    namespace = _namespace_of(agent)
    pinned = isinstance(agent, type)

    for name, builder in declarations.records:
        if pinned:
            stored = _state_of(agent).secret_values.get(name, _MISSING)

            if stored is _MISSING:
                stored = _pinned_stored(
                        agent,
                        name,
                        )
        else:
            stored = namespace.get(name)

        if name in deleted_before or isinstance(
                stored,
                (
                    _Bound,
                    _Pinned_Operation,
                ),
                ):
            stored = None

        takes_stored = _takes_stored(builder)

        if takes_stored:
            _refuse_stored_input_collision(
                    builder,
                    inputs,
                    )

        named = _protocol_inputs(
                builder,
                inputs,
                2 if takes_stored else 1,
                )

        try:
            if takes_stored:
                value = builder(
                        agent,
                        stored,
                        **named,
                        )
            else:
                value = builder(
                        agent,
                        **named,
                        )
        except TagError:
            raise
        except Exception as error:
            raise TagCompositionError(
                    f"Record {builder.__qualname__} could not be"
                    f" materialized: {type(error).__name__}: {error}"
                    ) from error

        if pinned and name in declarations.secrets:
            namespace.pop(name, None)
            _state_of(agent).secret_values[name] = value
        else:
            namespace[name] = value
