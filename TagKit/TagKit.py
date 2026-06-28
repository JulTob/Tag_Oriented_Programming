from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from functools import partial
from functools import wraps
from inspect import Parameter
from inspect import signature
from types import MethodType
from typing import Any
from typing import Callable
from typing import ClassVar
from typing import Iterator
from weakref import WeakKeyDictionary
from weakref import WeakValueDictionary
import atexit
import warnings
import weakref


Predicate = Callable[[object], bool]
Record_Builder = Callable[..., Any]
Operation_Body = Callable[..., Any]

_KIND = "__tagkit_kind__"
_UNDERLAY = "__tagkit_underlay__"
_RIP = "__tagkit_rip__"
_MISSING = object()

# Caches keyed weakly so dynamically created Tags / functions / runtime
# types are not pinned in memory once their last live user disappears.
_declarations_cache: "WeakKeyDictionary[type, _Tag_Declarations]" = (
        WeakKeyDictionary()
        )
_underlay_cache: "WeakKeyDictionary[Callable[..., Any], bool]" = (
        WeakKeyDictionary()
        )
_protocol_spec_cache: (
        "WeakKeyDictionary[Callable[..., Any], tuple[tuple[str, ...], bool]]"
        ) = WeakKeyDictionary()
_runtime_type_cache: "WeakValueDictionary[tuple, type]" = (
        WeakValueDictionary()
        )
_exit_registry: "list[weakref.ReferenceType[object]]" = []
_verifying: "set[int]" = set()


# ============================================================
# Failures
# ============================================================


class TagError(Exception):
    """Base failure for TagKit."""


class TagCompositionError(TagError):
    """Raised when Tags cannot form a coherent Overlay."""


class TagResolutionError(TagError):
    """Raised when a required Underlay or Tag view is unavailable."""


class TagPreconditionError(TagError):
    """Raised when a Precondition prevents Tagging."""


class TagPostconditionError(TagError):
    """Raised when a Postcondition rejects a candidate Overlay."""


class TagImprintError(TagError):
    """Raised when an Imprint cannot complete."""


class TagDeletionError(TagError):
    """Raised when a deletion declaration is invalid."""


class TagContractError(TagError):
    """Raised when a condition yields a non-boolean (truthy/falsy) value."""


class TagOverwriteWarning(UserWarning):
    """Warns when an independent Tag replaces a visible contribution."""


class TagContractWarning(UserWarning):
    """Warns when a Shape weakens a Base Postcondition without @Underlay."""


# ============================================================
# Python profile declarations
# ============================================================


def _mark(
        function: Callable[..., Any],
        kind: str,
        ) -> Callable[..., Any]:
    setattr(
            function,
            _KIND,
            kind,
            )

    return function


def Action(
        function: Action,
        ) -> Action:
    """Mark a Tag method as an Agent Action.

    A bare method on a Tag is already treated as an Action, so this
    decorator is optional. It exists as the explicit, stackable form,
    e.g. ``@Action`` over ``@Underlay`` or ``@Rip``.
    """

    return _mark(
            function,
            "action",
            )


def Record(
        function: Record_Builder,
        ) -> Record_Builder:
    """Mark a Tag method as an Agent Record materializer."""

    return _mark(
            function,
            "record",
            )


def Underlay(
        function: Callable[..., Any],
        ) -> Callable[..., Any]:
    """Mark an Action or Record as extending the prior visible contribution.

    The captured prior contribution is passed as the function's second
    positional parameter under whatever name the author chooses. This is
    the explicit, preferred form of the implicit ``underlay``-named
    parameter convention, and stacks with ``@Action`` / ``@Record``::

        @Action
        @Underlay
        def Attack(agent, past):
            return "With grace " + past()
    """

    setattr(
            function,
            _UNDERLAY,
            True,
            )

    return function


def Rip(
        function: Action,
        ) -> Action:
    """Mark an Action as teardown logic that auto-runs on Rip.

    A ``@Rip`` Action runs when the Agent is extracted from the Tag's
    Field. Stacked with ``@Action`` the same function is both a normally
    callable Action and a teardown::

        @Action
        @Rip
        def Disarm(agent):
            agent.weapon = None
    """

    setattr(
            function,
            _RIP,
            True,
            )

    return function


def Imprint(
        function: Action,
        ) -> Action:
    """Mark application-time Tagging logic."""

    return _mark(
            function,
            "imprint",
            )


def Precondition(
        function: Predicate,
        ) -> Predicate:
    """Mark a predicate evaluated before a Tag Imprint."""

    return _mark(
            function,
            "precondition",
            )


def Postcondition(
        function: Predicate,
        ) -> Predicate:
    """Mark a predicate evaluated after a Tag Imprint."""

    return _mark(
            function,
            "postcondition",
            )


# `@Pre` / `@Post` are the short, canonical spellings of the conditions.
Pre = Precondition
Post = Postcondition


def Delete(
        function: Action,
        ) -> Action:
    """Mark a Tag declaration as an explicit contribution deletion."""

    return _mark(
            function,
            "delete",
            )


def Operation(
        function: Operation_Body,
        ) -> classmethod:
    """Mark a Tag-level operation and bind the Tag as its first input."""

    _mark(
            function,
            "operation",
            )

    return classmethod(function)


class Report:
    """Declare shared data belonging to a Tag."""

    def __init__(
            report,
            value: Any,
            ) -> None:
        report.value = value


# ============================================================
# Internal Tag declarations
# ============================================================


@dataclass(frozen=True)
class _Tag_Declarations:
    actions: tuple[tuple[str, Action], ...]
    records: tuple[tuple[str, Record_Builder], ...]
    imprints: tuple[Action, ...]
    preconditions: tuple[tuple[str, Predicate], ...]
    postconditions: tuple[tuple[str, Predicate], ...]
    deletions: tuple[str, ...]
    reports: tuple[tuple[str, Any], ...]
    operations: tuple[tuple[str, Operation_Body], ...]
    rips: tuple[tuple[str, Action], ...]


@dataclass
class _Tag_Snapshot:
    actions: dict[str, Action]
    records: dict[str, Any]
    reports: dict[str, Any]
    operations: dict[str, tuple[type["Tag"], Operation_Body]]
    deleted: frozenset[str]


@dataclass
class _Agent_State:
    host_type: type
    active_tags: list[type["Tag"]]
    actions: dict[str, Action]
    action_origins: dict[str, type["Tag"] | type]
    record_builders: dict[str, Record_Builder]
    record_origins: dict[str, type["Tag"] | type]
    preconditions: dict[str, Predicate]
    postconditions: dict[str, Predicate]
    reports: dict[str, Any]
    operations: dict[str, tuple[type["Tag"], Operation_Body]]
    deleted: set[str]
    snapshots: dict[type["Tag"], _Tag_Snapshot]
    rip_actions: dict[type["Tag"], tuple[tuple[str, Action], ...]]
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
                preconditions=dict(state.preconditions),
                postconditions=dict(state.postconditions),
                reports=dict(state.reports),
                operations=dict(state.operations),
                deleted=set(state.deleted),
                snapshots=dict(state.snapshots),
                rip_actions=dict(state.rip_actions),
                ever_tags=set(state.ever_tags),
                ripped=state.ripped,
                )


def _kind_of(
        attribute: Any,
        ) -> str | None:
    if isinstance(
            attribute,
            (
                classmethod,
                staticmethod,
            ),
            ):
        attribute = attribute.__func__

    return getattr(
            attribute,
            _KIND,
            None,
            )


def _is_private(
        name: str,
        ) -> bool:
    return (
            name.startswith("_")
            and not (
                name.startswith("__")
                and name.endswith("__")
                )
            )


def _dunder(
        name: str,
        ) -> bool:
    return (
            name.startswith("__")
            and name.endswith("__")
            )


def _declarations_for(
        tag: type["Tag"],
        ) -> _Tag_Declarations:
    """Return cached Tag declarations, scanned once per Tag class."""

    cached = _declarations_cache.get(tag)

    if cached is not None:
        return cached

    declarations = _build_declarations(tag)
    _declarations_cache[tag] = declarations

    return declarations


def _build_declarations(
        tag: type["Tag"],
        ) -> _Tag_Declarations:
    actions: list[tuple[str, Action]] = []
    records: list[tuple[str, Record_Builder]] = []
    imprints: list[Action] = []
    preconditions: list[tuple[str, Predicate]] = []
    postconditions: list[tuple[str, Predicate]] = []
    deletions: list[str] = []
    reports: list[tuple[str, Any]] = []
    operations: list[tuple[str, Operation_Body]] = []
    rips: list[tuple[str, Action]] = []

    for name, attribute in tag.__dict__.items():
        if _is_private(name):
            continue

        if isinstance(attribute, Report):
            reports.append(
                    (
                        name,
                        attribute.value,
                        )
                    )
            continue

        kind = _kind_of(attribute)

        if kind == "record":
            records.append(
                    (
                        name,
                        attribute,
                        )
                    )
            continue

        if kind == "imprint":
            imprints.append(attribute)
            continue

        if kind == "precondition":
            preconditions.append(
                    (
                        name,
                        attribute,
                        )
                    )
            continue

        if kind == "postcondition":
            postconditions.append(
                    (
                        name,
                        attribute,
                        )
                    )
            continue

        if kind == "delete":
            deletions.append(name)
            continue

        if kind == "operation":
            operations.append(
                    (
                        name,
                        attribute.__func__,
                        )
                    )
            continue

        is_rip = bool(
                getattr(
                        attribute,
                        _RIP,
                        False,
                        )
                )

        if (
                (kind == "action" or is_rip or kind is None)
                and callable(attribute)
                and not isinstance(
                        attribute,
                        (
                            classmethod,
                            staticmethod,
                        ),
                        )
                ):
            actions.append(
                    (
                        name,
                        attribute,
                        )
                    )

            if is_rip:
                rips.append(
                        (
                            name,
                            attribute,
                            )
                        )

    return _Tag_Declarations(
            actions=tuple(actions),
            records=tuple(records),
            imprints=tuple(imprints),
            preconditions=tuple(preconditions),
            postconditions=tuple(postconditions),
            deletions=tuple(deletions),
            reports=tuple(reports),
            operations=tuple(operations),
            rips=tuple(rips),
            )


# ============================================================
# Fields
# ============================================================


class _Field:
    """A non-owning population of Agents for one Tag."""

    def __init__(
            field,
            ) -> None:
        field._references: list[weakref.ReferenceType[object]] = []

    def Add(
            field,
            agent: object,
            ) -> None:
        for reference in field._references:
            if reference() is agent:
                return

        try:
            reference = weakref.ref(
                    agent,
                    field._Forget,
                    )
        except TypeError as error:
            raise TagCompositionError(
                    "Tagged Agents must support weak references for Fields"
                    ) from error

        field._references.append(reference)

    def Remove(
            field,
            agent: object,
            ) -> None:
        field._references = [
                reference
                for reference in field._references
                if reference() is not agent
                ]

    def _Forget(
            field,
            expired: weakref.ReferenceType[object],
            ) -> None:
        field._references = [
                reference
                for reference in field._references
                if reference is not expired
                ]

    def __iter__(
            field,
            ) -> Iterator[object]:
        agents: list[object] = []
        live: list[weakref.ReferenceType[object]] = []

        for reference in field._references:
            agent = reference()

            if agent is None:
                continue

            agents.append(agent)
            live.append(reference)

        field._references = live

        return iter(agents)


# ============================================================
# Tag relationships and runtime types
# ============================================================


def _direct_supertags_for(
        tag: type["Tag"],
        ) -> tuple[type["Tag"], ...]:
    return tuple(
            candidate
            for candidate in tag.__bases__
            if (
                isinstance(candidate, MetaTag)
                and candidate is not Tag
                )
            )


def _lineage_for(
        tag: type["Tag"],
        ) -> tuple[type["Tag"], ...]:
    lineage: list[type[Tag]] = []

    def Visit(
            candidate: type[Tag],
            ) -> None:
        for supertag in _direct_supertags_for(candidate):
            Visit(supertag)

        if candidate not in lineage:
            lineage.append(candidate)

    Visit(tag)

    return tuple(lineage)


def _leaf_tags_for(
        active_tags: list[type["Tag"]],
        ) -> tuple[type["Tag"], ...]:
    return tuple(
            candidate
            for candidate in active_tags
            if not any(
                    other is not candidate
                    and issubclass(
                            other,
                            candidate,
                            )
                    for other in active_tags
                    )
            )


def _deleted_action(
        name: str,
        ) -> Action:
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
        return type(
                class_name,
                tuple(reversed(leaves)) + host_bases,
                namespace,
                )
    except TypeError as error:
        raise TagCompositionError(
                "Tags cannot form a Python runtime type with the Target"
                ) from error


def _runtime_type_for(
        state: _Agent_State,
        ) -> type:
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
    # a pure isinstance marker depending only on (host, leaves); it is shared
    # across every Agent of that shape instead of rebuilt per application.
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
            for ancestor in _lineage_for(leaf):
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


# ============================================================
# Agent state and composed contributions
# ============================================================


def _state_for(
        agent: object,
        ) -> _Agent_State:
    try:
        return object.__getattribute__(
                agent,
                "_TAGKIT_STATE",
                )
    except AttributeError:
        host_type = type(agent)

        state = _Agent_State(
                host_type=host_type,
                active_tags=[],
                actions={},
                action_origins={},
                record_builders={},
                record_origins={},
                preconditions={},
                postconditions={},
                reports={},
                operations={},
                deleted=set(),
                snapshots={},
                rip_actions={},
                ever_tags=set(),
                )

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

        return state


def _existing_state_for(
        agent: object,
        ) -> _Agent_State | None:
    try:
        return object.__getattribute__(
                agent,
                "_TAGKIT_STATE",
                )
    except AttributeError:
        return None


def _set_state(
        agent: object,
        state: _Agent_State,
        ) -> None:
    object.__setattr__(
            agent,
            "_TAGKIT_STATE",
            state,
            )


def _takes_underlay(
        function: Callable[..., Any],
        ) -> bool:
    """Report whether a contribution extends the prior visible one.

    Only the explicit ``@Underlay`` marker counts -- there is no implicit
    parameter-name convention. The verdict is cached per function, since a
    function's declaration never changes after definition.
    """

    cached = _underlay_cache.get(function)

    if cached is not None:
        return cached

    if not getattr(
            function,
            _UNDERLAY,
            False,
            ):
        _underlay_cache[function] = False

        return False

    positional = [
            parameter
            for parameter in signature(function).parameters.values()
            if parameter.kind in (
                    Parameter.POSITIONAL_ONLY,
                    Parameter.POSITIONAL_OR_KEYWORD,
                    )
            ]

    if len(positional) < 2:
        raise TagResolutionError(
                f"{function.__qualname__} is marked @Underlay but has no"
                " second positional parameter to receive the underlay"
                )

    _underlay_cache[function] = True

    return True


def _bind_action(
        function: Action,
        underlay: Action | None,
        ) -> Action:
    uses_underlay = _takes_underlay(function)

    if uses_underlay and underlay is None:
        raise TagResolutionError(
                f"{function.__qualname__} requires a visible Underlay"
                )

    @wraps(function)
    def Call(
            agent: object,
            *args: Any,
            **kwargs: Any,
            ) -> Any:
        if not uses_underlay:
            return function(
                    agent,
                    *args,
                    **kwargs,
                    )

        def Underlay(
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
                Underlay,
                *args,
                **kwargs,
                )

    return Call


def _is_independent(
        new_tag: type["Tag"],
        prior_origin: type["Tag"] | type,
        ) -> bool:
    if not isinstance(prior_origin, MetaTag):
        return False

    return not (
            issubclass(
                    new_tag,
                    prior_origin,
                    )
            or issubclass(
                    prior_origin,
                    new_tag,
                    )
            )


def _host_action_for(
        host_type: type,
        name: str,
        ) -> Action | None:
    for provider in host_type.__mro__:
        attribute = provider.__dict__.get(name)

        if isinstance(
                attribute,
                (
                    classmethod,
                    staticmethod,
                ),
                ):
            continue

        if not callable(attribute):
            continue

        @wraps(attribute)
        def Host_Action(
                agent: object,
                *args: Any,
                _attribute: Action = attribute,
                **kwargs: Any,
                ) -> Any:
            return _attribute(
                    agent,
                    *args,
                    **kwargs,
                    )

        return Host_Action

    return None


def _remove_contribution(
        state: _Agent_State,
        name: str,
        ) -> None:
    state.actions.pop(name, None)
    state.action_origins.pop(name, None)
    state.record_builders.pop(name, None)
    state.record_origins.pop(name, None)
    state.preconditions.pop(name, None)
    state.postconditions.pop(name, None)
    state.reports.pop(name, None)
    state.operations.pop(name, None)
    state.deleted.add(name)


def _install_declarations(
        state: _Agent_State,
        tag: type["Tag"],
        declarations: _Tag_Declarations,
        ) -> None:
    for name in declarations.deletions:
        _remove_contribution(
                state,
                name,
                )

    for name, predicate in declarations.preconditions:
        state.preconditions[name] = _bind_condition(
                predicate,
                state.preconditions.get(name),
                )
        state.deleted.discard(name)

    for name, predicate in declarations.postconditions:
        prior = state.postconditions.get(name)

        if prior is not None and not _takes_underlay(predicate):
            warnings.warn(
                    f"{tag.__name__}.{name} crunches a Base Postcondition"
                    " without @Underlay (weakens a promise; see Forward-Post)",
                    TagContractWarning,
                    stacklevel=4,
                    )

        state.postconditions[name] = _bind_condition(
                predicate,
                prior,
                )
        state.deleted.discard(name)

    for name, value in declarations.reports:
        state.reports[name] = value
        state.deleted.discard(name)

    for name, operation in declarations.operations:
        state.operations[name] = (
                tag,
                operation,
                )
        state.deleted.discard(name)

    for name, function in declarations.actions:
        underlay = state.actions.get(name)
        prior_origin = state.action_origins.get(name, state.host_type)
        was_deleted = name in state.deleted

        if (
                underlay is None
                and not was_deleted
                ):
            underlay = _host_action_for(
                    state.host_type,
                    name,
                    )

        if (
                underlay is not None
                and not _takes_underlay(function)
                and _is_independent(
                        tag,
                        prior_origin,
                        )
                ):
            warnings.warn(
                    f"{tag.__name__}.{name} replaces an independent Tag Action",
                    TagOverwriteWarning,
                    stacklevel=3,
                    )

        state.actions[name] = _bind_action(
                function,
                underlay,
                )
        state.action_origins[name] = tag
        state.deleted.discard(name)

    for name, builder in declarations.records:
        state.record_builders[name] = builder
        state.record_origins[name] = tag
        state.deleted.discard(name)

    if declarations.rips:
        state.rip_actions[tag] = declarations.rips


def _spec_for(
        function: Callable[..., Any],
        skip: int,
        ) -> tuple[tuple[str, ...], bool]:
    names: list[str] = []
    accepts_var_keyword = False

    for index, parameter in enumerate(
            signature(function).parameters.values()
            ):
        if index < skip:
            continue

        if parameter.kind is Parameter.VAR_KEYWORD:
            accepts_var_keyword = True
        elif parameter.kind is Parameter.VAR_POSITIONAL:
            continue
        else:
            names.append(parameter.name)

    return (
            tuple(names),
            accepts_var_keyword,
            )


def _protocol_inputs(
        function: Callable[..., Any],
        inputs: dict[str, Any],
        skip: int = 1,
        ) -> dict[str, Any]:
    """Bind application inputs to a protocol's named parameters.

    The first ``skip`` positional parameters are bound by position -- the
    Agent, and for an @Underlay condition the underlay -- so their names are
    the author's free choice, never reserved words. Every later named
    parameter is filled from the inputs by name, defaulting to None when the
    caller did not supply it, so the application call is the single source of
    truth. A ``**kwargs`` parameter receives any remaining inputs. The common
    case (skip == 1) is cached per function.
    """

    if skip == 1:
        spec = _protocol_spec_cache.get(function)

        if spec is None:
            spec = _spec_for(function, 1)
            _protocol_spec_cache[function] = spec
    else:
        spec = _spec_for(function, skip)

    names, accepts_var_keyword = spec
    matched = {
            name: inputs.get(name)
            for name in names
            }

    if accepts_var_keyword:
        for name, value in inputs.items():
            matched.setdefault(name, value)

    return matched


def _run_protocol(
        function: Callable[..., Any],
        agent: object,
        inputs: dict[str, Any],
        ) -> Any:
    return function(
            agent,
            **_protocol_inputs(function, inputs),
            )


def _condition_verdict(
        result: Any,
        label: str,
        ) -> bool:
    """The strict boolean verdict for a condition's result.

    ``True`` or ``None`` holds; ``False`` fails. Anything else is rejected:
    TOP does not coerce truthy/falsy values, because they are not booleans (a
    Record of ``0`` slots left is a real value, not a failure). Write the
    explicit comparison you mean -- ``x != 0``, ``x > 0``, ``x is not None``.

    None -- or no return at all -- is a pass: a condition is a restriction, so
    saying nothing permits (innocent until written into law). An assert-style
    body returns None when its asserts pass and raises when one fails.
    """

    if result is True or result is None:
        return True

    if result is False:
        return False

    raise TagContractError(
            f"{label} returned {result!r} ({type(result).__name__}); a"
            " condition must yield True, False, or None. TOP does not coerce"
            " truthy / falsy values -- write an explicit comparison such as"
            " `x != 0`, `x > 0`, or `x is not None`."
            )


def _bind_condition(
        function: Predicate,
        prior: Callable[[object, dict[str, Any]], Any] | None,
        ) -> Callable[[object, dict[str, Any]], Any]:
    """Bind a condition, supplying its Underlay when marked @Underlay.

    An @Underlay condition receives, as its second positional parameter, a
    callable reporting whether the prior visible condition of the same name
    held (True / False) -- normalized so that both ``assert under()`` and
    ``return under() and ...`` compose, whatever style the Base used.
    """

    uses_underlay = _takes_underlay(function)

    if uses_underlay and prior is None:
        raise TagResolutionError(
                f"{function.__qualname__} is @Underlay but no prior"
                " condition of that name exists"
                )

    @wraps(function)
    def Check(
            agent: object,
            inputs: dict[str, Any],
            ) -> Any:
        if not uses_underlay:
            return function(
                    agent,
                    **_protocol_inputs(function, inputs, 1),
                    )

        def under() -> bool:
            try:
                return _condition_verdict(
                        prior(agent, inputs),
                        "underlay",
                        )
            except Exception:
                return False

        return function(
                agent,
                under,
                **_protocol_inputs(function, inputs, 2),
                )

    return Check


def _evaluate_conditions(
        conditions: dict[str, Callable[[object, dict[str, Any]], Any]],
        agent: object,
        failure_type: type[TagError],
        phase: str,
        inputs: dict[str, Any],
        ) -> None:
    for name, check in conditions.items():
        try:
            result = check(agent, inputs)
        except Exception as error:
            raise failure_type(
                    f"{phase} {name!r} raised {type(error).__name__}"
                    ) from error

        if not _condition_verdict(result, f"{phase} {name!r}"):
            raise failure_type(
                    f"{phase} {name!r} failed"
                    )


def _check_conditions(
        agent: object,
        scope: str,
        failure_type: type[TagError],
        phase: str,
        detailed: bool,
        ) -> bool:
    """Run an Agent's visible conditions of one ``scope`` on demand.

    ``scope`` is ``"preconditions"`` or ``"postconditions"``. Reentrancy-
    guarded: while an Agent's conditions are being checked, a nested
    ``bool(agent)`` (an ``if agent`` / ``assert agent`` inside a condition)
    returns True instead of recursing. With ``detailed`` it raises
    ``failure_type`` naming the first condition that does not hold; otherwise
    it returns a plain bool and never raises.
    """

    state = _existing_state_for(agent)

    if state is None:
        return True

    key = id(agent)

    if key in _verifying:
        return True

    _verifying.add(key)

    try:
        for name, check in getattr(state, scope).items():
            try:
                result = check(agent, {})
            except Exception as error:
                if detailed:
                    raise failure_type(
                            f"{phase} {name!r} raised"
                            f" {type(error).__name__}"
                            ) from error

                return False

            if not _condition_verdict(result, f"{phase} {name!r}"):
                if detailed:
                    raise failure_type(
                            f"{phase} {name!r} failed"
                            )

                return False

        return True
    finally:
        _verifying.discard(key)


def _scope_status(
        agent: object,
        scope: str,
        ) -> dict[str, bool]:
    """``{condition name: holds?}`` for one scope, never raising.

    A condition that fails or errors -- including a non-boolean result -- maps
    to False, so this is safe for diagnostics. Reentrancy-guarded like the
    other checks.
    """

    state = _existing_state_for(agent)

    if state is None:
        return {}

    key = id(agent)
    reentrant = key in _verifying

    if not reentrant:
        _verifying.add(key)

    out: dict[str, bool] = {}

    try:
        for name, check in getattr(state, scope).items():
            try:
                out[name] = _condition_verdict(
                        check(agent, {}),
                        name,
                        )
            except Exception:
                out[name] = False
    finally:
        if not reentrant:
            _verifying.discard(key)

    return out


def _capture_attribute(
        agent: object,
        name: str,
        ) -> tuple[bool, Any]:
    try:
        namespace = object.__getattribute__(
                agent,
                "__dict__",
                )
    except AttributeError:
        namespace = None

    if namespace is not None and name in namespace:
        return (
                True,
                namespace[name],
                )

    return (
            False,
            _MISSING,
            )


def _restore_attributes(
        agent: object,
        originals: dict[str, tuple[bool, Any]],
        ) -> None:
    for name, (was_instance_value, value) in originals.items():
        if was_instance_value:
            object.__setattr__(
                    agent,
                    name,
                    value,
                    )
            continue

        try:
            object.__delattr__(
                    agent,
                    name,
                    )
        except AttributeError:
            pass


def _record_underlay(
        agent: object,
        name: str,
        ) -> Any:
    # The current value of a Record is an Agent instance value only -- never
    # the Tag-class builder method that lives in the runtime MRO.
    try:
        namespace = object.__getattribute__(
                agent,
                "__dict__",
                )
    except AttributeError:
        return _MISSING

    if name in namespace:
        return namespace[name]

    return _MISSING


def _materialize_records(
        agent: object,
        declarations: _Tag_Declarations,
        deleted_before_tagging: set[str],
        ) -> dict[str, Any]:
    values: dict[str, Any] = {}

    for name, builder in declarations.records:
        if name in deleted_before_tagging:
            underlay = _MISSING
        else:
            underlay = _record_underlay(
                    agent,
                    name,
                    )

        if _takes_underlay(builder):
            if underlay is _MISSING:
                raise TagResolutionError(
                        f"{builder.__qualname__} requires a visible Underlay"
                        )

            value = builder(
                    agent,
                    lambda: underlay,
                    )
        else:
            value = builder(agent)

        values[name] = value

    return values


def _apply_record_values(
        agent: object,
        values: dict[str, Any],
        ) -> None:
    for name, value in values.items():
        object.__setattr__(
                agent,
                name,
                value,
                )


def _commit_deletions(
        agent: object,
        original_state: _Agent_State,
        new_state: _Agent_State,
        ) -> None:
    new_deletions = new_state.deleted - original_state.deleted

    for name in new_deletions:
        try:
            namespace = object.__getattribute__(
                    agent,
                    "__dict__",
                    )
        except AttributeError:
            namespace = None

        if namespace is None or name not in namespace:
            continue

        object.__delattr__(
                agent,
                name,
                )


def _snapshot_for(
        agent: object,
        state: _Agent_State,
        ) -> _Tag_Snapshot:
    records: dict[str, Any] = {}

    for name in state.record_builders:
        if name in state.deleted:
            continue

        value = _record_underlay(
                agent,
                name,
                )

        if value is not _MISSING:
            records[name] = value

    return _Tag_Snapshot(
            actions=dict(state.actions),
            records=records,
            reports=dict(state.reports),
            operations=dict(state.operations),
            deleted=frozenset(state.deleted),
            )


def _apply_one(
        agent: object,
        tag: type["Tag"],
        inputs: dict[str, Any] | None = None,
        ) -> object:
    """Apply one Tag (and any missing Bases) to an Agent.

    Re-applying a Tag that is already active is a strict no-op: it does not
    re-run Imprints and does not reset Records. Resetting is a deliberate
    act -- Rip the Tag, then apply it again.

    ``inputs`` are the keyword inputs from ``Tag(target, **inputs)``. Each
    Imprint, Precondition and Postcondition applied during this call receives
    the inputs whose names match its parameters; a declared parameter the
    caller did not supply is passed as None.
    """

    inputs = inputs or {}

    state = _state_for(agent)

    if tag in state.active_tags:
        return agent

    for supertag in _direct_supertags_for(tag):
        _apply_one(
                agent,
                supertag,
                inputs,
                )

    state = _state_for(agent)

    if tag in state.active_tags:
        return agent

    declarations = _declarations_for(tag)
    candidate = state.Copy()
    original_type = type(agent)

    _install_declarations(
            candidate,
            tag,
            declarations,
            )

    candidate.active_tags.append(tag)
    candidate.ever_tags.add(tag)
    next_type = _runtime_type_for(candidate)
    originals = {
            name: _capture_attribute(
                    agent,
                    name,
                    )
            for name in (
                    *declarations.deletions,
                    *(name for name, _ in declarations.records),
                    )
            }

    _set_state(
            agent,
            candidate,
            )

    try:
        _evaluate_conditions(
                candidate.preconditions,
                agent,
                TagPreconditionError,
                "Precondition",
                inputs,
                )

        for imprint in declarations.imprints:
            try:
                _run_protocol(imprint, agent, inputs)
            except Exception as error:
                raise TagImprintError(
                        f"Imprint {imprint.__qualname__} failed"
                        ) from error

        values = _materialize_records(
                agent,
                declarations,
                state.deleted,
                )

        _apply_record_values(
                agent,
                values,
                )

        _evaluate_conditions(
                candidate.postconditions,
                agent,
                TagPostconditionError,
                "Postcondition",
                inputs,
                )

        candidate.snapshots[tag] = _snapshot_for(
                agent,
                candidate,
                )

        _commit_deletions(
                agent,
                state,
                candidate,
                )

        agent.__class__ = next_type
        tag._tagkit_field.Add(agent)
    except TagError:
        _restore_attributes(
                agent,
                originals,
                )

        if type(agent) is not original_type:
            agent.__class__ = original_type

        _set_state(
                agent,
                state,
                )
        raise
    except TypeError as error:
        _restore_attributes(
                agent,
                originals,
                )

        if type(agent) is not original_type:
            agent.__class__ = original_type

        _set_state(
                agent,
                state,
                )
        raise TagCompositionError(
                f"{type(agent).__name__} cannot be actualized in place"
                ) from error

    return agent


def _capture_instance_dict(
        agent: object,
        ) -> dict[str, Any] | None:
    try:
        namespace = object.__getattribute__(
                agent,
                "__dict__",
                )
    except AttributeError:
        return None

    return {
            name: value
            for name, value in namespace.items()
            if name != "_TAGKIT_STATE"
            }


def _restore_instance_dict(
        agent: object,
        captured: dict[str, Any] | None,
        ) -> None:
    if captured is None:
        return

    try:
        namespace = object.__getattribute__(
                agent,
                "__dict__",
                )
    except AttributeError:
        return

    for name in list(namespace.keys()):
        if name == "_TAGKIT_STATE":
            continue

        del namespace[name]

    namespace.update(captured)


def _apply_transaction(
        agent: object,
        tag: type["Tag"],
        inputs: dict[str, Any] | None = None,
        ) -> object:
    """Apply one Tag as an atomic transaction.

    A single ``Tag(target, **inputs)`` call commits everything or nothing.
    If any Base pulled in by this call, or the requested Tag itself, fails,
    the Agent is restored to exactly its state at call entry. Tags committed
    by earlier calls survive untouched.
    """

    entry_state = _existing_state_for(agent)
    entry_tags = (
            tuple(entry_state.active_tags)
            if entry_state is not None
            else ()
            )
    entry_state_copy = (
            entry_state.Copy()
            if entry_state is not None
            else None
            )
    entry_dict = _capture_instance_dict(agent)
    entry_class = type(agent)

    try:
        return _apply_one(
                agent,
                tag,
                inputs,
                )
    except BaseException:
        current_state = _existing_state_for(agent)

        if current_state is not None:
            added = [
                    candidate
                    for candidate in current_state.active_tags
                    if candidate not in entry_tags
                    ]

            for candidate in added:
                candidate._tagkit_field.Remove(agent)

        _restore_instance_dict(
                agent,
                entry_dict,
                )

        if type(agent) is not entry_class:
            agent.__class__ = entry_class

        if entry_state_copy is not None:
            _set_state(
                    agent,
                    entry_state_copy,
                    )
        else:
            try:
                object.__delattr__(
                        agent,
                        "_TAGKIT_STATE",
                        )
            except AttributeError:
                pass

        raise


def _requiring_shapes(
        tag: type["Tag"],
        active_tags: list[type["Tag"]],
        ) -> tuple[type["Tag"], ...]:
    return tuple(
            other
            for other in active_tags
            if (
                other is not tag
                and issubclass(
                        other,
                        tag,
                        )
                )
            )


def _rip_one(
        agent: object,
        tag: type["Tag"],
        ) -> object:
    """Extract an Agent from one Tag's Field (the Rip protocol).

    Membership ends but contributions are sticky: Actions and Records
    remain on the Agent (a "Rogue Agent") unless the Tag declares ``@Rip``
    teardown Actions, which run after the Agent leaves the Field. Ripping
    is refused for a Base while an active Shape still requires it,
    preserving upward closure. Ripping a Tag never auto-clears its Bases.
    """

    state = _existing_state_for(agent)

    if state is None or tag not in state.active_tags:
        raise TagResolutionError(
                f"{tag.__name__} is not active on this Agent"
                )

    blocking = _requiring_shapes(
            tag,
            state.active_tags,
            )

    if blocking:
        names = ", ".join(
                shape.__name__
                for shape in blocking
                )

        raise TagCompositionError(
                f"{tag.__name__} is required by active Shape(s): {names}"
                )

    state.active_tags = [
            candidate
            for candidate in state.active_tags
            if candidate is not tag
            ]

    tag._tagkit_field.Remove(agent)

    for _name, rip in state.rip_actions.get(tag, ()):
        rip(agent)

    state.rip_actions.pop(tag, None)

    return agent


def _host_finalizer(
        runtime_type: type,
        ) -> Callable[[object], None] | None:
    """Find a host ``__del__`` shadowed by ``Tagged.__del__``, if any."""

    for klass in runtime_type.__mro__:
        if klass is Tagged:
            continue

        finalizer = klass.__dict__.get("__del__")

        if finalizer is not None:
            return finalizer

    return None


# ============================================================
# Agent-bound Tag views
# ============================================================


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
        if name in view._snapshot.deleted:
            raise AttributeError(
                    f"{view._tag.__name__} deleted {name!r}"
                    )

        if name in view._snapshot.actions:
            return MethodType(
                    view._snapshot.actions[name],
                    view._agent,
                    )

        if name in view._snapshot.records:
            return view._snapshot.records[name]

        if name in view._snapshot.reports:
            return view._snapshot.reports[name]

        if name in view._snapshot.operations:
            origin, operation = view._snapshot.operations[name]

            return partial(
                    operation,
                    origin,
                    )

        raise AttributeError(
                f"{view._tag.__name__} has no visible member {name!r}"
                )


# ============================================================
# Public TOP types
# ============================================================


class MetaTag(type):
    """Metaclass for durable semantic Tag categories."""

    def __new__(
            meta,
            name: str,
            bases: tuple[type, ...],
            namespace: dict[str, Any],
            **kwargs: Any,
            ) -> "MetaTag":
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

    def __getattribute__(
            tag,
            name: str,
            ) -> Any:
        if name == "Field":
            return type.__getattribute__(
                    tag,
                    "_tagkit_field",
                    )

        value = super().__getattribute__(name)

        if isinstance(value, Report):
            return value.value

        return value

    def __contains__(
            tag,
            candidate: object,
            ) -> bool:
        state = _existing_state_for(candidate)

        return (
                state is not None
                and tag in state.active_tags
                )

    def __iter__(
            tag,
            ) -> Iterator[object]:
        return iter(tag._tagkit_field)

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
        after extraction. Ripping is refused while an active Shape still
        requires this Tag as a Base.

        Tags are ripped; Records are removed with ``del agent.record``.
        """

        return _rip_one(
                agent,
                tag,
                )

    def __call__(
            tag,
            *args: object,
            **kwargs: object,
            ) -> object:
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


class Tag(metaclass=MetaTag):
    """Base class for TOP semantic categories."""

    NAME: ClassVar[str] = ""
    DESCRIPTION: ClassVar[str] = ""
    ABSTRACT: ClassVar[bool] = False

    @classmethod
    def Label(
            tag,
            ) -> str:
        return tag.NAME or tag.__name__

    @classmethod
    def Describe(
            tag,
            ) -> str:
        return tag.DESCRIPTION or ""

    @classmethod
    def Lineage(
            tag,
            ) -> tuple[type["Tag"], ...]:
        return _lineage_for(tag)

    @classmethod
    def Path(
            tag,
            *,
            roots: tuple[type["Tag"], ...] = (),
            ) -> tuple[type["Tag"], ...]:
        lineage = tag.Lineage()

        if not roots:
            return lineage

        for index, candidate in enumerate(lineage):
            if candidate in roots:
                return lineage[index:]

        return lineage


class Tagged:
    """Mixin supplied to an Agent after its first successful Tagging."""

    TAG_ROOTS: ClassVar[tuple[type[Tag], ...]] = ()

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
                return MethodType(
                        state.actions[name],
                        agent,
                        )

            if name in state.record_builders:
                # A Record lives only as an Agent instance value. Resolve to
                # that value, or raise -- never expose the Tag-class builder
                # method that the runtime MRO would otherwise reveal once the
                # value has been removed with ``del agent.record``.
                namespace = object.__getattribute__(
                        agent,
                        "__dict__",
                        )

                if name in namespace:
                    return namespace[name]

                raise AttributeError(
                        f"{type(agent).__name__} has no visible member {name!r}"
                        )

        return object.__getattribute__(
                agent,
                name,
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

            if snapshot is None:
                break

            return _Tag_View(
                    agent,
                    tag,
                    snapshot,
                    )

        raise AttributeError(
                f"{type(agent).__name__} has no Tag view {name!r}"
                )

    def __bool__(
            agent,
            ) -> bool:
        # Truthiness IS the boolean contract check: an Agent is truthy exactly
        # when its visible Postconditions hold, so `if agent` / `assert agent`
        # read as "if the agent's conditions hold". Never raises (reentrancy-
        # guarded); use Contract.Postconditions(agent) for the named failure.
        return _check_conditions(
                agent,
                "postconditions",
                TagPostconditionError,
                "Postcondition",
                False,
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
                    for _name, rip in state.rip_actions.get(tag, ()):
                        try:
                            rip(agent)
                        except Exception:
                            pass

            finalizer = _host_finalizer(type(agent))

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
        for tag in tags:
            if not isinstance(tag, MetaTag):
                raise TypeError(
                        f"{tag!r} is not a Tag class"
                        )

            _apply_transaction(
                    agent,
                    tag,
                    )

        return agent

    def With(
            agent,
            *tags: type[Tag],
            ) -> "Tagged":
        return agent.ApplyTags(
                *tags,
                )

    def As(
            agent,
            *tags: type[Tag],
            ) -> "Tagged":
        return agent.ApplyTags(
                *tags,
                )

    def __or__(
            agent,
            tag: type[Tag],
            ) -> "Tagged":
        return agent.ApplyTags(tag)

    def __ior__(
            agent,
            tag: type[Tag],
            ) -> "Tagged":
        return agent.ApplyTags(tag)

    def Tag(
            agent,
            tag: type[Tag],
            ) -> _Tag_View:
        state = _state_for(agent)

        if tag not in state.active_tags:
            raise TagResolutionError(
                    f"{tag.__name__} is not active on this Agent"
                    )

        return _Tag_View(
                agent,
                tag,
                state.snapshots[tag],
                )

    def Tags(
            agent,
            ) -> tuple[type[Tag], ...]:
        return tuple(
                reversed(
                        _leaf_tags_for(
                                _state_for(agent).active_tags
                                )
                        )
                )

    def TagPaths(
            agent,
            ) -> tuple[tuple[type[Tag], ...], ...]:
        state = _state_for(agent)
        roots = getattr(
                state.host_type,
                "TAG_ROOTS",
                (),
                )

        return tuple(
                tag.Path(
                        roots=roots,
                        )
                for tag in _leaf_tags_for(state.active_tags)
                )

    def TagTree(
            agent,
            ) -> dict[type[Tag], dict[Any, Any]]:
        tree: dict[type[Tag], dict[Any, Any]] = {}

        for path in agent.TagPaths():
            cursor = tree

            for tag in path:
                cursor = cursor.setdefault(
                        tag,
                        {},
                        )

        return tree

    def Outline(
            agent,
            *,
            indent: str = "  ",
            ) -> str:
        state = _state_for(agent)
        lines = [state.host_type.__name__]

        def Visit(
                tree: dict[type[Tag], dict[Any, Any]],
                depth: int,
                ) -> None:
            for tag, children in tree.items():
                lines.append(
                        f"{indent * depth}{tag.Label()}"
                        )
                Visit(
                        children,
                        depth + 1,
                        )

        Visit(
                agent.TagTree(),
                1,
                )

        return "\n".join(lines)

    def Has(
            agent,
            *probes: object,
            ) -> bool:
        return all(
                probe in agent
                for probe in probes
                )

    def __contains__(
            agent,
            probe: object,
            ) -> bool:
        state = _state_for(agent)

        if isinstance(probe, MetaTag):
            return probe in state.active_tags

        if isinstance(probe, str):
            return any(
                    tag.Label().casefold() == probe.casefold()
                    for tag in state.active_tags
                    )

        # A contribution declaration, e.g. `Wizard.spell_slots in agent`:
        # does the Agent currently carry that Record or Action, by name?
        name = getattr(probe, "__name__", None)

        if name and callable(probe):
            if name in state.actions:
                return True

            try:
                namespace = object.__getattribute__(agent, "__dict__")
            except AttributeError:
                namespace = {}

            return name in namespace

        return False


# ============================================================
# Exit protocols
# ============================================================


@contextmanager
def Scope(
        agent: object,
        *tags: type[Tag],
        ) -> Iterator[object]:
    """Apply Tags for a block, guaranteeing a Rip on exit.

    Tags are applied on entry and Ripped in reverse order on exit -- even
    if the block raises -- so teardown runs deterministically. This is the
    guaranteed counterpart to the best-effort ``__del__`` extraction::

        with Scope(agent, Sentry):
            guard_the_gate(agent)
        # Sentry teardown has run here, exception or not.
    """

    applied: list[type[Tag]] = []

    try:
        for tag in tags:
            tag(agent)
            applied.append(tag)

        yield agent
    finally:
        for tag in reversed(applied):
            try:
                tag.Rip(agent)
            except TagError:
                pass


class Contract:
    """The named, on-demand contract checks for an Agent.

    ``bool(agent)`` / ``if agent`` / ``assert agent`` give the boolean form of
    the Postconditions. ``Contract`` gives the form that *names the culprit*:
    each method runs the relevant visible conditions and raises -- naming the
    first that does not hold -- or returns True. It is a namespace of
    language-level operations *on* the Agent, not a feature of the Agent and
    not a Tag method.

        Contract.Postconditions(agent)   # the promises hold, or raise naming one
        Contract.Preconditions(agent)    # the entry gates still hold, or raise
        Contract.Conditions(agent)       # both, Pre then Post
    """

    @staticmethod
    def Postconditions(
            agent: object,
            ) -> bool:
        return _check_conditions(
                agent,
                "postconditions",
                TagPostconditionError,
                "Postcondition",
                True,
                )

    @staticmethod
    def Preconditions(
            agent: object,
            ) -> bool:
        return _check_conditions(
                agent,
                "preconditions",
                TagPreconditionError,
                "Precondition",
                True,
                )

    @staticmethod
    def Conditions(
            agent: object,
            ) -> bool:
        Contract.Preconditions(agent)
        Contract.Postconditions(agent)

        return True

    @staticmethod
    def Status(
            agent: object,
            ) -> dict[str, bool]:
        """Return ``{condition name: does it hold?}`` for every visible
        condition (Preconditions then Postconditions) -- the diagnostic
        primitive.

        Each is evaluated against the Agent's current state. It never raises:
        a condition that fails or errors maps to False. Build any view you
        like from this dict; Display is one.
        """

        return {
                **_scope_status(agent, "preconditions"),
                **_scope_status(agent, "postconditions"),
                }

    @staticmethod
    def Display(
            agent: object,
            ) -> str:
        """A human-readable rendering of ``Status``, with Preconditions and
        Postconditions in separate sections, one marked line each.
        ``print(Contract.Display(agent))`` to eyeball a contract while
        debugging.
        """

        # The full composed runtime-type name -- e.g. "Hero__Wizard" -- is the
        # explicit form: it shows the host and the active leaf Tags at a glance.
        title = type(agent).__name__

        pre = _scope_status(agent, "preconditions")
        post = _scope_status(agent, "postconditions")

        if not pre and not post:
            return f"{title}: no conditions"

        lines = [f"{title} contract:"]

        for heading, scope in (
                ("Pre", pre),
                ("Post", post),
                ):
            if not scope:
                continue

            lines.append(f"  {heading}:")

            for name, holds in scope.items():
                lines.append(
                        f"    {'OK ' if holds else 'XX '} {name}"
                        )

        return "\n".join(lines)


def At_Exit(
        agent: object,
        ) -> object:
    """Register an Agent's @Rip teardown to also run at interpreter exit.

    The registration is weak and never keeps the Agent alive. At a normal
    exit, any still-active @Rip teardown runs once (best-effort). This
    complements ``__del__``, which Python does not guarantee at shutdown.
    """

    _exit_registry.append(
            weakref.ref(agent)
            )

    return agent


def _run_exit_protocols() -> None:
    for reference in _exit_registry:
        agent = reference()

        if agent is None:
            continue

        state = _existing_state_for(agent)

        if state is None or state.ripped:
            continue

        state.ripped = True

        for tag in reversed(state.active_tags):
            for _name, rip in state.rip_actions.get(tag, ()):
                try:
                    rip(agent)
                except Exception:
                    pass


atexit.register(_run_exit_protocols)


__all__ = [
        "Action",
        "At_Exit",
        "Contract",
        "Delete",
        "Imprint",
        "Operation",
        "Post",
        "Postcondition",
        "Pre",
        "Precondition",
        "Record",
        "Report",
        "Rip",
        "Scope",
        "Tag",
        "TagCompositionError",
        "TagContractError",
        "TagContractWarning",
        "TagDeletionError",
        "TagError",
        "TagImprintError",
        "TagOverwriteWarning",
        "TagPostconditionError",
        "TagPreconditionError",
        "TagResolutionError",
        "Tagged",
        "Underlay",
        ]
