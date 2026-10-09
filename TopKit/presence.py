"""A Contribution's name at an Agent, independent of its kind or value."""

from __future__ import annotations

from functools import partial
from inspect import getattr_static
from types import GetSetDescriptorType
from types import MemberDescriptorType
from typing import Any

from .declarations import STATE
from .declarations import _MISSING
from .state import _Deleted
from .state import _Published
from .state import _Secret_Gate
from .constants import _Constant_Gate
from .contracts import _Condition_Gate


def _namespace(agent: object) -> Any:
    """Read real storage even when a host shadows ``__dict__``."""

    if issubclass(type(agent), type):
        return type.__dict__["__dict__"].__get__(agent)

    for owner in type(agent).__mro__:
        member = owner.__dict__.get("__dict__")

        if issubclass(type(member), GetSetDescriptorType):
            return member.__get__(agent, type(agent))

    return {}


def _binding(agent: object, name: str, namespace: Any) -> tuple[Any, bool]:
    """Static lookup with real instance storage and descriptor precedence."""

    for owner in type(agent).__mro__:
        member = owner.__dict__.get(name, _MISSING)

        if member is not _MISSING:
            member_type = type(member)

            if (getattr_static(member_type, "__get__", _MISSING) is not _MISSING
                    and (getattr_static(member_type, "__set__", _MISSING) is not _MISSING
                         or getattr_static(member_type, "__delete__", _MISSING) is not _MISSING)):
                return member, False

            break

    if name in namespace:
        return namespace[name], True

    return getattr_static(agent, name, _MISSING), False


def _present(
        agent: object,
        name: str,
        ) -> bool:
    """Inspect the current binding without running a getter or a promise.

    TOP's contribution registries describe the Overlay, but do not prove
    a Record or Action still has a binding. Host members participate in
    the same lookup; dynamically invented ``__getattr__`` answers do not.
    """

    if name == STATE or name.startswith("_TOPKIT_"):
        return False

    namespace = _namespace(agent)
    state = namespace.get(STATE)

    if state is not None and name in state.secrets:
        if state.composing == 0:
            return False

        if state.pinned is not None:
            return name in state.secret_values

    member, stored = _binding(agent, name, namespace)

    if issubclass(type(member), _Constant_Gate):
        if state is not None and state.constants.get(name, (None, None))[1] == "postcondition":
            return False
        if member.member is _MISSING:
            return name in namespace
        member = member.member

    if issubclass(type(member), _Condition_Gate):
        if state is not None and (
                name in state.preconditions
                or name in state.postconditions
                ):
            return False
        if member.member is _MISSING:
            return name in namespace
        member = member.member

    if stored:
        return True

    if member is _MISSING:
        return False

    if issubclass(type(member), (_Deleted, _Secret_Gate)):
        return name in namespace

    if issubclass(type(member), _Published):
        if state is None or name not in state.reports:
            return False

        origin, _report = state.reports[name]
        return (
                origin in state.active
                and getattr_static(origin, name, _MISSING) is not _MISSING
                )

    if issubclass(type(member), MemberDescriptorType):
        # A slot declaration alone does not mean its storage is filled.
        # This is Python's built-in slot reader, never a user getter.
        try:
            member.__get__(agent, type(agent))
        except AttributeError:
            return False

    return True


class _Presence:
    """Add the name query without changing reflected-operator priority.

    Python compares class-level reflected methods before giving a right
    subtype priority. Expose the original method there; binding to an
    Agent supplies the dispatcher. A plain wrapper function would make
    every generated runtime type look like a new matrix implementation.
    """

    __slots__ = ("fallback",)

    def __init__(hook, fallback: Any) -> None:
        hook.fallback = fallback

    def __get__(hook, agent: object, owner: type | None = None) -> Any:
        if agent is not None:
            return partial(hook, agent)

        if hook.fallback is _MISSING:
            return hook

        descriptor = getattr(type(hook.fallback), "__get__", None)

        if descriptor is not None:
            return descriptor(hook.fallback, None, owner)

        return hook.fallback

    def __call__(hook, agent: object, operand: object) -> Any:
        if issubclass(type(operand), str):
            return _present(agent, str.__str__(operand))

        fallback = hook.fallback

        if fallback is _MISSING:
            return NotImplemented

        descriptor = getattr(type(fallback), "__get__", None)

        if descriptor is not None:
            fallback = descriptor(fallback, agent, type(agent))

        return fallback(operand)


def _presence_hook(
        namespace: dict[str, Any],
        host_type: type,
        ) -> None:
    """Keep the reflected operator that the composed runtime would use.

    Save the descriptor itself so host methods, Tag Actions and TOP's
    deletion/Secret gates retain their ordinary binding for other operands.
    """

    fallback = namespace.get("__rmatmul__", _MISSING)

    if fallback is _MISSING:
        for owner in host_type.__mro__:
            if "__rmatmul__" in owner.__dict__:
                fallback = owner.__dict__["__rmatmul__"]
                break

    if issubclass(type(fallback), _Presence):
        fallback = fallback.fallback

    namespace["__rmatmul__"] = _Presence(fallback)
