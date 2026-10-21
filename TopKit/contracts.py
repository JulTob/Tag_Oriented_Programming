"""Contracts: Pre Services gate Tagging; Post Gains bind the Agent.

A condition is strictly boolean: True or a fall-through (None) holds,
False fails, anything else is rejected. An assert-style body fails by
raising.
"""

from __future__ import annotations

from contextlib import nullcontext
from typing import Any
from typing import Callable
from typing import Iterable

from .observations import _refuse_observed_act
from .observations import _observing
from .observations import _ObservationViolation
from .post_queries import _post_evaluation
from .post_queries import _post_verdict
from .post_queries import _verdict_in_session
from .post_queries import _Session

from .arrest import _arrest_of
from .arrest import _safehouse
from .declarations import _MISSING
from .declarations import _protocol_inputs
from .declarations import _discard_lazy_result
from .declarations import _takes_underlay
from .errors import _Named
from .errors import _exception_text
from .errors import _type_name
from .errors import TagCompositionError
from .errors import TagContractError
from .errors import TagPostconditionError
from .geometry import _leaves
from .state import _namespace_of
from .state import _State
from .state import _name_of
from .state import _state_of


Check = Callable[[object, dict[str, Any]], Any]
_NO_INPUTS: dict[str, Any] = {}   # Post wrappers never receive named inputs


def _holds_for_population(agent: object) -> bool:
    """Judge every Post; an exact recursive edge contributes neutral True."""

    if _safehouse and _arrest_of(agent) is not None:
        return False
    return _holds(agent)


def _refuse_condition_binding(
        agent: object,
        name: str,
        ) -> None:
    """A visible Post is computed on read and has no stored binding."""

    state = _state_of(agent)

    if state is not None and name in state.postconditions:
        raise TagCompositionError(
                f"{name!r} is a computed Post on {_name_of(agent)};"
                " it cannot be assigned or deleted"
                )


class _Post_Gate:
    """Compute a Post on read and refuse writes while it is visible.

    If the Agent's state no longer carries the Post, expose the binding
    gate this descriptor replaced, or ordinary instance storage when there was
    none.
    """

    __slots__ = ("name", "member")

    def __init__(
            gate,
            name: str,
            member: Any = _MISSING,
            ) -> None:
        gate.name = name
        gate.member = member

    def __get__(
            gate,
            agent: object,
            owner: type | None = None,
            ) -> Any:
        if agent is None:
            if gate.member is _MISSING:
                return gate

            getter = getattr(type(gate.member), "__get__", None)
            return getter(gate.member, None, owner) if getter else gate.member

        state = _state_of(agent)

        if state is not None:
            verdict = _condition_member(
                    agent,
                    state,
                    gate.name,
                    )

            if verdict is not None:
                return verdict

        if gate.member is not _MISSING:
            getter = getattr(type(gate.member), "__get__", None)
            return (
                    getter(gate.member, agent, type(agent))
                    if getter else gate.member
                    )

        value = _namespace_of(agent).get(
                gate.name,
                _MISSING,
                )

        if value is _MISSING:
            raise AttributeError(
                    f"{_name_of(agent)} has no member {gate.name!r}"
                    )

        return value

    def __set__(
            gate,
            agent: object,
            value: Any,
            ) -> None:
        _refuse_condition_binding(agent, gate.name)

        if gate.member is not _MISSING:
            setter = getattr(type(gate.member), "__set__", None)

            if setter is not None:
                setter(gate.member, agent, value)
                return

        _namespace_of(agent)[gate.name] = value

    def __delete__(
            gate,
            agent: object,
            ) -> None:
        _refuse_condition_binding(agent, gate.name)

        if gate.member is not _MISSING:
            deleter = getattr(type(gate.member), "__delete__", None)

            if deleter is not None:
                deleter(gate.member, agent)
                return

        _namespace_of(agent).pop(
                gate.name,
                None,
                )


def _result_repr(result: Any) -> str:
    """Keep ordinary diagnostic detail without trusting an invalid value's repr."""

    try:
        return str.__str__(repr(result))
    except Exception:
        return "<result representation unavailable>"


def _verdict(
        result: Any,
        label: str,
        ) -> bool:
    if result is True or result is None:
        return True

    if result is False:
        return False

    try:
        lazy = _discard_lazy_result(result)
    except Exception as error:
        raise TagContractError(
                f"{label} returned a lazy result that could not be"
                f" disposed of: {_type_name(error)}: {_exception_text(error)}"
                ) from error

    if lazy is not None:
        article = "an" if lazy == "async generator" else "a"

        raise TagContractError(
                f"{label} returned {article} {lazy}; a condition must"
                " complete synchronously. TOP does not await or iterate"
                " application protocols."
                )

    raise TagContractError(
            f"{label} returned {_result_repr(result)} ({_type_name(result)}); a"
            " condition must yield True, False, or None. TOP does not"
            " coerce truthy / falsy values: write the comparison you mean,"
            " such as `x != 0`, `x > 0`, or `x is not None`."
            )


def _bind_condition(
        function: Callable[..., Any],
        prior: Check | None,
        with_inputs: bool,
        name: str,
        *,
        uses_underlay: bool | None = None,
        neutral_underlay: bool = False,
        ) -> Check:
    """Bind one condition, giving it its Underlay when marked.

    The Underlay is a callable reporting whether the prior condition of the
    same name holds (True / False), so ``assert base()`` and
    ``return base() and ...`` both compose.
    """

    if uses_underlay is None:
        uses_underlay = _takes_underlay(function, name)

    if uses_underlay and prior is None and not neutral_underlay:
        from .errors import TagResolutionError

        raise TagResolutionError(
                f"{str.__str__(name)!r} is @Underlay but no prior"
                " condition of that name is visible"
                )

    skip = 2 if uses_underlay else 1

    if not uses_underlay and not with_inputs:
        def Plain_Check(
                agent: object,
                inputs: dict[str, Any],
                ) -> Any:
            return function(agent)   # holds no prior binding: re-applying cannot pile up

        Plain_Check.__topkit_post_label__ = (str.__str__(name), f"Postcondition {str.__str__(name)!r}")
        return Plain_Check

    if not uses_underlay:
        prior = None   # never called: do not keep the earlier binding alive

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
            if prior is None:
                return True

            try:
                if not with_inputs:
                    return _post_verdict(
                            agent, prior, inputs,
                            lambda: _verdict(prior(agent, inputs), "condition Underlay"),
                            )
                result = prior(agent, inputs)
            except TagContractError:
                raise
            except Exception:
                return False

            return _verdict(result, "condition Underlay")

        return function(
                agent,
                base,
                **named,
                )

    Check.__topkit_post_label__ = (str.__str__(name), f"Postcondition {str.__str__(name)!r}")
    return Check


def _evaluate(
        checks: Iterable[tuple[str, Check]],
        agent: object,
        inputs: dict[str, Any],
        failure: _Named,
        phase: str,
        *,
        post: bool = False,
        ) -> None:
    """Run conditions; name the first failure without hiding other Posts in cycles."""

    with _post_evaluation() if post else nullcontext() as query:
        for name, check in checks:
            plain_name = str.__str__(name)
            label = f"{phase} {plain_name!r}"
            try:
                # Error rendering is observed too, including on memo hits.
                with _observing(label):
                    def Evaluate() -> bool:
                        return _checked_result(
                                agent, plain_name, check, inputs,
                                label, failure,
                                )

                    verdict = (
                            _post_verdict(agent, check, inputs, Evaluate, _query=query)
                            if post else Evaluate()
                            )

                    if not verdict:
                        raise failure.Named(plain_name)(f"{label} failed")
            except _ObservationViolation as error:
                raise failure.Named(plain_name)(
                        f"{label} raised {_type_name(error)}: {_exception_text(error)}"
                        ) from error


def _checked_result(
        agent: object,
        name: str,
        check: Check,
        inputs: dict[str, Any],
        label: str,
        failure: _Named,
        ) -> bool:
    """Distinguish a body failure from rejecting its returned verdict.

    Disposing an invalid lazy result may itself fail. Its original cause
    belongs directly to that Contract Failure, rather than another wrapper.
    """

    try:
        result = check(agent, inputs)
    except TagContractError as error:
        raise TagContractError(
                f"{label} failed: {_exception_text(error)}"
                ) from error
    except Exception as error:
        raise failure.Named(name)(
                f"{label} raised {_type_name(error)}: {_exception_text(error)}"
                ) from error

    return _verdict(result, label)


def _read_post(
        agent: object,
        name: str,
        check: Check,
        *,
        check_custody: bool = True,
        query: _Session | None = None,
        ) -> bool:
    """Read one Post, observing its calculation only when it actually runs."""

    plain_name, label = check.__topkit_post_label__

    def Evaluate() -> bool:
        with _observing(label):
            return _checked_result(
                    agent, plain_name, check, _NO_INPUTS, label, TagPostconditionError,
                    )

    if query is not None:
        return _verdict_in_session(
                query, agent, check, _NO_INPUTS, Evaluate, check_custody,
                )
    return _post_verdict(
            agent, check, _NO_INPUTS, Evaluate,
            check_custody=check_custody,
            )


def _guarded(
        agent: object,
        detailed: bool,
        failure: _Named,
        phase: str,
        ) -> bool:
    """Check the visible Contract, sharing completed Post results in one query."""

    state = _state_of(agent)
    if state is None:
        return True

    state.composing += 1
    try:
        with _post_evaluation() as query:
            checks = tuple(state.postconditions.items())
            if detailed:
                _evaluate(checks, agent, {}, failure, phase, post=True)
                return True

            for name, check in checks:
                try:
                    if not _read_post(agent, name, check, query=query):
                        return False
                except Exception:
                    return False
            return True
    finally:
        state.composing -= 1


def _holds(
        agent: object,
        state: _State | None = None,
        ) -> bool:
    """True exactly when the Agent is free and every visible Post holds."""

    if _safehouse and _arrest_of(agent) is not None:
        return False
    if state is None:
        state = _state_of(agent)
    if state is None or not state.postconditions:
        return True

    state.composing += 1
    try:
        with _post_evaluation() as query:
            for name, check in tuple(state.postconditions.items()):
                try:
                    if not _read_post(agent, name, check, query=query):
                        return False
                except Exception:
                    return False
            return not _safehouse or _arrest_of(agent) is None
    finally:
        state.composing -= 1


def _condition_member(
        agent: object,
        state: _State,
        name: str,
        ) -> bool | None:
    """Read a named Post; exact recursive references contribute True."""

    check = state.postconditions.get(name)
    if check is None:
        return None

    state.composing += 1
    try:
        try:
            return _read_post(agent, name, check)
        except TagContractError:
            raise
        except Exception:
            return False
    finally:
        state.composing -= 1


def _status_of(agent: object) -> dict[str, bool]:
    state = _state_of(agent)
    if state is None:
        return {}

    state.composing += 1
    status: dict[str, bool] = {}
    try:
        with _post_evaluation() as query:
            for name, check in tuple(state.postconditions.items()):
                result_name = str.__str__(name)
                try:
                    status[result_name] = _read_post(
                            agent, name, check, check_custody=False, query=query,
                            )
                except Exception:
                    status[result_name] = False
    finally:
        state.composing -= 1
    return status


def _title_of(
        agent: object,
        ) -> str:
    state = _state_of(agent)
    host = _name_of(agent)

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
    def Postconditions(
            agent: object,
            ) -> bool:
        from .link_forms import _resolve_seat
        agent = _resolve_seat(agent)
        return _guarded(
                agent,
                True,
                TagPostconditionError,
                "Postcondition",
                )

    @staticmethod
    def Delete(
            agent: object,
            *names: str,
            ) -> None:
        """Explicitly end the named removable Post towers.

        An absent name is already at the neutral state and is therefore a
        no-op.  This also keeps older Rip protocols safe when they explicitly
        end a Post that Field removal has just ended automatically.
        """

        _refuse_observed_act('delete a Post')

        from .link_forms import _resolve_seat
        agent = _resolve_seat(agent)
        state = _state_of(agent)

        from .constants import _refuse_constant

        for name in names:
            _refuse_constant(state, name)

        if state is not None:
            from .overlay import _clear_post_name

            for name in names:
                _clear_post_name(state, name)

        if state is not None and names:
            from .state import _runtime_type_for
            from .state import _set_runtime_type

            _set_runtime_type(
                    agent,
                    _runtime_type_for(state),
                    )

    @staticmethod
    def Status(
            agent: object,
            ) -> dict[str, bool]:
        """Verdicts for visible conditions. Ordinary check errors become
        False; an exact recursive Post edge contributes neutral True."""

        from .link_forms import _resolve_seat
        agent = _resolve_seat(agent)
        return {
                **_status_of(agent),
                }

    @staticmethod
    def Display(
            agent: object,
            ) -> str:
        from .link_forms import _resolve_seat
        agent = _resolve_seat(agent)
        title = _title_of(agent)
        post = _status_of(agent)

        if not post:
            return f"{title}: no conditions"

        lines = [f"{title} contract:"]

        lines.append("  Post:")

        for name, holds in post.items():
            lines.append(
                    f"    {'OK' if holds else 'XX'}  {name}"
                    )

        return "\n".join(lines)
