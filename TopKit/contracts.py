"""Contracts: Preconditions gate the incoming Agent, Postconditions
promise about the finished one.

A condition is strictly boolean: True or a fall-through (None) holds,
False fails, anything else is rejected. An assert-style body fails by
raising.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextlib import nullcontext
from contextvars import ContextVar
from typing import Any
from typing import Callable
from typing import Iterable
from typing import Iterator

from .declarations import _MISSING
from .declarations import _protocol_inputs
from .declarations import _discard_lazy_result
from .declarations import _takes_underlay
from .errors import _Named
from .errors import _exception_text
from .errors import _type_name
from .errors import TagCompositionError
from .errors import TagContractError
from .errors import TagError
from .errors import TagPostconditionError
from .errors import TagPreconditionError
from .geometry import _leaves
from .observation import _observing
from .observation import _pre_observation
from .state import _namespace_of
from .state import _State
from .state import _name_of
from .state import _state_of


Check = Callable[[object, dict[str, Any]], Any]


class _Post_Check:
    __slots__ = ("identity", "check_identity", "active")

    def __init__(self, agent: object, check: Check) -> None:
        self.identity = id(agent)
        self.check_identity = id(check)
        self.active = True


_post_checks: ContextVar[tuple[_Post_Check, ...]] = ContextVar(
        "topkit_post_checks", default=(),
        )


@contextmanager
def _checking_post(agent: object, check: Check) -> Iterator[Any]:
    """Observe one Post; its exact check is neutral on recursive reads."""

    marker = _Post_Check(agent, check)
    token = _post_checks.set((*_post_checks.get(), marker))

    try:
        with _observing("a Postcondition") as flow:
            yield flow
    finally:
        marker.active = False
        _post_checks.reset(token)


def _is_checking_post(agent: object, check: Check) -> bool:
    for marker in _post_checks.get():
        if (marker.active and marker.identity == id(agent)
                and marker.check_identity == id(check)):
            return True

    return False


def _holds_for_population(agent: object) -> bool:
    """A recursive Post contributes neutral True to this Agent's verdict."""

    state = _state_of(agent)

    if state is None or not state.postconditions:
        return True

    return _holds(agent, state)


def _refuse_condition_binding(
        agent: object,
        name: str,
        ) -> None:
    """A visible condition is computed on read and has no stored binding."""

    state = _state_of(agent)

    if state is not None and (
            name in state.preconditions
            or name in state.postconditions
            ):
        raise TagCompositionError(
                f"{name!r} is a computed condition on {_name_of(agent)};"
                " it cannot be assigned or deleted"
                )


class _Condition_Gate:
    """Compute a condition on read and refuse writes while it is visible.

    If the Agent's state no longer carries the condition, expose the binding
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

    if result is True or result is None:
        return True

    if result is False:
        return False

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
        ) -> Check:
    """Bind one condition, giving it its Underlay when marked.

    The Underlay is a callable reporting whether the prior condition of the
    same name holds (True / False), so ``assert base()`` and
    ``return base() and ...`` both compose.
    """

    uses_underlay = _takes_underlay(function, name)

    if uses_underlay and prior is None:
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
            try:
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
    """Run conditions; raise ``failure`` naming the first that does not hold."""

    for name, check in checks:
        if post and _is_checking_post(agent, check):
            continue

        flow = None
        if post:
            observation = _checking_post(agent, check)
        elif phase == "Precondition":
            observation = _pre_observation()
        else:
            observation = nullcontext()

        try:
            with observation as flow:
                try:
                    result = check(agent, inputs)
                except TagContractError as error:
                    raise TagContractError(
                            f"{phase} {name!r} failed: {_exception_text(error)}"
                            ) from error
                except Exception as error:
                    raise failure.Named(name)(
                            f"{phase} {name!r} raised {_type_name(error)}: {_exception_text(error)}"
                            ) from error

                verdict = _verdict(result, f"{phase} {name!r}")
        except TagCompositionError as error:
            if flow is None or error is not flow.violation:
                raise
            # Verdicts and diagnostics can catch the immediate refusal.
            # The observation still names the failed Gate or promise.
            # Its name may be a str subclass whose __repr__ performs a TOP
            # act after observation ends, so render a plain string.
            plain_name = str.__str__(name)
            raise failure.Named(plain_name)(
                    f"{phase} {plain_name!r} raised {_type_name(error)}: {_exception_text(error)}"
                    ) from error

        if not verdict:
            raise failure.Named(name)(
                    f"{phase} {name!r} failed"
                    )


def _guarded(
        agent: object,
        scope: str,
        detailed: bool,
        failure: _Named,
        phase: str,
        ) -> bool:
    """Run one scope of the Agent's visible conditions on demand.

    A recursive Post contributes neutral True; other Posts are still judged.
    """

    state = _state_of(agent)

    if state is None or (scope == "preconditions" and state.checking):
        return True

    reentrant = state.checking
    if scope == "preconditions":
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
                    post=scope == "postconditions",
                    )

            return True

        for name, check in checks:
            if scope == "postconditions" and _is_checking_post(agent, check):
                continue

            if scope == "postconditions":
                observation = _checking_post(agent, check)
            elif scope == "preconditions":
                observation = _pre_observation()
            else:
                observation = nullcontext()

            try:
                with observation:
                    verdict = _verdict(check(agent, {}), name)
                if not verdict:
                    return False
            except Exception:
                return False

        return True
    finally:
        state.composing -= 1
        state.checking = reentrant


def _holds(
        agent: object,
        state: _State | None = None,
        ) -> bool:
    """True exactly when every visible Postcondition holds."""

    if state is None:
        state = _state_of(agent)

    if state is None or not state.postconditions:
        return True   # nothing promised

    state.composing += 1

    try:
        for name, check in state.postconditions.items():
            if _is_checking_post(agent, check):
                continue

            try:
                with _checking_post(agent, check):
                    verdict = _verdict(check(agent, {}), name)
                if not verdict:
                    return False
            except Exception:
                return False

        return True
    finally:
        state.composing -= 1


def _condition_member(
        agent: object,
        state: _State,
        name: str,
        ) -> bool | None:
    """The condition called ``name`` on the Agent, read as a plain bool
    (STEP-SPEC-14): a Postcondition first, then a Precondition. None when
    the Agent has no condition of that name."""

    check = state.postconditions.get(name)
    post = check is not None

    if not post:
        check = state.preconditions.get(name)

    if check is None:
        return None

    if post and _is_checking_post(agent, check):
        return True

    reentrant = state.checking
    if not post:
        state.checking = True
    state.composing += 1

    try:
        try:
            with _checking_post(agent, check) if post else _pre_observation():
                verdict = _verdict(
                        check(agent, {}),
                        name,
                        )
            return verdict
        except TagContractError:
            raise
        except Exception:
            return False

    finally:
        state.composing -= 1
        state.checking = reentrant


def _status_of(
        agent: object,
        scope: str,
        ) -> dict[str, bool]:
    state = _state_of(agent)

    if state is None:
        return {}

    reentrant = state.checking
    if scope == "preconditions":
        state.checking = True
    state.composing += 1
    status: dict[str, bool] = {}

    try:
        for name, check in getattr(state, scope).items():
            # A str subclass key may run code from __hash__. The result
            # dictionary is also written on the fallback path, after the
            # observation has ended, so store only inert plain strings.
            result_name = str.__str__(name)
            if scope == "postconditions" and _is_checking_post(agent, check):
                status[result_name] = True
                continue

            try:
                observation = (
                        _checking_post(agent, check)
                        if scope == "postconditions"
                        else _pre_observation()
                        )
                with observation:
                    verdict = _verdict(check(agent, {}), name)
                status[result_name] = verdict
            except Exception:
                status[result_name] = False
    finally:
        state.composing -= 1
        state.checking = reentrant

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
    def Delete(
            agent: object,
            *names: str,
            ) -> None:
        """End the named conditions on the Agent, explicitly.

        Conditions are sticky: Rip does not remove them. A Tag whose gate
        or promise should end with its membership deletes it here, from
        its own ``@Rip`` protocol, one deliberate name at a time. A name
        that is not a condition on the Agent is a Resolution Failure: an
        author who ends a promise must be ending a real one. Every requested
        name is validated before any condition ends.
        """

        from .errors import TagResolutionError
        from .observation import _refuse_pre_mutation

        _refuse_pre_mutation("delete a condition")

        state = _state_of(agent)

        from .constants import _refuse_constant

        available = set()

        if state is not None:
            available.update(state.preconditions)
            available.update(state.postconditions)

        for name in names:
            if name not in available:
                raise TagResolutionError(
                        f"{name!r} is not a condition on {_name_of(agent)};"
                        " Contract.Delete ends a gate or a promise that is"
                        " there"
                        )

            _refuse_constant(state, name)
            available.remove(name)

        for name in names:
            for scope in (
                    state.preconditions if state is not None else {},
                    state.postconditions if state is not None else {},
                    ):
                scope.pop(name, None)

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
        False; a recursive Post contributes neutral True at its exact
        revisited check while other conditions are still evaluated."""

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
