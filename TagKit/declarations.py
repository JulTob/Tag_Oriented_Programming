"""Declarations: the marks an author puts on a Tag, and how they are read.

Agent scope:  @Action, @Record          (external by default, @Secret hides)
Tag scope:    @Operation, Report(...)   (internal by default, Public publishes)
Protocols:    @Imprint, @Pre, @Post, @Rip, @Delete
Composition:  @Underlay                 (extend the prior visible contribution)

A Tag class is scanned once; the result is cached per class.
"""

from __future__ import annotations

from dataclasses import dataclass
from inspect import Parameter
from inspect import signature
from typing import Any
from typing import Callable
from weakref import WeakKeyDictionary

from .errors import TagDeclarationError


_KIND = "__tagkit_kind__"
_UNDERLAY = "__tagkit_underlay__"
_RIP = "__tagkit_rip__"
_SECRET = "__tagkit_secret__"
_PUBLIC = "__tagkit_public__"

_MISSING = object()

Function = Callable[..., Any]


# ------------------------------------------------------------------
# Marks
# ------------------------------------------------------------------


def _mark(
        function: Function,
        kind: str,
        ) -> Function:
    setattr(
            function,
            _KIND,
            kind,
            )

    return function


def _flag(
        target: Any,
        name: str,
        ) -> Any:
    function = getattr(
            target,
            "__func__",
            target,
            )
    setattr(
            function,
            name,
            True,
            )

    return target


def Action(
        function: Function,
        ) -> Function:
    """Agent behaviour. A bare method on a Tag is already an Action; this
    is the explicit, stackable spelling."""

    return _mark(
            function,
            "action",
            )


def Record(
        function: Function,
        ) -> Function:
    """Agent state. The builder runs at tagging and its value is stored on
    the Agent. A second positional parameter receives the value already
    stored under that name, or None when there is none::

        @Record
        def spells(agent, stored):
            return (stored or []) + ["Fireball"]
    """

    return _mark(
            function,
            "record",
            )


def Underlay(
        function: Function,
        ) -> Function:
    """Extend the prior visible contribution of the same name.

    For an Action or a condition the second positional parameter receives a
    callable that runs the prior contribution. For a Record the second
    positional parameter receives the stored value (the mark is optional
    there; the parameter alone is enough).
    """

    return _flag(
            function,
            _UNDERLAY,
            )


def Rip(
        function: Function,
        ) -> Function:
    """Teardown. Runs when the Agent leaves the Tag's Field. It is also a
    normally callable Action."""

    return _flag(
            function,
            _RIP,
            )


def Imprint(
        function: Function,
        ) -> Function:
    """Work performed after the Tag has applied."""

    return _mark(
            function,
            "imprint",
            )


def Precondition(
        function: Function,
        ) -> Function:
    """A gate on the incoming Agent. Evaluated before the Tag applies."""

    return _mark(
            function,
            "precondition",
            )


def Postcondition(
        function: Function,
        ) -> Function:
    """A promise about the finished Agent. Evaluated after every Tagging."""

    return _mark(
            function,
            "postcondition",
            )


Pre = Precondition
Post = Postcondition


def Delete(
        function: Function,
        ) -> Function:
    """Remove a visible contribution (or host member) by name."""

    return _mark(
            function,
            "delete",
            )


def Operation(
        function: Function,
        ) -> classmethod:
    """Tag behaviour. The Tag is its first input."""

    _mark(
            function,
            "operation",
            )

    return classmethod(function)


def Secret(
        function: Function,
        ) -> Function:
    """Hide an Action or Record from code outside composition."""

    return _flag(
            function,
            _SECRET,
            )


def Public(
        member: Any,
        ) -> Any:
    """Publish a Report or Operation on the Agent, as a read-only name or
    as an Action that forwards to the Operation with the Agent as its
    second input."""

    if isinstance(member, Report):
        member.public = True

        return member

    return _flag(
            member,
            _PUBLIC,
            )


class Report:
    """Shared data belonging to a Tag. Reads as its value on the Tag."""

    def __init__(
            report,
            value: Any,
            ) -> None:
        report.value = value
        report.public = False

    def __get__(
            report,
            instance: object,
            owner: type | None = None,
            ) -> Any:
        return report.value

    def __repr__(
            report,
            ) -> str:
        return f"Report({report.value!r})"


# ------------------------------------------------------------------
# Scanning a Tag class
# ------------------------------------------------------------------


@dataclass(frozen=True)
class _Declarations:
    actions: tuple[tuple[str, Function], ...]
    records: tuple[tuple[str, Function], ...]
    secrets: frozenset[str]
    imprints: tuple[Function, ...]
    preconditions: tuple[tuple[str, Function], ...]
    postconditions: tuple[tuple[str, Function], ...]
    deletions: tuple[str, ...]
    reports: tuple[tuple[str, Any, bool], ...]
    operations: tuple[tuple[str, Function, bool], ...]
    rips: tuple[str, ...]
    dunders: frozenset[str]


_scan_cache: "WeakKeyDictionary[type, _Declarations]" = WeakKeyDictionary()


def _declarations_of(
        tag: type,
        ) -> _Declarations:
    cached = _scan_cache.get(tag)

    if cached is None:
        cached = _scan(tag)
        _scan_cache[tag] = cached

    return cached


def _is_private(
        name: str,
        ) -> bool:
    return (
            name.startswith("_")
            and not _is_dunder(name)
            )


def _is_dunder(
        name: str,
        ) -> bool:
    return (
            name.startswith("__")
            and name.endswith("__")
            )


def _kind_of(
        attribute: Any,
        ) -> str | None:
    function = getattr(
            attribute,
            "__func__",
            attribute,
            )

    return getattr(
            function,
            _KIND,
            None,
            )


def _has_flag(
        attribute: Any,
        name: str,
        ) -> bool:
    function = getattr(
            attribute,
            "__func__",
            attribute,
            )

    return bool(
            getattr(
                    function,
                    name,
                    False,
                    )
            )


def _scan(
        tag: type,
        ) -> _Declarations:
    actions: list[tuple[str, Function]] = []
    records: list[tuple[str, Function]] = []
    secrets: set[str] = set()
    imprints: list[Function] = []
    preconditions: list[tuple[str, Function]] = []
    postconditions: list[tuple[str, Function]] = []
    deletions: list[str] = []
    reports: list[tuple[str, Any, bool]] = []
    operations: list[tuple[str, Function, bool]] = []
    rips: list[str] = []
    dunders: set[str] = set()

    for name, attribute in tag.__dict__.items():
        if _is_private(name):
            continue

        if isinstance(attribute, Report):
            reports.append(
                    (
                        name,
                        attribute.value,
                        attribute.public,
                        )
                    )
            continue

        kind = _kind_of(attribute)
        secret = _has_flag(attribute, _SECRET)
        public = _has_flag(attribute, _PUBLIC)

        if kind == "operation":
            _reject_secret(tag, name, secret)
            operations.append(
                    (
                        name,
                        attribute.__func__,
                        public,
                        )
                    )
            continue

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

        if kind == "record":
            _reject_public(tag, name, public)
            records.append(
                    (
                        name,
                        attribute,
                        )
                    )

            if secret:
                secrets.add(name)

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

        # Anything else callable is an Action (kind "action" or unmarked).
        _reject_public(tag, name, public)
        actions.append(
                (
                    name,
                    attribute,
                    )
                )

        if secret:
            secrets.add(name)

        if _has_flag(attribute, _RIP):
            rips.append(name)

        if _is_dunder(name):
            dunders.add(name)

    return _Declarations(
            actions=tuple(actions),
            records=tuple(records),
            secrets=frozenset(secrets),
            imprints=tuple(imprints),
            preconditions=tuple(preconditions),
            postconditions=tuple(postconditions),
            deletions=tuple(deletions),
            reports=tuple(reports),
            operations=tuple(operations),
            rips=tuple(rips),
            dunders=frozenset(dunders),
            )


def _reject_secret(
        tag: type,
        name: str,
        secret: bool,
        ) -> None:
    if secret:
        raise TagDeclarationError(
                f"{tag.__name__}.{name}: @Secret applies to Actions and"
                " Records only; Tag members are internal already"
                )


def _reject_public(
        tag: type,
        name: str,
        public: bool,
        ) -> None:
    if public:
        raise TagDeclarationError(
                f"{tag.__name__}.{name}: Public applies to Reports and"
                " Operations only; Agent members are external already"
                )


# ------------------------------------------------------------------
# Parameters
# ------------------------------------------------------------------


@dataclass(frozen=True)
class _Parameters:
    positional: int
    named: tuple[tuple[str, bool], ...]
    var_keyword: bool


_parameter_cache: "WeakKeyDictionary[Function, _Parameters]" = (
        WeakKeyDictionary()
        )


def _parameters_of(
        function: Function,
        ) -> _Parameters:
    cached = _parameter_cache.get(function)

    if cached is not None:
        return cached

    positional = 0
    named: list[tuple[str, bool]] = []
    var_keyword = False

    for parameter in signature(function).parameters.values():
        if parameter.kind is Parameter.VAR_KEYWORD:
            var_keyword = True
        elif parameter.kind is Parameter.VAR_POSITIONAL:
            continue
        else:
            positional += 1
            named.append(
                    (
                        parameter.name,
                        parameter.default is not Parameter.empty,
                        )
                    )

    spec = _Parameters(
            positional=positional,
            named=tuple(named),
            var_keyword=var_keyword,
            )
    _parameter_cache[function] = spec

    return spec


def _takes_underlay(
        function: Function,
        ) -> bool:
    """An Action or condition extends the prior contribution when marked
    @Underlay. The mark requires a second positional parameter."""

    if not _has_flag(function, _UNDERLAY):
        return False

    if _parameters_of(function).positional < 2:
        raise TagDeclarationError(
                f"{function.__qualname__} is marked @Underlay but has no"
                " second positional parameter to receive the underlay"
                )

    return True


def _takes_stored(
        function: Function,
        ) -> bool:
    """A Record builder receives the stored value when it declares a second
    positional parameter (the @Underlay mark is accepted as documentation)."""

    return _parameters_of(function).positional >= 2


def _protocol_inputs(
        function: Function,
        inputs: dict[str, Any],
        skip: int,
        ) -> dict[str, Any]:
    """Bind application inputs to a protocol's named parameters.

    The first ``skip`` positional parameters are bound by position (the
    Agent, and an underlay when present), so their names are the author's
    choice. Later parameters are filled from ``inputs`` by name. A parameter
    the caller did not supply keeps its own default, or receives None when
    it has none. ``**kwargs`` receives any remaining inputs.
    """

    spec = _parameters_of(function)
    bound: dict[str, Any] = {}

    for index, (name, has_default) in enumerate(spec.named):
        if index < skip:
            continue

        if name in inputs:
            bound[name] = inputs[name]
        elif not has_default:
            bound[name] = None

    if spec.var_keyword:
        for name, value in inputs.items():
            bound.setdefault(
                    name,
                    value,
                    )

    return bound
