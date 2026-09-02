from __future__ import annotations

"""Uniform Agent access for Actions, Records, and Conditions."""

from inspect import Parameter
from inspect import isasyncgenfunction
from inspect import iscoroutinefunction
from inspect import isgeneratorfunction
from inspect import signature
from types import MethodType
from typing import Any

from .declarations import _MISSING


def _bound_action(
        agent: object,
        name: str,
        body: Any,
        ) -> "_Bound_Member":
    return _Bound_Member(
            agent,
            name,
            "action",
            body=body,
            )


def _bound_record(
        agent: object,
        name: str,
        frozen: Any = _MISSING,
        ) -> "_Bound_Member":
    return _Bound_Member(
            agent,
            name,
            "record",
            frozen=frozen,
            )


def _bound_condition(
        agent: object,
        name: str,
        check: Any,
        ) -> "_Bound_Member":
    return _Bound_Member(
            agent,
            name,
            "condition",
            body=check,
            )


def _assigned(
        value: Any,
        ) -> Any:
    if isinstance(
            value,
            _Bound_Member,
            ):
        return value._released()

    return value


def _as_operand(
        value: Any,
        ) -> Any:
    if isinstance(
            value,
            _Bound_Member,
            ):
        return value._payload()

    return value


def _nullary_invocable(
        bound: Any,
        ) -> bool:
    function = getattr(
            bound,
            "__func__",
            bound,
            )

    if (
            iscoroutinefunction(function)
            or isasyncgenfunction(function)
            or isgeneratorfunction(function)
            ):
        return False

    try:
        expected = signature(bound)
    except (
            TypeError,
            ValueError,
            ):
        return False

    for parameter in expected.parameters.values():
        if parameter.kind in (
                Parameter.VAR_POSITIONAL,
                Parameter.VAR_KEYWORD,
                ):
            continue

        if parameter.default is Parameter.empty:
            return False

    return True


class _Bound_Member:
    """One Agent contribution readable as data or as a call.

    A Record's stored value stays stored: ``agent.hp()`` does not run the
    materializer again. A nullary Action may be read without ``()``; an
    Action that needs inputs remains a handle until it is called. A
    Condition is a binary check: ``agent.Has_Spellbook`` and
    ``agent.Has_Spellbook()`` both report whether the promise holds.
    """

    __slots__ = (
            "_agent",
            "_name",
            "_kind",
            "_body",
            "_frozen",
            )

    def __init__(
            member,
            agent: object,
            name: str,
            kind: str,
            body: Any = None,
            frozen: Any = _MISSING,
            ) -> None:
        object.__setattr__(
                member,
                "_agent",
                agent,
                )
        object.__setattr__(
                member,
                "_name",
                name,
                )
        object.__setattr__(
                member,
                "_kind",
                kind,
                )
        object.__setattr__(
                member,
                "_body",
                body,
                )
        object.__setattr__(
                member,
                "_frozen",
                frozen,
                )

    def _bound(
            member,
            ) -> Any:
        return MethodType(
                member._body,
                member._agent,
                )

    def _value(
            member,
            ) -> Any:
        if member._frozen is not _MISSING:
            return member._frozen

        from .records import _record_value_for

        value = _record_value_for(
                member._agent,
                member._name,
                )

        if value is _MISSING:
            raise AttributeError(
                    f"{type(member._agent).__name__} has no visible"
                    f" member {member._name!r}"
                    )

        return value

    def _condition_error_type(
            member,
            ) -> type:
        from .errors import TagPostconditionError
        from .errors import TagPreconditionError
        from .runtime_types import _existing_state_for

        state = _existing_state_for(member._agent)

        if (
                state is not None
                and member._name in state.postconditions
                ):
            return getattr(
                    TagPostconditionError,
                    member._name,
                    )

        return getattr(
                TagPreconditionError,
                member._name,
                )

    def _condition_holds(
            member,
            ) -> bool:
        from .contracts import _condition_verdict

        try:
            result = member._body(
                    member._agent,
                    {},
                    )
        except Exception:
            return False

        return _condition_verdict(
                result,
                f"condition {member._name!r}",
                )

    def _released(
            member,
            ) -> Any:
        if member._kind == "action":
            return member._bound()

        if member._kind == "condition":
            return member._condition_holds()

        return member._value()

    def _payload(
            member,
            ) -> Any:
        if member._kind == "record":
            return member._value()

        if member._kind == "condition":
            return member._condition_holds()

        bound = member._bound()

        if _nullary_invocable(bound):
            return bound()

        return bound

    def __call__(
            member,
            *args: Any,
            **kwargs: Any,
            ) -> Any:
        if member._kind == "condition":
            if args or kwargs:
                raise TypeError(
                        f"Condition {member._name!r} takes no arguments"
                        )

            return member._condition_holds()

        if member._kind == "action":
            return member._bound()(
                    *args,
                    **kwargs,
                    )

        value = member._value()

        if not args and not kwargs:
            return value

        if callable(value):
            return value(
                    *args,
                    **kwargs,
                    )

        raise TypeError(
                f"Record {member._name!r} takes no arguments"
                )

    @property
    def __signature__(
            member,
            ):
        if member._kind == "condition":
            def Condition_Check():
                return True

            return signature(Condition_Check)

        if member._kind == "action":
            return signature(
                    member._bound()
                    )

        def Record_Value():
            return member._value()

        return signature(Record_Value)

    def __bool__(
            member,
            ) -> bool:
        return bool(
                member._payload()
                )

    def __hash__(
            member,
            ) -> int:
        return hash(
                member._payload()
                )

    def __repr__(
            member,
            ) -> str:
        if member._kind == "condition":
            return repr(
                    member._condition_holds()
                    )

        if member._kind == "record":
            return repr(
                    member._value()
                    )

        return repr(
                member._bound()
                )

    def __str__(
            member,
            ) -> str:
        if member._kind == "condition":
            return str(
                    member._condition_holds()
                    )

        if member._kind == "record":
            return str(
                    member._value()
                    )

        return str(
                member._bound()
                )

    def __format__(
            member,
            specification: str,
            ) -> str:
        return format(
                member._payload(),
                specification,
                )

    def __eq__(
            member,
            other: object,
            ) -> Any:
        return member._payload() == _as_operand(other)

    def __getattr__(
            member,
            name: str,
            ) -> Any:
        if (
                member._kind == "condition"
                and name == "Error"
                ):
            return member._condition_error_type()

        return getattr(
                member._payload(),
                name,
                )

    def __setattr__(
            member,
            name: str,
            value: Any,
            ) -> None:
        if name in _Bound_Member.__slots__:
            object.__setattr__(
                    member,
                    name,
                    value,
                    )
            return

        setattr(
                member._released(),
                name,
                _assigned(value),
                )

    def __delattr__(
            member,
            name: str,
            ) -> None:
        delattr(
                member._released(),
                name,
                )

    def __getitem__(
            member,
            key: Any,
            ) -> Any:
        return member._payload()[
                _as_operand(key)
                ]

    def __setitem__(
            member,
            key: Any,
            value: Any,
            ) -> None:
        member._payload()[
                _as_operand(key)
                ] = _assigned(value)

    def __delitem__(
            member,
            key: Any,
            ) -> None:
        del member._payload()[
                _as_operand(key)
                ]

    def __len__(
            member,
            ) -> int:
        return len(
                member._payload()
                )

    def __iter__(
            member,
            ) -> Any:
        return iter(
                member._payload()
                )

    def __contains__(
            member,
            item: Any,
            ) -> bool:
        return _as_operand(item) in member._payload()

    def __reversed__(
            member,
            ) -> Any:
        return reversed(
                member._payload()
                )

    def __index__(
            member,
            ) -> int:
        return member._payload().__index__()

    def __int__(
            member,
            ) -> int:
        return int(
                member._payload()
                )

    def __float__(
            member,
            ) -> float:
        return float(
                member._payload()
                )

    def __complex__(
            member,
            ) -> complex:
        return complex(
                member._payload()
                )

    def __round__(
            member,
            digits: int | None = None,
            ) -> Any:
        payload = member._payload()

        if digits is None:
            return round(payload)

        return round(
                payload,
                digits,
                )


def _binary_operator(
        operation: str,
        ):
    def operate(
            member: _Bound_Member,
            other: Any,
            *rest: Any,
            ) -> Any:
        payload = member._payload()
        method = getattr(
                payload,
                operation,
                None,
                )

        if method is None:
            return NotImplemented

        operand = _as_operand(other)

        if rest:
            return method(
                    operand,
                    *rest,
                    )

        return method(operand)

    operate.__name__ = operation
    operate.__qualname__ = f"_Bound_Member.{operation}"

    return operate


def _reflected_operator(
        operation: str,
        ):
    def operate(
            member: _Bound_Member,
            other: Any,
            ) -> Any:
        payload = member._payload()
        method = getattr(
                payload,
                operation,
                None,
                )

        if method is None:
            return NotImplemented

        return method(
                _as_operand(other)
                )

    operate.__name__ = operation
    operate.__qualname__ = f"_Bound_Member.{operation}"

    return operate


def _inplace_operator(
        operation: str,
        ):
    def operate(
            member: _Bound_Member,
            other: Any,
            ) -> Any:
        payload = member._payload()
        method = getattr(
                payload,
                operation,
                None,
                )

        if method is None:
            return NotImplemented

        result = method(
                _as_operand(other)
                )

        if result is NotImplemented:
            return NotImplemented

        return result

    operate.__name__ = operation
    operate.__qualname__ = f"_Bound_Member.{operation}"

    return operate


def _unary_operator(
        operation: str,
        ):
    def operate(
            member: _Bound_Member,
            ) -> Any:
        payload = member._payload()
        method = getattr(
                payload,
                operation,
                None,
                )

        if method is None:
            return NotImplemented

        return method()

    operate.__name__ = operation
    operate.__qualname__ = f"_Bound_Member.{operation}"

    return operate


_BINARY_NAMES = (
        "add",
        "sub",
        "mul",
        "matmul",
        "truediv",
        "floordiv",
        "mod",
        "divmod",
        "pow",
        "lshift",
        "rshift",
        "and",
        "xor",
        "or",
        )
_UNARY_NAMES = (
        "neg",
        "pos",
        "abs",
        "invert",
        "floor",
        "ceil",
        "trunc",
        )
_COMPARE_NAMES = (
        "lt",
        "le",
        "gt",
        "ge",
        )

for _name in _BINARY_NAMES:
    _dunder = f"__{_name}__"
    setattr(
            _Bound_Member,
            _dunder,
            _binary_operator(_dunder),
            )
    setattr(
            _Bound_Member,
            f"__r{_name}__",
            _reflected_operator(f"__r{_name}__"),
            )
    setattr(
            _Bound_Member,
            f"__i{_name}__",
            _inplace_operator(f"__i{_name}__"),
            )

for _name in _UNARY_NAMES:
    _dunder = f"__{_name}__"
    setattr(
            _Bound_Member,
            _dunder,
            _unary_operator(_dunder),
            )

for _name in _COMPARE_NAMES:
    _dunder = f"__{_name}__"
    setattr(
            _Bound_Member,
            _dunder,
            _binary_operator(_dunder),
            )
    setattr(
            _Bound_Member,
            f"__r{_name}__",
            _reflected_operator(f"__r{_name}__"),
            )

del _name
del _dunder
