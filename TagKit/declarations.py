from __future__ import annotations

"""Tag contribution declarations and protocol invocation."""

from dataclasses import dataclass
from functools import wraps
from inspect import Parameter
from inspect import isasyncgen
from inspect import isawaitable
from inspect import isgenerator
from inspect import signature
from types import FunctionType
from typing import Any
from typing import Callable
from typing import ParamSpec
from typing import Protocol
from typing import TypeVar
from typing import cast
from weakref import WeakKeyDictionary

from .errors import TagCompositionError
from .errors import TagResolutionError


Action_Body = Callable[..., Any]
Predicate = Callable[..., bool | None]
Record_Builder = Callable[..., Any]
Operation_Body = Callable[..., Any]
Parameters = ParamSpec(
        "Parameters",
        )
Result = TypeVar(
        "Result",
        )
Target = TypeVar(
        "Target",
        )

_KIND = "__tagkit_kind__"
_UNDERLAY = "__tagkit_underlay__"
_RIP = "__tagkit_rip__"
_MISSING = object()

_declarations_cache = WeakKeyDictionary()
_underlay_cache = WeakKeyDictionary()
_protocol_spec_cache = WeakKeyDictionary()


class _Class_Method(
        Protocol[Parameters, Result],
        ):
    @property
    def __func__(
            descriptor,
            ) -> Callable[Parameters, Result]:
        ...

    def __get__(
            descriptor,
            instance: object,
            owner: type | None = None,
            ) -> Callable[..., Result]:
        ...


def _mark(
        function: Callable[Parameters, Result],
        kind: str,
        ) -> Callable[Parameters, Result]:
    contribution = _adapt_contribution(
            function,
            )

    setattr(
            contribution,
            _KIND,
            kind,
            )

    return contribution


def _adapt_contribution(
        function: Callable[Parameters, Result],
        ) -> Callable[Parameters, Result]:
    """Return an independently markable adapter for a callable."""

    if isinstance(
            function,
            FunctionType,
            ):
        contribution = FunctionType(
                function.__code__,
                function.__globals__,
                function.__name__,
                function.__defaults__,
                function.__closure__,
                )
        contribution = wraps(function)(
                contribution
                )
        contribution.__kwdefaults__ = (
                dict(function.__kwdefaults__)
                if function.__kwdefaults__ is not None
                else None
                )
        contribution.__annotations__ = dict(
                function.__annotations__
                )

        return cast(
                Callable[Parameters, Result],
                contribution,
                )

    @wraps(function)
    def Contribution(
            *args: Parameters.args,
            **kwargs: Parameters.kwargs,
            ) -> Result:
        return function(
                *args,
                **kwargs,
                )

    return Contribution


def Action(
        function: Callable[Parameters, Result],
        ) -> Callable[Parameters, Result]:
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
        function: Callable[Parameters, Result],
        ) -> Callable[Parameters, Result]:
    """Mark a Tag method as an Agent Record materializer."""

    return _mark(
            function,
            "record",
            )


def Underlay(
        function: Callable[Parameters, Result],
        ) -> Callable[Parameters, Result]:
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

    contribution = _adapt_contribution(
            function,
            )

    setattr(
            contribution,
            _UNDERLAY,
            True,
            )

    return contribution


def Rip(
        function: Callable[Parameters, Result],
        ) -> Callable[Parameters, Result]:
    """Mark an Action as teardown logic that auto-runs on Rip.

    A ``@Rip`` Action runs when the Agent is extracted from the Tag's
    Field. Stacked with ``@Action`` the same function is both a normally
    callable Action and a teardown::

        @Action
        @Rip
        def Disarm(agent):
            agent.weapon = None
    """

    contribution = _adapt_contribution(
            function,
            )

    setattr(
            contribution,
            _RIP,
            True,
            )

    return contribution


def Imprint(
        function: Callable[Parameters, Result],
        ) -> Callable[Parameters, Result]:
    """Mark application-time Tagging logic."""

    return _mark(
            function,
            "imprint",
            )


def Precondition(
        function: Callable[Parameters, Result],
        ) -> Callable[Parameters, Result]:
    """Mark a predicate evaluated before a Tag Imprint."""

    return _mark(
            function,
            "precondition",
            )


def Postcondition(
        function: Callable[Parameters, Result],
        ) -> Callable[Parameters, Result]:
    """Mark a predicate evaluated after a Tag Imprint."""

    return _mark(
            function,
            "postcondition",
            )



Pre = Precondition
Post = Postcondition


def Delete(
        function: Callable[Parameters, Result],
        ) -> Callable[Parameters, Result]:
    """Mark a Tag declaration as an explicit contribution deletion."""

    return _mark(
            function,
            "delete",
            )


def Operation(
        function: Callable[Parameters, Result],
        ) -> _Class_Method[Parameters, Result]:
    """Mark a Tag-level operation and bind the Tag as its first input."""

    operation = _mark(
            function,
            "operation",
            )

    return cast(
            _Class_Method[Parameters, Result],
            classmethod(operation),
            )


class Report:
    """Explicitly mark shared data belonging to a Tag."""

    def __init__(
            report,
            value: Any,
            ) -> None:
        report.value = value


def _report_value(
        name: str,
        attribute: Any,
        ) -> Any:
    """Return public Tag data in its Report form."""

    if isinstance(
            attribute,
            Report,
            ):
        return attribute.value

    if (
            name.startswith("_")
            or _kind_of(attribute) is not None
            or isinstance(
                    attribute,
                    (
                        classmethod,
                        staticmethod,
                        ),
                    )
            or hasattr(
                    attribute,
                    "__get__",
                    )
            or callable(attribute)
            ):
        return _MISSING

    return attribute


@dataclass(
        frozen=True,
        slots=True,
        )
class _Tag_Declarations:
    actions: tuple[tuple[str, Action_Body], ...]
    records: tuple[tuple[str, Record_Builder], ...]
    imprints: tuple[Action_Body, ...]
    preconditions: tuple[tuple[str, Predicate], ...]
    postconditions: tuple[tuple[str, Predicate], ...]
    deletions: tuple[str, ...]
    reports: tuple[tuple[str, Any], ...]
    operations: tuple[tuple[str, Operation_Body], ...]
    rips: tuple[tuple[str, Action_Body], ...]


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
    actions: list[tuple[str, Action_Body]] = []
    records: list[tuple[str, Record_Builder]] = []
    imprints: list[Action_Body] = []
    preconditions: list[tuple[str, Predicate]] = []
    postconditions: list[tuple[str, Predicate]] = []
    deletions: list[str] = []
    reports: list[tuple[str, Any]] = []
    operations: list[tuple[str, Operation_Body]] = []
    rips: list[tuple[str, Action_Body]] = []

    for name, attribute in tag.__dict__.items():
        if _is_private(name):
            continue

        report_value = _report_value(
                name,
                attribute,
                )

        if report_value is not _MISSING:
            reports.append(
                    (
                        name,
                        report_value,
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


def _takes_underlay(
        function: Callable[..., Any],
        ) -> bool:
    """Report whether a contribution extends the prior visible one.

    Only the explicit ``@Underlay`` marker counts -- there is no implicit
    parameter-name convention. The verdict is cached per function, since a
    function's declaration never changes after definition.
    """

    try:
        cached = _underlay_cache.get(function)
    except TypeError:
        cached = None

    if cached is not None:
        return cached

    if not getattr(
            function,
            _UNDERLAY,
            False,
            ):
        try:
            _underlay_cache[function] = False
        except TypeError:
            pass

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

    try:
        _underlay_cache[function] = True
    except TypeError:
        pass

    return True


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
        try:
            spec = _protocol_spec_cache.get(function)
        except TypeError:
            spec = None

        if spec is None:
            spec = _spec_for(function, 1)

            try:
                _protocol_spec_cache[function] = spec
            except TypeError:
                pass
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
    result = function(
            agent,
            **_protocol_inputs(function, inputs),
            )

    return _require_synchronous_result(
            result,
            f"Protocol {function.__qualname__}",
            )


def _discard_awaitable(
        result: object,
        ) -> None:
    close = getattr(
            result,
            "close",
            None,
            )

    if callable(close):
        close()

        return

    cancel = getattr(
            result,
            "cancel",
            None,
            )

    if callable(cancel):
        cancel()


def _require_synchronous_result(
        result: Any,
        label: str,
        *,
        allow_generator: bool = False,
        ) -> Any:
    if isawaitable(result):
        _discard_awaitable(result)

        raise TagCompositionError(
                f"{label} returned an awaitable; Tag application protocols"
                " are synchronous. Keep async behavior in Actions or"
                " Operations."
                )

    if isasyncgen(result):
        raise TagCompositionError(
                f"{label} returned an async generator; its body cannot run"
                " in a synchronous Tag application protocol. Keep streaming"
                " behavior in Actions or Operations."
                )

    if (
            isgenerator(result)
            and not allow_generator
            ):
        result.close()

        raise TagCompositionError(
                f"{label} returned a generator; its body cannot run in a"
                " synchronous Tag application protocol. Keep streaming"
                " behavior in Actions or Operations."
                )

    return result
