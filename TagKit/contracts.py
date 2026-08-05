from __future__ import annotations

"""Tagging Preconditions, Postconditions, and diagnostics."""

from contextvars import ContextVar
from functools import wraps
from inspect import isasyncgen
from inspect import isawaitable
from inspect import isgenerator
from typing import Any
from typing import Callable

from .declarations import Predicate
from .declarations import _discard_awaitable
from .declarations import _protocol_inputs
from .declarations import _takes_underlay
from .errors import TagContractError
from .errors import TagError
from .errors import TagPostconditionError
from .errors import TagPreconditionError
from .errors import TagResolutionError
from .runtime_types import _existing_state_for


_verifying = ContextVar(
        "tagkit_verifying",
        default=frozenset(),
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

    if (
            isawaitable(result)
            or isasyncgen(result)
            or isgenerator(result)
            ):
        if not isasyncgen(result):
            _discard_awaitable(result)

        kind = (
                "awaitable"
                if isawaitable(result)
                else (
                    "async generator"
                    if isasyncgen(result)
                    else "generator"
                    )
                )
        article = (
                "an"
                if kind != "generator"
                else "a"
                )

        raise TagContractError(
                f"{label} returned {article} {kind}; Tag conditions"
                " must complete synchronously"
                )

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
        inputs: dict[str, Any],
        ) -> Callable[[object, dict[str, Any]], Any]:
    """Bind a condition to the inputs from its own Tagging.

    An @Underlay condition receives, as its second positional parameter, a
    callable reporting whether the prior visible condition of the same name
    held (True / False) -- normalized so that both ``assert under()`` and
    ``return under() and ...`` compose, whatever style the Base used.
    """

    uses_underlay = _takes_underlay(function)
    captured_inputs = dict(inputs)

    if uses_underlay and prior is None:
        raise TagResolutionError(
                f"{function.__qualname__} is @Underlay but no prior"
                " condition of that name exists"
                )

    @wraps(function)
    def Check(
            agent: object,
            _evaluation_inputs: dict[str, Any],
            ) -> Any:
        if not uses_underlay:
            return function(
                    agent,
                    **_protocol_inputs(
                            function,
                            captured_inputs,
                            1,
                            ),
                    )

        def under() -> bool:
            try:
                return _condition_verdict(
                        prior(
                                agent,
                                {},
                                ),
                        "underlay",
                        )
            except Exception:
                return False

        return function(
                agent,
                under,
                **_protocol_inputs(
                        function,
                        captured_inputs,
                        2,
                        ),
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
    verifying = _verifying.get()

    if key in verifying:
        return True

    token = _verifying.set(
            verifying
            | {
                key,
                }
            )

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
        _verifying.reset(token)


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
    verifying = _verifying.get()

    if key in verifying:
        return {}

    token = _verifying.set(
            verifying
            | {
                key,
                }
            )

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
        _verifying.reset(token)

    return out


class Contract:
    """The named, on-demand contract checks for an Agent.

    When visible Postconditions exist, ``bool(agent)`` / ``if agent`` /
    ``assert agent`` give their boolean form. Without one, native host
    truthiness remains intact. ``Contract`` gives the form that *names the
    culprit*: each method runs the relevant visible conditions and raises --
    naming the first that does not hold -- or returns True. It is a namespace
    of language-level operations *on* the Agent, not a feature of the Agent
    and not a Tag method.

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
