"""Contracts: Preconditions gate the incoming Agent, Postconditions
promise about the finished one.

A condition is strictly boolean: True or a fall-through (None) holds,
False fails, anything else is rejected. An assert-style body fails by
raising.
"""

from __future__ import annotations

from typing import Any
from typing import Callable
from typing import Iterable

from .declarations import _protocol_inputs
from .declarations import _takes_underlay
from .errors import TagContractError
from .errors import TagError
from .errors import TagPostconditionError
from .errors import TagPreconditionError
from .geometry import _leaves
from .state import _State
from .state import _state_of


Check = Callable[[object, dict[str, Any]], Any]


def _verdict(
        result: Any,
        label: str,
        ) -> bool:
    if result is True or result is None:
        return True

    if result is False:
        return False

    raise TagContractError(
            f"{label} returned {result!r} ({type(result).__name__}); a"
            " condition must yield True, False, or None. TOP does not"
            " coerce truthy / falsy values: write the comparison you mean,"
            " such as `x != 0`, `x > 0`, or `x is not None`."
            )


def _bind_condition(
        function: Callable[..., Any],
        prior: Check | None,
        with_inputs: bool,
        ) -> Check:
    """Bind one condition, giving it its Underlay when marked.

    The Underlay is a callable reporting whether the prior condition of the
    same name holds (True / False), so ``assert base()`` and
    ``return base() and ...`` both compose.
    """

    uses_underlay = _takes_underlay(function)

    if uses_underlay and prior is None:
        from .errors import TagResolutionError

        raise TagResolutionError(
                f"{function.__qualname__} is @Underlay but no prior"
                " condition of that name is visible"
                )

    skip = 2 if uses_underlay else 1

    def Check(
            agent: object,
            inputs: dict[str, Any],
            ) -> Any:
        named = (
                _protocol_inputs(function, inputs, skip)
                if with_inputs
                else {}
                )

        if not uses_underlay:
            return function(
                    agent,
                    **named,
                    )

        def base() -> bool:
            try:
                return _verdict(
                        prior(agent, inputs),
                        "underlay",
                        )
            except Exception:
                return False

        return function(
                agent,
                base,
                **named,
                )

    return Check


def _evaluate(
        checks: Iterable[tuple[str, Check]],
        agent: object,
        inputs: dict[str, Any],
        failure: type[TagError],
        phase: str,
        ) -> None:
    """Run conditions; raise ``failure`` naming the first that does not hold."""

    for name, check in checks:
        try:
            result = check(agent, inputs)
        except TagContractError:
            raise
        except Exception as error:
            raise failure(
                    f"{phase} {name!r} raised {type(error).__name__}: {error}"
                    ) from error

        if not _verdict(result, f"{phase} {name!r}"):
            raise failure(
                    f"{phase} {name!r} failed"
                    )


def _guarded(
        agent: object,
        scope: str,
        detailed: bool,
        failure: type[TagError],
        phase: str,
        ) -> bool:
    """Run one scope of the Agent's visible conditions on demand.

    Re-entrancy guarded: a nested ``bool(agent)`` inside a condition
    answers True instead of recursing.
    """

    state = _state_of(agent)

    if state is None or state.checking:
        return True

    state.checking = True
    state.composing += 1

    try:
        checks = getattr(state, scope).items()

        if detailed:
            _evaluate(
                    checks,
                    agent,
                    {},
                    failure,
                    phase,
                    )

            return True

        for name, check in checks:
            try:
                if not _verdict(check(agent, {}), name):
                    return False
            except Exception:
                return False

        return True
    finally:
        state.composing -= 1
        state.checking = False


def _holds(
        agent: object,
        ) -> bool:
    """True exactly when every visible Postcondition holds."""

    return _guarded(
            agent,
            "postconditions",
            False,
            TagPostconditionError,
            "Postcondition",
            )


def _status_of(
        agent: object,
        scope: str,
        ) -> dict[str, bool]:
    state = _state_of(agent)

    if state is None:
        return {}

    reentrant = state.checking
    state.checking = True
    state.composing += 1
    status: dict[str, bool] = {}

    try:
        for name, check in getattr(state, scope).items():
            try:
                status[name] = _verdict(
                        check(agent, {}),
                        name,
                        )
            except Exception:
                status[name] = False
    finally:
        state.composing -= 1
        state.checking = reentrant

    return status


def _title_of(
        agent: object,
        ) -> str:
    state = _state_of(agent)
    host = type(agent).__name__

    if state is None or not state.active:
        return host

    leaves = ", ".join(
            tag.__name__
            for tag in _leaves(state.active)
            )

    return f"{host}[{leaves}]"


class Contract:
    """Named, on-demand contract checks for an Agent.

    ``bool(agent)`` is the boolean form. ``Contract`` names the culprit.
    """

    @staticmethod
    def Holds(
            agent: object,
            ) -> bool:
        return _holds(agent)

    @staticmethod
    def Postconditions(
            agent: object,
            ) -> bool:
        return _guarded(
                agent,
                "postconditions",
                True,
                TagPostconditionError,
                "Postcondition",
                )

    @staticmethod
    def Preconditions(
            agent: object,
            ) -> bool:
        return _guarded(
                agent,
                "preconditions",
                True,
                TagPreconditionError,
                "Precondition",
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
        """``{condition: holds?}`` for every visible condition, never raising."""

        return {
                **_status_of(agent, "preconditions"),
                **_status_of(agent, "postconditions"),
                }

    @staticmethod
    def Display(
            agent: object,
            ) -> str:
        title = _title_of(agent)
        pre = _status_of(agent, "preconditions")
        post = _status_of(agent, "postconditions")

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
                        f"    {'OK' if holds else 'XX'}  {name}"
                        )

        return "\n".join(lines)
